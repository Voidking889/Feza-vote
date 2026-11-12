"""
Generate fresh random passwords for every user and print:
  1) the AUTH_CONFIG_JSON line to paste into .env / Render
  2) a plain list of who got which password (hand these out, then close the terminal)

Edit the name lists below if staff change. Run:  python make_auth_json.py
"""
import json
import secrets
import string

DEVELOPERS = ['BARAKA67', 'ASHLEYDVP']
TEACHERS = ['AZAMATFB', 'SABRIFB', 'SAIDFB', 'SANGAFB', 'HAJISUDI', 'IBRAHIMFB', 'MAIRAMBEKFB']

ALPHABET = string.ascii_letters + string.digits


def new_password(length=12):
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))


config = {
    'developers': {name: new_password() for name in DEVELOPERS},
    'teachers': {name: new_password() for name in TEACHERS},
}

print('\n=== Paste this ONE line into .env and into Render ===\n')
print('AUTH_CONFIG_JSON=' + json.dumps(config, separators=(',', ':')))

print('\n=== Who gets which password (share privately) ===\n')
for group, users in config.items():
    for name, pw in users.items():
        print(f'{group[:-1]:10} {name:14} {pw}')
print()
