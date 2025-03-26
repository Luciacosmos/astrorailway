FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口（默认 5000）
EXPOSE 5000

# 使用 shell 形式启动 gunicorn，通过环境变量 PORT 绑定端口
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
