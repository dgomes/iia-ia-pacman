import random
import sys
import json
import asyncio
import websockets
import os
from mapa import Map

async def agent_loop(server_address = "localhost:8000", agent_name="student"):
    async with websockets.connect("ws://{}/player".format(server_address)) as websocket:

        # Receive information about static game properties 
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg) 
         
        mapa = Map(game_properties['map'])
       
        #init agent properties 
        key = 'a'
        cur_x, cur_y = None, None
        while True: 
            r = await websocket.recv()
            state = json.loads(r) #receive game state
            if not state['lives']:
                print("GAME OVER")
                return

            x, y = state['pacman']
            if x == cur_x and y == cur_y:
                if key in "ad":
                    key = random.choice("ws")
                elif key in "ws":
                    key = random.choice("ad")
            cur_x, cur_y = x, y

            #send new key
            await websocket.send(json.dumps({"cmd": "key", "key": key}))


loop = asyncio.get_event_loop()
SERVER = os.environ.get('SERVER', 'localhost')
PORT = os.environ.get('PORT', '8000')
NAME = os.environ.get('NAME', 'student')
loop.run_until_complete(agent_loop("{}:{}".format(SERVER,PORT), NAME))
