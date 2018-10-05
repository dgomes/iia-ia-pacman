import json
import asyncio
import websockets

async def hello():
    async with websockets.connect('ws://localhost:8000/connect') as websocket:
        await websocket.send(json.dumps({"cmd": "view"}))
        
        while True:
            r = await websocket.recv()
            print(r)

asyncio.get_event_loop().run_until_complete(hello())
