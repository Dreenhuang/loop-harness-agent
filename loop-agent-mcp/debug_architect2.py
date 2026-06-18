#!/usr/bin/env python
"""详细调试architect错误"""
import sys
import tempfile
import shutil
import traceback

sys.path.insert(0, '.')

# 直接导入并测试execute_architect_agent
from loop_agent_mcp.engines.executors import execute_architect_agent

tmpdir = tempfile.mkdtemp(prefix='debug2-')
print(f"工作区: {tmpdir}")

try:
    print("\n调用 execute_architect_agent...")
    result = execute_architect_agent({
        "task_type": "structure"
    })
    print(f"结果: {result}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    print("\n完整traceback:")
    traceback.print_exc()

shutil.rmtree(tmpdir, ignore_errors=True)
