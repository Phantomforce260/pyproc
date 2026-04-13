import socket

class ProcReceiver:
    def start_receiver(self, host="0.0.0.0", port=12345):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.listen(5)

            print(f"Listening on {host}:{port}...")

            while True:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Connected by {client_address}")
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        print(f"Received data: {data.decode()}")


if __name__ == "__main__":
    rec = ProcReceiver()
    rec.start_receiver(port=8008)
