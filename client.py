import socket
import sys

class ProcClient:
    def say_hello(self):
        return "Hello from client!"

    def handle_command(self, cmd: str):
        if cmd == "sayHello":
            return self.say_hello()
        else:
            return f"Unknown command: {cmd}"

    def start_client(self, host: str, port=8008):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            print(f"Connected to receiver at {host}:{port}")

            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    cmd = data.decode().strip()
                    print(f"Received command: {cmd}")
                    response = self.handle_command(cmd)
                    client_socket.sendall(response.encode())
            except KeyboardInterrupt:
                print("Client exiting...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <server_ip>")
        sys.exit(1)

    server_ip = sys.argv[1]
    cli = ProcClient()
    cli.start_client(server_ip)
