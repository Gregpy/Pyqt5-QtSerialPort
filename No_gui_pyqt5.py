from PyQt5 import QtCore, QtSerialPort, QtWidgets 
import matplotlib.pyplot as plt
import numpy as np
import sys

steps = 360
degsPerStep = 1     # This has to be calibrated by you 
verbose = 0         # if want to see more details

arryAll = []        # Declare arrays for storing data.
stepCounts=[]       # Step indexes
adcValues = []      # ADC readings
device = 'COM4'     # Set COM port used by arduino

attempts = []       # Counts connection attempts
connected = False   # Used to show when connected

if verbose: print("Verbose mode activated")

# word wrap can be set in spyder, wrap lines in display editor preferences
# ctrl-4 and ctrl-5 can be used to comment in out and blocks of code
# This can be used with inline, instead of commenting out app.setQuitOnLastWindowClosed(True) 
# =============================================================================
# class CoreApplication(QtCore.QCoreApplication):
#     def setQuitOnLastWindowClosed(self, quit):
#         pass
# 
# app = CoreApplication([])
# =============================================================================

# with pyqt, automatic backend graphics can cause conflicts
# since the window may use Qt
#app = QtCore.QCoreApplication([]) # use with inline plotting

app = QtWidgets.QApplication([]) # use with automatic plotting

serial_port = QtSerialPort.QSerialPort(device) # COM? choose COM port number

serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud115200) # set to rate arduino is set at
isopen = serial_port.open(QtCore.QIODevice.ReadWrite) # open arduino to read write and return if true

if isopen: # if true
    if verbose: print(f'Device found at {device}')
    pass
    
else: # if seral port not opened
    print('Device not found')
    serial_port.close() # close port (may not be needed)
    app.quit() # quit pyqt eventloop
    sys.exit() # end program


serial_port.setDataTerminalReady(1) # reset arduino with dtr's
serial_port.setDataTerminalReady(0)
serial_port.setDataTerminalReady(1)
print('serial port:' , serial_port) # print serial port specs
print('description:',QtSerialPort.QSerialPortInfo(serial_port).description())
print('baud rate:' , serial_port.baudRate())
print('data bits:', serial_port.dataBits())
print('parity:' , serial_port.parity())
print('stop bits:', serial_port.StopBits())
print('DTR signal:', serial_port.DataTerminalReadySignal) 
print('flow control:', serial_port.flowControl())
print('is DTR' , serial_port.isDataTerminalReady())

def send(text): # used to write to serial port
    text = text + '\n' # added for arduino code
    serial_port.write(text.encode()) # encode text to bytes and write to serial port
    if verbose: print(f"Sent '{text}'")

def handle_ready_read(): # function runs when something is to be read from serial port
    global connected # global so can be accessed in function
    while serial_port.canReadLine(): # when a readline is there
        if verbose: print('Waiting for response...')
        resp = serial_port.readLine().data().decode().strip() # gets data from readline, decodes bytes to string, strips spaces
        #resp = serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # another way to read data
        if verbose: print(f"Got response: '{resp}'")
        if connected == False and resp == "LASER 2017": # if not connected and the response is this
            
            if verbose: print("Arduino is communicating")
            connected = True # set connected to true
            send("LASER 1360") # Laser control voltage
            send(f"STEPS {steps}") # Total number of steps
            send("DELAY 4") # Delay time before reading value (ms), >4 recommende
            send("START") # Start the stepping/reading
            send("STOP") # Sends a signal to change a variable on the arduino such that the motor stops after one full loop
        
        elif connected == False and len(attempts) < 5: # if not connected and attempts are less than 5
            
            if verbose: print("Exception")
            attempts.append(1) # add attempt count
        
        elif connected == False and len(attempts) == 5: # if still not connected after 5 attempts 
            
            print("Unable to communicate with Arduino...5 exceptions")
            send("LASER 0") # shuts off laser
            serial_port.setDataTerminalReady(0) # reset arduino to off so can be run again
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close() # closes port
            app.quit() # quit pyqt eventloop           
            
        if 9 == len(resp) and resp[4] == ':': # if the length of the response is 9 and index 4 gives :

            arryAll.append(resp)               # Append raw response to array of raw serial data
            print("Got response ", resp, "\n")
                
            words = str.split(resp, ":")  # Split the response by the colon delimiter
    
            step = int(words[0])            # Note step count and append to appropriate array
            stepCounts.append(step)
            
            adc = int(words[1])            # Note A0 ADC value and append to appropriate array
            adcValues.append(adc)
        
        else:
            
            print(f"Unexpected response: {resp}") # print if response is not right format
            print(f"Length: {len(resp)}")   
        
        if len(stepCounts) == steps:
            stepCountsCal = np.array(stepCounts) * degsPerStep # create array of step counts * degsperstep
            adcValuesnp = np.array(adcValues)    # create array of adv values
    
            plt.plot(stepCountsCal, adcValuesnp)    # Basic plot of ADC value per calibrated degree
                                             # Useful for a quick check of th data's quality
            plt.xlabel("Step index") # set x label of plot
            plt.ylabel('ADC reading') # set y label
            print('Closing port') 
            send("LASER 0") # shuts off laser
            serial_port.setDataTerminalReady(0) # resets dtr to 0
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close() # closes port
            #app.quit() # If automatic backend is set, this is not needed and it would close the plot quickly, with inline it is, the latter using app = QtCore.QCoreApplication([])  

        if resp == 'Timeout!': # if got this response
            
            print('Timeout occured, closing')
            send("LASER 0") # shut off laser
            serial_port.setDataTerminalReady(0) # reset to 0
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close() # close port
            app.quit() # end pyqt eventloop

serial_port.clear()  # clear buffer, may not be needed

serial_port.readyRead.connect(handle_ready_read) # run handle ready read function when something is to be read in serial port
 
app.setQuitOnLastWindowClosed(True) # comment out if using inline graphics backend, ends pyqt event loop when closing plot window

sys.exit(app.exec_()) # start pyqt event loot, end program when finishing

