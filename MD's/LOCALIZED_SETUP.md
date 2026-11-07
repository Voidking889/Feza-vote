# 🗳️ Localized Voting System Setup Guide

## Overview

The Feza Voting System is now **completely localized** and works offline without any internet connection. All computers on the same network can participate in voting with all data stored locally on the server machine.

## ✨ Key Features

- ✅ **Completely Offline** - No internet required, works in any environment
- ✅ **Network Accessible** - Any computer on the LAN can access and vote
- ✅ **Local SQLite Database** - All data stored securely on server
- ✅ **Persistent Storage** - Data survives server restarts
- ✅ **Real-time Results** - Live vote updates across all connected devices
- ✅ **Easy Installation** - One-command setup on any computer

## System Architecture

### Components

1. **Server Machine** (Windows/macOS/Linux)
   - Runs the Flask application
   - Hosts SQLite database
   - Provides LAN access to all clients

2. **Client Machines** (Any computer on network)
   - Accesses server via web browser
   - No installation needed
   - Real-time voting and results

3. **Local Database**
   - SQLite database (`voting_system.db`)
   - Stores candidates, votes, and tokens
   - No cloud sync, completely local

## Installation Guide

### Option 1: Windows

#### Step 1: Install Python (First Time Only)
1. Download Python 3.7+ from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check ✓ "Add Python to PATH"
4. Click "Install Now"

#### Step 2: Run Installation Script
1. Navigate to the feza-vote folder
2. Double-click `install.bat`
3. Wait for installation to complete

#### Step 3: Start the Server
1. Double-click `start_server.bat`
2. You should see:
   ```
   [VOTING SYSTEM] Localized Offline Voting System v2.0
   [ACCESS]
     Local Machine:    http://localhost:3000
     Network (LAN):    http://[YOUR-SERVER-IP]:3000
   ```

### Option 2: macOS/Linux

#### Step 1: Install Python (if not already installed)
```bash
# macOS (Homebrew)
brew install python3

# Ubuntu/Debian
sudo apt-get install python3-pip
```

#### Step 2: Run Installation Script
```bash
cd feza-vote
bash install.sh
```

#### Step 3: Start the Server
```bash
bash start_server.sh
```

## Finding Your Server IP Address

### Windows
1. Open Command Prompt
2. Type: `ipconfig`
3. Look for "IPv4 Address" under your network adapter (e.g., 192.168.1.100)

### macOS/Linux
```bash
ifconfig
```
Look for "inet" address on your network adapter (usually 192.168.x.x)

## Accessing the System

### From the Server Machine
- **Voting Page**: http://localhost:3000
- **Registration**: http://localhost:3000/register.html
- **Results**: http://localhost:3000/ (scroll down)

### From Other Computers on Network
Replace `[SERVER-IP]` with the server's IP address found above:

- **Voting Page**: http://[SERVER-IP]:3000
- **Registration**: http://[SERVER-IP]:3000/register.html
- **Results**: http://[SERVER-IP]:3000/

Example: `http://electionpoll.com:3000`

## System API Endpoints

All computers can access these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/candidates` | GET | List all candidates |
| `/api/vote` | POST | Submit a vote |
| `/api/results` | GET | Get current results |
| `/api/check-token/<token>` | GET | Check token status |
| `/api/system-info` | GET | Server information & stats |
| `/api/export-data` | GET | Export all data as JSON |
| `/api/reset` | POST | Reset all votes (admin) |

## Database Structure

The system uses **SQLite** with these tables:

### `candidates`
```
- id: Unique candidate ID
- name: Candidate name
- position: 'president' or 'vice_president'
- votes: Vote count
- image: Base64 encoded image
- slogan: Candidate slogan
- student_id: Unique student identifier
- registration_date: When registered
```

### `votes`
```
- id: Vote record ID
- token: Voter token
- candidate_id: Candidate voted for
- position: Position voted for
- timestamp: Vote timestamp
```

### `valid_tokens`
```
- token: Unique voter token
- is_spent: Whether token used for both positions
- created_date: When token created
```

## File Structure

```
feza-vote/
├── app_local.py                    # Main Flask app (SQLite version)
├── install.bat                     # Windows installation script
├── install.sh                      # macOS/Linux installation script
├── start_server.bat                # Windows server launcher
├── start_server.sh                 # macOS/Linux server launcher
├── voting_system.db                # SQLite database (created on first run)
├── requirements.txt                # Python dependencies
├── README.md                       # Original README
├── LOCALIZED_SETUP.md              # This file
└── public/                         # Frontend files
    ├── index.html
    ├── register.html
    ├── script.js
    ├── styles.css
    ├── voters_tokens.txt           # Token file (loaded at startup)
    └── ...
