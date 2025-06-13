@echo off
setlocal
set PYTHONPATH=%~dp0
robot %~dp0\HLK.robot
endlocal
