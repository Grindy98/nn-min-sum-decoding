@echo off
setlocal
cd /d %~dp0

call ..\c\generate.bat
call ..\..\hardware\generate.bat

call python argfilegen.py -o simfiles.f