import socket
import os
from datetime import datetime, timezone
from email.utils import formatdate
    
def handle_request(request):
    lines = request.split('\r\n')
    print(lines[0])
    method, path, _ = lines[0].split(' ')
    print(f"Method: {method}, Path: {path}")
    content_length_header = next((line for line in lines if line.startswith('Content-Length:')), None)
    
    # Check if the requested resource exists

    # 411 Length Required: Check if request has proper Content-Length value
    if method == 'POST':
        if content_length_header is None:
            # Content-Length header is missing
            print("Content-Length header is required for POST requests")
            response = 'HTTP/1.1 411 Length Required\r\n\r\n'
            return response.encode()
        
        try:
            content_length = int(content_length_header.split(':')[1].strip())
            if content_length == 0:
                # Content-Length is present but has a value of 0
                print("Content-Length header must be greater than 0 for POST requests")
                response = 'HTTP/1.1 411 Length Required\r\n\r\n'
                return response.encode()
        except ValueError:
            # Content-Length header has a non-integer value
            print("Invalid Content-Length header value for POST requests")
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
    # Set a specific date and time
    #specific_date = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Now you can use specific_date in your comparison
    last_modified_time = datetime.utcfromtimestamp(os.path.getmtime(path[1:])).replace(tzinfo=timezone.utc)
    if_modified_since_header = next((line for line in lines if line.startswith('If-Modified-Since:')), None)
    if if_modified_since_header:
        try:
            # Extract the date from the header using the correct index
            header_date_str = if_modified_since_header.split(':', 1)[1].strip()
            # Parse the date from the header
            header_date = datetime.strptime(header_date_str, '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc)

            # Compare the last modification time with the date from the header
            if last_modified_time <= header_date:
                # The resource hasn't been modified since the specified date
                print("Resource not modified since the specified date")
                # Retrieve the actual last modification time of the resource
                actual_last_modified_time = datetime.utcfromtimestamp(os.path.getmtime(path[1:])).replace(tzinfo=timezone.utc)

                # Format the last modification time according to the HTTP date format
                last_modified_str = formatdate(actual_last_modified_time.timestamp(), usegmt=True)

                # Include the actual last modification time in the response headers
                response = f'HTTP/1.1 304 Not Modified\r\nLast-Modified: {last_modified_str}\r\n\r\n'
                return response.encode()
        except ValueError:
            # Invalid date format in the header
            print("Invalid If-Modified-Since header format")
            response = 'HTTP/1.1 400 Bad Request\r\n\r\n'
            return response.encode()

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
                request = client_socket.recv(9192).decode()

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
    start_server(8080)

