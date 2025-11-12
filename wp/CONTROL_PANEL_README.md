# Control Panel - Comprehensive Documentation

## Overview

The Control Panel is a modern Single Page Application (SPA) that provides a unified interface for managing Baidu Netdisk automation operations. It features real-time queue monitoring, file browsing, runtime configuration, and multi-account management capabilities.

**Key Features:**
- 📁 File browsing and search across Baidu Netdisk accounts
- 📋 Real-time queue management (transfer and share operations)
- ⚙️ Runtime configuration with live updates
- 📊 Dashboard with aggregate statistics
- 🔐 API key authentication with persistence
- 📱 Responsive design (desktop, tablet, mobile)
- 🔄 Auto-refresh with configurable intervals

## Architecture

### Frontend Architecture

**Technology Stack:**
- Vanilla JavaScript (ES6+)
- HTML5 + CSS3
- No external frameworks or dependencies
- LocalStorage for client-side persistence

**File Structure:**
```
static/control-panel/
├── index.html                 # Main SPA entry point
├── css/
│   └── control-panel.css     # Responsive styles with BEM-like naming
└── js/
    ├── main.js               # Core app logic, EventBus, state management
    ├── browse.js             # File browsing module
    ├── queue.js              # Queue management module
    └── settings.js           # Settings configuration module
```

**State Management:**
- **EventBus Pattern:** Global event system for inter-module communication
- **Shared State:** API key, selected account, auto-refresh interval
- **LocalStorage Keys:**
  - `control_panel_api_key` - API authentication key
  - `control_panel_selected_account` - Last selected account

**Module Lifecycle:**
- Modules initialize only when their tab becomes active
- Auto-refresh timers start/stop based on tab visibility
- Event listeners registered on init, cleaned up on tab switch
- Proper memory management prevents leaks

### Backend Architecture

**Flask Routes:**
```python
# SPA Routes
GET  /control                    # Serve control panel index.html
GET  /control/                   # Alternate route for index
GET  /control/<path:path>        # Serve static assets (CSS/JS)

# API Routes (require X-API-Key authentication)
GET  /api/control/overview       # Dashboard data (health, accounts, queues)
GET  /api/control/queues         # Detailed queue data per account
GET  /api/control/settings       # Load current settings
PUT  /api/control/settings       # Update and apply settings
PATCH /api/control/settings      # Partial settings update
GET  /api/control/browse/<path>  # Browse files in directory
GET  /api/control/search         # Search files by keyword
# ... queue control endpoints (start, pause, stop, clear, export)
```

**Configuration Storage:**
- **Path:** `data/control_panel_settings.json`
- **Format:** JSON with throttle, workers, rate limit, UI preferences
- **Persistence:** Updated on every settings change via PUT/PATCH
- **Initialization:** Created with defaults if missing

**Helper Functions:**
Located in `control_panel_helpers.py`:
- `aggregate_queue_summary()` - Sum queue stats across accounts
- `build_health_status()` - Generate health info
- `build_account_list()` - List accounts with availability
- `aggregate_account_queues()` - Build per-account queue data
- `build_overview_data()` - Assemble complete overview
- `filter_queue_by_status()` - Filter tasks by status
- `count_tasks_by_status()` - Count tasks by status

## UI Layout

### Sidebar Navigation

**Fixed Left Sidebar (Desktop):**
```
┌─────────────────────┐
│  Control Panel      │
├─────────────────────┤
│  [API Key Input]    │
│  [Account Dropdown] │
├─────────────────────┤
│  Dashboard Summary  │
│  • Transfer: 5/2    │
│  • Share: 3/1       │
│  [Refresh Button]   │
├─────────────────────┤
│  📁 Browse          │
│  📋 Queue           │
│  ⚙️ Settings        │
└─────────────────────┘
```

**Horizontal Navigation (Mobile < 768px):**
```
┌──────────────────────────────┐
│ Control Panel  [API] [Acct]  │
├──────────────────────────────┤
│ 📁 Browse | 📋 Queue | ⚙️ Set│
└──────────────────────────────┘
```

### Content Area

**Browse Tab:**
- Directory tree navigation (click folders to expand)
- Breadcrumb navigation (click to go up)
- File list with metadata (name, size, modified date)
- Search bar with real-time filtering
- File details modal (path, size, download URL)

