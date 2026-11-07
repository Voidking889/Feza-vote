from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from auth_config import AUTH_CONFIG
import os
import sqlite3
import json
from datetime import datetime
from functools import wraps
import socket
import logging
from logging.handlers import RotatingFileHandler
from time import perf_counter

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "OPTIONS"]}})

# Database path
DB_PATH = 'voting_system.db'
DB_TIMEOUT_SECONDS = 15
LOG_PATH = os.path.join('logs', 'server.log')
ADMIN_CONTROL_KEY = '12345'
DECLARATION_OPEN_TEXT = 'Election is now OPEN for voting.'
DECLARATION_CLOSED_TEXT = 'Election is now CLOSED for voting.'
ALLOWED_DECLARATIONS = {DECLARATION_OPEN_TEXT, DECLARATION_CLOSED_TEXT, ''}
ONLINE_SECONDS = 60
IDLE_SECONDS = 300
CANDIDATES_CACHE = {
    'data': None,
    'dirty': True
}
REQUEST_COUNTER = {}

def setup_logging():
    """Configure lightweight rotating server logs."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    if not any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

setup_logging()

# Get local IP address for LAN access
def get_local_ip():
    """Determine the LAN IP address, even when offline."""
    # Method 1: Try connecting to a dummy address (standard way)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use a non-routable IP to determine the local interface
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
        s.close()
        if ip != "127.0.0.1":
            return ip
    except:
        pass

    # Method 2: Fallback to hostname-based lookup
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

@app.before_request
def start_request_timer():
    if request.path.startswith('/api/'):
        g.request_started_at = perf_counter()

@app.after_request
def log_api_response(response):
    client_ip = get_client_ip()
    started_at = getattr(g, 'request_started_at', None)
    duration_ms = int((perf_counter() - started_at) * 1000) if started_at else -1
    track_request_metrics(client_ip, request.path, response.status_code, duration_ms)

    if not request.path.startswith('/api/'):
        return response

    if request.path == '/api/heartbeat' and response.status_code < 400 and duration_ms < 1000:
        return response

    log_method = app.logger.warning if response.status_code >= 400 else app.logger.info
    log_method(
        '%s %s -> %s in %sms | ip=%s',
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        client_ip
    )
    return response

@app.teardown_request
def log_request_exception(error):
    if error is None or not request.path.startswith('/api/'):
        return

    started_at = getattr(g, 'request_started_at', None)
    duration_ms = int((perf_counter() - started_at) * 1000) if started_at else -1
    app.logger.exception(
        'Unhandled exception on %s %s after %sms | ip=%s',
        request.method,
        request.path,
        duration_ms,
        get_client_ip()
    )

def configure_sqlite_connection(conn):
    """Apply SQLite settings that reduce lock contention under polling traffic."""
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = NORMAL')
    conn.execute(f'PRAGMA busy_timeout = {DB_TIMEOUT_SECONDS * 1000}')
    return conn

# Initialize database
def init_db():
    """Initialize SQLite database with required tables"""
    conn = configure_sqlite_connection(sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS))
    c = conn.cursor()
    
    # Candidates table
    c.execute('''CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT NOT NULL,
        votes INTEGER DEFAULT 0,
        image TEXT,
        slogan TEXT,
        student_id TEXT UNIQUE NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Votes table (track each vote)
    c.execute('''CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        candidate_id INTEGER NOT NULL,
        position TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id)
    )''')
    
    # Valid tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS valid_tokens (
        token TEXT PRIMARY KEY,
        is_spent INTEGER DEFAULT 0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # System config table (for metadata)
    c.execute('''CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Leadership timeline archive (persistent historical snapshots by year)
    c.execute('''CREATE TABLE IF NOT EXISTS leadership_timeline (
        year INTEGER PRIMARY KEY,
        payload TEXT NOT NULL,
        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Active client/device activity tracking
    c.execute('''CREATE TABLE IF NOT EXISTS active_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT NOT NULL,
        username TEXT NOT NULL DEFAULT 'Anonymous',
        user_role TEXT NOT NULL DEFAULT 'unknown',
        user_agent TEXT DEFAULT '',
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        request_count INTEGER DEFAULT 1,
        last_path TEXT DEFAULT '',
        UNIQUE(ip_address, username, user_role)
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_active_clients_last_seen ON active_clients(last_seen)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_votes_token_position ON votes(token, position)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_candidates_position_votes ON candidates(position, votes DESC)')

    # System defaults
    c.execute('''INSERT OR IGNORE INTO system_config (key, value) VALUES ('election_open', '1')''')
    c.execute('''INSERT OR IGNORE INTO system_config (key, value) VALUES ('winner_declaration', '')''')
    c.execute('''INSERT OR IGNORE INTO system_config (key, value) VALUES ('election_closed_at', '')''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    return configure_sqlite_connection(sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS))

def invalidate_candidates_cache():
    CANDIDATES_CACHE['data'] = None
    CANDIDATES_CACHE['dirty'] = True

def get_cached_candidates(conn):
    if not CANDIDATES_CACHE['dirty'] and CANDIDATES_CACHE['data'] is not None:
        return CANDIDATES_CACHE['data']

    c = conn.cursor()
    c.execute('''SELECT id, name, position, votes, image, slogan, student_id, registration_date
                 FROM candidates
                 ORDER BY position, votes DESC, id ASC''')
    candidates = []
    for row in c.fetchall():
        candidates.append({
            'id': row['id'],
            'name': row['name'],
            'position': row['position'],
            'votes': row['votes'],
            'image': row['image'],
            'slogan': row['slogan'],
            'studentId': row['student_id'],
            'registrationDate': row['registration_date']
        })

    CANDIDATES_CACHE['data'] = candidates
    CANDIDATES_CACHE['dirty'] = False
    return candidates

def get_system_config(conn, key, default=''):
    """Read a config value from system_config"""
    c = conn.cursor()
    c.execute('SELECT value FROM system_config WHERE key = ?', (key,))
    row = c.fetchone()
    return row['value'] if row else default

def set_system_config(conn, key, value):
    """Upsert a config value in system_config"""
    c = conn.cursor()
    c.execute(
        '''INSERT INTO system_config (key, value, updated_date)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET
               value = excluded.value,
               updated_date = CURRENT_TIMESTAMP''',
        (key, value)
    )

def build_election_state(conn):
    """Return normalized election state payload"""
    is_open = get_system_config(conn, 'election_open', '1') == '1'
    declaration = get_system_config(conn, 'winner_declaration', '')
    closed_at = get_system_config(conn, 'election_closed_at', '')
    return {
        'isOpen': is_open,
        'winnerDeclaration': declaration or '',
        'closedAt': closed_at or None
    }

def build_timeline_snapshot(conn, archive_year=None):
    """Build a timeline snapshot from current election candidates/state."""
    c = conn.cursor()
    c.execute('''SELECT id, name, position, votes, image, slogan, student_id, registration_date
                 FROM candidates
                 ORDER BY position ASC, votes DESC, name ASC''')
    rows = c.fetchall()
    contestants = []
    for row in rows:
        contestants.append({
            'id': row['id'],
            'name': row['name'],
            'position': row['position'],
            'votes': row['votes'],
            'image': row['image'],
            'slogan': row['slogan'],
            'studentId': row['student_id'],
            'registrationDate': row['registration_date']
        })

    if not contestants:
        return None

    presidents = [x for x in contestants if x['position'] == 'president']
    vice_presidents = [x for x in contestants if x['position'] == 'vice_president']
    election_state = build_election_state(conn)

    year = archive_year
    if year is None:
        closed_at = election_state.get('closedAt')
        if closed_at:
            year = int(str(closed_at)[:4])
        else:
            year = datetime.now().year

    return {
        'year': int(year),
        'archivedAt': datetime.now().isoformat(),
        'election': election_state,
        'leaders': {
            'president': presidents[0] if presidents else None,
            'vice_president': vice_presidents[0] if vice_presidents else None
        },
        'totals': {
            'presidentVotes': sum(x['votes'] for x in presidents),
            'vicePresidentVotes': sum(x['votes'] for x in vice_presidents),
            'contestants': len(contestants)
        },
        'contestants': contestants
    }

def archive_current_election(conn, archive_year=None):
    """Persist current election snapshot into leadership timeline."""
    snapshot = build_timeline_snapshot(conn, archive_year=archive_year)
    if not snapshot:
        return None

    c = conn.cursor()
    c.execute(
        '''INSERT INTO leadership_timeline (year, payload, archived_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(year) DO UPDATE SET
               payload = excluded.payload,
               archived_at = CURRENT_TIMESTAMP''',
        (snapshot['year'], json.dumps(snapshot))
    )
    return snapshot

def restore_latest_timeline_snapshot(conn):
    """Restore candidates and vote totals from the latest archived timeline snapshot."""
    c = conn.cursor()
    c.execute('SELECT payload, year FROM leadership_timeline ORDER BY archived_at DESC, year DESC LIMIT 1')
    row = c.fetchone()
    if not row:
        return None

    data = json.loads(row['payload'])
    contestants = data.get('contestants') if isinstance(data.get('contestants'), list) else []
    if not contestants:
        return None

    # Replace current election data with archived snapshot data.
    c.execute('DELETE FROM votes')
    c.execute('DELETE FROM candidates')
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('candidates', 'votes')")
    c.execute('UPDATE valid_tokens SET is_spent = 0')

    used_student_ids = set()
    restored_count = 0
    for idx, candidate in enumerate(contestants, start=1):
        student_id = (candidate.get('studentId') or '').strip()
        if not student_id or student_id in used_student_ids:
            student_id = f"restored-{row['year']}-{idx}"
        used_student_ids.add(student_id)

        position = (candidate.get('position') or '').strip()
        if position not in ('president', 'vice_president'):
            continue

        c.execute(
            '''INSERT INTO candidates (name, position, votes, image, slogan, student_id, registration_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                (candidate.get('name') or 'Unknown').strip(),
                position,
                int(candidate.get('votes') or 0),
                candidate.get('image') or '',
                candidate.get('slogan') or '',
                student_id,
                candidate.get('registrationDate') or datetime.now().isoformat()
            )
        )
        restored_count += 1

    election_state = data.get('election', {}) if isinstance(data.get('election'), dict) else {}
    declaration = (election_state.get('winnerDeclaration') or '').strip()
    set_system_config(conn, 'winner_declaration', declaration)
    set_system_config(conn, 'election_closed_at', '')

    return {
        'year': int(data.get('year') or row['year']),
        'contestantsRestored': restored_count
    }

def require_admin_key(data):
    """Validate admin action key from request body"""
    provided_key = (data or {}).get('adminKey', '').strip()
    return provided_key == ADMIN_CONTROL_KEY

def get_client_ip():
    """Best effort client IP extraction (works behind proxies too)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'

