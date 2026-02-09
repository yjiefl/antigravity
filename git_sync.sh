#!/bin/zsh

# =============================================================================
# Antigravity Git Sync Script (Focused Version)
# 功能：极速同步 antigravity 主仓库 (Commit -> Pull -> Push)
# =============================================================================

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. 路径设置
REPO_PATH=$(cd "$(dirname "$0")"; pwd)
REPORT_DIR="$REPO_PATH/report"
LOG_FILE="$REPORT_DIR/sync.log"
mkdir -p "$REPORT_DIR"

cd "$REPO_PATH" || exit 1

log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# -----------------------------------------------------------------------------
# 核心功能模块
# -----------------------------------------------------------------------------

# 同步主仓库
run_sync() {
    local force=$1
    echo "${CYAN}=== 开始同步 Antigravity 仓库 ===${NC}"
    
    # 1. 检查修改
    if [ -n "$(git status --porcelain)" ]; then
        echo "   ${YELLOW}检测到本地修改，正在提交...${NC}"
        git add .
        COMMIT_MSG="feat: auto sync at $(date '+%Y-%m-%d %H:%M:%S')"
        if git commit -m "$COMMIT_MSG"; then
            echo "   ${GREEN}本地提交成功。${NC}"
            log_to_file "Committed changes."
        fi
    else
        echo "   ${GREEN}工作区干净，无需提交。${NC}"
    fi

    # 2. 拉取更新
    BRANCH=$(git branch --show-current)
    echo "   ${YELLOW}正在从远程拉取 (Rebase)...${NC}"
    if git pull --rebase --autostash origin "$BRANCH"; then
        echo "   ${GREEN}拉取成功。${NC}"
    else
        echo "${RED}错误: 拉取失败！请查看上方 Git 报错信息。${NC}"
        log_to_file "Pull failed."
        return 1
    fi

    # 3. 推送
    NEEDS_PUSH=$(git cherry -v origin/"$BRANCH" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$NEEDS_PUSH" -gt 0 ] || [ "$force" = true ]; then
        echo "   ${YELLOW}正在推送到远程...${NC}"
        local push_cmd="git push origin $BRANCH"
        [ "$force" = true ] && push_cmd="git push --force origin $BRANCH"
        
        if $push_cmd; then
            echo "   ${GREEN}推送成功！${NC}"
            log_to_file "Pushed changes."
        else
            echo "${RED}错误: 推送失败！${NC}"
            log_to_file "Push failed."
        fi
    else
        echo "   ${GREEN}远程已是最新，无需推送。${NC}"
    fi
}

# 检查状态
run_status() {
    echo "${BLUE}>>> 仓库状态概览...${NC}"
    git status -s
    echo "--------------------------------"
    git fetch origin "$BRANCH" 2>/dev/null
    BRANCH=$(git branch --show-current)
    BEHIND=$(git rev-list --count HEAD..origin/"$BRANCH" 2>/dev/null || echo 0)
    AHEAD=$(git rev-list --count origin/"$BRANCH"..HEAD 2>/dev/null || echo 0)
    
    echo "当前分支: $BRANCH"
    echo "领先: $AHEAD | 落后: $BEHIND"
}

# 创建 Release
run_release() {
    echo "${CYAN}>>> 创建新版本 (Release)${NC}"
    echo -n "输入版本号 (如 v1.2.0): "
    read version_tag
    [ -z "$version_tag" ] && { echo "${RED}版本号不能为空${NC}"; return; }
    
    git tag -a "$version_tag" -m "Release $version_tag"
    if git push origin "$version_tag"; then
        echo "${GREEN}标签 $version_tag 已推送到远程。${NC}"
        # 尝试使用 GitHub CLI
        if command -v gh >/dev/null 2>&1; then
             gh release create "$version_tag" --title "$version_tag" --notes "Auto-generated release"
        fi
    fi
}

# -----------------------------------------------------------------------------
# 菜单
# -----------------------------------------------------------------------------
show_menu() {
    echo "${CYAN}=========================================${NC}"
    echo "${CYAN}     Antigravity Git Sync (Lite)         ${NC}"
    echo "${CYAN}=========================================${NC}"
    echo "1. ${GREEN}快速同步${NC} (Add + Commit + Pull + Push)"
    echo "2. ${BLUE}查看状态${NC}"
    echo "3. ${MAGENTA}发布版本${NC} (Create Tag & Push)"
    echo "4. ${RED}强制推送${NC} (覆盖远程)"
    echo "0. 退出"
    echo "-----------------------------------------"
    echo -n "请选择 [0-4]: "
    read choice
    
    case $choice in
        1) run_sync false ;;
        2) run_status ;;
        3) run_release ;;
        4) run_sync true ;;
        0) exit 0 ;;
        *) echo "无效选择" ;;
    esac
}

if [ $# -gt 0 ]; then
    case $1 in
        -s|--status) run_status ;;
        -p|--push|--sync) run_sync false ;;
        *) run_sync false ;;
    esac
else
    show_menu
fi
