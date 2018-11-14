import asyncio
import pygame
import random
from functools import partial
from mapa import Map
import json
import asyncio
import websockets
import logging
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

PACMAN = {'up': (24, 72), 'left': (0, 72), 'down': (120, 72), 'right': (96, 72)}

RED_GHOST = {'up': (168, 144), 'left': (96, 144), 'down': (48, 144), 'right': (0, 144)}
PINK_GHOST = {'up': (168, 192), 'left': (96, 192), 'down': (48, 192), 'right': (0, 192)}
ORANGE_GHOST = {'up': (168, 216), 'left': (96, 216), 'down': (48, 216), 'right': (0, 216)}
BLUE_GHOST = {'up': (8*24+168, 192), 'left': (8*24+96, 192), 'down': (8*24+48, 192), 'right': (8*24+0, 192)}
GHOSTS = [RED_GHOST, PINK_GHOST, ORANGE_GHOST, BLUE_GHOST]

CHAR_LENGTH = 26
CHAR_SIZE= CHAR_LENGTH, CHAR_LENGTH #22 + 2px border
ENERGY_RADIUS = 4
BOOST_RADIUS = 8
SCALE = None 

async def messages_handler(ws_path, queue):
    async with websockets.connect(ws_path) as websocket:
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
        self.direction = "left"
        self.image.blit(*self.sprite_pos())
        self.image = pygame.transform.scale(self.image, scale((1,1)))
        super().__init__()
   
    def sprite_pos(self, new_pos=(0,0)):
        CROP = 22 
        x, y = new_pos 
        
        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        x, y = PACMAN[self.direction]
        return (self.images, (2,2), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'pacman' in state:
            x, y = state['pacman']
            sx, sy = scale((x, y))
            self.rect = pygame.Rect((sx, sy) + CHAR_SIZE)
            self.image = pygame.Surface(CHAR_SIZE)
            self.image.fill((0,0,0))
            self.image.blit(*self.sprite_pos((sx, sy)))
            self.image = pygame.transform.scale(self.image, scale((1, 1)))

            self.x, self.y = sx, sy

class Ghost(pygame.sprite.Sprite):
    def __init__(self, *args, **kw):
        self.x, self.y = (kw.pop("pos", ((kw.pop("x", 0), kw.pop("y", 0)))))
        self.index = kw.pop("index", 0)
        self.images = kw["images"]
        self.direction = "left"
        self.rect = pygame.Rect((self.x, self.y) + CHAR_SIZE)
        self.image = pygame.Surface(CHAR_SIZE)
        self.image.blit(*self.sprite_pos((self.x, self.y)))
        self.image = pygame.transform.scale(self.image, scale((1,1)))
        super().__init__()
   
    def sprite_pos(self, new_pos, boost=False):
        CROP = 22 
        x, y = new_pos 

        if x > self.x:
            self.direction = "right"
        if x < self.x:
            self.direction = "left"
        if y > self.y:
            self.direction = "down"
        if y < self.y:
            self.direction = "up"

        x, y = GHOSTS[self.index][self.direction] 

        if boost:
            x, y = 168, 96
        return (self.images, (2,2), (x, y, x+CROP, y+CROP))

    def update(self, state):
        if 'ghosts' in state:
            x, y = state['ghosts'][self.index]
            sx, sy = scale((x, y))
            self.rect = pygame.Rect((sx, sy) + CHAR_SIZE)
            self.image = pygame.Surface(CHAR_SIZE)
            self.image.fill((0,0,0))
            self.image.blit(*self.sprite_pos((sx, sy), state['super']))
            self.image = pygame.transform.scale(self.image, scale((1,1)))

            self.x, self.y = sx, sy


def clear_callback(surf, rect):
    color = 0, 0, 0
    surf.fill(color, rect)

def scale(pos):
    x, y = pos
    return int(x * CHAR_LENGTH / SCALE), int(y * CHAR_LENGTH / SCALE)

def draw_background(mapa, SCREEN):
    for x in range(int(mapa.size[0])):
        for y in range(int(mapa.size[1])):
            if mapa.is_wall((x,y)):
                draw_wall(SCREEN, x, y)
        
def draw_wall(SCREEN, x, y):
    wx, wy = scale((x, y))
    wall_color = (100,100,100)
    pygame.draw.rect(SCREEN, wall_color,
                       (wx,wy,*scale((1,1))), 0)

def draw_energy(SCREEN, x, y, boost=False):
    ex, ey = scale((x, y))
    pygame.draw.circle(SCREEN, (200, 0, 0),
                       (ex+int(CHAR_LENGTH/SCALE/2),ey+int(CHAR_LENGTH/SCALE/2)),
                       int(BOOST_RADIUS/SCALE) if boost else int(ENERGY_RADIUS/SCALE), 0)

def draw_info(SCREEN, text, pos):
    myfont = pygame.font.Font(None, 30) 
    textsurface = myfont.render(text, True, (0, 0, 0))

    erase = pygame.Surface(textsurface.get_size())
    erase.fill((200,200,200))

    if pos[0] > SCREEN.get_size()[0]:
        pos = SCREEN.get_size()[0] - textsurface.get_size()[0], pos[1]
    if pos[1] > SCREEN.get_size()[1]:
        pos = pos[0], SCREEN.get_size()[1] - textsurface.get_size()[1]

    SCREEN.blit(erase,pos)
    SCREEN.blit(textsurface,pos)

async def main_loop(q):
    main_group = pygame.sprite.OrderedUpdates()
    images = pygame.image.load("data/sprites/spritemap.png")
   
    logging.info("Waiting for map information from server") 
    state = await q.get() #first state message includes map information

    newgame_json = json.loads(state)
    mapa = Map(newgame_json["map"])
    GAME_SPEED = newgame_json["fps"]
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
   
        if "score" in state:
            text = str(state["score"])
            draw_info(SCREEN, text.zfill(6), (0,0))
            text = str(state["player"])
            draw_info(SCREEN, text, (4000,0))
        if "energy" in state:
            for x, y in state["energy"]:
                draw_energy(SCREEN, x, y)
        if "boost" in state:
            for x, y in state["boost"]:
                draw_energy(SCREEN, x, y, True)
        main_group.draw(SCREEN)
       
        main_group.update(state)
       
        pygame.display.flip()
        
        try:
            state = json.loads(q.get_nowait())
            
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(1./GAME_SPEED)
            continue 
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP address of the server", default="localhost")
    parser.add_argument("--scale", help="reduce size of window by x times", type=int, default=1)
    parser.add_argument("--port", help="TCP port", type=int, default=8000)
    args = parser.parse_args()
    SCALE = args.scale

    LOOP = asyncio.get_event_loop()
    pygame.font.init()
    q = asyncio.Queue()
    
    ws_path = 'ws://{}:{}/viewer'.format(args.server, args.port)

    try:
        LOOP.run_until_complete(asyncio.gather(messages_handler(ws_path, q), main_loop(q)))
    finally:
        LOOP.stop()
        pygame.quit()
