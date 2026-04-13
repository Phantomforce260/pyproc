import socket
import sys
import time

from hyprproc import Hypr
from processes import ProcessManager

class ProcClient:
    def __init__(self):
        self.hypr = Hypr()

    def say_hello(self) -> str:
        return "Hello from client!"

    def hypr_proc(self) -> str:
        return "\n".join([str(c) for c in self.hypr.clients()]) + "\n"

    def handle_command(self, cmd: str) -> str:
        match cmd:
            case "sayHello":
                return self.say_hello()
            case "hypr":
                return self.hypr_proc()
            case _:
                return f"Unknown command: {cmd}"

    def connect(self, host, port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        return client_socket

    def start_client(self, host: str, port=8008):
        while True:
            try:
                print("Attempting to connect to server...")
                sock = self.connect(host, port)
                print("Connected to server")
                while True:
                    data = sock.recv(1024)
                    if not data:
                        print("Server disconnected.")
                        break

                    cmd = data.decode().strip()
                    print(f"Received command: {cmd}")

                    response = self.handle_command(cmd)
                    sock.sendall(response.encode())
            except (ConnectionRefusedError, OSError):
                print("Server not available. Retrying in 3 seconds...")
                time.sleep(3)
            except KeyboardInterrupt:
                print("Client exiting...")
                exit(0)
            finally:
                try:
                    sock.close()
                except:
                    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <server_ip>")
        sys.exit(1)

    server_ip = sys.argv[1]
    cli = ProcClient()
    cli.start_client(server_ip)
