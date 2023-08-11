set /A DEV=0
title MBTA Mapper


docker stop mbta_mapper
docker rm mbta_mapper:latest
docker build --tag mbta_mapper .
docker run -d -p 80:80 mbta_mapper


@REM set HOST=0.0.0.0
@REM set SUBWAY = 0,1
@REM set RAPID_TRANSIT = 0,1,4
@REM set COMMUTER_RAIL = 2
@REM set BUS = 3
@REM set FERRY = 4
@REM set ALL_ROUTES = 0,1,2,3,4
@REM set LIST_KEYS = SUBWAY,RAPID_TRANSIT,COMMUTER_RAIL,BUS,FERRY,ALL_ROUTES



@REM @echo off
@REM python -m venv ./.venv --upgrade-deps
@REM @REM .venv\Scripts\Activate.bat
@REM .venv\Scripts\python.exe -m pip install --upgrade pip
@REM .venv\Scripts\python.exe -m pip install --upgrade -r requirements.txt

@REM set PYTHONPATH=/helper_functions;/gtfs_schedule;/gtfs_realtime;/gtfs_loader;

@REM start /B ./.venv/Scripts/python.exe startup.py

@REM IF %DEV% NEQ 0 (
@REM     start /B .venv/Scripts/python.exe app.py
@REM ) ELSE (
@REM     start /B .venv/Scripts/python.exe -m waitress --listen=*:80 --call startup:create_default_app
@REM )