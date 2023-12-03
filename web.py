import socket
import os
    
def handle_request(request):
    lines = request.split('\r\n')
    method, path, _ = lines[0].split(' ')
    content_length_header = next((line for line in lines if line.startswith('Content-Length:')), None)
    print(f"Method: {method}, Path: {path}")

    # 411 Length Required: Check if request has proper Content-Length value
    if method == 'POST' and not content_length_header:
        # 411: Length Required
        print("Content-Length header is required for POST requests")
        response = 'HTTP/1.1 411 Length Required\r\n\r\n'
        return response.encode()
    
    # 403 Forbidden: Check if access to the resource is allowed
    if "private" in path:
        print("Access to the resource is forbidden")
        response = 'HTTP/1.1 403 Forbidden\r\n\r\n'
        return response.encode()

    # 404 Not Found: Check if the requested resource is valid
    if not os.path.exists(path[1:]):
        print("No such file")
        response = 'HTTP/1.1 404 Not Found\r\n\r\n'
        return response.encode()
    
    #400: Check if request is in valid syntax(e.g. valid method)
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        response = 'HTTP/1.1 400 Bad Request\r\n\r\n'
        return response.encode()

    #304

    # 200 OK
    with open(path[1:], 'rb') as file:
        content = file.read()
        response = 'HTTP/1.1 200 OK\r\n'
        response += f'Content-Length: {len(content)}\r\n\r\n'
        response = response.encode() + content

    return response

def start_server(port):
    # Create a socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to a specific address and port
    server_socket.bind(('localhost', port))
    
    # Listen for incoming connections
    server_socket.listen(1)
    print(f'Server listening on port {port}...')
    
    try:
        while True:
            # Accept a connection
            client_socket, client_address = server_socket.accept()
            print(f'\nAccepted connection from {client_address}')
            
            try:
                # Receive data from the client
                request = client_socket.recv(1024).decode()
                
                # Handle the request
                response = handle_request(request)
                
                # Send the response back to the client
                client_socket.sendall(response)
                
            except Exception as e:
                print(f"Error handling request: {e}")

            finally:
                # Close the connection
                client_socket.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
        server_socket.close()

if __name__ == '__main__':
    # Start the server on port 8080
    start_server(8081)

