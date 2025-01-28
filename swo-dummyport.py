import os
import socket
import threading
from time import sleep
import signal
import sys
import subprocess
import time

HOST = "127.0.0.1"

ide_connected = False
ctrl_c_pressed = False

# The purpose of this script is to enable Tracealyzer trace streaming 
# in STM32CubeIDE, using an STLINK v3 connected to the SWO pin, while
# also allowing for regular debugging in STM32CubeIDE at the same time.
# 
# Setup:
#
#    1. Configure TraceRecorder to use the ARM_ITM streamport (see ...)
#
#    2. Configure SWO output in STM32CubeIDE (ITM port 1 enabled, no timestamps etc.)
#       -
#       -
#
#    3. Enable SWO output
#       -
#       -
#
#    4. Update your Debug Configuration in STM32CubeIDE:
#       -
#       -
#
#    5. Test-run a debug session to check that "swo-data.bin" is created in
#       your project folder and contains some data.
#
#    6. Configure Tracealyzer to read the data from swo-data.bin (PSF streaming settings).
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
#       with the tracing, but the SWV features in STM32CubeIDE will not provide any data.
#
#    3. Start a streaming trace session in Tracealyzer, using the setup described above.
#       This opens the "Live Stream" window. 
#       Check for a notice about "Missed events" in the bottom-right corner, under "Event Rate".
#       If this notice shows up, follow the advice under "Troubleshooting". Tracealyzer needs a
#       complete data stream to correctly display the trace.
#
# Troubleshooting:
# The main risk is "Missed events", i.e. data loss in the transfer. Missed events are detected
# and reported by Tracealyzer, and typically only occurs if streaming at over 500 KB/s for
# several minutes when using this approach. In case you see Missed Events, make sure to resolve
# such issues before studying the traces in Tracealyzer, otherwise the displayed data might be
# partically incorrect.
#
# One reason for Missed events can be the SWO frequency. Up to 7 MHz seems reliable, but in our
# experiments STM32CubeIDE selected 12 MHz by default (core clock divided by 10) which resulted
# in unreliable data transmission. It is recommended to select "Limit SWO frequency" and specify
# a lower value, for example 7 MHz.

# Another  reason for such missed events is most likely the small SWO data buffer in the
# STLINK GDB server. It seems this can overflow at very high and continuous data rates, probably
# due to interference from other applications or background activity in the operating system. 
#
# If you see Missed events, please try the following:
#
#    1. Make sure to limit the SWO frequency to avoid transmission errors.
#       In your STM32CubeIDE Debug Configuration, open the "Debugger" page and you find
#       the "Limit SWO clock" in the "Serial View Viewer" panel. Try 6-7 MHz to begin with.
#       If you still have issues, try a lower value, otherwise you can try a higher value to
#       see if you can increase the performance a bit.
#       Note that minor changes in SWO frequency might not have any effect, as the GDB server
#       has fixed valid baud rates and applies the nearest lower valid setting. This appears to
#       be in steps of 500 KHz or so. The actual SWO baud rate used can be seen in
#       the GDB server window. For example, if setting 7000 KHz results in "baudrate 6620000Hz".
#
#    2. Disable live visualization in Tracealyzer. This may cause higher load on the
#       host computer, that may contribute to Missed Events at higher event rates.
#       - Open Tracealyzer and select "Open Live Stream Tool" from the Trace menu.
#       - Before starting the session, enable the checkbox "Disable Live Visualization".
#       - Click "Connect" and "Start Session" to begin reading the data, either while the
#         target is running or after it has been stopped.
#       - Select "Stop Session" to show the trace data in Tracealyzer.
#
#    3. If this doesn't help, you may try closing other open applications that isn't
#       needed at the moment, perhaps also Tracealyzer itself (at least if a large
#       trace is already loaded). Open Tracealyzer again when there is no data transmission,
#       for example when halted on a breakpoint, and load the data like described above.
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

def sdsdTimestampMillisec64():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000) 
    
def create_dummy_port_for_ide(gdb_srv):
    global ide_connected        
    PORT = 61035

    ide_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ide_socket.settimeout(0.2)
    ide_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ide_socket.bind((HOST, PORT))        
    print("[swo-dummyport] Waiting for IDE connection.")
    ide_socket.listen()
    
    while (ide_connected == False and ctrl_c_pressed == False):
        try:            
            conn, addr = ide_socket.accept()            
            ide_connected = True
        except socket.timeout:
            # Timeout is only needed to allow exiting on Ctrl-C
            pass
        
    print("[swo-dummyport] IDE connected.")
    
    bytecount = 0
    last_bytecount = -1
    counter = 0
    ts = 0
    last_ts = 0
        
    while (ctrl_c_pressed == False):
        retcode = gdb_srv.poll();
        if (retcode is not None):
            print("[swo-dummyport] GDB server closed, exiting.")
            break
        else:

            sleep(2.5)
            
            last_bytecount = bytecount
            last_ts = ts
            ts = time.time()
            try:                 
                bytecount = os.path.getsize("swo-data.bin")
            except:
                pass
                
            if (bytecount > 100):
                if (bytecount != last_bytecount):  
                    sampletime = ts - last_ts
                    print("[swo-reader] Data rate: " + str(int((bytecount-last_bytecount)/(1000*sampletime))) + " KB/s" + 
                                     ", Data received: " + str(round(bytecount/1000000, 1)) + " MB")                    

def signal_handler(sig, frame):
    global ctrl_c_pressed
    ctrl_c_pressed = True

# Install the Ctrl-C handler, for clean exit.
signal.signal(signal.SIGINT, signal_handler)

# Start the GDB server as a sub process.
gdb_server_proc = subprocess.Popen(["run_stlink_gdb_server.bat"], shell=False)

# Start the dummy port. Will exit when the GDB server exits.
create_dummy_port_for_ide(gdb_server_proc)