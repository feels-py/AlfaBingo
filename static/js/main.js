document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const currentNumberEl = document.getElementById('currentNumber');
    const drawnNumbersGrid = document.getElementById('drawnNumbersGrid');
    const totalDrawnEl = document.getElementById('totalDrawn');
    const winnerScreen = document.getElementById('winnerScreen');
    const winnerName = document.getElementById('winnerName');
    const winnerId = document.getElementById('winnerId');
    const winnerTime = document.getElementById('winnerTime');
    const closeWinnerBtn = document.getElementById('closeWinnerBtn');
    
    // Sons pré-carregados
    const drawSound = new Audio('/static/sounds/draw.mp3');
    const winSound = new Audio('/static/sounds/win.mp3');
    
    // Inicializa a grade de números
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
    
    // Mostra um número sorteado
    function showDrawnNumber(number) {
        // Atualiza o número atual com animação
        currentNumberEl.textContent = number;
        currentNumberEl.style.animation = 'none';
        void currentNumberEl.offsetWidth; // Trigger reflow
        currentNumberEl.style.animation = 'pulse 0.5s ease-in-out';
        
        // Toca o som do sorteio
        drawSound.currentTime = 0;
        drawSound.play().catch(e => console.log("Autoplay prevented:", e));
        
        // Destaca o número na grade
        const numberEl = document.getElementById(`number-${number}`);
        numberEl.classList.add('drawn', 'recent');
        
        // Remove o destaque após 1 segundo
        setTimeout(() => {
            numberEl.classList.remove('recent');
        }, 1000);
    }
    
    // Mostra a tela do vencedor
    function showWinnerScreen(winner) {
        winnerName.textContent = winner.name;
        winnerId.textContent = winner.id;
        winnerTime.textContent = winner.timestamp;
        winnerScreen.style.display = 'flex';
        
        // Toca o som da vitória
        winSound.currentTime = 0;
        winSound.play().catch(e => console.log("Autoplay prevented:", e));
        
        // Efeito de confete
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
    
    // Fecha a tela do vencedor
    closeWinnerBtn.addEventListener('click', () => {
        winnerScreen.style.display = 'none';
    });
    
    // Inicializa a grade de números
    initializeNumberGrid();
    
    // Eventos do Socket.IO
    socket.on('number_drawn', (data) => {
        showDrawnNumber(data.number);
        totalDrawnEl.textContent = data.total;
    });
    
    socket.on('new_winner', (winner) => {
        showWinnerScreen(winner);
    });
    
    socket.on('game_update', (data) => {
        // Atualiza todos os números sorteados
        data.numbers.forEach(num => {
            const numberEl = document.getElementById(`number-${num}`);
            if (numberEl) numberEl.classList.add('drawn');
        });
        
        totalDrawnEl.textContent = data.numbers.length;
    });
    
    socket.on('game_reset', () => {
        // Reseta a interface
        currentNumberEl.textContent = '--';
        initializeNumberGrid();
        totalDrawnEl.textContent = '0';
        winnerScreen.style.display = 'none';
    });
});