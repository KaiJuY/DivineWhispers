# True Real-Time Streaming Solution

## Problem Analysis

The previous implementation still had the **stacking issue** where all progress updates were sent at once after blocking operations completed. Looking at your timestamps:

```
01:23:35.542935 - Progress updates sent rapidly
01:23:35.556713
01:23:35.560875
01:23:36.585499 - Last update before blocking

[19-second gap - no updates during actual processing]

01:23:55.498795 - Updates resume after processing completes
01:23:55.536422
```

This happens because the RAG queries and LLM calls are **synchronous blocking operations** that prevent the event loop from processing other tasks.

## Solution: True Background Processing with Real-Time Updates

### 1. **Streaming Processor Architecture**

The new `StreamingProcessor` class runs heavy operations in the background while sending real-time progress updates:

```python
# Instead of blocking the event loop
await blocking_rag_operation()  # ❌ Blocks for 19 seconds

# Use streaming processor
await streaming_processor.adaptive_stream_processing(
    blocking_rag_operation,  # ✅ Runs in background
    "RAG檢索", 15, 50, "rag"   # ✅ Sends updates during processing
)
```

### 2. **How It Works**

#### Before (Blocking)
```
Task Start → [Black Box Processing 19s] → All Updates Sent → Complete
```

#### After (Streaming)
```
Task Start → Background Task Created → Real-time Updates Every 800ms → Complete
           ↓
           Progress Monitor Loop
           ├─ 800ms: "🔍 開始 RAG 檢索..."
           ├─ 1.6s:  "📡 連接向量資料庫..."
           ├─ 2.4s:  "🧮 生成查詢向量..."
           ├─ 3.2s:  "🔎 搜索相似內容..."
           └─ ...continues until completion
```

### 3. **Smart Adaptive Progress**

The `SmartStreamingProcessor` learns from operation history:

```python
# First time (estimates)
RAG: ~3.0s, LLM: ~15.0s

# After learning (actual averages)
RAG: ~2.1s, LLM: ~18.5s

# Adaptive messages based on progress
if elapsed < estimated * 0.3:
    "🚀 RAG檢索 進行中... (剛開始)"
elif elapsed < estimated * 0.7:
    "⚡ RAG檢索 進行中... (進展順利)"
else:
    "⏰ RAG檢索 進行中... (比預期稍長)"
```

## Implementation Details

### 1. **New Task Processing Flow**

```python
async def process_task(self, task_id: str):
    # Create streaming processor
    streaming_processor = create_streaming_processor(task_id, self.send_sse_event, smart=True)

    # RAG with real-time updates
    poem_data = await streaming_processor.adaptive_stream_processing(
        self._get_poem_data_blocking,  # Actual work
        "RAG檢索",                     # Stage name
        15, 50,                       # Progress range
        "rag",                        # Operation type
        task                          # Arguments
    )

    # LLM with real-time updates
    response_text = await streaming_processor.adaptive_stream_processing(
        self._generate_response_blocking,  # Actual work
        "LLM推理",                        # Stage name
        55, 90,                          # Progress range
        "llm",                           # Operation type
        task, poem_data                  # Arguments
    )
```

### 2. **Real-Time Progress Events**

Instead of the old stacked updates, you'll now see:

