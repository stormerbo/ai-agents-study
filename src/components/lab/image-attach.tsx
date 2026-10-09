'use client';

import { useRef, useState } from 'react';

/** 可以挂到消息上的图像（与 schema 里的 image ContentBlock 字段一致） */
export interface AttachedImage {
  mediaType: string;
  dataBase64: string;
  width: number;
  height: number;
  bytes: number;
}

/**
 * 估算一张图的输入 token。
 *
 * 常数来自第 8 章的实测阶梯（deepseek-flash，2026-10-08）：
 *   512×512 → 186、768×768 → 384、1024×1024 → 654、1280×1280 → 996
 * 拟合出的形状是「下限 186 / 上限 996 / 中间约每 1700 像素 1 token」。
 *
 * 注意这只是**估算**：第 8 章也记录了文档里那条「像素数 ÷ 750」的公式在本端点上对不上。
 * 拿它做量级判断可以，不要拿它当账单。
 */
export function estimateImageTokens(width: number, height: number): number {
  const raw = 32 + (width * height) / 1700;
  return Math.round(Math.min(996, Math.max(186, raw)));
}

/**
 * 按第 8 章的结论取缩放目标：实测 ≥1280 的 token 完全相同（服务端会缩），
 * 所以传更大的只是白传字节；而 ≤512 是一个固定下限，再缩不省钱、只丢信息。
 */
const MAX_EDGE = 1280;
/** 超过这个大小就不往中转端点发了 —— 请求体过大的失败发生在流开始之前，报错不好看 */
const MAX_BYTES = 4 * 1024 * 1024;

function base64FromBytes(bytes: Uint8Array): string {
  // 分块拼接：一次性 apply 几十万字节会爆栈
  let bin = '';
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    bin += String.fromCharCode(...bytes.subarray(i, i + CHUNK));
  }
  return btoa(bin);
}

async function readImage(file: File): Promise<AttachedImage> {
  if (!file.type.startsWith('image/')) throw new Error('请选择图片文件');

  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_EDGE / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    bitmap.close();
    throw new Error('浏览器不支持 canvas 2d 上下文');
  }
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  // 缩过的图转 JPEG：字节数能砍掉一半以上，而 token 完全不变（第 8 章实测）。
  // 没缩过的保持原格式 —— 截图里的细笔画在 PNG 下更干净。
  const mediaType = scale < 1 ? 'image/jpeg' : file.type || 'image/png';
  const blob: Blob = await new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('图片编码失败'))), mediaType, 0.92),
  );
  if (blob.size > MAX_BYTES) {
    throw new Error(`图片 ${(blob.size / 1048576).toFixed(1)}MB，超过 4MB 上限`);
  }

  const dataBase64 = base64FromBytes(new Uint8Array(await blob.arrayBuffer()));
  return { mediaType, dataBase64, width, height, bytes: blob.size };
}

export function ImageAttach({
  value,
  onChange,
  disabled,
}: {
  value: AttachedImage | null;
  onChange: (next: AttachedImage | null) => void;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pick = async (file: File | undefined) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      onChange(await readImage(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  if (value) {
    return (
      <div className="flex items-center gap-3 rounded-md border border-border bg-muted/40 px-2 py-1.5">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`data:${value.mediaType};base64,${value.dataBase64}`}
          alt="将要发送的图片"
          className="h-9 w-9 rounded border border-border object-cover"
        />
        <div className="min-w-0 flex-1 text-xs leading-tight">
          <div className="text-foreground">
            {value.width}×{value.height}
            <span className="text-muted-foreground">
              {' · '}
              {(value.bytes / 1024).toFixed(0)}KB
              {' · 约 '}
              {estimateImageTokens(value.width, value.height)} token
            </span>
          </div>
          <div className="mt-0.5 truncate text-muted-foreground">
            会作为 content 数组里的一个 image 块发送，并按内容计费
          </div>
        </div>
        <button
          type="button"
          onClick={() => onChange(null)}
          className="shrink-0 text-xs text-muted-foreground hover:text-foreground"
        >
          移除
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        className="hidden"
        onChange={(e) => void pick(e.target.files?.[0])}
      />
      <button
        type="button"
        disabled={disabled || busy}
        onClick={() => inputRef.current?.click()}
        className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
      >
        {busy ? '处理中…' : '+ 图片'}
      </button>
      <span className="text-xs text-muted-foreground">
        长边会缩到 {MAX_EDGE}px —— 实测再大 token 也一样，只是白传字节
      </span>
      {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
    </div>
  );
}
