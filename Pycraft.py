from minecraft.networking.connection import Connection
from minecraft.networking.packets import serverbound, clientbound
import time
import threading

SERVER_IP = "Flins_comehome.aternos.me"
SERVER_PORT = 38656
USERNAME = "AFKBot"
PASSWORD = "123456"
AUTO_AUTH = True


def keep_alive(conn):
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
        time.sleep(10)


def start_bot():
    conn = Connection(SERVER_IP, SERVER_PORT, username=USERNAME)

    @conn.register_exception_handler
    def on_exception(exc):
        print("[ERROR] Disconnected:", exc)
        time.sleep(5)
        start_bot()

    @conn.listener(clientbound.play.JoinGamePacket)
    def join_game(packet):
        print("[INFO] Joined server!")
        t = threading.Thread(target=keep_alive, args=(conn,))
        t.daemon = True
        t.start()

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

    print("[INFO] Connecting...")
    conn.connect()

    # Prevent script from exiting
    while True:
        time.sleep(1)


if __name__ == "__main__":
    start_bot()
