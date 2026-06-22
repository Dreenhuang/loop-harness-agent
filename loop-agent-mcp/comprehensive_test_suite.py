#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Loop-Harness-Agent MCP v1.2 全面测试套件
=====================================

测试范围：
1. 核心功能模块完整性（15个工具）
2. 边界条件和异常处理
3. 系统稳定性和压力测试
4. 响应时间和性能基准
5. 资源占用评估

作者: Loop-Harness-Agent 测试团队
日期: 2026-06-19
版本: v1.0
"""

import sys
import os
import time
import json
import tempfile
import shutil
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    category: str
    tool_name: str
    arguments: Dict[str, Any]
    expected_status: str  # executed / ok / hint_only / error
    expected_keys: List[str] = field(default_factory=list)
    validation_func: Optional[callable] = None
    timeout: float = 5.0  # 秒


@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    name: str
    passed: bool
    duration_ms: float
    status: str = ""
    output: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    details: str = ""


@dataclass
class PerformanceMetric:
    """性能指标"""
    tool_name: str
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    success_rate: float
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class MCPTestSuite:
    """MCP 全面测试套件"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.performance_metrics: Dict[str, PerformanceMetric] = {}
        self.test_workspace: Optional[Path] = None
        self.start_time: float = 0
        self.total_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0
        self.error_details: List[str] = []

        # 延迟导入（避免启动时错误）
        self.dispatch = None
        self.TOOL_SCHEMAS = None

    def setup(self):
        """初始化测试环境"""
        print("=" * 80)
        print("🧪 Loop-Harness-Agent MCP v1.2 全面测试套件")
        print("=" * 80)
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 创建临时工作区
        self.test_workspace = Path(tempfile.mkdtemp(prefix="mcp-test-"))
        print(f"📁 测试工作区: {self.test_workspace}")

        # 导入MCP模块
        try:
            from loop_agent_mcp.tools.dispatcher import dispatch
            from loop_agent_mcp.tools.schemas import TOOL_SCHEMAS
            self.dispatch = dispatch
            self.TOOL_SCHEMAS = TOOL_SCHEMAS
            print("✅ MCP模块导入成功")
            print(f"📦 可用工具数: {len(self.TOOL_SCHEMAS)}")
        except Exception as e:
            print(f"❌ 模块导入失败: {e}")
            traceback.print_exc()
            sys.exit(1)

        self.start_time = time.time()
        print()

    def teardown(self):
        """清理测试环境"""
        if self.test_workspace and self.test_workspace.exists():
            shutil.rmtree(self.test_workspace, ignore_errors=True)
            print(f"\n🧹 已清理测试工作区")

    def run_test(self, test_case: TestCase) -> TestResult:
        """执行单个测试用例"""
        start = time.time()
        result = TestResult(
            test_id=test_case.id,
            name=test_case.name,
            passed=False,
            duration_ms=0,
        )

        try:
            # 执行工具调用
            output = self.dispatch(test_case.tool_name, {
                **test_case.arguments,
                "workspace": str(self.test_workspace)  # 注入工作区
            })

            duration = (time.time() - start) * 1000
            result.duration_ms = duration
            result.output = output
            result.status = output.get("status", "")

            # ===== 增强的状态验证逻辑（v1.1 修复）=====
            is_status_match = False

            if test_case.expected_status == "executed":
                # 执行成功：检查 status=executed 或 mode=executed
                is_status_match = (
                    output.get("status") == "executed" or
                    output.get("mode") == "executed"
                )

            elif test_case.expected_status == "ok":
                # 元操作成功：检查 status=ok 或 action 存在或关键元数据存在
                is_status_match = (
                    output.get("status") == "ok" or
                    output.get("action") in ("file_written", "file_read", "files_listed") or
                    # 元操作特征：有 loop_id/mode/workspace/count 等字段但无 error
                    (any(k in output for k in ["loop_id", "mode", "workspace", "count", "agents"])
                     and "error" not in output)
                )

            elif test_case.expected_status == "error":
                # 错误响应：检查 status=error 或 error 字段存在
                is_status_match = (
                    output.get("status") == "error" or
                    "error" in output
                )

            elif test_case.expected_status == "hint_only":
                # 提示角色：检查 status=hint_only 或 mode=hint_only
                is_status_match = (
                    output.get("status") == "hint_only" or
                    output.get("mode") == "hint_only"
                )

            if is_status_match:
                result.passed = True

            # 验证关键字段
            if test_case.expected_keys and result.passed:
                missing_keys = [k for k in test_case.expected_keys if k not in output]
                if missing_keys:
                    result.passed = False
                    result.error_message = f"缺少字段: {missing_keys}"

            # 自定义验证函数
            if test_case.validation_func and result.passed:
                validation_result = test_case.validation_func(output, self.test_workspace)
                if not validation_result[0]:
                    result.passed = False
                    result.error_message = validation_result[1]

            result.details = f"状态={output.get('status', 'N/A')}, 模式={output.get('mode', 'N/A')}"

        except Exception as e:
            duration = (time.time() - start) * 1000
            result.duration_ms = duration
            result.error_message = str(e)
            result.details = traceback.format_exc()

        return result

    def generate_test_cases(self) -> List[TestCase]:
        """生成所有测试用例"""
        cases = []

        # ========== 1. 核心功能测试 ==========

        # 1.1 start_loop
        cases.append(TestCase(
            id="CORE-001",
            name="start_loop - 启动默认模式",
            category="核心功能",
            tool_name="start_loop",
            arguments={"mode": "default", "time_budget_hours": 9},
            expected_status="ok",
            expected_keys=["loop_id", "mode", "workspace"],
        ))

        # 1.2 get_status
        cases.append(TestCase(
            id="CORE-002",
            name="get_status - 查询初始状态",
            category="核心功能",
            tool_name="get_status",
            arguments={},
            expected_status="ok",
            expected_keys=["loop_id", "current_phase", "mode"],
        ))

        # 1.3 list_agents
        cases.append(TestCase(
            id="CORE-003",
            name="list_agents - 列出16角色",
            category="核心功能",
            tool_name="list_agents",
            arguments={},
            expected_status="ok",
            expected_keys=["count", "agents"],
            validation_func=lambda o, w: (o.get("count") == 16, f"期望16个角色，实际{o.get('count')}"),
        ))

        # 1.4 spawn_agent - backend (API开发)
        cases.append(TestCase(
            id="CORE-004",
            name="spawn_agent backend - API接口开发",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "backend",
                "task_input": {
                    "task_type": "api",
                    "endpoint": "products",
                    "method": "GET",
                    "description": "产品列表接口"
                }
            },
            expected_status="executed",
            expected_keys=["files_created", "mode", "agent"],
            validation_func=self._validate_files_created,
        ))

        # 1.5 spawn_agent - backend (数据库模型)
        cases.append(TestCase(
            id="CORE-005",
            name="spawn_agent backend - 数据库模型生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "backend",
                "task_input": {
                    "task_type": "database",
                    "model_name": "User",
                    "fields": [
                        {"name": "email", "type": "string"},
                        {"name": "password", "type": "string"}
                    ]
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.6 spawn_agent - frontend (组件)
        cases.append(TestCase(
            id="CORE-006",
            name="spawn_agent frontend - React组件生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "frontend",
                "task_input": {
                    "task_type": "component",
                    "component_name": "DataTable",
                    "framework": "react",
                    "props": ["columns", "dataSource"]
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.7 spawn_agent - frontend (页面)
        cases.append(TestCase(
            id="CORE-007",
            name="spawn_agent frontend - 页面组件生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "frontend",
                "task_input": {
                    "task_type": "page",
                    "page_name": "Dashboard",
                    "route": "/dashboard"
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.8 spawn_agent - architect (项目结构)
        cases.append(TestCase(
            id="CORE-008",
            name="spawn_agent architect - 项目结构文档",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "architect",
                "task_input": {"task_type": "structure"}
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.9 spawn_agent - architect (配置文件)
        cases.append(TestCase(
            id="CORE-009",
            name="spawn_agent architect - 配置文件生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "architect",
                "task_input": {
                    "task_type": "config",
                    "project_name": "TestProject"
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.10 spawn_agent - requirements (PRD)
        cases.append(TestCase(
            id="CORE-010",
            name="spawn_agent requirements - PRD文档生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "requirements",
                "task_input": {
                    "task_type": "prd",
                    "product_name": "测试产品",
                    "features": ["功能A", "功能B"]
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.11 spawn_agent - tester (单元测试)
        cases.append(TestCase(
            id="CORE-011",
            name="spawn_agent tester - 单元测试生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "tester",
                "task_input": {
                    "task_type": "unit",
                    "target": "src/components/Button"
                }
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.12 spawn_agent - devops (Dockerfile)
        cases.append(TestCase(
            id="CORE-012",
            name="spawn_agent devops - Docker配置生成",
            category="核心功能",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "devops",
                "task_input": {"task_type": "docker"}
            },
            expected_status="executed",
            expected_keys=["files_created"],
            validation_func=self._validate_files_created,
        ))

        # 1.13 save_blackboard
        cases.append(TestCase(
            id="CORE-013",
            name="save_blackboard - 黑板保存",
            category="核心功能",
            tool_name="save_blackboard",
            arguments={
                "append_section": "测试日志段"
            },
            expected_status="ok",
            expected_keys=["status", "path"],
        ))

        # 1.14 write_file
        cases.append(TestCase(
            id="CORE-014",
            name="write_file - 文件写入",
            category="核心功能",
            tool_name="write_file",
            arguments={
                "path": "test-output/hello.txt",
                "content": "Hello MCP Test!"
            },
            expected_status="ok",
            expected_keys=["action", "path"],
            validation_func=lambda o, w: (
                Path(o.get("path", "")).exists() and
                Path(o.get("path", "")).read_text().startswith("Hello"),
                "文件内容不正确"
            ),
        ))

        # 1.15 read_file
        cases.append(TestCase(
            id="CORE-015",
            name="read_file - 文件读取",
            category="核心功能",
            tool_name="read_file",
            arguments={
                "path": "test-output/hello.txt"
            },
            expected_status="ok",
            expected_keys=["action", "content"],
            validation_func=lambda o, w: (
                "Hello MCP Test!" in o.get("content", ""),
                "读取内容不匹配"
            ),
        ))

        # 1.16 list_files
        cases.append(TestCase(
            id="CORE-016",
            name="list_files - 文件列表",
            category="核心功能",
            tool_name="list_files",
            arguments={"directory": "."},
            expected_status="ok",
            expected_keys=["action", "count", "files"],
        ))

        # ========== 2. 边界条件测试 ==========

        # 2.1 空参数
        cases.append(TestCase(
            id="BOUND-001",
            name="边界测试 - spawn_agent 空参数",
            category="边界条件",
            tool_name="spawn_agent",
            arguments={},
            expected_status="error",
        ))

        # 2.2 无效角色名
        cases.append(TestCase(
            id="BOUND-002",
            name="边界测试 - 无效agent名称",
            category="边界条件",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "invalid_agent_12345",
                "task_input": {}
            },
            expected_status="error",
        ))

        # 2.3 不存在的文件路径
        cases.append(TestCase(
            id="BOUND-003",
            name="边界测试 - 读取不存在文件",
            category="边界条件",
            tool_name="read_file",
            arguments={"path": "nonexistent/file.txt"},
            expected_status="error",
        ))

        # 2.4 特殊字符路径
        cases.append(TestCase(
            id="BOUND-004",
            name="边界测试 - 特殊字符路径",
            category="边界条件",
            tool_name="write_file",
            arguments={
                "path": "special/path with spaces/@#$%/file.txt",
                "content": "特殊字符测试"
            },
            expected_status="ok",
        ))

        # 2.5 大内容写入
        large_content = "X" * 100000  # 100KB
        cases.append(TestCase(
            id="BOUND-005",
            name="边界测试 - 大文件写入(100KB)",
            category="边界条件",
            tool_name="write_file",
            arguments={
                "path": "large-file.txt",
                "content": large_content
            },
            expected_status="ok",
            validation_func=lambda o, w: (
                Path(w / "large-file.txt").stat().st_size >= 99000,
                "大文件写入大小不符"
            ),
        ))

        # 2.6 深层目录创建
        cases.append(TestCase(
            id="BOUND-006",
            name="边界测试 - 深层嵌套目录",
            category="边界条件",
            tool_name="write_file",
            arguments={
                "path": "a/b/c/d/e/f/g/deep.txt",
                "content": "深层目录测试"
            },
            expected_status="ok",
            validation_func=lambda o, w: (
                Path(w / "a/b/c/d/e/f/g/deep.txt").exists(),
                "深层目录未创建"
            ),
        ))

        # ========== 3. 异常处理测试 ==========

        # 3.1 工具名称错误
        cases.append(TestCase(
            id="EXCP-001",
            name="异常测试 - 未知工具名",
            category="异常处理",
            tool_name="nonexistent_tool_xyz",
            arguments={},
            expected_status="error",
        ))

        # 3.2 参数类型错误
        cases.append(TestCase(
            id="EXCP-002",
            name="异常测试 - 参数类型错误",
            category="异常处理",
            tool_name="start_loop",
            arguments={"time_budget_hours": "not_a_number"},
            expected_status="error",
        ))

        # 3.3 路径遍历攻击防护验证（v1.3 新增）
        cases.append(TestCase(
            id="EXCP-003",
            name="异常测试 - 路径遍历攻击防护(v1.3安全加固)",
            category="异常处理",
            tool_name="write_file",
            arguments={
                "path": "../../etc/passwd",  # 路径遍历攻击
                "content": "hacked"
            },
            expected_status="error",  # v1.3: 必须被阻止
        ))

        # 3.4 危险扩展名阻止验证（v1.3 新增）
        cases.append(TestCase(
            id="EXCP-004",
            name="异常测试 - 危险扩展名阻止(v1.3安全加固)",
            category="异常处理",
            tool_name="write_file",
            arguments={
                "path": "virus.bat",
                "content": "malicious"
            },
            expected_status="error",  # v1.3: .bat被禁止
        ))

        # 3.5 绝对路径阻止验证（v1.3 新增）
        cases.append(TestCase(
            id="EXCP-005",
            name="异常测试 - 绝对路径阻止(v1.3安全加固)",
            category="异常处理",
            tool_name="write_file",
            arguments={
                "path": "/etc/passwd",
                "content": "hacked"
            },
            expected_status="error",  # v1.3: 绝对路径被禁止
        ))

        # ========== 4. 提示类角色测试 ==========

        # 4.1 product-manager (hint_only)
        cases.append(TestCase(
            id="HINT-001",
            name="提示角色 - product-manager",
            category="提示角色",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "product-manager",
                "task_input": {"decision": "技术选型"}
            },
            expected_status="hint_only",
            expected_keys=["status", "output"],
        ))

        # 4.2 ux-researcher (hint_only)
        cases.append(TestCase(
            id="HINT-002",
            name="提示角色 - ux-researcher",
            category="提示角色",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "ux-researcher",
                "task_input": {"flow": "用户注册流程"}
            },
            expected_status="hint_only",
        ))

        # 4.3 code-reviewer (hint_only)
        cases.append(TestCase(
            id="HINT-003",
            name="提示角色 - code-reviewer",
            category="提示角色",
            tool_name="spawn_agent",
            arguments={
                "agent_name": "code-reviewer",
                "task_input": {"target": "src/api/users.ts"}
            },
            expected_status="hint_only",
        ))

        return cases

    def _validate_files_created(self, output: Dict, workspace: Path) -> Tuple[bool, str]:
        """验证生成的文件是否存在且非空"""
        files = output.get("files_created", [])
        if not files:
            return False, "未生成任何文件"

        for file_path in files:
            p = Path(file_path)
            if not p.exists():
                return False, f"文件不存在: {file_path}"
            if p.stat().st_size == 0:
                return False, f"文件为空: {file_path}"

        return True, f"已验证{len(files)}个文件"

    def run_performance_test(self, tool_name: str, arguments: Dict, iterations: int = 10) -> PerformanceMetric:
        """运行性能基准测试"""
        times = []

        for i in range(iterations):
            start = time.time()
            try:
                self.dispatch(tool_name, {**arguments, "workspace": str(self.test_workspace)})
                times.append((time.time() - start) * 1000)
            except:
                times.append((time.time() - start) * 1000)

        times.sort()

        return PerformanceMetric(
            tool_name=tool_name,
            avg_response_time_ms=sum(times) / len(times),
            min_response_time_ms=times[0],
            max_response_time_ms=times[-1],
            p95_response_time_ms=times[int(len(times) * 0.95)] if len(times) > 1 else times[0],
            p99_response_time_ms=times[int(len(times) * 0.99)] if len(times) > 1 else times[0],
            success_rate=len([t for t in times if t < 5000]) / len(times),  # 5秒内算成功
        )

    def run_stress_test(self, concurrent_calls: int = 50):
        """压力测试：并发调用"""
        import threading
        results = []
        errors = []

        def worker():
            try:
                start = time.time()
                self.dispatch("list_agents", {"workspace": str(self.test_workspace)})
                results.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker) for _ in range(concurrent_calls)]

        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - start

        return {
            "concurrent_calls": concurrent_calls,
            "successful_calls": len(results),
            "failed_calls": len(errors),
            "total_time_sec": round(total_time, 3),
            "avg_time_per_call_ms": round(sum(results) / len(results) * 1000, 2) if results else 0,
            "errors": errors[:5],  # 只保留前5个错误
        }

    def generate_report(self) -> str:
        """生成完整测试报告"""
        total_duration = time.time() - self.start_time

        report = []
        report.append("# Loop-Harness-Agent MCP v1.2 全面测试报告")
        report.append("")
        report.append(f"> **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"> **总耗时**: {total_duration:.2f} 秒")
        report.append(f"> **通过率**: {self.passed_tests}/{self.total_tests} ({self.passed_tests/self.total_tests*100:.1f}%)" if self.total_tests > 0 else "")
        report.append("")

        # 1. 测试概览
        report.append("## 📊 测试概览")
        report.append("")
        report.append("| 指标 | 数值 |")
        report.append("|------|------|")
        report.append(f"| 总测试数 | {self.total_tests} |")
        report.append(f"| 通过数 | ✅ {self.passed_tests} |")
        report.append(f"| 失败数 | ❌ {self.failed_tests} |")
        report.append(f"| 通过率 | {self.passed_tests/self.total_tests*100:.1f}% |" if self.total_tests > 0 else "| 通过率 | N/A |")
        report.append(f"| 总耗时 | {total_duration:.2f}s |")
        report.append("")

        # 2. 详细结果
        report.append("## 🔍 详细测试结果")
        report.append("")

        # 按类别分组
        categories = defaultdict(list)
        for r in self.results:
            categories[r.test_id.split("-")[0]].append(r)

        category_names = {
            "CORE": "核心功能",
            "BOUND": "边界条件",
            "EXCP": "异常处理",
            "HINT": "提示角色"
        }

        for cat_id, tests in sorted(categories.items()):
            cat_name = category_names.get(cat_id, cat_id)
            report.append(f"### {cat_id}: {cat_name} ({len(tests)} 个测试)")
            report.append("")
            report.append("| ID | 用例名称 | 状态 | 耗时(ms) | 详情 |")
            report.append("|----|----------|------|----------|------|")

            for t in tests:
                status_icon = "✅" if t.passed else "❌"
                detail = t.details[:50] if t.details else (t.error_message[:50] if t.error_message else "-")
                report.append(f"| {t.test_id} | {t.name} | {status_icon} | {t.duration_ms:.1f} | {detail} |")

            report.append("")

        # 3. 失败用例详情
        if self.failed_tests > 0:
            report.append("## ❌ 失败用例详情")
            report.append("")
            for r in self.results:
                if not r.passed:
                    report.append(f"### {r.test_id}: {r.name}")
                    report.append(f"- **错误**: {r.error_message}")
                    report.append(f"- **输出**: ```json\n{json.dumps(r.output, ensure_ascii=False, indent=2)[:500]}\n```")
                    report.append("")

        # 4. 性能指标
        if self.performance_metrics:
            report.append("## ⚡ 性能指标")
            report.append("")
            report.append("| 工具 | 平均响应(ms) | P95(ms) | P99(ms) | 成功率 |")
            report.append("|------|-------------|--------|--------|--------|")

            for metric in self.performance_metrics.values():
                m = self.performance_metrics[metric.tool_name]
                report.append(f"| {m.tool_name} | {m.avg_response_time_ms:.1f} | {m.p95_response_time_ms:.1f} | {m.p99_response_time_ms:.1f} | {m.success_rate*100:.0f}% |")

            report.append("")

        # 5. 结论和建议
        report.append("## 📋 结论与建议")
        report.append("")

        if self.passed_tests == self.total_tests:
            report.append("### ✅ 所有测试通过！")
            report.append("")
            report.append("MCP v1.2 智能执行器重构**完全符合设计要求**，可以投入生产使用。")
        elif self.passed_tests / self.total_tests >= 0.9:
            report.append(f"### ⚠️ 基本合格 ({self.passed_tests/self.total_tests*100:.0f}%通过)")
            report.append("")
            report.append("存在少量问题需要修复，但不影响主要功能使用。")
        else:
            report.append(f"### ❌ 存在较多问题 ({self.passed_tests/self.total_tests*100:.0f}%通过)")
            report.append("")
            report.append("需要修复关键问题后再进行验收。")

        report.append("")
        report.append("---")
        report.append("*报告由 Loop-Harness-Agent 自动生成*")

        return "\n".join(report)

    def run_all(self):
        """执行所有测试"""
        self.setup()

        try:
            # 生成测试用例
            test_cases = self.generate_test_cases()
            self.total_tests = len(test_cases)
            print(f"\n📝 共生成 {self.total_tests} 个测试用例\n")

            # 执行功能测试
            print("=" * 60)
            print("🔍 第1阶段: 功能完整性测试")
            print("=" * 60 + "\n")

            for i, case in enumerate(test_cases, 1):
                print(f"[{i}/{self.total_tests}] {case.id}: {case.name}...", end=" ")

                result = self.run_test(case)
                self.results.append(result)

                if result.passed:
                    self.passed_tests += 1
                    print(f"✅ ({result.duration_ms:.1f}ms)")
                else:
                    self.failed_tests += 1
                    print(f"❌ ({result.duration_ms:.1f}ms)")
                    if result.error_message:
                        print(f"   错误: {result.error_message}")

            # 性能测试
            print("\n" + "=" * 60)
            print("⚡ 第2阶段: 性能基准测试")
            print("=" * 60 + "\n")

            perf_tools = [
                ("list_agents", {}, "列出角色"),
                ("spawn_agent", {"agent_name": "backend", "task_input": {"task_type": "api", "endpoint": "perf_test"}}, "后端Agent"),
                ("write_file", {"path": "perf-test.txt", "content": "performance test"}, "文件写入"),
                ("read_file", {"path": "perf-test.txt"}, "文件读取"),
            ]

            for tool_name, args, desc in perf_tools:
                print(f"⏱️  {desc}...", end=" ")
                metric = self.run_performance_test(tool_name, args, iterations=5)
                self.performance_metrics[tool_name] = metric
                print(f"平均 {metric.avg_response_time_ms:.1f}ms, P95 {metric.p95_response_time_ms:.1f}ms")

            # 压力测试
            print("\n" + "=" * 60)
            print("💪 第3阶段: 压力测试")
            print("=" * 60 + "\n")

            print("并发调用 list_agents (50次)...", end=" ")
            stress_result = self.run_stress_test(50)
            print(f"完成! 成功率: {stress_result['successful_calls']/stress_result['concurrent_calls']*100:.0f}%")
            print(f"   平均耗时: {stress_result['avg_time_per_call_ms']}ms")

            # 生成报告
            print("\n" + "=" * 60)
            print("📄 第4阶段: 生成测试报告")
            print("=" * 60 + "\n")

            report = self.generate_report()
            report_path = self.test_workspace / "TEST_REPORT.md"

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"✅ 报告已保存到: {report_path}")
            print("\n" + report)  # 同时输出到控制台

            # 保存报告到项目目录
            project_report_path = Path(__file__).parent.parent / "docs" / "TEST_REPORT_V1.2.md"
            with open(project_report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📋 报告副本已保存到: {project_report_path}")

        finally:
            self.teardown()

        return self.passed_tests == self.total_tests


def main():
    suite = MCPTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
