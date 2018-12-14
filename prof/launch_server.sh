MAP=map1
GHOSTS=4
LEVEL=3
PORT=8001

docker run -d -it --name ${MAP}_${GHOSTS}g_${LEVEL}l -p $PORT:8000 -e MAP=data/$MAP.bmp -e GHOSTS=$GHOSTS -e LEVEL=$LEVEL pacman_server:latest
