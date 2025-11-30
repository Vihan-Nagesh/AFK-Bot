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
RECONNECT_DELAY = 30  # safer reconnect delay
MAX_SESSION_TIME = 60 * 60  # optional max session 1 hour

# --- HUMAN-LIKE ACTIONS ---
def human_like_behavior(conn):
    """Perform random actions to look human."""
    yaw = random.uniform(0, 360)
    start_time = time.time()

    while conn.connected:
        # Randomly move small distances
        try:
            # Random chance to move or look around
            if random.random() < 0.5:
                # Random look direction
                yaw += random.uniform(-30, 30)
                pkt = serverbound.play.PlayerPositionAndRotationPacket()
                pkt.x = math.cos(math.radians(yaw)) * random.uniform(0, 0.5)
                pkt.y = 0
                pkt.z = math.sin(math.radians(yaw)) * random.uniform(0, 0.5)
                pkt.yaw = yaw
                pkt.pitch = random.uniform(-10, 10)
                pkt.on_ground = True
                conn.write_packet(pkt)

            # Random jump
            if random.random() < 0.1:
                jump_pkt = serverbound.play.PlayerAbilitiesPacket()
                jump_pkt.flags = 0x02
                conn.write_packet(jump_pkt)

            # Random idle pauses
            time.sleep(random.uniform(5, 20))

            # Optional: end session after max session time to simulate human
            if MAX_SESSION_TIME and time.time() - start_time > MAX_SESSION_TIME:
                print("[INFO] Max session reached. Logging out.")
                conn.disconnect()
                return

        except Exception as e:
            print("[ERROR] Human-like behavior stopped:", e)
            break


def auto_keep_alive(conn):
    """Send minimal keep-alive packets to prevent timeout."""
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
        except:
            break
        time.sleep(15)  # slightly longer interval for safer behavior


def run_bot():
    """Main bot loop with safer reconnects and human-like behavior."""
    while True:
        try:
            conn = Connection(SERVER_IP, SERVER_PORT, username=USERNAME)
            print("[INFO] Connecting...")

            @conn.register_exception_handler
            def on_exception(exc):
                print("[ERROR] Disconnected:", exc)
                conn.connected = False

            @conn.listener(clientbound.play.DisconnectPacket)
            def on_disconnect(packet):
                print(f"[INFO] Disconnected: {packet.json_data}")
                conn.connected = False

            @conn.listener(clientbound.play.JoinGamePacket)
            def join_game(packet):
                print("[INFO] Joined server!")

                # Start threads for human-like behavior
                t1 = threading.Thread(target=auto_keep_alive, args=(conn,))
                t1.daemon = True
                t1.start()

                t2 = threading.Thread(target=human_like_behavior, args=(conn,))
                t2.daemon = True
                t2.start()

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

            conn.connect()

            # Keep main thread alive while connected
            while conn.connected:
                time.sleep(1)

        except Exception as e:
            print("[ERROR] Connection failed:", e)

        # Safer reconnect delay to reduce detection
        wait_time = RECONNECT_DELAY + random.randint(0, 20)
        print(f"[INFO] Reconnecting in {wait_time} seconds...")
        time.sleep(wait_time)


if __name__ == "__main__":
    run_bot()
