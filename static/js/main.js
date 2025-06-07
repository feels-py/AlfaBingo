document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    
    // Elementos da UI
    const currentNumberEl = document.getElementById('currentNumber');
    const drawnNumbersEl = document.getElementById('drawnNumbers');
    const winnersContainer = document.getElementById('winnersContainer');
    const totalDrawnEl = document.getElementById('totalDrawn');
    
    // Efeitos de áudio
    const drawSound = new Audio('/static/sounds/draw.mp3');
    const winSound = new Audio('/static/sounds/win.mp3');
    const backgroundMusic = new Audio('/static/sounds/background.mp3');
    
    // Configura música de fundo
    backgroundMusic.loop = true;
    backgroundMusic.volume = 0.3;
    
    // Eventos do Socket.IO
    socket.on('connect', () => {
        console.log('Conectado ao servidor de bingo');
    });
    
    socket.on('number_drawn', (data) => {
        animateNumber(data.number);
        updateDrawnNumbers(data.numbers);
        totalDrawnEl.textContent = data.total;
        playDrawSound();
    });
    
    socket.on('new_winner', (winner) => {
        displayWinner(winner);
        playWinSound();
        createConfettiEffect();
    });
    
    socket.on('game_update', (data) => {
        updateDrawnNumbers(data.numbers);
        totalDrawnEl.textContent = data.numbers.length;
        
        if (data.winners && data.winners.length > 0) {
            winnersContainer.innerHTML = '';
            data.winners.forEach(winner => {
                displayWinner(winner);
            });
        }
    });
    
    socket.on('game_reset', () => {
        currentNumberEl.textContent = '--';
        drawnNumbersEl.innerHTML = '';
        winnersContainer.innerHTML = '';
        totalDrawnEl.textContent = '0';
    });
    
    // Funções de animação
    function animateNumber(number) {
        currentNumberEl.textContent = number;
        currentNumberEl.classList.add('animate');
        
        setTimeout(() => {
            currentNumberEl.classList.remove('animate');
        }, 1000);
    }
    
    function updateDrawnNumbers(numbers) {
        drawnNumbersEl.innerHTML = numbers.map(num => 
            `<span class="drawn-number">${num}</span>`
        ).join('');
    }
    
    function displayWinner(winner) {
        const winnerCard = document.createElement('div');
        winnerCard.className = 'winner-card highlight';
        winnerCard.innerHTML = `
            <h3>${winner.name}</h3>
            <p>Cartela: ${winner.id}</p>
            <p class="win-time">${winner.timestamp}</p>
        `;
        
        winnersContainer.prepend(winnerCard);
        
        setTimeout(() => {
            winnerCard.classList.remove('highlight');
        }, 2000);
    }
    
    function playDrawSound() {
        drawSound.currentTime = 0;
        drawSound.play().catch(e => console.log("Autoplay prevented:", e));
    }
    
    function playWinSound() {
        winSound.currentTime = 0;
        winSound.play().catch(e => console.log("Autoplay prevented:", e));
    }
    
    function createConfettiEffect() {
        const colors = ['#ff6f00', '#e91e63', '#4caf50', '#2196f3', '#ffeb3b'];
        
        for (let i = 0; i < 100; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = `${Math.random() * 100}vw`;
            confetti.style.animationDelay = `${Math.random() * 2}s`;
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                confetti.remove();
            }, 5000);
        }
    }
    
    // Controles de música
    const musicToggle = document.getElementById('musicToggle');
    if (musicToggle) {
        musicToggle.addEventListener('click', () => {
            if (backgroundMusic.paused) {
                backgroundMusic.play();
                musicToggle.innerHTML = '<i class="fas fa-volume-up"></i>';
            } else {
                backgroundMusic.pause();
                musicToggle.innerHTML = '<i class="fas fa-volume-mute"></i>';
            }
        });
    }
    
    // Inicia música de fundo após interação do usuário
    document.body.addEventListener('click', () => {
        if (backgroundMusic.paused) {
            backgroundMusic.play().catch(e => console.log("Autoplay prevented:", e));
        }
    }, { once: true });
});