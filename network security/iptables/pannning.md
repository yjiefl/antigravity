# iptables 配置脚本

## 需求

/Users/yangjie/code/antigravity/network security/iptables
做一个脚本，便于我操作远程服务器的 iptables 配置

## 功能

1. 自动识别远程服务器的 os 版本
2. 根据 os 版本，交互式选择防火墙 iptables 配置
3. 输入命令后，交互式让我输入登录远程服务器的ssh命令
4. 执行命令后，自动执行 iptables 配置，提示我是否执行
5. 危险命令进行警告
6. 完成后将所有操作情况保存到日志文件中形成报告，存放在output目录
