import json
from websocket import create_connection

ws = create_connection("ws://localhost:8000/connect")
print("Sending 'Hello, World'...")
ws.send(json.dumps({"cmd":"join"}))
print("Sent")
print("Receiving...")
result =  ws.recv()
print("Received '%s'" % result)
ws.close()
