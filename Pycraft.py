from minecraft.networking.connection import Connection
from minecraft.networking.packets import serverbound, clientbound
import time
import threading
import random

SERVER_IP = "Flins_comehome.aternos.me"
SERVER_PORT = 38656
USERNAME = "AFKBot"
PASSWORD = "123456"
AUTO_AUTH = True
RECONNECT_DELAY = 5  # seconds before reconnecting


def afk_movement(conn):
    """Random movement and jumps to avoid AFK kick."""
    directions = ['forward', 'back', 'left', 'right']
    while conn.connected:
        try:
            pkt = serverbound.play.PlayerPositionAndRotationPacket()
            pkt.x = random.uniform(-1, 1)
            pkt.y = 0
            pkt.z = random.uniform(-1, 1)
            pkt.yaw = random.uniform(0, 360)
            pkt.pitch = 0
            pkt.on_ground = True
            conn.write_packet(pkt)

            if random.random() < 0.3:  # 30% chance to jump
                jump_pkt = serverbound.play.PlayerAbilitiesPacket()
                jump_pkt.flags = 0x02
                conn.write_packet(jump_pkt)

        except Exception as e:
            print("[ERROR] AFK movement stopped:", e)
            break

        time.sleep(random.uniform(5, 15))


def keep_alive(conn):
    """Send periodic packets to stay online."""
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


def run_bot():
    """Main loop: connect, handle events, and auto-reconnect safely."""
    while True:  # infinite loop to reconnect indefinitely
        try:
            conn = Connection(SERVER_IP, SERVER_PORT, username=USERNAME)
            print("[INFO] Connecting...")

            # Exception handler
            @conn.register_exception_handler
            def on_exception(exc):
                print("[ERROR] Disconnected:", exc)
                conn.connected = False  # stop threads

            # Disconnect handler (handles kicks too)
            @conn.listener(clientbound.play.DisconnectPacket)
            def on_disconnect(packet):
                print(f"[INFO] Disconnected from server: {packet.json_data}")
                conn.connected = False

            # On join
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

            # Connect to server
            conn.connect()

            # Keep main thread alive while connected
            while conn.connected:
                time.sleep(1)

        except Exception as e:
            print("[ERROR] Connection failed:", e)

        # Reconnect delay
        print(f"[INFO] Reconnecting in {RECONNECT_DELAY} seconds...")
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    run_bot()
