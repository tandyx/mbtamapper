#!/bin/bash

python3 main.py &
python3 -m waitress --listen=*:80 --call main:create_default_app &
wait -n
exit $?