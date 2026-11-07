
# 🗳️ Visual Setup & Usage Guide

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                   FEZA VOTING SYSTEM v2.0                          │
│              Localized Offline Voting System                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SETUP PHASE                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INSTALL                    2. START SERVER                      │
│  ┌─────────────────┐          ┌──────────────────┐                │
│  │ install.bat     │────────▶ │ start_server.bat │                │
│  │ (2 min)         │          │ (30 seconds)     │                │
│  └─────────────────┘          └─────┬────────────┘                │
│       ▲                             │                              │
│       │                             ▼                              │
│   Python 3.7+            Flask Server Running                      │
│   (must install)         http://0.0.0.0:3000                      │
│                                     │                              │
│                                     ▼                              │
│                          SQLite Database Created                   │
│                          (voting_system.db)                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  USAGE PHASE                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SERVER IP: electionpoll.com:3000 (FIND WITH: ipconfig)             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ LOCAL MACHINE                NETWORK ACCESS                 │  │
│  │ (Server Computer)            (Any Computer)                 │  │
│  │ ┌────────────────────────┐  ┌──────────────────────────┐   │  │
│  │ │ http://localhost:3000  │  │ http://electionpoll.com:3000   │   │  │
│  │ └────────────────────────┘  └──────────────────────────┘   │  │
│  │           ↓                              ↓                  │  │
│  │ ┌────────────────────────────────────────────────────────┐ │  │
│  │ │              VOTING INTERFACE                          │ │  │
│  │ │  - Enter voter token                                   │ │  │
│  │ │  - View available candidates                           │ │  │
│  │ │  - Click to vote for President                         │ │  │
│  │ │  - Click to vote for Vice President                    │ │  │
│  │ │  - See results update live                             │ │  │
│  │ └────────────────────────────────────────────────────────┘ │  │
│  │                        │                                    │  │
│  │                        ▼                                    │  │
│  │ ┌────────────────────────────────────────────────────────┐ │  │
│  │ │              SQLite DATABASE                           │ │  │
│  │ │  Stores: Candidates, Votes, Tokens, Config            │ │  │
│  │ │  Location: voting_system.db                            │ │  │
│  │ │  Persistence: Permanent (survives restarts)            │ │  │
│  │ └────────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Installation

### Windows Installation Flow

```
START
  │
  ▼
┌─────────────────────────────────┐
│ Check Python installed          │
│ Run: python --version           │
└─────────────┬───────────────────┘
              │
         YES? │ NO?
         ─────┴─────
         │         │
         ▼         ▼
      CONTINUE  INSTALL PYTHON
         │       (from python.org)
         │         │
         │         ▼
         │      RESTART
         │         │
         └─────────┘
              │
              ▼
     ┌──────────────────────┐
     │ Double-click:        │
     │ install.bat          │
     └────────┬─────────────┘
              │
              ▼
     ┌──────────────────────┐
     │ Creating venv        │
     │ Installing packages  │
     │ (Flask, flask-cors)  │
     └────────┬─────────────┘
              │
              ▼
     ┌──────────────────────┐
     │ ✓ Installation OK    │
     └────────┬─────────────┘
              │
              ▼
     ┌──────────────────────┐
     │ Double-click:        │
     │ start_server.bat     │
     └────────┬─────────────┘
              │
              ▼
     ┌──────────────────────┐
     │ Server running on:   │
     │ http://localhost:3000│
     │ http://electionpoll.com:3000 │
     └────────┬─────────────┘
              │
              ▼
            READY!
```

## Voting Process Flow

