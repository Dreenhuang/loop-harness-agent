#!/usr/bin/env python
"""清理缓存并重新测试"""
import sys
import shutil
import subprocess

# 清理__pycache__
cache_dirs = [
    'loop_agent_mcp/__pycache__',
    'loop_agent_mcp/engines/__pycache__',
    'loop_agent_mcp/tools/__pycache__',
    'loop_agent_mcp/core/__pycache__',
]

for d in cache_dirs:
    if __import__('os').path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
        print(f'已清理: {d}')

print('\n重新运行快速修复测试...')
result = subprocess.run([sys.executable, 'quick_fix_test.py'], cwd='.')
sys.exit(result.returncode)
