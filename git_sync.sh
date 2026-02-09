#!/bin/zsh

# =============================================================================
# Antigravity Git Sync Script
# 功能：自动同步本地与远程仓库，支持多端协作
# 逻辑：Check -> Commit -> Pull (Rebase) -> Push
# =============================================================================

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 动态获取项目路径（关键修改：适配多台电脑）
# $(dirname "$0") 获取脚本所在目录，确保无论在哪台电脑，只要脚本在项目根目录就能正常工作
REPO_PATH=$(cd "$(dirname "$0")"; pwd)

# 进入项目目录
cd "$REPO_PATH" || { echo "${RED}错误: 无法进入目录 $REPO_PATH${NC}"; exit 1; }

echo "${BLUE}>>> 当前项目路径: $REPO_PATH${NC}"

# 定义日志文件及辅助函数
LOG_FILE="$REPO_PATH/log/debug.log"

log_to_file() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # 确保日志目录存在
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$timestamp - [Git Sync] $msg" >> "$LOG_FILE"
}

echo "${GREEN}>>> 开始同步流程...${NC}"

# -----------------------------------------------------------------------------
# 步骤 1: 检查并提交本地修改 (Commit)
# -----------------------------------------------------------------------------
echo "${YELLOW}[1/3] 检查本地修改...${NC}"
STATUS=$(git status --porcelain)

if [ -n "$STATUS" ]; then
    echo "${BLUE}检测到本地有未提交的更改:${NC}"
    echo "$STATUS"
    
    echo "${YELLOW}正在添加并提交更改...${NC}"
    git add .
    
    COMMIT_MSG="chore: auto sync updates at $(date '+%Y-%m-%d %H:%M:%S')"
    if git commit -m "$COMMIT_MSG"; then
        echo "${GREEN}本地修改已提交。${NC}"
        log_to_file "Local changes committed: $COMMIT_MSG"
    else
        echo "${RED}提交失败，请检查 git status。${NC}"
        exit 1
    fi
else
    echo "${GREEN}工作区干净，无未提交更改。${NC}"
fi

# -----------------------------------------------------------------------------
# 步骤 2: 拉取远程更新 (Pull --rebase)
# -----------------------------------------------------------------------------
echo "${YELLOW}[2/3] 拉取远程更新 (Rebase)...${NC}"
# 使用 rebase 保持提交历史线性，避免杂乱的 Merge Commit
if git pull --rebase origin main; then
    echo "${GREEN}远程更新拉取成功（或已是最新）。${NC}"
else
    echo "${RED}错误: 拉取失败！可能存在合并冲突。${NC}"
    echo "${RED}解决建议:${NC}"
    echo "1. 手动打开冲突文件解决冲突"
    echo "2. 运行 'git add <file>'"
    echo "3. 运行 'git rebase --continue'"
    log_to_file "Error: Pull/Rebase failed due to conflicts."
    exit 1
fi

# -----------------------------------------------------------------------------
# 步骤 3: 推送至远程 (Push)
# -----------------------------------------------------------------------------
echo "${YELLOW}[3/3] 检查推送需求...${NC}"
# 检查本地分支是否领先于远程分支
NEEDS_PUSH=$(git cherry -v origin/main 2>/dev/null | wc -l | tr -d ' ')

if [ "$NEEDS_PUSH" -gt 0 ]; then
    echo "${YELLOW}本地有 $NEEDS_PUSH 个提交需要推送，正在执行...${NC}"
    if git push origin main; then
        echo "${GREEN}>>> 同步完成！所有更改已推送到远程。${NC}"
        log_to_file "Sync completed successfully. Pushed $NEEDS_PUSH commits."
    else
        echo "${RED}错误: 推送失败！请检查网络或权限。${NC}"
        log_to_file "Error: Push failed."
        exit 1
    fi
else
    echo "${GREEN}>>> 同步完成！本地已是最新版本，无需推送。${NC}"
    log_to_file "Sync completed. No push needed."
fi
