import socket
import sys

class ProcClient:
    def start_client(self, host, port=8008):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            print("Enter the data to send:")
            while True:
                data = input()

                if data.lower() == "exit":
                    break

                client_socket.sendall(data.encode())

                print(f"Data sent to {host}:{port}")

            client_socket.shutdown(socket.SHUT_WR)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <receiver_host_ip>")
        sys.exit(1)

    receiver_ip = sys.argv[1]
    cli = ProcClient()
    cli.start_client(receiver_ip)
