# 数据分析工具 (Data Parser)

这是一个基于 Flask 的 Web 应用程序，包含以下功能：

1. **新能源功率预测分析**：分析 CSV 格式的功率预测扣分汇总数据。
2. **运营日报自动化审核**：自动审核 .xlsx 格式的运营日报表。

## 快速启动

1. 确保已安装 Python 3.12+。
2. 安装依赖：`pip install -r requirements.txt`
3. 启动服务：`./start.sh`
4. 访问地址：[http://127.0.0.1:5001](http://127.0.0.1:5001)

## 部署说明

- **本地启动**：使用 `start.sh` 脚本。
- **NAS 部署**：使用 `deploy_nas.sh` 脚本，通过 Docker 部署。
- **Docker 启动**：`docker-compose up -d --build` (端口映射 5004:5001)
