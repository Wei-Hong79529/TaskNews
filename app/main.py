"""
每日新聞自動化推播系統 - 主程式入口
Daily News Automation System - Main Entry Point

功能：
  1. 從多個 RSS Feed 來源抓取每日新聞 (台灣、國際、財經)
  2. 格式化為推播訊息
  3. 透過 Telegram Bot 推播 (LINE Messaging API 暫時停用)
  4. 支援排程模式 (APScheduler) 或單次執行模式

使用方式：
  - 單次執行：python app/main.py
  - 排程模式：python app/main.py --schedule
"""

import os
import sys
import logging
import argparse

# 載入 .env 環境變數（本地開發用；生產環境由雲端平台管理）
from dotenv import load_dotenv

load_dotenv()

# 匯入自定義模組
from app.scrapers import NEWS_SOURCES
from app.notifier import TelegramNotifier  # , LineNotifier  # LINE 暫時停用
from app.utils import setup_logging, format_news_report

# 設定 logger
logger = logging.getLogger(__name__)


def run_daily_job() -> None:
    """
    執行每日新聞抓取與推播任務。
    此函數為核心業務邏輯，可被排程器或 AWS Lambda handler 直接呼叫。
    """
    logger.info("=" * 50)
    logger.info("🚀 開始執行每日新聞抓取任務...")
    logger.info("=" * 50)

    # ====== 階段一：抓取新聞 ======
    news_data = {}
    for category, scraper in NEWS_SOURCES.items():
        logger.info(f"📡 正在抓取分類: {category}")
        articles = scraper.fetch()
        news_data[category] = articles
        logger.info(f"   → 取得 {len(articles)} 筆新聞")

    # ====== 階段二：格式化報告 ======
    report = format_news_report(news_data)
    logger.info(f"📝 新聞報告已產生 (共 {len(report)} 字元)")

    # ====== 階段三：推播通知 ======
    notifiers = []

    # 只在有設定 Token 的情況下才啟用對應的推播管道
    if os.getenv("TELEGRAM_TOKEN"):
        notifiers.append(("Telegram", TelegramNotifier()))
    else:
        logger.warning("⚠️ 未設定 TELEGRAM_TOKEN，跳過 Telegram 推播")

    # [LINE 暫時停用] 若需啟用，請取消以下註解並匯入 LineNotifier
    # if os.getenv("LINE_TOKEN"):
    #     notifiers.append(("LINE", LineNotifier()))
    # else:
    #     logger.warning("⚠️ 未設定 LINE_TOKEN，跳過 LINE 推播")

    if not notifiers:
        logger.warning("⚠️ 沒有任何推播管道被啟用！請至少設定一組 Token。")
        logger.info("以下為本次產生的新聞報告內容：")
        print("\n" + report + "\n")
        return

    success_count = 0
    for name, notifier in notifiers:
        logger.info(f"📤 正在透過 {name} 發送推播...")
        if notifier.send(report):
            success_count += 1
        else:
            logger.error(f"❌ {name} 推播失敗")

    logger.info(f"✅ 每日新聞任務完成！成功推播至 {success_count}/{len(notifiers)} 個管道。")


def start_scheduler() -> None:
    """
    啟動 APScheduler 排程器，設定每日 08:00 (Asia/Taipei) 自動執行新聞推播。
    適用於長時間運行的容器化部署場景。
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BlockingScheduler()

    # 設定 Cron Job：每日早上 08:00 (台灣時間)
    trigger = CronTrigger(hour=8, minute=0, timezone="Asia/Taipei")
    scheduler.add_job(run_daily_job, trigger=trigger, id="daily_news_job", name="每日新聞推播")

    logger.info("⏰ 排程器已啟動！每日 08:00 (Asia/Taipei) 將自動執行新聞推播。")
    logger.info("   按 Ctrl+C 可停止排程器。")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 排程器已手動停止。")
        scheduler.shutdown()


def start_server() -> None:
    """
    啟動簡易 Web Server，用於 Cloud Run 等需要監聽 HTTP Port 的環境。
    提供 / 端點作健康檢查，/trigger 端點可手動觸發抓取任務。
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import threading

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("TaskNews Service is running. Use /trigger to run job.".encode("utf-8"))
            elif self.path == '/trigger':
                # 在背景執行，避免阻斷回應
                threading.Thread(target=run_daily_job).start()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("Job triggered in background.".encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), RequestHandler)
    logger.info(f"🌐 Web Server 啟動，監聽 Port {port} (支援 Cloud Run 部署)")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Web Server 已停止。")
        server.server_close()


# ==========================================
# AWS Lambda 入口點 (若使用 Serverless 部署)
# ==========================================
def lambda_handler(event, context):
    """
    AWS Lambda handler。
    當 CloudWatch Event (cron) 觸發 Lambda 時，會呼叫此函數。
    """
    setup_logging()
    run_daily_job()
    return {"statusCode": 200, "body": "Daily news job completed."}


# ==========================================
# 主程式入口
# ==========================================
if __name__ == "__main__":
    # 初始化日誌系統
    setup_logging()

    # 解析命令列參數
    parser = argparse.ArgumentParser(description="每日新聞自動化推播系統")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="啟用排程模式（每日 08:00 自動執行）",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="啟動 Web Server 模式 (支援 HTTP 端點觸發)",
    )
    args = parser.parse_args()

    # 自動偵測：如果環境變數有 PORT（如 Cloud Run），或是帶有 --server 參數，就啟動 Web Server
    if args.server or "PORT" in os.environ:
        start_server()
    elif args.schedule:
        start_scheduler()
    else:
        # 單次執行模式
        run_daily_job()
