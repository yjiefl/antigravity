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
        local success=false
        if [ "$force" = true ]; then
            git push --force origin "$BRANCH" && success=true
        else
            git push origin "$BRANCH" && success=true
        fi
        
        if [ "$success" = true ]; then
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
    BRANCH=$(git branch --show-current)
    echo "${BLUE}>>> 仓库状态概览 ($BRANCH)...${NC}"
    
    # 1. 检查本地工作区 (包含未追踪文件)
    MODIFIED_COUNT=$(git status --porcelain | wc -l | tr -d ' ')
    if [ "$MODIFIED_COUNT" -gt 0 ]; then
        git status -s
        echo "   ${YELLOW}提示: 您有 $MODIFIED_COUNT 个本地文件变动 (M/??)${NC}"
    else
        echo "   ${GREEN}工作区干净 (无本地修改)${NC}"
    fi
    
    echo "--------------------------------"
    
    # 2. 检查云端同步状态 (基于 Commit)
    echo "${YELLOW}正在获取远程状态...${NC}"
    git fetch origin "$BRANCH" 2>/dev/null
    
    BEHIND=$(git rev-list --count HEAD..origin/"$BRANCH" 2>/dev/null || echo 0)
    AHEAD=$(git rev-list --count origin/"$BRANCH"..HEAD 2>/dev/null || echo 0)
    
    echo "同步状态: 领先: ${GREEN}$AHEAD${NC} 提交 | 落后: ${RED}$BEHIND${NC} 提交"
    
    # 3. 后续操作提示
    if [ "$AHEAD" -gt 0 ] || [ "$BEHIND" -gt 0 ]; then
         echo "\n${CYAN}>>> 输入 'd' 可查看详细差异，回车返回主菜单${NC}"
         read -r -t 8 -n 1 opt
         if [[ "$opt" == "d" ]]; then
             run_compare
         fi
    elif [ "$MODIFIED_COUNT" -gt 0 ]; then
        echo "\n${CYAN}>>> 提示: 本地文件已修改但尚未提交。请选择 [1] 自动提交并同步。${NC}"
    fi
}

# 对比本地与远程的差异
run_compare() {
    BRANCH=$(git branch --show-current)
    echo "${CYAN}=== 差异对比: 本地(HEAD) vs 远程(origin/$BRANCH) ===${NC}"
    
    # 获取差异统计
    echo "${YELLOW}1. 文件变动统计:${NC}"
    git diff --stat "origin/$BRANCH"..HEAD
    
    echo "\n${YELLOW}2. 具体文件状态 (A:新增, M:修改, D:删除):${NC}"
    git diff --name-status "origin/$BRANCH"..HEAD
    
    echo "\n${YELLOW}是否查看详细代码差异? (y/n):${NC} "
    read -r show_detail
    if [[ "$show_detail" =~ ^[Yy]$ ]]; then
        git diff "origin/$BRANCH"..HEAD
    fi
}

# 以本地数据为准强制覆盖远程 (Local Overwrite Remote)
run_local_overwrite() {
    BRANCH=$(git branch --show-current)
    echo "${YELLOW}正在获取远程最新状态以供对比...${NC}"
    git fetch origin "$BRANCH" 2>/dev/null

    echo "${RED}！！！警告：此操作将跳过远程拉取，直接使用本地数据强制覆盖远程仓库！！！${NC}"
    echo "${RED}！！！远程仓库中比本地新的提交 (落后部分) 将会丢失！！！${NC}"
    
    while true; do
        echo -n "请确认操作: [y]继续, [n]取消, [v]查看差异详情: "
        read -r confirm
        case "$confirm" in
            [Vv]) run_compare ;;
            [Yy]) break ;;
            [Nn]) echo "操作已取消。"; return ;;
            *) echo "无效输入，请输入 y, n 或 v" ;;
        esac
    done

    echo "${CYAN}=== 开始以本地为主覆盖同步 ===${NC}"
    
    # 1. 提交本地所有修改（包括删除）
    if [ -n "$(git status --porcelain)" ]; then
        echo "   ${YELLOW}检测到本地修改，正在提交 (含删除)...${NC}"
        git add -A
        COMMIT_MSG="feat: local overwrite sync at $(date '+%Y-%m-%d %H:%M:%S')"
        if git commit -m "$COMMIT_MSG"; then
            echo "   ${GREEN}本地提交成功。${NC}"
            log_to_file "Committed changes for local overwrite."
        fi
    else
        echo "   ${GREEN}工作区干净，准备同步当前状态。${NC}"
    fi

    # 2. 强制推送
    BRANCH=$(git branch --show-current)
    echo "   ${YELLOW}正在强制推送到远程 (origin/$BRANCH)...${NC}"
    if git push --force origin "$BRANCH"; then
        echo "   ${GREEN}覆盖成功！远程已同步为本地最新状态。${NC}"
        log_to_file "Force pushed local state to remote (Overwrite)."
    else
        echo "${RED}错误: 推送失败！${NC}"
        log_to_file "Force push overwrite failed."
    fi
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
    echo "4. ${YELLOW}以本地为准同步${NC} (Overwrite Remote! Skip Pull)"
    echo "5. ${RED}强制推送${NC} (仅 Push --force)"
    echo "0. 退出"
    echo "-----------------------------------------"
    echo -n "请选择 [0-5]: "
    read choice
    
    case $choice in
        1) run_sync false ;;
        2) run_status ;;
        3) run_release ;;
        4) run_local_overwrite ;;
        5) run_sync true ;;
        0) exit 0 ;;
        *) echo "无效选择" ;;
    esac
}

if [ $# -gt 0 ]; then
    case $1 in
        -s|--status) run_status ;;
        -p|--push|--sync) run_sync false ;;
        -o|--overwrite) run_local_overwrite ;;
        -f|--force) run_sync true ;;
        *) run_sync false ;;
    esac
else
    show_menu
fi