def track_request_metrics(ip_address, path, status_code, duration_ms):
    stats = REQUEST_COUNTER.setdefault(ip_address, {
        'count': 0,
        'apiCount': 0,
        'errors': 0,
        'lastPath': '',
        'lastStatus': 0,
        'lastDurationMs': 0,
        'firstSeen': datetime.now().isoformat(),
        'lastSeen': ''
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

def normalize_role(raw_role):
    role = (raw_role or '').strip().lower()
    return role if role in ('developer', 'teacher', 'public') else 'unknown'

def normalize_last_seen(value):
    """Parse SQLite timestamp to datetime."""
    if isinstance(value, datetime):
        return value
    text = str(value or '').strip()
    if not text:
        return datetime.min
    # SQLite default format is usually 'YYYY-MM-DD HH:MM:SS'
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except Exception:
        return datetime.min

def to_device_status(last_seen_dt):
    age_seconds = max(0, int((datetime.now() - last_seen_dt).total_seconds()))
    if age_seconds <= ONLINE_SECONDS:
        return 'online', age_seconds
    if age_seconds <= IDLE_SECONDS:
        return 'idle', age_seconds
    return 'offline', age_seconds

def upsert_client_activity(conn, username='Anonymous', user_role='unknown', path=''):
    """Record/refresh a client's activity for device visibility."""
    c = conn.cursor()
    ip_address = get_client_ip()
    clean_username = (username or 'Anonymous').strip()[:120] or 'Anonymous'
    role = normalize_role(user_role)
    user_agent = (request.headers.get('User-Agent') or '')[:255]
    clean_path = (path or request.path or '')[:255]

    c.execute(
        '''INSERT INTO active_clients (
               ip_address, username, user_role, user_agent, first_seen, last_seen, request_count, last_path
           ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, ?)
           ON CONFLICT(ip_address, username, user_role) DO UPDATE SET
               user_agent = excluded.user_agent,
               last_seen = CURRENT_TIMESTAMP,
               request_count = active_clients.request_count + 1,
               last_path = excluded.last_path''',
        (ip_address, clean_username, role, user_agent, clean_path)
    )

def is_developer_request():
    """Basic role gate for developer-only endpoints (UI-level auth model)."""
    role_header = (request.headers.get('X-Auth-Role') or '').strip().lower()
    role_query = (request.args.get('role') or '').strip().lower()
    role_body = normalize_role((request.get_json(silent=True) or {}).get('role', ''))
    return 'developer' in (role_header, role_query, role_body)

def load_tokens_from_file():
    """Load tokens from voters_tokens.txt file into database"""
    TOKEN_FILE = 'public/voters_tokens.txt'
    
    if not os.path.exists(TOKEN_FILE):
        return 0
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            content = f.read()
            # Handle various delimiters
            parts = content.replace('\n', ',').split(',')
            
        conn = get_db()
        c = conn.cursor()
        
        loaded = 0
        for part in parts:
            cleaned = part.strip()
            if cleaned:
                try:
                    c.execute('INSERT OR IGNORE INTO valid_tokens (token) VALUES (?)', (cleaned,))
                    loaded += 1
                except:
                    pass
        
        conn.commit()
        conn.close()
        return loaded
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return 0

# Initialize database on startup
init_db()
tokens_loaded = load_tokens_from_file()
print(f"[DATABASE] Initialized SQLite database")
print(f"[DATABASE] Loaded {tokens_loaded} tokens")

# ==================== API ROUTES ====================

@app.route('/api/login', methods=['GET', 'POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200
    
    if request.method == 'GET':
        return jsonify({'error': 'Method Not Allowed. Use POST.'}), 405

    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if role == 'public':
        try:
            conn = get_db()
            upsert_client_activity(conn, username or 'Public User', role, request.path)
            conn.commit()
            conn.close()
        except Exception:
            pass
        return jsonify({
            'success': True,
            'user': username or 'Public User',
            'role': 'public'
        })
    
    if role == 'developer':
        config = AUTH_CONFIG.get('developers', {})
        if username in config and config[username] == password:
            try:
                conn = get_db()
                upsert_client_activity(conn, username, role, request.path)
                conn.commit()
                conn.close()
            except Exception:
                pass
            return jsonify({'success': True, 'user': username, 'role': 'developer'})
            
    if role == 'teacher':
        config = AUTH_CONFIG.get('teachers', {})
        if username in config and config[username] == password:
            try:
                conn = get_db()
                upsert_client_activity(conn, username, role, request.path)
                conn.commit()
                conn.close()
            except Exception:
                pass
            return jsonify({'success': True, 'user': username, 'role': 'teacher'})

    return jsonify({'success': False, 'message': 'wrong username or password'}), 401

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """Update latest activity timestamp for connected device visibility."""
    try:
        data = request.get_json(silent=True) or {}
        username = data.get('user') or data.get('username') or 'Anonymous'
        role = data.get('role') or data.get('userRole') or 'unknown'
        path = data.get('path') or request.path

        conn = get_db()
        upsert_client_activity(conn, username=username, user_role=role, path=path)
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connected-devices', methods=['GET'])
def connected_devices():
    """Return device/IP activity summary for developer dashboard."""
    try:
        if not is_developer_request():
            return jsonify({'error': 'Developer access required'}), 403

        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT ip_address, username, user_role, user_agent, first_seen, last_seen, request_count, last_path
                     FROM active_clients
                     ORDER BY last_seen DESC''')
        rows = c.fetchall()
        conn.close()

        devices = []
        online = 0
        idle = 0
        offline = 0

        for row in rows:
            last_seen_dt = normalize_last_seen(row['last_seen'])
            status, age_seconds = to_device_status(last_seen_dt)

            if status == 'online':
                online += 1
            elif status == 'idle':
                idle += 1
            else:
                offline += 1

            devices.append({
                'ip': row['ip_address'],
                'username': row['username'],
                'role': row['user_role'],
                'status': status,
                'lastSeen': row['last_seen'],
                'ageSeconds': age_seconds,
                'firstSeen': row['first_seen'],
                'requestCount': int(row['request_count'] or 0),
                'lastPath': row['last_path'] or '',
                'userAgent': row['user_agent'] or ''
            })

        return jsonify({
            'summary': {
                'total': len(devices),
                'online': online,
                'idle': idle,
                'offline': offline
            },
            'devices': devices
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/request-metrics', methods=['GET'])
def request_metrics():
    """Return simple per-IP request counters for troubleshooting."""
    try:
        if not is_developer_request():
            return jsonify({'error': 'Developer access required'}), 403

        items = []
        for ip_address, stats in REQUEST_COUNTER.items():
            items.append({
                'ip': ip_address,
                'count': int(stats.get('count', 0)),
                'apiCount': int(stats.get('apiCount', 0)),
                'errors': int(stats.get('errors', 0)),
                'lastPath': stats.get('lastPath', ''),
                'lastStatus': int(stats.get('lastStatus', 0)),
                'lastDurationMs': int(stats.get('lastDurationMs', 0)),
                'firstSeen': stats.get('firstSeen', ''),
                'lastSeen': stats.get('lastSeen', '')
            })

        items.sort(key=lambda item: item['count'], reverse=True)
        return jsonify({
            'totalIps': len(items),
            'requests': items
        })
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
    """Get all candidates"""
    try:
        conn = get_db()
        candidates = get_cached_candidates(conn)
        conn.close()
        return jsonify(candidates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidates/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    """Update an existing candidate"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        position = data.get('position', '').strip()
        image = data.get('image', '').strip()
        student_id = data.get('studentId', '').strip()
        slogan = data.get('slogan', '').strip()

        if not all([name, position, student_id, image]):
            return jsonify({'error': 'Missing required fields'}), 400

        if position not in ['president', 'vice_president']:
            return jsonify({'error': 'Invalid position'}), 400

        if not image.startswith('data:image/'):
            return jsonify({'error': 'Invalid image format'}), 400

        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
        existing = c.fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'Candidate not found'}), 404

        c.execute('SELECT id FROM candidates WHERE student_id = ? AND id != ?', (student_id, candidate_id))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Student ID already registered'}), 400

        c.execute(
            '''UPDATE candidates
               SET name = ?, position = ?, image = ?, slogan = ?, student_id = ?
               WHERE id = ?''',
            (name, position, image, slogan, student_id, candidate_id)
        )
        conn.commit()
        invalidate_candidates_cache()

        c.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
        updated = c.fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Candidate updated successfully',
            'candidate': {
                'id': updated['id'],
                'name': updated['name'],
                'position': updated['position'],
                'votes': updated['votes'],
                'image': updated['image'],
                'slogan': updated['slogan'],
                'studentId': updated['student_id'],
                'registrationDate': updated['registration_date']
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    """Submit a vote"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidateId')
        position = data.get('position')
        token = data.get('token')
        
        if not all([candidate_id, position, token]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if position not in ['president', 'vice_president']:
            return jsonify({'error': 'Invalid position'}), 400
        
        conn = get_db()
        c = conn.cursor()

        # Check if election is open
        if get_system_config(conn, 'election_open', '1') != '1':
            conn.close()
            return jsonify({'error': 'Election is closed. Voting is disabled.'}), 403
        
        # Check if token is valid
        c.execute('SELECT * FROM valid_tokens WHERE token = ?', (token,))
        token_row = c.fetchone()
        
        if not token_row:
            conn.close()
            return jsonify({'error': 'Invalid token'}), 403
        
        # Check if token is fully spent
        if token_row['is_spent']:
            conn.close()
            return jsonify({'error': 'Token already used for both positions'}), 403
        
        # Check if already voted for this position
        c.execute('SELECT * FROM votes WHERE token = ? AND position = ?', (token, position))
        if c.fetchone():
            conn.close()
            return jsonify({'error': f'Already voted for {position}'}), 403
        
        # Verify candidate exists
        c.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
        candidate = c.fetchone()
        
        if not candidate:
            conn.close()
            return jsonify({'error': 'Candidate not found'}), 404
        
        if candidate['position'] != position:
            conn.close()
            return jsonify({'error': f'Candidate not registered for {position}'}), 400
        
        # Record the vote
        c.execute('INSERT INTO votes (token, candidate_id, position) VALUES (?, ?, ?)',
                 (token, candidate_id, position))
        
        # Update vote count
        c.execute('UPDATE candidates SET votes = votes + 1 WHERE id = ?', (candidate_id,))
        
        # Check if token should be marked as spent
        c.execute('SELECT DISTINCT position FROM votes WHERE token = ?', (token,))
        positions = [row['position'] for row in c.fetchall()]
        
        if len(positions) == 2 or (position == 'president' and 'president' in positions) and (position == 'vice_president' and 'vice_president' in positions):
            c.execute('UPDATE valid_tokens SET is_spent = 1 WHERE token = ?', (token,))
        
        conn.commit()
        invalidate_candidates_cache()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Vote submitted successfully',
            'candidate': candidate['name']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tokens', methods=['GET'])
def get_all_tokens():
    """Get status of all tokens"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get all tokens
        c.execute('SELECT * FROM valid_tokens ORDER BY token ASC')
        tokens = c.fetchall()
        
        token_data = []
        spent_count = 0
        
        for row in tokens:
            token = row['token']
            is_spent = bool(row['is_spent'])
            
            if is_spent:
                spent_count += 1
                
            # Get voted positions for this token
            c.execute('SELECT DISTINCT position FROM votes WHERE token = ?', (token,))
            positions = [r['position'] for r in c.fetchall()]
            
            token_data.append({
                'token': token,
                'isSpent': is_spent,
                'votedPositions': positions
            })
            
        conn.close()
        
        return jsonify({
            'total': len(tokens),
            'spent': spent_count,
            'remaining': len(tokens) - spent_count,
            'tokens': token_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-token/<token>', methods=['GET'])
def check_token(token):
    """Check token status"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Check if token exists
        c.execute('SELECT * FROM valid_tokens WHERE token = ?', (token,))
        token_row = c.fetchone()
        
        if not token_row:
            conn.close()
            return jsonify({
                'isValid': False,
                'isSpent': False,
                'votedPositions': []
            })
        
        # Get voted positions with indexed lookup
        c.execute('SELECT position FROM votes WHERE token = ? GROUP BY position', (token,))
        positions = [row['position'] for row in c.fetchall()]
        
        conn.close()
        
        return jsonify({
            'isValid': True,
            'isSpent': bool(token_row['is_spent']),
            'votedPositions': positions
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get voting results"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get president results
        c.execute('''SELECT * FROM candidates WHERE position = 'president' 
                    ORDER BY votes DESC''')
        presidents = []
        total_pres = 0
        for row in c.fetchall():
            presidents.append({
                'id': row['id'],
                'name': row['name'],
                'position': row['position'],
                'votes': row['votes'],
                'image': row['image'],
                'slogan': row['slogan']
            })
            total_pres += row['votes']
        
        # Get vice president results
        c.execute('''SELECT * FROM candidates WHERE position = 'vice_president' 
                    ORDER BY votes DESC''')
        vice_presidents = []
        total_vice = 0
        for row in c.fetchall():
            vice_presidents.append({
                'id': row['id'],
                'name': row['name'],
                'position': row['position'],
                'votes': row['votes'],
                'image': row['image'],
                'slogan': row['slogan']
            })
            total_vice += row['votes']
        
        election_state = build_election_state(conn)
        conn.close()
        return jsonify({
            'president': {
                'candidates': presidents,
                'totalVotes': total_pres
            },
            'vice_president': {
                'candidates': vice_presidents,
                'totalVotes': total_vice
            },
            'election': election_state
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidates/register', methods=['POST'])
def register_candidate():
    """Register a new candidate"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        position = data.get('position', '').strip()
        image = data.get('image', '').strip()
        student_id = data.get('studentId', '').strip()
        slogan = data.get('slogan', '').strip()
        
        # Validation
        if not all([name, position, student_id, image]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if position not in ['president', 'vice_president']:
            return jsonify({'error': 'Invalid position'}), 400
        
        if not image.startswith('data:image/'):
            return jsonify({'error': 'Invalid image format'}), 400
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if student ID already registered
        c.execute('SELECT * FROM candidates WHERE student_id = ?', (student_id,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Student ID already registered'}), 400
        
        # Insert candidate
        c.execute('''INSERT INTO candidates (name, position, image, slogan, student_id)
                    VALUES (?, ?, ?, ?, ?)''',
                 (name, position, image, slogan, student_id))
        
        conn.commit()
        invalidate_candidates_cache()
        candidate_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Candidate registered successfully',
            'candidate': {
                'id': candidate_id,
                'name': name,
                'position': position,
                'votes': 0,
                'image': image,
                'slogan': slogan
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_votes():
    """Reset all votes (admin)"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Reset vote counts
        c.execute('UPDATE candidates SET votes = 0')
        
        # Clear votes table
        c.execute('DELETE FROM votes')
        
        # Reset tokens
        c.execute('UPDATE valid_tokens SET is_spent = 0')
        
        conn.commit()
        invalidate_candidates_cache()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'System reset successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/election-state', methods=['GET'])
def election_state():
    """Get election open/closed state and winner declaration"""
    try:
        conn = get_db()
        state = build_election_state(conn)
        conn.close()
        return jsonify(state)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/election/close', methods=['POST'])
def close_election():
    """Temporarily close election and disable voting (no timeline archive)."""
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403

        conn = get_db()
        set_system_config(conn, 'election_open', '0')
        set_system_config(conn, 'election_closed_at', datetime.now().isoformat())
        conn.commit()
        state = build_election_state(conn)
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Election temporarily closed. Voting is disabled, contestants are preserved.',
            'state': state
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/election/reopen', methods=['POST'])
def reopen_election():
    """Re-open election without clearing candidates, votes, or tokens."""
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403

        conn = get_db()
        set_system_config(conn, 'election_open', '1')
        set_system_config(conn, 'election_closed_at', '')
        conn.commit()
        state = build_election_state(conn)
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Election resumed. Voting is enabled and data was preserved.',
            'state': state
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/election/reopen-reset', methods=['POST'])
def reopen_election_reset():
    """Reopen election and refresh full vote state"""
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403

        conn = get_db()
        c = conn.cursor()

        # Save past leadership data before full refresh
        archived = archive_current_election(conn)

        # Full refresh for a brand-new election round
        # Remove all election activity and all registered candidates.
        c.execute('DELETE FROM votes')
        c.execute('DELETE FROM candidates')
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('candidates', 'votes')")
        c.execute('UPDATE valid_tokens SET is_spent = 0')
        set_system_config(conn, 'election_open', '1')
        set_system_config(conn, 'winner_declaration', '')
        set_system_config(conn, 'election_closed_at', '')

        conn.commit()
        invalidate_candidates_cache()
        state = build_election_state(conn)
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Voting re-opened and system fully refreshed. All candidates were removed.',
            'state': state,
            'timelineArchived': bool(archived)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/election/restore-latest', methods=['POST'])
def restore_latest_election_snapshot():
    """Restore latest archived candidates and vote totals after accidental reset."""
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403

        conn = get_db()
        restored = restore_latest_timeline_snapshot(conn)
        if not restored:
            conn.close()
            return jsonify({'error': 'No archived snapshot available to restore.'}), 404

        set_system_config(conn, 'election_open', '1')
        conn.commit()
        invalidate_candidates_cache()
        state = build_election_state(conn)
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Latest archived data restored. Voting resumed.',
            'state': state,
            'restored': restored,
            'note': 'Token-level spent state and per-token vote history cannot be reconstructed from timeline archive.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leadership-timeline/years', methods=['GET'])
def get_timeline_years():
    """Return all archived timeline years."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT year, archived_at FROM leadership_timeline ORDER BY year DESC')
        rows = c.fetchall()
        conn.close()
        return jsonify({
            'years': [row['year'] for row in rows],
            'items': [{'year': row['year'], 'archivedAt': row['archived_at']} for row in rows]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leadership-timeline/<int:year>', methods=['GET'])
def get_timeline_year(year):
    """Return archived leadership snapshot for a selected year."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT payload, archived_at FROM leadership_timeline WHERE year = ?', (year,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({'error': 'No timeline data found for selected year'}), 404

        payload = json.loads(row['payload'])
        payload['archivedAt'] = payload.get('archivedAt') or row['archived_at']
        return jsonify(payload)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leadership-history', methods=['GET'])
def get_leadership_history_legacy():
    """Legacy alias endpoint for leadership timeline consumers."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT payload FROM leadership_timeline ORDER BY year DESC')
        rows = c.fetchall()
        conn.close()

        history = []
        for row in rows:
            data = json.loads(row['payload'])
            leaders = data.get('leaders', {})
            president = leaders.get('president') or {}
            vice = leaders.get('vice_president') or {}
            totals = data.get('totals', {})
            total_votes = int(totals.get('presidentVotes', 0)) + int(totals.get('vicePresidentVotes', 0))
            history.append({
                'year': data.get('year'),
                'presidentName': president.get('name', 'N/A'),
                'presidentPhoto': president.get('image', ''),
                'vicePresidentName': vice.get('name', 'N/A'),
                'vicePresidentPhoto': vice.get('image', ''),
                'presidentVotes': int(president.get('votes', 0)),
                'vicePresidentVotes': int(vice.get('votes', 0)),
                'votesWon': int(president.get('votes', 0)),
                'totalVotes': total_votes,
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
    """Set winner declaration text"""
    try:
        data = request.get_json() or {}
        if not require_admin_key(data):
            return jsonify({'error': 'Invalid admin key'}), 403

        declaration = (data.get('declaration') or '').strip()
        if declaration not in ALLOWED_DECLARATIONS:
            return jsonify({
                'error': 'Invalid declaration. Use one of the pre-made declaration statements.'
            }), 400

        conn = get_db()
        set_system_config(conn, 'winner_declaration', declaration)
        conn.commit()
        state = build_election_state(conn)
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Winner declaration saved.',
            'state': state
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-info', methods=['GET'])
def system_info():
    """Get system information and server details"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Count data
        c.execute('SELECT COUNT(*) as count FROM candidates')
        total_candidates = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM votes')
        total_votes = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM valid_tokens')
        total_tokens = c.fetchone()['count']
        
        c.execute('SELECT COUNT(*) as count FROM valid_tokens WHERE is_spent = 1')
        spent_tokens = c.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'serverType': 'Localized Voting System',
            'version': '2.0',
            'database': 'SQLite (Local)',
            'localIP': LOCAL_IP,
            'port': os.environ.get('PORT', 3000),
            'accessURL': f'http://{LOCAL_IP}:{os.environ.get("PORT", 3000)}',
            'stats': {
                'totalCandidates': total_candidates,
                'totalVotes': total_votes,
                'totalTokens': total_tokens,
                'spentTokens': spent_tokens,
                'remainingTokens': total_tokens - spent_tokens
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-data', methods=['GET'])
def export_data():
    """Export all voting data as JSON"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get all candidates
        c.execute('SELECT * FROM candidates')
        candidates = [dict(row) for row in c.fetchall()]
        
        # Get all votes
        c.execute('SELECT * FROM votes')
        votes = [dict(row) for row in c.fetchall()]
        
        # Get token stats
        c.execute('SELECT COUNT(*) as total FROM valid_tokens')
        total_tokens = c.fetchone()['total']
        
        c.execute('SELECT COUNT(*) as spent FROM valid_tokens WHERE is_spent = 1')
        spent_tokens = c.fetchone()['spent']
        
        conn.close()
        
        export_data = {
            'exportDate': datetime.now().isoformat(),
            'candidates': candidates,
            'votes': votes,
            'tokenStats': {
                'total': total_tokens,
                'spent': spent_tokens,
                'remaining': total_tokens - spent_tokens
            }
        }
        
        return jsonify(export_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    if filename.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    try:
        return send_from_directory('public', filename)
    except:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f'\n{"="*60}')
    print(f'[VOTING SYSTEM] Localized Offline Voting System v2.0')
    print(f'[DATABASE] SQLite - {DB_PATH}')
    print(f'[LOGS] Request log - {LOG_PATH}')
    print(f'{"="*60}')
    print(f'[ACCESS]')
    print(f'  Local Machine:    http://localhost:{port}')
    print(f'  Network (LAN):    http://{LOCAL_IP}:{port}')
    print(f'  Registration:      http://{LOCAL_IP}:{port}/register.html')
    print(f'  System Info:       http://{LOCAL_IP}:{port}/api/system-info')
    print(f'{"="*60}')
    print(f'[FEATURES]')
    print(f'  ✓ Completely offline - no internet required')
    print(f'  ✓ Access from any computer on the network')
    print(f'  ✓ Persistent SQLite database')
    print(f'  ✓ All data stored locally')
    print(f'{"="*60}\n')
    
    app.run(host='0.0.0.0', port=port, debug=False)
