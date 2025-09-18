import logging
import os
from datetime import datetime
from pathlib import Path

from CrawlerFactory import CrawlerFactory

# Setup logging for crawler
def setup_crawler_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_filename = f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
    log_file_path = log_dir / log_filename

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)

# Initialize logging
logger = setup_crawler_logging()

# Retrieve = ["GuanYu", "Mazu", "YueLao", "Zhusheng", "GuanYin100", "Tianhou", "Asakusa", "ErawanShrine"]
Retrieve = ["YueLao", "Zhusheng", "Tianhou"]

logger.info(f"Starting crawler for temples: {Retrieve}")

for crawler_type in Retrieve:
    try:
        logger.info(f"Initializing crawler for: {crawler_type}")
        crawler = CrawlerFactory.create_crawler(crawler_type)
        logger.info(f"Starting crawl for: {crawler_type}")
        crawler.crawl(True)
        logger.info(f"Completed crawl for: {crawler_type}")
    except Exception as e:
        logger.error(f"Error crawling {crawler_type}: {str(e)}", exc_info=True)

logger.info("Crawler execution completed")