# 純 Chroma 詩籤檢索系統
# 安裝需求：pip install chromadb sentence-transformers

import chromadb
import json
import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class FortuneChromaSystem:
    def __init__(self, persist_directory: str = "./chroma_fortune_db"):
        """
        初始化純 Chroma 檢索系統
        
        Args:
            persist_directory: Chroma 資料庫存儲路徑
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
        
        # 使用免費的嵌入模型（不需要 OpenAI API）
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        
        print(f"Chroma 資料庫位置: {persist_directory}")

    def create_sample_data(self) -> List[Dict]:
        """創建範例詩籤資料"""
        return [
            {
                "id": "001",
                "name": "上上籤",
                "poem": "春雷一聲天地開，萬物復甦展笑顏。前程似錦光明路，貴人相助福自來。",
                "explanation": "此籤大吉，象徵新的開始和希望。如春雷響起，預示著轉機即將到來。諸事順利，會有貴人相助。",
                "meaning": {
                    "career": "事業將有重大突破，新的機會即將出現，上司或客戶會給予支持",
                    "love": "感情運勢佳，單身者可能遇到良緣，有情人終成眷屬", 
                    "health": "身體康健，精神狀態良好，適合調養生息",
                    "wealth": "財運亨通，投資理財皆有收穫，正財偏財兩相宜"
                },
                "category": "總運",
                "keywords": ["轉機", "新開始", "貴人", "成功", "突破"]
            },
            {
                "id": "002",
                "name": "中平籤", 
                "poem": "雲遮月色影朦朧，耐心等待見光明。莫急莫躁守本分，時來運轉自然成。",
                "explanation": "目前運勢平穩，雖有困難但不必憂心。需要耐心等待時機成熟，守住本分即可。",
                "meaning": {
                    "career": "工作需要更多耐心，短期內變化不大，但穩定發展可期",
                    "love": "感情進展緩慢，需要時間培養，不宜操之過急",
                    "health": "注意休息，避免過度勞累，保持規律作息",
                    "wealth": "財運平穩，不宜冒險投資，以穩健理財為主"
                },
                "category": "總運",
                "keywords": ["等待", "耐心", "穩定", "時機", "守分"]
            },
            {
                "id": "003",
                "name": "求財籤",
                "poem": "金龍入水財源廣，四方之財聚一堂。誠心經營得厚利，富貴雙全樂安康。",
                "explanation": "財運極佳，適合投資理財。誠信經營將帶來豐厚回報，四面八方都有財源。",
                "meaning": {
                    "career": "事業蒸蒸日上，收入將有顯著增加，升職加薪在望",
                    "investment": "投資理財運勢佳，可適度增加投資比重，但需謹慎選擇",
                    "business": "生意興隆，客源廣進，合作機會多",
                    "windfall": "可能有意外之財，但需把握機會，不可貪心"
                },
                "category": "求財",
                "keywords": ["財運", "投資", "生意", "富貴", "機會"]
            },
            {
                "id": "004",
                "name": "求愛情籤",
                "poem": "花開並蒂喜相逢，月老牽線結良緣。真心相待情深重，白首偕老共百年。",
                "explanation": "愛情運勢大好，有望遇到真愛。已有對象者感情更加穩定，可考慮進入下一階段。",
                "meaning": {
                    "single": "單身者即將遇到心儀對象，可能是朋友介紹或自然相遇",
                    "dating": "正在交往者感情穩定發展，雙方真心相待",
                    "marriage": "適合考慮結婚，家庭和諧美滿",
                    "advice": "以真誠待人，不要過於計較小事"
                },
                "category": "求姻緣",
                "keywords": ["愛情", "真愛", "結婚", "和諧", "真誠"]
            },
            {
                "id": "005", 
                "name": "工作籤",
                "poem": "寶劍鋒從磨礪出，梅花香自苦寒來。努力耕耘終有報，功名成就在今朝。",
                "explanation": "事業需要持續努力和堅持。雖然過程辛苦，但努力終將獲得回報，成功就在不遠處。",
                "meaning": {
                    "career": "需要堅持不懈的努力，暫時的困難是成功路上的必經之路",
                    "promotion": "升職機會需要靠實力爭取，展現你的專業能力",
                    "change": "不宜輕易轉換工作，專注現職更有前途",
                    "skill": "持續學習進修，提升專業技能是關鍵"
                },
                "category": "求事業",
                "keywords": ["努力", "堅持", "成功", "專業", "回報"]
            }
        ]

    def setup_collection(self, collection_name: str = "fortune_poems"):
        """
        設置 Chroma 集合
        """
        try:
            # 嘗試獲取現有集合
            self.collection = self.client.get_collection(collection_name)
            print(f"載入現有集合: {collection_name}")
        except:
            # 如果不存在，創建新集合
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "詩籤內容向量資料庫"}
            )
            print(f"創建新集合: {collection_name}")

    def load_data_to_chroma(self, json_files: List[str] = None):
        """
        載入資料到 Chroma
        
        Args:
            json_files: JSON 檔案路徑列表，如果為 None 則使用範例資料
        """
        if self.collection is None:
            raise ValueError("請先設置集合")
        
        if json_files is None:
            # 使用範例資料
            fortune_data = self.create_sample_data()
        else:
            # 載入實際 JSON 檔案
            fortune_data = []
            for json_file in json_files:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        fortune_data.extend(data)
                    else:
                        fortune_data.append(data)
        
        # 準備要存入 Chroma 的資料
        documents = []
        metadatas = []
        ids = []
        
        for item in fortune_data:
            # 組合文本內容 (這是會被向量化的部分)
            content = self._create_searchable_content(item)
            documents.append(content)
            
            # 元資料 (用於過濾和顯示)
            metadata = {
                "id": item["id"],
                "name": item["name"],
                "poem": item["poem"],
                "explanation": item["explanation"],
                "category": item["category"],
                "keywords": ",".join(item["keywords"]),
                "meaning": json.dumps(item["meaning"], ensure_ascii=False)
            }
            metadatas.append(metadata)
            ids.append(item["id"])
        
        # 存入 Chroma
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"已載入 {len(documents)} 個籤詩到 Chroma 資料庫")

    def _create_searchable_content(self, item: Dict) -> str:
        """
        創建可搜尋的文本內容
        這個函數決定什麼內容會被向量化和搜尋
        """
        # 組合所有相關文字，讓搜尋更準確
        content_parts = [
            f"籤詩名稱：{item['name']}",
            f"籤詩內容：{item['poem']}", 
            f"籤詩解釋：{item['explanation']}",
            f"類別：{item['category']}",
            f"關鍵字：{', '.join(item['keywords'])}"
        ]
        
        # 添加詳細含義
        if 'meaning' in item:
            for key, value in item['meaning'].items():
                content_parts.append(f"{key}：{value}")
        
        return "\n".join(content_parts)

    def search_fortune(self, user_question: str, n_results: int = 2) -> Dict[str, Any]:
        """
        搜尋相關籤詩
        
        Args:
            user_question: 用戶問題
            n_results: 返回結果數量
            
        Returns:
            搜尋結果和為 LLM 準備的資料
        """
        if self.collection is None:
            raise ValueError("請先設置集合")
        
        # 在 Chroma 中搜尋
        results = self.collection.query(
            query_texts=[user_question],
            n_results=n_results
        )
        
        # 整理搜尋結果
        retrieved_fortunes = []
        for i in range(len(results['ids'][0])):
            fortune_data = {
                "id": results['metadatas'][0][i]['id'],
                "name": results['metadatas'][0][i]['name'],
                "poem": results['metadatas'][0][i]['poem'],
                "explanation": results['metadatas'][0][i]['explanation'],
                "category": results['metadatas'][0][i]['category'],
                "keywords": results['metadatas'][0][i]['keywords'],
                "meaning": json.loads(results['metadatas'][0][i]['meaning']),
                "distance": results['distances'][0][i] if 'distances' in results else None
            }
            retrieved_fortunes.append(fortune_data)
        
        # 為 LLM 準備提示資料
        llm_context = self._prepare_llm_context(retrieved_fortunes, user_question)
        
        return {
            "user_question": user_question,
            "retrieved_fortunes": retrieved_fortunes,
            "llm_context": llm_context,
            "llm_prompt": self._create_llm_prompt(llm_context, user_question)
        }

    def _prepare_llm_context(self, fortunes: List[Dict], user_question: str) -> str:
        """
        為 LLM 準備上下文資料
        """
        context_parts = []
        
        for i, fortune in enumerate(fortunes, 1):
            context = f"""
