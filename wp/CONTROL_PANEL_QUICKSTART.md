# Control Panel - Quick Start Guide

## Accessing the Control Panel

```
URL: http://localhost:5000/control
```

## First Time Setup

1. **Enter API Key**
   - Get API key from server configuration (`API_SECRET_KEY` in config)
   - Default development key: `default_insecure_key`
   - Enter key and click "保存" (Save)

2. **Select Account**
   - Choose account from dropdown in sidebar
   - Accounts must be configured in server `.env` file

## Navigation

### Browse Tab 📁
- **View files:** Click folders to navigate
- **Search:** Type in search bar and press Enter
- **File details:** Click file to view metadata
- **Copy path:** Open file details, click "复制路径"

### Queue Tab 📋
- **View queues:** See transfer and share task lists
- **Control:**
  - ▶️ Start - Begin processing queue
  - ⏸️ Pause - Pause without clearing
  - ▶️ Resume - Continue paused queue
  - ⏹️ Stop - Stop and reset
  - 🗑️ Clear - Remove all completed/failed
  - 📤 Export - Download as CSV
- **Auto-refresh:** Toggle on/off (default 5s interval)

### Settings Tab ⚙️
- **Throttle:** API rate limiting settings
- **Workers:** Concurrent thread counts
- **Rate Limit:** Global rate limit toggle
- **UI Prefs:** Auto-refresh interval, API key retention
- Click "保存设置" (Save Settings) to apply

## Dashboard Summary

Located in sidebar below account selector:
- Shows aggregate queue statistics
- Click 🔄 Refresh to update manually
- Auto-updates when switching accounts

## Keyboard Tips

- `Enter` in search box - Execute search
- `Enter` in API key input - Save key
- Tab navigation - Use mouse for now

## Troubleshooting

**Problem:** Can't access /control
- **Solution:** Ensure server is running: `python3 server.py`

**Problem:** API key invalid
- **Solution:** Check `.env` file for `API_SECRET_KEY` value

**Problem:** No accounts shown
- **Solution:** Configure accounts in `.env`:
  ```
  ACCOUNT_MAIN_COOKIE=your_cookie_here
  ```

**Problem:** Auto-refresh not working
- **Solution:** 
  1. Check toggle is ON in Queue tab
  2. Verify tab is active (not hidden)
  3. Check browser console for errors

**Problem:** Settings won't save
- **Solution:**
  1. Validate all inputs are within allowed ranges
  2. Check `data/control_panel_settings.json` is writable
  3. Verify API key is valid

## Configuration Files

- **Server Config:** `config.py` or `.env`
- **Settings Storage:** `data/control_panel_settings.json`
- **Logs:** `logs/app.log`

## API Endpoints

All endpoints require `X-API-Key` header:

```bash
# Get overview
curl -H "X-API-Key: your_key" http://localhost:5000/api/control/overview

# Get queues
curl -H "X-API-Key: your_key" http://localhost:5000/api/control/queues

# Get settings
curl -H "X-API-Key: your_key" http://localhost:5000/api/control/settings

# Update settings
curl -X PUT -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"throttle":{"jitter_ms_min":500},...}' \
  http://localhost:5000/api/control/settings
```

## Default Settings

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
  "ui": {
    "auto_refresh_interval": 5000,
    "api_key_retention": true
  }
}
```

## Best Practices

1. **Monitor Queues:** Check Queue tab regularly for failures
2. **Adjust Throttle:** If seeing rate limit errors, increase delays
3. **Worker Count:** Keep low (1-2) to avoid detection
4. **Auto-Refresh:** Balance between freshness and server load
5. **Backup Settings:** Save `data/control_panel_settings.json` before major changes

## Mobile Access

The control panel is responsive:
- Sidebar becomes horizontal nav
- Forms stack vertically
- Tables scroll horizontally
- Touch-friendly buttons

Recommended mobile browsers:
- Safari (iOS)
- Chrome (Android)

## Integration with Other Features

**Knowledge Base:** Access at `/kb` for document management

**API Documentation:** Access at `/docs` for Swagger UI

**Health Check:** Access at `/api/health` for server status

## Support

For issues or questions:
1. Check browser console for errors (F12 → Console)
2. Check server logs: `logs/app.log`
3. Run tests: `python3 test_control_panel_integration.py`
4. Review `CONTROL_PANEL_SPA_COMPLETE.md` for detailed docs
