"""
測試模組：工具函式 (Utils)
"""
from app.utils import format_news_report


class TestFormatNewsReport:
    """新聞報告格式化測試"""

    def test_format_with_data(self):
        """測試有新聞資料時的格式化"""
        data = {
            "台灣新聞": [
                {"title": "新聞標題 1", "link": "https://example.com/1"},
                {"title": "新聞標題 2", "link": "https://example.com/2"},
            ]
        }
        result = format_news_report(data)
        assert "台灣新聞" in result
        assert "新聞標題 1" in result
        assert "https://example.com/1" in result

    def test_format_with_empty_category(self):
        """測試空分類顯示警告"""
        data = {"空分類": []}
        result = format_news_report(data)
        assert "暫無新聞" in result

    def test_format_header(self):
        """測試報告標頭"""
        data = {}
        result = format_news_report(data)
        assert "每日新聞快報" in result
