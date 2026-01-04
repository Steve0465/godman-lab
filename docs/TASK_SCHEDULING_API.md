# Task Scheduling API Documentation

## Overview

The Task Scheduling API provides endpoints for creating, managing, and executing scheduled tasks. Tasks can be executed immediately or scheduled to run at specific intervals (hourly, daily, or using CRON expressions).

## Endpoints

### POST /task

Create a new scheduled task.

**Request Body:**
```json
{
  "task_input": "string (required) - The task command or input to execute",
  "schedule_type": "string (required) - One of: 'now', 'hourly', 'daily', 'cron'",
  "schedule_value": "string (optional) - Schedule-specific value (e.g., '14:30' for daily, cron expression for cron)",
  "priority": "integer (optional, default: 1) - Task priority (higher = more important)",
  "metadata": "object (optional) - Additional metadata for the task"
}
```

**Schedule Types:**

- **now**: Execute immediately (one-time)
- **hourly**: Run at the top of every hour
- **daily**: Run daily at a specific time
  - `schedule_value`: Time in "HH:MM" format (e.g., "14:30" for 2:30 PM)
  - If not provided, defaults to midnight (00:00)
- **cron**: Run based on a CRON expression
  - `schedule_value`: Standard 5-field CRON expression (e.g., "*/15 * * * *" for every 15 minutes)

**Response:**
```json
{
  "success": true,
  "task_id": 1,
  "task": {
    "id": 1,
    "task_input": "Process receipts",
    "schedule_type": "daily",
    "schedule_value": "14:30",
    "status": "active",
    "priority": 5,
    "created_at": "2026-01-04T04:51:03.450289",
    "updated_at": null,
    "last_run": null,
    "next_run": "2026-01-04T14:30:00",
    "run_count": 0,
    "metadata": null
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "Backup database",
    "schedule_type": "daily",
    "schedule_value": "02:00",
    "priority": 10
  }'
```

---

### GET /task

List all scheduled tasks with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status ('pending', 'active', 'paused', 'completed', 'failed')
- `schedule_type` (optional): Filter by schedule type ('now', 'hourly', 'daily', 'cron')
- `limit` (optional, default: 100): Maximum number of tasks to return
- `offset` (optional, default: 0): Offset for pagination

**Response:**
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "task_input": "Sync data",
      "schedule_type": "hourly",
      "status": "active",
      ...
    }
  ],
  "count": 1
}
```

**Example:**
```bash
# List all tasks
curl http://localhost:8000/task

# List only active hourly tasks
curl "http://localhost:8000/task?schedule_type=hourly&status=active"
```

---

### GET /task/{task_id}

Get details of a specific task.

**Path Parameters:**
- `task_id` (required): The task ID

**Response:**
```json
{
  "success": true,
  "task": {
    "id": 1,
    "task_input": "Process data",
    "schedule_type": "hourly",
    "schedule_value": null,
    "status": "active",
    "priority": 3,
    "created_at": "2026-01-04T04:51:03.450289",
    "updated_at": null,
    "last_run": null,
    "next_run": "2026-01-04T05:00:00",
    "run_count": 0,
    "metadata": null
  }
}
```

**Example:**
```bash
curl http://localhost:8000/task/1
```

---

### PUT /task/{task_id}

Update a scheduled task.

**Path Parameters:**
- `task_id` (required): The task ID

**Request Body:**
```json
{
  "schedule_type": "string (optional) - New schedule type",
  "schedule_value": "string (optional) - New schedule value",
  "priority": "integer (optional) - New priority",
  "status": "string (optional) - New status ('active', 'paused', etc.)",
  "metadata": "object (optional) - New metadata"
}
```

**Response:**
```json
{
  "success": true,
  "task": {
    "id": 1,
    ...
  }
}
```

**Example:**
```bash
# Pause a task
curl -X PUT http://localhost:8000/task/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'

# Change priority
curl -X PUT http://localhost:8000/task/1 \
  -H "Content-Type: application/json" \
  -d '{"priority": 15}'
```

---

### DELETE /task/{task_id}

Delete/cancel a scheduled task.

**Path Parameters:**
- `task_id` (required): The task ID

**Response:**
```json
{
  "success": true,
  "message": "Task 1 deleted"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/task/1
```

---

## Task Status Values

- **pending**: Task is created but not yet active
- **active**: Task is scheduled and will run according to schedule
- **paused**: Task is temporarily disabled
- **completed**: One-time task that has been executed
- **failed**: Task execution failed

## Task Lifecycle

### One-Time Tasks (schedule_type: "now")
1. Created with status: `pending`
2. Immediately enqueued to job queue
3. Status updated to: `completed` (or `failed` on error)

### Recurring Tasks (schedule_type: "hourly", "daily", "cron")
1. Created with status: `active`
2. `next_run` calculated based on schedule
3. When time matches `next_run`:
   - Task enqueued to job queue
   - `last_run` updated to current time
   - `run_count` incremented
   - New `next_run` calculated
4. Process repeats until task is paused or deleted

## Integration with Daemon

The task scheduler is integrated with the GodmanAI daemon. When the daemon is running, it automatically:

1. Checks for pending tasks every second
2. Enqueues tasks that are due for execution
3. Updates task metadata (last_run, next_run, run_count)

To start the daemon:
```bash
python -m godman_ai.service.daemon start
```

## Examples

### Daily Backup at 2 AM
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "backup --database=production --target=s3",
    "schedule_type": "daily",
    "schedule_value": "02:00",
    "priority": 10,
    "metadata": {"category": "backup", "critical": true}
  }'
```

### Hourly Data Sync
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "sync --source=api --destination=database",
    "schedule_type": "hourly",
    "priority": 5
  }'
```

### Custom CRON Schedule (Every 15 minutes)
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "health_check --services=all",
    "schedule_type": "cron",
    "schedule_value": "*/15 * * * *",
    "priority": 3
  }'
```

### Immediate Execution
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_input": "process_receipts --urgent",
    "schedule_type": "now",
    "priority": 15
  }'
```

## Error Handling

### Invalid Schedule Type
**Request:**
```json
{
  "task_input": "test",
  "schedule_type": "invalid"
}
```

**Response (400):**
```json
{
  "detail": "Invalid schedule type. Must be one of: ['now', 'hourly', 'daily', 'cron']"
}
```

### Invalid CRON Expression
**Request:**
```json
{
  "task_input": "test",
  "schedule_type": "cron",
  "schedule_value": "invalid cron"
}
```

**Response (400):**
```json
{
  "detail": "Invalid cron expression: invalid cron"
}
```

### Task Not Found
**Request:**
```
GET /task/999
```

**Response (404):**
```json
{
  "detail": "Task 999 not found"
}
```

## Storage

Tasks are persisted in an SQLite database at `.godman/state/tasks.db`. This ensures tasks survive server restarts.

## Security

For production deployments, set the `GODMAN_API_TOKEN` environment variable to require authentication for mutating endpoints (POST, PUT, DELETE).

```bash
export GODMAN_API_TOKEN="your-secret-token"
```

Then include the token in requests:
```bash
curl -X POST http://localhost:8000/task \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"task_input": "...", "schedule_type": "hourly"}'
```
