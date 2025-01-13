#!/bin/bash

# Update these paths to match your system!
export ST_GDB_PATH=/opt/st/stm32cubeide_1.17.0/plugins/com.st.stm32cube.ide.mcu.externaltools.stlink-gdb-server.linux64_2.2.0.202409170845/tools/bin
export ST_PROGRAMMER_PATH=/opt/st/stm32cubeide_1.17.0/plugins/com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.linux64_2.2.0.202409170845/tools/bin

# If using STM32CubeIDE, this should match your GDB server port number in your Debug Configuration.
export ST_GDB_PORT=61234

# You should not need to change this, unless the port is used by another service. 
# If you need to change this, also update this setting in swo-reader.py.
export SWO_OUTPUT_PORT=61998

rm -f swo-data.bin
touch swo-data.bin

# Should run in background (note &)
${ST_GDB_PATH}/ST-LINK_gdbserver \
--port-number ${ST_GDB_PORT} \
--swd \
--shared \
--swo-port ${SWO_OUTPUT_PORT} \
--attach \
--verbose \
-cp ${ST_PROGRAMMER_PATH} \
-m 0 &

# Should run in foreground (killed by Ctrl-C)
python3 swo-reader.py
