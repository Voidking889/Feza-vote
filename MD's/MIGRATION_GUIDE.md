# Migration Guide: Online System → Localized System

This guide helps you migrate your existing voting system to the new localized (offline) version.

## What's Changed?

| Aspect | Old System | New System |
|--------|-----------|-----------|
| **Storage** | In-memory (lost on restart) | SQLite Database (persistent) |
| **Access** | Localhost only | Any computer on network |
| **Internet** | Optionally used | Completely offline |
| **Data Persistence** | Not saved | Permanently saved |
| **Multi-user** | Limited | Full network support |
| **Scalability** | ~100 users | 500+ users |

## Why Upgrade?

✅ **Persistent Data** - Votes saved even after restart  
✅ **Network Access** - Use from any computer on LAN  
✅ **Completely Offline** - No internet connection needed  
✅ **Better Performance** - SQLite is more efficient  
✅ **Backup Capability** - Export data anytime  
✅ **Production Ready** - Suitable for large events  

## Migration Steps

### Step 1: Backup Old Data

If you have existing voting data:

```bash
# On the old system, export data:
# 1. Note all candidates and their vote counts
# 2. Save token list from public/voters_tokens.txt
```

### Step 2: Prepare New System

1. **Install new version**:
   - Windows: Run `install.bat`
   - macOS/Linux: Run `install.sh`

2. **Transfer files to new system**:
   - Copy `public/voters_tokens.txt` (if existing)
   - Copy any custom images or configurations

### Step 3: First Run - Initialize Database

1. **Start server**:
   - Windows: `start_server.bat`
   - macOS/Linux: `start_server.sh`

2. **Server initializes database**:
   - Automatically creates `voting_system.db`
   - Loads tokens from `voters_tokens.txt`
   - Ready for use

### Step 4: Restore Old Candidates (if needed)

If you had candidates from old system:

**Option A: Manual Re-registration**

1. Go to: `http://localhost:3000/register.html`
2. Re-enter each candidate
3. Upload images again

**Option B: Database Import Script** (Advanced)

Create a Python script to import:
```python
import sqlite3

# Connect to new database
conn = sqlite3.connect('voting_system.db')
c = conn.cursor()

# Insert candidates
candidates = [
    ("John Doe", "president", "base64_image_data", "VOTE001", "Make it great"),
    ("Jane Smith", "vice_president", "base64_image_data", "VOTE002", "Best VP"),
]

for name, position, image, student_id, slogan in candidates:
    c.execute('''INSERT INTO candidates 
                (name, position, image, student_id, slogan)
                VALUES (?, ?, ?, ?, ?)''',
             (name, position, image, student_id, slogan))

conn.commit()
conn.close()
```

### Step 5: Verify Migration

1. **Check database created**:
   ```bash
   # List files in voting folder
   # Should see: voting_system.db
   ```

2. **Check tokens loaded**:
   - Access: `http://localhost:3000/api/system-info`
   - Should show token count

3. **Test registration**:
   - Go to: `/register.html`
   - Add a test candidate
   - Verify it appears on voting page

4. **Test voting**:
   - Try submitting a vote
   - Check results update
   - Verify data persists after refresh

## File Changes

### Old Files (still available)
- `app.py` - Original Flask app (in-memory)
- `requirements.txt` - Original dependencies

### New Files
- `app_local.py` - **Use this instead** (SQLite version)
- `install.bat / install.sh` - Installation scripts
- `start_server.bat / start_server.sh` - Server launchers
- `LOCALIZED_SETUP.md` - Full documentation
- `NETWORK_SETUP.md` - Network access guide
- `QUICK_START.md` - Quick reference

## Running Both Versions Simultaneously

To run old and new system on different ports:

```bash
# Old system on port 3000
python app.py

# New system on port 3001
PORT=3001 python app_local.py
```

Access:
- Old: `http://localhost:3000`
- New: `http://localhost:3001`

## Database Schema

The new system uses these tables:

```sql
-- Candidates
candidates (id, name, position, votes, image, slogan, student_id, registration_date)

-- Individual votes
votes (id, token, candidate_id, position, timestamp)

-- Valid voter tokens
valid_tokens (token, is_spent, created_date)

-- System configuration
system_config (key, value, updated_date)
```

## API Changes

### Same Endpoints (Compatible)
- `GET /api/candidates`
- `POST /api/vote`
- `GET /api/results`
- `GET /api/check-token/<token>`
- `POST /api/candidates/register`
- `POST /api/reset`

### New Endpoints
- `GET /api/system-info` - Server stats
- `GET /api/export-data` - Export all data

## Data Export

Export voting data anytime:

```bash
# Access in browser
http://localhost:3000/api/export-data

# Returns JSON with:
# - All candidates
# - All votes
# - Token statistics
# - Export timestamp
```

## Backup & Restore

### Backup Database
```bash
# Copy database file
cp voting_system.db voting_system_backup.db
```

### Restore Database
```bash
# Restore from backup
cp voting_system_backup.db voting_system.db

# Restart server
```

## Performance Comparison

### Old System (In-Memory)
- Fast: O(1) access
- Data lost on restart
- Memory grows with votes
- Limited to ~100 voters

### New System (SQLite)
- Fast: O(log n) access  
- Data persists
- Constant memory usage
- Supports 500+ voters
- Indexed queries

## Troubleshooting Migration

### Problem: "Database locked"
- Close old app.py if running
- Only one instance of app_local.py should run
- Restart server

### Problem: "Tokens not loaded"
- Check `voters_tokens.txt` exists
- Verify file has proper format (comma or newline separated)
- Restart server and check logs

### Problem: "Import error"
- Run: `pip install Flask flask-cors`
- Ensure in activated virtual environment
- Use Python 3.7+

### Problem: "Port already in use"
- Use different port: `PORT=3001 python app_local.py`
- Or kill process using port 3000

## Rollback to Old System

If you need to use old system:

```bash
# Old system (in-memory, no persistence)
python app.py
```

Data will NOT persist, but system works as before.

## Long-term: Stay with New System

**Recommended**: Keep using the new localized system because:

✓ Data persists  
✓ Works offline  
✓ Scales better  
✓ Network accessible  
✓ Production ready  

## Migration Checklist

- [ ] Backup old system data
- [ ] Run `install.bat` or `install.sh`
- [ ] Start `start_server.bat` or `start_server.sh`
- [ ] Verify database created
- [ ] Check system info at `/api/system-info`
- [ ] Test candidate registration
- [ ] Test voting
- [ ] Test token validation
- [ ] Test results display
- [ ] Export data to JSON
- [ ] Verify network access from other computer
- [ ] Set up regular backups

## Next Steps

1. **Read**: QUICK_START.md (5 min overview)
2. **Setup**: LOCALIZED_SETUP.md (detailed guide)
3. **Network**: NETWORK_SETUP.md (multi-computer setup)
4. **Start voting!**

---

**Migration Complete!** You now have a modern, offline voting system. ✨

For support, check documentation or restart the server.
