"""
Centralized logging configuration for Divine Whispers
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import time


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Set up centralized logging configuration with file output

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
    """

    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Generate log filename with timestamp
    log_filename = f"divine_whispers_{datetime.now().strftime('%Y%m%d')}.log"
    log_file_path = log_path / log_filename

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create and configure file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)

    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)

    # Add duplicate message filter to handlers to reduce polling noise
    duplicate_filter = DuplicateMessageFilter(time_window=300)  # 5 minutes
    file_handler.addFilter(duplicate_filter)
    console_handler.addFilter(duplicate_filter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('watchfiles.main').setLevel(logging.WARNING)  # Suppress file change spam

    # Reduce noise from specific internal modules with heavy polling
    logging.getLogger('app.services.job_processor').setLevel(logging.INFO)
    logging.getLogger('app.services.task_queue_service').setLevel(logging.INFO)

    # Set DEBUG level messages from these modules to be less verbose
    # (the duplicate filter will further reduce repetitive messages)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file_path}")
    logger.info(f"Duplicate message filter enabled (time_window=300s)")

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (defaults to calling module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class DuplicateMessageFilter(logging.Filter):
    """
    Filter to suppress duplicate/repetitive log messages within a time window.
    Useful for reducing noise from polling operations.
    """

    def __init__(self, time_window: int = 300):
        """
        Initialize the duplicate message filter.

        Args:
            time_window: Time window in seconds to track duplicates (default: 300s/5min)
        """
        super().__init__()
        self.time_window = time_window
        self.message_cache = defaultdict(float)  # message_key -> last_logged_timestamp
        self.message_count = defaultdict(int)    # message_key -> count since last log

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out duplicate messages within the time window.

        Args:
            record: Log record to filter

        Returns:
            True if message should be logged, False otherwise
        """
        # Don't filter ERROR or CRITICAL messages
        if record.levelno >= logging.ERROR:
            return True

        # Create a key from the message pattern (ignore specific values)
        message = record.getMessage()

        # Identify polling-related messages that should be filtered
        polling_patterns = [
            "checked for jobs, none available",
            "Worker worker-",
            "No jobs available",
            "Polling for tasks",
            "Task dispatcher checking",
            "SSE send ->",
            "BEGIN (implicit)",
            "ROLLBACK",
            "COMMIT",
            "SELECT chat_tasks",
            "SELECT fortune_jobs",
            "[cached since",
            "[generated in",
            "WHERE chat_tasks.status",
            "WHERE fortune_jobs.status",
            "LIMIT ? OFFSET ?",
            "FROM chat_tasks",
            "FROM fortune_jobs",
            "change detected",  # watchfiles auto-reload
        ]

        # Special handling for watchfiles logger (uvicorn --reload)
        if record.name == "watchfiles.main" and "change detected" in message:
            return False  # Suppress file change detection spam

        # Special handling for sqlalchemy.engine.Engine logger to suppress polling queries
        if record.name == "sqlalchemy.engine.Engine" and record.levelno == logging.INFO:
            # Only allow through non-repetitive SQL messages or important ones
            is_polling_sql = any(pattern in message for pattern in [
                "SELECT chat_tasks", "SELECT fortune_jobs", "BEGIN", "ROLLBACK",
                "COMMIT", "[cached", "[generated", "WHERE", "LIMIT", "FROM"
            ])
            if is_polling_sql:
                return False  # Suppress these

        is_polling_message = any(pattern in message for pattern in polling_patterns)

        if not is_polling_message:
            return True

        # Create cache key from logger name and message pattern
        cache_key = f"{record.name}:{record.levelno}:{message[:100]}"
        current_time = time.time()
        last_logged = self.message_cache.get(cache_key, 0)

        # Increment count
        self.message_count[cache_key] += 1

        # Check if enough time has passed
        if current_time - last_logged >= self.time_window:
            # Log this message and include suppression count if > 1
            count = self.message_count[cache_key]
            if count > 1:
                record.msg = f"{record.msg} (repeated {count} times in last {self.time_window}s)"

            # Reset tracking
            self.message_cache[cache_key] = current_time
            self.message_count[cache_key] = 0

            return True

        # Suppress this duplicate message
        return False


class PeriodicSummaryHandler(logging.Handler):
    """
    Handler that aggregates low-priority messages and logs summaries periodically.
    """

    def __init__(self, summary_interval: int = 600):
        """
        Initialize the periodic summary handler.

        Args:
            summary_interval: Interval in seconds between summary logs (default: 600s/10min)
        """
        super().__init__()
        self.summary_interval = summary_interval
        self.last_summary_time = time.time()
        self.message_counts = defaultdict(int)

    def emit(self, record: logging.LogRecord):
        """
        Aggregate messages and emit summaries periodically.

        Args:
            record: Log record to process
        """
        current_time = time.time()

        # Aggregate polling messages
        message = record.getMessage()
        if "checked for jobs" in message or "polling" in message.lower():
            self.message_counts["polling_checks"] += 1
        elif "SSE send" in message:
            self.message_counts["sse_messages"] += 1
        elif "task_id" in message.lower() and "processing" in message.lower():
            self.message_counts["task_processing"] += 1

        # Check if it's time to emit summary
        if current_time - self.last_summary_time >= self.summary_interval:
            if self.message_counts:
                summary_parts = []
                for msg_type, count in self.message_counts.items():
                    summary_parts.append(f"{msg_type}={count}")

                summary_message = f"Activity Summary (last {self.summary_interval}s): {', '.join(summary_parts)}"

                # Create a new log record for the summary
                summary_record = logging.LogRecord(
                    name="activity_summary",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=summary_message,
                    args=(),
                    exc_info=None
                )

                # Reset counters
                self.message_counts.clear()
                self.last_summary_time = current_time