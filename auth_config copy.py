# Server-side authentication configuration.
# SAFE TO COMMIT: contains no passwords. Users come from the AUTH_CONFIG_JSON
# environment variable (set it in .env locally and in Render's dashboard).
#
# Expected shape (single line):
#   {"developers": {"NAME": "password"}, "teachers": {"NAME": "password"}}
import json
import os

_raw = os.environ.get('AUTH_CONFIG_JSON', '').strip()

if not _raw:
    raise SystemExit(
        'AUTH_CONFIG_JSON is not set. Run `python make_auth_json.py`, '
        'then paste the printed line into .env (and into Render).'
    )

try:
    AUTH_CONFIG = json.loads(_raw)
except json.JSONDecodeError as e:
    raise SystemExit(f'AUTH_CONFIG_JSON is not valid JSON: {e}. It must be ONE line, no extra quotes around it.')

for _group in ('developers', 'teachers'):
    if not isinstance(AUTH_CONFIG.get(_group), dict):
        raise SystemExit(f'AUTH_CONFIG_JSON must contain a "{_group}" object.')
