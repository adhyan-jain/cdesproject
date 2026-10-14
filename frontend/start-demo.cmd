@echo off
rem Starts the STRATA demo: builds the engine and the page, then opens http://localhost:5199
cd /d "%~dp0web"
if not exist node_modules call npm install
call npm start
pause
