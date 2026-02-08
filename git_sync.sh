#!/bin/zsh

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 无颜色

REPO_PATH="/Users/yangjie/code/antigravity"

# 进入项目目录
cd "$REPO_PATH" || { echo "${RED}错误: 无法进入目录 $REPO_PATH${NC}"; exit 1; }

echo "${GREEN}>>> 正在同步仓库: $REPO_PATH${NC}"

# 1. 执行 Pull
echo "${YELLOW}正在拉取远程更新...${NC}"
if ! git pull origin main; then
    echo "${RED}错误: 拉取失败！可能存在合并冲突或网络问题，请手动处理。${NC}"
    exit 1
fi
echo "${GREEN}拉取成功。${NC}"

# 2. 检查本地修改
echo "${YELLOW}检查本地修改情况...${NC}"
STATUS=$(git status --porcelain)

if [ -z "$STATUS" ]; then
    echo "没有本地修改需要同步。"
else
    echo "${YELLOW}检测到以下修改:${NC}"
    echo "$STATUS"
    
    # 3. Add 和 Commit
    echo "${YELLOW}正在提交修改...${NC}"
    git add .
    COMMIT_MSG="chore: auto sync updates at $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
fi

# 4. 执行 Push
echo "${YELLOW}正在推送到远程仓库...${NC}"
if git push origin main; then
    echo "${GREEN}Done! 同步完成！${NC}"
else
    echo "${RED}错误: 推送失败！${NC}"
    exit 1
fi
