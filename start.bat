SET /A DEV=0
set HOST="127.0.0.1"


@REM @echo off
python -m venv ./.venv --upgrade-deps
.venv/Scripts/Activate.ps1
.venv/Scripts/python.exe -m pip install --upgrade pip
pip install -r requirements.txt

set PYTHONPATH=/helper_functions;/gtfs_schedule;/gtfs_realtime;/gtfs_loader;

start /B .venv/Scripts/python.exe test.py

IF %DEV% NEQ 0 (
    start /B .venv/Scripts/python.exe app.py
) ELSE (
    echo "dev mode is off"

    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/subway_app run --host=%HOST% --port=500
    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/rapid_transit_app run --host=%HOST% --port=501
    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/commuter_rail_app run --host=%HOST% --port=502
    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/bus_app run --host=%HOST% --port=503
    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/ferry_app run --host=%HOST% --port=504
    start /B .venv/Scripts/python.exe -m flask --app flask_apps/executables/all_routes_app run --host=%HOST% --port=505
)