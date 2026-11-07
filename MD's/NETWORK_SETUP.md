# Network Configuration Guide

## Accessing the Voting System from Other Computers

This guide explains how to set up and access the localized voting system from multiple computers on the same network.

## Prerequisites

1. **Server Computer** - Running the voting system (Windows, macOS, or Linux)
2. **Client Computers** - Any computer with a web browser on the same network
3. **Network Connection** - All computers connected to same WiFi or Ethernet

## Step 1: Start the Server

### On the Server Machine:
- **Windows**: Double-click `start_server.bat`
- **macOS/Linux**: Run `bash start_server.sh`

You should see output like:
```
============================================================
   FEZA VOTING SYSTEM - Localized Offline Voting System v2.0
[DATABASE] SQLite - voting_system.db
============================================================
[ACCESS]
   Local Machine:    http://localhost:3000
   Network (LAN):    http://electionpoll.com:3000
   Registration:      http://electionpoll.com:3000/register.html
   System Info:       http://electionpoll.com:3000/api/system-info
============================================================
```

**Save the Network (LAN) address** shown (e.g., electionpoll.com)

## Step 2: Find Your Server IP Address

If the server doesn't show the IP, find it manually:

### Windows
1. Open Command Prompt (Win+R, type `cmd`, Enter)
2. Type: `ipconfig`
3. Look for "IPv4 Address" (usually 192.168.x.x or 10.x.x.x)

Example output:
```
Ethernet adapter Ethernet:
   IPv4 Address. . . . . . . . . : electionpoll.com
   Subnet Mask . . . . . . . . . : 255.255.255.0
```

### macOS
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Linux
```bash
hostname -I
```

## Step 3: Connect from Client Computers

### Option 1: Direct Access (Recommended)

1. Open any web browser on client computer
2. Type in address bar: `http://[SERVER-IP]:3000`
   - Replace `[SERVER-IP]` with the domain from Step 2
   - Example: `http://electionpoll.com:3000`
3. Press Enter

### Option 2: Bookmark for Easy Access

1. Access the voting page as shown above
2. Press Ctrl+D (or Cmd+D on Mac)
3. Click "Save" to bookmark

Next time, just click the bookmark!

### Option 3: QR Code Access (Mobile Devices)

Create a QR code for the URL:
1. Visit https://qr-code-generator.com/
2. Enter: `http://[SERVER-IP]:3000`
3. Generate QR code
4. Print or display on screen
5. Scan with phone/tablet

## Network Configuration Examples

### Scenario 1: Small Classroom (10-20 users)

```
┌─────────────────────────────────────────────┐
│ WiFi Network: "SchoolWiFi"                  │
├─────────────────────────────────────────────┤
│                                             │
│ Server: Teacher's Laptop (electionpoll.com)   │
│   ├── Student 1 Tablet (electionpoll.com)     │
│   ├── Student 2 Laptop (electionpoll.com)     │
│   ├── Student 3 Phone (electionpoll.com)      │
│   └── ... (up to 20 users)                 │
│                                             │
└─────────────────────────────────────────────┘

URL for all students: http://electionpoll.com:3000
```

### Scenario 2: Multi-Room Event

```
┌────────────────┬────────────────┬────────────────┐
│   Room A       │   Room B       │   Room C       │
├────────────────┼────────────────┼────────────────┤
│ Server PC      │ 5 Voters       │ 7 Voters       │
│ electionpoll.com  │ On network     │ On network     │
│                │                │                │
│ 3 Voters       │                │                │
│ In Room A      │                │                │
└────────────────┴────────────────┴────────────────┘

All access the same URL: http://electionpoll.com:3000
```

## Firewall Configuration

### Windows Firewall

If people can't access from other computers:

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python or Flask
4. Make sure "Private networks" is checked

### macOS Firewall

1. System Preferences → Security & Privacy
2. Firewall Options
3. Add Python to allowed apps

### Linux Firewall

```bash
# For UFW
sudo ufw allow 3000/tcp

# For iptables
│ Server: Teacher's Laptop (electionpoll.com) │
```

