# 语音转文本项目规范

## 1. 架构与选型

- **后端**: FastAPI (Python 3.10+)
- **前端**: React + Vite
- **语音识别**: OpenAI Whisper API

## 2. 关键流程

- 用户在网页上传音频文件。
- 后端接收文件，若超过 25MB 则进行压缩或分段处理。
- 调用 OpenAI Whisper API 进行转录。
- 返回 SRT 格式的字幕数据。

## 3. 运行环境

- 后端依赖: `pip install -r server/requirements.txt`
- 前端依赖: `cd web && npm install`

## 4. 启动与停止

- 使用 `start.sh` 启动所有服务。
- 使用 `stop.sh` 停止所有服务。
