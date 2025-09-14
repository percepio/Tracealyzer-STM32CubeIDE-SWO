@echo off

echo run_stlink_gdb_server.bat
set GDB_PORT=%1%
echo   GDB_PORT: %GDB_PORT%

set GDB_SWO_PORT=%2%
echo   GDB_SWO_PORT: %GDB_SWO_PORT%

set GDB_SERVER_PATH=%3%
echo   GDB_SERVER_PATH: %GDB_SERVER_PATH%

set STLINK_PROG_DIR=%4%
echo   STLINK_PROG_DIR: %STLINK_PROG_DIR%

set APID=%5%
echo   APID: %APID%

%GDB_SERVER_PATH% ^
--port-number %GDB_PORT% ^
--swd ^
--shared ^
--swo-port %GDB_SWO_PORT% ^
--attach ^
--verbose ^
-cp %STLINK_PROG_DIR% ^
-m %APID%