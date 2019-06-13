@echo off

setlocal

if exist reload.bat goto ok
echo reload.bat must be run from its folder
goto end

:ok

:: stop
taskkill /im demo1.exe /f
del /q /f /a pid

:: start
start /b bin\demo1 >> log\panic.log 2>&1 &

echo reload successfully

:end