import os
import json
import http.server
import socketserver
from http import HTTPStatus
import urllib.request
import urllib.parse
import urllib.error

# Your Digital Ocean Agent configuration
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "https://agent-ac90c60eec7af7997858-wur6b.ondigitalocean.app/api/v1/chat/completions")
AGENT_ACCESS_KEY = os.getenv("AGENT_ACCESS_KEY", "6_WDRN-yATG7NGl3-dfUqtk3xhkaDE-N")

class AgentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve a simple HTML page with information about the agent API
        if self.path == '/':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>DO GenAI Agent API</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>Digital Ocean GenAI Agent API</h1>
                <p>This server forwards requests to your Digital Ocean GenAI agent.</p>
                <h2>Usage:</h2>
                <p>Send a POST request to <code>/ask</code> with a JSON body containing your question:</p>
                <pre>
{{
  "message": "What is the capital of France?"
}}
                </pre>
                <p>The agent will process your question and return a response.</p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        # Handle POST requests to the /ask endpoint
        if self.path.startswith('/ask'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the incoming JSON data
                request_data = json.loads(post_data.decode('utf-8'))
                user_message = request_data.get('message', '')
                
                # Prepare the request to the Digital Ocean agent
                agent_request = {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ],
                    "stream": False,
                    "include_functions_info": False,
                    "include_retrieval_info": False,
                    "include_guardrails_info": False
                }
                
                # Additional parameters if provided
                if 'include_retrieval_info' in request_data:
                    agent_request['include_retrieval_info'] = request_data['include_retrieval_info']
                
                # Send the request to the agent endpoint
                req = urllib.request.Request(
                    AGENT_ENDPOINT,
                    data=json.dumps(agent_request).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {AGENT_ACCESS_KEY}'
                    }
                )
                
                with urllib.request.urlopen(req) as response:
                    agent_response = response.read()
                    
                    # Return the agent's response
                    self.send_response(HTTPStatus.OK)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(agent_response)
                    
            except json.JSONDecodeError:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": "Invalid JSON"}).encode('utf-8')
                self.wfile.write(error_msg)
                
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": f"Agent API error: {e.reason}"}).encode('utf-8')
                self.wfile.write(error_msg)
                
            except Exception as e:
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": str(e)}).encode('utf-8')
                self.wfile.write(error_msg)
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            self.wfile.write(b'Not Found')

# Make the server accessible from outside
port = int(os.getenv('PORT', 80))
print(f'Starting server on port {port}')
print(f'Access the agent through the /ask endpoint')
httpd = socketserver.TCPServer(('0.0.0.0', port), AgentHandler)
httpd.serve_forever()
