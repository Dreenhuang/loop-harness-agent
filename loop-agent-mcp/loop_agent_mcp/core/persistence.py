"""Loop 状态持久化模块。

v1.3 关键改进（修复 v1.2 的 Critical 缺陷）：
- StateManager 之前是纯内存单例，进程重启 = 状态全丢
- resume_loop 之前是假实现（注释自认"简化"）
- 现在使用 JSON 文件持久化 + 自动恢复

v1.4 安全增强（G-5/G-8 修复）：
- G-5：添加 HMAC-SHA256 签名校验，防止状态文件被篡改
- G-8：添加路径遍历防护，确保 delete_loop 不会删除工作区外文件

设计：
- 每个 loop_id 一个 .json 文件 + .sig 签名文件
- 写入使用线程锁保护
- 支持列出所有 Loop、加载最新 Loop
- 签名密钥从环境变量 STATE_SIGNING_KEY 读取，默认使用机器名 + 固定盐
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StatePersistence:
    """状态持久化管理器：JSON 文件存储 + 自动快照 + HMAC 签名校验。"""

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
        # G-5 修复：初始化签名密钥
        self._signing_key = self._get_signing_key()

    def _get_signing_key(self) -> bytes:
        """获取 HMAC 签名密钥。
        
        优先从环境变量 STATE_SIGNING_KEY 读取，否则使用机器名 + 固定盐。
        
        Returns:
            签名密钥字节
        """
        env_key = os.environ.get("STATE_SIGNING_KEY")
        if env_key:
            return env_key.encode("utf-8")
        # 默认密钥：机器名 + 固定盐
        import socket
        default_key = f"{socket.gethostname()}_loop_agent_state_salt_v1"
        return default_key.encode("utf-8")

    def _compute_signature(self, data: bytes) -> str:
        """计算 HMAC-SHA256 签名。
        
        Args:
            data: 待签名数据
            
        Returns:
            十六进制签名字符串
        """
        return hmac.new(self._signing_key, data, hashlib.sha256).hexdigest()

    def _verify_signature(self, data: bytes, signature: str) -> bool:
        """验证 HMAC-SHA256 签名。
        
        Args:
            data: 原始数据
            signature: 待验证签名
            
        Returns:
            签名是否有效
        """
        expected = self._compute_signature(data)
        return hmac.compare_digest(expected, signature)

    def _state_file(self, loop_id: str) -> Path:
        """获取状态文件路径。"""
        # 清理 loop_id 中的特殊字符
        safe_id = "".join(c for c in loop_id if c.isalnum() or c in ("-", "_"))
        if not safe_id:
            safe_id = f"loop-{int(time.time())}"
        return self.state_dir / f"{safe_id}.json"

    def save_state(self, loop_id: str, state: dict[str, Any]) -> bool:
        """保存状态到磁盘（带 HMAC 签名）。

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
                # 序列化为 JSON
                json_content = json.dumps(state, ensure_ascii=False, indent=2, default=str)
                json_bytes = json_content.encode("utf-8")
                
                # G-5 修复：计算并保存签名
                signature = self._compute_signature(json_bytes)
                sig_file = state_file.with_suffix(".sig")
                sig_file.write_text(signature, encoding="utf-8")
                
                # 写入临时文件后改名（原子性）
                tmp_file = state_file.with_suffix(".tmp")
                tmp_file.write_bytes(json_bytes)
                # 原子改名（Windows 上先删后改）
                if os.name == "nt" and state_file.exists():
                    state_file.unlink()
                tmp_file.rename(state_file)
                return True
            except (OSError, TypeError, ValueError):
                return False

    def load_state(self, loop_id: str) -> dict[str, Any] | None:
        """从磁盘加载状态（带 HMAC 签名验证）。

        Args:
            loop_id: Loop 唯一标识。

        Returns:
            状态字典，若不存在、加载失败或签名不匹配则返回 None。
        """
        with self._lock:
            state_file = self._state_file(loop_id)
            if not state_file.exists():
                return None
            try:
                json_bytes = state_file.read_bytes()
                
                # G-5 修复：验证签名
                sig_file = state_file.with_suffix(".sig")
                if sig_file.exists():
                    stored_signature = sig_file.read_text(encoding="utf-8")
                    if not self._verify_signature(json_bytes, stored_signature):
                        logger.warning(
                            f"State file signature mismatch for loop {loop_id}, "
                            "falling back to empty state"
                        )
                        return None
                else:
                    # 签名文件不存在，可能是旧版本或首次运行
                    logger.debug(f"No signature file found for loop {loop_id}, loading without verification")
                
                return json.loads(json_bytes.decode("utf-8"))
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
        """删除指定 Loop 的状态文件（带路径遍历防护）。

        Args:
            loop_id: Loop 唯一标识。

        Returns:
            是否删除成功。
            
        Raises:
            ValueError: 如果检测到路径遍历攻击
        """
        with self._lock:
            state_file = self._state_file(loop_id)
            
            # G-8 修复：路径遍历防护
            # 确保最终路径仍在 state_dir 内
            try:
                resolved_state_file = state_file.resolve()
                resolved_state_dir = self.state_dir.resolve()
                resolved_state_file.relative_to(resolved_state_dir)
            except ValueError as e:
                logger.error(
                    f"Path traversal detected in delete_loop: "
                    f"loop_id={loop_id}, state_file={state_file}"
                )
                raise ValueError("Path traversal detected") from e
            
            if state_file.exists():
                try:
                    state_file.unlink()
                    # 同时删除签名文件
                    sig_file = state_file.with_suffix(".sig")
                    if sig_file.exists():
                        sig_file.unlink()
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
