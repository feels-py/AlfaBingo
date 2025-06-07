document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const currentNumberEl = document.getElementById('currentNumber');
    const drawnNumbersGrid = document.getElementById('drawnNumbersGrid');
    const totalDrawnEl = document.getElementById('totalDrawn');
    const winnersList = document.getElementById('winnersList');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const winnersContainer = document.getElementById('winnersContainer');
    
    // Cria os espaços para os números de 1 a 75
    function initializeNumberGrid() {
        drawnNumbersGrid.innerHTML = '';
        for (let i = 1; i <= 75; i++) {
            const numberEl = document.createElement('div');
            numberEl.className = 'drawn-number';
            numberEl.textContent = i;
            numberEl.id = `number-${i}`;
            drawnNumbersGrid.appendChild(numberEl);
        }
    }
    
    // Atualiza o status do jogo
    function updateGameStatus(isRunning) {
        if (isRunning) {
            statusIndicator.style.color = '#2ecc71';
            statusText.textContent = 'Sorteio em andamento';
        } else {
            statusIndicator.style.color = '#e74c3c';
            statusText.textContent = 'Sorteio pausado';
        }
    }
    
    // Mostra um número sorteado
    function showDrawnNumber(number) {
        // Atualiza o número atual com animação
        currentNumberEl.textContent = number;
        currentNumberEl.style.animation = 'none';
        void currentNumberEl.offsetWidth; // Trigger reflow
        currentNumberEl.style.animation = 'pulse 0.5s ease-in-out';
        
        // Destaca o número na grade
        const numberEl = document.getElementById(`number-${number}`);
        numberEl.classList.add('drawn', 'recent');
        
        // Remove o destaque após 3 segundos
        setTimeout(() => {
            numberEl.classList.remove('recent');
        }, 3000);
    }
    
    // Mostra um vencedor
    function showWinner(winner) {
        const winnerEl = document.createElement('div');
        winnerEl.className = 'winner-card';
        winnerEl.innerHTML = `
            <h3>${winner.name}</h3>
            <p>Cartela: ${winner.id}</p>
            <p class="win-time">${winner.timestamp}</p>
        `;
        winnersList.prepend(winnerEl);
        
        // Mostra o container de vencedores se estiver oculto
        winnersContainer.style.display = 'block';
        
        // Animação de confete
        createConfettiEffect();
    }
    
    // Efeito de confete
    function createConfettiEffect() {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
    
    // Inicializa a grade de números
    initializeNumberGrid();
    
    // Eventos do Socket.IO
    socket.on('connect', () => {
        console.log('Conectado ao servidor de sorteio');
    });
    
    socket.on('number_drawn', (data) => {
        showDrawnNumber(data.number);
        totalDrawnEl.textContent = data.total;
    });
    
    socket.on('new_winner', (winner) => {
        showWinner(winner);
        playWinSound();
    });
    
    socket.on('game_paused', (data) => {
        updateGameStatus(false);
        if (data.reason === 'winner_found') {
            const msg = 'Sorteio pausado automaticamente porque temos um ganhador!';
            console.log(msg);
            alert(msg);
        }
    });
    
    socket.on('game_update', (data) => {
        // Atualiza todos os números sorteados
        data.numbers.forEach(num => {
            const numberEl = document.getElementById(`number-${num}`);
            if (numberEl) numberEl.classList.add('drawn');
        });
        
        totalDrawnEl.textContent = data.numbers.length;
        updateGameStatus(data.is_running);
        
        // Atualiza lista de ganhadores
        if (data.winners && data.winners.length > 0) {
            winnersList.innerHTML = '';
            data.winners.forEach(winner => {
                showWinner(winner);
            });
        } else {
            winnersContainer.style.display = 'none';
        }
    });
    
    socket.on('game_reset', () => {
        // Reseta a interface
        currentNumberEl.textContent = '--';
        initializeNumberGrid();
        totalDrawnEl.textContent = '0';
        winnersList.innerHTML = '';
        winnersContainer.style.display = 'none';
        updateGameStatus(false);
    });
    
    // Efeitos de áudio
    function playWinSound() {
        const winSound = new Audio('/static/sounds/win.mp3');
        winSound.play().catch(e => console.log("Autoplay prevented:", e));
    }
});