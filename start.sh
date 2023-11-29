#!/bin/bash

cd static &&
    mkdir -p node_modules &&
    npm install &&
    cd ..

python3 main.py &
python3 -m waitress --listen=*:80 --threads=50 --call main:create_default_app &
wait
exit $?
