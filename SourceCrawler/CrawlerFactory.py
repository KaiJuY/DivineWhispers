from ITempleCrawler import TempleCrawler as BaseCrawler
from FSCrawler import FScrawler

class CrawlerFactory:
    @staticmethod
    def create_crawler(crawler_type: str) -> BaseCrawler:
        if crawler_type == "fs":
            return FScrawler()
        # 可以擴展其他類型
        raise ValueError(f"Unknown crawler type: {crawler_type}")