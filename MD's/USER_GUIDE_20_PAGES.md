FEZA VOTE USER GUIDE – TEXTBOOK EDITION

Page 1: Introduction and Purpose

Feza Vote is a digital platform designed to manage Feza-school elections efficiently, securely, and transparently. This comprehensive guide covers everything you need—from initial installation to post-election reporting—ensuring you can confidently run a full election cycle with Feza Vote.

Who should use this guide?

* School administrators who oversee elections
* ICT officers responsible for technical setup
* Election supervisors ensuring process integrity
* Teachers managing live results and reporting
* Developers maintaining and updating the system

Primary objectives of Feza Vote:

* Register and manage candidates 
* Prevent double voting with secure controls
* Enable real-time voting and result updates
* Provide a live, interactive results dashboard
* Protect sensitive operations via authentication

Key system components:

* app.py: Main Flask backend server
* public/: Frontend pages and JavaScript code
* auth_config.py: Backend authentication management
* generate_tokens.py: Voter token generation utility
* Documentation files: Setup, authentication, deployment, and IP protection guides

Tip: Read this manual fully before your first election. Use it as a checklist during real events to ensure no step is missed.

---

Page 2: System Architecture Overview

Feza Vote’s architecture is intentionally straightforward to support reliability and clarity during school elections.

Components:

* Frontend: HTML, CSS, JavaScript in public/ folder (voting and results pages)
* Backend: Flask Python server (handles election logic, APIs)
* Data storage: Local database or files, depending on your configuration

Election workflow:

1. Admin sets up candidates and generates tokens for voters.
2. Each voter accesses the platform and casts their vote.
3. Backend records and validates each vote, preventing duplicates.
4. Results page displays live, auto-updating tallies.
5. Authenticated staff (teachers/devs) access protected dashboards for oversight.

Design principles:

* Each voter can vote only once.
* Results update immediately as votes are cast.
* Sensitive dashboards are protected by authentication.
* Every administrative action is controlled and, where possible, logged.

Note: For school-internal elections, this design is robust. Public or external elections require additional enterprise-grade security.

---

Page 3: Prerequisites and Environment Setup

What you need:

* Python 3.7 or higher
* pip Python package manager
* A modern web browser (Chrome, Edge, Firefox, Safari)
* Local network setup for multiple-device voting

Setup steps:

1. Open a command prompt in the project’s root directory.
2. Create a virtual environment:
  * Windows: python -m venv venv
3. Activate the environment:
  * Windows PowerShell: venv\Scripts\Activate.ps1
4. Install dependencies:
  * pip install -r requirements.txt

Troubleshooting:
If you get a PowerShell script execution error, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Best practice: Dedicate one machine as the election host. Avoid installing unrelated software during election week.

---

Page 4: Project Files Explained

Core files and their roles:

* app.py: Main backend application with all API routes
* app_local.py: Local variant for some workflows
* public/index.html: The student voting interface
* public/results.html: The live results display
* public/results.js: Responsible for fetching and updating results
* public/auth-config.js: Frontend authentication settings
* auth_config.py: Backend authentication mapping
* generate_tokens.py: Generates unique tokens for voting
* verify_tokens.py: Checks validity of tokens

Documentation files:

* 00_START_HERE.md, QUICK_START.md: Getting started guides
* AUTH_GUIDE.md, AUTHENTICATION_SETUP.md: Authentication documentation
* IP_PROTECTION_GUIDE.md: Intellectual property protection
* DEPLOYMENT_CHECKLIST.md: Step-by-step deployment

Security: Treat configuration and credential files as confidential. Never share them in public channels or student groups.

---

Page 5: First Run and Smoke Test

To launch Feza Vote:

* Run python app.py

What to expect:

