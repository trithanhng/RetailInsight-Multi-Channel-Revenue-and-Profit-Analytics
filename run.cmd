@echo off
setlocal
cd /d "%~dp0"
set "TASK_PYTHON=%~dp0.venv\Scripts\python.exe"
set "PYTHONUTF8=1"
if not exist "%TASK_PYTHON%" (
  echo Run setup.cmd first.
  exit /b 1
)
if not defined JAVA_HOME if exist "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin\java.exe" set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
set "TASK_NAME=%~1"
if "%TASK_NAME%"=="" set "TASK_NAME=dashboard"
if /i "%TASK_NAME%"=="dashboard" goto dashboard
if /i "%TASK_NAME%"=="pipeline" goto pipeline
if /i "%TASK_NAME%"=="benchmark" goto benchmark
if /i "%TASK_NAME%"=="load-test" goto loadtest
if /i "%TASK_NAME%"=="test" goto test
if /i "%TASK_NAME%"=="report" goto report
if /i "%TASK_NAME%"=="package" goto package
if /i "%TASK_NAME%"=="all" goto all
echo Usage: run.cmd dashboard^|pipeline^|benchmark^|load-test^|test^|report^|package^|all
exit /b 2
:dashboard
"%TASK_PYTHON%" -m streamlit run dashboard.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
exit /b %errorlevel%
:pipeline
"%TASK_PYTHON%" -m retail_bi.pipeline --download
exit /b %errorlevel%
:benchmark
"%TASK_PYTHON%" -m retail_bi.benchmark --repeats 3
exit /b %errorlevel%
:loadtest
"%TASK_PYTHON%" -m retail_bi.benchmark --scale 5 --repeats 3
exit /b %errorlevel%
:test
"%TASK_PYTHON%" -m retail_bi.delivery --verify
exit /b %errorlevel%
:report
"%TASK_PYTHON%" -m retail_bi.report
exit /b %errorlevel%
:package
"%TASK_PYTHON%" -m retail_bi.delivery --package
exit /b %errorlevel%
:all
"%TASK_PYTHON%" -m retail_bi.pipeline --download
if errorlevel 1 exit /b 1
"%TASK_PYTHON%" -m retail_bi.benchmark --repeats 3
if errorlevel 1 exit /b 1
"%TASK_PYTHON%" -m retail_bi.report
if errorlevel 1 exit /b 1
"%TASK_PYTHON%" -m retail_bi.delivery --verify --package
exit /b %errorlevel%
