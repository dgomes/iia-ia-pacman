import random
import sys
import json
import asyncio
import websockets


async def hello():
    async with websockets.connect('ws://localhost:8000/player') as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))
        map_info = await websocket.recv()
        key = 'a'
        cur_x, cur_y = None, None
        while True:
            r = await websocket.recv()
            state = json.loads(r)
            x, y = state['pacman']
            if x == cur_x and y == cur_y:
                if key in "ad":
                    key = random.choice("ws")
                elif key in "ws":
                    key = random.choice("ad")
            cur_x, cur_y = x, y
            await websocket.send(json.dumps({"cmd": "key", "key": key}))


loop = asyncio.get_event_loop()
loop.run_until_complete(hello())
