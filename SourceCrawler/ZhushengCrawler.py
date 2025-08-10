import urllib.request as REQ
import bs4 as BS
import json
from pathlib import Path
class ZhushengCrawler:
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
        Baseurl = "https://qiangua.temple01.com/qianshi.php?t=fs_zhu"
        pages = list(range(1, 31))
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
                folder_path = Path("Zhusheng")
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
        poem = ""
        for line in clean_lines:
            # print(f'{line_count} / {len(clean_lines)}: {line}')
            if line_count == 0:
                self.title = line
            elif line_count == 1:
                poem = line.strip()
                poem = poem.replace("、",",")
                self.poem = poem
            line_count+=1

    def get_analysis_info(self, bs):
        """祝生娘娘沒有英文日文與典故，英文日文可以由AI生成翻譯"""
        # 分析
        P_analyse_div = bs.find("div", class_="qianshi_view_sidebox_right")
        # print(f'P_analyse_div: {P_analyse_div}')
        s_analyse = P_analyse_div.find_all("div", class_="fs_box fs_left fs_solve fs_lang")
        sub_line_count = 0
        zh=""
        for s in s_analyse:
            # print(f'{sub_line_count} / {len(s_analyse)}: {s}')
            import re
            html_str = str(s)
            processed = re.sub(r'<br\s*/?>', '\\n', html_str, flags=re.IGNORECASE)
            clean = re.sub(r'<[^>]*>', '', processed)
            clean = clean.replace("\n", "").replace("\r", ",")
            ref_text = clean
            zh += "\n" + ref_text            
            sub_line_count += 1
        self.analysis["zh"] = zh[1:].replace("\n", "").replace("\r", "")