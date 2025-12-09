// game.js

// DOM Elementleri
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const container = document.getElementById('gameContainer');
const statusEl = document.getElementById('status');
const positionEl = document.getElementById('position');
const botCountEl = document.getElementById('bot_count');

// Oyun Değişkenleri
let playerX = 0;
let playerY = 0;
const playerSize = 10;
const botSize = 5;
let MAP_SIZE = 1000; 

let bots = []; 
const heldKeys = {};

// WebSocket Bağlantısı
const socket = new WebSocket("ws://localhost:8080");

// --- WebSocket İşleyicileri ---

socket.onopen = () => {
    statusEl.textContent = "BAĞLANDI";
    console.log("Sunucuya bağlandı.");
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'init') {
        // Başlangıç verilerini al
        playerX = data.player_pos.x;
        playerY = data.player_pos.y;
        MAP_SIZE = data.map_size;
        botCountEl.textContent = data.bot_count;
        
        // Canvas boyutunu harita büyüklüğüne ayarla
        canvas.width = MAP_SIZE;
        canvas.height = MAP_SIZE;

    } else if (data.type === 'update') {
        // Sunucudan gelen güncel durumu al
        playerX = data.player.x;
        playerY = data.player.y;
        bots = data.bots; 
        
        positionEl.textContent = `${playerX.toFixed(0)}, ${playerY.toFixed(0)}`;
    }
};

socket.onclose = () => {
    statusEl.textContent = "BAĞLANTI KOPTU";
};

socket.onerror = (error) => {
    statusEl.textContent = "HATA";
    console.error("WebSocket Hatası:", error);
};

// --- Kullanıcı Girdileri ---

document.addEventListener('keydown', (e) => {
    if (['w', 'a', 's', 'd'].includes(e.key.toLowerCase())) {
        heldKeys[e.key.toLowerCase()] = true;
    }
});

document.addEventListener('keyup', (e) => {
    if (['w', 'a', 's', 'd'].includes(e.key.toLowerCase())) {
        heldKeys[e.key.toLowerCase()] = false;
    }
});

// Sunucuya Hareket Komutu Gönderme
function sendMovement() {
    let direction = null;
    if (heldKeys['w']) direction = "up";
    else if (heldKeys['s']) direction = "down";
    else if (heldKeys['a']) direction = "left";
    else if (heldKeys['d']) direction = "right";

    if (direction && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "move", direction: direction }));
    }
}

// Kamera Takibi
function updateCamera() {
    const viewCenterX = container.clientWidth / 2;
    const viewCenterY = container.clientHeight / 2;
    
    const cameraX = viewCenterX - playerX;
    const cameraY = viewCenterY - playerY;

    let finalX = Math.min(0, Math.max(cameraX, container.clientWidth - MAP_SIZE));
    let finalY = Math.min(0, Math.max(cameraY, container.clientHeight - MAP_SIZE));

    // CSS transform kullanarak Canvas'ı kaydır
    canvas.style.transform = `translate(${finalX}px, ${finalY}px)`;
}

// --- Oyun Çizim Döngüsü ---

function gameLoop() {
    // 1. Temizle
    ctx.clearRect(0, 0, MAP_SIZE, MAP_SIZE);

    // 2. Harita Zeminini Çiz
    ctx.fillStyle = "#225522"; 
    ctx.fillRect(0, 0, MAP_SIZE, MAP_SIZE);
    
    // 3. 100 Botu Çiz
    ctx.fillStyle = "yellow"; 
    bots.forEach(bot => {
        ctx.beginPath();
        ctx.arc(bot.x, bot.y, botSize, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // 4. Oyuncuyu Çiz (Merkezde)
    ctx.fillStyle = "red";
    ctx.beginPath();
    ctx.arc(playerX, playerY, playerSize, 0, Math.PI * 2);
    ctx.fill();
    
    // 5. Kamerayı Güncelle (Kaydırma)
    updateCamera();

    // 6. Hareketi Sunucuya bildir
    sendMovement();

    requestAnimationFrame(gameLoop); 
}

gameLoop(); // Döngüyü başlat
