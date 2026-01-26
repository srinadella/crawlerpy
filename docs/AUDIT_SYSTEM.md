# Audit System Documentation

## Overview

The audit system provides comprehensive logging and persistence of user actions and application state between sessions. It uses a separate SQLite database (`audit.db`) to track all user activities.

## Architecture

### Database: `audit.db`

Two main tables store audit data:

#### 1. AuditLog Table
Tracks every user action and system event.

**Columns:**
- `id`: Primary key
- `user_id`: User who performed the action (0 for system events)
- `username`: Username for easy reference
- `action`: Type of action (e.g., "crawler_created", "login_success")
- `resource_type`: What was affected (e.g., "crawler", "crawl_job", "user")
- `resource_id`: ID of the affected resource
- `resource_name`: Human-readable name of the resource
- `details`: JSON field with action-specific metadata
- `status`: "success" or "error"
- `error_message`: Error details if status is "error"
- `ip_address`: IP address of the request (if available)
- `created_at`: Timestamp of the action

**Example Actions:**
- `crawler_created` - New crawler configuration created
- `crawler_deleted` - Crawler configuration deleted
- `crawl_job_started` - Crawl job initiated
- `login_success` - User logged in successfully
- `login_failed` - Failed login attempt
- `search_executed` - Search query performed

#### 2. ApplicationState Table
Persists application settings and state between sessions.

**Columns:**
- `id`: Primary key
- `key`: State key (e.g., "theme_preference", "last_search_filter")
- `value`: JSON value
- `updated_at`: Last update timestamp
- `updated_by_id`: User ID who updated this state (0 for system)

## API Endpoints

All audit endpoints require authentication and are prefixed with `/api/audit`.

### GET `/api/audit` (Admin only)
List all audit logs with pagination.

**Query Parameters:**
- `limit`: Number of logs to return (default: 100)
- `offset`: Pagination offset (default: 0)
- `user_id`: Filter by user ID (optional)
- `action`: Filter by action type (optional)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "action": "crawler_created",
      "resource_type": "crawler",
      "resource_id": "5",
      "resource_name": "My Crawler",
      "details": {"seed_urls": ["https://example.com"]},
      "status": "success",
      "error_message": null,
      "ip_address": "127.0.0.1",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

### GET `/api/audit/user/{user_id}`
Get audit logs for a specific user.

**Rules:**
- Users can view their own logs
- Only admins can view other users' logs

### GET `/api/audit/actions/summary` (Admin only)
Get summary statistics of recent actions.

**Response:**
```json
{
  "actions": {
    "crawler_created": 5,
    "login_success": 15,
    "search_executed": 42
  },
  "status": {
    "success": 60,
    "error": 2
  },
  "total_logs": 62
}
```

### GET `/api/audit/state/{key}`
Get stored application state.

**Example:** `GET /api/audit/state/theme_preference`

### POST `/api/audit/state/{key}` (Admin only)
Save application state.

**Request Body:**
```json
{
  "value": "dark"
}
```

## Usage in Code

### Logging an Action

```python
from app.audit import log_action

# Successful action
log_action(
    user_id=current_user.id,
    username=current_user.username,
    action="crawler_created",
    resource_type="crawler",
    resource_id=str(crawler.id),
    resource_name=crawler.name,
    details={
        "seed_urls": crawler.seed_urls,
        "max_depth": crawler.max_depth
    },
    status="success"
)

# Failed action
log_action(
    user_id=current_user.id,
    username=current_user.username,
    action="crawl_job_started",
    resource_type="crawl_job",
    resource_id=str(job_id),
    resource_name="Job for XYZ Crawler",
    details={"config_id": config_id},
    status="error",
    error_message="Crawler is disabled"
)
```

### Retrieving Audit Logs

```python
from app.audit import get_audit_logs

# Get all logs with pagination
logs = get_audit_logs(limit=50, offset=0)

# Filter by user
user_logs = get_audit_logs(user_id=5, limit=50)

# Filter by action
creation_logs = get_audit_logs(action="crawler_created", limit=100)
```

