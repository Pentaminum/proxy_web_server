import socket
import os
    
def handle_request(request):
    return 0

def start_server(port):
    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to a specific address and port
    server_socket.bind(('localhost', port))
    
    # Listen for incoming connections
    server_socket.listen(1)
    print(f'Server listening on port {port}...')
    
    while True:
        # Accept a connection
        client_socket, client_address = server_socket.accept()
        print(f'Accepted connection from {client_address}')
        
        # Receive data from the client
        request = client_socket.recv(1024).decode()
        
        # Handle the request
        response = handle_request(request)
        
        # Send the response back to the client
        client_socket.sendall(response)
        
        # Close the connection
        client_socket.close()

if __name__ == '__main__':
    # Start the server on port 8080
    start_server(8080)