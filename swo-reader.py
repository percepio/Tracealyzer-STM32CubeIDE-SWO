import os
import socket
import threading
from time import sleep
import signal
import sys

HOST = "127.0.0.1"

global ide_connected
ide_connected = False

global swo_connected
swo_connected = False

global bytecount
bytecount = 0
    
# TCP client, connects to GDB server and reads SWO data.
def gdb_swo_reader():
    PORT = 61998
    global swo_connected
    swo_connected = False
    
    global bytecount
    bytecount = 0
    
    while True:
        print("SWO reader connecting to port " + str(PORT) + ".")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', PORT))
        except:
            print("Error connecting, is GDB server started?")
        
        print("SWO reader connected.")
        swo_connected = True
        
        file_path = "swo-data.bin"
        outfile = open(file_path, "wb")

        # This makes the GDB server output the SWO data.        
        byte_array = bytearray( [1, 0, 0, 0, 0, 0, 0, 0] )
        
        s.send(byte_array)
        bytecount = 0
        
        print("Reading SWO data, writing to " + file_path)
        while (swo_connected):
            
            try:                              
                data = s.recv(50*1024)
                                
                if (data == b''):
                    print("swo_reader_thread: Disconnected.")
                    swo_connected = False
                else:
                    bytecount = bytecount + len(data)
                    outfile.write(data);
                
            except KeyboardInterrupt:
                print("Ctrl-C (thread)")
                swo_connected = False

            except Exception as err:                
                print("SWO reader disconnected.")
                swo_connected = False
                
        s.close()
        outfile.close()
        print("SWO reader closed.")
        exit(0)


# STM32CubeIDE feature will connect here, looking for SWO data, but won't get any.
# Starts the SWO reader when IDE connected...

def ide_swo_fakesender():
    global ide_connected
    ide_connected = False
    PORT = 61235  
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            print("Waiting for IDE connection.")
            s.listen()
            conn, addr = s.accept()
           
            print("Connected, waiting 3 sec...")
            ide_connected = True
            
            # Waits for GDB server to be ready for the SWO connection.
            sleep(3)
            
            print("Connecting to GDB server for SWO data.")
            thread_gdb_swo_reader = threading.Thread(target=gdb_swo_reader)
            thread_gdb_swo_reader.start();

            while (ide_connected):
                try:
                    data = conn.recv(5)
                    if (data == b''):
                        print("IDE disconnected.")
                        ide_connected = False
                        s.close()
                except:
                        print("IDE disconnected.")
                        ide_connected = False
                        s.close()

print("Starting server thread for STM32CubeIDE")
thread_ide_swo_fakesender = threading.Thread(target=ide_swo_fakesender)
thread_ide_swo_fakesender.start()

last = 0
while True:   
    try:
        sleep(2)
        if (bytecount != last):
            print("Data rate: " + str((bytecount-last)/2000) + " KB/s")
            
        last = bytecount
        
    except KeyboardInterrupt:
        print("Ctrl-C (main)")
        swo_connected = False
