from ITempleCrawler import TempleCrawler as BaseCrawler
from GuanYuCrawler import GuanYuCrawler
from MazuCrawler import MazuCrawler
from YueLaoCrawler import YueLaoCrawler

class CrawlerFactory:
    @staticmethod
    def create_crawler(crawler_type: str) -> BaseCrawler:
        if crawler_type == "GuanYu":
            return GuanYuCrawler()
        elif crawler_type == "Mazu":
            return MazuCrawler()
        elif crawler_type == "YueLao":
            return YueLaoCrawler()
        raise ValueError(f"Unknown crawler type: {crawler_type}")