```

## First-Time Setup Checklist

- [ ] Install Python on server machine
- [ ] Run `install.bat` (Windows) or `install.sh` (macOS/Linux)
- [ ] Run `start_server.bat` or `start_server.sh`
- [ ] Note the server IP address shown in console
- [ ] Test access from server: http://localhost:3000
- [ ] Test access from another computer: http://[SERVER-IP]:3000
- [ ] Add candidates via registration page
- [ ] Create voter tokens in `public/voters_tokens.txt` if needed
- [ ] Start voting!

## Troubleshooting

### "Python not found" or "Python not in PATH"
- **Windows**: Reinstall Python and check "Add Python to PATH"
- **macOS/Linux**: Install Python 3 using package manager

### "Can't connect from other computers"
1. Check server IP address with `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Use correct address in URL (e.g., http://electionpoll.com:3000)
3. Ensure both computers are on same network
4. Check if firewall blocks port 3000

### "Database is locked"
- Close server and restart it
- Ensure only one instance of `app_local.py` is running

### "Port 3000 already in use"
Change the port when starting:
```bash
# Windows
set PORT=3001 && python app_local.py

# macOS/Linux
PORT=3001 python app_local.py
```

## Admin Functions

### Reset All Votes
```bash
# Send POST request to reset endpoint
curl -X POST http://[SERVER-IP]:3000/api/reset
```

### Export Data
Access in browser:
```
http://[SERVER-IP]:3000/api/export-data
```

### View System Info
```
http://[SERVER-IP]:3000/api/system-info
```

## Security Notes

- **Firewall**: Only allows connections from network (port 3000)
- **Tokens**: Load from `voters_tokens.txt` on startup
- **Database**: SQLite file stored locally (`voting_system.db`)
- **Network**: Runs on all interfaces (0.0.0.0) for LAN access

## Performance

- Tested with 500+ voters
- Database automatically optimized for local access
- Real-time synchronization across all clients
- Minimal memory footprint (~50MB)

## Backup & Recovery

### Backup Data
```bash
# Copy the database file
cp voting_system.db voting_system_backup.db
```

### Restore Data
```bash
# Replace the database file
cp voting_system_backup.db voting_system.db
```

### Export to JSON
Access: `http://[SERVER-IP]:3000/api/export-data`

This exports all candidates, votes, and statistics.

## Running Multiple Instances

If you need multiple voting sessions:

1. Create separate folders for each session
2. Run each on different ports:
   ```bash
   PORT=3000 python app_local.py    # Session 1
   PORT=3001 python app_local.py    # Session 2
   ```

## Network Diagram

```
┌─────────────────────────────────────────────────────┐
│            Local Network (No Internet Needed)       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────┐   ┌──────────────────┐  │
│  │  SERVER (Windows/Mac)│   │   Client PC 1    │  │
│  │ ┌────────────────────┤   ├──────────────────┤  │
│  │ │ Flask App Port 3000│◄──┤ Browser :3000   │  │
│  │ │ SQLite Database    │   └──────────────────┘  │
│  │ └────────────────────┤                         │
│  └──────────────────────┘   ┌──────────────────┐  │
│           ▲                 │   Client PC 2    │  │
│           └─────────────────┤ Browser :3000   │  │
│           ▲                 └──────────────────┘  │
│           │                                       │
│  ┌────────┴─────────┐      ┌──────────────────┐  │
│  │  Voter Tokens    │      │  Client PC 3     │  │
│  │  Candidates      │◄─────┤ Browser :3000   │  │
│  │  Votes           │      └──────────────────┘  │
│  └──────────────────┘                             │
│                                                   │
└─────────────────────────────────────────────────────┘
```

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Verify Python installation
3. Ensure port 3000 is available
4. Check server is running and accessible

---

**Version**: 2.0 - Localized Offline System  
**Last Updated**: January 28, 2026
