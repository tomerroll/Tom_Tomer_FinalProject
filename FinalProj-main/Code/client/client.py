import socket
import sys
from PyQt5.QtWidgets import QApplication
from loginScreen import LoginScreen


def main():
    ip = socket.gethostbyname(socket.gethostname())
    port = 5000
    addr = (ip, port)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(addr)
    print(f"[CONNECTED] Client connected to server at {ip}:{port}")

    # Create the application
    app = QApplication(sys.argv)
    window = LoginScreen(app, client)  # Pass the client socket to the LoginScreen
    window.show()
    app.exec()

    # Disconnect the client when the GUI is closed
    try:
        client.send('DISCONNECT'.encode("utf-8"))
    except socket.error as e:
        print(f"Socket error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
