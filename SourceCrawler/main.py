from CrawlerFactory import CrawlerFactory
Retrieve = ["GuanYu", "Mazu", "YueLao", "Zhusheng", "GuanYin100", "Tianhou", "Asakusa", "ErawanShrine"]
for crawler_type in Retrieve:
    crawler = CrawlerFactory.create_crawler(crawler_type)
    crawler.crawl(True)