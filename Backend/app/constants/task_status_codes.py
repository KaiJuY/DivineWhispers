"""
Task Status Codes for SSE Progress Updates

Backend sends numeric codes, frontend handles i18n translation.
This ensures stable, consistent status reporting independent of language.
"""

class TaskStatusCode:
    """Numeric status codes for task progress tracking"""

    # Queue & Initialization (0-9)
    QUEUED = 0
    INITIALIZING = 1
    PROCESSING = 2

    # RAG Processing (10-19)
    RAG_START = 10
    RAG_CONNECTING = 11
    RAG_VECTORIZING = 12
    RAG_SEARCHING = 13
    RAG_SCORING = 14
    RAG_SORTING = 15
    RAG_PREPARING = 16
    RAG_COMPLETE = 17

    # LLM Processing (20-39)
    LLM_START = 20
    LLM_LOADING = 21
    LLM_ANALYZING = 22
    LLM_CONTEXT = 23
    LLM_GENERATING = 24
    LLM_OPTIMIZING = 25
    LLM_WISDOM = 26
    LLM_CHECKING = 27
    LLM_POLISHING = 28
    LLM_FORMATTING = 29
    LLM_FINAL_CHECK = 30
    LLM_COMPLETE = 31

    # LLM Streaming Progress (40-49)
    LLM_STREAMING = 40
    LLM_STREAMING_EARLY = 41    # Just started
    LLM_STREAMING_MIDDLE = 42   # Going well
    LLM_STREAMING_LATE = 43     # Almost done
    LLM_STREAMING_OVERTIME = 44 # Taking longer

    # Validation (50-59)
    VALIDATING = 50
    VALIDATION_COMPLETE = 51

    # Completion (60-69)
    FINALIZING = 60
    COMPLETED = 61
    SUCCESS = 62

    # Error states (70-79)
    ERROR = 70
    TIMEOUT = 71
    FAILED = 72


# Mapping for readable names (for logging/debugging)
STATUS_CODE_NAMES = {
    TaskStatusCode.QUEUED: "QUEUED",
    TaskStatusCode.INITIALIZING: "INITIALIZING",
    TaskStatusCode.PROCESSING: "PROCESSING",

    TaskStatusCode.RAG_START: "RAG_START",
    TaskStatusCode.RAG_CONNECTING: "RAG_CONNECTING",
    TaskStatusCode.RAG_VECTORIZING: "RAG_VECTORIZING",
    TaskStatusCode.RAG_SEARCHING: "RAG_SEARCHING",
    TaskStatusCode.RAG_SCORING: "RAG_SCORING",
    TaskStatusCode.RAG_SORTING: "RAG_SORTING",
    TaskStatusCode.RAG_PREPARING: "RAG_PREPARING",
    TaskStatusCode.RAG_COMPLETE: "RAG_COMPLETE",

    TaskStatusCode.LLM_START: "LLM_START",
    TaskStatusCode.LLM_LOADING: "LLM_LOADING",
    TaskStatusCode.LLM_ANALYZING: "LLM_ANALYZING",
    TaskStatusCode.LLM_CONTEXT: "LLM_CONTEXT",
    TaskStatusCode.LLM_GENERATING: "LLM_GENERATING",
    TaskStatusCode.LLM_OPTIMIZING: "LLM_OPTIMIZING",
    TaskStatusCode.LLM_WISDOM: "LLM_WISDOM",
    TaskStatusCode.LLM_CHECKING: "LLM_CHECKING",
    TaskStatusCode.LLM_POLISHING: "LLM_POLISHING",
    TaskStatusCode.LLM_FORMATTING: "LLM_FORMATTING",
    TaskStatusCode.LLM_FINAL_CHECK: "LLM_FINAL_CHECK",
    TaskStatusCode.LLM_COMPLETE: "LLM_COMPLETE",

    TaskStatusCode.LLM_STREAMING: "LLM_STREAMING",
    TaskStatusCode.LLM_STREAMING_EARLY: "LLM_STREAMING_EARLY",
    TaskStatusCode.LLM_STREAMING_MIDDLE: "LLM_STREAMING_MIDDLE",
    TaskStatusCode.LLM_STREAMING_LATE: "LLM_STREAMING_LATE",
    TaskStatusCode.LLM_STREAMING_OVERTIME: "LLM_STREAMING_OVERTIME",

    TaskStatusCode.VALIDATING: "VALIDATING",
    TaskStatusCode.VALIDATION_COMPLETE: "VALIDATION_COMPLETE",

    TaskStatusCode.FINALIZING: "FINALIZING",
    TaskStatusCode.COMPLETED: "COMPLETED",
    TaskStatusCode.SUCCESS: "SUCCESS",

    TaskStatusCode.ERROR: "ERROR",
    TaskStatusCode.TIMEOUT: "TIMEOUT",
    TaskStatusCode.FAILED: "FAILED",
}


def get_status_name(code: int) -> str:
    """Get readable status name from code"""
    return STATUS_CODE_NAMES.get(code, f"UNKNOWN_{code}")
