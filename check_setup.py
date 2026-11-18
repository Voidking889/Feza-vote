"""
Diagnose "admin key / passwords not working".  Run in the project folder:
    python check_setup.py
It never prints your secrets. Passwords/keys you type are hidden.
"""
import getpass
import json
import os
import sys
import urllib.request
from pathlib import Path

here = Path(__file__).resolve().parent
print(f'\nFolder being checked: {here}\n')


def ok(msg): print(f'  [OK]   {msg}')
def bad(msg): print(f'  [FIX]  {msg}')
def info(msg): print(f'  [i]    {msg}')


# 1. Which server files exist
print('1) Server files')
for name in ('app.py', 'app_local.py', 'app_pg.py'):
    (ok if (here / name).exists() else info)(f'{name}: {"present" if (here / name).exists() else "not here"}')
info('You must start the server with:  python app_pg.py   (app_local.py has the key 12345 hard-coded)')

# 2. auth_config.py version
print('\n2) auth_config.py')
ac = here / 'auth_config.py'
if not ac.exists():
    bad('auth_config.py is missing from this folder')
else:
    text = ac.read_text(encoding='utf-8', errors='ignore')
    if 'AUTH_CONFIG_JSON' in text:
        ok('new version (reads AUTH_CONFIG_JSON)')
    else:
        bad('OLD version with hard-coded passwords. This is why old passwords still work. '
            'Replace it with the new auth_config.py')

# 3. .env file
print('\n3) .env file')
env_path = here / '.env'
if (here / '.env.txt').exists():
    bad('Found ".env.txt". Rename it to exactly ".env"')
if not env_path.exists():
    bad('.env not found in this folder')
    env = {}
else:
    ok('.env found')
    env = {}
    for line in env_path.read_text(encoding='utf-8-sig', errors='ignore').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"\'')
    for key in ('DATABASE_URL', 'ADMIN_CONTROL_KEY', 'AUTH_CONFIG_JSON'):
        (ok if env.get(key) else bad)(f'{key} {"set in .env" if env.get(key) else "MISSING in .env"}')
    raw = env_path.read_text(encoding='utf-8-sig', errors='ignore')
    if 'ADMIN_CONTROL_KEY =' in raw or 'AUTH_CONFIG_JSON =' in raw:
        bad('Remove the spaces around "=" in .env')

# 4. Stale terminal variables that override .env
print('\n4) Old values stuck in your terminal')
stale = False
for key in ('ADMIN_CONTROL_KEY', 'AUTH_CONFIG_JSON', 'DATABASE_URL'):
    if key in os.environ and env.get(key) and os.environ[key].strip().strip('"\'') != env[key]:
        stale = True
        bad(f'{key} is set in this terminal/Windows and DIFFERS from .env. '
            f'Close the terminal (or clear it) and open a new one')
if not stale:
    ok('no conflicting terminal variables')

# 5. Test the actual secrets
print('\n5) Test your secrets (typing is hidden)')
cfg = {}
try:
    cfg = json.loads(env.get('AUTH_CONFIG_JSON', ''))
    ok(f'AUTH_CONFIG_JSON is valid: {len(cfg.get("developers", {}))} developers, '
       f'{len(cfg.get("teachers", {}))} teachers')
except Exception as e:
    bad(f'AUTH_CONFIG_JSON in .env is not valid JSON ({e}). It must be ONE line.')

if cfg:
    user = input('  Username to test (Enter to skip): ').strip()
    if user:
        pw = getpass.getpass('  Its password: ')
        found = [g for g in ('developers', 'teachers') if cfg.get(g, {}).get(user) == pw]
        (ok if found else bad)(f'login {"matches (" + found[0] + ")" if found else "does NOT match .env"}')

if env.get('ADMIN_CONTROL_KEY'):
    typed = getpass.getpass('  Admin key to test (Enter to skip): ').strip()
    if typed:
        (ok if typed == env['ADMIN_CONTROL_KEY'] else bad)(
            'admin key ' + ('matches .env' if typed == env['ADMIN_CONTROL_KEY'] else
                            f'does NOT match .env (yours is {len(typed)} chars, .env has {len(env["ADMIN_CONTROL_KEY"])})'))

# 6. Which server is actually running right now?
print('\n6) Server currently running on port 3000')
try:
    data = json.load(urllib.request.urlopen('http://localhost:3000/api/system-info', timeout=3))
    db = data.get('database', '?')
    if 'PostgreSQL' in db:
        ok('app_pg.py is running (PostgreSQL)')
    else:
        bad(f'An OLD server is running (database: {db}). Stop it (Ctrl+C in its window, or close '
            f'all Python windows), then start: python app_pg.py')
except Exception:
    info('nothing answering on localhost:3000 (fine if the server is stopped)')
    info('If you get a 404 on /api/system-info while running, that is the very old app.py')

print('\nDone.\n')
