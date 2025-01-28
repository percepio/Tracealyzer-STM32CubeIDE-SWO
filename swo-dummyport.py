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

# The purpose of this script is to trick STM32CubeIDE to start a debugging
# session with SWO trace output enabled, while the SWO data is read by
# swo-reader.py instead of the IDE. (The GDB server is configured to send
# the SWO data to another port, where swo-reader.py connects.)
# This script provides a "dummy" TCP port for the IDE to read SWO data.
# No data is provided to the IDE (possible extension) but the connection
# is successful and we avoid errors in the IDE aborting the debug session.

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