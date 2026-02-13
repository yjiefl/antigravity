# ZeroTier Moon 部署脚本

这是一个用于自动化部署 ZeroTier Moon 服务器的 Bash 脚本。

## 功能

* 自动检测并安装 ZeroTier。
* 配置 Moon 定义文件 (`moon.json`)。
* 生成签名 `.moon` 文件并部署。
* 将生成的 Moon 文件下载到本地备份。
* 提供客户端加入 Moon 的命令。

## 使用方法

1. 确保你能够通过 SSH 连接到目标服务器（建议配置 SSH Key 免密登录）。
2. 运行脚本：

    ```bash
    chmod +x deploy_moon.sh
    ./deploy_moon.sh
    ```

3. 根据提示输入 SSH 连接地址（例如 `root@192.168.1.100`）和公网 IP。

## 输出

脚本运行完成后，生成的 `.moon` 文件将保存在 `output/YYYYMMDD_HHMMSS_<MoonID>/` 目录下。

## 注意事项

* 请确保云服务器的安全组/通过防火墙放行 **UDP 9993** 端口。
