#!/bin/zsh

# =============================================================================
# Antigravity Git Sync Script (Ultimate)
# 功能：递归同步主仓库及所有嵌套 Git 仓库 (不管是否注册为 submodule)
# 逻辑：Nested Repos (Commit->Push) -> Main Repo (Commit->Pull->Push)
# =============================================================================

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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

# 获取所有嵌套仓库列表 (排除根目录)
get_nested_repos() {
    find "$REPO_PATH" -name ".git" -not -path "$REPO_PATH/.git" | while read git_dir; do
        dirname "$git_dir"
    done
}

# -----------------------------------------------------------------------------
# 关键功能模块
# -----------------------------------------------------------------------------

# 1. 检查状态
check_repo_status() {
    local repo_path=$1
    local name=$2
    
    # 尝试进入目录，失败则跳过
    if ! cd "$repo_path" >/dev/null 2>&1; then
        return
    fi
    
    # 检查本地修改
    LOCAL_CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    
    # 检查远程同步
    git fetch origin HEAD > /dev/null 2>&1
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
    
    if [ -z "$CURRENT_BRANCH" ]; then
        REMOTE_STATUS="${MAGENTA}Detached/No Branch${NC}"
    else
        BEHIND=$(git rev-list --count HEAD..origin/"$CURRENT_BRANCH" 2>/dev/null || echo 0)
        AHEAD=$(git rev-list --count origin/"$CURRENT_BRANCH"..HEAD 2>/dev/null || echo 0)
        
        if [ "$BEHIND" -gt 0 ]; then REMOTE_STATUS="${YELLOW}↓ 落后 $BEHIND${NC}"; 
        elif [ "$AHEAD" -gt 0 ]; then REMOTE_STATUS="${YELLOW}↑ 领先 $AHEAD${NC}";
        else REMOTE_STATUS="${GREEN}✓ 同步${NC}"; fi
    fi

    if [ "$LOCAL_CHANGES" -gt 0 ]; then
        FILE_STATUS="${YELLOW}● 修改: $LOCAL_CHANGES${NC}"
    else
        FILE_STATUS="${GREEN}✓ 干净${NC}"
    fi
    
    # 计算相对路径用于显示
    REL_PATH=${repo_path#$REPO_PATH/}
    if [ "$repo_path" = "$REPO_PATH" ]; then REL_PATH="Main (Root)"; fi
    
    printf "%-40s %-20s %s\n" "$REL_PATH" "$FILE_STATUS" "$REMOTE_STATUS"
}

run_check_status() {
    echo "${BLUE}>>> 仓库状态概览 (自动扫描所有嵌套仓库)...${NC}"
    printf "${CYAN}%-40s %-20s %s${NC}\n" "仓库/模块" "工作区" "远程状态"
    echo "--------------------------------------------------------------------------------"
    
    # 1. 检查主仓库
    check_repo_status "$REPO_PATH" "Main (Root)"
    
    # 2. 检查所有嵌套仓库
    get_nested_repos | while read repo; do
        check_repo_status "$repo"
    done
    
    echo "--------------------------------------------------------------------------------"
    log_to_file "Checked repo status."
}

# 2. 生成报告
run_generate_report() {
    REPORT_TIME=$(date '+%Y-%m-%d_%H%M%S')
    REPORT_FILE="$REPO_PATH/log/repo_status_${REPORT_TIME}.txt"
    echo "${BLUE}>>> 正在生成详细报告...${NC}"
    {
        echo "=== Repository Status Report ==="
        echo "Generated: $(date)"
        echo ""
        echo ">>> Main Repository"
        cd "$REPO_PATH" && git status
        echo ""
        echo ">>> Nested Repositories"
        get_nested_repos | while read repo; do
            echo "--- ${repo#$REPO_PATH/} ---"
            cd "$repo" && git status -s
            echo ""
        done
    } > "$REPORT_FILE"
    echo "${GREEN}报告已生成: $REPORT_FILE${NC}"
    log_to_file "Generated report: $REPORT_FILE"
}

# 3. 核心同步逻辑 (单个仓库)
sync_one_repo() {
    local repo_path=$1
    local name=$2
    local force=$3
    
    if ! cd "$repo_path" >/dev/null 2>&1; then
        echo "${RED}错误: 无法进入 $repo_path${NC}"
        return
    fi
    
    echo "${CYAN}>>> 同步: $name${NC}"
    
    # Commit
    STATUS=$(git status --porcelain 2>/dev/null)
    if [ -n "$STATUS" ]; then
        echo "   ${YELLOW}检测到修改，正在提交...${NC}"
        git add .
        COMMIT_MSG="chore: auto sync updates at $(date '+%Y-%m-%d %H:%M:%S')"
        if git commit -m "$COMMIT_MSG"; then
            echo "   ${GREEN}已提交。${NC}"
            log_to_file "[$name] Committed changes."
        fi
    else
        echo "   ${GREEN}工作区干净。${NC}"
    fi
    
    # Pull
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -z "$BRANCH" ]; then
        echo "   ${MAGENTA}警告: Detached HEAD 或非 Git 目录，跳过 Pull/Push。${NC}"
        return
    fi

    echo "   ${YELLOW}正在拉取 (Rebase)...${NC}"
    if git pull --rebase --autostash origin "$BRANCH" 2>/dev/null; then
        echo "   ${GREEN}拉取成功。${NC}"
    else
        echo "   ${RED}错误: 拉取失败 (冲突)。停止同步该仓库。${NC}"
        log_to_file "[$name] Pull failed."
        return # 子模块失败不应终止整个脚本，继续下一个
    fi
    
    # Push
    NEEDS_PUSH=$(git cherry -v origin/"$BRANCH" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$NEEDS_PUSH" -gt 0 ] || [ "$force" = true ]; then
        echo "   ${YELLOW}正在推送...${NC}"
        if [ "$force" = true ]; then
            git push --force origin "$BRANCH"
        else
            git push origin "$BRANCH"
        fi
        
        if [ $? -eq 0 ]; then
            echo "   ${GREEN}推送成功。${NC}"
            log_to_file "[$name] Pushed changes."
        else
            echo "   ${RED}推送失败。${NC}"
        fi
    else
        echo "   ${GREEN}无需推送。${NC}"
    fi
}

# 4. 执行全量同步
run_full_sync() {
    local force=$1
    echo "${GREEN}=== 开始递归同步 (自动扫描所有嵌套仓库) ===${NC}"
    log_to_file "Started recursive sync (Force: ${force:-false})."
    
    # 同步所有嵌套仓库
    get_nested_repos | while read repo; do
        REL_PATH=${repo#$REPO_PATH/}
        sync_one_repo "$repo" "$REL_PATH" "$force"
    done
    
    # 同步主仓库
    sync_one_repo "$REPO_PATH" "Main Repository" "$force"
    
    echo "${GREEN}=== 所有同步完成 ===${NC}"
    log_to_file "Recursive sync completed."
}

# -----------------------------------------------------------------------------
# 交互式菜单
# -----------------------------------------------------------------------------
show_menu() {
    clear
    echo "${CYAN}=========================================${NC}"
    echo "${CYAN}   Antigravity Git Sync Tool (Ultimate)  ${NC}"
    echo "${CYAN}=========================================${NC}"
    echo "1. ${GREEN}全量同步${NC} (递归扫描所有Git仓库)"
    echo "2. ${BLUE}检查状态${NC} (查看所有嵌套仓库状态)"
    echo "3. ${YELLOW}生成报告${NC} (导出状态到文件)"
    echo "4. ${RED}强制推送${NC} (慎用, 覆盖远程)"
    echo "0. ${NC}退出${NC}"
    echo "-----------------------------------------"
    echo -n "请选择功能 [1-4]: "
    read choice
    echo ""
    
    case $choice in
        1) run_full_sync false ;;
        2) run_check_status ;;
        3) run_generate_report ;;
        4) 
           echo "${RED}警告: 强制推送可能会覆盖远程记录。${NC}"
           echo -n "确认要继续吗? (y/n): "
           read confirm
           if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
               run_full_sync true
           else
               echo "操作已取消。"
           fi
           ;;
        0) echo "再见！"; exit 0 ;;
        *) echo "${RED}无效选项，请重新运行。${NC}" ;;
    esac
}

# -----------------------------------------------------------------------------
# 入口逻辑
# -----------------------------------------------------------------------------

# 如果有命令行参数，优先处理参数
if [ $# -gt 0 ]; then
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help) 
                echo "用法: ./git_sync.sh [无参数进入菜单]" 
                echo "  -s  检查状态"
                echo "  -r  生成报告"
                exit 0 ;;
            -s|--status) run_check_status; exit 0 ;;
            -r|--report) run_generate_report; exit 0 ;;
            -f|--force)  run_full_sync true; exit 0 ;;
            *) echo "无效选项: $1"; exit 1 ;;
        esac
        shift
    done
else
    # 无参数时，显示交互式菜单
    show_menu
fi
