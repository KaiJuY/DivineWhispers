import urllib.request as REQ
import bs4 as BS
import json

class AsakusaCrawler:
    def __init__(self):
        self.id = ""
        self.title = ""
        self.subtitle = ""
        self.fortune = ""
        self.poem = []
        self.analysis = {
            "zh": [],
            "en": [],
            "jp": [],
            "reference": []
        }
    def crawl(self, export_json: bool = False):
        # self.get_basic_info()
        self.get_analysis_info()
        if export_json:                
            with open(f"GuanYu\\chuck_{self.id}.json", "w", encoding="utf-8") as f:
                f.write(self.get_RAG_Json())
                f.close()
        else:
            print(self.get_RAG_Json())

    def get_basic_info(self):

        Baseurl = "http://www.chance.org.tw/%E7%B1%A4%E8%A9%A9%E9%9B%86/%E6%B7%BA%E8%8D%89%E9%87%91%E9%BE%8D%E5%B1%B1%E8%A7%80%E9%9F%B3%E5%AF%BA%E4%B8%80%E7%99%BE%E7%B1%A4/%E7%B1%A4%E8%A9%A9%E7%B6%B2%E2%80%A7%E6%B7%BA%E8%8D%89%E9%87%91%E9%BE%8D%E5%B1%B1%E8%A7%80%E9%9F%B3%E5%AF%BA%E4%B8%80%E7%99%BE%E7%B1%A4"
        pages = list(range(1, 101))
        for page in pages:
            str_page = f'__%E7%AC%AC{page:03d}%E7%B1%A4.htm'
            url = Baseurl + str_page
            req = REQ.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            })
            with REQ.urlopen(req) as response:
                data = response.read().decode("big5", errors="ignore")
            self.id = page
            bs = BS.BeautifulSoup(data, "html.parser")
            all_p = bs.find_all("p")
            count = 0
            title = ""
            for p in all_p:
                if page == 2:
                    if count == 3: #日本淺草觀音寺一百籤（日本佛寺一百籤）
                        title = p.text[:10]
                    elif count == 4: #第一百籤凶
                        subtitle_len = self.getsubtitleLens(page)
                        title += p.text[:subtitle_len] + "籤" if page != 100 else p.text[:subtitle_len]
                        self.title = title.strip()
                        self.fortune = p.text[subtitle_len:]
                    elif count == 5: #籤詩
                        poem = p.text if page != 22 else p.text[1:]
                        self.poem = poem.replace("\r", "").replace("\n", ",")
                else:
                    if count == 4: #日本淺草觀音寺一百籤（日本佛寺一百籤）
                        title = p.text[:10]
                    elif count == 5: #第一百籤凶
                        subtitle_len = self.getsubtitleLens(page)
                        title += p.text[:subtitle_len] + "籤" if page != 100 else p.text[:subtitle_len]
                        self.title = title
                        self.fortune = p.text[subtitle_len:]
                    elif count == 6: #籤詩
                        poem = p.text if page != 22 else p.text[1:]
                        self.poem = poem.replace("\r", "").replace("\n", ",")
                count += 1
            # print(f'Page {page} subtitle: {self.title}')
            # print(f'Page {page} fortune: {self.fortune}')
            # print(f'Page {page} poem: {self.poem}')
                
    def getsubtitleLens(self, page):
        if page <= 10:
            return 2
        elif page >= 11 and page <= 19  or page % 10 == 0  and page != 100:
            return 3
        else:
            return 4

    def get_RAG_Json(self) -> json:
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "fortune": self.fortune,
            "poem": self.poem,
            "analysis": self.analysis
        }, ensure_ascii=False)

    def get_analysis_info(self):
        Baseurl = "https://temples.tw/stick/fs_akt100/"
        pages = list(range(1, 2))
        for page in pages:
            str_page = f"{page}"
            url = Baseurl + str_page
            req = REQ.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            })
            with REQ.urlopen(req) as response:
                data = response.read().decode("utf-8")
            
            bs = BS.BeautifulSoup(data, "html.parser")
            # 分析
            s_analyse = bs.find_all("div", class_="stick_box")
            sub_line_count = 0
            zh=""
            for s in s_analyse:
                if sub_line_count == 0 or sub_line_count >= 3:
                    pass
                else :
                    ref_text = s.text.strip()
                    zh += "\n" + ref_text            
                sub_line_count += 1
            self.analysis["zh"] = zh.replace("\n", "").replace("\r", "")