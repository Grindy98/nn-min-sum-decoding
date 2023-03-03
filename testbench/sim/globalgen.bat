@echo off
setlocal
cd /d %~dp0

call ..\c\generate.bat
call ..\..\hardware\generate.bat

call python argfilegen.py -v simfiles_v.f -c simfiles_c.f