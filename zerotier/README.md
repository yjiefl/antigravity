# ZeroTier Moon 部署脚本

这是一个用于自动化部署 ZeroTier Moon 服务器的 Bash 脚本。

## 功能

### 1. Moon 部署模式

* 自动检测并安装 ZeroTier。
* 配置 Moon 定义文件 (`moon.json`)。
* 生成签名 `.moon` 文件并部署。
* 将生成的 Moon 文件下载到本地备份。
* 提供客户端加入 Moon 的命令。

### 2. Planet (ztncui) 部署模式

* 自动化部署 ZeroTier Web 控制器 (ztncui)。
* 支持 HTTP/HTTPS 访问配置。
* 自动集成 ZeroTier 认证 Token。

## 使用方法

1. 确保你能够通过 SSH 连接到目标服务器（建议配置 SSH Key 免密登录）。
2. 运行脚本：

    ```bash
    chmod +x deploy_moon.sh
    ./deploy_moon.sh
    ```

3. 根据提示输入 SSH 连接地址（例如 `root@192.168.1.100`）。
4. 选择部署模式：输入 `1` (Moon) 或 `2` (Planet)。

## 输出

* **Moon**: 生成的 `.moon` 文件将保存在 `output/YYYYMMDD_HHMMSS_<MoonID>/` 目录下。
* **Planet**: 部署完成后会输出 Web 控制台访问地址及默认凭据。

## 注意事项

* **Moon**: 请确保云服务器放行 **UDP 9993** 端口。
* **Planet**: 请确保云服务器放行 **TCP 3443** (HTTPS) 端口。
