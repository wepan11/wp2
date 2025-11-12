# Control Panel Browse UI

A web-based interface for browsing and managing Baidu Netdisk files through the control panel.

## Overview

The Control Panel provides a user-friendly interface to:
- Browse Baidu Netdisk directories
- Search for files
- View file metadata
- Navigate using breadcrumbs
- Manage multiple accounts

## Files Structure

```
static/control-panel/
├── index.html              # Main HTML layout
├── css/
│   └── control-panel.css   # Styles for all components
├── js/
│   ├── main.js            # Core app logic and API management
│   └── browse.js          # File browsing functionality
└── README.md              # This file
```

## Features

### API Key Management
- Secure storage in browser localStorage
- Automatic validation against backend
- Persistent sessions across page reloads

### Account Selection
- Dynamic loading of available accounts from `/api/info`
- Account switcher in sidebar
- Account-specific file browsing

### File Browsing
- List directory contents via `/api/files/list`
- Click folders to navigate
- Breadcrumb navigation for easy path traversal
- File metadata display in detail drawer

### File Search
- Real-time search with debouncing
- Search within current path or globally
- Results displayed with full metadata
- Clear search to return to directory view

### UI States
- **Loading**: Spinner animation during API calls
- **Error**: User-friendly error messages with retry option
- **Empty**: Contextual empty state messages
- **Success**: File list with grid layout

### Responsive Design
- Mobile-friendly layout
- Adaptive sidebar navigation
- Touch-optimized controls

## Usage

### Direct Access
```
http://localhost:5000/static/control-panel/index.html
```

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/info` | GET | Get available accounts |
| `/api/files/list` | GET | List directory contents |
| `/api/files/search` | GET | Search for files |

### Required Headers
- `X-API-Key`: Your API authentication key

### Query Parameters

**List Files:**
```
GET /api/files/list?path=/my/folder&account=account1
```

**Search Files:**
```
GET /api/files/search?keyword=document&path=/&account=account1
```

## Architecture

### main.js - Core Application
- **ControlPanel Class**: Main application controller
  - API key management
  - Account loading and selection
  - Tab switching
  - Authentication flow
  
- **EventBus Class**: Simple pub/sub system
  - `accountsLoaded`: When accounts are fetched
  - `accountChanged`: When user selects different account
  - `tabChanged`: When user switches tabs

### browse.js - Browse Module
- **BrowseModule Class**: File browsing logic
  - Directory navigation
  - File listing and rendering
  - Search functionality with debouncing
  - Breadcrumb rendering
  - File detail drawer
  - State management (loading/error/empty)

### CSS Architecture
- CSS custom properties for theming
- BEM-like naming conventions
- Modular component styles
- Responsive breakpoints
- Smooth animations and transitions

## Extending

### Adding New Tabs
1. Add nav item in `index.html`:
```html
<li>
    <a href="#" class="nav-item" data-tab="newtab">
        🆕 New Tab
    </a>
</li>
```

2. Add tab view section:
```html
<section id="newtabView" class="tab-view">
    <div class="view-header">
        <h2>New Tab</h2>
    </div>
    <!-- Content here -->
</section>
```

3. Listen to tab changes in your module:
```javascript
window.controlPanel.eventBus.on('tabChanged', (tab) => {
    if (tab === 'newtab') {
        // Initialize your tab
    }
});
```

### Custom File Actions
Extend `browse.js` to add custom actions in the file detail drawer:

```javascript
document.getElementById('myCustomBtn').addEventListener('click', () => {
    if (this.selectedFile) {
        // Custom action logic
    }
});
```

## Development

### Testing Locally
1. Start the backend server:
```bash
cd wp
python3 server.py
```

2. Open in browser:
```
http://localhost:5000/static/control-panel/index.html
```

3. Enter your API key (configured in backend)

### Debugging
- Open browser DevTools (F12)
- Check Console for errors
- Monitor Network tab for API calls
- Use localStorage inspector to check stored keys

### Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers with modern JavaScript support

## Future Enhancements

The following sections are currently placeholders:

### Queue Management (Planned)
- View transfer queue
- View share queue
- Add/remove items from queues
- Queue status monitoring

### Settings (Planned)
- Account management
- API key management
- Display preferences
- Batch operation settings

## Troubleshooting

### API Key Invalid
- Check that your key matches the backend configuration
- Verify backend is running
- Check browser console for 401 errors

### Files Not Loading
- Ensure account is selected
- Check that account has active session in backend
- Verify network connectivity to backend
- Check browser console for errors

### Search Not Working
- Ensure keyword is not empty
- Check that backend search endpoint is available
- Verify account has proper permissions

## License

Part of the Baidu Netdisk Automation project.
