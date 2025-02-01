# Settings for Tracealyzer streaming via ST-LINK_gdbserver.
# See readme.md for instructions.

# Enter the two paths from "Show Command Line" in the STM32CubeIDE Debug Configuration.
GDB_SERVER_PATH = r'C:\ST\STM32CubeIDE_1.15.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.stlink-gdb-server.win32_2.1.400.202404281720\tools\bin\ST-LINK_gdbserver.exe'
STLINK_PROG_DIR = r'C:\ST\STM32CubeIDE_1.15.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.win32_2.1.400.202404281720\tools\bin'
# Note: If using Windows, make sure to use the r'path' syntax above for correct encoding of backslashes.

# The TCP port where you connect with Tracealyzer. 
# If you change this, also update the "Port" setting in Tracealyzer (under PSF Streaming Settings).
TRACE_OUTPUT_PORT = '5000'

# The main TCP port of ST-LINK_gdbserver.
# If you change this, also update your STM32CubeIDE debug configuration,
# specifically the "Port number" setting for "Connect to remote GDB server".
GDB_SERVER_PORT = '61237'

# This port is for internal communication between the GDB server and the swo-reader script.
# You can change this port number freely, without other changes needed.
GDB_SWO_PORT = '61997'

# This port is for internal communication between STM32CubeIDE and the gdb-server-launcher
# script. If you change this, also update the SWO port number in your Debug Configuration 
# under "Serial Wire Viewer" settings.
IDE_SWO_PORT = '61035'