**Queue Tab:**
- Transfer queue table (source, destination, status, progress)
- Share queue table (path, link, password, status)
- Control buttons: Start, Pause, Resume, Stop, Clear
- Export button: Download queue as CSV
- Auto-refresh toggle with interval display
- Status filters: All, Pending, Running, Completed, Failed

**Settings Tab:**
- **Throttle Configuration:**
  - Jitter delays (min/max milliseconds)
  - Operations per window
  - Window duration and rest period
  - Failure handling (max consecutive, pause duration)
  - Cooldown on specific errors
- **Worker Configuration:**
  - Max transfer workers (concurrent threads)
  - Max share workers (concurrent threads)
- **Rate Limiting:**
  - Enable/disable global rate limit toggle
- **UI Preferences:**
  - Auto-refresh interval (milliseconds)
  - API key retention toggle
- Save/Reset buttons with validation

### Dashboard Summary

Located in sidebar (below account selector):
```
┌──────────────────────┐
│  Queue Summary       │
├──────────────────────┤
│  Transfer Queue      │
│  Pending:     5      │
│  Running:     2      │
│  Completed:  10      │
│  Failed:      1      │
├──────────────────────┤
│  Share Queue         │
│  Pending:     3      │
│  Running:     1      │
│  Completed:   8      │
│  Failed:      0      │
├──────────────────────┤
│  [🔄 Refresh]        │
└──────────────────────┘
```

**Features:**
- Aggregates stats from all accounts
- Updates when switching accounts
- Manual refresh button
- Hidden until accounts are loaded

## Usage Walkthrough

### Initial Setup

1. **Start the Server:**
   ```bash
   cd wp
   python3 server.py
   # Or use systemd service:
   sudo systemctl start baidu-pan-server
   ```

2. **Access Control Panel:**
   Open browser and navigate to:
   ```
   http://localhost:5000/control
   ```

3. **Enter API Key:**
   - Locate your API key in server configuration
   - Default dev key: `default_insecure_key`
   - Production: Set `API_SECRET_KEY` in `.env`
   - Enter key in the input field
   - Click "保存" (Save) or press Enter
   - Key is validated against `/api/info` endpoint
   - On success, main content loads

4. **Select Account:**
   - Choose account from dropdown in sidebar
   - Accounts must be configured in `.env`:
     ```env
     ACCOUNT_MAIN_COOKIE=your_bduss_cookie
     ACCOUNT_WP1_COOKIE=another_bduss_cookie
     ```
   - Selected account persists in localStorage

### File Browsing

1. **Navigate Directories:**
   - Click folder names to open
   - Use breadcrumb trail to go back
   - Root directory shows all top-level items

2. **Search Files:**
   - Type search query in search bar
   - Press Enter to execute search
   - Search across filename, path, and metadata
   - Results update in file list

3. **View File Details:**
   - Click file name to open details modal
   - View full path, size, modified date
   - Copy path to clipboard
   - Open download URL (if available)

### Queue Management

1. **View Current Queues:**
   - Switch to Queue tab in sidebar
   - View transfer queue (top table)
   - View share queue (bottom table)
   - Check task status, progress, errors

2. **Control Queue Operations:**
   ```
   ▶️ Start   - Begin processing pending tasks
   ⏸️ Pause   - Pause without clearing state
   ▶️ Resume  - Continue from paused state
   ⏹️ Stop    - Stop and reset queue
   🗑️ Clear   - Remove completed/failed tasks
   📤 Export  - Download queue as CSV
   ```

3. **Auto-Refresh Configuration:**
   - Toggle switch to enable/disable
   - Default interval: 5000ms (5 seconds)
   - Adjust in Settings tab
   - Auto-refresh only active when Queue tab is visible
   - Stops when switching to other tabs

4. **Filter by Status:**
   - Click status badges to filter
   - Available filters: All, Pending, Running, Completed, Failed
   - Multiple filters can be active

### Runtime Configuration

1. **Navigate to Settings Tab:**
   - Click ⚙️ Settings in sidebar
   - Settings load from backend on first visit

2. **Adjust Throttle Settings:**
   ```
   Jitter Min (ms):     500    - Minimum random delay
   Jitter Max (ms):     1500   - Maximum random delay
   Ops Per Window:      50     - Max operations per time window
   Window (sec):        60     - Time window duration
   Rest (sec):          20     - Cooldown after window
   Max Failures:        5      - Consecutive failures before pause
   Pause on Fail (sec): 60     - Pause duration after failures
   Cooldown -62 (sec):  120    - Cooldown for specific error code
   ```

