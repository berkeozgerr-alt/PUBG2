# server.py
import asyncio
import websockets
import json
import random

# --- Oyun Ayarları ---
MAP_SIZE = 1000  # Basit bir kare harita (1000x1000)
BOT_COUNT = 100
PLAYER_SPEED = 5
BOT_SPEED = 3

# --- Oyun Durumu ---
# Oyuncu (Şimdilik tek bir ana oyuncu konumu tutuluyor)
PLAYER_POSITION = {"x": MAP_SIZE // 2, "y": MAP_SIZE // 2}
CONNECTIONS = set() # Bağlı olan tüm istemcileri tutar

# 100 Botun Başlatılması
BOTS = []
for i in range(BOT_COUNT):
    BOTS.append({
        "id": f"bot_{i}",
        "x": random.randint(0, MAP_SIZE),
        "y": random.randint(0, MAP_SIZE),
        "target_x": random.randint(0, MAP_SIZE),
        "target_y": random.randint(0, MAP_SIZE)
    })

# --- Yardımcı Fonksiyonlar ---

def update_bot_positions():
    """Tüm botların konumlarını basit AI ile günceller."""
    for bot in BOTS:
        # Bot hedefine doğru hareket eder
        dx = bot["target_x"] - bot["x"]
        dy = bot["target_y"] - bot["y"]

        # Hedefe yaklaştıysa yeni bir hedef belirle
        if abs(dx) < BOT_SPEED and abs(dy) < BOT_SPEED:
            bot["target_x"] = random.randint(0, MAP_SIZE)
            bot["target_y"] = random.randint(0, MAP_SIZE)
            continue
        
        # Normalleştirme (botun sabit hızda hareket etmesi için)
        distance = (dx**2 + dy**2)**0.5
        if distance > 0:
            bot["x"] += (dx / distance) * BOT_SPEED
            bot["y"] += (dy / distance) * BOT_SPEED

        # Harita sınırlarında tut
        bot["x"] = max(0, min(MAP_SIZE, bot["x"]))
        bot["y"] = max(0, min(MAP_SIZE, bot["y"]))


async def bot_update_loop():
    """Belirli aralıklarla botları günceller ve tüm oyunculara yayar."""
    while True:
        update_bot_positions()
        
        # Oyuncuya ve botlara ait güncel veriyi hazırla
        game_state = {
            "type": "update",
            "player": PLAYER_POSITION,
            # Bot konumlarını tam sayıya çevirerek veri miktarını azaltırız
            "bots": [{"id": b["id"], "x": int(b["x"]), "y": int(b["y"])} for b in BOTS] 
        }
        
        # Tüm bağlı istemcilere (oyunculara) durumu yayınla
        websockets.broadcast(CONNECTIONS, json.dumps(game_state))
        
        await asyncio.sleep(0.1)  # Saniyede 10 kez (100ms) güncelleme

# --- WebSocket Sunucusu İşleyicisi ---

async def game_server(websocket, path):
    """Oyuncu bağlantılarını yönetir ve gelen hareket komutlarını işler."""
    
    # Yeni bağlantıyı kaydet
    CONNECTIONS.add(websocket)
    print(f"Yeni bağlantı: {websocket.remote_address}. Toplam bağlantı: {len(CONNECTIONS)}")

    try:
        # Oyuncuya başlangıç konumunu ve harita büyüklüğünü gönder
        init_message = {
            "type": "init", 
            "player_pos": PLAYER_POSITION, 
            "map_size": MAP_SIZE, 
            "bot_count": BOT_COUNT
        }
        await websocket.send(json.dumps(init_message))

        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Oyuncudan gelen hareket komutunu işle
                if data.get("type") == "move":
                    direction = data.get("direction")
                    
                    # Oyuncu hareketini güncelle
                    if direction == "up":
                        PLAYER_POSITION["y"] -= PLAYER_SPEED
                    elif direction == "down":
                        PLAYER_POSITION["y"] += PLAYER_SPEED
                    elif direction == "left":
                        PLAYER_POSITION["x"] -= PLAYER_SPEED
                    elif direction == "right":
                        PLAYER_POSITION["x"] += PLAYER_SPEED
                    
                    # Oyuncuyu harita sınırında tut
                    PLAYER_POSITION["x"] = max(0, min(MAP_SIZE, PLAYER_POSITION["x"]))
                    PLAYER_POSITION["y"] = max(0, min(MAP_SIZE, PLAYER_POSITION["y"]))
                    
                
            except json.JSONDecodeError:
                print(f"Geçersiz JSON alındı: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        pass # Bağlantı normal şekilde kapandı
    finally:
        # Bağlantı koptuğunda listeden kaldır
        CONNECTIONS.remove(websocket)
        print(f"Bağlantı kapandı. Kalan bağlantı: {len(CONNECTIONS)}")

# --- Sunucu Başlatma ---

async def main():
    """Ana eşzamanlı fonksiyon, sunucuyu ve bot döngüsünü başlatır."""
    # Bot hareket döngüsünü arka planda başlat
    asyncio.create_task(bot_update_loop())
    
    # WebSocket sunucusunu başlat
    async with websockets.serve(game_server, "localhost", 8080):
        print("Python Oyun Sunucusu 'ws://localhost:8080' adresinde başlatıldı...")
        await asyncio.Future()  # Sonsuza kadar çalışmasını sağla

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
