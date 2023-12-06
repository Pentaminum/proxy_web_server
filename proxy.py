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
    content_length_header = next((line for line in lines if line.startswith('Content-Length:')), None)

    if path in cache and 'Last-Modified' in cache[path]:
        # Add If-Modified-Since header to the request
        if 'If-Modified-Since' not in request:
            last_modified_date = cache[path]['Last-Modified']
            request += f'If-Modified-Since: {last_modified_date}\r\n'

    # 411 Length Required: Check if request has proper Content-Length value
    if method == 'POST':
        if content_length_header is None:
            # Content-Length header is missing
            print("Content-Length header is required for POST requests")
            response = 'HTTP/1.1 411 Length Required\r\n\r\n'
            client_socket.sendall(response.encode())
            client_socket.close()
            return
        
        try:
            content_length = int(content_length_header.split(':')[1].strip())
            if content_length == 0:
                # Content-Length is present but has a value of 0
                print("Content-Length header must be greater than 0 for POST requests")
                response = 'HTTP/1.1 411 Length Required\r\n\r\n'
                client_socket.sendall(response.encode())
                client_socket.close()
                return
        except ValueError:
            # Content-Length header has a non-integer value
            print("Invalid Content-Length header value for POST requests")
            response = 'HTTP/1.1 411 Length Required\r\n\r\n'
            client_socket.sendall(response.encode())
            client_socket.close()
            return
        
    #400: Check if request is in valid syntax(e.g. valid method)
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        response = 'HTTP/1.1 400 Bad Request\r\n\r\n'
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    # Modify the path in the request to include the target port
    modified_request = request.replace(f' http://localhost:{port}/{path}', f' http://localhost:{target_port}/{path}', 1)

    # Connect to the target server
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((target_host, target_port))

    # Forward the modified request to the target server
    target_socket.sendall(modified_request.encode())

    # Receive the response from the target server
    target_response = target_socket.recv(9192)

    # Check for a 304 Not Modified response
    if 'HTTP/1.1 304 Not Modified' in target_response.decode():
            print(f"Received 304 Not Modified for {path}")
            print(f"Cache hit for {path}")
            # Use the cached response
            cache[path]['response'] = target_response
            cached_response = cache[path]['response']
            client_socket.sendall(cached_response)
            
    else:
        if path in cache:
            # Update the cache with the new response
            cache[path]['response'] = target_response
            # Optionally, update the 'last-modified' timestamp in the cache if applicable
            if 'last-modified' in cache[path]:
                # Update the timestamp based on the target server's 'last-modified' header
                # Assuming the 'last-modified' header is present in the target response
                # You might need to adjust this part based on the actual structure of your response
                last_modified_header = target_response.decode().split('Last-Modified: ', 1)[1].split('\r\n', 1)[0] if 'Last-Modified' in target_response.decode() else None
                cache[path]['last-modified'] = last_modified_header
        else:
            # Cache the new response
            # Extract the 'last-modified' header from the target response if applicable
            last_modified_header = target_response.decode().split('Last-Modified: ', 1)[1].split('\r\n', 1)[0] if 'Last-Modified' in target_response.decode() else None
            cache[path] = {'response': target_response, 'last-modified': last_modified_header}

        # Send the response back to the client
        client_socket.sendall(target_response)


    target_socket.close()
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
                request = client_socket.recv(9192).decode()

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