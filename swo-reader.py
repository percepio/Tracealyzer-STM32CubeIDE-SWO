import os
import socket
import threading
from time import sleep
import signal
import sys

global running
running = True
   
# TCP client, connects to GDB server and reads SWO data.
def gdb_swo_reader():    
    global running
    SWO_PORT = 61998  
        
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SWO_PORT))
    except:
        print("[swo-reader] Error connecting, is GDB server started?")
        running = False
        return
            
    swo_connected = True
    
    file_path = "swo-data.bin"
    outfile = open(file_path, "wb")

    # This makes the GDB server output the SWO data.        
    byte_array = bytearray( [1, 0, 0, 0, 0, 0, 0, 0] )
    
    try:
        s.send(byte_array)
    except:
        print("[swo-reader] Error sending to GDB server.")
        running = False            
        return
        
    bytecount = 0
    
    while (swo_connected):
        
        try:                              
            data = s.recv(1000000)
                            
            if (data == b''):
                swo_connected = False
            else:
                bytecount = bytecount + len(data)
                outfile.write(data);
            
        except KeyboardInterrupt:
            swo_connected = False

        except Exception as err:                
            swo_connected = False
            
    s.close()
    outfile.close()    
    running = False


thread_gdb_swo_reader = threading.Thread(target=gdb_swo_reader)
thread_gdb_swo_reader.start();

running = True

while running:   
    try:
        sleep(2)
                
    except KeyboardInterrupt:
        running = False 

