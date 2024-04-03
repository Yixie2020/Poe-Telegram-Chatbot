# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim-bullseye

# 设置工作目录
WORKDIR /app

# 将 requirements.txt 文件复制到容器中
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录的文件复制到容器的/app目录
COPY . .

# 设置容器的默认命令为 python bot.py
CMD ["python", "bot.py"]
