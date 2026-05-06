"""
測試模組：推播服務 (Notifier)
"""
import pytest
from unittest.mock import patch, MagicMock
from app.notifier import TelegramNotifier


class TestTelegramNotifier:
    """Telegram 推播服務測試"""

    @patch.dict("os.environ", {"TELEGRAM_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "12345"})
    @patch("app.notifier.requests.post")
    def test_send_success(self, mock_post):
        """測試正常推播成功"""
        mock_post.return_value.raise_for_status = MagicMock()
        notifier = TelegramNotifier()
        result = notifier.send("Hello!")
        assert result is True
        mock_post.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)
    def test_send_missing_config(self):
        """測試缺少 Token 時回傳 False"""
        notifier = TelegramNotifier()
        result = notifier.send("Hello!")
        assert result is False

    def test_split_message_short(self):
        """測試短訊息不需切分"""
        chunks = TelegramNotifier._split_message("short", max_length=4096)
        assert len(chunks) == 1

    def test_split_message_long(self):
        """測試長訊息正確切分"""
        long_msg = "a" * 10000
        chunks = TelegramNotifier._split_message(long_msg, max_length=4096)
        assert len(chunks) == 3


# class TestLineNotifier:
#     """LINE 推播服務測試"""
# 
#     @patch.dict("os.environ", {"LINE_TOKEN": "test_token", "LINE_USER_ID": "U123"})
#     @patch("app.notifier.requests.post")
#     def test_send_success(self, mock_post):
#         """測試正常推播成功"""
#         mock_post.return_value.raise_for_status = MagicMock()
#         # notifier = LineNotifier()
#         # result = notifier.send("Hello!")
#         # assert result is True
# 
#     @patch.dict("os.environ", {}, clear=True)
#     def test_send_missing_config(self):
#         """測試缺少 Token 時回傳 False"""
#         # notifier = LineNotifier()
#         # result = notifier.send("Hello!")
#         # assert result is False
