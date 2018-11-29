import requests
import sys
import json
import asyncio
import websockets
import os

WEBHOOK = os.environ.get('WEBHOOK', 'localhost')
SERVER = "pacman-aulas.ws.atnog.av.it.pt"


async def agent_loop(server_address = SERVER, agent_name="slack_bot"):
    async with websockets.connect("ws://{}/viewer".format(server_address)) as websocket:

        # Receive information about static game properties 
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg) 
        
        scores = ":video_game: Current Highscores @ {}\n\n:trophy:".format(SERVER)
        for [group, score] in game_properties['highscores']:
            scores += "*{}* ({})\n".format(group, score)


        payload = {"channel": "#ai", 
                   "username": "AI_server_bot",
                   "icon_emoji": ":ghost:",
                   "text": scores}

        print(payload) 
        response = requests.post(WEBHOOK, json=payload)
        if response.status_code != 200:
            raise ValueError('Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text)
        )

loop = asyncio.get_event_loop()
loop.run_until_complete(agent_loop())
