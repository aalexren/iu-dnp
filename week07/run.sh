#!/bin/zsh
(trap 'kill 0' SIGINT; poetry run python server.py 0 & poetry run python server.py 1 & poetry run python server.py 2) 

