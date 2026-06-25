FROM python:3.10-slim

WORKDIR /app

# 安装必要的编译工具，供一些 Python C 扩展包使用
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8012

CMD ["python", "main.py"]
