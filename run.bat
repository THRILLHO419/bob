@echo off
REM Pulls the latest version of this tool, then runs it. Just run this instead
REM of calling video_shuffler.py directly -- you'll always be on the newest code.
cd /d "%~dp0"

git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel%==0 (
    git pull --ff-only >nul 2>&1
    if not %errorlevel%==0 echo warning: could not auto-update ^(offline?^), using local copy
)

python video_shuffler.py %*
