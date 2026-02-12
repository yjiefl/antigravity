# AI 语音转字幕 (Speech-to-Text)

这是一个基于 React 前端和 FastAPI 后端的音视频转字幕工具。它支持多种识别引擎，包括 OpenAI Whisper、Groq 以及本地运行的 Faster-Whisper。

## 主要功能

- **多引擎支持**:
  - **OpenAI Whisper API**: 极高准确率，需付费。
  - **Groq API**: 极速且目前免费，需申请 API Key。
  - **本地 Whisper**: 完全免费、私密，在本地 CPU/GPU 运行（推荐 M 系列 Mac 使用）。
- **大文件处理**: 自动压缩或切片处理超过 25MB 的文件。
- **字幕导出**: 直接生成并下载 `.srt` 格式字幕文件。
- **一键管理**: 提供 `start.sh` 和 `stop.sh` 脚本方便启动和停止服务。

## 目录结构

- `web/`: React 前端项目（运行在 5005 端口）。
- `server/`: Python FastAPI 后端服务（运行在 8000 端口）。
- `start.sh`: 启动脚本（自动清理旧进程、安装依赖并打开浏览器）。
- `stop.sh`: 停止脚本。

## 快速开始

1.  克隆仓库并进入目录。
2.  确保已安装 `ffmpeg` (处理音频必需)。
3.  编辑 `server/.env`，填入你的 `OPENAI_API_KEY` 或 `GROQ_API_KEY`（如需使用云端服务）。
4.  运行启动脚本：
    ```bash
    ./start.sh
    ```
5.  浏览器将自动打开 `http://localhost:5005`。

## 注意事项

- **本地模式**: 首次使用本地 Whisper 会下载模型文件（约几百 MB），请耐心等待。
- **环境依赖**: 需要 Python 3.8+ 和 Node.js 环境。
