import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

// 用 .mts 而非 .ts：这个文件是 ESM 语法，而 package.json 没有 "type": "module"，
// 用 .ts 会被当成 CommonJS 加载并产生警告。
export default defineConfig({
  resolve: {
    // 与 tsconfig.json 的 paths 保持一致，否则测试里用不了 @/ 别名
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    // 目前测的全是纯数据与纯函数（内容完整性、SSE 编解码、agent 状态机），
    // 不需要 DOM。等测 React 组件时再按文件切换 environment。
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
});
