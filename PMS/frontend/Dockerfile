FROM node:20-alpine

WORKDIR /app

# 复制 package.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 5173

# 开发模式启动
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
