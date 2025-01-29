import settings

import os
import socket
import threading
from time import sleep
import signal
import sys
import subprocess
import time

# Notes on sudden performance issue, Jan 28/29
# Tuesday afternoon the Tz streaming started performing worse, with more
# Missed events, after earlier being very reliable. 
# At first I suspected the problem to be related to the USB hub, maybe combined
# with using remote desktop.
# But the problems persisted wednesday morning in the office, without using the USB hub.
# Turns out I had made an experimental change in the Debug Configuration
# and raised the priority of swo-reader.py (start /high). Restoring this to normal priority
# made it perform like before (stable at full speed at 7 MHz).
#
# - You don't need keep Tz closed while streaming. You can have the Live Stream window running,
#   with perfect(?) reliablity if running with live visualization disabled.
#
# - Also found that the streaming works reliably also WITH live visualization.
#   Decreasing the priority of the Tracealyzer process one step ("below normal") seems to help.
#
# - In this setting, using "separate receiver thread" does not seem necessary.
#   This only causes lag in the live display.
#
# - Also evaluated a variant of swo-reader.py that used a queue to speed up the reading loop.
#   But this had no impact.
#
# - For Live Visualization, "Use separate receiver thread" seems to perform worse.
#   Getting frequent errors with this. Might be that Tz polls the file more often this way,
#   causing increased conflicts when reading/writing the file at the same time.
#
# - SWO speed: 9.5 MHz seems too high. Getting occational missed events.
#   Try 8.5 (seemed reliable) and see what frequency that is selected in practice.
#   Higher frequency may cause host-side issues if the data rate is too high, but that
#   depends on the host computer and can be resolved by closing Tz. Lower SWO frequency
#   causes slower writes and higher tracing overhead, so this is important to improve
#   even if you don't need the peak throughput enabled by the higher frequency.
#
# - Note: It seems as transmission errors causes a different "pattern" in Missed events, with only 1 or a few missed events.
#   When the problem is on the host-side, you typically get hundreds of missed events in chunks.
#   Add this to the troubleshooting notes.
#
# TODO: 
#  - Rename swo-dummyport.py to "run_gdb_server_with_swo_output.py"
#  - Update the instructions   



# The purpose of this script is to enable Tracealyzer trace streaming 
# in STM32CubeIDE, using an STLINK v3 connected to the SWO pin, while
# also allowing for regular debugging in STM32CubeIDE at the same time.
# 
# Setup:
#
#    1. Configure TraceRecorder to use the ARM_ITM streamport (see ...)
#       - Explain more....
#
#    2. Configure SWO output in STM32CubeIDE (ITM port 1 enabled, no timestamps etc.)
#       - Explain more....
#       -
#
#    3. Enable SWO output
#       - Explain more....
#       -
#
#    4. Update your Debug Configuration in STM32CubeIDE:
#       - Explain more....
#       -
#
#    5. Add this script as an "External Tool" in STM32CubeIDE.
#       - Set the name to "GDB server with trace output" or similar.
#       - Locate the "External Tools" button (next to "Run") and click the dropdown menu.
#       - Select External Tools Configuration...
#       - Under "Location", select "Browse File System" and select
#         the "stm32cubeide_external_tool_start_gdb_server" script.
#       - Under "Working Directory", select your project root folder.
#       - Save and run it to test that it works. You should see a terminal window
#         with the GDB server waiting for a connection. Keep it open for the next step.
#
#    6. Launch a debug session to check that your debugging is working, and that "swo-data.bin"
#       is created in your project folder. The file size of "swo-data.bin" should increase when
#       the target is running.
#
#    7. Configure Tracealyzer to read the data from swo-data.bin (PSF streaming settings).
#       - Open File -> Settings and select "PSF Streaming Settings"
#       - Target Connection: File System
#       - File: path/to/swo-data.bin
#       - Replay mode: Unchecked
#       - Data is ITM encoded: Checked
#
# Usage:
#
#    1. Start this script, e.g. by using your "External Tool" shortcut in STM32CubeIDE.
#       This opens a separate terminal window showing the GDB server log together with
#       messages from this script.
#
#    2. Start your debug session and run your system. The trace data is saved to "swo-data.bin".
#       
#       You should see messages labeled "[swo-reader]" about the data rate and total
#       data received. You may use breakpoints and halt/go debugging without interfering
#       with the tracing, although the SWV features in STM32CubeIDE will not get any data.
#
#    3. Start a streaming trace session in Tracealyzer, using the setup described above.
#       This opens the "Live Stream" window. 
#       Check for a notice about "Missed events" in the bottom-right corner, under "Event Rate".
#       If this notice shows up, follow the advice under "Troubleshooting". Tracealyzer needs a
#       complete data stream to correctly display the trace.
#
# Troubleshooting:
#
# The main risk is "Missed events", i.e. data loss in the transfer. Missed events are detected
# and reported by Tracealyzer, and typically only occurs if streaming at over 500 KB/s for
# several minutes when using this approach. 
#
# In case you see Missed Events, make sure to resolve such issues before studying the traces in
# Tracealyzer, otherwise the displayed data might be partically incorrect.
#
# There seem to be two main reasons for missed events when using this approach:
# 
# 1. Too high SWO frequency. Up to 7 MHz seems reliable, but in our experiments STM32CubeIDE
# selected 12 MHz by default (core clock divided by 10) which resulted in occational missed
# events also at lower event rate. It is recommended to select "Limit SWO frequency" and specify
# a lower value, for example 7 MHz.
#
# 1.1. In your STM32CubeIDE Debug Configuration, open the "Debugger" page and you find the 
# "Limit SWO clock" in the "Serial View Viewer" panel. Try 6-7 MHz to begin with.
#
# 1.2. If you still have issues, try a lower value, otherwise you can try a higher value to see
# if you can increase the performance a bit.
# Note that minor changes in SWO frequency might not have any effect, as the GDB server
# has fixed valid baud rates and applies the nearest lower valid setting. This appears to
# be in steps of 500 KHz or so. The actual SWO baud rate used can be seen in the GDB server
# window. For example, if setting 7000 KHz results in "baudrate 6620000Hz".
#
# 2. Another reason for such missed events is continuously high event rate causing occational
# overflows in the (pretty small) SWO data buffer in the STLINK GDB server or STLINK driver.
# That may occur due to interference from other applications or background activity in there
# operating system. 
#
# 2.1. Disable live visualization in Tracealyzer. This may cause higher load on the
#      host computer, that may contribute to Missed Events at higher event rates.
#    - Open Tracealyzer and select "Open Live Stream Tool" from the Trace menu.
#    - Before starting the session, enable the checkbox "Disable Live Visualization".
#    - Click "Connect" and "Start Session" to begin reading the data, either while the
#      target is running or after it has been stopped.
#    - Select "Stop Session" to show the trace data in Tracealyzer.
#
# 2.2. If your trace data rate exceeds 500 KB/s on average, try reducing the data rate using
#      the settings in trcConfig.h. For example, tracing of OS Tick events is usually redundant
#      and can be disabled. Also, if you added custom events like tracing interrupt handlers or
#      "User Events" in frequently executed code, you can try commenting them out.
#
# 2.3. If this doesn't help, you may try closing other open applications that isn't
#      needed at the moment, perhaps also Tracealyzer itself (at least if a large
#      trace is already loaded). Open Tracealyzer again when there is no data transmission,
#      for example when halted on a breakpoint, and load the data like described above.
#
# How it works:
#
# The SWO data is provided by the STLINK GDB server on a TCP port, but
# STM32CubeIDE will normally connect to this port and consume all data.
#
# This solution provides a "dummy" TCP port that is used as SWO port
# in the STM32CubeIDE debug configuration. This script also starts the
# GDB server via a script. This way, we can configure the GDB server
# to output the SWO data on a different TCP port number. This script
# can be configured as an "External Tool" in STM32CubeIDE, so only
# one extra click is required. 
#
# A second python script ("swo-reader.py") connects to this port and saves
# the SWO data to a file. This is started as a "Run Command" in the debug
# configuration, which makes it start automatically when the debug session
# is ready to run.
#

