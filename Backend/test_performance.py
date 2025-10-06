"""
Performance testing script for optimized chat_tasks system
Tests the event-driven queue and caching improvements
"""

import asyncio
import httpx
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "perftest@example.com"
TEST_PASSWORD = "PerfTest@123!"  # 12 chars, uppercase, lowercase, number, symbol

async def register_and_login():
    """Register a test user and get auth token"""
    async with httpx.AsyncClient() as client:
        # Try to register (might already exist)
        try:
            register_response = await client.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "confirm_password": TEST_PASSWORD
                }
            )
            print(f"Register: {register_response.status_code}")
        except Exception as e:
            print(f"Register failed (might already exist): {e}")

        # Login
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        if login_response.status_code == 200:
            data = login_response.json()
            return data["tokens"]["access_token"]
        else:
            print(f"Login failed: {login_response.text}")
            return None

async def test_task_submission(token: str, test_num: int):
    """Submit a test task and measure response time"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Submit task
        start_time = time.time()
        submit_time = datetime.now()

        response = await client.post(
            f"{BASE_URL}/api/v1/async-chat/ask-question",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "deity_id": "yue_lao",
                "fortune_number": 1,  # Same poem for cache testing
                "question": f"Performance test question #{test_num} - testing optimizations"
            }
        )

        submit_elapsed = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Test {test_num} failed: {response.text}")
            return None

        task_data = response.json()
        task_id = task_data["task_id"]

        print(f"\n[START] Test #{test_num} - Task {task_id}")
        print(f"   Submitted at: {submit_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   Submit time: {submit_elapsed*1000:.0f}ms")

        # Poll for completion
        completed = False
        poll_count = 0

        while not completed and poll_count < 120:  # 2 minutes max
            await asyncio.sleep(1)
            poll_count += 1

            status_response = await client.get(
                f"{BASE_URL}/api/v1/async-chat/task/{task_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if status_response.status_code == 200:
                status_data = status_response.json()

                if status_data["status"] == "completed":
                    total_time = time.time() - start_time
                    processing_time = status_data.get("processing_time_ms", 0)

                    print(f"   [OK] Completed!")
                    print(f"   Total time: {total_time:.1f}s")
                    print(f"   Processing time: {processing_time}ms ({processing_time/1000:.1f}s)")
                    print(f"   Queue wait: ~{(total_time - processing_time/1000):.1f}s")

                    return {
                        "test_num": test_num,
                        "task_id": task_id,
                        "total_time_s": total_time,
                        "processing_time_ms": processing_time,
                        "queue_wait_s": total_time - processing_time/1000,
                        "submit_time": submit_time
                    }

                elif status_data["status"] == "failed":
                    print(f"   [ERROR] Failed: {status_data.get('error', 'Unknown error')}")
                    return None

                elif poll_count % 10 == 0:
                    print(f"   [WAIT] Still processing... ({poll_count}s)")

        print(f"   [TIMEOUT] Timeout after {poll_count}s")
        return None

async def run_performance_tests():
    """Run comprehensive performance tests"""
    print("=" * 70)
    print("[TEST] PERFORMANCE TEST - Chat Tasks System Optimizations")
    print("=" * 70)

    # Get auth token
    print("\n[AUTH] Authenticating...")
    token = await register_and_login()

    if not token:
        print("[ERROR] Authentication failed")
        return

    print("[OK] Authenticated successfully")

    # Run tests
    results = []

    print("\n" + "=" * 70)
    print("TEST 1: First request (cache miss expected)")
    print("=" * 70)
    result1 = await test_task_submission(token, 1)
    if result1:
        results.append(result1)

    await asyncio.sleep(2)

    print("\n" + "=" * 70)
    print("TEST 2: Same poem (cache hit expected)")
    print("=" * 70)
    result2 = await test_task_submission(token, 2)
    if result2:
        results.append(result2)

    # Print summary
    print("\n" + "=" * 70)
    print("[SUMMARY] PERFORMANCE SUMMARY")
    print("=" * 70)

    if len(results) >= 2:
        test1 = results[0]
        test2 = results[1]

        print(f"\nTest 1 (Cache Miss):")
        print(f"  Total: {test1['total_time_s']:.1f}s")
        print(f"  Processing: {test1['processing_time_ms']/1000:.1f}s")
        print(f"  Queue wait: {test1['queue_wait_s']:.1f}s")

        print(f"\nTest 2 (Cache Hit Expected):")
        print(f"  Total: {test2['total_time_s']:.1f}s")
        print(f"  Processing: {test2['processing_time_ms']/1000:.1f}s")
        print(f"  Queue wait: {test2['queue_wait_s']:.1f}s")

        # Calculate improvements
        time_saved = test1['processing_time_ms'] - test2['processing_time_ms']
        queue_improvement = test1['queue_wait_s'] - test2['queue_wait_s']

        print(f"\n[OPTIMIZATIONS] DETECTED:")
        if test2['queue_wait_s'] < 1.0:
            print(f"  [OK] Event-driven queue: ~{test2['queue_wait_s']:.1f}s wait (excellent!)")
        else:
            print(f"  [WARN] Queue wait: {test2['queue_wait_s']:.1f}s (expected < 1s)")

        if time_saved > 500:
            print(f"  [OK] Cache working: Saved {time_saved}ms ({time_saved/1000:.1f}s)")
        else:
            print(f"  [INFO] Cache effect: {time_saved}ms (might not be cached)")

    print("\n" + "=" * 70)
    print("[LOGS] Check Backend logs for detailed performance breakdown:")
    print("   grep 'PERF_SUMMARY' logs/divine_whispers_*.log")
    print("   grep 'CACHE_HIT' logs/divine_whispers_*.log")
    print("   grep 'EVENT' logs/divine_whispers_*.log")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
