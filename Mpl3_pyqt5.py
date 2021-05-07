# This code works like pyserial code, but is not the recommended way to do it, errors are ignored from using hardcoded pauses that exit the event loop (I think because the plot uses Qt with automatic plotting, but the pyqt5 event loop also uses Qt), pyqtgraph is preferable, matplotlib is slow
from PyQt5 import QtCore, QtSerialPort, QtWidgets 
import matplotlib.pyplot as plt
import numpy as np
import sys
#import matplotlib
#matplotlib.use('Qt5Agg')

steps = 360
degsPerStep = 1     # This has to be calibrated by you 
verbose = 0         # if want to see more details

arryAll = []        # Declare arrays for storing data.
stepCounts=[]       # Step indexes
adcValues = []      # ADC readings
device = 'COM4'     # Set COM port used by arduino

attempts = []
connected = False
isclosed = False
vector = np.zeros(steps)

# Most of this was explained in laserInterface_pyqt5.py, laserInterfaceGraph_pyqt5.py or laserInterfaceGraph_python3_edit.py
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
#loop = QtCore.QEventLoop()
serial_port = QtSerialPort.QSerialPort(device) # COM? choose COM port number

serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud115200)
isopen = serial_port.open(QtCore.QIODevice.ReadWrite) 

if isopen:
    if verbose: print(f'Device found at {device}')
    pass
    
else:
    print('Device not found')
    serial_port.close()
    app.quit()
    sys.exit()


serial_port.setDataTerminalReady(1)
serial_port.setDataTerminalReady(0)
serial_port.setDataTerminalReady(1)
print('serial port:' , serial_port)
print('description:',QtSerialPort.QSerialPortInfo(serial_port).description())
print('baud rate:' , serial_port.baudRate())
print('data bits:', serial_port.dataBits())
print('parity:' , serial_port.parity())
print('stop bits:', serial_port.StopBits())
print('DTR signal:', serial_port.DataTerminalReadySignal) 
print('flow control:', serial_port.flowControl())
print('is DTR' , serial_port.isDataTerminalReady())

 
# =============================================================================
# plt.ion()
# fig = plt.figure()
# 
# global ax
# ax = fig.add_subplot(111)
# ax.set_xlabel("Step index")
# ax.set_ylabel("ADC reading")
# global lines
# lines, = ax.plot([], [])  
# =============================================================================


def send(text):
    text = text + '\n'
    serial_port.write(text.encode())
    if verbose: print(f"Sent '{text}'")

def handle_ready_read(): 
    global connected # made global so can be accessed inside and outside function
    global isclosed
    while serial_port.canReadLine():
        if verbose: print('Waiting for response...')
        resp = serial_port.readLine().data().decode().strip()
        #resp = serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # another way to read data
        if verbose: print(f"Got response: '{resp}'")
        if connected == False and resp == "LASER 2017":
            
            if verbose: print("Arduino is communicating")
            connected = True
            send("LASER 1360") # Laser control voltage
            send(f"STEPS {steps}") # Total number of steps
            send("DELAY 4") # Delay time before reading value (ms), >4 recommende
            send("START") # Start the stepping/reading
            send("STOP") # Sends a signal to change a variable on the arduino such that the motor stops after one full loop
        
        elif connected == False and len(attempts) < 5:
            
            if verbose: print("Exception")
            attempts.append(1)
        
        elif connected == False and len(attempts) == 5:
            
            print("Unable to communicate with Arduino...5 exceptions")
            send("LASER 0") 
            serial_port.setDataTerminalReady(0)
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close()
            app.quit()            

        if 9 == len(resp) and resp[4] == ':':
            #plt.pause(0.01) 
            arryAll.append(resp)               # Append raw response to array of raw serial data
            print("Got response ", resp, "\n")
                
            words = str.split(resp, ":")  # Split the response by the colon delimiter
    
            step = int(words[0])            # Note step count and append to appropriate array
            stepCounts.append(step)
            
            adc = int(words[1])            # Note A0 ADC value and append to appropriate array
            adcValues.append(adc)

            if 0 == step:
                #QtCore.QTimer.singleShot(1000, loop.exit)  
                #plt.ion() # can be commented in or out, I think setting graphics to automatic already make them interactive
                fig = plt.figure()
                #plt.xlabel("Step index") # setting label with ax
                #plt.ylabel("ADC reading")
                global ax
                ax = fig.add_subplot(111)
                ax.set_xlabel("Step index")
                ax.set_ylabel("ADC reading")
                global lines
                lines, = ax.plot(list(range(step+1)), vector[:step+1])  
                #ax.set_xlim(0, steps)
                #ax.set_ylim(0, max(vector)) # max(vector) is 0 here
                #plt.axis([0, steps, 0, max(vector)]) # set axis limits with ax
                #lines, = ax.plot(np.array(range(k+1))*degsPerStep, vector[:k+1])  
                #plt.axis([0, steps*degsPerStep, 0, max(vector)])
                #ax.set_xlim(0, steps*degsPerStep)
                #ax.set_ylim(0, max(vector)) # max(vector) is 0 here
                try:
                    plt.pause(0.001)  # short pause
                except RuntimeError: # gives occasional runtimeerrors
                    pass # pass if error
                #loop.exec_()    
            
            vector[step] = adc

            #QtCore.QTimer.singleShot(1000, loop.exit)   

            lines.set_data(list(range(step+1)), vector[:step+1])
            #plt.axis([0, steps, 0, max(vector)])
            ax.set_xlim(0, steps)
            ax.set_ylim(0, max(vector))
            #loop.exec_()
            #lines.set_data(np.array(range(k+1))*degsPerStep, vector[:k+1])
            #plt.axis([0, steps*degsPerStep, 0, max(vector)])
            #ax.set_xlim(0, steps*degsPerStep)
            #ax.set_ylim(0, max(vector))
            try:#
                plt.pause(0.001)  # try to pause, or pass if runtimeerror
            except RuntimeError:
                pass
            
        else:
            
            print(f"Unexpected response: {resp}")
            print(f"Length: {len(resp)}")   

        if len(stepCounts) == steps:
            #stepCountsCal=np.array(stepCounts) * degsPerStep
            #adcValuesnp=np.array(adcValues)    
    
            #plt.plot(stepCountsCal, adcValuesnp)    # Basic plot of ADC value per calibrated degree
                                             # Useful for a quick check of th data's quality
            
            send("LASER 0") 
            serial_port.setDataTerminalReady(0)
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close()

            if isclosed == False:     
                print('Port is closed')
                isclosed = True
            #app.quit() # If automatic backend is set, this is not needed and it would close the plot quickly, with inline it is, the latter using app = QtCore.QCoreApplication([])  

        if resp == 'Timeout!':
            
            print('Timeout occured, closing')
            send("LASER 0") 
            serial_port.setDataTerminalReady(0)
            serial_port.setDataTerminalReady(1)
            serial_port.setDataTerminalReady(0)
            serial_port.close()
            app.quit()             

serial_port.clear()  

serial_port.readyRead.connect(handle_ready_read) 
 
app.setQuitOnLastWindowClosed(True) # comment out if using inline graphics backend

sys.exit(app.exec_())

