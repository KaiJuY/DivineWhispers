"""
Real-time progress tracking for long-running operations
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    task_id: str
    stage: str
    progress: int  # 0-100
    message: str
    data: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "type": "progress",
            "task_id": self.task_id,
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class ProgressTracker:
    """
    Real-time progress tracker that can send updates to multiple subscribers
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.subscribers: List[Callable] = []
        self.current_progress = 0
        self.current_stage = "initialized"
        self.start_time = time.time()
        self.stage_times: Dict[str, float] = {}

    def subscribe(self, callback: Callable[[ProgressUpdate], None]):
        """Subscribe to progress updates"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from progress updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def update(self, stage: str, progress: int, message: str, data: Optional[Dict] = None):
        """Send progress update to all subscribers"""
        self.current_progress = progress
        self.current_stage = stage
        self.stage_times[stage] = time.time()

        update = ProgressUpdate(
            task_id=self.task_id,
            stage=stage,
            progress=progress,
            message=message,
            data=data
        )

        logger.debug(f"Progress update for {self.task_id}: {stage} - {progress}% - {message}")

        # Send to all subscribers
        for callback in self.subscribers[:]:  # Copy to avoid modification during iteration
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Error sending progress update to subscriber: {e}")

    async def update_with_substeps(self, stage: str, base_progress: int, progress_range: int,
                                   message: str, substeps: int = 5, delay: float = 0.5):
        """
        Update progress with simulated substeps for long-running operations

        Args:
            stage: Current stage name
            base_progress: Starting progress percentage
            progress_range: Range of progress to cover (e.g., 20 for 20%)
            message: Base message
            substeps: Number of substeps to simulate
            delay: Delay between substeps in seconds
        """
        step_size = progress_range / substeps

        for i in range(substeps):
            current_progress = int(base_progress + (i * step_size))
            step_message = f"{message} ({i+1}/{substeps})"

            await self.update(stage, current_progress, step_message)

            if i < substeps - 1:  # Don't delay after the last step
                await asyncio.sleep(delay)

    def get_elapsed_time(self) -> float:
        """Get elapsed time since tracker creation"""
        return time.time() - self.start_time

    def get_stage_duration(self, stage: str) -> Optional[float]:
        """Get duration of a specific stage"""
        if stage in self.stage_times:
            return self.stage_times[stage] - self.start_time
        return None


class StreamingProgressTracker(ProgressTracker):
    """
    Enhanced progress tracker that simulates streaming responses
    """

    async def simulate_llm_streaming(self, base_progress: int = 70, progress_range: int = 25,
                                     chunks: Optional[List[str]] = None):
        """
        Simulate LLM streaming response with progress updates

        Args:
            base_progress: Starting progress percentage
            progress_range: Range of progress to cover
            chunks: Optional list of response chunks to simulate
        """
        if chunks is None:
            chunks = [
                "根據您的問題，我開始分析相關的籤詩內容...",
                "正在結合傳統智慧與現代解釋...",
                "分析您的具體情況與籤詩的對應關係...",
                "整合多方面的建議與指導...",
                "準備最終的個人化解釋..."
            ]

        chunk_progress = progress_range / len(chunks)

        for i, chunk in enumerate(chunks):
            current_progress = int(base_progress + (i * chunk_progress))

            await self.update(
                stage="generating_llm",
                progress=current_progress,
                message=f"正在生成回應... ({i+1}/{len(chunks)})",
                data={"chunk": chunk, "chunk_index": i, "total_chunks": len(chunks)}
            )

            # Simulate processing time
            await asyncio.sleep(0.8)

    async def simulate_rag_processing(self, base_progress: int = 20, progress_range: int = 30):
        """
        Simulate RAG processing with detailed progress updates
        """
        rag_steps = [
            ("query_embedding", "生成查詢向量..."),
            ("similarity_search", "搜索相似內容..."),
            ("context_ranking", "排序相關文檔..."),
            ("context_preparation", "準備上下文...")
        ]

        step_progress = progress_range / len(rag_steps)

        for i, (step_name, step_message) in enumerate(rag_steps):
            current_progress = int(base_progress + (i * step_progress))

            await self.update(
                stage="analyzing_rag",
                progress=current_progress,
                message=step_message,
                data={"rag_step": step_name, "step_index": i, "total_steps": len(rag_steps)}
            )

            # Simulate processing time
            await asyncio.sleep(0.6)


class ProgressTrackerManager:
    """
    Global manager for progress trackers
    """

    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}

    def create_tracker(self, task_id: str, streaming: bool = False) -> ProgressTracker:
        """Create a new progress tracker"""
        if streaming:
            tracker = StreamingProgressTracker(task_id)
        else:
            tracker = ProgressTracker(task_id)

        self.trackers[task_id] = tracker
        logger.info(f"Created progress tracker for task {task_id}")
        return tracker

    def get_tracker(self, task_id: str) -> Optional[ProgressTracker]:
        """Get existing progress tracker"""
        return self.trackers.get(task_id)

    def remove_tracker(self, task_id: str):
        """Remove progress tracker"""
        if task_id in self.trackers:
            del self.trackers[task_id]
            logger.info(f"Removed progress tracker for task {task_id}")

    def cleanup_old_trackers(self, max_age_seconds: float = 3600):
        """Clean up old trackers (older than max_age_seconds)"""
        current_time = time.time()
        to_remove = []

        for task_id, tracker in self.trackers.items():
            if current_time - tracker.start_time > max_age_seconds:
                to_remove.append(task_id)

        for task_id in to_remove:
            self.remove_tracker(task_id)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old progress trackers")


# Global progress tracker manager
progress_manager = ProgressTrackerManager()


async def create_progress_aware_task(task_id: str, sse_callback: Callable, streaming: bool = True):
    """
    Create a progress tracker and set up SSE callback

    Args:
        task_id: Task identifier
        sse_callback: Callback function to send SSE events
        streaming: Whether to use streaming progress tracker

    Returns:
        ProgressTracker instance
    """
    tracker = progress_manager.create_tracker(task_id, streaming)

    # Subscribe SSE callback to progress updates
    async def sse_progress_callback(update: ProgressUpdate):
        try:
            await sse_callback(task_id, update.to_dict())
        except Exception as e:
            logger.error(f"Error sending progress via SSE: {e}")

    tracker.subscribe(sse_progress_callback)

    return tracker