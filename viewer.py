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

async def messages_handler(queue):
    async with websockets.connect('ws://localhost:8000/viewer') as websocket:
        await websocket.send(json.dumps({"cmd": "join"}))

        while True:
            r = await websocket.recv()
            logging.debug(r)
            queue.put_nowait(r)

class GameOver(BaseException):
    pass

class PacMan(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.images = kw["images"]
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
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
        logging.debug(state)
        if 'pacman' in state:
            x, y = state['pacman']
            self.x, self.y = x*CHAR_LENGTH, y*CHAR_LENGTH
            self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
            self.image.blit(*self.sprite_pos("left"))
        #get new position and fill self.rect.x + y
        pass

class Energy(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.images = kw["images"]
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.image.blit(images, (2,2) (self.x, self.y, self.x+CROP, self.y+CROP))
        super().__init__()

class Wall(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.image.fill((100, 100, 100), self.rect)
        super().__init__()
    TODO add update()

def clear_callback(surf, rect):
    color = 0, 0, 0
    surf.fill(color, rect)

def scale(pos):
    x, y = pos
    return x * 26, y * 26

async def main_loop(q):
    main_group = pygame.sprite.OrderedUpdates()
    background_group = pygame.sprite.Group()
    images = pygame.image.load("data/sprites/spritemap.png")
   
    logging.info("Waiting for map information from server") 
    state = await q.get() #first state message includes map information
    
    map_json = json.loads(state)
    mapa = Map(map_json["map"])
    main_group.add(Wall(pos=scale((15,15))))
    main_group.add(PacMan(pos=scale(mapa.pacman_spawn), images=images))
    SCREEN = pygame.display.set_mode(scale(mapa.size))
    while True:
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop() 
    
        main_group.clear(SCREEN, clear_callback)
        main_group.update(json.loads(state))
        main_group.draw(SCREEN)
        pygame.display.flip()
        
        try:
            state = await q.get_nowait() 
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
