"""
推播服務模組 (Notification Service Module)
定義統一的推播介面 (Interface Segregation Principle)，
確保 Telegram 與 LINE 的實作互不干擾。
新增推播平台只需繼承 Notifier 類別即可。
"""

import os
import logging
import requests
from abc import ABC, abstractmethod

# 設定模組級別的 logger
logger = logging.getLogger(__name__)


class Notifier(ABC):
    """推播服務抽象基類"""

    @abstractmethod
    def send(self, message: str) -> bool:
        """
        發送推播訊息。
        Args:
            message: 要推播的訊息內容
        Returns:
            bool: 發送成功回傳 True，失敗回傳 False
        """
        pass


class TelegramNotifier(Notifier):
    """
    Telegram Bot 推播服務
    使用 Telegram Bot API 的 sendMessage 端點發送訊息。
    需要環境變數：TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send(self, message: str) -> bool:
        """透過 Telegram Bot API 發送訊息"""
        if not self.token or not self.chat_id:
            logger.error("Telegram 設定不完整：缺少 TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID 環境變數")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        try:
            # Telegram 單則訊息長度上限為 4096 字元，超過需要分段發送
            chunks = self._split_message(message, max_length=4096)
            for chunk in chunks:
                response = requests.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": chunk,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,  # 避免大量連結產生預覽
                    },
                    timeout=30,
                )
                response.raise_for_status()

            logger.info(f"Telegram 推播成功 (共 {len(chunks)} 則訊息)")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram 推播失敗: {e}")
            return False

    @staticmethod
    def _split_message(text: str, max_length: int = 4096) -> list:
        """將過長的訊息切分為多段"""
        if len(text) <= max_length:
            return [text]
        chunks = []
        while text:
            chunks.append(text[:max_length])
            text = text[max_length:]
        return chunks


# [LINE 暫時停用] 若需啟用，請取消以下註解
# class LineNotifier(Notifier):
#     """
#     LINE Messaging API 推播服務
#     使用 LINE Messaging API 的 push message 端點發送訊息。
#     需要環境變數：LINE_TOKEN, LINE_USER_ID
#     """
#
#     def __init__(self):
#         self.token = os.getenv("LINE_TOKEN")
#         self.user_id = os.getenv("LINE_USER_ID")
#
#     def send(self, message: str) -> bool:
#         """透過 LINE Messaging API 發送推播訊息"""
#         if not self.token or not self.user_id:
#             logger.error("LINE 設定不完整：缺少 LINE_TOKEN 或 LINE_USER_ID 環境變數")
#             return False
#
#         url = "https://api.line.me/v2/bot/message/push"
#         headers = {
#             "Authorization": f"Bearer {self.token}",
#             "Content-Type": "application/json",
#         }
#
#         try:
#             # LINE 單則訊息上限 5000 字元，超過需分段
#             chunks = self._split_message(message, max_length=5000)
#             # LINE 單次 push 最多 5 則訊息
#             for i in range(0, len(chunks), 5):
#                 batch = chunks[i : i + 5]
#                 payload = {
#                     "to": self.user_id,
#                     "messages": [{"type": "text", "text": chunk} for chunk in batch],
#                 }
#                 response = requests.post(url, json=payload, headers=headers, timeout=30)
#                 response.raise_for_status()
#
#             logger.info(f"LINE 推播成功 (共 {len(chunks)} 則訊息)")
#             return True
#
#         except requests.exceptions.RequestException as e:
#             logger.error(f"LINE 推播失敗: {e}")
#             return False
#
#     @staticmethod
#     def _split_message(text: str, max_length: int = 5000) -> list:
#         """將過長的訊息切分為多段"""
#         if len(text) <= max_length:
#             return [text]
#         chunks = []
#         while text:
#             chunks.append(text[:max_length])
#             text = text[max_length:]
#         return chunks
