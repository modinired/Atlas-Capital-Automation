@echo off
REM Windows launcher for Terry Delmonaco Presents: AI
REM
REM This batch file activates the project's virtual environment if it exists
REM and then runs the Python launcher script to start both the API and MCP.
REM You can create a shortcut to this file and assign it a custom icon for
REM a polished desktop launcher.

cd /d %~dp0

REM Activate virtual environment if present
IF EXIST .venv\Scripts\activate (
    call .venv\Scripts\activate
)

REM Execute the Python launch script, forwarding any arguments
python scripts\launch.py %*

REM Keep the window open until the user closes it
pause