ide_connected = False
ctrl_c_pressed = False

def error_log(message):    
    print("Error: " + message)
    file1 = open("trace_error.log", "a")  # append mode
    file1.write("[" + datetime.datetime.now().strftime("%d %b, %Y at %H:%M:%S") +  "] Error in " + str(os.path.basename(__file__)) + ": " + message + "\n")
    file1.close()
    
def create_dummy_port_for_ide(gdb_srv):
    global ide_connected        
    
    IDE_PORT = 0
    
    try:
        IDE_PORT = int(settings.IDE_SWO_PORT)
    except:
        error_log("Invalid value for IDE_SWO_PORT")
        sys.exit(-1)
    
    ide_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
    ide_socket.settimeout(0.2)
    ide_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        ide_socket.bind(("127.0.0.1", IDE_PORT))
    except:
        error_log("Can't bind socket to IDE_SWO_PORT, already in use? (" + settings.IDE_SWO_PORT + ")")
        sys.exit(-1)
    
    print("[gdb-server-launcher] Waiting for connection to IDE_SWO_PORT.")
    ide_socket.listen()
    
    while (ide_connected == False and ctrl_c_pressed == False):
        try:            
            conn, addr = ide_socket.accept()            
            ide_connected = True
        except socket.timeout:
            # Timeout is only needed to allow exiting on Ctrl-C
            pass
        
    print("[gdb-server-launcher] IDE connected to IDE_SWO_PORT.")
    
    bytecount = 0
    last_bytecount = -1
    counter = 0
    ts = 0
    last_ts = 0
        
    while (ctrl_c_pressed == False):
        retcode = gdb_srv.poll();
        if (retcode is not None):
            print("[gdb-server-launcher] GDB server closed, exiting.")
            break
        else:
            sleep(3)

def signal_handler(sig, frame):
    global ctrl_c_pressed
    ctrl_c_pressed = True

# Install the Ctrl-C handler, for clean exit.
signal.signal(signal.SIGINT, signal_handler)

# Start the GDB server as a sub process.
gdb_server_proc = subprocess.Popen(["run_stlink_gdb_server.bat", settings.GDB_SERVER_PORT, settings.GDB_SWO_PORT, settings.GDB_SERVER_PATH, settings.STLINK_PROG_DIR], shell=False)

# Start the dummy port. Will exit when the GDB server exits.
create_dummy_port_for_ide(gdb_server_proc)