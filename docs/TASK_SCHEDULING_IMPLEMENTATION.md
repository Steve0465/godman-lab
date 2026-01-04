# Task Scheduling Implementation Summary

## Overview

This implementation adds comprehensive task scheduling capabilities to the GodmanAI system through a new TaskManager component and REST API endpoints. The system supports immediate execution, recurring schedules (hourly, daily), and flexible CRON-based scheduling.

## Components Added

### 1. TaskManager (`godman_ai/scheduler/task_manager.py`)

A new SQLite-based task management system that:
- Persists scheduled tasks to `.godman/state/tasks.db`
- Supports multiple schedule types: `now`, `hourly`, `daily`, `cron`
- Calculates next run times automatically
- Integrates with existing JobQueue for task execution
- Tracks execution metadata (run count, last run, next run)

**Key Features:**
- Persistent storage with SQLite
- Automatic next-run calculation
- Task lifecycle management (pending → active → completed/failed)
- Metadata support for custom task attributes
- Priority-based execution

### 2. API Endpoints (`godman_ai/service/api.py`)

Five new REST endpoints for task management:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/task` | Create a new scheduled task |
| GET | `/task` | List tasks with optional filtering |
| GET | `/task/{task_id}` | Get specific task details |
| PUT | `/task/{task_id}` | Update a scheduled task |
| DELETE | `/task/{task_id}` | Cancel/delete a task |

### 3. Daemon Integration (`godman_ai/service/daemon.py`)

The daemon scheduler loop now:
- Checks for pending tasks every second
- Automatically enqueues tasks when their scheduled time arrives
- Updates task metadata after execution
- Calculates next run times for recurring tasks

## Schedule Types

### 1. Now (Immediate Execution)
```json
{
  "task_input": "process receipts",
  "schedule_type": "now"
}
```
- Executes immediately
- Task status changes to `completed` after execution

### 2. Hourly
```json
{
  "task_input": "sync data",
  "schedule_type": "hourly"
}
```
- Runs at the top of every hour (e.g., 1:00, 2:00, 3:00)
- Automatically reschedules after each execution

### 3. Daily
```json
{
  "task_input": "daily backup",
  "schedule_type": "daily",
  "schedule_value": "02:00"
}
```
- Runs daily at specified time (HH:MM format)
- Defaults to midnight if no time specified

### 4. CRON
```json
{
  "task_input": "health check",
  "schedule_type": "cron",
  "schedule_value": "*/15 * * * *"
}
```
- Supports standard 5-field CRON expressions
- Uses `croniter` library when available, falls back to basic parser
- Examples:
  - `*/15 * * * *` - Every 15 minutes
  - `0 */2 * * *` - Every 2 hours
  - `30 14 * * *` - Daily at 14:30

## Database Schema

### scheduled_tasks Table

```sql
CREATE TABLE scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_input TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    last_run TEXT,
    next_run TEXT,
    run_count INTEGER DEFAULT 0,
    metadata TEXT
)
```

**Indexes:**
- `idx_status_next_run` on (status, next_run) for efficient pending task queries

## Task Lifecycle

### One-Time Tasks (now)
```
Created (pending) → Enqueued → Executed → Completed
```

### Recurring Tasks (hourly, daily, cron)
```
Created (active) → Enqueued → Executed → Next Run Calculated → (repeat)
                                ↓
                            Paused (manual) or Deleted
```

## Testing

### Test Coverage

**Task Manager Tests (`tests/test_task_manager.py`):**
- ✅ Create tasks with all schedule types
- ✅ Validate schedule type and cron expressions
- ✅ List and filter tasks
- ✅ Update task properties
- ✅ Delete tasks
- ✅ Task metadata handling

**API Tests (`tests/test_task_api.py`):**
- ✅ All CRUD operations via REST API
- ✅ Error handling (invalid types, not found, etc.)
- ✅ Query parameter filtering
- ✅ Response validation

**Total:** 17 tests, 100% passing

## Usage Examples

### 1. Immediate Task
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "process urgent data",
    "schedule_type": "now",
    "priority": 10
  }'
```

### 2. Hourly Sync
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "sync database",
    "schedule_type": "hourly",
    "priority": 5
  }'
```

### 3. Daily Backup
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "backup production",
    "schedule_type": "daily",
    "schedule_value": "02:00",
    "priority": 10,
    "metadata": {"critical": true}
  }'
```

### 4. Custom CRON
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "health check",
    "schedule_type": "cron",
    "schedule_value": "*/15 * * * *"
  }'
```

### 5. List Active Tasks
```bash
curl "http://localhost:8000/task?status=active"
```

### 6. Update Task Status
```bash
curl -X PUT http://localhost:8000/task/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

### 7. Delete Task
```bash
curl -X DELETE http://localhost:8000/task/1
```

## Integration Points

### With Existing Systems

1. **JobQueue**: Tasks are enqueued for execution
   - Respects task priority
   - Background processing via JobWorker

2. **Scheduler**: Daemon loop integration
   - Checks for pending tasks every second
   - Automatic execution when due

3. **SQLite Memory**: Consistent storage approach
   - Same pattern as existing job queue
   - Persistent across restarts

## Security

- Token-based authentication (optional)
- Set `GODMAN_API_TOKEN` environment variable
- Mutating endpoints require Bearer token
- Read-only endpoints are public by default

## Files Modified/Created

### Created:
- `godman_ai/scheduler/task_manager.py` (183 lines)
- `tests/test_task_manager.py` (240 lines)
- `tests/test_task_api.py` (370 lines)
- `docs/TASK_SCHEDULING_API.md` (documentation)

### Modified:
- `godman_ai/service/api.py` (added 5 endpoints)
- `godman_ai/service/daemon.py` (integrated task manager)
- `.gitignore` (exclude logs and state databases)

## Future Enhancements

Potential improvements:
- Task retry logic for failed executions
- Task dependencies (run B after A completes)
- Task groups/categories
- Webhook notifications on task completion
- Task execution history/audit log
- Web UI for task management
- Task templates for common patterns

## Documentation

See `docs/TASK_SCHEDULING_API.md` for complete API documentation including:
- Detailed endpoint descriptions
- Request/response examples
- Error handling
- Security configuration
- Integration guide
