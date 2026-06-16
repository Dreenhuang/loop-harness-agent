#!/bin/bash
# =============================================================================
# Loop-Harness-Agent 跨项目跨 IDE 一键集成脚本 (macOS/Linux)
# =============================================================================
# 用法：
#   ./setup-lha.sh <project-dir> [lha-root]
#   ./setup-lha.sh /path/to/my-project
#   ./setup-lha.sh /path/to/my-project ~/lha
# =============================================================================

set -e

PROJECT_DIR=$1
LHA_ROOT=${2:-"$HOME/loop-harness-agent"}
MODE=${3:-"symlink"}  # full | symlink | minimal

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() { echo -e "\n${CYAN}▶ $1${NC}"; }
ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "  ${RED}❌ $1${NC}"; }

# 验证
[ -z "$PROJECT_DIR" ] && { err "用法: $0 <project-dir> [lha-root] [mode]"; exit 1; }
[ ! -d "$LHA_ROOT" ] && { err "LHA 源目录不存在: $LHA_ROOT"; exit 1; }
[ ! -d "$PROJECT_DIR" ] && { warn "目标项目不存在，创建"; mkdir -p "$PROJECT_DIR"; }

step "源目录: $LHA_ROOT"
step "目标项目: $PROJECT_DIR"
step "模式: $MODE"

cd "$PROJECT_DIR"

# Step 1: .trae
step "Step 1: 集成 .trae 目录"
if [ -e .trae ]; then
  warn ".trae 已存在，跳过"
else
  case $MODE in
    full)     cp -R "$LHA_ROOT/.trae" .trae && ok "已复制 .trae" ;;
    minimal)  mkdir -p .trae/rules && cp -R "$LHA_ROOT/.trae/rules/"* .trae/rules/ && ok "已复制 .trae/rules（最小化）" ;;
    symlink)  ln -s "$LHA_ROOT/.trae" .trae && ok "已创建符号链接 .trae → $LHA_ROOT/.trae" ;;
  esac
fi

# Step 2: templates
if [ "$MODE" != "minimal" ]; then
  step "Step 2: 集成 templates"
  if [ -e templates ]; then
    warn "templates 已存在"
  else
    case $MODE in
      full)    cp -R "$LHA_ROOT/templates" templates && ok "已复制 templates" ;;
      symlink) ln -s "$LHA_ROOT/templates" templates && ok "已创建符号链接 templates" ;;
    esac
  fi
fi

# Step 3: artifacts
if [ "$MODE" != "minimal" ]; then
  step "Step 3: 集成 artifacts"
  if [ -e artifacts ]; then
    warn "artifacts 已存在"
  else
    case $MODE in
      full)    cp -R "$LHA_ROOT/artifacts" artifacts && ok "已复制 artifacts" ;;
      symlink) ln -s "$LHA_ROOT/artifacts" artifacts && ok "已创建符号链接 artifacts" ;;
    esac
  fi
fi

# Step 4: domain-chips
if [ "$MODE" != "minimal" ]; then
  step "Step 4: 集成 domain-chips"
  if [ -e domain-chips ]; then
    warn "domain-chips 已存在"
  else
    case $MODE in
      full)    cp -R "$LHA_ROOT/domain-chips" domain-chips && ok "已复制 domain-chips" ;;
      symlink) ln -s "$LHA_ROOT/domain-chips" domain-chips && ok "已创建符号链接 domain-chips" ;;
    esac
  fi
fi

# Step 5: IDE 规则软链接
step "Step 5: 创建 IDE 规则软链接"

# Cursor
if [ ! -e .cursorrules ]; then
  ln -s ".trae/rules/loop-agent.md" .cursorrules && ok "已创建 .cursorrules"
else
  warn ".cursorrules 已存在"
fi

# Windsurf
if [ ! -e .windsurfrules ]; then
  ln -s ".trae/rules/loop-agent.md" .windsurfrules && ok "已创建 .windsurfrules"
else
  warn ".windsurfrules 已存在"
fi

# VSCode
mkdir -p .vscode/rules
if [ ! -e .vscode/rules/lha.md ]; then
  ln -s "../../.trae/rules/loop-agent.md" .vscode/rules/lha.md && ok "已创建 .vscode/rules/lha.md"
else
  warn ".vscode/rules/lha.md 已存在"
fi

# JetBrains
mkdir -p .idea
if [ ! -e .idea/ai-assistant-prompt.xml ]; then
  cat > .idea/ai-assistant-prompt.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project-prompt>
  <rule source="$PROJECT_DIR$/.trae/rules/loop-agent.md" name="Loop-Harness-Agent" />
  <description>Loop-Harness-Agent v1.2 - 5级封装 + 16角色 + 18 Skill</description>
</project-prompt>
EOF
  ok "已创建 .idea/ai-assistant-prompt.xml"
else
  warn ".idea/ai-assistant-prompt.xml 已存在"
fi

# Step 6: CLAUDE.md
step "Step 6: 复制 CLAUDE.md"
if [ ! -e CLAUDE.md ]; then
  cp "$LHA_ROOT/CLAUDE.md" CLAUDE.md && ok "已复制 CLAUDE.md"
else
  warn "CLAUDE.md 已存在"
fi

# 验证
step "Step 7: 验证集成结果"
PASS=0
TOTAL=0
check() {
  TOTAL=$((TOTAL+1))
  if [ -e "$1" ]; then
    ok "$2 → $1"
    PASS=$((PASS+1))
  else
    err "$2 → $1 缺失"
  fi
}

check ".trae/rules/loop-agent.md" "LHA 主规则"
check ".trae/agents" "Agent Profiles"
check ".trae/skills/core" "Skill 库"
check ".cursorrules" "Cursor 规则"
check ".vscode/rules/lha.md" "VSCode 规则"
check ".idea/ai-assistant-prompt.xml" "JetBrains 规则"
[ "$MODE" != "minimal" ] && check "templates" "工件模板"
[ "$MODE" != "minimal" ] && check "artifacts" "工件注册表"
[ "$MODE" != "minimal" ] && check "domain-chips" "领域芯片"

echo -e "\n通过: $PASS / $TOTAL"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  集成完成！触发方式：${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo "  Cursor:   \"/loop-harness-agent\" 或自然语言 \"LHA\""
echo "  VSCode:   Continue / Cline 中输入 \"/loop-harness-agent\""
echo "  Windsurf: \"/loop-harness-agent\" 或自然语言"
echo "  JetBrains: AI Assistant 中输入 \"/loop-harness-agent\""
echo "  Trae:     \"/loop-harness-agent\" 或 \"/loop-agent\""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}\n"
