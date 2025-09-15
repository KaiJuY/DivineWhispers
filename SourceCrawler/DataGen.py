import os
import re
import json
import glob
import copy
import time
from pathlib import Path
import ollama  # pip install ollama

MODEL = "gpt-oss:20b"  # 或 llama3.1, gemma2, mistral 等
INPUT_DIRS = ["GuanYu", "Mazu", "YueLao", "Zhusheng", "GuanYin100", "Tianhou", "Asakusa", "ErawanShrine"]
OUTPUT_DIR = "outputs"
MAX_RETRIES = 2
error_files = []  # 全域或外部定義，用來記錄錯誤檔案

os.makedirs(OUTPUT_DIR, exist_ok=True)
for input_dir in INPUT_DIRS:
    os.makedirs(os.path.join(OUTPUT_DIR, input_dir), exist_ok=True)
PROMPT_TEMPLATE = """
你是一位精通中文、英文、日文的籤詩專業解析師，請依照下列規則解析並回傳 JSON。

規則：
1. 不要修改輸入 JSON 中的 id, title, subtitle, fortune, poem。
2. analysis 物件需包含 zh, en, jp 三個欄位：
   - 以 zh 為主進行完整撰寫，長度約 200–300 字，風格需正式、流暢、帶解釋性，避免過度口語化。
   - en 與 jp 必須嚴格根據 zh 翻譯，保持結構與字數大致一致，不可自行改寫或省略。
   - 三個欄位開頭皆須為「這首詩的主題是...」的對應語言版本。
   - 僅針對詩詞內容進行解讀，不加入其他傳統卜卦或外部典故。
3. rag_analysis 欄位需以英文撰寫：
   - 開頭必須是 "According to the poem, the core meaning is..."
   - 全文長度約 300–500 字。
   - 先總結詩詞的核心意涵與哲理，再依序條列出六個方向的啟示：
     1. Health  
     2. Love and Relationships  
     3. Career and Ambition  
     4. Wealth and Finances  
     5. Family and Harmony  
     6. Social Connections and Reputation  
   - 每個方向需有 2–3 句完整說明，保持正式、清晰的分析風格。
4. reference 欄位：若原來存在就保留；若不存在則維持空陣列。
5. 回傳格式：純 JSON，必須包含 analysis.zh, analysis.en, analysis.jp 與 rag_analysis。

輸入 JSON：
{json_data}
"""

def build_prompt(original_json):
    return PROMPT_TEMPLATE.format(json_data=json.dumps(original_json, ensure_ascii=False))

def call_ollama(prompt):
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return resp['message']['content']
        except Exception as e:
            print("Ollama error:", e)
            time.sleep(1 + attempt * 2)
    raise RuntimeError("Ollama failed after retries")

def process_file(subfolder, path, dry_run=True):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    orig = copy.deepcopy(data)

    prompt = build_prompt(data)

    raw_text = call_ollama(prompt)
    parsed = safe_json_loads(raw_text)

    if parsed is None:
            print(f"[WARN] 無法解析 JSON: {file}")
            error_files.append(file)
            return  # 跳過此檔案
    try:
        if "analysis" not in parsed:
            raise ValueError("Missing analysis key from LLM result")
        if "rag_analysis" not in parsed:
            raise ValueError("Missing rag_analysis key from LLM result")

        data["analysis"] = data.get("analysis", {})
        for lang in ["zh", "en", "jp"]:
            data["analysis"][lang] = parsed["analysis"].get(lang, data["analysis"].get(lang, ""))

        data["rag_analysis"] = parsed.get("rag_analysis", "")

        data["_llm_meta"] = {
            "model": MODEL,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": os.path.basename(path),
            "raw_llm_response_preview": raw_text[:300]
        }

        outpath = os.path.join(OUTPUT_DIR, subfolder, os.path.basename(path))
        if dry_run:
            print(f"Dry-run: would write {outpath}")
        else:
            Path(outpath).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        error_files.append(path)
        return
def safe_json_loads(raw_text):
    """
    嘗試從 LLM 輸出中提取並解析 JSON，若失敗則回傳 None。
    """
    # 先嘗試直接解析
    try:
        return json.loads(raw_text)
    except:
        pass

    # 找第一個 { 和最後一個 }
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1:
        return None

    json_str = raw_text[start:end+1]

    # 清理常見 JSON 格式錯誤
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)
    json_str = json_str.replace("\u0000", "")

    try:
        return json.loads(json_str)
    except:
        return None
    
if __name__ == "__main__":
    output_base = Path("outputs")  # 假設 outputs 資料夾在當前目錄
    retry_count = 0
    while True and retry_count < 5:
        for input_dir in INPUT_DIRS:
            input_path = Path(input_dir)
            if not input_path.exists():
                print(f"Input directory {input_dir} does not exist, skipping.")
                continue
                
            files = list(input_path.glob("*.json"))
            if not files:
                print(f"No JSON files found in {input_dir}, skipping.")
                continue
                
            # 建立對應的 output 目錄
            output_dir = output_base / input_path.name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                # 檢查 output 中是否已經存在對應檔案
                output_file = output_dir / file.name
                if output_file.exists():
                    print(f"Output file {output_file} already exists, skipping {file.name}")
                    continue
                    
                print(f"Processing missing file: {file.name}")
                process_file(input_dir, file, dry_run=False)

        if error_files:
            retry_count += 1
            print("\n=== 以下檔案解析失敗，請重跑 ===")
            for ef in error_files:
                print(ef)
        else:
            print("\n所有檔案處理成功 ✅")
            break  # 全部成功，跳出迴圈