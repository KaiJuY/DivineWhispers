"""
Internationalization messages for SSE progress updates
"""

SSE_MESSAGES = {
    "zh": {
        # Initialization
        "initializing": "初始化任務...",
        "processing": "啟動處理流程...",

        # RAG processing
        "rag_start": "開始檢索籤詩資料...",
        "rag_processing_connect": "連接向量資料庫...",
        "rag_processing_vector": "生成查詢向量...",
        "rag_processing_search": "搜索相似內容...",
        "rag_processing_score": "計算相似度分數...",
        "rag_processing_sort": "排序搜索結果...",
        "rag_processing_prepare": "準備上下文資料...",
        "rag_complete": "籤詩資料檢索完成",

        # LLM processing
        "llm_start": "開始分析籤詩...",
        "llm_processing_load": "載入模型...",
        "llm_processing_analyze": "分析籤詩內容...",
        "llm_processing_context": "建立上下文關聯...",
        "llm_processing_generate": "生成初步回應...",
        "llm_processing_optimize": "優化表達方式...",
        "llm_processing_wisdom": "結合傳統智慧...",
        "llm_processing_check": "檢查邏輯一致性...",
        "llm_processing_polish": "潤飾最終回應...",
        "llm_processing_format": "格式化輸出...",
        "llm_processing_final": "最終品質檢查...",
        "llm_complete": "分析完成",

        # LLM streaming
        "llm_streaming": "正在生成: {partial_text}",
        "llm_streaming_progress": "正在生成解籤內容... ({token_count} 字元)",

        # Validation
        "validating": "驗證報告完整性...",
        "validation_complete": "驗證通過",

        # Completion
        "finalizing": "完成最終處理...",
        "completed": "解籤完成！",
        "success": "成功生成您的解籤報告",

        # Generic progress
        "progress_start": "開始 {operation}...",
        "progress_processing": "{operation}中...",
        "progress_complete": "{operation}完成",

        # Adaptive messages
        "progress_early": "{stage_name} 進行中... (剛開始)",
        "progress_middle": "{stage_name} 進行中... (進展順利)",
        "progress_late": "{stage_name} 進行中... (即將完成)",
        "progress_overtime": "{stage_name} 進行中... (比預期稍長)",
    },

    "en": {
        # Initialization
        "initializing": "Initializing task...",
        "processing": "Starting processing...",

        # RAG processing
        "rag_start": "Retrieving poem data...",
        "rag_processing_connect": "Connecting to vector database...",
        "rag_processing_vector": "Generating query vectors...",
        "rag_processing_search": "Searching similar content...",
        "rag_processing_score": "Calculating similarity scores...",
        "rag_processing_sort": "Sorting search results...",
        "rag_processing_prepare": "Preparing context data...",
        "rag_complete": "Poem data retrieval complete",

        # LLM processing
        "llm_start": "Starting analysis...",
        "llm_processing_load": "Loading model...",
        "llm_processing_analyze": "Analyzing poem content...",
        "llm_processing_context": "Building context connections...",
        "llm_processing_generate": "Generating initial response...",
        "llm_processing_optimize": "Optimizing expression...",
        "llm_processing_wisdom": "Incorporating traditional wisdom...",
        "llm_processing_check": "Checking logical consistency...",
        "llm_processing_polish": "Polishing final response...",
        "llm_processing_format": "Formatting output...",
        "llm_processing_final": "Final quality check...",
        "llm_complete": "Analysis complete",

        # LLM streaming
        "llm_streaming": "Generating: {partial_text}",
        "llm_streaming_progress": "Generating interpretation... ({token_count} tokens)",

        # Validation
        "validating": "Validating report integrity...",
        "validation_complete": "Validation passed",

        # Completion
        "finalizing": "Finalizing processing...",
        "completed": "Interpretation complete!",
        "success": "Successfully generated your interpretation report",

        # Generic progress
        "progress_start": "Starting {operation}...",
        "progress_processing": "{operation} in progress...",
        "progress_complete": "{operation} complete",

        # Adaptive messages
        "progress_early": "{stage_name} in progress... (just started)",
        "progress_middle": "{stage_name} in progress... (going well)",
        "progress_late": "{stage_name} in progress... (almost done)",
        "progress_overtime": "{stage_name} in progress... (taking a bit longer)",
    },

    "ja": {
        # Initialization
        "initializing": "タスクを初期化中...",
        "processing": "処理を開始しています...",

        # RAG processing
        "rag_start": "おみくじデータを検索中...",
        "rag_processing_connect": "ベクトルデータベースに接続中...",
        "rag_processing_vector": "クエリベクトルを生成中...",
        "rag_processing_search": "類似コンテンツを検索中...",
        "rag_processing_score": "類似度スコアを計算中...",
        "rag_processing_sort": "検索結果をソート中...",
        "rag_processing_prepare": "コンテキストデータを準備中...",
        "rag_complete": "おみくじデータの検索完了",

        # LLM processing
        "llm_start": "分析を開始中...",
        "llm_processing_load": "モデルを読み込み中...",
        "llm_processing_analyze": "おみくじ内容を分析中...",
        "llm_processing_context": "コンテキスト関連を構築中...",
        "llm_processing_generate": "初期応答を生成中...",
        "llm_processing_optimize": "表現を最適化中...",
        "llm_processing_wisdom": "伝統的な知恵を組み込み中...",
        "llm_processing_check": "論理的整合性をチェック中...",
        "llm_processing_polish": "最終応答を磨き上げ中...",
        "llm_processing_format": "出力をフォーマット中...",
        "llm_processing_final": "最終品質チェック中...",
        "llm_complete": "分析完了",

        # LLM streaming
        "llm_streaming": "生成中: {partial_text}",
        "llm_streaming_progress": "解釈を生成しています... ({token_count} トークン)",

        # Validation
        "validating": "レポートの整合性を検証中...",
        "validation_complete": "検証完了",

        # Completion
        "finalizing": "最終処理を完了中...",
        "completed": "解釈完了！",
        "success": "解釈レポートの生成に成功しました",

        # Generic progress
        "progress_start": "{operation}を開始...",
        "progress_processing": "{operation}処理中...",
        "progress_complete": "{operation}完了",

        # Adaptive messages
        "progress_early": "{stage_name} 処理中... (開始したばかり)",
        "progress_middle": "{stage_name} 処理中... (順調に進行中)",
        "progress_late": "{stage_name} 処理中... (もうすぐ完了)",
        "progress_overtime": "{stage_name} 処理中... (予想より少し長め)",
    }
}


def get_message(language: str, key: str, **kwargs) -> str:
    """
    Get localized message for given language and key

    Args:
        language: Language code (zh, en, ja)
        key: Message key
        **kwargs: Format parameters

    Returns:
        Localized message string
    """
    # Default to Chinese if language not supported
    lang = language if language in SSE_MESSAGES else "zh"

    # Get message template
    message = SSE_MESSAGES[lang].get(key)

    # Fallback to Chinese if key not found
    if message is None:
        message = SSE_MESSAGES["zh"].get(key, f"[{key}]")

    # Format with parameters if provided
    try:
        return message.format(**kwargs) if kwargs else message
    except KeyError:
        # Return unformatted if parameters missing
        return message
