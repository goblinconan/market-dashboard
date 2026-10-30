FROM python:3.11-slim-bookworm

WORKDIR /app

# akshare / pandas 通常不需要从源码编译，gcc 可以去掉
# 如果后续确实需要编译，再换回国内 apt 源安装 gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]