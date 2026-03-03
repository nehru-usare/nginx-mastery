from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from datetime import datetime

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Simulate a slow 1-second database query or expensive generation task
        time.sleep(1) 
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        timestamp = datetime.now()
        response_text = f"Hello! The simulated slow backend generated this at: {timestamp}\n"
        self.wfile.write(response_text.encode('utf8'))

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), RequestHandler)
    print("Backend listening on port 8080...")
    server.serve_forever()
