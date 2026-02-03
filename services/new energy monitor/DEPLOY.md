# 部署指南 (Deployment Guide)

本项目是一个单文件静态网页 (`monitor.html`)，部署非常简单。以下是将项目部署到 Linux VPS (如 Ubuntu/Debian) 的标准步骤。

## 1. 准备工作

*   一台 Linux VPS (推荐 Ubuntu 20.04 或 22.04)
*   VPS 的 IP 地址
*   SSH 登录权限 (root 用户或有 sudo 权限的用户)
*   (可选) 一个域名解析到该 VPS IP (如果想通过域名访问)

## 2. 登录 VPS

在你的本地终端执行：

```bash
ssh root@your_vps_ip
```

## 3. 安装 Nginx Web 服务器

Nginx 是一个高性能的 Web 服务器，非常适合托管静态文件。

```bash
sudo apt update
sudo apt install nginx -y
```

安装完成后，Nginx 会自动启动。你可以通过浏览器访问 `http://your_vps_ip`，如果看到 "Welcome to nginx!" 页面，说明安装成功。

## 4. 上传文件

你需要将本地的 `monitor.html` 上传到 VPS。

**方法 A: 使用 `scp` 命令 (推荐)**

在**本地电脑**的终端中（不要在 SSH 内部），运行：

```bash
# 假设你在项目根目录下
scp monitor.html root@your_vps_ip:/var/www/html/index.html
```

*注意：我们将文件名改为了 `index.html`，这样访问 IP 时无需输入文件名即可直接打开。*

**方法 B: 如果你已经在 VPS 上有 git**

你也可以在 VPS 上拉取代码库：

```bash
cd /var/www/html
rm index.nginx-debian.html  # 删除默认页
git clone <your-repo-url> .
mv monitor.html index.html
```

## 5. 验证部署

现在，再次通过浏览器访问：

`http://your_vps_ip`

你应该能看到 **光伏电站发电功率模拟器** 的页面了。

## 6. (进阶) 配置 HTTPS - 如果你有域名

如果你有一个域名（例如 `solar.example.com`）并已解析到 VPS IP，建议配置 HTTPS 加密。

1.  **安装 Certbot**:
    ```bash
    sudo apt install certbot python3-certbot-nginx -y
    ```

2.  **修改 Nginx 配置**:
    编辑 `/etc/nginx/sites-available/default`，将 `server_name _;` 修改为 `server_name solar.example.com;`。
    
    ```bash
    nano /etc/nginx/sites-available/default
    # 修改后按 Ctrl+O 保存，Ctrl+X 退出
    ```
    
    重启 Nginx:
    ```bash
    systemctl reload nginx
    ```

3.  **获取证书**:
    ```bash
    sudo certbot --nginx -d solar.example.com
    ```
    按照提示输入邮箱并同意条款。

完成后，你就可以通过 `https://solar.example.com` 安全访问了。

---

## 7. 常见问题

*   **乱码问题**: 确保 Nginx 配置中有 `charset utf-8;`，或者 HTML 文件头已包含 `<meta charset="UTF-8">` (本项目已包含)。
*   **权限问题**: 如果访问 403 Forbidden，请确保文件权限正确：
    ```bash
    chmod 644 /var/www/html/index.html
    ```

---

## 8. (新增) 部署移动端 React 应用

如果你想部署 `mobile/` 目录下的 React 高端移动版，步骤略有不同，需要先编译构建。

### 8.1 本地构建

在本地终端运行以下命令，生成静态资源包：

```bash
cd mobile
npm install     # 如果还没安装依赖
npm run build
```

这会在 `mobile/dist` 目录下生成构建好的文件（包含 `index.html` 和 assets 文件夹）。

### 8.2 上传到 VPS

将 `dist` 目录下的所有内容上传到 VPS 的 Web 目录。

**方案 A：覆盖主站**
如果你希望移动版作为主站：

```bash
# 在本地 mobile 目录下执行
scp -r dist/* root@your_vps_ip:/var/www/html/
```

**方案 B：部署到子目录 (推荐)**
如果你希望通过 `http://your_vps_ip/mobile/` 访问：

1. 在 VPS 上创建目录：
   ```bash
   mkdir -p /var/www/html/mobile
   ```

2. 上传文件：
   ```bash
   # 在本地 mobile 目录下执行
   scp -r dist/* root@your_vps_ip:/var/www/html/mobile/
   ```

### 8.3 Nginx 配置 (针对 React SPA)

React 单页应用 (SPA) 需要特殊的 Nginx 配置，以防止刷新页面时出现 404 错误。

编辑 Nginx 配置文件：
```bash
nano /etc/nginx/sites-available/default
```

在 `server` 块中添加（或修改）以下 location 块：

**如果是部署在根目录 (方案 A):**
```nginx
location / {
    root /var/www/html;
    index index.html;
    try_files $uri $uri/ /index.html;  # 关键配置：所有路由回退到 index.html
}
```

**如果是部署在子目录 (方案 B):**
```nginx
location /mobile/ {
    alias /var/www/html/mobile/;
    try_files $uri $uri/ /mobile/index.html;
}
```

保存并重启 Nginx：
```bash
systemctl reload nginx
```

现在访问对应的 URL 即可体验移动端应用。
