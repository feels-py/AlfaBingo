document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    
    // Login Admin
    const loginForm = document.getElementById('adminLoginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            try {
                const response = await fetch('/admin/auth', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        username: document.getElementById('username').value,
                        password: document.getElementById('password').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert(data.error || 'Credenciais inválidas');
                }
            } catch (error) {
                alert('Erro ao conectar com o servidor');
            }
        });
    }

    // Controles do Jogo
    const startBtn = document.getElementById('startGameBtn');
    const stopBtn = document.getElementById('stopGameBtn');
    const resetBtn = document.getElementById('resetGameBtn');
    const addCardForm = document.getElementById('addCardForm');

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            const response = await fetch('/api/admin/start', {method: 'POST'});
            const data = await response.json();
            if (data.success) {
                startBtn.disabled = true;
                stopBtn.disabled = false;
                document.getElementById('gameStatus').textContent = 'Em andamento';
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            const response = await fetch('/api/admin/stop', {method: 'POST'});
            const data = await response.json();
            if (data.success) {
                startBtn.disabled = false;
                stopBtn.disabled = true;
                document.getElementById('gameStatus').textContent = 'Pausado';
            }
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (confirm('Tem certeza que deseja reiniciar o jogo?')) {
                const response = await fetch('/api/admin/reset', {method: 'POST'});
                if (response.ok) {
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    document.getElementById('gameStatus').textContent = 'Parado';
                    document.getElementById('numbersDrawn').textContent = '0';
                    document.getElementById('winnersList').innerHTML = '';
                }
            }
        });
    }

    if (addCardForm) {
        addCardForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const playerName = document.getElementById('playerName').value;
            
            try {
                const response = await fetch('/api/admin/cards/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: playerName })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(`Cartela ${data.card_id} adicionada para ${playerName}!`);
                    addCardForm.reset();
                } else {
                    alert('Erro ao adicionar cartela: ' + (data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro ao conectar com o servidor');
            }
        });
    }

    // Atualizações em tempo real
    socket.on('number_drawn', (data) => {
        const counter = document.getElementById('numbersDrawn');
        if (counter) counter.textContent = data.total;
    });

    socket.on('new_winner', (winner) => {
        const winnersList = document.getElementById('winnersList');
        if (winnersList) {
            const winnerEl = document.createElement('div');
            winnerEl.className = 'winner-card';
            winnerEl.innerHTML = `
                <h3>${winner.name}</h3>
                <p>Cartela: ${winner.id}</p>
                <small>${winner.timestamp}</small>
            `;
            winnersList.prepend(winnerEl);
        }
    });

    socket.on('game_reset', () => {
        if (document.getElementById('numbersDrawn')) {
            document.getElementById('numbersDrawn').textContent = '0';
        }
        if (document.getElementById('winnersList')) {
            document.getElementById('winnersList').innerHTML = '';
        }
    });
});