```json
# Real-time streaming (updates sent every 800ms-1.2s during processing)
{"type": "streaming_progress", "stage": "RAG檢索_start", "progress": 15, "message": "🎯 開始 RAG檢索 (預計 3.0s)", "elapsed_seconds": 0.1}

{"type": "streaming_progress", "stage": "RAG檢索_processing", "progress": 25, "message": "📡 連接向量資料庫...", "elapsed_seconds": 0.8}

{"type": "streaming_progress", "stage": "RAG檢索_processing", "progress": 30, "message": "🧮 生成查詢向量...", "elapsed_seconds": 1.6}

{"type": "streaming_progress", "stage": "RAG檢索_processing", "progress": 35, "message": "🔎 搜索相似內容...", "elapsed_seconds": 2.4}

{"type": "streaming_progress", "stage": "RAG檢索_complete", "progress": 50, "message": "✅ RAG檢索完成 (2.1s)", "elapsed_seconds": 2.1}

{"type": "streaming_progress", "stage": "LLM推理_start", "progress": 55, "message": "🎯 開始 LLM推理 (預計 15.0s)", "elapsed_seconds": 2.2}

{"type": "streaming_progress", "stage": "LLM推理_processing", "progress": 60, "message": "🧠 載入語言模型...", "elapsed_seconds": 3.4}

{"type": "streaming_progress", "stage": "LLM推理_processing", "progress": 65, "message": "📖 分析籤詩內容...", "elapsed_seconds": 4.6}

# ... continues every 1.2s until completion
```

### 3. **Enhanced Event Types**

All events now include detailed timing and progress information:

```typescript
interface StreamingProgressEvent {
  type: "streaming_progress";
  task_id: string;
  stage: string;           // "RAG檢索_processing", "LLM推理_complete", etc.
  progress: number;        // 0-100
  message: string;         // "📖 分析籤詩內容..."
  data?: {
    elapsed?: number;      // Time since operation started
    estimated_duration?: number;  // Estimated total time
    progress_rate?: number;        // Completion percentage
  };
  timestamp: string;       // ISO timestamp
  elapsed_seconds: number; // Total task elapsed time
}
```

## Frontend Integration

### JavaScript EventSource Handler

```javascript
const eventSource = new EventSource('/api/v1/streaming-chat/sse/task_123?token=' + authToken);

let lastProgressTime = Date.now();
let progressHistory = [];

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const now = Date.now();
    const timeSinceLastUpdate = now - lastProgressTime;

    if (data.type === 'streaming_progress') {
        // True real-time updates
        updateProgressBar(data.progress);
        showProgressMessage(data.message);

        // Log timing to verify real-time behavior
        console.log(`Progress: ${data.progress}% - ${data.message}`);
        console.log(`Time since last update: ${timeSinceLastUpdate}ms`);
        console.log(`Operation elapsed: ${data.elapsed_seconds}s`);

        // Store progress history
        progressHistory.push({
            progress: data.progress,
            message: data.message,
            stage: data.stage,
            timestamp: data.timestamp,
            timeSinceLastUpdate: timeSinceLastUpdate
        });

        lastProgressTime = now;

        // Show stage-specific UI
        updateStageIndicator(data.stage);
        showElapsedTime(data.elapsed_seconds);

        if (data.data?.estimated_duration) {
            showEstimatedTimeRemaining(
                data.data.estimated_duration - data.data.elapsed
            );
        }
    }
};

function updateStageIndicator(stage) {
    const stages = {
        'RAG檢索_start': '🔍 RAG 檢索',
        'RAG檢索_processing': '⚡ RAG 處理中',
        'RAG檢索_complete': '✅ RAG 完成',
        'LLM推理_start': '🤖 LLM 推理',
        'LLM推理_processing': '💭 LLM 處理中',
        'LLM推理_complete': '✅ LLM 完成'
    };

    document.getElementById('current-stage').textContent = stages[stage] || stage;
}

function showElapsedTime(seconds) {
    document.getElementById('elapsed-time').textContent = `已用時: ${seconds.toFixed(1)}s`;
}

function showEstimatedTimeRemaining(remainingSeconds) {
    if (remainingSeconds > 0) {
        document.getElementById('remaining-time').textContent =
            `預計剩餘: ${remainingSeconds.toFixed(1)}s`;
    }
}
```

### React Hook for Real-Time Progress

