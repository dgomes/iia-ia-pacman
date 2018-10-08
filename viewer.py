import asyncio
import pygame
import random
from functools import partial
from mapa import Map
import json
import asyncio
import websockets
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

CHAR_LENGTH = 26
CHAR_SIZE= CHAR_LENGTH, CHAR_LENGTH #22 + 2px border
ENERGY_RADIUS = 4
BOOST_RADIUS = 8

async def messages_handler(queue):
    async with websockets.connect('ws://localhost:8000/viewer') as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            queue.put_nowait(r)

class GameOver(BaseException):
    pass

class PacMan(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.images = kw["images"]
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        #TODO determine direction of pacman
        self.image.blit(*self.sprite_pos("left"))
        super().__init__()
   
    def sprite_pos(self, direction):
        CROP = 22 
        x, y = None, None

        if direction == "left":
            x, y = 48, 72
        if direction == "right":
            x, y = 96, 72
        if direction == "down":
            x, y = 120, 72
        if direction == "up":
            x, y = 24, 72
        return (self.images, (2,2), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'pacman' in state:
            x, y = state['pacman']
            self.x, self.y = x*CHAR_LENGTH, y*CHAR_LENGTH
            self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
            #TODO determine direction of pacman 
            self.image.blit(*self.sprite_pos("left"))


class Ghost(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.index = kw.pop("index", 0)
        self.images = kw["images"]
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.image.blit(*self.sprite_pos("left"))
        super().__init__()
   
    def sprite_pos(self, direction):
        CROP = 22 
        x, y = None, None

        if direction == "left":
            x, y = 48, 144 
        if direction == "right":
            x, y = 96, 144 
        if direction == "down":
            x, y = 120, 144
        if direction == "up":
            x, y = 24, 144
        return (self.images, (2,2), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'ghosts' in state:
            x, y = state['ghosts'][self.index]
            self.x, self.y = x*CHAR_LENGTH, y*CHAR_LENGTH
            self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
            self.image.blit(*self.sprite_pos("left"))

def clear_callback(surf, rect):
    color = 0, 0, 0
    surf.fill(color, rect)

def scale(pos):
    x, y = pos
    return x * 26, y * 26

def draw_background(mapa, SCREEN):
    for x in range(mapa.size[0]):
        for y in range(mapa.size[1]):
            if mapa.is_wall((x,y)):
                draw_wall(SCREEN, x, y)
        
def draw_wall(SCREEN, x, y):
    wx, wy = scale((x, y))
    pygame.draw.rect(SCREEN, (100, 100, 100),
                       (wx,wy,CHAR_LENGTH, CHAR_LENGTH), 0)

def draw_energy(SCREEN, x, y, boost=False):
    ex, ey = scale((x, y))
    pygame.draw.circle(SCREEN, (200, 0, 0),
                       (ex+int(CHAR_LENGTH/2),ey+int(CHAR_LENGTH/2)),
                       BOOST_RADIUS if boost else ENERGY_RADIUS, 0)

async def main_loop(q):
    main_group = pygame.sprite.OrderedUpdates()
    images = pygame.image.load("data/sprites/spritemap.png")
   
    logging.info("Waiting for map information from server") 
    state = await q.get() #first state message includes map information
    
    newgame_json = json.loads(state)
    mapa = Map(newgame_json["map"])
    SCREEN = pygame.display.set_mode(scale(mapa.size))
   
    draw_background(mapa, SCREEN)
    main_group.add(PacMan(pos=scale(mapa.pacman_spawn), images=images))
    
    for i in range(newgame_json["ghosts"]):
        main_group.add(Ghost(pos=scale(mapa.ghost_spawn), images=images, index=i))
    
    state = dict() 
    while True:
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop() 
    
        main_group.clear(SCREEN, clear_callback)
   
        main_group.draw(SCREEN)
        if "energy" in state:
            for x, y in state["energy"]:
                draw_energy(SCREEN, x, y)
        if "boost" in state:
            for x, y in state["boost"]:
                draw_energy(SCREEN, x, y, True)
       
        main_group.update(state)
        
        pygame.display.flip()
        
        try:
            state = json.loads(q.get_nowait())
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(0.05)
            continue 
        

async def main():

    q = asyncio.Queue()

    await asyncio.gather(messages_handler(q), main_loop(q)) 

if __name__ == "__main__":
    LOOP = asyncio.get_event_loop()

    try:
        LOOP.run_until_complete(main())
    finally:
        LOOP.stop()
        pygame.quit()
