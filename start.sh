#!/bin/bash

DEV=0

HOST=0.0.0.0
# SUBWAY="0 1"
# RAPID_TRANSIT="0 1 4"
# COMMUTER_RAIL=2
# BUS=3
# FERRY=4
# ALL_ROUTES="0 1 2 3 4"
# LIST_KEYS="SUBWAY RAPID_TRANSIT COMMUTER_RAIL BUS FERRY ALL_ROUTES"

# python -m venv ./.venv --upgrade-deps
# source ./.venv/bin/activate
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe setup.py build_ext --force
.venv/Scripts/python.exe -m pip install --upgrade -r requirements.txt

export PYTHONPATH="/helper_functions:/gtfs_schedule:/gtfs_realtime:/gtfs_loader"

.venv/Scripts/python.exe test.py &

if [ "$DEV" -ne 0 ]; then
    python app.py &
else
    echo "dev mode is off"
    waitress-serve --host $HOST --port 500 app:SW_APP &
    waitress-serve --host $HOST --port 501 app:RT_APP &
    waitress-serve --host $HOST --port 502 app:CR_APP &
    waitress-serve --host $HOST --port 503 app:BUS_APP &
    waitress-serve --host $HOST --port 504 app:FRR_APP &
    waitress-serve --host $HOST --port 505 app:ALL_APP &
fi