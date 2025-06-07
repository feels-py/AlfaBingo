import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import random
import time
import threading
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurações do Admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "AlfaBingo2024!"  # Troque esta senha!
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.numbers_drawn = []
        self.is_running = False
        self.auto_draw = False
        self.draw_speed = 5  # segundos
        self.cards = {}
        self.winners = []
        self.draw_thread = None

game_state = GameState()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_card_numbers():
    return sorted(random.sample(range(1, 76), 24))

def auto_draw():
    with app.app_context():
        while game_state.is_running and game_state.auto_draw:
            available = [n for n in range(1, 76) if n not in game_state.numbers_drawn]
            if not available:
                break
            
            new_number = random.choice(available)
            game_state.numbers_drawn.append(new_number)
            
            socketio.emit('number_drawn', {
                'number': new_number,
                'numbers_drawn': game_state.numbers_drawn,
                'total': len(game_state.numbers_drawn)
            })
            
            check_winners(new_number)
            time.sleep(game_state.draw_speed)

def check_winners(number):
    winners_found = False
    for card_id, card in game_state.cards.items():
        if number in card['numbers'] and number not in card.get('marked', []):
            card['marked'] = card.get('marked', []) + [number]
            if len(card['marked']) >= 24:  # Bingo!
                if card_id not in [w['id'] for w in game_state.winners]:
                    winner = {
                        'id': card_id,
                        'name': card['name'],
                        'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        'numbers': card['numbers'],
                        'marked_numbers': card['marked']
                    }
                    game_state.winners.append(winner)
                    socketio.emit('new_winner', winner)
                    winners_found = True
    
    # Pausa o jogo automaticamente se houver vencedores
    if winners_found and game_state.auto_draw:
        game_state.auto_draw = False
        socketio.emit('game_paused', {'reason': 'winner_found'})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/auth', methods=['POST'])
def auth():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if (username == ADMIN_USERNAME and 
            check_password_hash(ADMIN_PASSWORD_HASH, password)):
            session['admin_logged_in'] = True
            return jsonify({
                'success': True, 
                'redirect': url_for('admin_dashboard')
            })
        
        return jsonify({'error': 'Usuário ou senha incorretos'}), 401
    
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', game_state={
        'is_running': game_state.is_running,
        'numbers_drawn': game_state.numbers_drawn,
        'total_cards': len(game_state.cards),
        'winners': game_state.winners
    })

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/api/admin/start', methods=['POST'])
@admin_required
def start():
    if not game_state.is_running:
        game_state.is_running = True
        game_state.auto_draw = True
        game_state.draw_thread = threading.Thread(target=auto_draw)
        game_state.draw_thread.start()
        return jsonify({'success': True})
    return jsonify({'error': 'Jogo já está em andamento'}), 400

@app.route('/api/admin/stop', methods=['POST'])
@admin_required
def stop():
    game_state.auto_draw = False
    return jsonify({'success': True})

@app.route('/api/admin/reset', methods=['POST'])
@admin_required
def reset():
    game_state.reset()
    socketio.emit('game_reset')
    return jsonify({'success': True})

@app.route('/api/admin/cards/add', methods=['POST'])
@admin_required
def add_card():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Dados inválidos ou nome não fornecido'}), 400

        card_id = f"ALFA-{secrets.token_hex(3).upper()}"
        numbers = generate_card_numbers()
        
        game_state.cards[card_id] = {
            'name': data['name'].strip(),
            'numbers': numbers,
            'marked': [],
            'created_at': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        return jsonify({
            'success': True,
            'card_id': card_id,
            'numbers': numbers,
            'name': data['name'].strip()
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao criar cartela: {str(e)}'}), 500

@app.route('/api/admin/cards/list', methods=['GET'])
@admin_required
def list_cards():
    return jsonify({
        'success': True,
        'cards': game_state.cards,
        'total': len(game_state.cards)
    })

@socketio.on('connect')
def connect():
    emit('game_update', {
        'numbers': game_state.numbers_drawn,
        'winners': [w['id'] for w in game_state.winners],
        'is_running': game_state.is_running
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)