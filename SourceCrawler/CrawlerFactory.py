from ITempleCrawler import TempleCrawler as BaseCrawler
from GuanYuCrawler import GuanYuCrawler
from MazuCrawler import MazuCrawler
from YueLaoCrawler import YueLaoCrawler
from GuanYin100Crawler import GuanYin100Crawler
from TianhouCrawler import TianhouCrawler
from AsakusaCrawler import AsakusaCrawler
from ErawanShrineCrawler import ErawanShrineCrawler
from ZhushengCrawler import ZhushengCrawler

class CrawlerFactory:
    @staticmethod
    def create_crawler(crawler_type: str) -> BaseCrawler:
        if crawler_type == "GuanYu":
            return GuanYuCrawler()
        elif crawler_type == "Mazu":
            return MazuCrawler()
        elif crawler_type == "YueLao":
            return YueLaoCrawler()
        elif crawler_type == "GuanYin100":
            return GuanYin100Crawler()
        elif crawler_type == "Tianhou":
            return TianhouCrawler()
        elif crawler_type == "Asakusa":
            return AsakusaCrawler()
        elif crawler_type == "ErawanShrine":
            return ErawanShrineCrawler()
        elif crawler_type == "Zhusheng":
            return ZhushengCrawler()
        raise ValueError(f"Unknown crawler type: {crawler_type}")