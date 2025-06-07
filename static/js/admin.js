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

    // Função para carregar e exibir cartelas
    async function loadCards() {
        try {
            const response = await fetch('/api/admin/cards/list');
            const data = await response.json();
            
            if (data.success) {
                const cardsList = document.getElementById('cardsList');
                cardsList.innerHTML = '';
                
                Object.entries(data.cards).forEach(([cardId, card]) => {
                    const cardEl = document.createElement('div');
                    cardEl.className = 'card-item';
                    cardEl.innerHTML = `
                        <h3>${card.name} <small>(${cardId})</small></h3>
                        <p>Criada em: ${card.created_at}</p>
                        <div class="card-numbers">
                            ${card.numbers.map(num => `<span class="card-number">${num}</span>`).join('')}
                        </div>
                        <div class="card-actions">
                            <button class="copy-btn" data-numbers="${card.numbers.join(',')}">
                                <i class="fas fa-copy"></i> Copiar Números
                            </button>
                        </div>
                    `;
                    cardsList.appendChild(cardEl);
                });
                
                // Adiciona eventos de cópia
                document.querySelectorAll('.copy-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const numbers = btn.getAttribute('data-numbers');
                        navigator.clipboard.writeText(numbers)
                            .then(() => alert('Números copiados para a área de transferência!'))
                            .catch(() => alert('Falha ao copiar. Permita acesso à área de transferência.'));
                    });
                });
            }
        } catch (error) {
            console.error('Erro ao carregar cartelas:', error);
        }
    }

    // Adicionar nova cartela
    if (addCardForm) {
        addCardForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const playerName = document.getElementById('playerName').value;
            const submitBtn = addCardForm.querySelector('button[type="submit"]');
            
            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando...';
                
                const response = await fetch('/api/admin/cards/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: playerName })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(`Cartela ${data.card_id} gerada com sucesso para ${data.name}!`);
                    addCardForm.reset();
                    loadCards(); // Atualiza a lista de cartelas
                } else {
                    alert('Erro ao gerar cartela: ' + (data.error || 'Erro desconhecido'));
                }
            } catch (error) {
                alert('Erro ao conectar com o servidor');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-plus"></i> Gerar Nova Cartela';
            }
        });
    }

    // Botão para atualizar lista de cartelas
    document.getElementById('refreshCardsBtn')?.addEventListener('click', loadCards);

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

    // Carrega as cartelas ao iniciar
    loadCards();
});