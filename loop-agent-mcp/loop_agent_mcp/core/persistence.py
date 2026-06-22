"""Loop 状态持久化模块。

v1.3 关键改进（修复 v1.2 的 Critical 缺陷）：
- StateManager 之前是纯内存单例，进程重启 = 状态全丢
- resume_loop 之前是假实现（注释自认"简化"）
- 现在使用 JSON 文件持久化 + 自动恢复

设计：
- 每个 loop_id 一个 .json 文件
- 写入使用线程锁保护
- 支持列出所有 Loop、加载最新 Loop
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class StatePersistence:
    """状态持久化管理器：JSON 文件存储 + 自动快照。"""

    # 状态文件目录名（位于工作区内）
    STATE_DIR_NAME = ".loop-agent-state"

    def __init__(self, workspace: Path | str) -> None:
        """初始化持久化管理器。

        Args:
            workspace: 工作区根目录。
        """
        if isinstance(workspace, str):
            workspace = Path(workspace)
        self.workspace = workspace
        self.state_dir = workspace / self.STATE_DIR_NAME
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _state_file(self, loop_id: str) -> Path:
        """获取状态文件路径。"""
        # 清理 loop_id 中的特殊字符
        safe_id = "".join(c for c in loop_id if c.isalnum() or c in ("-", "_"))
        if not safe_id:
            safe_id = f"loop-{int(time.time())}"
        return self.state_dir / f"{safe_id}.json"

    def save_state(self, loop_id: str, state: dict[str, Any]) -> bool:
        """保存状态到磁盘。

        Args:
            loop_id: Loop 唯一标识。
            state: 状态字典。

        Returns:
            是否保存成功。
        """
        with self._lock:
            try:
                state_file = self._state_file(loop_id)
                # 添加保存时间戳
                state = dict(state)  # 浅拷贝避免污染原数据
                state["_saved_at"] = datetime.now().isoformat()
                state["_loop_id"] = loop_id
                # 写入临时文件后改名（原子性）
                tmp_file = state_file.with_suffix(".tmp")
                tmp_file.write_text(
                    json.dumps(state, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                # 原子改名（Windows 上先删后改）
                if os.name == "nt" and state_file.exists():
                    state_file.unlink()
                tmp_file.rename(state_file)
                return True
            except (OSError, TypeError, ValueError):
                return False

    def load_state(self, loop_id: str) -> dict[str, Any] | None:
        """从磁盘加载状态。

        Args:
            loop_id: Loop 唯一标识。

        Returns:
            状态字典，若不存在或加载失败则返回 None。
        """
        with self._lock:
            state_file = self._state_file(loop_id)
            if not state_file.exists():
                return None
            try:
                return json.loads(state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                return None

    def list_loops(self) -> list[dict[str, Any]]:
        """列出所有 Loop 状态摘要。

        Returns:
            Loop 摘要列表，按 saved_at 降序排序。
        """
        with self._lock:
            loops: list[dict[str, Any]] = []
            if not self.state_dir.exists():
                return []
            for f in self.state_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    loops.append({
                        "loop_id": data.get("_loop_id", data.get("loop_id", f.stem)),
                        "mode": data.get("mode", "unknown"),
                        "current_phase": data.get("current_phase", "unknown"),
                        "saved_at": data.get("_saved_at", "unknown"),
                        "file": str(f.relative_to(self.workspace)),
                    })
                except (json.JSONDecodeError, OSError, KeyError):
                    continue
            # 按 saved_at 降序排序
            loops.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
            return loops

    def get_latest_loop(self) -> dict[str, Any] | None:
        """获取最近保存的 Loop 完整状态。

        Returns:
            最新 Loop 的完整状态字典，若无则返回 None。
        """
        loops = self.list_loops()
        if not loops:
            return None
        latest_id = loops[0]["loop_id"]
        return self.load_state(latest_id)

    def delete_loop(self, loop_id: str) -> bool:
        """删除指定 Loop 的状态文件。

        Args:
            loop_id: Loop 唯一标识。

        Returns:
            是否删除成功。
        """
        with self._lock:
            state_file = self._state_file(loop_id)
            if state_file.exists():
                try:
                    state_file.unlink()
                    return True
                except OSError:
                    return False
            return False

    def cleanup_orphan_temp_files(self) -> int:
        """清理孤立的临时文件（.tmp）。

        Returns:
            清理的文件数。
        """
        with self._lock:
            count = 0
            for f in self.state_dir.glob("*.tmp"):
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
            return count
