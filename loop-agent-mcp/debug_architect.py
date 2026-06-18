#!/usr/bin/env python
"""调试architect structure错误"""
import sys
import tempfile
import shutil
import traceback

sys.path.insert(0, '.')

from loop_agent_mcp.engines.executors import _generate_structure_doc

print("测试 _generate_structure_doc 函数...")

try:
    result = _generate_structure_doc({})
    print("✅ 函数执行成功")
    print(f"输出长度: {len(result)} 字符")
    print("\n前200字符:")
    print(result[:200])
except Exception as e:
    print(f"❌ 错误: {e}")
    traceback.print_exc()

tmpdir = tempfile.mkdtemp(prefix='debug-')
print(f"\n测试工作区: {tmpdir}")

# 直接调用write_file测试
from loop_agent_mcp.engines.executors import _write_file

try:
    path = _write_file(tmpdir, "docs/architecture/test.md", result)
    print(f"✅ 文件写入成功: {path}")
except Exception as e:
    print(f"❌ 写入失败: {e}")
    traceback.print_exc()

shutil.rmtree(tmpdir, ignore_errors=True)
