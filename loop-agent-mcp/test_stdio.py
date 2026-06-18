"""MCP stdio 握手 + tools/list 验证脚本。"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("G:/ai-gongju/Loop-agent/loop-agent-mcp/loop_agent_mcp/server.py").resolve()

requests = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0.1"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
]

# 启动 server.py，包根目录加入 sys.path 父目录
proc = subprocess.Popen(
    [sys.executable, str(SCRIPT)],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=str(SCRIPT.parent.parent),  # loop-agent-mcp/
    text=True,
)

# 先发 stdio 消息（每行一个 JSON）
for r in requests:
    proc.stdin.write(json.dumps(r) + "\n")
proc.stdin.flush()

# 读 stderr（非协议信息）
import threading
def drain_stderr():
    for line in proc.stderr:
        print(f"[server stderr] {line.rstrip()}")
t = threading.Thread(target=drain_stderr, daemon=True)
t.start()

# 读 stdout（JSON-RPC 响应）
import time
time.sleep(0.5)
responses = []
for _ in range(2):
    line = proc.stdout.readline()
    if not line:
        break
    responses.append(line.rstrip())

# 关闭
proc.stdin.close()
proc.terminate()
try:
    proc.wait(timeout=2)
except subprocess.TimeoutExpired:
    proc.kill()

print("=" * 60)
print("MCP stdio 握手测试")
print("=" * 60)
print(f"Server 启动命令: python {SCRIPT.name}")
print(f"CWD: {SCRIPT.parent.parent}")
print(f"发出请求: {len(requests)}")
print(f"收到响应: {len(responses)}")
print()

ok = True
if len(responses) >= 1:
    try:
        r1 = json.loads(responses[0])
        print(f"Response 1: {json.dumps(r1, ensure_ascii=False)[:300]}")
        server_name = r1.get("result", {}).get("serverInfo", {}).get("name", "")
        print(f"  server name: {server_name}")
        if server_name != "loop-harness-agent":
            print("  ❌ server name 不匹配")
            ok = False
        else:
            print("  ✅ server name OK")
    except json.JSONDecodeError as e:
        print(f"  ❌ Response 1 不是有效 JSON: {e}")
        ok = False
else:
    print("  ❌ 无响应 1")
    ok = False

if len(responses) >= 2:
    try:
        r2 = json.loads(responses[1])
        tools = r2.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        print(f"Response 2: tools/list → {len(tools)} 工具")
        for name in tool_names:
            print(f"  - {name}")
        expected = {"start_loop", "get_status", "abort_loop", "list_agents", "spawn_agent",
                    "save_blackboard", "check_artifact_completeness", "check_evidence_sufficiency",
                    "detect_deviation", "check_veto_items", "check_fusion_targets", "get_token_budget_status"}
        if set(tool_names) == expected:
            print("  ✅ 12 工具全部就位")
        else:
            missing = expected - set(tool_names)
            extra = set(tool_names) - expected
            print(f"  ❌ 工具集合不一致：缺 {missing} 多 {extra}")
            ok = False
    except json.JSONDecodeError as e:
        print(f"  ❌ Response 2 不是有效 JSON: {e}")
        ok = False
else:
    print("  ❌ 无响应 2")
    ok = False

print()
print("=" * 60)
if ok:
    print("【MCP stdio 启动 + tools/list 验证通过 ✅】")
    sys.exit(0)
print("【失败 ❌】")
sys.exit(1)
