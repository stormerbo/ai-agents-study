import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并 Tailwind 类名。
 *
 * clsx 负责条件拼接，twMerge 负责解决冲突——后者是必需的：
 * `cn('px-2', 'px-4')` 应该得到 `px-4` 而不是两个类同时存在
 * （同时存在时最终效果取决于 CSS 里的声明顺序，不可预测）。
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