```
┌─────────────────────────────────────────────────┐
│           VOTER JOURNEY                         │
└─────────────────────────────────────────────────┘

START: Voter opens http://[SERVER-IP]:3000
  │
  ▼
┌─────────────────────────────────────────────────┐
│ VOTING PAGE LOADS                               │
│ - Voting Interface                              │
│ - Token Input Field                             │
│ - "Check Status" Button                         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌──────────────────────────┐
        │ Enter Voter Token        │
        │ Example: "VOTE123"       │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Click "Check Status"     │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │ Check Token Status:              │
        │ - Valid?                         │
        │ - Spent?                         │
        │ - Which positions voted?         │
        └──────────┬──────────────────────┘
                   │
          TOKEN VALID? ┌─────────┐ NO?
                  YES? │         │
          ┌───────────┴─┘         └───────────┐
          │                                   │
          ▼                                   ▼
    ┌──────────────────┐            ┌────────────────┐
    │ Show Positions   │            │ Show Error     │
    │ - President      │            │ Invalid Token  │
    │ - Vice President │            │ Ask Again      │
    └────────┬─────────┘            └────────────────┘
             │
             ▼
       ┌─────────────────────────────────┐
       │ POSITION SELECTION              │
       │ Can voter vote for this?        │
       │ PRESIDENT CANDIDATES:           │
       │ ┌─────────────────────────────┐ │
       │ │ [Candidate 1]  0 votes      │ │
       │ │ [Candidate 2]  3 votes      │ │
       │ └─────────────────────────────┘ │
       │ VICE PRESIDENT CANDIDATES:      │
       │ ┌─────────────────────────────┐ │
       │ │ [Candidate 3]  1 vote       │ │
       │ │ [Candidate 4]  2 votes      │ │
       │ └─────────────────────────────┘ │
       └────────┬────────────────────────┘
                │
                ▼
       ┌──────────────────────────┐
       │ Click Candidate to Vote  │
       │ (e.g., Candidate 1)      │
       └──────────┬───────────────┘
                  │
                  ▼
       ┌──────────────────────────┐
       │ VOTE SUBMITTED           │
       │ - Vote recorded          │
       │ - Database updated       │
       │ - Vote count increases   │
       └──────────┬───────────────┘
                  │
                  ▼
       ┌──────────────────────────┐
       │ Token Status:            │
       │ ✓ Can vote VP?           │
       │ YES: Show VP candidates  │
       │ NO: Show completion      │
       └──────────┬───────────────┘
                  │
          ┌───────┴─────────┐
          │                 │
     Can Vote VP?      Already Voted Both
          │                 │
          ▼                 ▼
    ┌──────────────┐  ┌──────────────┐
    │ VICE PRES.   │  │ THANK YOU    │
    │ CANDIDATES   │  │ PAGE         │
    │ (Same flow)  │  │ "Voting OK"  │
    └──────────────┘  └──────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ After vote:              │
    │ ✓ Both Positions Voted   │
    │ ✓ Token Marked Spent     │
    │ ✓ Can't vote again       │
    └──────────┬───────────────┘
               │
               ▼
            COMPLETE!
```

## Network Architecture Visualization

