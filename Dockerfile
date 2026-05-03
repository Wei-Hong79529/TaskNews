# ==========================================
# Daily News Bot - Dockerfile
# 多階段建置，減少最終映像檔大小
# ==========================================
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 先複製依賴清單並安裝（利用 Docker layer cache 加速建置）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼
COPY . .

# 設定環境變數（避免 Python 輸出緩衝，確保日誌即時輸出至 CloudWatch）
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 預設以排程模式啟動（容器化部署場景）
# 若由外部排程器 (如 AWS EventBridge / Zeabur Cron) 觸發，可改為：
#   CMD ["python", "-m", "app.main"]
CMD ["python", "-m", "app.main"]