3. **Configure Workers:**
   ```
   Transfer Workers:    1      - Concurrent transfer threads
   Share Workers:       1      - Concurrent share threads
   ```
   
   **Note:** Keep worker counts low (1-2) to avoid detection

4. **UI Preferences:**
   ```
   Auto-Refresh (ms):   5000   - Queue refresh interval
   Retain API Key:      ✓      - Save key in localStorage
   ```

5. **Save Changes:**
   - Click "保存设置" (Save Settings)
   - Settings validated client-side first
   - Sent to backend via PUT request
   - Applied to all active CoreService instances
   - Persisted to `data/control_panel_settings.json`
   - `settingsUpdated` event broadcasts changes
   - Queue module updates auto-refresh interval

6. **Reset to Defaults:**
   - Click "重置为默认值" (Reset to Defaults)
   - Restores factory default settings
   - Must save to apply

## Configuration Files

### Settings JSON Structure

**Location:** `data/control_panel_settings.json`

**Format:**
```json
{
  "throttle": {
    "jitter_ms_min": 500,
    "jitter_ms_max": 1500,
    "ops_per_window": 50,
    "window_sec": 60,
    "window_rest_sec": 20,
    "max_consecutive_failures": 5,
    "pause_sec_on_failure": 60,
    "cooldown_on_errno_-62_sec": 120
  },
  "workers": {
    "max_transfer_workers": 1,
    "max_share_workers": 1
  },
  "rate_limit": {
    "enabled": true
  },
  "ui": {
    "auto_refresh_interval": 5000,
    "api_key_retention": true
  }
}
```

### Environment Variables

**Required in `.env` or `config.py`:**
```env
# API Authentication
API_SECRET_KEY=your_secure_api_key_here

# Account Configuration (BDUSS cookies)
ACCOUNT_MAIN_COOKIE=your_bduss_cookie_value
ACCOUNT_WP1_COOKIE=another_bduss_cookie_value

# Database (optional, defaults to SQLite)
DB_TYPE=sqlite
DB_PATH=data/baidu_pan.db

# Optional: Rate Limiting
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0
```

### Resetting Settings

**Method 1: Delete Settings File**
```bash
cd wp
rm data/control_panel_settings.json
# Restart server - defaults will be created
python3 server.py
```

**Method 2: Use Settings UI**
1. Open Control Panel Settings tab
2. Click "重置为默认值" (Reset to Defaults)
3. Click "保存设置" (Save Settings)

**Method 3: API Call**
```bash
curl -X PUT -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"reset_to_defaults": true}' \
  http://localhost:5000/api/control/settings
```

## API Reference

### Authentication

All control panel API endpoints require authentication via `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key_here" \
  http://localhost:5000/api/control/overview
```

**On Authentication Failure:**
- HTTP 401 Unauthorized
- UI clears stored API key and prompts for re-entry

### Endpoints

#### GET /api/control/overview

**Description:** Consolidated dashboard data including health, accounts, and queue summaries

**Response:**
```json
{
  "success": true,
  "data": {
    "health": {
      "status": "ok",
      "timestamp": "2024-11-12 10:30:00",
      "services": {
        "core": true,
        "crawler": true,
        "link_extractor": true
      }
    },
    "accounts": ["account1", "account2"],
    "queues_summary": {
      "total_accounts": 2,
      "total_transfer_pending": 5,
      "total_transfer_running": 2,
      "total_transfer_completed": 10,
      "total_transfer_failed": 1,
      "total_share_pending": 3,
      "total_share_running": 1,
      "total_share_completed": 8,
      "total_share_failed": 0
    }
  }
}
```

#### GET /api/control/queues

**Description:** Detailed queue data for all accounts

**Query Parameters:**
- `account` (optional) - Filter by specific account

**Response:**
```json
{
  "success": true,
  "queues": {
    "account1": {
      "transfer": {
        "pending": [...],
        "running": [...],
        "completed": [...],
        "failed": [...]
      },
      "share": {
        "pending": [...],
        "running": [...],
        "completed": [...],
        "failed": [...]
      }
    }
  }
}
```

#### GET /api/control/settings

**Description:** Load current control panel settings

