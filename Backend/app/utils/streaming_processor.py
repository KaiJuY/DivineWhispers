"""
True streaming processor that provides real-time updates during actual processing
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingProcessor:
    """
    Processor that provides real-time updates during long-running operations
    """

    def __init__(self, task_id: str, progress_callback: Callable):
        self.task_id = task_id
        self.progress_callback = progress_callback
        self.current_stage = "initialized"
        self.current_progress = 0
        self.start_time = time.time()
        self.is_cancelled = False

    async def send_update(self, stage: str, progress: int, message: str, data: Optional[Dict] = None):
        """Send progress update via callback"""
        self.current_stage = stage
        self.current_progress = progress

        update_data = {
            "type": "streaming_progress",
            "task_id": self.task_id,
            "stage": stage,
            "progress": progress,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - self.start_time, 2)
        }

        try:
            await self.progress_callback(self.task_id, update_data)
        except Exception as e:
            logger.error(f"Error sending streaming update: {e}")

    async def stream_rag_processing(self, rag_function: Callable, *args, **kwargs):
        """Stream RAG processing with real-time updates"""
        await self.send_update("rag_start", 20, "🔍 開始 RAG 檢索...")

        # Create background task for RAG processing
        rag_task = asyncio.create_task(rag_function(*args, **kwargs))

        # Simulate streaming progress while RAG is running
        progress_steps = [
            (25, "📡 連接向量資料庫..."),
            (30, "🧮 生成查詢向量..."),
            (35, "🔎 搜索相似內容..."),
            (40, "📊 計算相似度分數..."),
            (45, "📋 排序搜索結果..."),
            (48, "📝 準備上下文資料...")
        ]

        step_index = 0
        check_interval = 0.8  # Check every 800ms

        while not rag_task.done() and not self.is_cancelled:
            if step_index < len(progress_steps):
                progress, message = progress_steps[step_index]
                await self.send_update("rag_processing", progress, message)
                step_index += 1

            try:
                # Wait for either task completion or timeout
                await asyncio.wait_for(asyncio.shield(rag_task), timeout=check_interval)
                break  # Task completed
            except asyncio.TimeoutError:
                # Task still running, continue with progress updates
                continue

        if rag_task.done():
            await self.send_update("rag_complete", 50, "✅ RAG 檢索完成")
            return await rag_task
        else:
            # Handle cancellation
            rag_task.cancel()
            raise asyncio.CancelledError("RAG processing was cancelled")

    async def stream_llm_processing(self, llm_function: Callable, *args, **kwargs):
        """Stream LLM processing with real-time updates"""
        await self.send_update("llm_start", 55, "🤖 啟動 LLM 推理引擎...")

        # Create background task for LLM processing
        llm_task = asyncio.create_task(llm_function(*args, **kwargs))

        # More detailed LLM progress simulation
        progress_steps = [
            (60, "🧠 載入語言模型..."),
            (65, "📖 分析籤詩內容..."),
            (68, "🔗 建立上下文關聯..."),
            (72, "💭 生成初步回應..."),
            (75, "🎨 優化表達方式..."),
            (78, "📚 結合傳統智慧..."),
            (82, "🔍 檢查邏輯一致性..."),
            (85, "✨ 潤飾最終回應..."),
            (88, "📋 格式化輸出..."),
            (90, "🔍 最終品質檢查...")
        ]

        step_index = 0
        check_interval = 1.2  # Check every 1.2 seconds for LLM

        while not llm_task.done() and not self.is_cancelled:
            if step_index < len(progress_steps):
                progress, message = progress_steps[step_index]
                await self.send_update("llm_processing", progress, message)
                step_index += 1

            try:
                # Wait for either task completion or timeout
                await asyncio.wait_for(asyncio.shield(llm_task), timeout=check_interval)
                break  # Task completed
            except asyncio.TimeoutError:
                # Task still running, continue with progress updates
                continue

        if llm_task.done():
            await self.send_update("llm_complete", 92, "✅ LLM 推理完成")
            return await llm_task
        else:
            # Handle cancellation
            llm_task.cancel()
            raise asyncio.CancelledError("LLM processing was cancelled")

    async def stream_with_heartbeat(self, operation_function: Callable, stage_name: str,
                                    start_progress: int, end_progress: int,
                                    base_message: str, *args, **kwargs):
        """
        Stream any operation with heartbeat updates
        """
        await self.send_update(f"{stage_name}_start", start_progress, f"🚀 開始 {base_message}...")

        # Create background task
        operation_task = asyncio.create_task(operation_function(*args, **kwargs))

        # Progress increment
        progress_range = end_progress - start_progress
        max_steps = 8
        step_size = progress_range / max_steps

        step = 0
        check_interval = 1.0

        while not operation_task.done() and not self.is_cancelled:
            if step < max_steps:
                current_progress = int(start_progress + (step * step_size))
                dots = "." * ((step % 3) + 1)
                message = f"⏳ {base_message}中{dots}"

                await self.send_update(f"{stage_name}_processing", current_progress, message, {
                    "step": step + 1,
                    "max_steps": max_steps,
                    "operation": stage_name
                })
                step += 1

            try:
                await asyncio.wait_for(asyncio.shield(operation_task), timeout=check_interval)
                break
            except asyncio.TimeoutError:
                continue

        if operation_task.done():
            await self.send_update(f"{stage_name}_complete", end_progress, f"✅ {base_message}完成")
            return await operation_task
        else:
            operation_task.cancel()
            raise asyncio.CancelledError(f"{stage_name} processing was cancelled")

    def cancel(self):
        """Cancel the streaming processor"""
        self.is_cancelled = True


class SmartStreamingProcessor(StreamingProcessor):
    """
    Enhanced streaming processor with adaptive timing
    """

    def __init__(self, task_id: str, progress_callback: Callable):
        super().__init__(task_id, progress_callback)
        self.operation_history: List[Dict] = []

    async def adaptive_stream_processing(self, operation_function: Callable, stage_name: str,
                                         start_progress: int, end_progress: int,
                                         operation_type: str, *args, **kwargs):
        """
        Adaptively stream processing based on operation type and historical data
        """
        operation_start = time.time()

        # Estimate duration based on operation type
        estimated_duration = self._estimate_duration(operation_type)
        await self.send_update(f"{stage_name}_start", start_progress,
                               f"🎯 開始 {stage_name} (預計 {estimated_duration:.1f}s)")

        # Create the actual operation task
        operation_task = asyncio.create_task(operation_function(*args, **kwargs))

        # Adaptive progress updates
        progress_range = end_progress - start_progress
        update_interval = max(0.5, estimated_duration / 10)  # Update 10 times during operation

        last_update_time = time.time()
        current_step = 0

        while not operation_task.done() and not self.is_cancelled:
            current_time = time.time()
            elapsed = current_time - operation_start

            # Calculate adaptive progress
            if estimated_duration > 0:
                estimated_progress = min(90, (elapsed / estimated_duration) * 100)  # Cap at 90%
            else:
                estimated_progress = start_progress + (current_step * 5)  # Fallback

            actual_progress = int(start_progress + (estimated_progress / 100) * progress_range)
            actual_progress = min(actual_progress, end_progress - 2)  # Leave room for completion

            # Send update if enough time has passed
            if current_time - last_update_time >= update_interval:
                message = self._get_adaptive_message(stage_name, elapsed, estimated_duration)
                await self.send_update(f"{stage_name}_processing", actual_progress, message, {
                    "elapsed": round(elapsed, 1),
                    "estimated_duration": estimated_duration,
                    "progress_rate": round(estimated_progress, 1)
                })

                last_update_time = current_time
                current_step += 1

            # Check if operation completed
            try:
                await asyncio.wait_for(asyncio.shield(operation_task), timeout=0.3)
                break
            except asyncio.TimeoutError:
                continue

        # Record operation completion
        actual_duration = time.time() - operation_start
        self.operation_history.append({
            "type": operation_type,
            "duration": actual_duration,
            "estimated": estimated_duration,
            "timestamp": datetime.now()
        })

        if operation_task.done():
            await self.send_update(f"{stage_name}_complete", end_progress,
                                   f"✅ {stage_name} 完成 ({actual_duration:.1f}s)")
            return await operation_task
        else:
            operation_task.cancel()
            raise asyncio.CancelledError(f"{stage_name} processing was cancelled")

    def _estimate_duration(self, operation_type: str) -> float:
        """Estimate operation duration based on historical data"""
        # Get recent operations of the same type
        recent_ops = [op for op in self.operation_history[-10:] if op["type"] == operation_type]

        if recent_ops:
            # Use average of recent operations
            avg_duration = sum(op["duration"] for op in recent_ops) / len(recent_ops)
            return avg_duration
        else:
            # Default estimates
            defaults = {
                "rag": 3.0,
                "llm": 15.0,
                "poem_lookup": 2.0,
                "initialization": 1.0
            }
            return defaults.get(operation_type, 5.0)

    def _get_adaptive_message(self, stage_name: str, elapsed: float, estimated: float) -> str:
        """Generate adaptive progress message"""
        if elapsed < estimated * 0.3:
            return f"🚀 {stage_name} 進行中... (剛開始)"
        elif elapsed < estimated * 0.7:
            return f"⚡ {stage_name} 進行中... (進展順利)"
        elif elapsed < estimated:
            return f"🔄 {stage_name} 進行中... (即將完成)"
        else:
            return f"⏰ {stage_name} 進行中... (比預期稍長)"


# Global processor registry
_active_processors: Dict[str, StreamingProcessor] = {}


def create_streaming_processor(task_id: str, progress_callback: Callable,
                               smart: bool = True) -> StreamingProcessor:
    """Create and register a streaming processor"""
    if smart:
        processor = SmartStreamingProcessor(task_id, progress_callback)
    else:
        processor = StreamingProcessor(task_id, progress_callback)

    _active_processors[task_id] = processor
    return processor


def get_streaming_processor(task_id: str) -> Optional[StreamingProcessor]:
    """Get active streaming processor"""
    return _active_processors.get(task_id)


def cleanup_streaming_processor(task_id: str):
    """Clean up streaming processor"""
    if task_id in _active_processors:
        processor = _active_processors[task_id]
        processor.cancel()
        del _active_processors[task_id]


def cleanup_old_processors(max_age_seconds: float = 600):
    """Clean up old processors"""
    current_time = time.time()
    to_remove = []

    for task_id, processor in _active_processors.items():
        if current_time - processor.start_time > max_age_seconds:
            to_remove.append(task_id)

    for task_id in to_remove:
        cleanup_streaming_processor(task_id)