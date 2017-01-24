@echo off

REM cd into this batch file's directory
cd %~dp0

IF NOT EXIST ..\..\tale\__init__.py GOTO :use_lib_tail
REM use the tail library found in the project directory a few dirs up
SETLOCAL
SET PYTHONPATH=..\..;%PYTHONPATH%

:use_lib_tail

REM start the game
py -3 -m tale.main --game . %*
