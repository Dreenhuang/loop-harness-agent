# Loop Agent · 辅助脚本

> **版本**：v1.0
> **生效日期**：2026-06-15
> **对齐**：Trae Solo 工程实现指南 第八章

---

## 脚本清单

| 脚本 | 用途 | 调用时机 |
|------|------|----------|
| **init-blackboard.bat** | 初始化黑板目录结构 + state.json + A2A 文件 | 新建项目 / 首次使用 |
| **snapshot-state.bat** | 保存当前 Blackboard 完整状态到快照 | 每 Phase 完成 / 手动备份 |
| **restore-state.bat** | 从指定快照恢复 Blackboard | 崩溃恢复 / 回滚 |

---

## 使用方式

### 1. 初始化（首次使用）

```cmd
scripts\init-blackboard.bat [项目名]
```

执行后将创建：
- 22 个黑板子目录
- `blackboard\state.json`（状态机初始状态）
- `blackboard\a2a\*`（A2A 消息日志）
- `blackboard\knowledge_index.json`
- `项目进度记录.md`（复制模板到项目根）
- `blackboard\input\README.md`（PRD 入口）

### 2. 创建快照

```cmd
scripts\snapshot-state.bat
```

输出：`blackboard\.snapshots\<时间戳>\`

### 3. 恢复快照

```cmd
# 方式 1：交互式（列出所有快照后选择）
scripts\restore-state.bat

# 方式 2：直接指定快照 ID
scripts\restore-state.bat 20260615_143052
```

---

## 自动化集成

### 配合 Loop Agent 主入口规则

主入口 `loop-agent.md` 中应包含以下规则：

```yaml
# 触发 Loop Agent 时的强制行为
on_trigger:
  - if no_blackboard → call init-blackboard.bat
  - if has_blackboard → read 项目进度记录.md → output progress_summary

# 每 Phase 完成
on_phase_complete:
  - call snapshot-state.bat
  - update 项目进度记录.md
  - output checkpoint_id

# 崩溃恢复
on_resume:
  - call restore-state.bat [last_checkpoint_id]
  - continue from restored state
```

---

## 跨平台兼容

当前为 Windows 批处理（.bat）实现。如需 Linux/Mac：

| Windows | Linux/Mac |
|---------|-----------|
| `init-blackboard.bat` | `init-blackboard.sh` |
| `snapshot-state.bat` | `snapshot-state.sh` |
| `restore-state.bat` | `restore-state.sh` |

如需跨平台版本，可使用 Bash + PowerShell Core 实现，未来扩展。

---

## 版本

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v1.0 | 2026-06-15 | 初始版本：3 个 Windows 脚本 |

---

**【Loop Agent Scripts v1.0 · 3 个脚本就绪】**
