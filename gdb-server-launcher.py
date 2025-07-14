import settings

import os
import socket
import threading
from time import sleep
import signal
import sys
import subprocess
import time
from sys import platform

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
gdb_server_proc = None
launch_script = ""

if platform == "linux" or platform == "linux2":
    launch_script = "./run_stlink_gdb_server.sh"
elif platform == "win32":
    launch_script = "run_stlink_gdb_server.bat"
elif platform == "darwin":
    print("macOS not supported.")
    sleep(1.5)
    exit()

gdb_server_proc = subprocess.Popen(
    [launch_script,
     settings.GDB_SERVER_PORT, 
     settings.GDB_SWO_PORT, 
     settings.GDB_SERVER_PATH, 
     settings.STLINK_PROG_DIR,
     settings.APID], 
    shell=False)

# Start the dummy port. Will exit when the GDB server exits.
create_dummy_port_for_ide(gdb_server_proc)

