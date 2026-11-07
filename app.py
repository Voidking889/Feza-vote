from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime


app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "OPTIONS"]}})
CORS(app)

from auth_config import AUTH_CONFIG

# In-memory storage (replace with database in production)
votes = {}  # Track votes by token: {token: {'president': candidate_id, 'vice_president': candidate_id}}
# Default placeholder image
default_image = 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect fill=\'%23e2e8f0\' width=\'200\' height=\'200\'/%3E%3Ctext fill=\'%2394a3b8\' font-family=\'sans-serif\' font-size=\'14\' dy=\'10.5\' font-weight=\'bold\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\'%3ENo Image%3C/text%3E%3C/svg%3E'

candidates = []  # Start with empty list - candidates will be added through registration
# Server-side state
spent_tokens = set()  # Track fully spent tokens (both president and vice president voted)
next_candidate_id = 1  # Auto-increment ID for new candidates
registered_student_ids = set()  # Track registered student IDs
LEADERSHIP_HISTORY_FILE = 'leadership_history.json'

def load_leadership_history():
    if not os.path.exists(LEADERSHIP_HISTORY_FILE):
        return []
    try:
        with open(LEADERSHIP_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def normalize_legacy_snapshot(entry):
    year = int(entry.get('year', datetime.now().year))
    contestants = entry.get('contestants') if isinstance(entry.get('contestants'), list) else []
    return {
        'year': year,
        'archivedAt': entry.get('archivedAt') or None,
        'election': {
            'isOpen': False,
            'winnerDeclaration': entry.get('winnerDeclaration') or entry.get('slogan') or '',
            'closedAt': None
        },
        'leaders': {
            'president': {
                'name': entry.get('presidentName', 'N/A'),
                'image': entry.get('presidentPhoto', ''),
                'votes': int(entry.get('presidentVotes', entry.get('votesWon', 0) or 0))
            },
            'vice_president': {
                'name': entry.get('vicePresidentName', 'N/A'),
                'image': entry.get('vicePresidentPhoto', ''),
                'votes': int(entry.get('vicePresidentVotes', 0) or 0)
            }
        },
        'totals': {
            'presidentVotes': int(entry.get('presidentVotes', entry.get('votesWon', 0) or 0)),
            'vicePresidentVotes': int(entry.get('vicePresidentVotes', 0) or 0),
            'contestants': int(entry.get('totalContestants', len(contestants)))
        },
        'contestants': contestants
    }

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if role == 'public':
        # Public role requires no password
        return jsonify({
            'success': True,
            'user': username or 'Public User',
            'role': 'public'
        })
    
    if role == 'developer':
        config = AUTH_CONFIG.get('developers', {})
        if username in config and config[username] == password:
            return jsonify({
                'success': True,
                'user': username,
                'role': 'developer'
            })
            
    if role == 'teacher':
        config = AUTH_CONFIG.get('teachers', {})
        if username in config and config[username] == password:
            return jsonify({
                'success': True,
                'user': username,
                'role': 'teacher'
            })

    return jsonify({
        'success': False,
        'message': 'wrong username or password'
    }), 401

# Serve HTML pages
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/register.html')
def register():
    return send_from_directory('public', 'register.html')

# API Routes - must be before catch-all static route
@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    return jsonify(candidates)

@app.route('/api/candidates/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    data = request.get_json()

    name = data.get('name', '').strip()
    position = data.get('position', '').strip()
    image = data.get('image', '').strip()
    student_id = data.get('studentId', '').strip()
    slogan = data.get('slogan', '').strip()

    if not name or not position or not student_id or not image:
        return jsonify({'error': 'Name, position, Student ID, and Image are required'}), 400

    if not image.startswith('data:image/'):
        return jsonify({'error': 'Invalid image format. Please upload a valid image file.'}), 400

    target_candidate = None
    for candidate in candidates:
        if int(candidate.get('id')) == candidate_id:
            target_candidate = candidate
            break

    if not target_candidate:
        return jsonify({'error': 'Candidate not found'}), 404

    for candidate in candidates:
        if int(candidate.get('id')) != candidate_id and (candidate.get('studentId') or '').strip() == student_id:
            return jsonify({'error': 'This Student ID is already registered as a candidate'}), 400

    old_student_id = (target_candidate.get('studentId') or '').strip()
    if old_student_id and old_student_id in registered_student_ids:
        registered_student_ids.discard(old_student_id)

    target_candidate['name'] = name
    target_candidate['position'] = position
    target_candidate['image'] = image
    target_candidate['slogan'] = slogan
    target_candidate['studentId'] = student_id
    registered_student_ids.add(student_id)

    return jsonify({
        'success': True,
        'message': 'Candidate updated successfully',
        'candidate': target_candidate
    })

# Load tokens from file
TOKEN_FILE = 'public/voters_tokens.txt'

def load_tokens():
    tokens = set()
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                content = f.read()
                # Handle various delimiters (newlines, commas)
                parts = content.replace('\n', ',').split(',')
                for part in parts:
                    cleaned = part.strip()
                    if cleaned:
                        tokens.add(cleaned)
        except Exception as e:
            print(f"Error loading tokens: {e}")
    return tokens

def save_tokens(tokens):
    try:
        token_list = sorted(list(tokens))
        lines = []
        chunk_size = 10
        for i in range(0, len(token_list), chunk_size):
            chunk = token_list[i:i + chunk_size]
            lines.append(','.join(chunk))
        
        with open(TOKEN_FILE, 'w') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error saving tokens: {e}")

# Initialize tokens
valid_tokens = load_tokens()
print(f"Loaded {len(valid_tokens)} valid tokens")

@app.route('/api/vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    candidate_id = data.get('candidateId')
    position = data.get('position')  # 'president' or 'vice_president'
    token = data.get('token')

    if not candidate_id or not position or not token:
        return jsonify({'error': 'Candidate ID, Position, and Voting Token are required'}), 400

    if position not in ['president', 'vice_president']:
        return jsonify({'error': 'Invalid position. Must be "president" or "vice_president"'}), 400

    # Check if token is fully spent
    if token in spent_tokens:
        return jsonify({'error': 'Token already used for both positions'}), 403

    # Load valid tokens
    if token not in valid_tokens:
        return jsonify({'error': 'Invalid token'}), 403

    # Find candidate and increment vote
    candidate = next((c for c in candidates if c['id'] == int(candidate_id)), None)
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404

    # Check candidate position matches requested position
    if candidate['position'] != position:
        return jsonify({'error': f'Candidate is not registered for {position}'}), 400

    # Initialize votes for token if not exists
    if token not in votes:
        votes[token] = {}

    # Check if already voted for this position
    if position in votes[token]:
        return jsonify({'error': f'You have already voted for {position}'}), 403

    # Record the vote
    candidate['votes'] += 1
    votes[token][position] = candidate_id

    # Mark token as spent if both positions are filled
    if 'president' in votes[token] and 'vice_president' in votes[token]:
        spent_tokens.add(token)

    return jsonify({
        'success': True,
        'message': 'Vote submitted successfully',
        'candidate': candidate['name'],
        'position': position,
        'votesRemaining': 1 if position in votes[token] and (position == 'president' and 'vice_president' not in votes[token] or position == 'vice_president' and 'president' not in votes[token]) else 0
    })

@app.route('/api/results', methods=['GET'])
def get_results():
    # Separate candidates by position
    presidents = [c for c in candidates if c['position'] == 'president']
    vice_presidents = [c for c in candidates if c['position'] == 'vice_president']
    
    sorted_presidents = sorted(presidents, key=lambda x: x['votes'], reverse=True)
    sorted_vice_presidents = sorted(vice_presidents, key=lambda x: x['votes'], reverse=True)
    
    total_votes_president = sum(c['votes'] for c in presidents)
    total_votes_vice_president = sum(c['votes'] for c in vice_presidents)
    
    return jsonify({
        'president': {
            'candidates': sorted_presidents,
            'totalVotes': total_votes_president
        },
        'vice_president': {
            'candidates': sorted_vice_presidents,
            'totalVotes': total_votes_vice_president
        }
    })

@app.route('/api/check-token/<token>', methods=['GET'])
def check_token(token):
    is_valid = token in valid_tokens
    is_spent = token in spent_tokens
    voted_positions = list(votes.get(token, {}).keys()) if token in votes else []
    
    return jsonify({
        'isValid': is_valid,
        'isSpent': is_spent,
        'votedPositions': voted_positions  # ['president'], ['vice_president'], or ['president', 'vice_president']
    })

@app.route('/api/tokens', methods=['GET'])
def get_all_tokens():
    token_data = []
    # Convert set to sorted list for consistent ordering
    sorted_tokens = sorted(list(valid_tokens))
    
    for token in sorted_tokens:
        is_spent = token in spent_tokens
        voted_positions = list(votes.get(token, {}).keys()) if token in votes else []
        
        token_data.append({
            'token': token,
            'isSpent': is_spent,
            'votedPositions': voted_positions
        })
    
    return jsonify({
        'total': len(valid_tokens),
        'spent': len(spent_tokens),
        'remaining': len(valid_tokens) - len(spent_tokens),
        'tokens': token_data
    })

@app.route('/api/candidates/register', methods=['POST'])
def register_candidate():
    global next_candidate_id
    data = request.get_json()
    
    name = data.get('name', '').strip()
    position = data.get('position', '').strip()
    image = data.get('image', '').strip()
    student_id = data.get('studentId', '').strip()
    slogan = data.get('slogan', '').strip()
    
    # Validation
    if not name or not position or not student_id or not image:
        return jsonify({'error': 'Name, position, Student ID, and Image are required'}), 400
    
    # Validate image is base64 data URL
    if not image.startswith('data:image/'):
        return jsonify({'error': 'Invalid image format. Please upload a valid image file.'}), 400
    
    # Check if student ID is already registered
    if student_id in registered_student_ids:
        return jsonify({'error': 'This Student ID is already registered as a candidate'}), 400
    
    # Create new candidate with registration date
    new_candidate = {
        'id': next_candidate_id,
        'name': name,
        'position': position,
        'votes': 0,
        'image': image,
        'slogan': slogan,
        'studentId': student_id,
        'registrationDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    candidates.append(new_candidate)
    registered_student_ids.add(student_id)
    next_candidate_id += 1
    
    return jsonify({
        'success': True,
        'message': 'Candidate registered successfully',
        'candidate': new_candidate
    }), 201

@app.route('/api/reset', methods=['POST'])
def reset_votes():
    global candidates, votes, spent_tokens
    for candidate in candidates:
        candidate['votes'] = 0
    votes.clear()
    spent_tokens.clear()
    return jsonify({'success': True, 'message': 'Votes reset successfully'})

@app.route('/api/leadership-history', methods=['GET'])
def get_leadership_history():
    return jsonify(load_leadership_history())

@app.route('/api/leadership-timeline/years', methods=['GET'])
def get_timeline_years():
    history = load_leadership_history()
    years = []
    for item in history:
        try:
            years.append(int(item.get('year')))
        except Exception:
            continue
    years = sorted(set(years), reverse=True)
    return jsonify({
        'years': years,
        'items': [{'year': y, 'archivedAt': None} for y in years]
    })

@app.route('/api/leadership-timeline/<int:year>', methods=['GET'])
def get_timeline_year(year):
    history = load_leadership_history()
    match = None
    for item in history:
        try:
            if int(item.get('year')) == year:
                match = item
                break
        except Exception:
            continue

    if not match:
        return jsonify({'error': 'No timeline data found for selected year'}), 404

    return jsonify(normalize_legacy_snapshot(match))




# Serve static files (CSS, JS, images, etc.) - MUST be last to avoid catching API routes
@app.route('/<path:filename>')
def serve_static(filename):
    # Don't serve API routes through this
    if filename.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    # Serve static files from public folder
    try:
        return send_from_directory('public', filename)
    except:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f'[SERVER] Voting server running on http://localhost:{port}')
    print(f'[SERVER] Registration page: http://localhost:{port}/register.html')
    print(f'[SERVER] Voting page: http://localhost:{port}/')
    print('[SERVER] IMPORTANT: Access pages through the Flask server, not by opening HTML files directly!')
    app.run(host='0.0.0.0', port=port, debug=True)
