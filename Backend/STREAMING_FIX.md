# LLM Streaming Fix - Thread Safety Issue

**Date:** October 6, 2025
**Issue:** `no running event loop` errors in streaming callback
**Status:** ✅ FIXED

---

## 🐛 Problem Identified

### Error in Logs:
```
2025-10-06 22:24:57 - ERROR - Error in LLM streaming callback: no running event loop
```

### Root Cause:
The LLM streaming callback was being executed from a **thread pool executor** (sync context) but trying to use `asyncio.create_task()` which requires an active event loop in the current thread.

**Code Flow:**
```
generate_response (async)
  ↓
poem_service.generate_fortune_interpretation (async)
  ↓
loop.run_in_executor(None, call_fortune_system)  ← Runs in thread pool
  ↓
fortune_system.ask_fortune_streaming()  ← Sync function in worker thread
  ↓
llm_client.generate_stream(callback=llm_token_callback)  ← Sync function
  ↓
llm_token_callback(token)  ← Called from worker thread!
  ↓
asyncio.create_task(send_sse_event(...))  ← ERROR: No event loop in this thread!
```

---

## ✅ Solution

Changed from `asyncio.create_task()` to `asyncio.run_coroutine_threadsafe()`.

### Before (Broken):
```python
def llm_token_callback(token: str):
    try:
        accumulated_tokens.append(token)
        token_count[0] += 1

        if token_count[0] % 5 == 0:
            # ERROR: This fails when called from thread pool
            asyncio.create_task(self.send_sse_event(task.task_id, {
                "type": "llm_streaming",
                "token": token,
                ...
            }))
    except Exception as e:
        logger.error(f"Error in LLM streaming callback: {e}")
```

### After (Fixed):
```python
# Get event loop before entering thread pool
loop = asyncio.get_event_loop()

def llm_token_callback(token: str):
    try:
        accumulated_tokens.append(token)
        token_count[0] += 1

        if token_count[0] % 5 == 0:
            # FIXED: Thread-safe scheduling of coroutine
            asyncio.run_coroutine_threadsafe(
                self.send_sse_event(task.task_id, {
                    "type": "llm_streaming",
                    "token": token,
                    ...
                }),
                loop  # Schedule in main event loop
            )
    except Exception as e:
        logger.error(f"Error in LLM streaming callback: {e}")
```

---

## 🔍 Why This Works

### `asyncio.create_task()`:
- ❌ Requires active event loop **in current thread**
- ❌ Fails when called from thread pool worker
- ✅ Fast and simple for same-thread async code

### `asyncio.run_coroutine_threadsafe()`:
- ✅ Can be called from **any thread**
- ✅ Schedules coroutine in specified event loop
- ✅ Thread-safe by design
- ✅ Returns a `concurrent.futures.Future` (we don't need to wait for it)

---

## 📊 Test Results

### Before Fix:
```
Line 4331-4406: 75+ errors "no running event loop"
Line 4564: Task completed successfully (streaming failed but didn't break core functionality)
```

### After Fix:
- No streaming errors expected
- LLM tokens will flow to frontend via SSE
- Users will see real-time generation

---

## 🎯 Key Learning

**When working with asyncio and threads:**

1. **Same Thread** → Use `asyncio.create_task()`
2. **Different Thread** → Use `asyncio.run_coroutine_threadsafe()`

**Our case:**
- Main async context runs in event loop thread
- LLM generation runs in thread pool (blocking operation)
- Callback runs in worker thread
- Need to schedule SSE events back in main event loop

**Solution Pattern:**
```python
# In async context, before thread pool
loop = asyncio.get_event_loop()

def sync_callback_in_thread():
    # Called from thread pool worker
    asyncio.run_coroutine_threadsafe(
        async_function(...),
        loop  # Main event loop reference
    )
```

---

## ✅ Verification Steps

1. **Restart Backend** - Load the fixed code
2. **Submit Question** - Watch for streaming events
3. **Check Logs** - Should see NO "no running event loop" errors
4. **Frontend SSE** - Should receive `llm_streaming` events

---

## 📝 Files Changed

**File:** `Backend/app/services/task_queue_service.py`
**Line:** ~558
**Change:** Added `loop = asyncio.get_event_loop()` and changed to `asyncio.run_coroutine_threadsafe()`

---

## 🚀 Status

✅ **Fixed and ready for testing**

The streaming implementation is now thread-safe and should work correctly!
