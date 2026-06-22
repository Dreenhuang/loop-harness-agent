"""Agent 执行引擎：实现各角色的实际业务逻辑。

融合 v1.2 强制要求：
- spawn_agent 必须执行实际开发操作
- 返回 files_created / output / execution_status
- 区分 executed（已执行）和 hint_only（仅提示）

v1.3 安全加固：
- 所有文件操作经 security.validate_path 校验
- 所有标识符经 security.sanitize_identifier 清洗
- 所有内容经 security.validate_content 校验大小
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.config import find_workspace_root
from loop_agent_mcp.core.security import (
    sanitize_identifier,
    validate_content,
    validate_path,
)
from loop_agent_mcp.core.state import StateManager


# ---- 文件操作工具函数 ----


def _write_file(workspace, relative_path: str, content: str) -> str:
    """写入文件并返回完整路径（v1.3 安全加固版）。"""
    if isinstance(workspace, str):
        workspace = Path(workspace)

    # v1.3 安全加固：路径验证 + 内容大小校验
    full_path = validate_path(workspace, relative_path, operation="write")
    validate_content(content)

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return str(full_path)


def _read_file(workspace, relative_path: str) -> str:
    """读取文件内容（v1.3 安全加固版）。"""
    if isinstance(workspace, str):
        workspace = Path(workspace)

    # v1.3 安全加固：路径验证（含工作区边界）
    full_path = validate_path(workspace, relative_path, operation="read")
    if not full_path.is_file():
        raise FileNotFoundError(f"文件不存在: {full_path}")

    return full_path.read_text(encoding="utf-8")


def _list_files(workspace, directory: str = ".") -> list[str]:
    """列出目录下所有文件（v1.3 安全加固版）。"""
    if isinstance(workspace, str):
        workspace = Path(workspace)

    # v1.3 安全加固：路径验证
    dir_path = validate_path(workspace, directory, operation="list")
    if not dir_path.is_dir():
        return []

    # v1.3 限制返回数量，防止 DoS
    files: list[str] = []
    for f in dir_path.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(workspace)))
            if len(files) >= 500:
                break
    return files


# ---- 各角色执行器 ----


def execute_backend_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行后端开发任务：API开发、数据库、服务逻辑。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "api")

    if task_type == "api":
        # API 接口开发
        endpoint = sanitize_identifier(task_input.get("endpoint", "example"))
        method = task_input.get("method", "GET")
        description = task_input.get("description", "")

        api_code = _generate_api_code(endpoint, method, description)
        file_path = _write_file(
            workspace,
            f"src/api/{endpoint}.ts",
            api_code
        )
        files_created.append(file_path)

        # 同时生成类型定义
        type_code = _generate_api_types(endpoint, task_input.get("schema", {}))
        type_path = _write_file(
            workspace,
            f"src/types/{endpoint}.ts",
            type_code
        )
        files_created.append(type_path)

    elif task_type == "database":
        # 数据库模型/迁移
        model_name = sanitize_identifier(task_input.get("model_name", "Example"))
        fields = task_input.get("fields", [])

        model_code = _generate_database_model(model_name, fields)
        file_path = _write_file(
            workspace,
            f"src/models/{model_name.lower()}.ts",
            model_code
        )
        files_created.append(file_path)

    elif task_type == "service":
        # 业务逻辑层
        service_name = sanitize_identifier(task_input.get("service_name", "ExampleService"))
        methods = task_input.get("methods", [])

        service_code = _generate_service(service_name, methods)
        file_path = _write_file(
            workspace,
            f"src/services/{service_name.lower()}.ts",
            service_code
        )
        files_created.append(file_path)

    # Task 4.2: 质量评估 - 集成代码质量打分
    quality_score = _assess_quality(files_created, task_type)

    return {
        "status": "executed",
        "agent": "backend",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ 后端任务完成：生成 {len(files_created)} 个文件",
        "timestamp": time.time(),
        "quality_score": quality_score,
    }


def _assess_quality(files_created: list[str], task_type: str) -> dict[str, Any]:
    """Task 4.2: 对生成的文件进行质量评估。

    Args:
        files_created: 创建的文件路径列表
        task_type: 任务类型

    Returns:
        包含 score/grade/issues 的质量评估字典
    """
    score = 100
    issues: list[str] = []

    # 1. 文件数量检查
    if not files_created:
        score -= 50
        issues.append("未生成任何文件")
    elif len(files_created) < 2:
        score -= 20
        issues.append("生成文件数量偏少，缺少配套类型/测试")

    # 2. 文件存在性检查
    for fp in files_created:
        if not Path(fp).exists():
            score -= 15
            issues.append(f"文件未实际创建: {fp}")

    # 3. 任务类型专项检查
    if task_type == "api" and len(files_created) < 2:
        score -= 10
        issues.append("API任务应同时生成接口文件和类型定义文件")

    # 4. 等级评定
    score = max(0, score)
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": score,
        "grade": grade,
        "issues": issues,
        "files_evaluated": len(files_created),
        "task_type": task_type,
    }


def execute_frontend_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行前端开发任务：组件、页面、样式。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "component")

    if task_type == "component":
        # React/Vue 组件
        component_name = sanitize_identifier(task_input.get("component_name", "ExampleComponent"))
        framework = task_input.get("framework", "react")
        props = task_input.get("props", [])

        component_code = _generate_component(component_name, framework, props)
        file_path = _write_file(
            workspace,
            f"src/components/{component_name}.{_get_ext(framework)}",
            component_code
        )
        files_created.append(file_path)

        # 生成样式文件
        style_code = _generate_component_styles(component_name)
        style_path = _write_file(
            workspace,
            f"src/components/{component_name}.module.css",
            style_code
        )
        files_created.append(style_path)

    elif task_type == "page":
        # 页面组件
        page_name = sanitize_identifier(task_input.get("page_name", "ExamplePage"))
        route = task_input.get("route", "/example")

        page_code = _generate_page(page_name, route)
        file_path = _write_file(
            workspace,
            f"src/pages/{page_name}.tsx",
            page_code
        )
        files_created.append(file_path)

    elif task_type == "hooks":
        # 自定义Hook
        hook_name = sanitize_identifier(task_input.get("hook_name", "useExample"))
        logic = task_input.get("logic", "state management")

        hook_code = _generate_hook(hook_name, logic)
        file_path = _write_file(
            workspace,
            f"src/hooks/{hook_name}.ts",
            hook_code
        )
        files_created.append(file_path)

    return {
        "status": "executed",
        "agent": "frontend",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ 前端任务完成：生成 {len(files_created)} 个文件",
        "timestamp": time.time(),
        "quality_score": _assess_quality(files_created, task_type),
    }


def execute_architect_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行架构设计任务：技术选型、目录结构、配置文件。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "structure")

    if task_type == "structure":
        # 项目目录结构
        structure = task_input.get("structure", {})
        structure_md = _generate_structure_doc(structure)
        file_path = _write_file(
            workspace,
            "docs/architecture/项目结构.md",
            structure_md
        )
        files_created.append(file_path)

        # 生成 tsconfig.json
        tsconfig = _generate_tsconfig()
        config_path = _write_file(workspace, "tsconfig.json", tsconfig)
        files_created.append(config_path)

    elif task_type == "config":
        # 配置文件（package.json, .env.example等）
        project_name = sanitize_identifier(task_input.get("project_name", "loop-agent-project"))
        dependencies = task_input.get("dependencies", {})

        package_json = _generate_package_json(project_name, dependencies)
        file_path = _write_file(workspace, "package.json", package_json)
        files_created.append(file_path)

        env_example = _generate_env_example()
        env_path = _write_file(workspace, ".env.example", env_example)
        files_created.append(env_path)

    elif task_type == "api_spec":
        # API 规范文档
        endpoints = task_input.get("endpoints", [])
        api_spec = _generate_api_spec(endpoints)
        file_path = _write_file(
            workspace,
            "docs/api/API-Spec.md",
            api_spec
        )
        files_created.append(file_path)

    return {
        "status": "executed",
        "agent": "architect",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ 架构任务完成：生成 {len(files_created)} 个文件",
        "timestamp": time.time(),
        "quality_score": _assess_quality(files_created, task_type),
    }


def execute_requirements_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行需求分析任务：PRD、用户故事、验收标准。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "prd")

    if task_type == "prd":
        # 产品需求文档
        product_name = task_input.get("product_name", "产品名称")
        features = task_input.get("features", [])
        user_stories = task_input.get("user_stories", [])

        prd_content = _generate_prd(product_name, features, user_stories)
        file_path = _write_file(
            workspace,
            "docs/prd/Product-Spec.md",
            prd_content
        )
        files_created.append(file_path)

    elif task_type == "user_stories":
        # 用户故事列表
        stories = task_input.get("stories", [])
        stories_content = _generate_user_stories(stories)
        file_path = _write_file(
            workspace,
            "docs/prd/User-Stories.md",
            stories_content
        )
        files_created.append(file_path)

    elif task_type == "acceptance_criteria":
        # 验收标准
        criteria = task_input.get("criteria", [])
        ac_content = _generate_acceptance_criteria(criteria)
        file_path = _write_file(
            workspace,
            "docs/prd/Acceptance-Criteria.md",
            ac_content
        )
        files_created.append(file_path)

    return {
        "status": "executed",
        "agent": "requirements",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ 需求分析完成：生成 {len(files_created)} 个文档",
        "timestamp": time.time(),
        "quality_score": _assess_quality(files_created, task_type),
    }


def execute_tester_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行测试任务：单元测试、集成测试、E2E测试。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "unit")

    target_file = task_input.get("target", "src/components/Example")
    test_framework = task_input.get("framework", "vitest")

    if task_type == "unit":
        # 单元测试
        unit_test = _generate_unit_test(target_file, test_framework)
        file_path = _write_file(
            workspace,
            f"{target_file}.test.ts",
            unit_test
        )
        files_created.append(file_path)

    elif task_type == "integration":
        # 集成测试
        integration_test = _generate_integration_test(target_file)
        file_path = _write_file(
            workspace,
            f"{target_file}.integration.test.ts",
            integration_test
        )
        files_created.append(file_path)

    elif task_type == "e2e":
        # E2E测试
        e2e_test = _generate_e2e_test(target_file)
        file_path = _write_file(
            workspace,
            f"e2e/{Path(target_file).name}.spec.ts",
            e2e_test
        )
        files_created.append(file_path)

    return {
        "status": "executed",
        "agent": "tester",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ 测试任务完成：生成 {len(files_created)} 个测试文件",
        "timestamp": time.time(),
        "quality_score": _assess_quality(files_created, task_type),
    }


def execute_devops_agent(task_input: dict[str, Any]) -> dict[str, Any]:
    """执行DevOps任务：部署脚本、CI/CD配置、Dockerfile。"""
    workspace = Path(StateManager.get().state.workspace or find_workspace_root())
    files_created: list[str] = []

    task_type = task_input.get("task_type", "deploy")

    if task_type == "docker":
        # Dockerfile
        dockerfile = _generate_dockerfile(task_input)
        file_path = _write_file(workspace, "Dockerfile", dockerfile)
        files_created.append(file_path)

        docker_compose = _generate_docker_compose()
        compose_path = _write_file(workspace, "docker-compose.yml", docker_compose)
        files_created.append(compose_path)

    elif task_type == "ci_cd":
        # CI/CD配置
        platform = task_input.get("platform", "github")
        ci_config = _generate_ci_cd(platform)
        file_path = _write_file(
            workspace,
            f".github/workflows/ci.yml" if platform == "github" else ".gitlab-ci.yml",
            ci_config
        )
        files_created.append(file_path)

    elif task_type == "deploy_script":
        # 部署脚本
        deploy_script = _generate_deploy_script(task_input)
        file_path = _write_file(workspace, "scripts/deploy.sh", deploy_script)
        files_created.append(file_path)

    return {
        "status": "executed",
        "agent": "devops",
        "task_type": task_type,
        "files_created": files_created,
        "output": f"✅ DevOps任务完成：生成 {len(files_created)} 个配置文件",
        "timestamp": time.time(),
        "quality_score": _assess_quality(files_created, task_type),
    }


# ---- 代码生成辅助函数 ----


def _generate_api_code(endpoint: str, method: str, description: str) -> str:
    """生成API接口代码模板。"""
    return f'''/**
 * {description}
 * Method: {method}
 * Endpoint: /api/{endpoint}
 */
import {{ request }} from '@/utils/http';

export interface {endpoint.capitalize()}Params {{
  // TODO: 定义请求参数
  [key: string]: any;
}}

export interface {endpoint.capitalize()}Response {{
  // TODO: 定义响应数据结构
  [key: string]: any;
}}

export async function {endpoint}(params?: {endpoint.capitalize()}Params): Promise<{endpoint.capitalize()}Response> {{
  return request<{endpoint.capitalize()}Response>({{
    url: `/api/{endpoint}`,
    method: '{method}',
    data: params,
  }});
}}

export default {endpoint};
'''


def _generate_api_types(endpoint: str, schema: dict) -> str:
    """生成API类型定义。"""
    return f'''/**
 * {endpoint} 相关类型定义
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

// 请求参数类型
export interface {endpoint.capitalize()}Request {{
  id?: string;
  // 根据实际需求补充字段
}}

// 响应数据类型
export interface {endpoint.capitalize()}Data {{
  id: string;
  createdAt: string;
  updatedAt: string;
}}

// 列表响应
export interface {endpoint.capitalize()}ListResponse {{
  data: {endpoint.capitalize()}Data[];
  total: number;
  page: number;
  pageSize: number;
}}
'''


def _generate_database_model(model_name: str, fields: list) -> str:
    """生成数据库模型代码。"""
    # 使用普通字符串拼接避免 f-string 嵌套冲突
    field_lines = []
    for field_item in fields:
        name = field_item.get('name', 'field')
        type_ = field_item.get('type', 'string')
        field_lines.append(f"  {name}: {type_};")
    fields_str = "\n  ".join(field_lines)

    return '''/**
 * ''' + model_name + ''' 模型
 * 自动生成于 ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''
 */

export interface ''' + model_name + ''' {
''' + fields_str + '''

  id: string;
  createdAt: Date;
  updatedAt: Date;
}

export class ''' + model_name + '''Model {
  static tableName = "''' + model_name.lower() + '''s";

  static async findById(id: string): Promise<''' + model_name + ''' | null> {
    // TODO: 实现数据库查询
    return null;
  }

  static async findAll(): Promise<''' + model_name + '''[]> {
    // TODO: 实现列表查询
    return [];
  }
}
'''


def _generate_service(service_name: str, methods: list) -> str:
    """生成服务层代码。"""
    methods_str = ""
    for m in (methods or ["list", "create", "update", "delete"]):
        methods_str += f'''
  async {m}(params?: any) {{
    // TODO: 实现 {m} 方法
    return {{}};
  }}

'''
    # 构建 service 类体
    class_body = methods_str

    return f'''/**
 * {service_name} 服务层
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

export class {service_name} {{
{class_body}
}}

export default new {service_name}();
'''


def _generate_component(name: str, framework: str, props: list) -> str:
    """生成前端组件代码。"""
    props_interface = ",\n  ".join([f"  {p}: {p}Type;" for p in (props or [])]) or "  // 无props"
    props_list = ", ".join(props or ["children"])

    # 使用普通字符串拼接而非 f-string（避免 JSX 花括号冲突）
    return '''/**
 * ''' + name + ''' 组件
 * 框架: ''' + framework + '''
 * 自动生成于 ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''
 */

import React from 'react';
import styles from './''' + name + '''.module.css';

interface ''' + name + '''Props {
''' + props_interface + '''
}

export const ''' + name + ''': React.FC<''' + name + '''Props> = (''' + props_list + ''') => {
  return (
    <div className={styles.container}>
      {/* TODO: 实现 ''' + name + ''' 组件内容 */}
      <h2>''' + name + '''</h2>
    </div>
  );
};

export default ''' + name + ''';
'''


def _generate_component_styles(name: str) -> str:
    """生成组件样式。"""
    return f'''/**
 * {name} 组件样式
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

.container {{
  padding: 16px;
  border-radius: 8px;
  background-color: #ffffff;
}}

h2 {{
  margin: 0 0 16px 0;
  color: #333;
}}
'''


def _generate_page(name: str, route: str) -> str:
    """生成页面组件。"""
    return '''/**
 * ''' + name + ''' 页面
 * 路由: ''' + route + '''
 * 自动生成于 ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''
 */

import React from 'react';

const ''' + name + ''': React.FC = () => {
  return (
    <div>
      <h1>''' + name + '''</h1>
      {/* TODO: 实现页面内容 */}
    </div>
  );
};

export default ''' + name + ''';
'''


def _generate_hook(name: str, logic: str) -> str:
    """生成自定义Hook。"""
    return '''/**
 * ''' + name + ''' Hook
 * 功能: ''' + logic + '''
 * 自动生成于 ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''
 */

import { useState, useEffect, useCallback } from 'react';

export function ''' + name + '''() {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // TODO: 实现 ''' + logic + ''' 逻辑

  return {
    state,
    loading,
    error,
    // TODO: 暴露必要的操作方法
  };
}

export default ''' + name + ''';
'''


def _generate_structure_doc(structure: dict) -> str:
    """生成项目结构文档。"""
    default_structure = {
        "src/": {
            "api/": "API 接口层",
            "components/": "通用组件",
            "pages/": "页面组件",
            "hooks/": "自定义 Hooks",
            "services/": "业务逻辑层",
            "models/": "数据模型",
            "types/": "TypeScript 类型定义",
            "utils/": "工具函数"
        },
        "docs/": {
            "prd/": "需求文档",
            "api/": "API 文档",
            "architecture/": "架构文档"
        },
        "tests/": "测试文件"
    }

    structure_json = json.dumps(structure or default_structure, indent=2)

    return '''# 项目目录结构

> 自动生成于 ''' + time.strftime('%Y-%m-%d %H:%M:%S') + '''

```
''' + structure_json + '''
```

## 目录说明

| 目录 | 用途 |
|------|------|
| src/api | 后端 API 接口封装 |
| src/components | 可复用 UI 组件 |
| src/pages | 页面级组件 |
| src/hooks | 自定义 React Hooks |
| src/services | 业务逻辑处理 |
| docs/prd | 产品需求文档 |
| tests | 单元/集成/E2E 测试 |
'''


def _generate_tsconfig() -> str:
    """生成TypeScript配置。"""
    return json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True,
            "baseUrl": ".",
            "paths": {
                "@/*": ["src/*"]
            }
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}]
    }, indent=2)


def _generate_package_json(project_name: str, dependencies: dict) -> str:
    """生成package.json。"""
    return json.dumps({
        "name": project_name,
        "version": "1.0.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "test": "vitest",
            "test:e2e": "playwright test",
            "lint": "eslint src --ext .ts,.tsx",
            "format": "prettier --write 'src/**/*.{ts,tsx,css}'"
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            **(dependencies or {})
        },
        "devDependencies": {
            "@types/react": "^18.3.12",
            "@types/react-dom": "^18.3.1",
            "@typescript-eslint/eslint-plugin": "^7.0.0",
            "@typescript-eslint/parser": "^7.0.0",
            "@vitejs/plugin-react": "^4.3.4",
            "eslint": "^8.57.0",
            "prettier": "^3.4.2",
            "typescript": "^5.6.3",
            "vite": "^6.0.0",
            "vitest": "^2.1.8"
        }
    }, indent=2)


def _generate_env_example() -> str:
    """生成环境变量示例。"""
    return '''# 环境变量配置
# 复制此文件为 .env 并填写实际值

# API 基础地址
VITE_API_BASE_URL=http://localhost:3000/api

# 应用标题
VITE_APP_TITLE=Loop Agent Project

# 功能开关
VITE_ENABLE_DEBUG=false
VITE_ENABLE_MOCK=true
'''


def _generate_api_spec(endpoints: list) -> str:
    """生成API规范文档。"""
    endpoints_table = "\n".join([
        f"| {e.get('method', 'GET')} | `{e.get('path', '/')}` | {e.get('description', '')} |"
        for e in (endpoints or [])
    ]) or "| - | - | - |"

    return f'''# API 接口规范

> 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}

## 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: Bearer Token
- **Content-Type**: application/json

## 接口列表

| Method | Path | Description |
|--------|------|-------------|
{endpoints_table}

## 通用响应格式

```json
{{
  "code": 0,
  "message": "success",
  "data": {{}},
  "timestamp": 1234567890
}}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 未授权 |
| 1003 | 资源不存在 |
| 5000 | 服务器内部错误 |
'''


def _generate_prd(product_name: str, features: list, user_stories: list) -> str:
    """生成PRD文档。"""
    features_list = "\n".join([f"- {f}" for f in (features or ["功能1", "功能2"])])
    stories_list = "\n".join([
        f"### {s.get('title', '故事')}\n\n**作为** {s.get('role', '用户')}\n\n**我想** {s.get('want', '做某事')}\n\n**以便** {s.get('benefit', '获得价值')}\n"
        for s in (user_stories or [])
    ]) or "暂无用户故事"

    return f'''# 产品需求文档 (PRD) - {product_name}

> 版本: v1.0.0
> 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
> 状态: Draft

## 1. 产品概述

{product_name} 是一个基于 Loop-Harness-Agent 开发的项目。

## 2. 核心功能

{features_list}

## 3. 用户故事

{stories_list}

## 4. 验收标准

- [ ] 所有核心功能可正常使用
- [ ] 通过全部自动化测试
- [ ] 性能指标达标（P95 < 300ms）
- [ ] 安全审计通过

## 5. 技术约束

- 前端框架: React 18 + TypeScript
- 后端框架: Node.js + Express/Fastify
- 数据库: PostgreSQL / SQLite
- 部署方式: Docker + Nginx
'''


def _generate_user_stories(stories: list) -> str:
    """生成用户故事文档。"""
    lines: list[str] = []
    lines.append("# 用户故事列表")
    lines.append("")
    lines.append(f"> 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    story_items: list[str] = []
    for i, s in enumerate(stories or []):
        title = s.get("title", f"故事{i+1}")
        role = s.get("role", "用户")
        want = s.get("want", "")
        benefit = s.get("benefit", "")
        priority = s.get("priority", "P2")
        acceptance = s.get("acceptance", "TBD")
        story_items.append(
            f"## {i+1}. {title}\n\n"
            f"- **角色**: {role}\n"
            f"- **期望**: {want}\n"
            f"- **价值**: {benefit}\n"
            f"- **优先级**: {priority}\n"
            f"- **验收标准**: {acceptance}\n"
        )

    if story_items:
        lines.append("\n---\n".join(story_items))
    else:
        lines.append("暂无用户故事")

    return "\n".join(lines)


def _generate_acceptance_criteria(criteria: list) -> str:
    """生成验收标准文档。"""
    criteria_list = "\n".join([f"- [ ] {c}" for c in (criteria or [
        "功能完整性",
        "性能达标",
        "安全合规",
        "用户体验",
        "可维护性"
    ])])

    return f'''# 验收标准 (Acceptance Criteria)

> 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}

## 功能验收

{criteria_list}

## 性能验收

- [ ] P95 响应时间 ≤ 300ms
- [ ] 错误率 ≤ 0.1%
- [ ] 并发支持 ≥ 100 QPS

## 质量门禁

- [ ] 0 Blocker 级别问题
- [ ] 0 Major 级别问题
- [ ] 代码覆盖率 ≥ 80%
- [ ] 所有测试通过
'''


def _generate_unit_test(target: str, framework: str) -> str:
    """生成单元测试。"""
    component_name = Path(target).name
    return f'''/**
 * {component_name} 单元测试
 * 框架: {framework}
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

import {{ describe, it, expect, vi }} from 'vitest';
import {{ render, screen }} from '@testing-library/react';
import {{ {component_name} }} from './{component_name}';

describe('{component_name}', () => {{
  it('应该正确渲染', () => {{
    render(<{component_name} />);
    expect(screen.getByText('{component_name}')).toBeInTheDocument();
  }});

  it('应该处理空状态', () => {{
    // TODO: 实现空状态测试
  }});

  it('应该处理加载状态', () => {{
    // TODO: 实现加载状态测试
  }});

  it('应该处理错误状态', () => {{
    // TODO: 实现错误状态测试
  }});
}});
'''


def _generate_integration_test(target: str) -> str:
    """生成集成测试。"""
    component_name = Path(target).name
    return f'''/**
 * {component_name} 集成测试
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

import {{ describe, it, expect, beforeAll, afterAll }} from 'vitest';
import {{ render, screen, waitFor }} from '@testing-library/react';

describe('{component_name} 集成测试', () => {{
  beforeAll(() => {{
    // TODO: 设置测试环境（mock API等）
  }});

  afterAll(() => {{
    // TODO: 清理测试环境
  }});

  it('应该与后端API正常交互', async () => {{
    // TODO: 实现API交互测试
  }});

  it('应该正确处理数据流', async () => {{
    // TODO: 实现数据流测试
  }});
}});
'''


def _generate_e2e_test(target: str) -> str:
    """生成E2E测试。"""
    page_name = Path(target).name
    return f'''/**
 * {page_name} E2E 测试
 * 使用 Playwright
 * 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
 */

import {{ test, expect }} from '@playwright/test';

test.describe('{page_name} E2E 测试', () => {{
  test.beforeEach(async ({{ page }}) => {{
    await page.goto('/{page_name.toLowerCase()}');
  }});

  test('应该显示页面主要内容', async ({{ page }}) => {{
    await expect(page.locator('h1')).toContainText('{page_name}');
  }});

  test('应该响应用户交互', async ({{ page }}) => {{
    // TODO: 实现交互测试
  }});

  test('应该在移动端正常显示', async ({{ page }}) => {{
    await page.setViewportSize({{ width: 375, height: 667 }});
    await expect(page).toHaveScreenshot('{page_name}-mobile.png');
  }});
}});
'''


def _generate_dockerfile(task_input: dict) -> str:
    """生成Dockerfile。"""
    node_version = task_input.get("node_version", "18-alpine")
    return f'''# 多阶段构建
FROM node:{node_version} AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生产镜像
FROM node:{node_version}-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

USER node

CMD ["npm", "start"]
'''


def _generate_docker_compose() -> str:
    """生成docker-compose.yml。"""
    return '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
'''


def _generate_ci_cd(platform: str) -> str:
    """生成CI/CD配置。"""
    if platform == "github":
        return '''name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to server
        run: |
          echo "部署到生产环境"
          # TODO: 添加部署步骤
'''
    return '''# GitLab CI/CD 配置

stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: node:18-alpine
  script:
    - npm ci
    - npm run lint
    - npm run test
  only:
    - main
    - develop

build:
  stage: build
  image: node:18-alpine
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
  only:
    - main

deploy:
  stage: deploy
  script:
    - echo "部署到生产环境"
  only:
    - main
'''


def _generate_deploy_script(task_input: dict) -> str:
    """生成部署脚本。"""
    server_ip = task_input.get("server_ip", "your-server-ip")
    return f'''#!/bin/bash
# 部署脚本
# 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}

set -e

echo "🚀 开始部署..."

# 1. 拉取最新代码
git pull origin main

# 2. 安装依赖
npm ci

# 3. 运行测试
npm test

# 4. 构建
npm run build

# 5. 部署到服务器
echo "📦 正在部署到 {server_ip}..."
# rsync -avz dist/ user@{server_ip}:/var/www/app/

# 6. 重启服务
# ssh user@{server_ip} "sudo systemctl restart my-app"

echo "✅ 部署完成！"
'''


def _get_ext(framework: str) -> str:
    """根据框架返回文件扩展名。"""
    ext_map = {
        "react": "tsx",
        "vue": "vue",
        "angular": "tsx",
        "svelte": "svelte",
    }
    return ext_map.get(framework, "tsx")


# ---- 执行路由映射 ----

EXECUTOR_MAP: dict[str, callable] = {
    "backend": execute_backend_agent,
    "frontend": execute_frontend_agent,
    "architect": execute_architect_agent,
    "requirements": execute_requirements_agent,
    "tester": execute_tester_agent,
    "devops": execute_devops_agent,
    # 其他角色暂时返回提示
    "product-manager": lambda t: {"status": "hint_only", "agent": "product-manager", "output": "请提供产品决策指导"},
    "ux-researcher": lambda t: {"status": "hint_only", "agent": "ux-researcher", "output": "请进行交互流程设计"},
    "ui-designer": lambda t: {"status": "hint_only", "agent": "ui-designer", "output": "请进行视觉设计"},
    "code-reviewer": lambda t: {"status": "hint_only", "agent": "code-reviewer", "output": "请执行代码审查"},
    "performance": lambda t: {"status": "hint_only", "agent": "performance", "output": "请执行性能测试"},
    "knowledge-curator": lambda t: {"status": "hint_only", "agent": "knowledge-curator", "output": "请沉淀知识"},
    "documenter": lambda t: {"status": "hint_only", "agent": "documenter", "output": "请生成文档"},
    "final-reviewer": lambda t: {"status": "hint_only", "agent": "final-reviewer", "output": "请执行终审"},
    "bug-fix": lambda t: {"status": "hint_only", "agent": "bug-fix", "output": "请修复Bug"},
}


# v1.3 扩展：支持从 executors 包中查找已注册的 BaseExecutor
def _try_registered_executor(agent_name: str):
    """尝试从 executors 包获取已注册的执行器（v1.3+ 插件扩展点）。"""
    try:
        from loop_agent_mcp.executors import get_executor_class
        cls = get_executor_class(agent_name)
        if cls is not None:
            return cls().execute
    except (ImportError, AttributeError):
        pass
    return None


def execute_agent(agent_name: str, task_input: dict[str, Any]) -> dict[str, Any]:
    """统一执行入口：根据agent_name路由到对应执行器。

    优先级（v1.3+）：
    1. executors 包中已注册的 BaseExecutor 子类（插件扩展点）
    2. EXECUTOR_MAP 中的内置执行器
    3. hint_only lambda（10个提示类角色）
    4. 错误：未知角色

    Args:
        agent_name: 角色名称
        task_input: 任务输入参数

    Returns:
        包含 execution_status, files_created, output 的结果字典
    """
    # 1. 优先查找插件注册的执行器
    executor = _try_registered_executor(agent_name)
    # 2. 回退到内置 EXECUTOR_MAP
    if executor is None:
        executor = EXECUTOR_MAP.get(agent_name)

    if executor is None:
        return {
            "status": "error",
            "error": f"未知角色: {agent_name}",
            "available_agents": list(EXECUTOR_MAP.keys()),
        }

    try:
        result = executor(task_input)
        # v1.3: 标准化结果（兼容 ExecutionResult 和 dict 两种返回类型）
        if hasattr(result, "to_dict"):
            result = result.to_dict()
        result["agent"] = agent_name
        result["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return result
    except ValueError as e:
        return {
            "status": "error",
            "agent": agent_name,
            "error": f"输入验证失败: {e}",
            "execution_failed": True,
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "agent": agent_name,
            "error": str(e),
            "execution_failed": True,
            "traceback": traceback.format_exc(),
        }
