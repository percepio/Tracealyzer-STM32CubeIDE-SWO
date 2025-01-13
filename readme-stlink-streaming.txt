Tracealyzer STLINK streaming (SWO/ITM)

Usage instructions (on Linux):

1. In STM32CubeIDE, make a Debug Configuration with the following settings:

   - On the "Debugger" page:
     
     - GDB Connection Settings: 
       - Connect to Remote GDB server: Checked
       - Host name or IP address: "localhost"
       - Port number: 61234 - To use a different port, also update "export ST_GDB_PORT=61234" in run_stlink_gdb_server.sh.
     
     - GDB Server Command Line Options:
       Click on "Show Command Line" and copy the contents into a text editor.
       You will need this in the next step.
         
     - Serial Wire Viewer, Enable: Checked

     - Serial Wire Viewer, Limit SWO Clock: Checked

     - Maximum SWO clock (kHz): 7000 (7 MHz) worked well in our tests on STLINK v3.
       Higher SWO speeds may cause occational data loss leading to incorrect display in Tracealyzer.

2. Open "run_stlink_gdb_server.sh" in a new text editor window.
   Update the two path variables, ST_GDB_PATH and ST_PROGRAMMER_PATH, according to the "Show Command Line" text you copied earlier.
   ST_GDB_PATH should be the first part, that ends with ".../ST-LINK_gdbserver". 
   ST_PROGRAMMER_PATH should be the second path, starting with "-cp"

3. Open a terminal and run the script ./run_stlink_gdb_server.sh

4. Start the debug sesson in STM32CubeIDE.

5. The first time, open "SWV Trace log". Find the two buttons in the upper right corner of the Window labeled "Configure Trace" and "Start Trace".
   Select Configure trace and enable ITM channel 1. Timestamps can be disabled.
   Click "Start Trace". This enabled the SWO output, providing the TraceRecorder trace stream as ITM event.
   These settings are stored in the STM32CubeIDE project.
   
In Tracealyzer...
