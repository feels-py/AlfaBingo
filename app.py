from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuração simples de autenticação (em produção, use algo mais robusto)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')  # Altere esta senha!

# Dados do bingo
numbers_drawn = []
all_numbers = list(range(1, 76))  # Bingo tradicional vai de 1 a 75
game_started = False

@app.route('/')
def index():
    return render_template('index.html', numbers_drawn=numbers_drawn, game_started=game_started)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
                session['logged_in'] = True
                return redirect(url_for('admin'))
            else:
                return render_template('admin.html', error="Credenciais inválidas"), 401
        return render_template('admin.html')
    
    # Se logado, mostra o painel de admin
    return render_template('admin.html', 
                          numbers_drawn=numbers_drawn, 
                          game_started=game_started,
                          remaining_numbers=len(all_numbers) - len(numbers_drawn))

@app.route('/draw_number', methods=['POST'])
def draw_number():
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    global game_started, numbers_drawn
    
    if not game_started:
        game_started = True
        numbers_drawn = []
    
    available_numbers = [n for n in all_numbers if n not in numbers_drawn]
    if not available_numbers:
        return jsonify({'error': 'Todos os números já foram sorteados'}), 400
    
    new_number = secrets.choice(available_numbers)
    numbers_drawn.append(new_number)
    
    return jsonify({
        'number': new_number,
        'numbers_drawn': numbers_drawn,
        'total_drawn': len(numbers_drawn)
    })

@app.route('/reset_game', methods=['POST'])
def reset_game():
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    global game_started, numbers_drawn
    game_started = False
    numbers_drawn = []
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin'))

@app.route('/get_numbers')
def get_numbers():
    return jsonify({
        'numbers_drawn': numbers_drawn,
        'game_started': game_started
    })

if __name__ == '__main__':
    app.run(debug=True)