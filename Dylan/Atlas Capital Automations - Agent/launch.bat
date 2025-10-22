@echo off
REM Windows launcher for Terry Delmonaco Presents: AI – Agent Edition

cd /d %~dp0

REM Activate virtual environment if present
IF EXIST .venv\Scripts\activate (
    call .venv\Scripts\activate
)

REM Run the Python launcher, forwarding any arguments
python scripts\launch.py %*

pause