#!/bin/bash

# ==============================================================================
# 脚本名称: remote_audit.sh
# 描述: 远端安全审计控制器，支持用户输入 SSH 命令 (免密登陆) 执行审计
# 作者: AntiGravity
# 版本: 1.1.0
# 日期: 2026-02-13
# ==============================================================================

# 配置
REMOTE_TMP_SCRIPT="/tmp/audit_worker.sh"
LOCAL_AUDIT_SCRIPT="./audit.sh"
REPORT_NAME="security_audit_report.md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 1. 检查本地审计脚本是否存在
if [ ! -f "$LOCAL_AUDIT_SCRIPT" ]; then
    echo -e "${RED}[!] 错误: 找不到本地审计脚本 $LOCAL_AUDIT_SCRIPT${NC}"
    exit 1
fi

# 2. 交互式获取 SSH 命令
echo -en "${GREEN}请输入您的 SSH 登录命令 (例如 'ssh aliecs' 或 'ssh user@8.8.8.8'): ${NC}"
read -r SSH_CMD_INPUT

# 简单验证输入
if [[ -z "$SSH_CMD_INPUT" ]]; then
    echo -e "${RED}[!] 错误: 未输入任何命令${NC}"
    exit 1
fi

# 提取主机别名/地址 (去除 ssh 前缀和可能的参数，简单提取最后一个参数作为 host)
# 假设用户输入的是形如 "ssh -p 22 user@host" 或 "ssh alias"
# 我们保留完整的 SSH 命令用于执行，但需要提取目标 Host 用于 SCP
# 这里我们尝试解析出 scp 需要的目标字符串
# 如果用户输入 "ssh myserver", 目标是 "myserver"
# 如果用户输入 "ssh -p 2202 root@1.2.3.4", 目标是 "root@1.2.3.4", 但 scp 需要 -P 2202
# 为了简化，我们直接使用用户输入的完整命令来提取连接信息可能比较复杂。
# 更好的策略是：让用户确保输入的是可以直接 ssh 连接的命令，我们尝试复用该命令进行 scp？
# 或许直接复用 ssh 连接管道传输文件更稳妥？ (cat script | ssh host "cat > /tmp/script")

# 解析 Host (取最后一个参数)
# 这是一个简化的假设，用户输入的最后一个部分通常是 destinations
eval "SSH_ARGS=($SSH_CMD_INPUT)"
REMOTE_TARGET="${SSH_ARGS[-1]}"

# 提取非 host 参数 (例如 -p 2222, -i key.pem)
# 移除第一个 'ssh' (如果存在) 和最后一个 element
SSH_OPTS=""
if [[ "${SSH_ARGS[0]}" == "ssh" ]]; then
    unset 'SSH_ARGS[0]'
fi
unset 'SSH_ARGS[${#SSH_ARGS[@]}-1]'
SSH_OPTS="${SSH_ARGS[@]}"

echo -e "${GREEN}[*] 目标主机: $REMOTE_TARGET (选项: ${SSH_OPTS:-默认})${NC}"

# 3. 将脚本传输到远端 (使用 ssh 管道传输，兼容性更好，无需构造 scp 命令)
echo -e "[*] 正在传输审计脚本到远端..."
# cat $LOCAL_AUDIT_SCRIPT | ssh $SSH_OPTS $REMOTE_TARGET "cat > $REMOTE_TMP_SCRIPT"
# 使用 eval 执行用户输入的 ssh 命令结构
eval "$SSH_CMD_INPUT \"cat > $REMOTE_TMP_SCRIPT\" < \"$LOCAL_AUDIT_SCRIPT\""

if [ $? -ne 0 ]; then
    echo -e "${RED}[!] 错误: 传输失败，请检查 SSH 连接能否正常工作${NC}"
    exit 1
fi

# 4. 在远端执行脚本
echo -e "[*] 正在远端执行审计 (需要 sudo 权限)..."
# 增加权限并执行
CMD_EXEC="chmod +x $REMOTE_TMP_SCRIPT && sudo $REMOTE_TMP_SCRIPT && rm $REMOTE_TMP_SCRIPT"
eval "$SSH_CMD_INPUT -t \"$CMD_EXEC\""

# 5. 取回报告
echo -e "[*] 正在取回审计报告..."
rm -f "./$REPORT_NAME"

# 从远端读取报告内容写入本地 (避免 SCP 参数解析问题)
# 尝试从当前目录或 /root/ 或 /tmp/ 读取
READ_CMD="if [ -f ./$REPORT_NAME ]; then cat ./$REPORT_NAME; elif [ -f /root/$REPORT_NAME ]; then sudo cat /root/$REPORT_NAME; else cat /tmp/$REPORT_NAME 2>/dev/null; fi"

# 抓取输出
eval "$SSH_CMD_INPUT \"$READ_CMD\"" > "./$REPORT_NAME"

# 检查文件大小判断是否成功
if [ -s "./$REPORT_NAME" ]; then
    echo -e "${GREEN}[+] 审计完成！报告已保存至本地: ./${REPORT_NAME}${NC}"
    # 清理远端报告
    CLEAN_CMD="rm -f ./$REPORT_NAME /tmp/$REPORT_NAME; sudo rm -f /root/$REPORT_NAME 2>/dev/null"
    eval "$SSH_CMD_INPUT \"$CLEAN_CMD\""
else
    echo -e "${RED}[!] 警告: 未能取回报告，或报告为空。请检查远端执行日志。${NC}"
    rm -f "./$REPORT_NAME"
fi
