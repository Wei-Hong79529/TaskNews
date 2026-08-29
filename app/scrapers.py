"""
新聞抓取策略模組 (News Scraper Module)
使用策略模式 (Strategy Pattern)，方便未來新增新聞來源。
遵循 SOLID 原則中的「開放封閉原則 (OCP)」：只需繼承 NewsScraper 即可新增來源，無需修改現有邏輯。
"""

import feedparser
import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Dict
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# 設定模組級別的 logger
logger = logging.getLogger(__name__)

# 建立翻譯器實例（英文 → 繁體中文）
translator = GoogleTranslator(source="auto", target="zh-TW")

# 用於檢查翻譯結果是否包含 Google 錯誤訊息的關鍵字
TRANSLATION_ERROR_KEYWORDS = [
    "error 500",
    "server error",
    "that’s an error",
    "too many requests",
    "error 403",
    "error 404",
]


class NewsScraper(ABC):
    """新聞抓取器抽象基類 (Abstract Base Class)"""

    @abstractmethod
    def fetch(self) -> List[Dict[str, str]]:
        """抓取新聞列表，回傳格式為 [{"title": "...", "link": "..."}]"""
        pass


class RSSScraper(NewsScraper):
    """
    RSS Feed 抓取器
    透過 feedparser 解析 RSS/Atom Feed 並回傳前 N 筆新聞。
    支援自動翻譯標題為繁體中文。
    """

    def __init__(self, url: str, limit: int = 10, translate_to_zh: bool = False):
        """
        Args:
            url: RSS Feed 的 URL
            limit: 最多回傳的新聞數量 (預設 10 筆)
            translate_to_zh: 是否將標題翻譯為繁體中文 (預設 False)
        """
        self.url = url
        self.limit = limit
        self.translate_to_zh = translate_to_zh

    def _translate_title(self, title: str) -> str:
        """
        將標題翻譯為繁體中文。
        若翻譯失敗或包含 Error 500 等錯誤網頁內容，則回傳原始標題（優雅降級）。
        """
        if not title or not title.strip():
            return title

        # 嘗試使用帶有完整 User-Agent 的 Web 請求（避免無標頭請求觸發 Google Translate Error 500）
        try:
            url = "https://translate.google.com/m"
            params = {"sl": "auto", "tl": "zh-TW", "q": title}
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                elem = soup.find("div", {"class": "result-container"})
                if elem:
                    translated = elem.get_text().strip()
                    if translated and not any(kw in translated.lower() for kw in TRANSLATION_ERROR_KEYWORDS):
                        return translated
        except Exception as e:
            logger.debug(f"直接 Web 翻譯失敗 ({e})，嘗試備用方案...")

        # 備用方案：deep_translator
        try:
            translated = translator.translate(title)
            if translated and not any(kw in translated.lower() for kw in TRANSLATION_ERROR_KEYWORDS):
                return translated
            logger.warning(f"標題翻譯回傳錯誤內容，使用原始標題: {title}")
            return title
        except Exception as e:
            logger.warning(f"標題翻譯失敗，使用原始標題 ({e}): {title}")
            return title

    def fetch(self) -> List[Dict[str, str]]:
        """
        解析 RSS Feed 並回傳前 N 筆新聞。
        若解析過程中發生錯誤，會記錄日誌並回傳空列表（優雅降級）。
        """
        try:
            logger.info(f"正在抓取 RSS Feed: {self.url}")
            feed = feedparser.parse(self.url)

            # 檢查 feedparser 是否有回報解析錯誤
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS Feed 解析遇到問題 ({self.url}): {feed.bozo_exception}")

            # 即使有 bozo 錯誤，仍嘗試提取有效的 entries
            if not feed.entries:
                logger.warning(f"RSS Feed 沒有任何新聞條目: {self.url}")
                return []

            results = []
            for entry in feed.entries[: self.limit]:
                title = getattr(entry, "title", "無標題")
                link = getattr(entry, "link", "#")

                # 若啟用翻譯，將標題翻譯為繁體中文
                if self.translate_to_zh:
                    title = self._translate_title(title)

                results.append({"title": title, "link": link})

            logger.info(f"成功從 {self.url} 抓取到 {len(results)} 筆新聞")
            return results

        except Exception as e:
            # 優雅降級 (Graceful Degradation)：單一來源失敗不影響整體系統
            logger.error(f"抓取 RSS Feed 失敗 ({self.url}): {e}")
            return []


