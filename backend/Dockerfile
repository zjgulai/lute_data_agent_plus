FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（含 Playwright 所需的依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright Chromium 浏览器
RUN playwright install chromium

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