## Troubleshooting Network Access

### Problem: "Can't connect from other computer"

**Check 1**: Are both on same network?
```bash
# On server, run:
ipconfig (Windows) or ifconfig (Mac/Linux)

# On client, run:
ipconfig (Windows) or ifconfig (Mac/Linux)

# First 3 octets should match (e.g., 192.168.1.x)
```

│ electionpoll.com  │ On network     │ On network     │
- Server machine should show "running on http://0.0.0.0:3000"

**Check 3**: Try localhost from server
- Open http://localhost:3000 on server machine
- If this fails, server isn't running properly

**Check 4**: Try IP address directly
- Verify IP with ipconfig
- From client: Try http://electionpoll.com:3000
- (replace with your actual IP)

**Check 5**: Ping the server
```bash
# On client computer:
ping electionpoll.com
# Should see responses like:
# Reply from electionpoll.com: bytes=32 time=2ms TTL=64
```

**Check 6**: Check firewall
- Temporarily disable Windows Defender Firewall
- Try connecting again
- If it works, add exception for port 3000

### Problem: "Connection timed out"

1. Verify server IP address is correct
2. Make sure port is 3000, not something else
3. Check firewall settings
4. Restart the server

### Problem: "Connection refused"

1. Server is not running - restart it
2. Wrong port - check it's 3000
3. Server crashed - check for error messages

## Performance Tips

### For Many Users (50+)

1. **Use WiFi 5GHz** instead of 2.4GHz if available
2. **Wired Connection** for server is best
3. **Close unnecessary apps** on server
4. **Disable debug mode** in production

To disable debug mode, in `app_local.py`, change:
```python
app.run(host='0.0.0.0', port=port, debug=False)  # Already done!
```

### For Mobile Users

1. Create mobile-friendly URL (use bookmarks)
2. Test on multiple browsers (Chrome, Safari, Firefox)
3. Ensure good WiFi signal

## Extending the Network

### With Ethernet

1. Run server on wired connection for better performance
2. Clients can use WiFi

### Across Multiple Networks

If you have multiple WiFi networks, connect all to same router network.

### Remote Access (ADVANCED)

To access from outside the local network:

1. Note server public IP (from ISP)
2. Configure port forwarding on router
3. Add firewall rule for port 3000

**Warning**: This exposes your system. Only do if secure!

## Real-Time Synchronization

All clients automatically see:
- New candidates when registered
- Vote updates as they happen
- Results refresh every 5 seconds

No manual refresh needed!

## Testing Connectivity

Run this on any client computer:

### Windows PowerShell
```powershell
# Test connection
Test-NetConnection -ComputerName electionpoll.com -Port 3000

# Should show:
# TcpTestSucceeded : True
```

### macOS/Linux Terminal
```bash
# Test connection
nc -zv electionpoll.com 3000

# Should show:
# Connection to electionpoll.com port 3000 [tcp/*] succeeded!
```

## Advanced: Custom Network Names

### Windows - Add to Hosts File

1. Run Notepad as Administrator
2. Open: `C:\Windows\System32\drivers\etc\hosts`
3. Add line: `electionpoll.com voting-server`
4. Save file

Then access with: `http://voting-server:3000`

### macOS/Linux

1. Open Terminal
2. Edit: `sudo nano /etc/hosts`
3. Add line: `electionpoll.com voting-server`
4. Save with Ctrl+X, Y, Enter

Then access with: `http://voting-server:3000`

## Network Statistics

Check system info at: `http://[SERVER-IP]:3000/api/system-info`

Shows:
- Total candidates
- Total votes cast
- Tokens available
- Tokens spent

## Backup Over Network

### From Server to Client

1. Access: `http://[SERVER-IP]:3000/api/export-data`
2. Save JSON file
3. Keep as backup

### Restore from Backup

Move backup `voting_system.db` to server folder and restart.

---

**Document Version**: 2.0  
**Last Updated**: January 28, 2026
