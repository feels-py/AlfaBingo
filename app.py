import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import random
import time
import threading
from functools import wraps  # Importação ESSENCIAL para o decorator
from datetime import datetime

# ==============================================
# CONFIGURAÇÃO INICIAL
# ==============================================
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

socketio = SocketIO(app, cors_allowed_origins=[], async_mode='eventlet')

# ==============================================
# CONFIGURAÇÕES DE ADMIN (ALTERE ESTAS CREDENCIAIS!)
# ==============================================
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password_hash": generate_password_hash("AlfaBingo2024!")  # Troque esta senha!
}

# ==============================================
# ESTADO DO JOGO
# ==============================================
class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.numbers_drawn = []
        self.is_running = False
        self.auto_draw = False
        self.draw_interval = 5
        self.cards = {}
        self.winners = []
        self.draw_thread = None

game_state = GameState()

# ==============================================
# DECORATOR PARA ROTAS ADMIN (CORRIGIDO)
# ==============================================
def admin_required(f):
    @wraps(f)  # Agora está corretamente importado
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================
# FUNÇÕES PRINCIPAIS
# ==============================================
def auto_draw():
    with app.app_context():
        while game_state.is_running and game_state.auto_draw and len(game_state.numbers_drawn) < 75:
            available = [n for n in range(1, 76) if n not in game_state.numbers_drawn]
            if not available:
                break
            
            new_number = random.choice(available)
            game_state.numbers_drawn.append(new_number)
            check_winners(new_number)
            
            socketio.emit('number_drawn', {
                'number': new_number,
                'total': len(game_state.numbers_drawn),
                'winners': [w['id'] for w in game_state.winners]
            })
            
            time.sleep(game_state.draw_interval)

def check_winners(number):
    for card_id, card in game_state.cards.items():
        if number in card['numbers'] and number not in card['marked']:
            card['marked'].append(number)
            if len(card['marked']) == 24:
                if card_id not in [w['id'] for w in game_state.winners]:
                    winner_data = {
                        'id': card_id,
                        'name': card['name'],
                        'numbers': card['numbers'],
                        'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                    game_state.winners.append(winner_data)
                    socketio.emit('new_winner', winner_data)

# ==============================================
# ROTAS PÚBLICAS
# ==============================================
@app.route('/')
def home():
    return render_template('index.html')

# ==============================================
# ROTAS ADMIN (COM VERIFICAÇÃO REFORÇADA)
# ==============================================
@app.route('/admin')
def admin_login_page():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if (username == ADMIN_CREDENTIALS["username"] and 
            check_password_hash(ADMIN_CREDENTIALS["password_hash"], password)):
            session['admin_logged_in'] = True
            return jsonify({
                'success': True,
                'redirect': url_for('admin_dashboard')
            })
        
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    except Exception as e:
        return jsonify({'error': f'Erro no servidor: {str(e)}'}), 500

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        return render_template('admin_dashboard.html', game_state={
            'is_running': game_state.is_running,
            'numbers_drawn': game_state.numbers_drawn,
            'total_cards': len(game_state.cards),
            'winners': game_state.winners
        })
    except Exception as e:
        return f"Erro ao carregar o painel: {str(e)}", 500

# ==============================================
# API ADMIN (COM TRATAMENTO DE ERROS)
# ==============================================
@app.route('/api/admin/start', methods=['POST'])
@admin_required
def start_game():
    try:
        if not game_state.is_running:
            game_state.is_running = True
            game_state.auto_draw = True
            game_state.draw_thread = threading.Thread(target=auto_draw)
            game_state.draw_thread.start()
            return jsonify({'success': True})
        return jsonify({'error': 'Jogo já iniciado'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stop', methods=['POST'])
@admin_required
def stop_game():
    try:
        game_state.auto_draw = False
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reset', methods=['POST'])
@admin_required
def reset_game():
    try:
        game_state.reset()
        socketio.emit('game_reset')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cards/add', methods=['POST'])
@admin_required
def add_card():
    try:
        data = request.get_json()
        card_id = f"ALFA-{secrets.token_hex(3).upper()}"
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==============================================
# WEBSOCKETS
# ==============================================
@socketio.on('connect')
def handle_connect():
    try:
        socketio.emit('game_update', {
            'numbers': game_state.numbers_drawn,
            'winners': [w['id'] for w in game_state.winners],
            'is_running': game_state.is_running
        })
    except Exception as e:
        print(f"Erro no WebSocket: {str(e)}")

# ==============================================
# INICIALIZAÇÃO
# ==============================================
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')