@echo off

setlocal
set PYTHONDIR=c:\python32\python
set PIBDIR=%~dp0

%PYTHONDIR% -u %PIBDIR%\pib.py %*