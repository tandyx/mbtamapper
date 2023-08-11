#!/bin/bash

python3 startup.py &
python3 -m waitress --listen=*:80 --call startup:create_default_app &
wait -n
exit $?