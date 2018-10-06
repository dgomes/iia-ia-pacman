import sys
import json
import asyncio
import websockets


async def hello():
    async with websockets.connect('ws://localhost:8000/player') as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))
        key = 's'
        while True:
            r = await websocket.recv()
            state = json.loads(r)
            x, y = state['pacman']
            if x > 10:
                key = 'a'
            if x == 0:
                key = 'd'
            await websocket.send(json.dumps({"cmd": "key", "key": key}))
            print(r)


loop = asyncio.get_event_loop()
loop.run_until_complete(hello())
