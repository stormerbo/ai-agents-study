import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
    // 实测采集脚本的落盘目录（已 gitignore）。里面的 mjs 是一次性实验代码，
    // 不是产品代码 —— 不忽略它，每写一个实验都会往 lint 里塞噪声。
    'verify-output/**',
    // Pagefind 生成的搜索索引与 UI 包（已 gitignore）。
    // 它们是构建产物、由工具生成，不该进 lint —— 否则每跑一次 build-search
    // 都会多出上百条来自压缩代码的告警。
    'public/pagefind/**',
  ]),
]);

export default eslintConfig;
