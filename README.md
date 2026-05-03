# 📰 Daily News Automation System
# 每日新聞自動化推播系統

自動抓取台灣、國際及財經新聞，每日 08:00 推播至 Telegram 與 LINE。

## 📁 專案結構

```
ImplentSpec/
├── app/
│   ├── __init__.py          # 套件初始化
│   ├── main.py              # 主程式入口 (支援排程 / 單次執行 / Lambda)
│   ├── scrapers.py          # 新聞抓取策略模式 (Strategy Pattern)
│   ├── notifier.py          # 推播服務介面 (Telegram / LINE)
│   └── utils.py             # 共用工具 (日誌、格式化)
├── tests/
│   ├── test_scrapers.py     # 爬蟲單元測試
│   ├── test_notifier.py     # 推播單元測試
│   └── test_utils.py        # 工具函式測試
├── infra/
│   └── main.tf              # Terraform IaC (AWS Lambda + EventBridge)
├── .github/workflows/
│   └── deploy.yml           # CI/CD 流水線 (GitHub Actions)
├── Dockerfile               # 容器化部署
├── requirements.txt         # Python 依賴
├── .env.example             # 環境變數範本
└── .gitignore
```

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp .env.example .env
# 編輯 .env 填入你的 Telegram / LINE Token
```

### 3. 單次執行
```bash
python -m app.main
```

### 4. 排程模式 (每日 08:00 自動推播)
```bash
python -m app.main --schedule
```

### 5. Docker 部署
```bash
docker build -t daily-news-bot .
docker run --env-file .env daily-news-bot
```

## 🧪 測試
```bash
pip install pytest
pytest tests/ -v
```

## ☁️ 雲端部署 (Google Cloud Platform)

本專案使用 **Google Cloud Run Jobs** 配合 **Cloud Scheduler** 實現每日自動化推播。

### 1. 基礎設施部署 (Terraform)
參考 `infra/main.tf`，使用 Terraform 一鍵部署 GCP 資源：
```bash
cd infra
terraform init
# 需提供 GCP Project ID 與 Telegram Token
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="telegram_token=YOUR_TOKEN" -var="telegram_chat_id=YOUR_ID"
```

### 2. CI/CD 流水線 (GitHub Actions)
每次推送到 `main` 分支時，GitHub Actions 會：
1. 執行測試 (`pytest`)。
2. 編譯 Docker 映像檔並推送至 **Artifact Registry**。
3. 更新 **Cloud Run Job** 映像檔。

**GitHub Secrets 設定：**
* `GCP_PROJECT_ID`: 您的 GCP 專案 ID。
* `GCP_SA_KEY`: 具備 Artifact Registry 與 Cloud Run 管理權限的 Service Account JSON Key。

## 📡 新聞來源
| 分類 | RSS Feed |
|------|----------|
| 台灣新聞 | Google News Taiwan |
| 國際新聞 | BBC World |
| 財經新聞 | Bloomberg Markets |
