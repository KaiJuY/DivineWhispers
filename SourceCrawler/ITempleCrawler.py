from abc import ABC, abstractmethod
import json

class TempleCrawler(ABC):
    @abstractmethod
    def crawl(self):
        pass
    def get_RAG_Json(self) -> json:
        pass
