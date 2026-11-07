# ⚡ Quick Start Guide - 5 Minutes

Get your voting system running in minutes!

## 🎯 What You Need

- Python installed (https://www.python.org/)
- Server computer (any Windows/Mac/Linux)
- Network connection between computers
- Web browsers on each voting computer

## 🚀 Start in 3 Steps

### Step 1: Install (1 minute)

**Windows:**
```
1. Open feza-vote folder
2. Double-click: install.bat
3. Wait for "Installation Successful"
```

**macOS/Linux:**
```bash
cd feza-vote
bash install.sh
```

### Step 2: Run Server (30 seconds)

**Windows:**
```
Double-click: start_server.bat
```

**macOS/Linux:**
```bash
bash start_server.sh
```

**You should see:**
```
[VOTING SYSTEM] Localized Offline Voting System v2.0
Network (LAN):    http://electionpoll.com:3000
```

Save that address!

### Step 3: Access from Any Computer (30 seconds)

**On server machine:**
```
http://localhost:3000
```

**On other computers (replace IP):**
```
http://electionpoll.com:3000
```

## 📋 Quick Tasks

### Add Voter Tokens
Edit `public/voters_tokens.txt`:
```
token1,token2,token3
token4,token5,token6
```

### Register Candidates
1. Go to: `http://[SERVER-IP]:3000/register.html`
2. Fill in: Name, Position, Image, Slogan
3. Click Register
4. Appears instantly on voting page!

### Start Voting
1. Go to: `http://[SERVER-IP]:3000`
2. Enter voter token
3. Click candidate
4. Done! Vote recorded in database

### View Results
Results auto-update every 5 seconds at bottom of voting page.

## 🔍 Find Server IP

**Windows (Command Prompt):**
```
ipconfig
```
Look for: `IPv4 Address . . . : 192.168.x.x`

**Mac/Linux (Terminal):**
```bash
ifconfig | grep "inet " | grep -v 127
```

## ✅ Verify It's Working

1. **On Server**: http://localhost:3000 ✓
2. **On Server**: http://electionpoll.com:3000 ✓
3. **On Other PC**: http://electionpoll.com:3000 ✓
4. **Check System**: http://electionpoll.com:3000/api/system-info ✓

## 🆘 Quick Fixes

| Problem | Fix |
|---------|-----|
| "Python not found" | Install Python from python.org |
| Port 3000 in use | Change PORT: `set PORT=3001 && python app_local.py` |
| Can't reach from other PC | Check IP is correct with ipconfig |
| No database error | Database creates automatically on first run |
| Server won't start | Try: `pip install Flask flask-cors` |

## 📊 System Info URL

Check everything at:
```
http://[SERVER-IP]:3000/api/system-info
```

Shows candidates, votes, tokens, everything!

## 📁 Important Files

- `app_local.py` - Main server (run this)
- `voting_system.db` - Database (created automatically)
- `public/voters_tokens.txt` - Add tokens here
- `install.bat / install.sh` - Setup script
- `start_server.bat / start_server.sh` - Start server

## 🔄 Daily Workflow

```
Morning:
1. Turn on server computer
2. Run: start_server.bat
3. Share address: electionpoll.com:3000

During Voting:
1. Students access: http://electionpoll.com:3000
2. Register candidates if needed: /register.html
3. Voting happens automatically

After Voting:
1. Export data: /api/export-data
2. Save for records
3. Stop server when done
```

## 📱 Mobile Access

Works perfectly on phones and tablets!

1. Connect to same WiFi
2. Type: http://electionpoll.com:3000
3. Vote!

## 🎨 Customize

Edit `public/script.js` and `public/styles.css` to customize appearance.

## 📚 More Help

- **Network Issues**: See NETWORK_SETUP.md
- **Full Guide**: See LOCALIZED_SETUP.md
- **Database Details**: See SQL tables in LOCALIZED_SETUP.md

## 🆘 Emergency Reset

To reset all votes:
```bash
# Access this URL in browser:
http://[SERVER-IP]:3000/api/reset
```

Or delete `voting_system.db` and restart server (creates fresh database).

---

**That's it! You're ready to vote!** ✨

For any issues, check the full documentation or restart the server.
