"""
Feza Vote server - PostgreSQL edition.
Drop-in replacement for app_local.py (same routes, same JSON shapes).

Required env vars:
    DATABASE_URL       e.g. postgresql://feza:secret@localhost:5432/feza_vote
    ADMIN_CONTROL_KEY  admin key used by the dashboard prompts
Optional:
    PORT (default 3000), TOKEN_FILE (default public/voters_tokens.txt)
"""
import json
import logging
import os
import socket
from contextlib import contextmanager
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from time import perf_counter

import psycopg2
from psycopg2 import errors, pool
from psycopg2.extras import RealDictCursor, execute_values
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS

from auth_config import AUTH_CONFIG

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "OPTIONS"]}})

# ---------------------------------------------------------------- config
DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_CONTROL_KEY = os.environ.get('ADMIN_CONTROL_KEY')
TOKEN_FILE = os.environ.get('TOKEN_FILE', 'public/voters_tokens.txt')
LOG_PATH = os.path.join('logs', 'server.log')

if not DATABASE_URL:
    raise SystemExit('DATABASE_URL is not set (see .env.example)')
if not ADMIN_CONTROL_KEY:
    raise SystemExit('ADMIN_CONTROL_KEY is not set (see .env.example)')

DECLARATION_OPEN_TEXT = 'Election is now OPEN for voting.'
DECLARATION_CLOSED_TEXT = 'Election is now CLOSED for voting.'
ALLOWED_DECLARATIONS = {DECLARATION_OPEN_TEXT, DECLARATION_CLOSED_TEXT, ''}
ONLINE_SECONDS = 60
IDLE_SECONDS = 300
REQUEST_COUNTER = {}


# ---------------------------------------------------------------- logging
def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False


setup_logging()


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
        s.close()
        if ip != "127.0.0.1":
            return ip
    except Exception:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


LOCAL_IP = get_local_ip()

# ---------------------------------------------------------------- database layer
POOL = pool.ThreadedConnectionPool(minconn=2, maxconn=20, dsn=DATABASE_URL)


class Conn:
    """Thin wrapper so route code can call cursor()/commit()/close() like before."""

    def __init__(self, raw):
        self.raw = raw

    def cursor(self):
        return self.raw.cursor(cursor_factory=RealDictCursor)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        # Anything not committed is rolled back, then the connection returns to the pool.
        try:
            self.raw.rollback()
        finally:
            POOL.putconn(self.raw)


@contextmanager
def db():
    conn = Conn(POOL.getconn())
    try:
        yield conn
    finally:
        conn.close()


