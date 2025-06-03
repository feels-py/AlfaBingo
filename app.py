import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import random
import time
import threading
from functools import wraps  # Importação adicionada para corrigir o erro
from datetime import datetime

# Configuração do Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)  # Chave segura para sessões

# Configuração do Socket.IO (compatível com Render)
socketio = SocketIO(app, cors_allowed_origins=[])

# Credenciais do Admin (ALTERE PARA PRODUÇÃO!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("AlfaBingo2024!")

# Estado do Jogo
class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.numbers_drawn = []      # Números sorteados
        self.is_running = False      # Jogo está ativo?
        self.auto_draw = False       # Sorteio automático?
        self.draw_speed = 5          # Intervalo entre sorteios (segundos)
        self.cards = {}              # Cartelas registradas
        self.winners = []            # Ganhadores
        self.draw_thread = None      # Thread do sorteio

game_state = GameState()

# Decorator para rotas admin (CORRIGIDO)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Sorteio automático em segundo plano
def auto_draw():
    with app.app_context():
        while game_state.is_running and game_state.auto_draw and len(game_state.numbers_drawn) < 75:
            available = [n for n in range(1, 76) if n not in game_state.numbers_drawn]
            if not available:
                break
            
            new_number = random.choice(available)
            game_state.numbers_drawn.append(new_number)
            
            # Verifica cartelas vencedoras
            check_winners(new_number)
            
            # Emite atualização em tempo real
            socketio.emit('number_drawn', {
                'number': new_number,
                'total': len(game_state.numbers_drawn),
                'winners': [w['id'] for w in game_state.winners]
            })
            
            time.sleep(game_state.draw_speed)

# Verifica cartelas vencedoras
def check_winners(number):
    for card_id, card in game_state.cards.items():
        if number in card['numbers'] and number not in card['marked']:
            card['marked'].append(number)
            
            # Cartela completa (BINGO!)
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

# Rotas Públicas
@app.route('/')
def home():
    return render_template('index.html')

# Rotas Admin
@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/auth', methods=['POST'])
def admin_auth():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if (username == ADMIN_USERNAME and 
        check_password_hash(ADMIN_PASSWORD_HASH, password)):
        session['admin_logged_in'] = True
        return jsonify({
            'success': True, 
            'redirect': url_for('admin_dashboard')
        })
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', game_state={
        'is_running': game_state.is_running,
        'numbers_drawn': game_state.numbers_drawn,
        'total_cards': len(game_state.cards),
        'winners': game_state.winners
    })

# API - Controles do Jogo
@app.route('/api/admin/start', methods=['POST'])
@admin_required
def start_game():
    if not game_state.is_running:
        game_state.is_running = True
        game_state.auto_draw = True
        game_state.draw_thread = threading.Thread(target=auto_draw)
        game_state.draw_thread.start()
        return jsonify({'success': True})
    return jsonify({'error': 'O jogo já está em andamento'}), 400

@app.route('/api/admin/stop', methods=['POST'])
@admin_required
def stop_game():
    game_state.auto_draw = False
    return jsonify({'success': True})

@app.route('/api/admin/reset', methods=['POST'])
@admin_required
def reset_game():
    game_state.reset()
    socketio.emit('game_reset')
    return jsonify({'success': True})

@app.route('/api/admin/cards/add', methods=['POST'])
@admin_required
def add_card():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
        
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

# WebSockets - Atualização em Tempo Real
@socketio.on('connect')
def handle_connect():
    socketio.emit('game_update', {
        'numbers': game_state.numbers_drawn,
        'winners': [w['id'] for w in game_state.winners],
        'is_running': game_state.is_running
    })

# Inicia o servidor
if __name__ == '__main__':
    socketio.run(app, debug=True)