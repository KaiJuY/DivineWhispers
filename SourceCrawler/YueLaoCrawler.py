import urllib.request as REQ
import bs4 as BS
import json

class YueLaoCrawler:
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
        Baseurl = "https://qiangua.temple01.com/qianshi.php?t=fs_yuelao"
        pages = list(range(1, 2))
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
                with open(f"GuanYu\\chuck_{self.id}.json", "w", encoding="utf-8") as f:
                    f.write(self.get_RAG_Json())
                    f.close()
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
                self.fortune = line                
            elif line_count == 2 or line_count == 3:                            
                poem += line
            line_count+=1
        self.poem = poem

    def get_analysis_info(self, bs):
        """月老籤沒有英文日文與典故，英文日文可以由AI生成翻譯"""
        # 分析
        P_analyse_div = bs.find("div", class_="qianshi_view_sidebox_right")
        s_analyse = P_analyse_div.find_all("div", class_="fs_box fs_left")
        sub_line_count = 0
        zh=""
        jp=""
        en=""
        reference=""
        for s in s_analyse:
            print(f'{sub_line_count} / {len(s_analyse)}: {s}')
            if sub_line_count == 0 or sub_line_count == 1:
                en_div = s.find("div", class_="fs_left fs_lang")
                if en_div:
                    en_div.extract()
                    en_text = en_div.text.strip()
                    en += "\n" + en_text
                jp_div = s.find("div", class_="fs_left fs_lang")
                if jp_div:
                    jp_div.extract()
                    jp_text = jp_div.text.strip()
                    jp += "\n" + jp_text
                sa_text = s.text.strip()
                zh += "\n" + sa_text
            else :
                ref_text = s.text.strip()
                zh += "\n" + ref_text            
            sub_line_count += 1
        self.analysis["zh"] = zh.replace("\n", "").replace("\r", "")
        self.analysis["en"] = en.replace("\n", "").replace("\r", "")
        self.analysis["jp"] = jp.replace("\n", "").replace("\r", "")
        ref_div = bs.find("div", class_="fs_box fs_left fs_lang")
        ref_text = ref_div.text.strip() if ref_div else ""
        reference += "\n" + ref_text
        ref_div = bs.find("div", class_="fs_box fs_left fs_solve fs_lang")
        ref_text = ref_div.text.strip() if ref_div else ""
        reference += "\n" + ref_text
        self.analysis["reference"] = reference.replace("\n", "").replace("\r", "")