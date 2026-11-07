# 📋 Deployment Checklist - Localized Voting System v2.0

## Pre-Deployment (Before Election Day)

### Environment Setup
- [ ] Python 3.7+ installed on server machine
- [ ] Run `install.bat` (Windows) or `bash install.sh` (Mac/Linux)
- [ ] Installation completed successfully
- [ ] Virtual environment created (`venv` folder exists)
- [ ] Dependencies installed (Flask, flask-cors)

### Database Preparation
- [ ] First run: `start_server.bat` or `start_server.sh`
- [ ] Database created (`voting_system.db` file exists)
- [ ] Tokens loaded from `voters_tokens.txt` (if existing)
- [ ] System ready: See "Running successfully" message

### Network Configuration
- [ ] Server IP address identified (use `ipconfig`)
- [ ] Network connectivity verified (ping test)
- [ ] Firewall allows port 3000
- [ ] All client computers on same network

### Data Preparation
- [ ] Voter tokens prepared in `voters_tokens.txt`
- [ ] Candidate information collected
- [ ] Images prepared for candidates
- [ ] Student IDs for candidates noted

### Server Testing
- [ ] Server starts without errors
- [ ] Access `http://localhost:3000` works
- [ ] Access `http://[SERVER-IP]:3000` works
- [ ] API returns data: `/api/candidates`
- [ ] System info shows: `/api/system-info`

### Frontend Testing
- [ ] Registration page loads: `/register.html`
- [ ] Voting page loads: `/`
- [ ] Results section displays: scroll to bottom
- [ ] Mobile view tested on phone/tablet

### Registration Test
- [ ] Register test candidate successfully
- [ ] Candidate appears immediately on voting page
- [ ] Image displays correctly
- [ ] Slogan appears on candidate card

### Voting Test (Single Computer)
- [ ] Test token works: `/api/check-token/<token>`
- [ ] Can submit vote for President
- [ ] Vote count increments
- [ ] Vote recorded in database
- [ ] Can vote for Vice President
- [ ] Token marked as spent
- [ ] Can't vote again with spent token

### Voting Test (Network)
- [ ] Access from second computer works
- [ ] Register candidate from second computer
- [ ] Candidate appears on all computers
- [ ] Vote from second computer counts
- [ ] Results update across all computers

### Backup & Export
- [ ] Database backed up: `voting_system.db` copied
- [ ] Export data: `/api/export-data` works
- [ ] JSON export contains all data
- [ ] Reset test: `/api/reset` clears votes
- [ ] System recovers after reset

### Documentation
- [ ] QUICK_START.md available
- [ ] NETWORK_SETUP.md printed/shared
- [ ] Server IP written down
- [ ] Instructions ready for users

---

## Election Day (Before Voting Starts)

### Morning Preparation
- [ ] Server machine powered on and updated
- [ ] Network router/WiFi working
- [ ] Server IP verified and noted
- [ ] Instructions printed for voters

### System Startup
- [ ] Database reset (if needed): `/api/reset`
- [ ] Fresh `voting_system.db` created
- [ ] Tokens loaded fresh
- [ ] Server started: `start_server.bat` or `start_server.sh`
- [ ] Server shows: "Running on 0.0.0.0:3000"

### Pre-Election Verification
- [ ] All candidates registered
- [ ] Candidate images visible
- [ ] Vote counts at zero
- [ ] Test vote from server works
- [ ] Test vote from client works
- [ ] Results update live

### Communication
- [ ] Server IP posted visibly
- [ ] WiFi credentials provided (if needed)
- [ ] Voting instructions distributed
- [ ] Technical support contact available

---

## During Voting

### Monitoring
- [ ] Server status monitored periodically
- [ ] Check system info: `/api/system-info`
- [ ] Monitor vote counts
- [ ] Verify network connectivity
- [ ] Backup data periodically

### Troubleshooting
- [ ] Keep troubleshooting guide handy
- [ ] Be ready to restart server if needed
- [ ] Have backup network plan ready
- [ ] Have offline backup device ready

### Voter Support
- [ ] Help voters access correct URL
- [ ] Assist with token entry
- [ ] Explain voting process
- [ ] Handle special requests

---

## During Voting - Issues & Resolution

### If Server Goes Down
- [ ] Check error message on server console
- [ ] Verify database not locked
- [ ] Restart: Stop server, wait 5 seconds, restart
- [ ] Check if port 3000 is available: `netstat -ano | findstr :3000`
- [ ] Try different port: `PORT=3001 python app_local.py`

### If Network Connection Fails
- [ ] Check WiFi router status
- [ ] Verify all devices on same network
- [ ] Check server IP hasn't changed
- [ ] Restart router if necessary
- [ ] Use Ethernet cable for server if possible

