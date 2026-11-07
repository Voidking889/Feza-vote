# Live Results Dashboard Authentication

## Overview
The live results dashboard now has authentication with two login types:

### 1. **Developer Access**
Two hardcoded developer accounts:
- **Username:** BARAKA SAID | **Password:** skynet67
- **Username:** ASHLEY CHARLES | **Password:** airwave67

### 2. **Teacher Access**
Customizable teacher password.

## How to Customize Teacher Password

### Method 1: Direct Edit (Recommended)
1. Open the file `public/auth-config.js`
2. Find this line:
   ```javascript
   teacherPassword: 'teacher123'
   ```
3. Change `'teacher123'` to your desired password, e.g.:
   ```javascript
   teacherPassword: 'YourNewPassword123'
   ```
4. Save the file
5. Reload the results page - the new password takes effect immediately

### Method 2: Programmatic Update
If you want to update the password dynamically via browser console:
```javascript
setTeacherPassword('NewPassword123');
```

## Login Flow
1. When you visit `/results.html`, the authentication modal appears
2. Choose either "Developer" or "Teacher" tab
3. Enter credentials and click Login
4. Once authenticated, the live results dashboard is visible
5. Click "Logout" in the top-right to return to login screen

## Session Persistence
- Authentication is stored in browser's `sessionStorage`
- Closing the browser tab clears the session
- Refreshing the page keeps you logged in (unless storage was cleared)

## Security Notes
- Developer credentials are hardcoded for simplicity
- Teacher password is stored client-side (frontend)
- For production use, consider backend authentication
- Credentials are visible in the source code - this is for internal/school use only

## Password Examples
Here are some password suggestion formats:
- `teacher123` (simple)
- `VoteDay2026` (with date)
- `FezaVote67` (with custom name)
- `P@ssw0rd!` (with special characters)

Choose what works best for your use case!
