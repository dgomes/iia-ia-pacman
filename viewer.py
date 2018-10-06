import asyncio
import pygame
import random
from functools import partial
import json
import asyncio
import websockets
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

SIZE = 800, 600
CHAR_LENGTH = 26
CHAR_SIZE= CHAR_LENGTH, CHAR_LENGTH #22 + 2px border

async def messages_handler(queue):
    async with websockets.connect('ws://localhost:8000/viewer') as websocket:
        await websocket.send(json.dumps({"cmd": "view"}))

        while True:
            r = await websocket.recv()
            logging.debug(r)
            queue.put_nowait(r)

class GameOver(BaseException):
    pass

class Object(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.color = kw.pop("color", (255,0,0))
        self.speed = kw.pop("speed", 10)

        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE) 
        self.move_function = kw.pop("move_function", lambda *args: None)
        super().__init__()

    def update(self):
        self.image.fill(self.color)
        self.move_function(self)

class PacMan(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.speed = kw.pop("speed", 1)

        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.images = pygame.image.load("data/sprites/spritemap.png")
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
        print(state)
        if 'pacman' in state:
            print(state['pacman'])
            x, y = state['pacman']
            self.x, self.y = x*CHAR_LENGTH, y*CHAR_LENGTH
            self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
            self.image.blit(*self.sprite_pos("left"))
        #get new position and fill self.rect.x + y
        pass

def clear_callback(surf, rect):
    color = 0, 0, 0
    surf.fill(color, rect)

async def main_loop(q):
    main_group = pygame.sprite.OrderedUpdates()
    main_group.add(PacMan(pos=(0, 0)))
    
    SCREEN = pygame.display.set_mode(SIZE)
    
    while True:
        state = await q.get() #this blocks the gui... :(
        pygame.event.pump()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            asyncio.get_event_loop().stop() 

        main_group.clear(SCREEN, clear_callback)
        main_group.update(json.loads(state))
        main_group.draw(SCREEN)
        pygame.display.flip()

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
