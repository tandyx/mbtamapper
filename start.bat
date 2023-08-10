set /A DEV=0
title MBTA Mapper
@REM set HOST=0.0.0.0
set SUBWAY = 0,1
set RAPID_TRANSIT = 0,1,4
set COMMUTER_RAIL = 2
set BUS = 3
set FERRY = 4
set ALL_ROUTES = 0,1,2,3,4
set LIST_KEYS = SUBWAY,RAPID_TRANSIT,COMMUTER_RAIL,BUS,FERRY,ALL_ROUTES



@echo off
python -m venv ./.venv --upgrade-deps
@REM .venv\Scripts\Activate.bat
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt

set PYTHONPATH=/helper_functions;/gtfs_schedule;/gtfs_realtime;/gtfs_loader;

start /B ./.venv/Scripts/python.exe startup.py

IF %DEV% NEQ 0 (
    start /B .venv/Scripts/python.exe app.py
) ELSE (
    start /B .venv/Scripts/python.exe -m waitress --listen=*:80 --call startup:create_default_app
)