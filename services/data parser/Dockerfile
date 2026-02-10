# 使用国内镜像源代理
FROM docker.m.daocloud.io/library/python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（增加中文字体支持）
RUN apt-get update && apt-get install -y \
	libmagic1 \
	fonts-wqy-microhei \
	&& rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 (使用清华源加速 pip)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p uploads output

# 暴露 Flask 端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
