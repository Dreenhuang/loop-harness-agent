"""任务级 JSONL 持久化存储。

每个任务以一行 JSON 形式追加写入，支持按 task_id / loop_id 查询与崩溃恢复。
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from loop_agent_mcp.core.config import find_workspace_root
from loop_agent_mcp.core.state import StateManager
from loop_agent_mcp.runtime.task import Task


class TaskStore:
    """任务级 JSONL 持久化存储。"""

    STORE_DIR_NAME = ".loop-agent-tasks"
    STORE_FILE_NAME = "tasks.jsonl"

    def __init__(self, workspace: Path | str | None = None) -> None:
        self._lock = threading.Lock()
        self._workspace = self._resolve_workspace(workspace)
        self._store_dir = self._workspace / self.STORE_DIR_NAME
        self._store_file = self._store_dir / self.STORE_FILE_NAME
        self._ensure_store()
        # 内存索引：task_id -> 最新记录，避免每次 O(n) 扫描文件
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _resolve_workspace(self, workspace: Path | str | None) -> Path:
        if workspace is not None:
            return Path(workspace).resolve()
        base_str = StateManager.get().state.workspace
        if base_str:
            return Path(base_str).resolve()
        return find_workspace_root()

    def _ensure_store(self) -> None:
        self._store_dir.mkdir(parents=True, exist_ok=True)
        if not self._store_file.exists():
            self._store_file.write_text("", encoding="utf-8")

    def _load_cache(self) -> None:
        """启动时一次性加载已有记录到内存索引。"""
        with self._lock:
            if not self._store_file.exists():
                return
            for line in self._store_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tid = record.get("task_id")
                if tid:
                    self._cache[tid] = record

    def save(self, task: Task) -> bool:
        """保存任务状态（追加 JSONL 并更新内存索引）。"""
        record = {
            "_stored_at": _now_iso(),
            **task.to_dict(),
        }
        with self._lock:
            try:
                with open(self._store_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                self._cache[task.task_id] = record
                return True
            except (OSError, TypeError, ValueError):
                return False

    def load(self, task_id: str) -> Task | None:
        """加载指定任务的最新状态。"""
        with self._lock:
            record = self._cache.get(task_id)
        if record is None:
            return None
        return Task.from_dict(record)

    def list_tasks(
        self,
        *,
        loop_id: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """列出任务，支持按 loop_id 和 status 过滤。"""
        with self._lock:
            records = list(self._cache.values())

        result = []
        for record in records:
            if loop_id and record.get("loop_id") != loop_id:
                continue
            if status and record.get("status") != status:
                continue
            result.append(Task.from_dict(record))
        return result

    def recover_latest(
        self,
        *,
        loop_id: str | None = None,
        only_incomplete: bool = True,
    ) -> list[Task]:
        """崩溃恢复：读取未完成任务。"""
        tasks = self.list_tasks(loop_id=loop_id)
        if only_incomplete:
            tasks = [t for t in tasks if not t.is_terminal()]
        return tasks

    def compact(self) -> int:
        """压缩 JSONL：只保留每个 task_id 的最新记录。"""
        with self._lock:
            if not self._store_file.exists():
                return 0

            tasks = dict(self._cache)
            tmp_file = self._store_file.with_suffix(".tmp")
            tmp_file.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False, default=str) + "\n"
                    for record in tasks.values()
                ),
                encoding="utf-8",
            )
            if os.name == "nt" and self._store_file.exists():
                self._store_file.unlink()
            tmp_file.rename(self._store_file)
            return len(tasks)


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