```javascript
import { useState, useEffect, useRef } from 'react';

function useRealTimeProgress(taskId, authToken) {
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState('');
    const [message, setMessage] = useState('');
    const [elapsedTime, setElapsedTime] = useState(0);
    const [estimatedRemaining, setEstimatedRemaining] = useState(null);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [progressHistory, setProgressHistory] = useState([]);

    const lastUpdateTime = useRef(Date.now());
    const updateIntervals = useRef([]);

    useEffect(() => {
        if (!taskId || !authToken) return;

        const eventSource = new EventSource(
            `/api/v1/streaming-chat/sse/${taskId}?token=${authToken}`
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const now = Date.now();
            const interval = now - lastUpdateTime.current;

            updateIntervals.current.push(interval);
            lastUpdateTime.current = now;

            switch (data.type) {
                case 'streaming_progress':
                    setProgress(data.progress);
                    setStage(data.stage);
                    setMessage(data.message);
                    setElapsedTime(data.elapsed_seconds);

                    if (data.data?.estimated_duration && data.data?.elapsed) {
                        setEstimatedRemaining(
                            data.data.estimated_duration - data.data.elapsed
                        );
                    }

                    setProgressHistory(prev => [...prev, {
                        ...data,
                        clientReceivedAt: new Date().toISOString(),
                        intervalSinceLastUpdate: interval
                    }]);
                    break;

                case 'complete':
                case 'enhanced_complete':
                    setProgress(100);
                    setStage('completed');
                    setMessage('完成！');
                    setResult(data.result);
                    eventSource.close();

                    // Log update intervals for debugging
                    const avgInterval = updateIntervals.current.reduce((a, b) => a + b, 0) / updateIntervals.current.length;
                    console.log(`Average update interval: ${avgInterval.toFixed(0)}ms`);
                    console.log(`Total updates received: ${updateIntervals.current.length}`);
                    break;

                case 'error':
                case 'enhanced_error':
                    setError(data.error);
                    eventSource.close();
                    break;
            }
        };

        return () => {
            eventSource.close();
        };
    }, [taskId, authToken]);

    return {
        progress,
        stage,
        message,
        elapsedTime,
        estimatedRemaining,
        result,
        error,
        progressHistory,
        averageUpdateInterval: updateIntervals.current.length > 0
            ? updateIntervals.current.reduce((a, b) => a + b, 0) / updateIntervals.current.length
            : 0
    };
}
```

## Performance Benefits

### 1. **True Real-Time Updates**
- Updates sent every **800ms-1.2s** during processing
- No more 19-second gaps without feedback
- Users see continuous progress throughout

### 2. **Adaptive Timing**
- Learning system improves estimates over time
- Better time remaining predictions
- Smart progress messages based on actual vs estimated time

### 3. **Enhanced User Experience**
- Detailed stage indicators with emojis
- Elapsed time and remaining time estimates
- Progress rate calculations
- Historical progress tracking for debugging

## Migration and Testing

### 1. **Testing Real-Time Behavior**

Use browser developer tools to verify timing:

```javascript
// Monitor update intervals
let lastUpdate = Date.now();
eventSource.onmessage = function(event) {
    const now = Date.now();
    const interval = now - lastUpdate;
    console.log(`Update interval: ${interval}ms`);
    lastUpdate = now;
};

// Should see intervals like: 800ms, 1200ms, 900ms, 1100ms
// NOT: 50ms, 50ms, 50ms, [19000ms gap], 50ms, 50ms
```

### 2. **Backward Compatibility**

- Original endpoints still work
- Enhanced endpoints provide true real-time streaming
- Clients can choose their preferred level of detail

### 3. **Configuration**

Adjust timing in `streaming_processor.py`:

```python
# RAG update interval
check_interval = 0.8  # 800ms

# LLM update interval
check_interval = 1.2  # 1200ms

# Progress steps (more steps = more frequent updates)
progress_steps = [
    (25, "📡 連接向量資料庫..."),
    (30, "🧮 生成查詢向量..."),
    # ... add more steps for finer granularity
]
```

This solution provides **true real-time progress updates** by running heavy operations in the background while maintaining a responsive event loop that can send updates during actual processing, eliminating the stacking issue you observed.