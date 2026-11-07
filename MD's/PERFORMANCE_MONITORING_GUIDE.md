# System Performance Monitoring — Developer Feature

## Overview
The live results dashboard now includes **comprehensive system performance metrics** to help developers monitor the health and responsiveness of the voting system in real-time.

## Performance Metrics

### 1. **Server Status**
- Indicates whether the backend is online or offline
- Shows a pulsing indicator (green = online, red = offline)
- Updates with each API call
- Color-coded badge showing "Healthy" or "Error"

### 2. **API Response Time**
- Measures the time it takes for the server to respond to requests
- Shows the most recent response time in milliseconds
- Automatically colored:
  - **Green (Good):** <500ms
  - **Yellow (Fair):** 500-1000ms
  - **Red (Slow):** >1000ms

### 3. **Data Sync**
- Shows how long ago data was last synchronized from the server
- Helps identify if data is stale or delayed
- Automatically colored:
  - **Green (Synced):** Updated within last 10 seconds
  - **Yellow (Delayed):** More than 10 seconds since last update

### 4. **Uptime**
- Tracks how long your current session has been active
- Displayed in minutes (m) and hours (h)
- Resets when you log out or refresh the page
- Shows "1h 23m" format for sessions longer than an hour

### 5. **Memory Usage**
- Estimated memory consumption based on request history
- Shows in megabytes (MB)
- Automatically colored:
  - **Green (Normal):** <50MB
  - **Yellow (Moderate):** 50-100MB
  - **Red (High):** >100MB
- Calculated from API response tracking and error count

### 6. **Failed Requests**
- Count of API requests that failed
- Indicates network or server issues
- Automatically colored:
  - **Green (None):** 0 failed requests
  - **Yellow (Warnings):** 1-5 failed requests
  - **Red (Critical):** >5 failed requests

## Example Display
```
⚙️ SYSTEM PERFORMANCE

Server Status: ● Online [Healthy]
API Response: 245ms [Good]
Data Sync: 2s ago [Synced]
Uptime: 15m [Active]
Memory Usage: 12.5MB [Normal]
Failed Requests: 0 [None]
```

## What Each Color Means

### Green (✓ Healthy)
- System is operating normally
- No immediate attention needed
- Everything is functioning as expected

### Yellow (⚠️ Warning)
- Minor issues detected
- May indicate slowing performance or delayed updates
- Monitor for further degradation

### Red (🔴 Critical)
- System has serious problems
- Requires immediate attention
- May affect voting functionality

## Developer Insights
- **High API Response Time?** May indicate server overload or network issues
- **Frequent Failed Requests?** Check server logs or network connectivity
- **Memory Growing?** Page might have a memory leak; try refreshing
- **Data Not Syncing?** Check if backend is still running (`python app.py`)
- **Status Offline?** Verify Flask server is running on port 3000

## Real-Time Updates
All metrics update automatically every 1 second while logged in.

## Troubleshooting Guide

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| API Response > 1000ms | Server overload | Scale up server or reduce load |
| Failed Requests increasing | Network issue | Check internet connection |
| Data Sync > 10s | Auto-refresh paused | Click "Resume" or refresh page |
| Memory > 100MB | Memory leak | Refresh the browser tab |
| Status = Offline | Backend down | Restart Flask: `python app.py` |

## Notes for Election Day
- Monitor API response time during peak voting periods
- Watch for failed requests that might indicate technical issues
- High VPS (votes per second) combined with fast API response = healthy system
- If any metric turns red, notify your system administrator
