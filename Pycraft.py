from minecraft.networking.connection import Connection
from minecraft.networking.packets import serverbound, clientbound
import threading
import time
import random
import math

# --- CONFIG ---
SERVER_IP = "Flins_comehome.aternos.me"
SERVER_PORT = 38656
USERNAME = "AFKBot"
PASSWORD = "123456"
AUTO_AUTH = True
RECONNECT_DELAY = 5  # seconds before reconnecting


# --- FUNCTIONS ---
def keep_alive(conn):
    """Send periodic packets to prevent disconnection."""
    while conn.connected:
        try:
            pkt = serverbound.play.PlayerPositionAndRotationPacket()
            pkt.x = 0
            pkt.y = 0
            pkt.z = 0
            pkt.yaw = 0
            pkt.pitch = 0
            pkt.on_ground = True
            conn.write_packet(pkt)
        except Exception as e:
            print("[ERROR] Keep-alive stopped:", e)
            break
        time.sleep(10)


def afk_movement(conn):
    """Random small movements and occasional jumps to avoid AFK kick."""
    yaw = random.uniform(0, 360)
    while conn.connected:
        try:
            # Move forward for 1–2 seconds
            duration = random.uniform(1.0, 2.5)
            start_time = time.time()
            while time.time() - start_time < duration and conn.connected:
                pkt = serverbound.play.PlayerPositionAndRotationPacket()
                pkt.x = math.cos(math.radians(yaw)) * 0.3
                pkt.y = 0
                pkt.z = math.sin(math.radians(yaw)) * 0.3
                pkt.yaw = yaw
                pkt.pitch = 0
                pkt.on_ground = True
                conn.write_packet(pkt)

                # Occasional jump (10% chance per step)
                if random.random() < 0.1:
                    jump_pkt = serverbound.play.PlayerAbilitiesPacket()
                    jump_pkt.flags = 0x02
                    conn.write_packet(jump_pkt)

                time.sleep(0.5)  # step interval

            # Randomly change direction
            yaw += random.uniform(-30, 30)

        except Exception as e:
            print("[ERROR] AFK movement stopped:", e)
            break


def run_bot():
    """Main loop: connect, stay online, and auto-reconnect."""
    while True:
        try:
            conn = Connection(SERVER_IP, SERVER_PORT, username=USERNAME)
            print("[INFO] Connecting...")

            # Exception handler
            @conn.register_exception_handler
            def on_exception(exc):
                print("[ERROR] Disconnected:", exc)
                conn.connected = False

            # Disconnect handler (handles kicks too)
            @conn.listener(clientbound.play.DisconnectPacket)
            def on_disconnect(packet):
                print(f"[INFO] Disconnected from server: {packet.json_data}")
                conn.connected = False

            # Join game
            @conn.listener(clientbound.play.JoinGamePacket)
            def join_game(packet):
                print("[INFO] Joined server!")

                # Start keep-alive and AFK threads
                t1 = threading.Thread(target=keep_alive, args=(conn,))
                t1.daemon = True
                t1.start()

                t2 = threading.Thread(target=afk_movement, args=(conn,))
                t2.daemon = True
                t2.start()

            # Chat handler for auto auth
            @conn.listener(clientbound.play.ChatMessagePacket)
            def handle_chat(packet):
                msg = packet.json_data.lower()
                print("[CHAT]", msg)

                if AUTO_AUTH:
                    if "register" in msg:
                        conn.write_packet(serverbound.play.ChatPacket(
                            message=f"/register {PASSWORD} {PASSWORD}"
                        ))
                    if "login" in msg:
                        conn.write_packet(serverbound.play.ChatPacket(
                            message=f"/login {PASSWORD}"
                        ))

            # Connect
            conn.connect()

            # Main thread waits while connected
            while conn.connected:
                time.sleep(1)

        except Exception as e:
            print("[ERROR] Connection failed:", e)

        print(f"[INFO] Reconnecting in {RECONNECT_DELAY} seconds...")
        time.sleep(RECONNECT_DELAY)


# --- RUN BOT ---
if __name__ == "__main__":
    run_bot()
