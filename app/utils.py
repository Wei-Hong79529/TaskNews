"""
共用工具模組 (Utility Module)
包含日誌設定、訊息格式化等共用功能。
"""

import logging
import sys
import html
from datetime import datetime


def setup_logging(level: int = logging.INFO) -> None:
    """
    初始化全域日誌設定。
    所有模組的 logger 都會繼承此設定。
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    log_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # 輸出至標準輸出 (CloudWatch Logs 可接收)
        ],
    )


def format_news_report(news_data: dict) -> str:
    """
    將抓取到的新聞資料格式化為推播用的訊息字串。

    Args:
        news_data: {分類名稱: [{"title": "...", "link": "..."}, ...]}

    Returns:
        格式化後的新聞報告字串
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_lines = [f"☀️ 每日新聞快報 ({now})", ""]

    for category, articles in news_data.items():
        report_lines.append(f"━━━ {category} ━━━")

        if not articles:
            report_lines.append("  ⚠️ 此分類暫無新聞（來源可能暫時無法存取）")
            report_lines.append("")
            continue

        for idx, article in enumerate(articles, start=1):
            title = html.escape(article.get("title", "無標題"))
            link = html.escape(article.get("link", "#"))
            report_lines.append(f"  {idx}. <a href=\"{link}\">{title}</a>")

        report_lines.append("")

    report_lines.append("📌 以上新聞由系統自動抓取，資料來源為各大新聞 RSS Feed。")
    return "\n".join(report_lines)