* Server starts (usually at http://localhost:3000)
* Voting and results pages load without errors
* All endpoints respond with valid data

Testing checklist:

1. Open the voting page—do all candidates appear?
2. Submit a test vote.
3. Open the results page—does your vote show up?
4. Refresh results—are results persistent?
5. Attempt a second vote with the same identity—system should block it.

If any test fails, resolve issues before going live.

---

Page 6: Candidate Registration and Election Setup

Before voting day:

* Define the election name, date, and position(s)
* Enter the full candidate list with accurate details
* Use consistent, official names and clear images where possible
* Double-check candidate IDs
* “Freeze” the candidate list before voting begins

Governance: Any change after voting starts must be approved and documented.

Checklist:

1. Committee signs off on candidate list
2. UI previewed on phone and laptop
3. Backend candidate count matches expectations

---

Page 7: Voter Access and Token Management

Feza Vote uses tokens for secure, one-time voter access. The system includes a script (generate_tokens.py) to create these tokens.

Token characteristics:

* Format: XXXX-XXXX (letters/digits)
* Each token is unique; “TXN” is never used
* Default: 600 tokens generated, saved to public/voters_tokens.txt

How to use:

1. Run python generate_tokens.py
2. Check output for confirmation and token count
3. Distribute tokens—one per voter, never publicly

Post-election: Archive the token file securely and mark those tokens as retired.

---

Page 8: Authentication Model (Staff Access)

Feza Vote supports role-based authentication for result dashboards:

* Developer accounts: Username and password (set in code)
* Teacher account: Customizable password

To change the teacher password:

* Edit public/auth-config.js, set teacherPassword to your chosen value, save, then reload results page.

Backend credentials: Defined in auth_config.py—this file must remain private.

Best practices:

* Use unique passwords each election
* Rotate teacher passwords
* Remove unused accounts

---

Page 9: Login Flow and Session Management

Login process for results dashboard:

1. Open results.html
2. Modal appears requesting credentials
3. Select role and enter details
4. On success, dashboard unlocks and results begin polling

Session details:

* Sessions are stored in browser sessionStorage
* Refreshing the page usually retains session
* Closing the tab may clear the session

Security tips:

* Always logout after your shift
* Do not leave monitoring screens unattended
* Use dedicated browser profiles on public machines

---

Page 10: Election Day Operations

Recommended steps:

1. Start server and verify all endpoints
2. Supervisors access dashboard on their devices
3. Open voting station pages for voters
4. Maintain a printed log of incidents and actions
5. Record opening, mid-point, and closing times

Roles:

* Technical operator: maintains server
* Queue supervisor: assists voters
* Election officer: resolves disputes
* Results monitor: checks dashboard accuracy

Rule: Never change code or credentials during active voting unless absolutely necessary.

---

Page 11: Live Results Monitoring

Treat the results dashboard as sensitive information.

Monitoring tasks:

* Ensure results refresh automatically
* Watch for unexpected count jumps or resets
* Confirm total votes match expected turnout
* Check that candidate bars/percentages are accurate

If results appear wrong:

1. Check backend API responses directly
2. Clear browser cache and reload
3. Look for duplicate browser tabs
4. Review server logs for errors

Communication: Share interim results only with authorized staff. If secrecy is required, keep display out of student view.

---

Page 12: Duplicate Vote Prevention and Integrity

Integrity mechanisms:

* Voter identity checked before voting
* Server blocks double submissions
* Vote status is checked before allowing another vote

Operational checks:

* Supervisors confirm voter identity and log incidents
* End-of-day cross-check between turnout and vote tally

Red flags:

* Sudden vote spikes
* Repeated failed attempts from one device
* Manual data edits during voting

If flagged: Pause the affected station, note the timestamp, and escalate to the committee.

---

Page 13: Admin/Reset Actions and Change Control

Reset operations:

* Only authorized staff may reset the system
* Written approval is required
* Always back up data first
* Log all resets with reason and timestamp

Change log template:

* What changed, why, who approved, who executed, when, impact

Never reset during voting without full authorization.

---

Page 14: Troubleshooting Common Issues

Page won’t load?

* Ensure server is running
* Check firewall/network settings
* Confirm devices are on the same network

Login fails?

* Verify credentials and spelling
* Remove extra spaces
* Clear browser session storage

Results not updating?

* Check browser console for script errors
* Confirm backend /api/results is responsive
* Ensure polling is active

Token rejected?

* Confirm format and usage
* Remove whitespace
* Verify token hasn’t been used

After any fix, rerun the smoke test before resuming.

---

Page 15: Security Hardening for School Elections

Essentials:

* Use strong, unique passwords
* Rotate credentials before each election
* Restrict election host access to staff
* Disable unnecessary services on the host machine
* Prefer a private local network

Data protection:

* Keep sensitive files off shared drives
* Back up before election day
* Use version control with access restrictions

Network security:

* Use HTTPS if serving outside local network
* Restrict open ports with firewall
* Monitor for unusual activity

This system is suitable for school environments. For larger or public use, add stronger authentication, audit trails, and identity checks.

---

Page 16: Backup, Recovery, and Data Retention

When to backup:

1. Before the election opens
2. At mid-point
3. After polls close

What to backup:

* Vote database/files
* Candidate list/configs
* Auth and token files
* Incident and audit logs

How to recover:

* Keep a standby machine ready
* Store backups on encrypted media
* Test restoring process in advance

Retention:

* Keep election records for at least one term (or as policy requires)
* Store in a secure, access-controlled location

---

Page 17: Deployment and Network Scenarios

Single-machine mode:

* Simplest
* Works for small elections

Multi-device LAN mode:

* Voting pages served over local network
* Multiple devices, requires good Wi-Fi or LAN

Remote/VPS mode:

* For distributed voting
* Requires advanced security
* Follow deployment checklists carefully

Always test your exact deployment one day before the event.

---


---

Page 18: Training and Pilot Elections

Why run a pilot?

* To ensure every operator knows their tasks
* To surface and fix process gaps

Pilot checklist:

1. Create a small candidate and voter set
2. Simulate a full voting cycle
3. Practice handling common failures
4. Check recovery and escalation procedures

Training outcomes:

* Staff can log in/out and monitor results
* Supervisors know escalation protocols
* Technical leads can restore from backup

If confusion remains, update guides and retrain.

---

Page 19: Final Checklist & Quick Reference

Before election:

* System installed and tested
* Candidate list finalized
* Credentials updated
* Tokens generated and distributed
* Backups tested

Opening:

* Server running
* Voting/results pages tested
* Incident log started
* Roles assigned

During voting:

* Monitor system health and results
* Log anomalies immediately
* Prohibit unauthorized config/code changes

Closing:

* Close voting window officially
* Snapshot final results
* Back up all data
* Log signed handover of results
* Archive/rotate credentials

Quick commands:

* Install: pip install -r requirements.txt
* Start: python app.py
* Tokens: python generate_tokens.py

End of Guide

---

Appendix: Recovered Documentation Summaries

(See guide body for integrated material from previously separated markdown files—authentication setup, IP protection, and core setup guidance are now included here for completeness and safety.)


prepared and authorized by : BARAKA SAIDI KIWANGA (Senior developer)