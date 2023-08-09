#!/bin/bash

# export SUBWAY="0 1"
# export RAPID_TRANSIT="0 1 4"
# export COMMUTER_RAIL=2
# export BUS=3
# export FERRY=4
# export ALL_ROUTES="0 1 2 3 4"
# export LIST_KEYS="SUBWAY RAPID_TRANSIT COMMUTER_RAIL BUS FERRY ALL_ROUTES"

# python2 -m pip install virtualenv
# virtualenv ./.venv/Scripts/activate --upgrade-deps
python3 -m venv ./.venv --upgrade-deps
source ./.venv/Scripts/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade -r requirements.txt

export PYTHONPATH=/helper_functions:/gtfs_schedule:/gtfs_realtime:/gtfs_loader:

python3 test.py &

python3 -m waitress --listen=*:500 app:SW_APP &
python3 -m waitress --listen=*:501 app:RT_APP &
python3 -m waitress --listen=*:502 app:CR_APP &
python3 -m waitress --listen=*:503 app:BUS_APP &
python3 -m waitress --listen=*:504 app:FRR_APP &
python3 -m waitress --listen=*:505 app:ALL_APP &

wait 