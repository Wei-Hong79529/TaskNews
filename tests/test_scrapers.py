"""
測試模組：新聞抓取器 (Scrapers)
"""
import pytest
from unittest.mock import patch, MagicMock
from app.scrapers import RSSScraper, NEWS_SOURCES


class TestRSSScraper:
    """RSSScraper 單元測試"""

    def test_fetch_returns_list(self):
        """測試 fetch() 回傳值為 list"""
        scraper = RSSScraper(url="https://example.com/rss", limit=5)
        with patch("app.scrapers.feedparser.parse") as mock_parse:
            mock_entry = MagicMock()
            mock_entry.title = "Test News"
            mock_entry.link = "https://example.com/1"
            mock_parse.return_value.entries = [mock_entry]
            mock_parse.return_value.bozo = False
            result = scraper.fetch()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["title"] == "Test News"

    def test_fetch_respects_limit(self):
        """測試 limit 參數正確限制回傳數量"""
        scraper = RSSScraper(url="https://example.com/rss", limit=2)
        with patch("app.scrapers.feedparser.parse") as mock_parse:
            entries = []
            for i in range(5):
                e = MagicMock()
                e.title = f"News {i}"
                e.link = f"https://example.com/{i}"
                entries.append(e)
            mock_parse.return_value.entries = entries
            mock_parse.return_value.bozo = False
            result = scraper.fetch()
            assert len(result) == 2

    def test_fetch_handles_exception(self):
        """測試網路異常時回傳空列表（優雅降級）"""
        scraper = RSSScraper(url="https://invalid-url.example")
        with patch("app.scrapers.feedparser.parse", side_effect=Exception("Network error")):
            result = scraper.fetch()
            assert result == []

    def test_fetch_handles_empty_feed(self):
        """測試空 Feed 回傳空列表"""
        scraper = RSSScraper(url="https://example.com/rss")
        with patch("app.scrapers.feedparser.parse") as mock_parse:
            mock_parse.return_value.entries = []
            mock_parse.return_value.bozo = False
            result = scraper.fetch()
            assert result == []

    def test_news_sources_configured(self):
        """測試預設新聞來源已正確設定"""
        assert len(NEWS_SOURCES) == 3
        for name, scraper in NEWS_SOURCES.items():
            assert isinstance(scraper, RSSScraper)
