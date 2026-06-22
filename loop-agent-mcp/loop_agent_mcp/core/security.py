"""Loop-Harness-Agent MCP 路径与内容安全验证模块。

v1.3 关键安全加固（修复 v1.2 的 Critical 漏洞）：
- 路径遍历防护：禁止 ".." 和绝对路径
- 工作区边界检查：解析后必须位于 workspace 内
- 文件类型白名单 + 黑名单
- 文件大小限制
- 标识符注入防护

设计原则：
- 零信任：所有用户输入都视为不可信
- 显式失败：所有错误必须抛出明确异常
- 默认安全：默认拒绝，仅显式允许才放行
"""
from __future__ import annotations

import re
from pathlib import Path


# ==================== 危险扩展名黑名单 ====================
# 可执行脚本、动态库、容器镜像等绝不允许 MCP 写入
DANGEROUS_EXTENSIONS: set[str] = {
    # Windows 可执行
    ".bat", ".cmd", ".exe", ".msi", ".com", ".scr", ".pif",
    # Shell 脚本
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1", ".psd1",
    # macOS 应用
    ".app", ".command", ".dmg", ".pkg",
    # Linux 包
    ".deb", ".rpm", ".apk",
    # 动态库（Windows/Linux/macOS）
    ".dll", ".so", ".dylib",
    # Java 字节码
    ".jar", ".class", ".war",
    # 脚本（防止 LLM 误执行）
    ".vbs", ".vbe", ".js", ".jse", ".mjs", ".cjs",
    # Office 宏
    ".docm", ".xlsm", ".pptm", ".dotm",
}


# ==================== 允许的扩展名白名单 ====================
# 默认仅允许源代码、配置、文档、样式等"安全"文件类型
ALLOWED_EXTENSIONS: set[str] = {
    # TypeScript / JavaScript
    ".ts", ".tsx", ".jsx",
    # 其他前端框架
    ".vue", ".svelte", ".astro",
    # 后端语言
    ".py", ".java", ".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".h",
    # 配置 / 数据
    ".json", ".yaml", ".yml", ".toml", ".xml", ".csv",
    # 文档
    ".md", ".txt", ".rst", ".adoc",
    # 样式
    ".css", ".scss", ".sass", ".less",
    # 模板
    ".html", ".htm", ".svg", ".ejs", ".hbs", ".pug",
    # 项目配置（无扩展名）
    ".env", ".gitignore", ".dockerignore", ".editorconfig", ".npmrc",
    # .env 系列（如 .env.example, .env.local, .env.production）
    ".example", ".local", ".production", ".development", ".staging", ".test",
    # 数据库 / API
    ".sql", ".graphql", ".gql", ".proto", ".prisma",
    # 构建 / 服务
    ".conf", ".ini", ".cfg", ".lock",
    # 日志
    ".log",
}


# 最大文件大小：10MB
MAX_FILE_SIZE: int = 10 * 1024 * 1024

# 标识符合法字符（用于代码注入防护）
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


# ==================== 核心验证函数 ====================


def validate_path(
    workspace: Path | str,
    relative_path: str,
    operation: str = "write",
) -> Path:
    """验证路径安全性，返回解析后的绝对路径。

    Args:
        workspace: 工作区根目录（Path 对象或字符串）。
        relative_path: 用户提供的相对路径。
        operation: 操作类型，可选 "write" / "read" / "list"。

    Returns:
        验证通过后的绝对 Path 对象。

    Raises:
        ValueError: 路径不安全、逃逸工作区、扩展名非法等。
        TypeError: 参数类型错误。
    """
    # 类型检查
    if not isinstance(relative_path, str):
        raise TypeError(f"path 必须是字符串，得到 {type(relative_path).__name__}")

    if not relative_path or relative_path.strip() == "":
        raise ValueError("path 不能为空")

    if operation not in ("write", "read", "list"):
        raise ValueError(f"未知 operation: {operation}（允许: write/read/list）")

    # 统一 workspace 为 Path
    if isinstance(workspace, str):
        workspace = Path(workspace)
    workspace = workspace.resolve()

    # 1. 禁止绝对路径（包括 Windows 盘符形式如 C:\\）
    p = Path(relative_path)
    if p.is_absolute():
        raise ValueError(f"禁止使用绝对路径: {relative_path}")

    # 2. 禁止路径遍历
    if ".." in p.parts:
        raise ValueError(f"禁止路径遍历（包含 ..）: {relative_path}")

    # 3. 解析并检查工作区边界
    full_path = (workspace / relative_path).resolve()
    try:
        full_path.relative_to(workspace)
    except ValueError:
        raise ValueError(
            f"路径逃逸工作区: {relative_path} -> {full_path}（必须位于 {workspace} 内）"
        )

    # 4. 写操作的扩展名检查
    if operation == "write":
        ext = full_path.suffix.lower()
        if ext:
            if ext in DANGEROUS_EXTENSIONS:
                raise ValueError(f"禁止写入危险文件类型: {ext}")
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"不支持的文件类型: {ext}。"
                    f"如需扩展，请修改 core/security.py 的 ALLOWED_EXTENSIONS。"
                )

    return full_path


def validate_content(content: str | bytes) -> None:
    """验证内容大小。

    Args:
        content: 文件内容（字符串或字节）。

    Raises:
        ValueError: 内容超过 10MB。
    """
    if isinstance(content, str):
        size = len(content.encode("utf-8"))
    elif isinstance(content, bytes):
        size = len(content)
    else:
        raise TypeError(f"content 必须是 str 或 bytes，得到 {type(content).__name__}")

    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"文件内容过大: {size} 字节（上限: {MAX_FILE_SIZE} 字节 = 10MB）"
        )


def sanitize_identifier(name: str) -> str:
    """清洗标识符，防止代码注入。

    只允许字母、数字、下划线，首字符不能是数字。

    Args:
        name: 原始标识符。

    Returns:
        清洗后的标识符（如果合法）。

    Raises:
        ValueError: 标识符非法。
        TypeError: 参数类型错误。
    """
    if not isinstance(name, str):
        raise TypeError(f"identifier 必须是字符串，得到 {type(name).__name__}")

    if not name:
        raise ValueError("identifier 不能为空")

    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"非法标识符: {name!r}（只允许字母、数字、下划线，且首字符不能是数字）"
        )

    return name


def is_safe_extension(extension: str) -> bool:
    """判断扩展名是否安全（用于独立判断）。"""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = "." + ext
    return ext in ALLOWED_EXTENSIONS and ext not in DANGEROUS_EXTENSIONS
