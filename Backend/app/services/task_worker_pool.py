"""
Task Worker Pool for concurrent task processing
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from app.models.chat_task import ChatTask, TaskStatus

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class WorkerMetrics:
    """Metrics for a worker"""
    worker_id: str
    status: WorkerStatus
    tasks_completed: int
    tasks_failed: int
    total_processing_time: float
    current_task_id: Optional[str] = None
    last_activity: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

    @property
    def avg_processing_time(self) -> float:
        """Average processing time per task"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 0.0
        return self.total_processing_time / total_tasks

    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 100.0
        return (self.tasks_completed / total_tasks) * 100


class TaskWorkerPool:
    """
    Manages a pool of workers for concurrent task processing
    """

    def __init__(self, max_workers: int = 3, worker_timeout: float = 120.0):
        self.max_workers = max_workers
        self.worker_timeout = worker_timeout
        self.workers: Dict[str, WorkerMetrics] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, str] = {}  # task_id -> worker_id
        self.worker_tasks: Dict[str, asyncio.Task] = {}  # worker_id -> asyncio.Task
        self.is_running = False
        self._shutdown_event = asyncio.Event()

        # Pool metrics
        self.total_tasks_processed = 0
        self.total_tasks_failed = 0
        self.pool_started_at = datetime.now()

    async def start(self):
        """Start the worker pool"""
        if self.is_running:
            logger.warning("Worker pool is already running")
            return

        logger.info(f"Starting worker pool with {self.max_workers} workers")
        self.is_running = True
        self._shutdown_event.clear()

        # Start workers
        for i in range(self.max_workers):
            worker_id = f"worker-{i+1}"
            await self._start_worker(worker_id)

        # Start monitoring task
        asyncio.create_task(self._monitor_workers())

        logger.info(f"Worker pool started successfully with {len(self.workers)} workers")

    async def stop(self):
        """Stop the worker pool and all workers"""
        if not self.is_running:
            return

        logger.info("Stopping worker pool...")
        self.is_running = False
        self._shutdown_event.set()

        # Cancel all worker tasks
        for worker_id, worker_task in self.worker_tasks.items():
            if not worker_task.done():
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass

        # Update worker statuses
        for worker_id in self.workers:
            self.workers[worker_id].status = WorkerStatus.SHUTDOWN

        # Clear queues and tasks
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.worker_tasks.clear()
        self.active_tasks.clear()

        logger.info("Worker pool stopped successfully")

    async def submit_task(self, task_id: str, task_processor_func, *args, **kwargs):
        """
        Submit a task to the worker pool

        Args:
            task_id: Unique task identifier
            task_processor_func: Function to process the task
            *args, **kwargs: Arguments for the processor function
        """
        if not self.is_running:
            raise RuntimeError("Worker pool is not running")

        if task_id in self.active_tasks:
            logger.warning(f"Task {task_id} is already being processed")
            return

        task_item = {
            'task_id': task_id,
            'processor_func': task_processor_func,
            'args': args,
            'kwargs': kwargs,
            'submitted_at': datetime.now()
        }

        await self.task_queue.put(task_item)
        logger.info(f"Task {task_id} submitted to worker pool (queue size: {self.task_queue.qsize()})")

    async def _start_worker(self, worker_id: str):
        """Start a single worker"""
        worker_metrics = WorkerMetrics(
            worker_id=worker_id,
            status=WorkerStatus.IDLE,
            tasks_completed=0,
            tasks_failed=0,
            total_processing_time=0.0
        )
        self.workers[worker_id] = worker_metrics

        # Start worker coroutine
        worker_task = asyncio.create_task(self._worker_loop(worker_id))
        self.worker_tasks[worker_id] = worker_task

        logger.info(f"Started worker: {worker_id}")

    async def _worker_loop(self, worker_id: str):
        """Main loop for a worker"""
        worker = self.workers[worker_id]

        try:
            while self.is_running and not self._shutdown_event.is_set():
                try:
                    # Wait for a task with timeout
                    task_item = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=5.0  # Check shutdown every 5 seconds
                    )

                    await self._process_task_item(worker_id, task_item)

                except asyncio.TimeoutError:
                    # No task available, continue checking
                    continue
                except Exception as e:
                    logger.error(f"Worker {worker_id} encountered error: {e}")
                    worker.status = WorkerStatus.ERROR
                    await asyncio.sleep(1)  # Brief pause before retrying
                    worker.status = WorkerStatus.IDLE

        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} was cancelled")
        except Exception as e:
            logger.error(f"Worker {worker_id} crashed: {e}")
            worker.status = WorkerStatus.ERROR
        finally:
            worker.status = WorkerStatus.SHUTDOWN
            logger.info(f"Worker {worker_id} stopped")

    async def _process_task_item(self, worker_id: str, task_item: Dict):
        """Process a single task item"""
        worker = self.workers[worker_id]
        task_id = task_item['task_id']
        processor_func = task_item['processor_func']
        args = task_item['args']
        kwargs = task_item['kwargs']

        start_time = time.time()
        worker.status = WorkerStatus.BUSY
        worker.current_task_id = task_id
        worker.last_activity = datetime.now()

        # Track active task
        self.active_tasks[task_id] = worker_id

        try:
            logger.info(f"Worker {worker_id} starting task {task_id}")

            # Process the task with timeout
            await asyncio.wait_for(
                processor_func(*args, **kwargs),
                timeout=self.worker_timeout
            )

            # Task completed successfully
            processing_time = time.time() - start_time
            worker.tasks_completed += 1
            worker.total_processing_time += processing_time
            self.total_tasks_processed += 1

            logger.info(f"Worker {worker_id} completed task {task_id} in {processing_time:.2f}s")

        except asyncio.TimeoutError:
            logger.error(f"Worker {worker_id} task {task_id} timed out after {self.worker_timeout}s")
            worker.tasks_failed += 1
            self.total_tasks_failed += 1

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Worker {worker_id} task {task_id} failed after {processing_time:.2f}s: {e}")
            worker.tasks_failed += 1
            worker.total_processing_time += processing_time
            self.total_tasks_failed += 1

        finally:
            # Clean up task tracking
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            worker.status = WorkerStatus.IDLE
            worker.current_task_id = None
            worker.last_activity = datetime.now()

    async def _monitor_workers(self):
        """Monitor worker health and performance"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                if not self.is_running:
                    break

                # Check for stuck workers
                now = datetime.now()
                for worker_id, worker in self.workers.items():
                    if worker.status == WorkerStatus.BUSY:
                        time_since_activity = now - worker.last_activity
                        if time_since_activity > timedelta(seconds=self.worker_timeout * 1.5):
                            logger.warning(
                                f"Worker {worker_id} appears stuck on task {worker.current_task_id} "
                                f"for {time_since_activity.total_seconds():.1f}s"
                            )

                # Log pool status
                self._log_pool_status()

            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")

    def _log_pool_status(self):
        """Log current pool status"""
        active_workers = sum(1 for w in self.workers.values() if w.status == WorkerStatus.BUSY)
        idle_workers = sum(1 for w in self.workers.values() if w.status == WorkerStatus.IDLE)
        error_workers = sum(1 for w in self.workers.values() if w.status == WorkerStatus.ERROR)

        queue_size = self.task_queue.qsize()
        active_tasks = len(self.active_tasks)

        logger.info(
            f"Worker Pool Status - Active: {active_workers}, Idle: {idle_workers}, "
            f"Error: {error_workers}, Queue: {queue_size}, Processing: {active_tasks}"
        )

    def get_metrics(self) -> Dict:
        """Get comprehensive pool metrics"""
        now = datetime.now()
        uptime = now - self.pool_started_at

        worker_metrics = []
        for worker_id, worker in self.workers.items():
            worker_metrics.append({
                'worker_id': worker_id,
                'status': worker.status.value,
                'tasks_completed': worker.tasks_completed,
                'tasks_failed': worker.tasks_failed,
                'success_rate': worker.success_rate,
                'avg_processing_time': worker.avg_processing_time,
                'current_task_id': worker.current_task_id,
                'last_activity': worker.last_activity.isoformat() if worker.last_activity else None
            })

        return {
            'pool_status': {
                'is_running': self.is_running,
                'max_workers': self.max_workers,
                'active_workers': len([w for w in self.workers.values() if w.status == WorkerStatus.BUSY]),
                'idle_workers': len([w for w in self.workers.values() if w.status == WorkerStatus.IDLE]),
                'error_workers': len([w for w in self.workers.values() if w.status == WorkerStatus.ERROR]),
                'uptime_seconds': uptime.total_seconds()
            },
            'queue_status': {
                'queue_size': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks)
            },
            'performance': {
                'total_tasks_processed': self.total_tasks_processed,
                'total_tasks_failed': self.total_tasks_failed,
                'success_rate': (self.total_tasks_processed / max(1, self.total_tasks_processed + self.total_tasks_failed)) * 100
            },
            'workers': worker_metrics
        }

    def is_task_active(self, task_id: str) -> bool:
        """Check if a task is currently being processed"""
        return task_id in self.active_tasks

    def get_worker_for_task(self, task_id: str) -> Optional[str]:
        """Get the worker ID processing a specific task"""
        return self.active_tasks.get(task_id)