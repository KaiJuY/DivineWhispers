/**
 * Task Status Codes - must match backend definitions
 * Backend sends numeric codes, frontend translates them using i18n
 */

export const TaskStatusCode = {
  // Queue & Initialization (0-9)
  QUEUED: 0,
  INITIALIZING: 1,
  PROCESSING: 2,

  // RAG Processing (10-19)
  RAG_START: 10,
  RAG_CONNECTING: 11,
  RAG_VECTORIZING: 12,
  RAG_SEARCHING: 13,
  RAG_SCORING: 14,
  RAG_SORTING: 15,
  RAG_PREPARING: 16,
  RAG_COMPLETE: 17,

  // LLM Processing (20-39)
  LLM_START: 20,
  LLM_LOADING: 21,
  LLM_ANALYZING: 22,
  LLM_CONTEXT: 23,
  LLM_GENERATING: 24,
  LLM_OPTIMIZING: 25,
  LLM_WISDOM: 26,
  LLM_CHECKING: 27,
  LLM_POLISHING: 28,
  LLM_FORMATTING: 29,
  LLM_FINAL_CHECK: 30,
  LLM_COMPLETE: 31,

  // LLM Streaming Progress (40-49)
  LLM_STREAMING: 40,
  LLM_STREAMING_EARLY: 41,    // Just started
  LLM_STREAMING_MIDDLE: 42,   // Going well
  LLM_STREAMING_LATE: 43,     // Almost done
  LLM_STREAMING_OVERTIME: 44, // Taking longer

  // Validation (50-59)
  VALIDATING: 50,
  VALIDATION_COMPLETE: 51,

  // Completion (60-69)
  FINALIZING: 60,
  COMPLETED: 61,
  SUCCESS: 62,

  // Error states (70-79)
  ERROR: 70,
  TIMEOUT: 71,
  FAILED: 72,
} as const;

export type TaskStatusCodeType = typeof TaskStatusCode[keyof typeof TaskStatusCode];

/**
 * Get i18n translation key for status code
 */
export function getStatusI18nKey(statusCode: number): string {
  const codeToKey: Record<number, string> = {
    [TaskStatusCode.QUEUED]: 'fortuneAnalysis.status.queued',
    [TaskStatusCode.INITIALIZING]: 'fortuneAnalysis.status.initializing',
    [TaskStatusCode.PROCESSING]: 'fortuneAnalysis.status.processing',

    [TaskStatusCode.RAG_START]: 'fortuneAnalysis.status.ragStart',
    [TaskStatusCode.RAG_CONNECTING]: 'fortuneAnalysis.status.ragConnecting',
    [TaskStatusCode.RAG_VECTORIZING]: 'fortuneAnalysis.status.ragVectorizing',
    [TaskStatusCode.RAG_SEARCHING]: 'fortuneAnalysis.status.ragSearching',
    [TaskStatusCode.RAG_SCORING]: 'fortuneAnalysis.status.ragScoring',
    [TaskStatusCode.RAG_SORTING]: 'fortuneAnalysis.status.ragSorting',
    [TaskStatusCode.RAG_PREPARING]: 'fortuneAnalysis.status.ragPreparing',
    [TaskStatusCode.RAG_COMPLETE]: 'fortuneAnalysis.status.ragComplete',

    [TaskStatusCode.LLM_START]: 'fortuneAnalysis.status.llmStart',
    [TaskStatusCode.LLM_LOADING]: 'fortuneAnalysis.status.llmLoading',
    [TaskStatusCode.LLM_ANALYZING]: 'fortuneAnalysis.status.llmAnalyzing',
    [TaskStatusCode.LLM_CONTEXT]: 'fortuneAnalysis.status.llmContext',
    [TaskStatusCode.LLM_GENERATING]: 'fortuneAnalysis.status.llmGenerating',
    [TaskStatusCode.LLM_OPTIMIZING]: 'fortuneAnalysis.status.llmOptimizing',
    [TaskStatusCode.LLM_WISDOM]: 'fortuneAnalysis.status.llmWisdom',
    [TaskStatusCode.LLM_CHECKING]: 'fortuneAnalysis.status.llmChecking',
    [TaskStatusCode.LLM_POLISHING]: 'fortuneAnalysis.status.llmPolishing',
    [TaskStatusCode.LLM_FORMATTING]: 'fortuneAnalysis.status.llmFormatting',
    [TaskStatusCode.LLM_FINAL_CHECK]: 'fortuneAnalysis.status.llmFinalCheck',
    [TaskStatusCode.LLM_COMPLETE]: 'fortuneAnalysis.status.llmComplete',

    [TaskStatusCode.LLM_STREAMING]: 'fortuneAnalysis.status.llmStreaming',
    [TaskStatusCode.LLM_STREAMING_EARLY]: 'fortuneAnalysis.status.llmStreamingEarly',
    [TaskStatusCode.LLM_STREAMING_MIDDLE]: 'fortuneAnalysis.status.llmStreamingMiddle',
    [TaskStatusCode.LLM_STREAMING_LATE]: 'fortuneAnalysis.status.llmStreamingLate',
    [TaskStatusCode.LLM_STREAMING_OVERTIME]: 'fortuneAnalysis.status.llmStreamingOvertime',

    [TaskStatusCode.VALIDATING]: 'fortuneAnalysis.status.validating',
    [TaskStatusCode.VALIDATION_COMPLETE]: 'fortuneAnalysis.status.validationComplete',

    [TaskStatusCode.FINALIZING]: 'fortuneAnalysis.status.finalizing',
    [TaskStatusCode.COMPLETED]: 'fortuneAnalysis.status.completed',
    [TaskStatusCode.SUCCESS]: 'fortuneAnalysis.status.success',

    [TaskStatusCode.ERROR]: 'fortuneAnalysis.status.error',
    [TaskStatusCode.TIMEOUT]: 'fortuneAnalysis.status.timeout',
    [TaskStatusCode.FAILED]: 'fortuneAnalysis.status.failed',
  };

  return codeToKey[statusCode] || 'fortuneAnalysis.status.unknown';
}
