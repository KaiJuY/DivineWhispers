from CrawlerFactory import CrawlerFactory

FS = CrawlerFactory.create_crawler("fs")
FS.crawl(True)