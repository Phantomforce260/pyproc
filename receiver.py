import socket
import threading
import queue
import readline

class ProcReceiver:
    def __init__(self):
        self.clients = {}
        self.client_id_counter = 1
        self.lock = threading.Lock()
        self.response_queues = {}

    def handle_client(self, client_socket: socket.socket, addr: tuple, client_id: int) -> None:
        print(f"Client {client_id} connected: {addr}")

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode()
                self.response_queues[client_id].put(message)
        finally:
            print(f"Client {client_id} disconnected")
            with self.lock:
                del self.clients[client_id]
                del self.response_queues[client_id]
            client_socket.close()

    def start_receiver(self, host="0.0.0.0", port=8008) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen()

        print(f"Listening on {host}:{port}")

        threading.Thread(
            target=self.accept_clients,
            args=(server_socket,),
            daemon=True
        ).start()

        self.command_loop()

    def accept_clients(self, server_socket: socket.socket) -> None:
        while True:
            client_socket, addr = server_socket.accept()
            with self.lock:
                client_id = self.client_id_counter
                self.clients[client_id] = client_socket
                self.client_id_counter += 1
                self.response_queues[client_id] = queue.Queue()

            threading.Thread(
                target=self.handle_client,
                args=(client_socket, addr, client_id),
                daemon=True
            ).start()

    def send_and_wait(self, targets, cmd):
        for client_id, client_socket in targets.items():
            client_socket.sendall(cmd.encode())

        for client_id in targets:
            try:
                response = self.response_queues[client_id].get(timeout=5)
                print(f"[Client {client_id}] Response: {response}")
            except queue.Empty:
                print(f"[Client {client_id}] No response (timeout)")

    def command_loop(self):
        while True:
            cmd_input = input("Enter command to send to clients (or 'exit' to quit):\n")
            if cmd_input.lower() == "exit":
                break

            parts = cmd_input.split()
            if len(parts) == 1:
                # Send to all clients
                cmd = parts[0]
                targets = self.clients.copy()
            elif len(parts) == 2:
                cmd, client_id = parts
                client_id = int(client_id)

                if client_id not in self.clients:
                    print(f"No client with ID {client_id}")
                    continue

                targets = {client_id: self.clients[client_id]}
            else:
                print("Invalid command format. Use: <command> [client_id]")
                continue

            if not targets:
                print("No clients connected.")
                continue

            self.send_and_wait(targets, cmd)

if __name__ == "__main__":
    rec = ProcReceiver()
    rec.start_receiver()