```
┌───────────────────────────────────────────────────────────────────┐
│                     LOCAL NETWORK (LAN)                           │
│                    192.168.1.x/24                                  │
│                  (All computers here)                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  ┌────────────────────────────────────────────────────┐   │ │
│  │  │ SERVER COMPUTER (electionpoll.com)                   │   │ │
│  │  │ ┌──────────────────────────────────────────────┐  │   │ │
│  │  │ │ Flask Server Port 3000                       │  │   │ │
│  │  │ ├──────────────────────────────────────────────┤  │   │ │
│  │  │ │ Serves HTML/CSS/JS                          │  │   │ │
│  │  │ │ Handles API requests                        │  │   │ │
│  │  │ │ Manages database                            │  │   │ │
│  │  │ └──────────────────────────────────────────────┘  │   │ │
│  │  │                    │                               │   │ │
│  │  │                    ▼                               │   │ │
│  │  │ ┌──────────────────────────────────────────────┐  │   │ │
│  │  │ │ SQLite Database (voting_system.db)          │  │   │ │
│  │  │ ├──────────────────────────────────────────────┤  │   │ │
│  │  │ │ - candidates (name, position, votes, image) │  │   │ │
│  │  │ │ - votes (token, candidate, position)        │  │   │ │
│  │  │ │ - valid_tokens (token, is_spent)           │  │   │ │
│  │  │ │ - system_config (key, value)                │  │   │ │
│  │  │ └──────────────────────────────────────────────┘  │   │ │
│  │  └────────────────────────────────────────────────────┘   │ │
│  │                           △                                 │ │
│  │                    ┌──────┴──────┬─────────┬───────────┐  │ │
│  │                    │             │         │           │  │ │
│  │  ┌─────────────────▼──┐  ┌──────▼─┐  ┌───▼────┐  ┌───▼──┐ │
│  │  │ CLIENT 1           │  │CLIENT 2│  │CLIENT 3│  │MOBILE│ │
│  │  │ (electionpoll.com)    │  │electionpoll.com │  │electionpoll.com │  │PHONE │ │
│  │  │                    │  │:3000   │  │:3000   │  │WiFi  │ │
│  │  │ Browser:           │  │Browser │  │Browser │  │      │ │
│  │  │ http://electionpoll.com:3000 │  │:3000   │  │:3000   │  │:3000 │ │
│  │  │                    │  │        │  │        │  │      │ │
│  │  │ VOTING             │  │VOTING  │  │VOTING  │  │VOTING│ │
│  │  └────────────────────┘  └────────┘  └────────┘  └──────┘ │
│  │                                                             │ │
│  │  * All computers see SAME CANDIDATES & RESULTS             │ │
│  │  * Votes are SYNCHRONIZED across all clients              │ │
│  │  * Data PERSISTS in SQLite on server                      │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ★ NO INTERNET CONNECTION NEEDED ★                               │
│  ★ ALL DATA STAYS LOCAL ★                                        │
│  ★ WORKS ANYWHERE WITH WIFI/ETHERNET ★                           │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## File Organization

```
feza-vote/
│
├── 📄 app_local.py              ← MAIN APPLICATION (use this!)
│   └─ SQLite database logic
│   └─ Network IP detection
│   └─ REST API endpoints
│
├── 📁 venv/                     ← Virtual Environment (auto-created)
│   └─ Python packages
│   └─ Dependencies
│
├── 📁 public/                   ← Frontend Files
│   ├─ index.html                ← Voting page
│   ├─ register.html             ← Candidate registration
│   ├─ results.html              ← Results display
│   ├─ script.js                 ← Voting logic
│   ├─ register.js               ← Registration logic
│   ├─ results.js                ← Results updates
│   ├─ styles.css                ← Styling
│   ├─ auth-config.js            ← Admin settings
│   └─ voters_tokens.txt         ← Voter tokens (auto-loaded)
│
├── 📄 voting_system.db          ← DATABASE (auto-created!)
│   ├─ candidates table
│   ├─ votes table
│   ├─ valid_tokens table
│   └─ config table
│
├── ⚙️ install.bat               ← INSTALLATION (Windows)
├── ⚙️ install.sh                ← INSTALLATION (Mac/Linux)
├── ▶️ start_server.bat           ← START SERVER (Windows)
├── ▶️ start_server.sh            ← START SERVER (Mac/Linux)
│
├── 📚 QUICK_START.md            ← START HERE! (5 min)
├── 📚 LOCALIZED_SETUP.md        ← Full setup guide
├── 📚 NETWORK_SETUP.md          ← Network configuration
├── 📚 MIGRATION_GUIDE.md        ← Upgrade from v1.0
├── 📚 README_v2.md              ← System overview
├── 📚 DEPLOYMENT_CHECKLIST.md   ← Before/during/after
├── 📚 IMPLEMENTATION_SUMMARY.md ← What was done
│
├── 📄 requirements.txt          ← Python dependencies
├── 📄 README.md                 ← Original docs
└── 📄 app.py                    ← Old version (reference)
```

## Database Schema Visualization

```
SQLite Database: voting_system.db
│
├── TABLE: candidates
│   ├─ id INTEGER (PRIMARY KEY)
│   ├─ name TEXT
│   ├─ position TEXT ('president' or 'vice_president')
│   ├─ votes INTEGER
│   ├─ image TEXT (Base64)
│   ├─ slogan TEXT
│   ├─ student_id TEXT (UNIQUE)
│   └─ registration_date TIMESTAMP
│
├── TABLE: votes
│   ├─ id INTEGER (PRIMARY KEY)
│   ├─ token TEXT
│   ├─ candidate_id INTEGER (FOREIGN KEY)
│   ├─ position TEXT
│   └─ timestamp TIMESTAMP
│
├── TABLE: valid_tokens
│   ├─ token TEXT (PRIMARY KEY)
│   ├─ is_spent INTEGER (0 or 1)
│   └─ created_date TIMESTAMP
│
└── TABLE: system_config
    ├─ key TEXT (PRIMARY KEY)
    ├─ value TEXT
    └─ updated_date TIMESTAMP
