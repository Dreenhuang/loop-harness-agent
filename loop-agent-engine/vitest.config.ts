import { defineConfig } from 'vitest/config';

/**
 * Loop-Agent Engine · 本地 Vitest 配置
 *
 * 用途：
 *   - 让 loop-agent-engine/ 子目录可独立运行测试（无需依赖根目录配置）
 *   - 直接以 .ts 形式加载被测模块（orchestrator.ts）和测试文件
 *   - 测试目录固定为 __tests__
 */
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['__tests__/**/*.test.ts'],
    // 允许从测试文件直接 import 同目录的 .ts 源码（无需先 build）
    server: {
      deps: {
        inline: [/\/loop-agent-engine\//],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['orchestrator.ts'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});