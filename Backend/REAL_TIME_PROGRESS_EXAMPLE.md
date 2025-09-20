# Real-Time Progress Updates Implementation

## Overview
The enhanced chat system now provides true real-time progress updates during RAG and LLM processing, giving users detailed feedback about what's happening at each stage.

## How It Works

### 1. Progress Tracking System
The `ProgressTracker` class monitors task execution and sends updates to SSE connections:

```python
# Create progress tracker for a task
progress_tracker = await create_progress_aware_task(
    task_id,
    sse_callback,
    streaming=True
)

# Send real-time updates
await progress_tracker.update("analyzing_rag", 25, "正在映射神明識別碼...")
await progress_tracker.update("analyzing_rag", 35, "正在查找 GuanYu 籤詩...")
await progress_tracker.update("generating_llm", 75, "結合傳統智慧與現代解釋...")
```

### 2. Enhanced SSE Events
Now users receive detailed progress updates throughout the entire process:

#### Traditional (Before)
```json
{"type": "status", "status": "queued", "progress": 0}
{"type": "progress", "status": "processing", "progress": 10}
{"type": "progress", "status": "analyzing_rag", "progress": 30}
{"type": "progress", "status": "generating_llm", "progress": 70}
{"type": "complete", "result": {...}}
```

#### Enhanced (Now)
```json
{"type": "enhanced_status", "status": "queued", "progress": 0, "task_info": {...}}
{"type": "enhanced_progress", "stage": "processing", "progress": 5, "message": "初始化處理流程..."}
{"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 25, "message": "正在映射神明識別碼..."}
{"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 35, "message": "正在查找 GuanYu 籤詩..."}
{"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 45, "message": "正在檢索第 40 籤..."}
{"type": "enhanced_progress", "stage": "generating_llm", "progress": 65, "message": "正在分析籤詩內容..."}
{"type": "enhanced_progress", "stage": "generating_llm", "progress": 75, "message": "結合傳統智慧與現代解釋..."}
{"type": "enhanced_progress", "stage": "generating_llm", "progress": 85, "message": "生成個人化建議..."}
{"type": "enhanced_complete", "result": {...}, "summary": {...}}
```

## New API Endpoints

### 1. Enhanced Fortune Request
```bash
POST /api/v1/streaming-chat/ask-question
Content-Type: application/json

{
  "deity_id": "guan_yu",
  "fortune_number": 40,
  "question": "我下週的面試會順利嗎？",
  "enable_streaming": true,
  "language": "zh"
}
```

**Response:**
```json
{
  "task_id": "task_123",
  "sse_url": "/api/v1/async-chat/sse/task_123",
  "enhanced_sse_url": "/api/v1/streaming-chat/sse/task_123",
  "status": "queued",
  "streaming_enabled": true
}
```

### 2. Enhanced SSE Stream
```bash
GET /api/v1/streaming-chat/sse/task_123?token=your_jwt_token
Accept: text/event-stream
```

**Real-time events:**
```
data: {"type": "enhanced_status", "status": "queued", "progress": 0, "task_info": {"deity_id": "guan_yu", "fortune_number": 40, "streaming_enabled": true}}

data: {"type": "enhanced_progress", "stage": "processing", "progress": 5, "message": "初始化處理流程...", "timestamp": "2024-01-15T10:30:01.123Z"}

data: {"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 25, "message": "正在映射神明識別碼...", "timestamp": "2024-01-15T10:30:01.623Z"}

data: {"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 35, "message": "正在查找 GuanYu 籤詩...", "timestamp": "2024-01-15T10:30:02.123Z"}

data: {"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 45, "message": "正在檢索第 40 籤...", "timestamp": "2024-01-15T10:30:02.623Z"}

data: {"type": "enhanced_progress", "stage": "analyzing_rag", "progress": 50, "message": "成功找到 GuanYu 籤詩", "timestamp": "2024-01-15T10:30:03.123Z"}

data: {"type": "enhanced_progress", "stage": "generating_llm", "progress": 65, "message": "正在分析籤詩內容...", "timestamp": "2024-01-15T10:30:04.123Z"}

data: {"type": "enhanced_progress", "stage": "generating_llm", "progress": 75, "message": "結合傳統智慧與現代解釋...", "timestamp": "2024-01-15T10:30:04.623Z"}

data: {"type": "enhanced_progress", "stage": "generating_llm", "progress": 85, "message": "生成個人化建議...", "timestamp": "2024-01-15T10:30:05.123Z"}

data: {"type": "enhanced_progress", "stage": "generating_llm", "progress": 92, "message": "完成解釋生成...", "timestamp": "2024-01-15T10:30:05.623Z"}

data: {"type": "enhanced_progress", "stage": "completed", "progress": 100, "message": "解釋生成完成！", "timestamp": "2024-01-15T10:30:06.123Z"}

data: {"type": "enhanced_complete", "result": {"response": "根據您的問題，我開始分析相關的籤詩內容...", "confidence": 84, "processing_time_ms": 5000}, "summary": {"total_processing_time": 5000, "stages_completed": ["processing", "analyzing_rag", "generating_llm", "completed"]}}
```

### 3. Progress Information
```bash
GET /api/v1/streaming-chat/progress/task_123
Authorization: Bearer your_jwt_token
```

