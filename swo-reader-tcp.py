import settings

import os
import socket
import threading
from time import sleep
import signal
import sys
import queue
import datetime

global running

running = True

data_queue = queue.Queue()
   
def error_log(message):    
    file1 = open("trace_error.log", "a")  # append mode
    file1.write("[" + datetime.datetime.now().strftime("%d %b, %Y at %H:%M:%S") +  "] Error in " + str(os.path.basename(__file__)) + ": " + message + "\n")
    file1.close()
   
# TCP client, connects to GDB server and reads SWO data.
def gdb_swo_reader():    
    global running
    global data_queue
            
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', int(settings.GDB_SWO_PORT)))
    except:
        error_log("Could not connect to GDB_SWO_PORT.")
        running = False
        return
            
    swo_connected = True
    
    # This makes the GDB server output the SWO data.        
    byte_array = bytearray( [1, 0, 0, 0, 0, 0, 0, 0] )
    
    try:
        s.send(byte_array)
    except:        
        error_log("Error sending start message to GDB_SWO_PORT.")
        running = False            
        return

    bytecount = 0
    
    while (swo_connected):
        
        try:                              
            data = s.recv(1000000)
            data_queue.put(data) 
            sleep(0.05) # To get bigger data chunks (more efficient?)
            
        except KeyboardInterrupt:
            swo_connected = False

        except Exception as err:                
            swo_connected = False
            
    s.close()
    running = False

thread_gdb_swo_reader = threading.Thread(target=gdb_swo_reader)
thread_gdb_swo_reader.start();

running = True

# Allows for logging all ITM data (the raw data stream). Set to True to generate rawtrace.bin. For (internal) debugging purposes.
ENABLE_RAWTRACE = False 

if ENABLE_RAWTRACE:
    _rawtrace_f = open("rawtrace.bin", "wb")
else:
    _rawtrace_f = None

try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except:        
    error_log("Could not create server socket.")
    
try:
    server_socket.bind(("127.0.0.1", int(settings.TRACE_OUTPUT_PORT)))
except:        
    error_log("Could not bind to TRACE_OUTPUT_PORT (" + settings.TRACE_OUTPUT_PORT + ")")
    
server_socket.listen(5)

tz_client_socket, client_address = server_socket.accept()

while running:   
    try:        
        qdata = data_queue.get()        
        if (qdata is None):
            break
        
        try:
            tz_client_socket.send(qdata)    

            if ENABLE_RAWTRACE:
                _rawtrace_f.write(qdata)
                
        except Exception as e:
            # Typically "disconnect" exceptions, not worth logging in trace_error.log.
            print(e)
            break
            
    except KeyboardInterrupt:
        running = False 

if ENABLE_RAWTRACE:
    _rawtrace_f.close()

tz_client_socket.close()
server_socket.close()