import socket
import threading
import sys
from datetime import datetime, timezone
from email.utils import formatdate

cache = {}

def handle_proxy_request(client_socket, request, target_port, port):
# Parse the request
    lines = request.split('\r\n')
    method, path, _ = lines[0].split(' ')  # Extract the method and path from the request
    print(path)
    # Extract the target host from the request
    target_host = lines[1].split(': ')[1].split(':')[0]

    # Modify the path in the request to include the target port
    modified_request = request.replace(f' http://localhost:{port}/{path}', f' http://localhost:{target_port}/{path}', 1)

    # Check if the response is in the cache
    if path in cache:
        print(f"Cache hit for {path}")
        cached_response = cache[path]['response']
        client_socket.sendall(cached_response)
    else:
        # Connect to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))

        # Forward the modified request to the target server
        target_socket.sendall(modified_request.encode())

        # Receive the response from the target server
        target_response = target_socket.recv(4096)
        print(target_response)
        # Cache the response
        cache[path] = {'response': target_response}

        # Send the response back to the client
        client_socket.sendall(target_response)

        # Close the target socket
        target_socket.close()

    # Close the client socket
    client_socket.close()


def start_proxy_server(port, port_list):
    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a specific address and port
    server_socket.bind(('localhost', port))

    # Listen for incoming connections
    server_socket.listen(5)
    print(f'Proxy Server listening on port {port}...')
    
    try:
        while True:
            # Accept a connection from a client
            client_socket, client_address = server_socket.accept()
            print(f'\nAccepted connection from {client_address}')

            try:
                # Receive data from the client
                request = client_socket.recv(4096).decode()

                # For each target port, handle the proxy request in a new thread
                for target_port in port_list:
                    proxy_thread = threading.Thread(target=handle_proxy_request, args=(client_socket, request, target_port, port))
                    proxy_thread.start()

            except Exception as e:
                print(f"Error handling request: {e}")

    except KeyboardInterrupt:
        print("\nProxy Server shutting down...")
        server_socket.close()


if __name__ == '__main__':
    # multiple ports
    port_list = [int(port) for port in sys.argv[1:]]
    
    # Start the proxy server on port 8888 with the list of target ports
    start_proxy_server(8888, port_list)