set /A DEV=0
set HOST="127.0.0.1"

@echo off
python -m venv ./.venv --upgrade-deps
@REM .venv\Scripts\Activate.bat
.venv\Scripts\python.exe -m pip install --upgrade pip
@REM pip install -r requirements.txt
.venv\Scripts\python.exe setup.py build_ext --force
pip install --upgrade -r requirements.txt

set PYTHONPATH=/helper_functions;/gtfs_schedule;/gtfs_realtime;/gtfs_loader;

start /B ./.venv/Scripts/python.exe test.py

IF %DEV% NEQ 0 (
    start /B .venv/Scripts/python.exe app.py
) ELSE (
    echo "dev mode is off"

    set ROUTE_KEY=COMMUTER_RAIL
    start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=502 --call app:create_app

    @REM FOR %%f in (SUBWAY, RAPID_TRANSIT, COMMUTER_RAIL, BUS, FERRY, ALL_ROUTES) DO (

    @REM     if %%f == SUBWAY (
    @REM         set /A PORT=500
    @REM     )
    @REM     If %%f == RAPID_TRANSIT (
    @REM         set /A PORT=501
    @REM     )
    @REM     If %%f == COMMUTER_RAIL (
    @REM         set /A PORT=502
    @REM     )
    @REM     If %%f == BUS (
    @REM         set /A PORT=503
    @REM     )
    @REM     If %%f == FERRY (
    @REM         set /A PORT=504
    @REM     )
    @REM     If %%f == ALL_ROUTES (
    @REM         set /A PORT=505
    @REM     )
    @REM     set ROUTE_KEY=%%f
    @REM     start /B .venv/Scripts/python.exe -m waitress --host %HOST% --port=!PORT! --call app:create_app
    @REM )
)