### If Database Locks
- [ ] Stop server completely
- [ ] Wait 10 seconds
- [ ] Restart server
- [ ] Try vote again

### If Results Don't Update
- [ ] Hard refresh browser: Ctrl+F5 (or Cmd+Shift+R on Mac)
- [ ] Check server is still running
- [ ] Verify network connectivity
- [ ] Check database not locked

---

## End of Voting

### Data Preservation
- [ ] Export final data: `/api/export-data`
- [ ] Save JSON export file
- [ ] Copy `voting_system.db` as backup
- [ ] Verify data integrity

### Results Documentation
- [ ] Screenshot results page
- [ ] Note all final vote counts
- [ ] Export data for records
- [ ] Print or save results

### Server Shutdown
- [ ] Stop server gracefully (Ctrl+C)
- [ ] Wait for shutdown message
- [ ] Verify database is saved
- [ ] Check no errors on shutdown

### Final Backup
- [ ] Copy `voting_system.db` to safe location
- [ ] Copy exported JSON to safe location
- [ ] Save screenshots of results
- [ ] Backup all voting records

---

## Post-Deployment Review

### Data Analysis
- [ ] Review final vote counts
- [ ] Identify winner(s)
- [ ] Check for any anomalies
- [ ] Verify vote totals add up

### Performance Review
- [ ] How many total votes cast?
- [ ] Longest voting time?
- [ ] Any downtime issues?
- [ ] Network performance acceptable?
- [ ] Database size (check `voting_system.db`)

### System Review
- [ ] All votes recorded correctly?
- [ ] No data loss observed?
- [ ] Tokens managed properly?
- [ ] Database integrity maintained?

### Lessons Learned
- [ ] What went well?
- [ ] What needs improvement?
- [ ] Any network issues?
- [ ] Any data concerns?
- [ ] Notes for next time?

---

## Maintenance (After Election)

### Data Archival
- [ ] Rename backup: `voting_system_election_2026_01_28.db`
- [ ] Store in secure location
- [ ] Keep JSON export as well
- [ ] Document date and event

### System Cleanup
- [ ] Remove temporary files
- [ ] Archive any logs
- [ ] Delete `voters_tokens.txt` if sensitive
- [ ] Clear browser cache if public computers

### Database Maintenance
- [ ] Verify database file size reasonable
- [ ] Check for any corruption
- [ ] Test restore from backup
- [ ] Document backup process

### Documentation Update
- [ ] Update notes for next election
- [ ] Record any issues encountered
- [ ] Save troubleshooting solutions
- [ ] Update runbooks if needed

---

## Final Safety Checklist

### Security
- [ ] No unauthorized access attempted
- [ ] All votes recorded accurately
- [ ] Tokens managed properly
- [ ] Database file secured
- [ ] No data breaches

### Reliability
- [ ] System available entire voting period
- [ ] No crashes or downtime
- [ ] All votes persisted
- [ ] Results accurate
- [ ] No data corruption

### Completeness
- [ ] All eligible voters could vote
- [ ] No vote was missed
- [ ] Results agree with records
- [ ] Backup created
- [ ] Documentation complete

---

## Deployment Sign-Off

**Election Details:**
- Date: _______________
- Event: _______________
- Server Machine: _______________
- Server IP: _______________

**Pre-Deployment:**
- [ ] All checks passed
- [ ] Ready for voting
- Name/Signature: _______________

**Deployment Completion:**
- [ ] Election completed successfully
- [ ] Data backed up
- [ ] System secured
- Name/Signature: _______________

**Post-Deployment Review:**
- [ ] Review completed
- [ ] Lessons documented
- [ ] Ready for next election
- Name/Signature: _______________

---

## Quick Reference - Election Day Commands

### Start Server (Windows)
```bash
start_server.bat
```

### Start Server (Mac/Linux)
```bash
bash start_server.sh
```

### Access Voting Page
```
http://[SERVER-IP]:3000
```

### Register Candidates
```
http://[SERVER-IP]:3000/register.html
```

### View Results
```
http://[SERVER-IP]:3000
(scroll to bottom)
```

### System Information
```
http://[SERVER-IP]:3000/api/system-info
```

### Export Data
```
http://[SERVER-IP]:3000/api/export-data
```

### Reset All Votes
```
http://[SERVER-IP]:3000/api/reset
(or delete voting_system.db and restart)
```

---

## Emergency Contacts

**Technical Issues:**
- Primary Contact: _______________
- Phone: _______________
- Backup Contact: _______________

**Network Issues:**
- Network Admin: _______________
- Phone: _______________

**Other Support:**
- IT Support: _______________
- Phone: _______________

---

## Notes

```
Use this space for additional notes during deployment:


```

---

**Deployment Checklist Version**: 2.0  
**Last Updated**: January 28, 2026  
**Status**: Ready for Production Deployment  

✅ **All systems ready for voting!**
