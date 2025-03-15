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
AGENT_ACCESS_KEY = os.getenv("AGENT_ACCESS_KEY", "your-access-key")

class AgentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve a simple HTML page with the chatbot embed
        if self.path == '/' or self.path == '/index.html':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SAP Security Agent Chatbot</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    .api-section {{ margin-top: 40px; }}
                </style>
            </head>
            <body>
                <h1>SAP Security Agent Chatbot</h1>
                <p>Use the chatbot in the bottom-right corner to interact with your SAP Security expert agent.</p>
                
                <div class="api-section">
                    <h2>API Usage:</h2>
                    <p>You can also send requests programmatically:</p>
                    <pre>
curl -X POST {self.server.server_address[0]}:{self.server.server_address[1]}/ask \\
  -H "Content-Type: application/json" \\
  -d '{{"message": "How do I set up SAP GRC?"}}'
                    </pre>
                </div>
                
                <!-- Digital Ocean Chatbot Embed -->
                <script async
                  src="https://agent-ac90c60eec7af7997858-wur6b.ondigitalocean.app/static/chatbot/widget.js"
                  data-agent-id="aba091df-018b-11f0-bf8f-4e013e2ddde4"
                  data-chatbot-id="7iL_BYEySLkSDxmXL0hs6-9FT35_i7eV"
                  data-name="SAP Security Agent Chatbot"
                  data-primary-color="#031B4E"
                  data-secondary-color="#E5E8ED"
                  data-button-background-color="#0061EB"
                  data-starting-message="Hello!Ask me anything about SAP Security"
                  data-logo="/static/chatbot/icons/default-agent.svg">
                </script>
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
                    self.send_header('Access-Control-Allow-Origin', '*')  # Add CORS support
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
    
    def do_OPTIONS(self):
        # Handle OPTIONS requests for CORS
        self.send_response(HTTPStatus.OK)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# Make the server accessible from outside
port = int(os.getenv('PORT', 80))
print(f'Starting server on port {port}')
print(f'Visit http://your-server-ip:{port}/ to see the SAP Security chatbot')
print(f'API endpoint available at http://your-server-ip:{port}/ask')
httpd = socketserver.TCPServer(('0.0.0.0', port), AgentHandler)
httpd.serve_forever()
