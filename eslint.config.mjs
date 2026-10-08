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
  ]),
]);

export default eslintConfig;