**Response:**
```json
{
  "success": true,
  "settings": {
    "throttle": {...},
    "workers": {...},
    "rate_limit": {...},
    "ui": {...}
  },
  "available_accounts": ["account1", "account2"]
}
```

#### PUT /api/control/settings

**Description:** Update control panel settings (full replacement)

**Request Body:**
```json
{
  "throttle": {
    "jitter_ms_min": 500,
    "jitter_ms_max": 1500,
    ...
  },
  "workers": {
    "max_transfer_workers": 1,
    "max_share_workers": 1
  },
  "rate_limit": {
    "enabled": true
  },
  "ui": {
    "auto_refresh_interval": 5000,
    "api_key_retention": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings updated successfully",
  "settings": {...}
}
```

#### PATCH /api/control/settings

**Description:** Partial settings update (merge with existing)

**Request Body:**
```json
{
  "ui": {
    "auto_refresh_interval": 10000
  }
}
```

#### Queue Control Endpoints

```
POST /api/control/queue/start?account=wp1
POST /api/control/queue/pause?account=wp1
POST /api/control/queue/resume?account=wp1
POST /api/control/queue/stop?account=wp1
POST /api/control/queue/clear?account=wp1
GET  /api/control/queue/export?account=wp1&format=csv
```

## Security Considerations

### API Key Protection

**Storage:**
- API key stored in browser localStorage (configurable)
- Not transmitted in URLs (header only)
- Can be disabled via "Retain API Key" toggle

**Best Practices:**
1. Use strong, randomly generated API keys in production
2. Rotate keys regularly
3. Never commit keys to version control
4. Use environment variables for key configuration
5. Consider session-based authentication for multi-user scenarios

**Generating Secure Keys:**
```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)  # Use this in .env as API_SECRET_KEY
```

### Access Control

**Restricting Access:**

1. **Firewall Rules:**
   ```bash
   # Allow only local access
   sudo ufw allow from 127.0.0.1 to any port 5000
   
   # Or specific IP range
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

2. **Nginx Reverse Proxy:**
   ```nginx
   location /control {
       # IP whitelist
       allow 192.168.1.0/24;
       deny all;
       
       # Forward to Flask
       proxy_pass http://localhost:5000;
       proxy_set_header X-API-Key $http_x_api_key;
   }
   ```

3. **HTTPS Only:**
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location /control {
           proxy_pass http://localhost:5000;
       }
   }
   ```

### CORS Configuration

**Backend Config (`server.py`):**
```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-domain.com"],
        "methods": ["GET", "POST", "PUT", "PATCH"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

### Input Validation

**Client-Side:**
- Number ranges validated before submission
- Required fields checked
- Format validation (e.g., positive integers)

**Server-Side:**
- All inputs validated in `settings_manager.py`
- Type checking, range checking
- Sanitization of file paths
- SQL injection prevention (parameterized queries)

### Rate Limiting

**Global Rate Limit:**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-API-Key'),
    default_limits=["100 per hour"]
)
```

### Logging and Monitoring

**Security Events Logged:**
- Failed authentication attempts
- Settings changes (who, when, what)
- Queue operations (start, stop, clear)
- File access patterns

**Log Location:** `logs/app.log`

**Monitor for:**
- Repeated 401 errors (brute force attempts)
- Unusual settings changes
- High-frequency API calls
- Failed queue operations

## Troubleshooting

### Common Issues

**Problem: Can't Access /control**
- **Cause:** Server not running or wrong port
- **Solution:** 
  ```bash
  ps aux | grep server.py  # Check if running
  cd wp && python3 server.py  # Start server
  ```

**Problem: API Key Invalid**
- **Cause:** Mismatch between stored key and server config
- **Solution:**
  ```bash
  # Check server config
  grep API_SECRET_KEY wp/.env
  # Clear browser storage
  localStorage.removeItem('control_panel_api_key')
  # Re-enter correct key in UI
  ```

**Problem: No Accounts Listed**
- **Cause:** Accounts not configured or invalid cookies
- **Solution:**
  ```bash
  # Verify .env has account cookies
  grep ACCOUNT_ wp/.env
  # Check logs for cookie validation errors
  tail -f wp/logs/app.log
  ```

