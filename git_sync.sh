#!/bin/zsh

# =============================================================================
# Antigravity Git Sync Script
# 功能：自动同步/检查/报告 Git 仓库状态
# 用法：./git_sync.sh [options]
# =============================================================================

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. 动态获取项目路径
REPO_PATH=$(cd "$(dirname "$0")"; pwd)
LOG_FILE="$REPO_PATH/log/debug.log"

# 进入项目目录
cd "$REPO_PATH" || { echo "${RED}错误: 无法进入目录 $REPO_PATH${NC}"; exit 1; }

# -----------------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------------

log_to_file() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$timestamp - [Git Sync] $msg" >> "$LOG_FILE"
}

show_help() {
    echo "${CYAN}Antigravity Git Sync Tool${NC}"
    echo "用法: ./git_sync.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -s, --status    仅检查同步状态（不执行同步）"
    echo "  -r, --report    生成当前仓库状态报告到日志目录"
    echo "  -f, --force     强制推送（慎用）"
    echo ""
    echo "默认行为: 执行完整的 Check -> Commit -> Pull(Rebase) -> Push 流程"
}

check_status() {
    echo "${BLUE}>>> 正在检查仓库状态...${NC}"
    
    # 检查本地修改
    LOCAL_CHANGES=$(git status --porcelain | wc -l | tr -d ' ')
    
    # 检查落后/领先提交
    git fetch origin main > /dev/null 2>&1
    BEHIND=$(git rev-list --count HEAD..origin/main)
    AHEAD=$(git rev-list --count origin/main..HEAD)
    
    echo "----------------------------------------"
    if [ "$LOCAL_CHANGES" -gt 0 ]; then
        echo "${YELLOW}● 本地有 $LOCAL_CHANGES 个文件被修改 (未提交)${NC}"
    else
        echo "${GREEN}● 工作区干净${NC}"
    fi
    
    if [ "$BEHIND" -gt 0 ]; then
        echo "${YELLOW}↓ 落后远程 $BEHIND 个提交 (需拉取)${NC}"
    else
        echo "${GREEN}✓ 已包含远程所有提交${NC}"
    fi
    
    if [ "$AHEAD" -gt 0 ]; then
        echo "${YELLOW}↑ 领先远程 $AHEAD 个提交 (需推送)${NC}"
    else
        echo "${GREEN}✓以此分支为准，无需推送${NC}"
    fi
    echo "----------------------------------------"
}

generate_report() {
    REPORT_TIME=$(date '+%Y-%m-%d_%H%M%S')
    REPORT_FILE="$REPO_PATH/log/repo_status_${REPORT_TIME}.txt"
    
    echo "${BLUE}>>> 正在生成详细报告...${NC}"
    
    {
        echo "=== Antigravity Repository Status Report ==="
        echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Branch: $(git branch --show-current)"
        echo ""
        echo "--- 1. Commit History (Last 5) ---"
        git log -n 5 --oneline --graph --decorate
        echo ""
        echo "--- 2. Status Short ---"
        git status -s
        echo ""
        echo "--- 3. Remote Info ---"
        git remote -v
        echo ""
        echo "--- 4. Detailed Status ---"
        git status
    } > "$REPORT_FILE"
    
    echo "${GREEN}报告已生成: $REPORT_FILE${NC}"
    log_to_file "Report generated: $REPORT_FILE"
}

# -----------------------------------------------------------------------------
# 核心同步逻辑 (原有逻辑封装)
# -----------------------------------------------------------------------------
run_sync() {
    local force_push=$1
    echo "${GREEN}>>> 开始同步流程...${NC}"
    
    # [Step 1] Commit
    echo "${YELLOW}[1/3] 检查本地修改...${NC}"
    STATUS=$(git status --porcelain)
    if [ -n "$STATUS" ]; then
        echo "${BLUE}检测到本地有未提交的更改，正在提交...${NC}"
        git add .
        COMMIT_MSG="chore: auto sync updates at $(date '+%Y-%m-%d %H:%M:%S')"
        if git commit -m "$COMMIT_MSG"; then
            echo "${GREEN}本地修改已提交。${NC}"
            log_to_file "Local changes committed: $COMMIT_MSG"
        else
            echo "${RED}提交失败。${NC}"; exit 1
        fi
    else
        echo "${GREEN}工作区干净。${NC}"
    fi

    # [Step 2] Pull (Rebase)
    echo "${YELLOW}[2/3] 拉取远程更新 (Rebase)...${NC}"
    if git pull --rebase --autostash origin main; then
        echo "${GREEN}拉取成功。${NC}"
    else
        echo "${RED}错误: 拉取失败！合并冲突。${NC}"
        # 生成冲突报告
        REPORT_TIME=$(date '+%Y-%m-%d_%H%M%S')
        REPORT_FILE="$REPO_PATH/log/conflict_report_${REPORT_TIME}.log"
        {
            echo "=== Conflict Report ==="
            git diff --name-only --diff-filter=U
            echo "---"
            git status
        } > "$REPORT_FILE"
        echo "${YELLOW}详情请见: $REPORT_FILE${NC}"
        log_to_file "Error: Pull failed. See $REPORT_FILE"
        exit 1
    fi

    # [Step 3] Push
    echo "${YELLOW}[3/3] 检查推送需求...${NC}"
    NEEDS_PUSH=$(git cherry -v origin/main 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$NEEDS_PUSH" -gt 0 ] || [ "$force_push" = true ]; then
        if [ "$force_push" = true ]; then
            echo "${RED}!!! 正在执行强制推送 !!!${NC}"
            CMD="git push --force origin main"
        else
            echo "${YELLOW}正在推送 ($NEEDS_PUSH commits)...${NC}"
            CMD="git push origin main"
        fi
        
        if eval "$CMD"; then
            echo "${GREEN}>>> 同步完成！${NC}"
            log_to_file "Sync completed. Pushed $NEEDS_PUSH commits."
        else
            echo "${RED}推送失败。${NC}"; exit 1
        fi
    else
        echo "${GREEN}>>> 无需推送。${NC}"
        log_to_file "Sync check: No push needed."
    fi
}

# -----------------------------------------------------------------------------
# 参数解析
# -----------------------------------------------------------------------------

# 如果没有参数，默认执行同步
if [ $# -eq 0 ]; then
    check_status # 同步前先显示状态
    run_sync false
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--status)
            check_status
            exit 0
            ;;
        -r|--report)
            generate_report
            exit 0
            ;;
        -f|--force)
            echo "${RED}警告: 您即将执行强制推送，这可能会覆盖远程的历史记录。${NC}"
            read -q "REPLY?确认执行吗? (y/n) "
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                run_sync true
            else
                echo "操作已取消。"
            fi
            exit 0
            ;;
        *)
            echo "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
    shift
done
