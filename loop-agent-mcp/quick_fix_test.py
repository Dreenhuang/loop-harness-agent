#!/usr/bin/env python
"""快速修复验证脚本"""
import sys
import tempfile
import shutil

sys.path.insert(0, '.')

from loop_agent_mcp.tools.dispatcher import dispatch

tmpdir = tempfile.mkdtemp(prefix='fix-test-')

print('测试1: backend database...')
r1 = dispatch('spawn_agent', {
    'agent_name': 'backend',
    'task_input': {
        'task_type': 'database',
        'model_name': 'User',
        'fields': [{'name': 'email', 'type': 'string'}, {'name': 'age', 'type': 'number'}]
    },
    'workspace': tmpdir
})
status1 = "PASS" if r1.get('status') == 'executed' else f"FAIL ({r1.get('status')})"
files1 = r1.get('files_created', [])
print(f"  结果: {status1}")
print(f"  文件: {files1}")

print('\n测试2: architect structure...')
r2 = dispatch('spawn_agent', {
    'agent_name': 'architect',
    'task_input': {'task_type': 'structure'},
    'workspace': tmpdir
})
status2 = "PASS" if r2.get('status') == 'executed' else f"FAIL ({r2.get('status')})"
files2 = r2.get('files_created', [])
print(f"  结果: {status2}")
print(f"  文件: {files2}")
if r2.get('error'):
    print(f"  错误: {r2.get('error')}")

shutil.rmtree(tmpdir, ignore_errors=True)

if status1 == "PASS" and status2 == "PASS":
    print('\n✅ 所有关键问题已修复!')
    sys.exit(0)
else:
    print('\n⚠️ 仍有问题需要处理')
    sys.exit(1)