class MultiRSSScraper(NewsScraper):
    """
    多來源 RSS Feed 抓取器
    從多個 RSS 來源各抓取 N 筆新聞，彙整後去重回傳。
    適用於單一分類需要整合多個新聞來源的情境。
    """

    def __init__(self, sources: List[Dict], total_limit: int = 10, translate_to_zh: bool = False):
        """
        Args:
            sources: RSS 來源清單，格式為 [{"url": "...", "limit": N, "name": "來源名稱"}]
            total_limit: 最終回傳的新聞總數上限
            translate_to_zh: 是否將標題翻譯為繁體中文 (預設 False)
        """
        self.sources = sources
        self.total_limit = total_limit
        self.translate_to_zh = translate_to_zh

    def fetch(self) -> List[Dict[str, str]]:
        """從多個 RSS 來源抓取新聞，去重後回傳"""
        all_articles = []
        seen_titles = set()

        for source in self.sources:
            should_translate = source.get("translate_to_zh", self.translate_to_zh)
            scraper = RSSScraper(
                url=source["url"],
                limit=source.get("limit", 5),
                translate_to_zh=should_translate,
            )
            articles = scraper.fetch()

            for article in articles:
                # 以標題去重，避免不同來源的重複新聞
                if article["title"] not in seen_titles:
                    seen_titles.add(article["title"])
                    all_articles.append(article)

        logger.info(f"多來源彙整完成，共取得 {len(all_articles)} 筆不重複新聞")
        return all_articles[: self.total_limit]


# ==========================================
# 預設新聞來源設定
# ==========================================
# 使用官方 RSS Feed 作為資料來源，遵循各網站的 robots.txt 規範
NEWS_SOURCES = {
    "🇹🇼 台灣新聞 TOP 10": MultiRSSScraper(
        sources=[
            {"url": "https://feeds.feedburner.com/rsscna/politics", "limit": 5, "name": "中央通訊社"},
            {"url": "https://news.pts.org.tw/xml/newsfeed.xml", "limit": 5, "name": "公視新聞"},
        ],
        total_limit=10,
        translate_to_zh=False,
    ),
    "🇯🇵 日本新聞 TOP 10": MultiRSSScraper(
        sources=[
            {"url": "https://www.japantimes.co.jp/feed/topstories/", "limit": 5, "name": "The Japan Times"},
            {"url": "https://www3.nhk.or.jp/nhkworld/data/en/news/backstory/rss.xml", "limit": 5, "name": "NHK World-Japan"},
        ],
        total_limit=10,
        translate_to_zh=True,
    ),
    "🌍 歐美新聞 TOP 10": MultiRSSScraper(
        sources=[
            {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "limit": 3, "name": "BBC World"},
            {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "limit": 3, "name": "NYT World"},
            {"url": "https://www.aljazeera.com/xml/rss/all.xml", "limit": 3, "name": "Al Jazeera"},
            {"url": "http://rss.cnn.com/rss/edition_world.rss", "limit": 3, "name": "CNN World"},
        ],
        total_limit=10,
        translate_to_zh=True,
    ),
    "🌏 東南亞新聞 TOP 10": MultiRSSScraper(
        sources=[
            {"url": "https://www.bangkokpost.com/rss/data/world.xml", "limit": 4, "name": "Bangkok Post"},
            {"url": "https://asia.nikkei.com/rss/feed/nar", "limit": 4, "name": "Nikkei Asia"},
            {"url": "https://www.newmandala.org/feed/", "limit": 4, "name": "New Mandala"},
        ],
        total_limit=10,
        translate_to_zh=True,
    ),
    "💰 國際財經新聞 TOP 10": RSSScraper(
        url="https://feeds.bloomberg.com/markets/news.rss",
        limit=10,
        translate_to_zh=True,
    ),
}

