import urllib.request as REQ
import bs4 as BS
import json
from pathlib import Path

class GuanYuCrawler:
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
        Baseurl = "https://qiangua.temple01.com/qianshi.php?t=fs100"
        pages = list(range(1, 101))
        for page in pages:
            str_page = f"&s={page}"
            url = Baseurl + str_page
            req = REQ.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            })
            with REQ.urlopen(req) as response:
                data = response.read().decode("utf-8")
            
            
            bs = BS.BeautifulSoup(data, "html.parser")

            self.id = page
            self.get_basic_info(bs)
            self.get_analysis_info(bs)

            if export_json:
                # 建立資料夾路徑
                folder_path = Path("GuanYu")
                folder_path.mkdir(exist_ok=True)

                file_path = folder_path / f"chuck_{self.id}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.get_RAG_Json())
            else:
                print(self.get_RAG_Json())

    def get_RAG_Json(self) -> json:
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "fortune": self.fortune,
            "poem": self.poem,
            "analysis": self.analysis
        }, ensure_ascii=False)
    
    def get_basic_info(self, bs):
        # 籤詩
        poem_div = bs.find("div", class_="fs_poetry_w_line")
        clean_text = poem_div.text.strip()
        lines = clean_text.splitlines()
        clean_lines = [line.strip() for line in lines if line.strip()]
        line_count = 0
        for line in clean_lines:
            if line_count == 0:
                self.title = line
            elif line_count == 1:
                splitline =line.split('\xa0')                
                self.subtitle = splitline[0] if len(splitline) > 0 else ""
                self.fortune = splitline[1] if len(splitline) > 1 else ""
            elif line_count == 2:
                line = line.replace("、", " ").replace("。", "")
                self.poem = line.split(" ")
            line_count+=1

    def get_analysis_info(self, bs):
        # 分析
        P_analyse_div = bs.find("div", class_="qianshi_view_sidebox_right")
        s_analyse = P_analyse_div.find_all("div", class_="fs_box fs_left fs_lang")
        sub_line_count = 0
        for s in s_analyse:
            # print(f'{sub_line_count} / {len(s_analyse)}: {s}')
            if sub_line_count == 0:
                foot = s.find("p", class_="fs_left fs_lang")
                if foot:                    
                    foot.extract()
                sa_text = s.text.strip()
                self.analysis["zh"] = sa_text.replace("\n", "").replace("\r", "")
                
            elif sub_line_count == 1:
                foot = s.find("p", class_="fs_left fs_lang")
                if foot:                    
                    foot.extract()
                jp_div = s.find("div", class_="fs_left fs_lang")
                if jp_div:
                    jp_div.extract()
                    jp_text = jp_div.text.strip()
                    self.analysis["jp"] = jp_text.replace("\n", "").replace("\r", "")

                en_text = s.text.strip()            
                self.analysis["en"] = en_text.replace("\n", "").replace("\r", "")
            else :
                ref_text = s.text.strip()
                self.analysis["reference"] = ref_text.replace("\n", "").replace("\r", "")
            sub_line_count += 1