```

## Access URLs Reference

```
┌─────────────────────────────────────────────────────────────┐
│              COMMON ACCESS URLS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ LOCAL (Server Computer):                                    │
│ ──────────────────────────────────────────────────────────  │
│ Voting Page:        http://localhost:3000                   │
│ Register:           http://localhost:3000/register.html     │
│ Results:            http://localhost:3000/results.html      │
│ System Info:        http://localhost:3000/api/system-info   │
│ Export Data:        http://localhost:3000/api/export-data   │
│                                                             │
│ NETWORK (Any Computer):                                     │
│ ──────────────────────────────────────────────────────────  │
│ Replace "192.168.1.100" with YOUR server address                │
│                                                             │
│ Voting Page:        http://electionpoll.com:3000              │
│ Register:           http://electionpoll.com:3000/register.html│
│ Results:            http://electionpoll.com:3000/results.html │
│ System Info:        http://electionpoll.com:3000/api/...      │
│ Export Data:        http://electionpoll.com:3000/api/...      │
│                                                             │
│ API ENDPOINTS:                                              │
│ ──────────────────────────────────────────────────────────  │
│ GET  /api/candidates       - List all candidates            │
│ POST /api/vote             - Submit vote                    │
│ GET  /api/results          - Get results                    │
│ GET  /api/check-token/<T>  - Check token status            │
│ GET  /api/system-info      - Server stats                   │
│ GET  /api/export-data      - Export JSON                    │
│ POST /api/reset            - Reset all votes                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting Decision Tree

```
                        ISSUE?
                          │
                ┌─────────┴──────────┐
                │                   │
           Server Won't Start    Can't Connect
                │                   │
           ┌────┴────┐          ┌───┴────┐
           │          │         │         │
      No Python   Port Busy  Server IP  Firewall
      Install it   Try 3001   Check IP   Check FW
                (PORT=3001)  (ipconfig)  Allow 3000
                
                
              SLOW OR ERRORS?
                    │
        ┌───────────┼───────────┐
        │           │           │
    Too Many     Database   Network
    Users        Locked     Problem
    (normal)     Restart    Check WiFi
                 Server
```

---

**Visual Guide Version**: 2.0  
**Last Updated**: January 28, 2026
improve this
Here’s an improved, more concise, and visually organized version of your FEZA Voting System v2.0 Visual Setup & Usage Guide. I’ve streamlined the flow diagrams, clarified the steps, improved section labeling, and enhanced readability while retaining all technical details.

🗳️ FEZA Voting System v2.0
Visual Setup & Usage Guide
Last Updated: January 28, 2026

1. System Overview
┌──────────────────────────────────────────────────────────────┐
│                   FEZA VOTING SYSTEM v2.0                   │
│            Localized, Offline, Reliable, Secure             │
└──────────────────────────────────────────────────────────────┘

      ┌────────────┐    ┌─────────────┐     ┌─────────────┐
      │  SETUP     │───▶│   USAGE     │───▶ │   RESULTS   │
      └────────────┘    └─────────────┘     └─────────────┘
2. Setup Phase
Step 1: Install Requirements

Ensure Python 3.7+ is installed
Run: python --version
If missing, download from python.orgOpens a new window
Step 2: Install Dependencies

Run: install.bat (Windows) or install.sh (Mac/Linux)
Creates virtual environment & installs packages
Step 3: Start the Server

Run: start_server.bat or start_server.sh
Server runs at:
http://localhost:3000 (local)
http://electionpoll.com:3000 (network)
Step 4: Database Setup

SQLite database auto-created: voting_system.db
Data persists across restarts
3. Usage Phase
Access the Voting Interface:

