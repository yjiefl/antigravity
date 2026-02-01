# 🎬 视频下载器 (YouTube & Bilibili)

一个功能强大的视频下载工具，提供友好的图形界面，支持YouTube和Bilibili视频下载，包括视频质量选择、音频下载和批量下载功能。

## ✨ 功能特性

- 🖥️ **图形界面** - 简洁美观的用户界面，操作简单
- 🌐 **多平台支持** - 支持YouTube和Bilibili视频下载
- 🎯 **质量选择** - 支持多种视频质量选项（4K、2K、1080p、720p等）
- 🎵 **音频下载** - 可单独下载音频并转换为MP3格式
- 📋 **批量下载** - 支持添加多个视频URL进行批量下载
- 🔑 **浏览器Cookies** - 自动从浏览器导入cookies，绕过YouTube机器人检测
- 📊 **实时进度** - 显示下载进度、速度和剩余时间
- 📁 **自定义路径** - 可自由选择视频保存位置
- 📝 **下载日志** - 详细的下载日志记录

## 📋 系统要求

- Python 3.7 或更高版本
- macOS / Windows / Linux

## 🚀 安装步骤

### 1. 克隆或下载项目

```bash
cd /Users/yangjie/Desktop/code/antigravity/youtube_downloader
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install yt-dlp
```

### 3. （可选）安装FFmpeg

如果需要下载音频并转换为MP3格式，需要安装FFmpeg：

**macOS (使用Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
从 [FFmpeg官网](https://ffmpeg.org/download.html) 下载并添加到系统PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🎯 使用方法

### 启动程序

```bash
python3 youtube_downloader_gui.py
```

> [!NOTE]
> 在macOS上，请使用 `python3` 命令而不是 `python`。

### 使用步骤

1. **输入视频URL**
   - 在顶部输入框中粘贴YouTube视频链接
   - 点击"添加到列表"按钮

2. **选择下载选项**
   - **下载类型**: 选择"视频+音频"或"仅音频(MP3)"
   - **视频质量**: 从下拉菜单选择所需质量（最佳质量、1080p、720p等）

3. **设置保存路径**
   - 默认保存在 `~/Downloads/YouTube/`
   - 点击"浏览..."按钮可更改保存位置

4. **批量添加（可选）**
   - 重复步骤1，可添加多个视频到下载列表
   - 可以移除或清空列表中的项目

5. **开始下载**
   - 点击"开始下载"按钮
   - 查看实时进度和下载日志
   - 可随时点击"停止下载"取消任务

## 📖 界面说明

### 主要区域

- **视频URL**: 输入YouTube视频链接
- **下载选项**: 选择下载类型和视频质量
- **保存路径**: 设置文件保存位置
- **下载列表**: 管理批量下载的视频列表
- **下载进度**: 显示当前下载进度和速度
- **下载日志**: 查看详细的下载信息和状态

### 质量选项说明

| 选项 | 说明 |
|------|------|
| 最佳质量 | 下载可用的最高质量视频 |
| 1080p | 下载1080p分辨率视频 |
| 720p | 下载720p分辨率视频（推荐） |
| 480p | 下载480p分辨率视频 |
| 360p | 下载360p分辨率视频 |
| 最小文件 | 下载最小文件大小的视频 |

## ⚠️ 注意事项

1. **版权声明**: 请仅下载您有权下载的内容，遵守YouTube服务条款
2. **网络连接**: 确保网络连接稳定，下载大文件可能需要较长时间
3. **存储空间**: 确保有足够的磁盘空间存储下载的视频
4. **FFmpeg依赖**: 下载音频功能需要安装FFmpeg
5. **URL格式**: 确保输入的是有效的YouTube视频链接

## 🐛 常见问题

### Q: 提示"command not found: python"怎么办？
A: 在macOS上，请使用 `python3` 命令：
```bash
python3 youtube_downloader_gui.py
```

### Q: 提示"ModuleNotFoundError: No module named '_tkinter'"怎么办？
A: 这是因为Python没有正确安装tkinter支持。解决方法：

**macOS (Homebrew Python):**
```bash
# 重新安装Python并包含tkinter支持
brew reinstall python-tk@3.13
```

或者使用系统自带的Python 3.12（通常已包含tkinter）：
```bash
/usr/bin/python3 youtube_downloader_gui.py
```

**验证tkinter是否可用：**
```bash
python3 -m tkinter
```
如果弹出一个小窗口，说明tkinter已正确安装。

### Q: 提示"Sign in to confirm you're not a bot"错误？
A: 这是YouTube的机器人检测机制。解决方法：

**步骤1**: 在浏览器中登录YouTube
- 打开Chrome、Firefox或Safari浏览器
- 访问 https://www.youtube.com 并登录

**步骤2**: 在下载器中选择对应的浏览器
- 在"下载选项"区域找到"使用浏览器"下拉菜单
- 选择您刚才登录的浏览器

**步骤3**: 重新下载
- 程序会自动从浏览器提取cookies进行身份验证

> [!TIP]
> 详细说明请查看 [使用说明.md](file:///Users/yangjie/Desktop/code/antigravity/youtube_downloader/使用说明.md)

### Q: 下载失败怎么办？
A: 请检查：
- 网络连接是否正常
- URL是否正确
- 视频是否可公开访问
- 是否安装了最新版本的yt-dlp

### Q: 无法下载音频？
A: 请确保已安装FFmpeg，并且FFmpeg已添加到系统PATH中

### Q: 下载速度很慢？
A: 下载速度取决于您的网络连接和YouTube服务器。可以尝试：
- 选择较低的视频质量
- 检查网络连接
- 避开网络高峰时段

### Q: 支持哪些视频网站？
A: 本程序基于yt-dlp，理论上支持1000+视频网站，但主要针对YouTube优化

## 🔄 更新依赖

定期更新yt-dlp以获得最佳兼容性：

```bash
pip install --upgrade yt-dlp
```

## 📝 许可证

本项目仅供学习和个人使用。请遵守相关法律法规和YouTube服务条款。

## 🤝 贡献

欢迎提交问题报告和改进建议！

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**免责声明**: 本工具仅用于学习和研究目的。用户应自行承担使用本工具的责任，并遵守所有适用的法律法规。
