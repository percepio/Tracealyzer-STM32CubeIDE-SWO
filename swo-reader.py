import os
import socket
import threading
from time import sleep
import signal
import sys

HOST = "127.0.0.1"

global SWO_PORT
SWO_PORT = 61998

global ide_connected
ide_connected = False

global swo_connected
swo_connected = False

global bytecount
bytecount = 0

global running
running = True
   
# TCP client, connects to GDB server and reads SWO data.
def gdb_swo_reader():
    global SWO_PORT

    global swo_connected
    swo_connected = False
    
    global bytecount
    bytecount = 0
    
    global running
    
    
    print("[swo-reader] Connecting to GDB server on port " + str(SWO_PORT) + ".")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', SWO_PORT))
    except:
        print("[swo-reader] Error connecting, is GDB server started?")
        running = False
        return
        
    print("[swo-reader] Connected.")
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
    
    print("[swo-reader] Ready for data. Writing trace data to: " + file_path)
    while (swo_connected):
        
        try:                              
            data = s.recv(250*1024)
                            
            if (data == b''):
                print("[swo-reader] Disconnected.")
                swo_connected = False
            else:
                bytecount = bytecount + len(data)
                outfile.write(data);
            
        except KeyboardInterrupt:
            print("[swo-reader] Ctrl-C (thread)")
            swo_connected = False

        except Exception as err:                
            print("[swo-reader] Disconnected.")
            swo_connected = False
            
    s.close()
    outfile.close()
    ide_connected = False
    running = False
    print("[swo-reader] Reader thread closed.")


# STM32CubeIDE feature will connect here, looking for SWO data, but won't get any.
# Starts the SWO reader when IDE connected...

def ide_swo_fakesender():
    global ide_connected
    global running
    ide_connected = False
    PORT = 61035
    while True:
        ide_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ide_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ide_socket.bind((HOST, PORT))        
        print("[swo-reader] Waiting for IDE connection.")
        ide_socket.listen()
        conn, addr = ide_socket.accept()
           
        print("[swo-reader] Connected, waiting 3 sec...")
        ide_connected = True
            
        # Waits for GDB server to be ready for the SWO connection.
        sleep(3)
            
        print("[swo-reader] Starting SWO reader thread.")
        thread_gdb_swo_reader = threading.Thread(target=gdb_swo_reader)
        thread_gdb_swo_reader.start();

        while (ide_connected):
            try:
                data = conn.recv(5)
                if (data == b''):
                    ide_connected = False
            except:
                    ide_connected = False
        
        running = False
        s.close()
        print("[swo-reader] IDE disconnected.")

print("[swo-reader] Starting server thread for STM32CubeIDE")
thread_ide_swo_fakesender = threading.Thread(target=ide_swo_fakesender)
thread_ide_swo_fakesender.start()

last = 0
running = True
while running:   
    try:
        sleep(2)
        if (bytecount != last and bytecount > 0):
            print("[swo-reader] Data rate: " + str((bytecount-last)/2000) + " KB/s")
            
        last = bytecount
        
        if (bytecount > 0 and ide_connected == False):
            running = False
        
    except KeyboardInterrupt:
        running = False 