Local (Server Computer):
http://localhost:3000

Network (Other Devices):
http://electionpoll.com:3000
(Find server IP using ipconfig if needed)

Voting Steps:

Open Voting Page
Enter Voter Token (e.g., VOTE123)
Check Status
Validates token, shows voting eligibility
Vote for President
Select candidate, vote is recorded
Vote for Vice President
Repeat process if eligible
Finish Voting
Token marked as spent, cannot vote again
Live results update for all users
4. Voting Process Flow
START
  │
  ▼
Open http://[SERVER-IP]:3000
  │
Enter Token ──► Check Status
  │               │
  │         [Valid?]
  │          │    │
  │         Yes   No
  │          │    │
  │   Show Positions
  │  (President/VP)
  │          │
  │   Select Candidate(s)
  │          │
  │   Vote Recorded
  │          │
  │ [Can vote another position?]
  │          │
  │     Yes / No
  │          │
  │   Repeat / Thank you!
  ▼
COMPLETE — Cannot vote again
5. Network Architecture
┌────────────────────────────────────────────────────────────┐
│                    LOCAL NETWORK (LAN)                    │
│             All computers connect via WiFi/Ethernet        │
│                                                          │
│   ┌─────────────┐         ┌─────────────┐                │
│   │ SERVER      │◀──────▶ │  CLIENTS    │                │
│   │ (election   │         │ (Any device │                │
│   │ poll.com)   │         │ browser)    │                │
│   └────┬────────┘         └─────┬───────┘                │
│        │                        │                        │
│   ┌────▼───────────┐      ┌─────▼────────────┐           │
│   │ Flask Server   │      │ Voting Interface │           │
│   │ port 3000      │      │ Browser:         │           │
│   │                │      │ http://election  │           │
│   │ SQLite DB      │      │ poll.com:3000    │           │
│   │ voting_system.db│      └─────────────────┘           │
│   └────────────────┘                                    │
│                                                        │
│  ★ No Internet needed — all data stays local! ★         │
└────────────────────────────────────────────────────────┘
6. File Structure
feza-vote/
│
├── app_local.py           # Main server application
├── voting_system.db       # SQLite database (auto-created)
├── venv/                  # Python virtual environment
├── public/                # Frontend files: HTML, JS, CSS
│   ├── index.html         # Voting page
│   ├── register.html      # Candidate registration
│   ├── results.html       # Live results
│   ├── script.js, ...     # Logic scripts
│   ├── voters_tokens.txt  # Voter tokens (auto-imported)
│   └── styles.css         # Stylesheet
├── install.bat/.sh        # Install dependencies
├── start_server.bat/.sh   # Start server
├── requirements.txt       # Python dependencies
├── README & Docs          # Setup, migration, deployment guides
└── app.py                 # (Old version - for reference)
7. Database Schema
voting_system.db
├── candidates (id, name, position, votes, image, slogan, student_id, registration_date)
├── votes (id, token, candidate_id, position, timestamp)
├── valid_tokens (token, is_spent, created_date)
└── system_config (key, value, updated_date)
8. Access URLs
Page	Local (Server)	Network (Any Device)
Voting	http://localhost:3000Opens a new window	http://electionpoll.com:3000Opens a new window
Register	/register.html	/register.html
Results	/results.html	/results.html
System Info	/api/system-info	/api/system-info
Export Data	/api/export-data	/api/export-data
API Endpoints:

GET /api/candidates — List candidates
POST /api/vote — Submit vote
GET /api/results — Live results
GET /api/check-token/<token> — Token status
POST /api/reset — Reset all votes
9. Troubleshooting
Server Won’t Start:

Python missing? Install it.
Port 3000 busy? Try 3001.
Database locked? Restart server.
Can’t Connect:

Wrong Server IP? Check with ipconfig.
Firewall blocking? Allow port 3000.
Slow/Errors:

Too many users? Wait & retry.
Network issue? Check WiFi/Ethernet.
Tip:

All votes/results sync instantly for all users.
Data is safe and persistent — even after server restarts.


Guide maintained by BARAKA SAIDI KIWANGA










