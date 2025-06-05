import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import random
import time
import threading
from datetime import datetime

# Configuração básica do Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configuração do Socket.IO para o Render
socketio = SocketIO(app, 
                   cors_allowed_origins=["https://alfabingo.onrender.com"],
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# Credenciais de administrador (ALTERE PARA PRODUÇÃO!)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv('ADMIN_PASSWORD', 'AlfaBingo2024!'))

class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.numbers_drawn = []
        self.is_running = False
        self.auto_draw = False
        self.draw_interval = 5  # segundos
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

def auto_draw():
    with app.app_context():
        while game_state.is_running and game_state.auto_draw:
            available = [n for n in range(1, 76) if n not in game_state.numbers_drawn]
            if not available:
                game_state.auto_draw = False
                break
            
            new_number = random.choice(available)
            game_state.numbers_drawn.append(new_number)
            
            socketio.emit('number_drawn', {
                'number': new_number,
                'total': len(game_state.numbers_drawn),
                'winners': [w['id'] for w in game_state.winners]
            }, namespace='/admin')
            
            check_winners(new_number)
            time.sleep(game_state.draw_interval)

def check_winners(number):
    for card_id, card in game_state.cards.items():
        if number in card['numbers'] and number not in card['marked']:
            card['marked'].append(number)
            if len(card['marked']) == 24:
                if card_id not in [w['id'] for w in game_state.winners]:
                    winner = {
                        'id': card_id,
                        'name': card['name'],
                        'timestamp': datetime.now().isoformat()
                    }
                    game_state.winners.append(winner)
                    socketio.emit('new_winner', winner, namespace='/admin')

# Rotas públicas
@app.route('/')
def home():
    return render_template('index.html')

# Rotas de administração
@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/auth', methods=['POST'])
def admin_auth():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        if (data.get('username') == ADMIN_USERNAME and 
            check_password_hash(ADMIN_PASSWORD_HASH, data.get('password')):
            session['admin_logged_in'] = True
            return jsonify({
                'success': True, 
                'redirect': url_for('admin_dashboard')
            })
        
        return jsonify({'error': 'Credenciais inválidas'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# API de administração
@app.route('/api/admin/start', methods=['POST'])
@admin_required
def start_game():
    if not game_state.is_running:
        game_state.is_running = True
        game_state.auto_draw = True
        game_state.draw_thread = threading.Thread(target=auto_draw)
        game_state.draw_thread.start()
        return jsonify({'success': True})
    return jsonify({'error': 'Jogo já está em andamento'}), 400

@app.route('/api/admin/stop', methods=['POST'])
@admin_required
def stop_game():
    game_state.auto_draw = False
    return jsonify({'success': True})

@app.route('/api/admin/reset', methods=['POST'])
@admin_required
def reset_game():
    game_state.reset()
    socketio.emit('game_reset', namespace='/admin')
    return jsonify({'success': True})

@app.route('/api/admin/cards/add', methods=['POST'])
@admin_required
def add_card():
    data = request.get_json()
    card_id = f"ALFA-{secrets.token_hex(4).upper()}"
    numbers = sorted(random.sample(range(1, 76), 24))
    
    game_state.cards[card_id] = {
        'name': data.get('name', 'Jogador Alfa Bingo'),
        'numbers': numbers,
        'marked': []
    }
    
    return jsonify({
        'success': True,
        'card_id': card_id,
        'numbers': numbers
    })

# WebSocket Handlers
@socketio.on('connect', namespace='/admin')
def handle_admin_connect():
    emit('game_update', {
        'numbers': game_state.numbers_drawn,
        'winners': [w['id'] for w in game_state.winners],
        'is_running': game_state.is_running
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)