### Managing Application State

```python
from app.audit import save_app_state, get_app_state

# Save state
save_app_state("theme_preference", "dark")

# Get state
theme = get_app_state("theme_preference")  # Returns "dark"

# State persists between server restarts
```

## Integrated Audit Points

The following actions are automatically logged:

### Authentication Routes (`app/routes/auth.py`)
- ✓ `login_success` - Successful login with user roles
- ✓ `login_failed` - Failed login with reason (invalid credentials, inactive account)

### Crawler Routes (`app/routes/crawlers.py`)
- ✓ `crawler_created` - New crawler created with seed URLs and config
- ✓ `crawler_deleted` - Crawler deleted with seed URLs retained in logs
- ⚠️ `crawler_updated` - (Not yet implemented, see "Edit Crawler" section below)

### Job Routes (`app/routes/jobs.py`)
- ✓ `crawl_job_started` - Job initiated with crawler name and config ID
- ⚠️ `crawl_job_stopped` - (Can be added to stop_crawl_job endpoint)
- ⚠️ `crawl_job_completed` - (Can be added to background job completion)

### Search Routes (`app/routes/search.py`)
- ✓ `search_executed` (on error) - Failed search with query and error message

## Future Enhancements

### 1. Search Execution Logging (on success)
Add successful search logging to track popular queries:
```python
log_action(
    user_id=current_user.id,
    username=current_user.username,
    action="search_executed",
    resource_type="search",
    resource_id="",
    details={
        "query": search_query.q,
        "results_count": len(results),
        "content_type": search_query.content_type
    },
    status="success"
)
```

### 2. Edit Crawler Updates
When edit_crawler is implemented:
```python
log_action(
    user_id=current_user.id,
    username=current_user.username,
    action="crawler_updated",
    resource_type="crawler",
    resource_id=str(crawler_id),
    resource_name=crawler.name,
    details={
        "changes": [
            {"field": "max_depth", "old": 3, "new": 5},
            {"field": "enabled", "old": True, "new": False}
        ]
    },
    status="success"
)
```

### 3. Job Completion Logging
In the background job execution:
```python
log_action(
    user_id=job.created_by_id,
    username=job.created_by.username,
    action="crawl_job_completed",
    resource_type="crawl_job",
    resource_id=str(job.id),
    resource_name=f"Job for {crawler.name}",
    details={
        "status": job.status,
        "duration_seconds": (job.completed_at - job.started_at).total_seconds(),
        "urls_crawled": job.urls_crawled,
        "documents_indexed": job.documents_indexed
    },
    status="success" if job.status == "completed" else "error"
)
```

### 4. Admin Dashboard UI
Create a new page to view audit logs, user activity trends, and action history.

## Database Maintenance

### Cleaning Old Logs
```python
from app.audit import get_audit_db
from datetime import datetime, timedelta

db = get_audit_db()
cutoff_date = datetime.utcnow() - timedelta(days=90)
db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
db.commit()
```

### Exporting Logs
Create an admin endpoint to export logs as CSV:
```
GET /api/audit/export?format=csv&start_date=2024-01-01&end_date=2024-12-31
```

## Security Considerations

1. **Access Control**: Audit endpoints require authentication; only admins can view all logs
2. **Sensitive Data**: Passwords are never logged; only non-sensitive details
3. **IP Tracking**: Optional IP address logging for security audit trails
4. **Error Messages**: Error messages are sanitized to avoid exposing system details
5. **Immutability**: Audit logs cannot be deleted by regular users (only by database admin)

## Performance Impact

- Audit logging uses asynchronous database writes in try/except blocks
- Failed audit writes do not interrupt main application requests
- Separate `audit.db` database keeps queries fast and isolated
- Indexes on `user_id`, `action`, and `created_at` for efficient queries

