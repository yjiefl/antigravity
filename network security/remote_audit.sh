#!/bin/bash

# ==============================================================================
# 脚本名称: remote_audit.sh
# 描述: 远端安全审计控制器，通过 SSH 登陆 aliecs 执行审计程序并取回报告
# 作者: AntiGravity
# 版本: 1.0.0
# 日期: 2026-02-13
# ==============================================================================

# 配置
REMOTE_ALIAS="aliecs"
REMOTE_TMP_SCRIPT="/tmp/audit_worker.sh"
LOCAL_AUDIT_SCRIPT="./audit.sh"
REPORT_NAME="security_audit_report.md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] 准备执行远端审计 (Host: $REMOTE_ALIAS)...${NC}"

# 1. 检查本地审计脚本是否存在
if [ ! -f "$LOCAL_AUDIT_SCRIPT" ]; then
    echo -e "${RED}[!] 错误: 找不到本地审计脚本 $LOCAL_AUDIT_SCRIPT${NC}"
    exit 1
fi

# 2. 将脚本传输到远端
echo -e "[*] 正在传输审计脚本到远端..."
scp "$LOCAL_AUDIT_SCRIPT" "${REMOTE_ALIAS}:${REMOTE_TMP_SCRIPT}"
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] 错误: SCP 传输失败，请检查免密登陆配置 (ssh $REMOTE_ALIAS)${NC}"
    exit 1
fi

# 3. 在远端执行脚本
echo -e "[*] 正在远端执行审计 (需要 sudo 权限)..."
# 注意：使用 -t 分配伪终端以支持 sudo 的可能交互（虽然免密 sudo 更好）
ssh -t "$REMOTE_ALIAS" "chmod +x $REMOTE_TMP_SCRIPT && sudo $REMOTE_TMP_SCRIPT && rm $REMOTE_TMP_SCRIPT"

# 4. 取回报告
echo -e "[*] 正在取回审计报告..."
rm -f "./$REPORT_NAME" # 先删除本地可能存在的旧报告（防止权限冲突）
scp "${REMOTE_ALIAS}:./$REPORT_NAME" "./$REPORT_NAME"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] 审计完成！报告已保存至本地: ./${REPORT_NAME}${NC}"
else
    # 尝试从 root 目录下查找报告（如果 sudo 运行后报告在 /root）
    ssh "$REMOTE_ALIAS" "sudo cp /root/$REPORT_NAME /tmp/$REPORT_NAME && sudo chmod 644 /tmp/$REPORT_NAME"
    scp "${REMOTE_ALIAS}:/tmp/$REPORT_NAME" "./$REPORT_NAME"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] 审计完成！报告已保存至本地: ./${REPORT_NAME}${NC}"
        ssh "$REMOTE_ALIAS" "sudo rm /tmp/$REPORT_NAME /root/$REPORT_NAME"
    else
        echo -e "${RED}[!] 警告: 未能取回报告，请检查远端脚本是否运行成功${NC}"
    fi
fi
