@echo off

setlocal
set PYTHONDIR="c:\Program Files (x86)\Python 3.5\python.exe"
set PIBDIR=%~dp0

%PYTHONDIR% -u %PIBDIR%\pib.py %*