**Response:**
```json
{
  "task_id": "task_123",
  "current_status": "generating_llm",
  "current_progress": 75,
  "status_message": "結合傳統智慧與現代解釋...",
  "tracker_active": true,
  "tracker_info": {
    "current_stage": "generating_llm",
    "elapsed_time_seconds": 3.45,
    "subscribers_count": 1
  }
}
```

## Frontend Integration Example

### JavaScript EventSource
```javascript
const eventSource = new EventSource('/api/v1/streaming-chat/sse/task_123?token=' + authToken);

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'enhanced_progress':
            updateProgressBar(data.progress);
            showProgressMessage(data.message);
            logProgressStep(data.stage, data.progress, data.message);
            break;

        case 'enhanced_complete':
            hideProgressBar();
            showResult(data.result.response);
            showSummary(data.summary);
            break;

        case 'enhanced_error':
            hideProgressBar();
            showError(data.error);
            break;

        case 'enhanced_ping':
            updateConnectionStatus('alive', data.connection_alive_seconds);
            break;
    }
};

function updateProgressBar(progress) {
    document.getElementById('progress-bar').style.width = progress + '%';
    document.getElementById('progress-text').textContent = progress + '%';
}

function showProgressMessage(message) {
    document.getElementById('progress-message').textContent = message;
}

function logProgressStep(stage, progress, message) {
    const logEntry = `[${new Date().toLocaleTimeString()}] ${stage}: ${progress}% - ${message}`;
    console.log(logEntry);

    // Optionally show in UI
    const progressLog = document.getElementById('progress-log');
    const logElement = document.createElement('div');
    logElement.textContent = logEntry;
    progressLog.appendChild(logElement);
}
```

### React Hook Example
```javascript
import { useState, useEffect } from 'react';

function useEnhancedProgress(taskId, authToken) {
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState('');
    const [message, setMessage] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [progressHistory, setProgressHistory] = useState([]);

    useEffect(() => {
        if (!taskId || !authToken) return;

        const eventSource = new EventSource(
            `/api/v1/streaming-chat/sse/${taskId}?token=${authToken}`
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'enhanced_progress':
                    setProgress(data.progress);
                    setStage(data.stage);
                    setMessage(data.message);
                    setProgressHistory(prev => [...prev, {
                        stage: data.stage,
                        progress: data.progress,
                        message: data.message,
                        timestamp: data.timestamp
                    }]);
                    break;

                case 'enhanced_complete':
                    setProgress(100);
                    setStage('completed');
                    setMessage('完成！');
                    setResult(data.result);
                    eventSource.close();
                    break;

                case 'enhanced_error':
                    setError(data.error);
                    eventSource.close();
                    break;
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            setError('連接錯誤');
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [taskId, authToken]);

    return {
        progress,
        stage,
        message,
        result,
        error,
        progressHistory
    };
}

// Usage in component
function FortuneChat() {
    const [taskId, setTaskId] = useState(null);
    const { progress, stage, message, result, error, progressHistory } =
        useEnhancedProgress(taskId, userToken);

    const askQuestion = async () => {
        const response = await fetch('/api/v1/streaming-chat/ask-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({
                deity_id: 'guan_yu',
                fortune_number: 40,
                question: '我下週的面試會順利嗎？',
                enable_streaming: true,
                language: 'zh'
            })
        });

        const data = await response.json();
        setTaskId(data.task_id);
    };

    return (
        <div>
            <button onClick={askQuestion}>問籤</button>

            {taskId && (
                <div className="progress-container">
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{width: `${progress}%`}}
                        ></div>
                    </div>

                    <div className="progress-info">
                        <div>階段: {stage}</div>
                        <div>進度: {progress}%</div>
                        <div>狀態: {message}</div>
                    </div>

                    <div className="progress-history">
                        {progressHistory.map((item, index) => (
                            <div key={index} className="progress-step">
                                {item.stage}: {item.progress}% - {item.message}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {result && (
                <div className="result">
                    <h3>解籤結果</h3>
                    <p>{result.response}</p>
                    <div>信心度: {result.confidence}%</div>
                </div>
            )}

            {error && (
                <div className="error">
                    錯誤: {error}
                </div>
            )}
        </div>
    );
}
```

## Benefits

1. **Real-time Feedback**: Users see exactly what's happening during processing
2. **Better UX**: No more black box waiting - users know the system is working
3. **Debugging**: Detailed progress helps identify where issues occur
4. **Transparency**: Users understand the complexity of the fortune-telling process
5. **Engagement**: Step-by-step progress keeps users engaged

## Migration Guide

### For Existing Clients
The original `/api/v1/async-chat/` endpoints still work as before. To get enhanced progress:

1. Use `/api/v1/streaming-chat/ask-question` instead of `/api/v1/async-chat/ask-question`
2. Connect to `/api/v1/streaming-chat/sse/{task_id}` for enhanced progress
3. Handle the new `enhanced_progress` event types in your EventSource handler

### Backward Compatibility
- All existing endpoints continue to work
- Enhanced endpoints provide additional detail without breaking changes
- Progressive enhancement - clients can choose their level of detail

This implementation provides the real-time progress updates you requested, giving users detailed feedback throughout the entire RAG and LLM processing pipeline!