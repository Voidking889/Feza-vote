"""
One-time migration: voting_system.db (SQLite)  ->  PostgreSQL.

Usage:
    export DATABASE_URL=postgresql://feza:secret@localhost:5432/feza_vote
    python migrate_sqlite_to_pg.py [path/to/voting_system.db]

Run app_pg.py once first (or let this script do it for you by importing nothing:
it creates the schema itself), then run this BEFORE the election starts.
Safe to re-run: existing rows are skipped.
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
import os
import sqlite3
import sys

import psycopg2
from psycopg2.extras import execute_values

SQLITE_PATH = sys.argv[1] if len(sys.argv) > 1 else 'voting_system.db'
#set Databse URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('Set DATABASE_URL first')
if not os.path.exists(SQLITE_PATH):
    raise SystemExit(f'SQLite file not found: {SQLITE_PATH}')

# Reuse the exact schema from the server so both stay in sync.
import re
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_pg.py'), encoding='utf-8').read()
SCHEMA = re.search(r"SCHEMA = '''(.*?)'''", src, re.S).group(1)

lite = sqlite3.connect(SQLITE_PATH)
lite.row_factory = sqlite3.Row
pg = psycopg2.connect(DATABASE_URL)
cur = pg.cursor()
cur.execute(SCHEMA)


def rows(sql):
    return [tuple(r) for r in lite.execute(sql).fetchall()]


# 1) tokens (must come before votes: FK)
tokens = rows('SELECT token, is_spent, created_date FROM valid_tokens')
execute_values(cur, '''INSERT INTO valid_tokens (token, is_spent, created_date) VALUES %s
                       ON CONFLICT (token) DO NOTHING''',
               [(t, bool(s), d) for t, s, d in tokens],
               template='(%s, %s, COALESCE(%s::timestamptz, NOW()))')

# 2) candidates (keep original ids so votes still point at the right person)
cands = rows('''SELECT id, name, position, votes, image, slogan, student_id, registration_date FROM candidates''')
execute_values(cur, '''INSERT INTO candidates (id, name, position, votes, image, slogan, student_id, registration_date)
                       VALUES %s ON CONFLICT (id) DO NOTHING''',
               cands, template='(%s, %s, %s, %s, %s, %s, %s, COALESCE(%s::timestamptz, NOW()))')

# 3) votes
votes = rows('SELECT id, token, candidate_id, position, timestamp FROM votes')
execute_values(cur, '''INSERT INTO votes (id, token, candidate_id, position, timestamp)
                       VALUES %s ON CONFLICT DO NOTHING''',
               votes, template='(%s, %s, %s, %s, COALESCE(%s::timestamptz, NOW()))')

# 4) config + timeline
cfg = rows('SELECT key, value FROM system_config')
execute_values(cur, '''INSERT INTO system_config (key, value) VALUES %s
                       ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value''', cfg)

tl = rows('SELECT year, payload, archived_at FROM leadership_timeline')
execute_values(cur, '''INSERT INTO leadership_timeline (year, payload, archived_at) VALUES %s
                       ON CONFLICT (year) DO NOTHING''',
               tl, template='(%s, %s, COALESCE(%s::timestamptz, NOW()))')

# 5) SERIAL sequences must continue after the highest copied id
for table in ('candidates', 'votes'):
    cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"GREATEST(COALESCE((SELECT MAX(id) FROM {table}), 0), 1), "
                f"(SELECT COUNT(*) FROM {table}) > 0)")

pg.commit()
print(f'Migrated: {len(tokens)} tokens, {len(cands)} candidates, {len(votes)} votes, '
      f'{len(cfg)} config rows, {len(tl)} timeline years')
