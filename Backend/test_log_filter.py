"""
Test script to verify log filtering reduces polling noise
"""

import logging
import time
from app.utils.logging_config import setup_logging

# Setup logging with the duplicate filter
setup_logging(log_level="INFO", log_dir="logs")

# Get logger for testing
logger = logging.getLogger("test_polling_logger")

print("Testing log filtering - simulating polling operations...")
print("=" * 70)

# Simulate polling operations that would normally create noise
for i in range(50):
    logger.info(f"Worker worker-{i % 2} checked for jobs, none available")
    logger.debug(f"SSE send -> task=test-{i} type=progress")

    # Some important messages that should always appear
    if i % 10 == 0:
        logger.warning(f"Important checkpoint {i}")
        logger.error(f"Critical error at iteration {i}")

    # Simulate delay between polls
    time.sleep(0.1)

print("=" * 70)
print("Test complete. Check logs/divine_whispers_*.log to verify filtering.")
print("\nExpected behavior:")
print("- Polling messages should be aggregated (not 50 separate entries)")
print("- Warning and error messages should all appear")
print("- First polling message appears, then suppressed, then summary after time window")