**Problem: Auto-Refresh Not Working**
- **Cause:** Toggle disabled, wrong tab, or JavaScript errors
- **Solution:**
  1. Verify Queue tab is active
  2. Check auto-refresh toggle is ON
  3. Open browser console (F12) for errors
  4. Verify settings `auto_refresh_interval > 0`

**Problem: Settings Won't Save**
- **Cause:** Validation errors or file permissions
- **Solution:**
  ```bash
  # Check file permissions
  ls -la wp/data/control_panel_settings.json
  chmod 644 wp/data/control_panel_settings.json
  
  # Check validation in browser console
  # Ensure all values are within allowed ranges
  ```

**Problem: Queue Operations Fail**
- **Cause:** CoreService not initialized or adapter errors
- **Solution:**
  ```bash
  # Check service status
  curl -H "X-API-Key: your_key" http://localhost:5000/api/health
  
  # Check account cookie validity
  # Verify adapter logs in app.log
  tail -f wp/logs/app.log | grep -i error
  ```

**Problem: Responsive Layout Broken**
- **Cause:** CSS not loaded or browser cache
- **Solution:**
  1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
  2. Check Network tab in DevTools for CSS 404s
  3. Verify `static/control-panel/css/` exists
  4. Clear browser cache

### Debug Mode

**Enable Detailed Logging:**

1. Edit `logger.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Restart server:
   ```bash
   cd wp
   python3 server.py
   ```

3. Watch logs:
   ```bash
   tail -f wp/logs/app.log
   ```

**Browser DevTools:**

1. Open Console (F12 → Console)
2. Check for JavaScript errors
3. Review Network tab for failed requests
4. Inspect Application tab for localStorage

**API Testing:**

```bash
# Test authentication
curl -v -H "X-API-Key: your_key" http://localhost:5000/api/info

# Test overview endpoint
curl -H "X-API-Key: your_key" http://localhost:5000/api/control/overview | jq

# Test settings load
curl -H "X-API-Key: your_key" http://localhost:5000/api/control/settings | jq
```

## Performance Optimization

### Frontend Optimization

**Lazy Loading:**
- Tab content loads only when visible
- Modules initialize on-demand
- Timers start/stop based on visibility

**Memory Management:**
- Event listeners properly cleaned up
- Timers cleared when switching tabs
- DOM elements reused where possible

**Caching:**
- Account list cached after first load
- Settings cached until explicit save
- Dashboard summary cached with manual refresh

### Backend Optimization

**Database:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_transfers_status ON transfers(status);
CREATE INDEX idx_shares_status ON shares(status);
CREATE INDEX idx_transfers_account ON transfers(account);
```

**Caching:**
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1'
})

@app.route('/api/control/overview')
@cache.cached(timeout=10)  # Cache for 10 seconds
def overview():
    # ...
```

**Async Operations:**
- Queue operations run in background threads
- File browsing uses async I/O
- Bulk operations batched to reduce API calls

### Monitoring

**Performance Metrics:**
```python
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    if duration > 1.0:  # Log slow requests
        app.logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
    return response
```

## Browser Compatibility

**Supported Browsers:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

**Required Features:**
- ES6+ JavaScript (classes, arrow functions, async/await)
- Fetch API
- LocalStorage
- CSS Grid and Flexbox
- CSS Custom Properties (variables)

**Graceful Degradation:**
- Clipboard API falls back to execCommand
- Modern date inputs fall back to text inputs
- CSS Grid falls back to Flexbox

## Testing

### Manual Testing Checklist

**Initial Setup:**
- [ ] /control URL loads successfully
- [ ] API key prompt displays
- [ ] Invalid key shows error message
- [ ] Valid key loads main interface
- [ ] Account dropdown populates

**Browse Tab:**
- [ ] Root directory loads
- [ ] Folders are clickable
- [ ] Breadcrumb navigation works
- [ ] Search returns results
- [ ] File details modal opens
- [ ] Copy path button works

**Queue Tab:**
- [ ] Transfer queue displays
- [ ] Share queue displays
- [ ] Control buttons respond
- [ ] Auto-refresh toggles on/off
- [ ] Export downloads CSV
- [ ] Status filters work

**Settings Tab:**
- [ ] Settings load from backend
- [ ] Form inputs update
- [ ] Validation prevents invalid values
- [ ] Save button persists changes
- [ ] Reset button restores defaults
- [ ] settingsUpdated event fires

**Dashboard:**
- [ ] Summary shows aggregate stats
- [ ] Refresh button updates data
- [ ] Stats change when switching accounts

**Responsive Design:**
- [ ] Desktop layout (> 1200px) correct
- [ ] Tablet layout (768px - 1200px) correct
- [ ] Mobile layout (< 768px) correct
- [ ] Sidebar collapses to horizontal nav
- [ ] Touch interactions work on mobile

### Automated Tests

**Unit Tests (pytest):**
```bash
cd wp
./run_unit_tests.sh