籤詩 {i}：
名稱：{fortune['name']}
內容：{fortune['poem']}
解釋：{fortune['explanation']}
類別：{fortune['category']}
關鍵字：{fortune['keywords']}

詳細含義：
"""
            # 添加詳細含義
            meaning = fortune['meaning']
            for key, value in meaning.items():
                context += f"- {key}：{value}\n"
            
            context_parts.append(context.strip())
        
        return "\n" + "="*50 + "\n".join(context_parts)

    def _create_llm_prompt(self, context: str, user_question: str) -> str:
        """
        創建完整的 LLM 提示
        """
        prompt = f"""你是一位慈祥智慧的解籤師，擅長為人指點迷津。

相關籤詩資料：
{context}

請根據以上籤詩內容，以溫和、鼓勵的語調回答用戶問題。回答應包含：
1. 籤詩的主要寓意與象徵
2. 針對用戶具體問題的解釋  
3. 實用的建議與正面指引
4. 適當的祝福與鼓勵

用戶問題：{user_question}

解籤回答："""
        
        return prompt

    def get_collection_info(self) -> Dict:
        """
        獲取集合資訊
        """
        if self.collection is None:
            return {"error": "集合未設置"}
        
        count = self.collection.count()
        return {
            "collection_name": self.collection.name,
            "document_count": count,
            "persist_directory": self.persist_directory
        }


# 使用範例和完整流程說明
def main():
    print("=" * 60)
    print("純 Chroma 詩籤檢索系統 - 完整流程演示")
    print("=" * 60)
    
    # 1. 初始化系統
    chroma_system = FortuneChromaSystem()
    
    # 2. 設置集合
    chroma_system.setup_collection()
    
    # 3. 載入資料
    print("\n📚 載入籤詩資料...")
    chroma_system.load_data_to_chroma()  # 使用範例資料
    # 如果要使用你的 JSON 檔案：
    # chroma_system.load_data_to_chroma(["path/to/your/file1.json", "path/to/your/file2.json"])
    
    # 4. 顯示集合資訊
    info = chroma_system.get_collection_info()
    print(f"\n📊 資料庫資訊：")
    print(f"   集合名稱: {info['collection_name']}")
    print(f"   文檔數量: {info['document_count']}")
    print(f"   存儲位置: {info['persist_directory']}")
    
    # 5. 測試查詢流程
    test_questions = [
        "我最近工作很不順，感覺遇到很多阻礙",
        "想知道最近的財運如何？有投資機會嗎？", 
        "感情方面有什麼建議嗎？我想知道會不會遇到對的人"
    ]
    
    print("\n" + "=" * 60)
    print("🔍 測試檢索流程")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\n👤 用戶問題：{question}")
        print("-" * 40)
        
        # 搜尋相關籤詩
        result = chroma_system.search_fortune(question, n_results=2)
        
        print(f"🔍 檢索到 {len(result['retrieved_fortunes'])} 個相關籤詩：")
        
        for i, fortune in enumerate(result['retrieved_fortunes'], 1):
            print(f"\n   📜 籤詩 {i}：{fortune['name']} ({fortune['category']})")
            print(f"      內容：{fortune['poem']}")
            print(f"      關鍵字：{fortune['keywords']}")
            if fortune['distance']:
                print(f"      相似度：{1 - fortune['distance']:.3f}")
        
        print(f"\n📝 為 LLM 準備的完整提示：")
        print("=" * 30)
        print(result['llm_prompt'])
        print("=" * 30)
        
        print(f"\n💡 下一步：將上述提示發送給你選擇的 LLM (OpenAI/Ollama/其他)")
        print(f"    LLM 會根據檢索到的籤詩內容生成個人化的解籤回答")
        
        print("\n" + "🔄" * 20)

if __name__ == "__main__":
    main()