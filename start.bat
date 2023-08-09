set /A DEV=0

set HOST=0.0.0.0
@REM set SUBWAY = 0,1
@REM set RAPID_TRANSIT = 0,1,4
@REM set COMMUTER_RAIL = 2
@REM set BUS = 3
@REM set FERRY = 4
@REM set ALL_ROUTES = 0,1,2,3,4
@REM set LIST_KEYS = SUBWAY,RAPID_TRANSIT,COMMUTER_RAIL,BUS,FERRY,ALL_ROUTES



@echo off
python -m venv ./.venv --upgrade-deps
@REM .venv\Scripts\Activate.bat
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe setup.py build_ext --force
pip install --upgrade -r requirements.txt

set PYTHONPATH=/helper_functions;/gtfs_schedule;/gtfs_realtime;/gtfs_loader;

start /B ./.venv/Scripts/python.exe test.py

IF %DEV% NEQ 0 (
    start /B .venv/Scripts/python.exe app.py
) ELSE (
    echo "dev mode is off"
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=500 app:SW_APP
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=501 app:RT_APP
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=502 app:CR_APP
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=503 app:BUS_APP
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=504 app:FRR_APP
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=505 app:ALL_APP
)