def ts(value):
    """Datetime -> 'YYYY-MM-DD HH:MM:SS' string (keeps JSON shape the frontend expects)."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def stringify_times(row):
    return {k: ts(v) for k, v in dict(row).items()}


SCHEMA = '''
CREATE TABLE IF NOT EXISTS candidates (
    id                SERIAL PRIMARY KEY,
    name              TEXT NOT NULL,
    position          TEXT NOT NULL CHECK (position IN ('president', 'vice_president')),
    votes             INTEGER NOT NULL DEFAULT 0,
    image             TEXT,
    slogan            TEXT,
    student_id        TEXT UNIQUE NOT NULL,
    registration_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS valid_tokens (
    token        TEXT PRIMARY KEY,
    is_spent     BOOLEAN NOT NULL DEFAULT FALSE,
    created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS votes (
    id           SERIAL PRIMARY KEY,
    token        TEXT NOT NULL REFERENCES valid_tokens(token),
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    position     TEXT NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (token, position)          -- one vote per position per token, enforced by the DB
);

CREATE TABLE IF NOT EXISTS system_config (
    key          TEXT PRIMARY KEY,
    value        TEXT,
    updated_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leadership_timeline (
    year        INTEGER PRIMARY KEY,
    payload     TEXT NOT NULL,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS active_clients (
    id            SERIAL PRIMARY KEY,
    ip_address    TEXT NOT NULL,
    username      TEXT NOT NULL DEFAULT 'Anonymous',
    user_role     TEXT NOT NULL DEFAULT 'unknown',
    user_agent    TEXT DEFAULT '',
    first_seen    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_count INTEGER NOT NULL DEFAULT 1,
    last_path     TEXT DEFAULT '',
    UNIQUE (ip_address, username, user_role)
);

CREATE INDEX IF NOT EXISTS idx_active_clients_last_seen ON active_clients(last_seen);
CREATE INDEX IF NOT EXISTS idx_votes_candidate ON votes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_position_votes ON candidates(position, votes DESC);
'''


def init_db():
    with db() as conn:
        c = conn.cursor()
        c.execute(SCHEMA)
        for key, value in (('election_open', '1'), ('winner_declaration', ''), ('election_closed_at', '')):
            c.execute('INSERT INTO system_config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING',
                      (key, value))
        conn.commit()


def load_tokens_from_file():
    if not os.path.exists(TOKEN_FILE):
        return 0
    try:
        with open(TOKEN_FILE, 'r') as f:
            parts = f.read().replace('\n', ',').split(',')
        tokens = sorted({p.strip() for p in parts if p.strip()})
        if not tokens:
            return 0
        with db() as conn:
            c = conn.cursor()
            execute_values(c, 'INSERT INTO valid_tokens (token) VALUES %s ON CONFLICT (token) DO NOTHING',
                           [(t,) for t in tokens])
            conn.commit()
        return len(tokens)
    except Exception as e:
        print(f'Error loading tokens: {e}')
        return 0


# ---------------------------------------------------------------- helpers
def get_system_config(conn, key, default=''):
    c = conn.cursor()
    c.execute('SELECT value FROM system_config WHERE key = %s', (key,))
    row = c.fetchone()
    return row['value'] if row else default


def set_system_config(conn, key, value):
    c = conn.cursor()
    c.execute('''INSERT INTO system_config (key, value, updated_date) VALUES (%s, %s, NOW())
                 ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_date = NOW()''',
              (key, value))


def candidate_to_dict(row):
    return {
        'id': row['id'],
        'name': row['name'],
        'position': row['position'],
        'votes': row['votes'],
        'image': row['image'],
        'slogan': row['slogan'],
        'studentId': row['student_id'],
        'registrationDate': ts(row['registration_date'])
    }


def fetch_candidates(conn, order='position, votes DESC, id ASC'):
    c = conn.cursor()
    c.execute(f'''SELECT id, name, position, votes, image, slogan, student_id, registration_date
                  FROM candidates ORDER BY {order}''')
    return [candidate_to_dict(r) for r in c.fetchall()]


def build_election_state(conn):
    return {
        'isOpen': get_system_config(conn, 'election_open', '1') == '1',
        'winnerDeclaration': get_system_config(conn, 'winner_declaration', '') or '',
        'closedAt': get_system_config(conn, 'election_closed_at', '') or None
    }


def build_timeline_snapshot(conn, archive_year=None):
    contestants = fetch_candidates(conn, order='position ASC, votes DESC, name ASC')
    if not contestants:
        return None

    presidents = [x for x in contestants if x['position'] == 'president']
    vices = [x for x in contestants if x['position'] == 'vice_president']
    state = build_election_state(conn)

    year = archive_year
    if year is None:
        year = int(str(state['closedAt'])[:4]) if state.get('closedAt') else datetime.now().year

    return {
        'year': int(year),
        'archivedAt': datetime.now().isoformat(),
        'election': state,
        'leaders': {
            'president': presidents[0] if presidents else None,
            'vice_president': vices[0] if vices else None
        },
        'totals': {
            'presidentVotes': sum(x['votes'] for x in presidents),
            'vicePresidentVotes': sum(x['votes'] for x in vices),
            'contestants': len(contestants)
        },
        'contestants': contestants
    }


def archive_current_election(conn, archive_year=None):
    snapshot = build_timeline_snapshot(conn, archive_year=archive_year)
    if not snapshot:
        return None
    c = conn.cursor()
    c.execute('''INSERT INTO leadership_timeline (year, payload, archived_at) VALUES (%s, %s, NOW())
                 ON CONFLICT (year) DO UPDATE SET payload = EXCLUDED.payload, archived_at = NOW()''',
              (snapshot['year'], json.dumps(snapshot)))
    return snapshot


def restore_latest_timeline_snapshot(conn):
    c = conn.cursor()
    c.execute('SELECT payload, year FROM leadership_timeline ORDER BY archived_at DESC, year DESC LIMIT 1')
    row = c.fetchone()
    if not row:
        return None

    data = json.loads(row['payload'])
    contestants = data.get('contestants') if isinstance(data.get('contestants'), list) else []
    if not contestants:
        return None

    c.execute('TRUNCATE votes, candidates RESTART IDENTITY')
    c.execute('UPDATE valid_tokens SET is_spent = FALSE')

    used_ids = set()
    restored = 0
    for idx, cand in enumerate(contestants, start=1):
        position = (cand.get('position') or '').strip()
        if position not in ('president', 'vice_president'):
            continue
        student_id = (cand.get('studentId') or '').strip()
        if not student_id or student_id in used_ids:
            student_id = f"restored-{row['year']}-{idx}"
        used_ids.add(student_id)

        c.execute('''INSERT INTO candidates (name, position, votes, image, slogan, student_id, registration_date)
                     VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s::timestamptz, NOW()))''',
                  ((cand.get('name') or 'Unknown').strip(), position, int(cand.get('votes') or 0),
                   cand.get('image') or '', cand.get('slogan') or '', student_id,
                   cand.get('registrationDate') or None))
        restored += 1

    election = data.get('election', {}) if isinstance(data.get('election'), dict) else {}
    set_system_config(conn, 'winner_declaration', (election.get('winnerDeclaration') or '').strip())
    set_system_config(conn, 'election_closed_at', '')
    return {'year': int(data.get('year') or row['year']), 'contestantsRestored': restored}


def require_admin_key(data):
    return (data or {}).get('adminKey', '').strip() == ADMIN_CONTROL_KEY


def get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def track_request_metrics(ip, path, status_code, duration_ms):
    stats = REQUEST_COUNTER.setdefault(ip, {
        'count': 0, 'apiCount': 0, 'errors': 0, 'lastPath': '', 'lastStatus': 0,
        'lastDurationMs': 0, 'firstSeen': datetime.now().isoformat(), 'lastSeen': ''
    })
    stats['count'] += 1
    if path.startswith('/api/'):
        stats['apiCount'] += 1
    if status_code >= 400:
        stats['errors'] += 1
    stats['lastPath'] = path
    stats['lastStatus'] = int(status_code)
    stats['lastDurationMs'] = int(duration_ms)
    stats['lastSeen'] = datetime.now().isoformat()


def normalize_role(raw):
    role = (raw or '').strip().lower()
    return role if role in ('developer', 'teacher', 'public') else 'unknown'


def to_device_status(last_seen_dt):
    if last_seen_dt.tzinfo is None:
        last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
    age = max(0, int((datetime.now(timezone.utc) - last_seen_dt).total_seconds()))
    if age <= ONLINE_SECONDS:
        return 'online', age
    if age <= IDLE_SECONDS:
        return 'idle', age
    return 'offline', age


def upsert_client_activity(conn, username='Anonymous', user_role='unknown', path=''):
    c = conn.cursor()
    c.execute('''INSERT INTO active_clients (ip_address, username, user_role, user_agent, last_path)
                 VALUES (%s, %s, %s, %s, %s)
                 ON CONFLICT (ip_address, username, user_role) DO UPDATE SET
                     user_agent = EXCLUDED.user_agent,
                     last_seen = NOW(),
                     request_count = active_clients.request_count + 1,
                     last_path = EXCLUDED.last_path''',
              (get_client_ip(),
               (username or 'Anonymous').strip()[:120] or 'Anonymous',
               normalize_role(user_role),
               (request.headers.get('User-Agent') or '')[:255],
               (path or request.path or '')[:255]))


def is_developer_request():
    role_header = (request.headers.get('X-Auth-Role') or '').strip().lower()
    role_query = (request.args.get('role') or '').strip().lower()
    role_body = normalize_role((request.get_json(silent=True) or {}).get('role', ''))
    return 'developer' in (role_header, role_query, role_body)


# ---------------------------------------------------------------- startup
init_db()
tokens_loaded = load_tokens_from_file()
print('[DATABASE] Connected to PostgreSQL, schema ready')
print(f'[DATABASE] Loaded {tokens_loaded} tokens from file')


# ---------------------------------------------------------------- request hooks
@app.before_request
def start_request_timer():
    if request.path.startswith('/api/'):
        g.request_started_at = perf_counter()


@app.after_request
def log_api_response(response):
    ip = get_client_ip()
    started = getattr(g, 'request_started_at', None)
    duration_ms = int((perf_counter() - started) * 1000) if started else -1
    track_request_metrics(ip, request.path, response.status_code, duration_ms)

    if not request.path.startswith('/api/'):
        return response
    if request.path == '/api/heartbeat' and response.status_code < 400 and duration_ms < 1000:
        return response

    log = app.logger.warning if response.status_code >= 400 else app.logger.info
    log('%s %s -> %s in %sms | ip=%s', request.method, request.path, response.status_code, duration_ms, ip)
    return response


# ================================================================ API ROUTES
@app.route('/api/login', methods=['GET', 'POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    if request.method == 'GET':
        return jsonify({'error': 'Method Not Allowed. Use POST.'}), 405

    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    def record(user):
        try:
            with db() as conn:
                upsert_client_activity(conn, user, role, request.path)
                conn.commit()
        except Exception:
            pass

    if role == 'public':
        record(username or 'Public User')
        return jsonify({'success': True, 'user': username or 'Public User', 'role': 'public'})

    if role in ('developer', 'teacher'):
        group = 'developers' if role == 'developer' else 'teachers'
        creds = AUTH_CONFIG.get(group, {})
        if username in creds and creds[username] == password:
            record(username)
            return jsonify({'success': True, 'user': username, 'role': role})

    return jsonify({'success': False, 'message': 'wrong username or password'}), 401


@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json(silent=True) or {}
        with db() as conn:
            upsert_client_activity(
                conn,
                username=data.get('user') or data.get('username') or 'Anonymous',
                user_role=data.get('role') or data.get('userRole') or 'unknown',
                path=data.get('path') or request.path)
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/connected-devices', methods=['GET'])
def connected_devices():
    try:
        if not is_developer_request():
            return jsonify({'error': 'Developer access required'}), 403

        with db() as conn:
            c = conn.cursor()
            c.execute('''SELECT ip_address, username, user_role, user_agent, first_seen, last_seen,
                                request_count, last_path
                         FROM active_clients ORDER BY last_seen DESC''')
            rows = c.fetchall()

        devices, counts = [], {'online': 0, 'idle': 0, 'offline': 0}
        for row in rows:
            status, age = to_device_status(row['last_seen'])
            counts[status] += 1
            devices.append({
                'ip': row['ip_address'],
                'username': row['username'],
                'role': row['user_role'],
                'status': status,
                'lastSeen': ts(row['last_seen']),
                'ageSeconds': age,
                'firstSeen': ts(row['first_seen']),
                'requestCount': int(row['request_count'] or 0),
                'lastPath': row['last_path'] or '',
                'userAgent': row['user_agent'] or ''
            })

        return jsonify({'summary': {'total': len(devices), **counts}, 'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/request-metrics', methods=['GET'])
def request_metrics():
    try:
        if not is_developer_request():
            return jsonify({'error': 'Developer access required'}), 403
        items = [{
            'ip': ip,
            'count': int(s.get('count', 0)),
            'apiCount': int(s.get('apiCount', 0)),
            'errors': int(s.get('errors', 0)),
            'lastPath': s.get('lastPath', ''),
            'lastStatus': int(s.get('lastStatus', 0)),
            'lastDurationMs': int(s.get('lastDurationMs', 0)),
            'firstSeen': s.get('firstSeen', ''),
            'lastSeen': s.get('lastSeen', '')
        } for ip, s in REQUEST_COUNTER.items()]
        items.sort(key=lambda i: i['count'], reverse=True)
        return jsonify({'totalIps': len(items), 'requests': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/register.html')
def register():
    return send_from_directory('public', 'register.html')


@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    try:
        with db() as conn:
            return jsonify(fetch_candidates(conn))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/candidates/register', methods=['POST'])
def register_candidate():
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        position = data.get('position', '').strip()
        image = data.get('image', '').strip()
        student_id = data.get('studentId', '').strip()
        slogan = data.get('slogan', '').strip()

        if not all([name, position, student_id, image]):
            return jsonify({'error': 'Missing required fields'}), 400
        if position not in ('president', 'vice_president'):
            return jsonify({'error': 'Invalid position'}), 400
        if not image.startswith('data:image/'):
            return jsonify({'error': 'Invalid image format'}), 400

        with db() as conn:
            c = conn.cursor()
            try:
                c.execute('''INSERT INTO candidates (name, position, image, slogan, student_id)
                             VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                          (name, position, image, slogan, student_id))
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({'error': 'Student ID already registered'}), 400
            candidate_id = c.fetchone()['id']
            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Candidate registered successfully',
            'candidate': {'id': candidate_id, 'name': name, 'position': position,
                          'votes': 0, 'image': image, 'slogan': slogan}
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/candidates/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        position = data.get('position', '').strip()
        image = data.get('image', '').strip()
        student_id = data.get('studentId', '').strip()
        slogan = data.get('slogan', '').strip()

        if not all([name, position, student_id, image]):
            return jsonify({'error': 'Missing required fields'}), 400
        if position not in ('president', 'vice_president'):
            return jsonify({'error': 'Invalid position'}), 400
        if not image.startswith('data:image/'):
            return jsonify({'error': 'Invalid image format'}), 400

        with db() as conn:
            c = conn.cursor()
            try:
                c.execute('''UPDATE candidates
                             SET name = %s, position = %s, image = %s, slogan = %s, student_id = %s
                             WHERE id = %s
                             RETURNING id, name, position, votes, image, slogan, student_id, registration_date''',
                          (name, position, image, slogan, student_id, candidate_id))
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({'error': 'Student ID already registered'}), 400
            row = c.fetchone()
            if not row:
                return jsonify({'error': 'Candidate not found'}), 404
            conn.commit()

        return jsonify({'success': True, 'message': 'Candidate updated successfully',
                        'candidate': candidate_to_dict(row)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vote', methods=['POST'])
def submit_vote():
    try:
        data = request.get_json() or {}
        candidate_id = data.get('candidateId')
        position = data.get('position')
        token = data.get('token')

        if not all([candidate_id, position, token]):
            return jsonify({'error': 'Missing required fields'}), 400
        if position not in ('president', 'vice_president'):
            return jsonify({'error': 'Invalid position'}), 400

        with db() as conn:
            c = conn.cursor()

            if get_system_config(conn, 'election_open', '1') != '1':
                return jsonify({'error': 'Election is closed. Voting is disabled.'}), 403

            # Lock this token's row so two simultaneous requests can't both slip through.
            c.execute('SELECT is_spent FROM valid_tokens WHERE token = %s FOR UPDATE', (token,))
            token_row = c.fetchone()
            if not token_row:
                return jsonify({'error': 'Invalid token'}), 403
            if token_row['is_spent']:
                return jsonify({'error': 'Token already used for both positions'}), 403

            c.execute('SELECT id, name, position FROM candidates WHERE id = %s', (candidate_id,))
            candidate = c.fetchone()
            if not candidate:
                return jsonify({'error': 'Candidate not found'}), 404
            if candidate['position'] != position:
                return jsonify({'error': f'Candidate not registered for {position}'}), 400

            try:
                c.execute('INSERT INTO votes (token, candidate_id, position) VALUES (%s, %s, %s)',
                          (token, candidate_id, position))
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({'error': f'Already voted for {position}'}), 403

            c.execute('UPDATE candidates SET votes = votes + 1 WHERE id = %s', (candidate_id,))

            c.execute('SELECT COUNT(DISTINCT position) AS n FROM votes WHERE token = %s', (token,))
            if c.fetchone()['n'] >= 2:
                c.execute('UPDATE valid_tokens SET is_spent = TRUE WHERE token = %s', (token,))

            conn.commit()

        return jsonify({'success': True, 'message': 'Vote submitted successfully',
                        'candidate': candidate['name']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tokens', methods=['GET'])
def get_all_tokens():
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('''SELECT t.token, t.is_spent,
                                COALESCE(ARRAY_AGG(DISTINCT v.position)
                                         FILTER (WHERE v.position IS NOT NULL), '{}') AS positions
                         FROM valid_tokens t
                         LEFT JOIN votes v ON v.token = t.token
                         GROUP BY t.token, t.is_spent
                         ORDER BY t.token ASC''')
            rows = c.fetchall()

        tokens = [{'token': r['token'], 'isSpent': bool(r['is_spent']),
                   'votedPositions': list(r['positions'])} for r in rows]
        spent = sum(1 for t in tokens if t['isSpent'])
        return jsonify({'total': len(tokens), 'spent': spent,
                        'remaining': len(tokens) - spent, 'tokens': tokens})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-token/<token>', methods=['GET'])
def check_token(token):
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('SELECT is_spent FROM valid_tokens WHERE token = %s', (token,))
            row = c.fetchone()
            if not row:
                return jsonify({'isValid': False, 'isSpent': False, 'votedPositions': []})
            c.execute('SELECT DISTINCT position FROM votes WHERE token = %s', (token,))
            positions = [r['position'] for r in c.fetchall()]
        return jsonify({'isValid': True, 'isSpent': bool(row['is_spent']), 'votedPositions': positions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        with db() as conn:
            c = conn.cursor()
            out = {}
            for position in ('president', 'vice_president'):
                c.execute('''SELECT id, name, position, votes, image, slogan
                             FROM candidates WHERE position = %s ORDER BY votes DESC, id ASC''', (position,))
                rows = [dict(r) for r in c.fetchall()]
                out[position] = {'candidates': rows, 'totalVotes': sum(r['votes'] for r in rows)}
            out['election'] = build_election_state(conn)
        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_votes():
    """Reset all votes (admin key now required)."""
    try:
        if not require_admin_key(request.get_json(silent=True) or {}):
            return jsonify({'error': 'Invalid admin key'}), 403
        with db() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM votes')
            c.execute('UPDATE candidates SET votes = 0')
            c.execute('UPDATE valid_tokens SET is_spent = FALSE')
            conn.commit()
        return jsonify({'success': True, 'message': 'System reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election-state', methods=['GET'])
def election_state():
    try:
        with db() as conn:
            return jsonify(build_election_state(conn))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election/close', methods=['POST'])
def close_election():
    try:
        if not require_admin_key(request.get_json() or {}):
            return jsonify({'error': 'Invalid admin key'}), 403
        with db() as conn:
            set_system_config(conn, 'election_open', '0')
            set_system_config(conn, 'election_closed_at', datetime.now().isoformat())
            conn.commit()
            state = build_election_state(conn)
        return jsonify({'success': True,
                        'message': 'Election temporarily closed. Voting is disabled, contestants are preserved.',
                        'state': state})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election/reopen', methods=['POST'])
def reopen_election():
    try:
        if not require_admin_key(request.get_json() or {}):
            return jsonify({'error': 'Invalid admin key'}), 403
        with db() as conn:
            set_system_config(conn, 'election_open', '1')
            set_system_config(conn, 'election_closed_at', '')
            conn.commit()
            state = build_election_state(conn)
        return jsonify({'success': True,
                        'message': 'Election resumed. Voting is enabled and data was preserved.',
                        'state': state})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election/reopen-reset', methods=['POST'])
def reopen_election_reset():
    try:
        if not require_admin_key(request.get_json() or {}):
            return jsonify({'error': 'Invalid admin key'}), 403
        with db() as conn:
            c = conn.cursor()
            archived = archive_current_election(conn)
            c.execute('TRUNCATE votes, candidates RESTART IDENTITY')
            c.execute('UPDATE valid_tokens SET is_spent = FALSE')
            set_system_config(conn, 'election_open', '1')
            set_system_config(conn, 'winner_declaration', '')
            set_system_config(conn, 'election_closed_at', '')
            conn.commit()          # archive + wipe happen in ONE transaction
            state = build_election_state(conn)
        return jsonify({'success': True,
                        'message': 'Voting re-opened and system fully refreshed. All candidates were removed.',
                        'state': state, 'timelineArchived': bool(archived)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election/restore-latest', methods=['POST'])
def restore_latest_election_snapshot():
    try:
        if not require_admin_key(request.get_json() or {}):
            return jsonify({'error': 'Invalid admin key'}), 403
        with db() as conn:
            restored = restore_latest_timeline_snapshot(conn)
            if not restored:
                return jsonify({'error': 'No archived snapshot available to restore.'}), 404
            set_system_config(conn, 'election_open', '1')
            conn.commit()
            state = build_election_state(conn)
        return jsonify({'success': True, 'message': 'Latest archived data restored. Voting resumed.',
                        'state': state, 'restored': restored,
                        'note': 'Token-level spent state and per-token vote history cannot be '
                                'reconstructed from timeline archive.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leadership-timeline/years', methods=['GET'])
def get_timeline_years():
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('SELECT year, archived_at FROM leadership_timeline ORDER BY year DESC')
            rows = c.fetchall()
        return jsonify({'years': [r['year'] for r in rows],
                        'items': [{'year': r['year'], 'archivedAt': ts(r['archived_at'])} for r in rows]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leadership-timeline/<int:year>', methods=['GET'])
def get_timeline_year(year):
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('SELECT payload, archived_at FROM leadership_timeline WHERE year = %s', (year,))
            row = c.fetchone()
        if not row:
            return jsonify({'error': 'No timeline data found for selected year'}), 404
        payload = json.loads(row['payload'])
        payload['archivedAt'] = payload.get('archivedAt') or ts(row['archived_at'])
        return jsonify(payload)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/leadership-history', methods=['GET'])
def get_leadership_history_legacy():
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('SELECT payload FROM leadership_timeline ORDER BY year DESC')
            rows = c.fetchall()

        history = []
        for row in rows:
            data = json.loads(row['payload'])
            leaders = data.get('leaders', {})
            president = leaders.get('president') or {}
            vice = leaders.get('vice_president') or {}
            totals = data.get('totals', {})
            history.append({
                'year': data.get('year'),
                'presidentName': president.get('name', 'N/A'),
                'presidentPhoto': president.get('image', ''),
                'vicePresidentName': vice.get('name', 'N/A'),
                'vicePresidentPhoto': vice.get('image', ''),
                'presidentVotes': int(president.get('votes', 0)),
                'vicePresidentVotes': int(vice.get('votes', 0)),
                'votesWon': int(president.get('votes', 0)),
                'totalVotes': int(totals.get('presidentVotes', 0)) + int(totals.get('vicePresidentVotes', 0)),
                'winnerDeclaration': (data.get('election', {}) or {}).get('winnerDeclaration', ''),
                'contestants': data.get('contestants', []),
                'totalContestants': int(totals.get('contestants', 0)),
                'archivedAt': data.get('archivedAt')
            })
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/election/winner', methods=['POST'])
def set_winner_declaration():
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403
        declaration = (data.get('declaration') or '').strip()
        if declaration not in ALLOWED_DECLARATIONS:
            return jsonify({'error': 'Invalid declaration. Use one of the pre-made declaration statements.'}), 400
        with db() as conn:
            set_system_config(conn, 'winner_declaration', declaration)
            conn.commit()
            state = build_election_state(conn)
        return jsonify({'success': True, 'message': 'Winner declaration saved.', 'state': state})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/system-info', methods=['GET'])
def system_info():
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('''SELECT (SELECT COUNT(*) FROM candidates) AS candidates,
                                (SELECT COUNT(*) FROM votes) AS votes,
                                (SELECT COUNT(*) FROM valid_tokens) AS tokens,
                                (SELECT COUNT(*) FROM valid_tokens WHERE is_spent) AS spent''')
            s = c.fetchone()
        port = os.environ.get('PORT', 3000)
        return jsonify({
            'serverType': 'Localized Voting System',
            'version': '3.0',
            'database': 'PostgreSQL',
            'localIP': LOCAL_IP,
            'port': port,
            'accessURL': f'http://{LOCAL_IP}:{port}',
            'stats': {'totalCandidates': s['candidates'], 'totalVotes': s['votes'],
                      'totalTokens': s['tokens'], 'spentTokens': s['spent'],
                      'remainingTokens': s['tokens'] - s['spent']}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-data', methods=['GET'])
def export_data():
    try:
        with db() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM candidates ORDER BY id')
            candidates = [stringify_times(r) for r in c.fetchall()]
            c.execute('SELECT * FROM votes ORDER BY id')
            votes = [stringify_times(r) for r in c.fetchall()]
            c.execute('SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_spent) AS spent FROM valid_tokens')
            t = c.fetchone()
        return jsonify({
            'exportDate': datetime.now().isoformat(),
            'candidates': candidates,
            'votes': votes,
            'tokenStats': {'total': t['total'], 'spent': t['spent'], 'remaining': t['total'] - t['spent']}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/<path:filename>')
def serve_static(filename):
    if filename.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    try:
        return send_from_directory('public', filename)
    except Exception:
        return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f'[VOTING SYSTEM] Feza Vote v3.0 (PostgreSQL)')
    print(f'  Local:   http://localhost:{port}')
    print(f'  Network: http://{LOCAL_IP}:{port}')
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