# Or directly:
pytest tests/unit/ -v

# Specific test files:
pytest tests/unit/test_settings_manager.py -v
pytest tests/unit/test_control_panel_helpers.py -v
pytest tests/unit/test_core_service_throttle.py -v
```

**Integration Tests:**
```bash
cd wp
pytest tests/integration/ -v

# Specific test:
pytest tests/integration/test_backend_endpoints.py -v
```

**Coverage:**
- Unit tests: 76 tests covering settings, throttle, helpers
- Integration tests: 38 tests covering backend endpoints
- Total: 114 tests

**Test Structure:**
```
tests/
├── unit/
│   ├── test_settings_manager.py        # Settings persistence
│   ├── test_core_service_throttle.py   # Throttle updates
│   └── test_control_panel_helpers.py   # Helper functions
└── integration/
    ├── conftest.py                     # Fixtures (FakeCoreService)
    └── test_backend_endpoints.py       # API endpoint tests
```

## Deployment

See [DEPLOYMENT_README.md](../DEPLOYMENT_README.md) for comprehensive deployment instructions.

**Quick Deployment:**
```bash
cd wp

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 3. Initialize database
python3 init_db.py

# 4. Start server
python3 server.py

# 5. Access control panel
# http://localhost:5000/control
```

**Production Deployment:**

See [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) for full checklist.

Key steps:
1. Configure secure API key
2. Set up HTTPS with Nginx
3. Use production WSGI server (Gunicorn/Waitress)
4. Configure systemd service
5. Set up database backups
6. Configure log rotation
7. Set up monitoring

## Related Documentation

- **[CONTROL_PANEL_QUICKSTART.md](CONTROL_PANEL_QUICKSTART.md)** - Quick start guide for operators
- **[CONTROL_PANEL_SPA_COMPLETE.md](CONTROL_PANEL_SPA_COMPLETE.md)** - Implementation details
- **[KNOWLEDGE_UI_README.md](KNOWLEDGE_UI_README.md)** - Knowledge base UI (separate from control panel)
- **[DEPLOYMENT_README.md](../DEPLOYMENT_README.md)** - Deployment guide
- **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Test strategy and commands
- **[settings_manager.py](settings_manager.py)** - Settings persistence implementation
- **[control_panel_helpers.py](control_panel_helpers.py)** - Backend helper functions

## Differences from Knowledge UI

The Control Panel and Knowledge UI are **separate interfaces** serving different purposes:

| Feature | Control Panel (`/control`) | Knowledge UI (`/kb`) |
|---------|---------------------------|----------------------|
| **Purpose** | Manage Baidu Netdisk operations | Browse/search knowledge base entries |
| **Operations** | File browse, queue control, settings | Article/link search, filter, export |
| **Data Source** | Live Baidu Netdisk API + queues | SQLite database (articles, links) |
| **Authentication** | API key in header | API key in header |
| **Real-time** | Yes (auto-refresh queues) | No (static data queries) |
| **Target Users** | System operators | Content researchers |

**When to use Control Panel:**
- Monitor transfer/share queue status
- Browse files in Baidu Netdisk
- Adjust throttle and worker settings
- Troubleshoot queue failures

**When to use Knowledge UI:**
- Search crawled articles
- Export link data as CSV
- Filter by status or tags
- Review extraction results

## Changelog

### v1.0.0 (2024-11-12)
- Initial release
- Multi-tab SPA (Browse, Queue, Settings)
- EventBus state management
- Dashboard summary
- Auto-refresh with configurable intervals
- Settings persistence
- Responsive design
- API key authentication

## License

This project follows the same license as the main wp1 project.

## Support

For issues, questions, or contributions:
1. Check browser console for errors (F12 → Console)
2. Review server logs: `logs/app.log`
3. Run tests: `./run_unit_tests.sh` and `pytest tests/integration/ -v`
4. Consult related documentation (see links above)
