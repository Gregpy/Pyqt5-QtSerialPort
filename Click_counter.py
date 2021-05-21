from PyQt5 import QtCore, QtSerialPort, QtWidgets # pyqt imports
import matplotlib.pyplot as plt
import numpy as np

value = 200 # value set by user
maxCount = 100 # maxcount set by user

data = [] # list to store data
numCount = [] # this is made as a list instead of an int counter, since it's incremented in a function, so it would have to be declared global
timeCount = [] # list of time counts

#app = QtCore.QCoreApplication([]) # can use with inline plotting
app = QtWidgets.QApplication([]) # use with automatic plotting
#[print('port:', i.portName()) for i in QtSerialPort.QSerialPortInfo().availablePorts()] # can show available COM ports
serial_port = QtSerialPort.QSerialPort('COM4') # COM? choose COM port number

#serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600) # not needed since defaults is 9600

serial_port.open(QtCore.QIODevice.ReadWrite) # open port and set it to read/write
# port specifications
print('serial port:', serial_port)
print('description:',QtSerialPort.QSerialPortInfo(serial_port).description())
print('baud rate:', serial_port.baudRate())
print('data bits:', serial_port.dataBits())
print('parity:', serial_port.parity())
print('stop bits:', serial_port.StopBits())
print('DTR signal:', serial_port.DataTerminalReadySignal) 
print('flow control:', serial_port.flowControl())
print('is DTR', serial_port.isDataTerminalReady())

timer = QtCore.QElapsedTimer() # create instance of qt's elapsed timer
timer.start() # start elapsed timer

def handle_ready_read(): # slot to handle when something is ready to be read

    while serial_port.canReadLine(): # while a realine can be read from serialport
        serialStringIn = serial_port.readLine().data().decode().strip() # read a line from the serial port, get the data from it, decode the bytes to a string, then strip spaces around string
        if serialStringIn == 'C': # if the string read is C
            numCount.append(1) # append a 1 to numcount list
            to = timer.nsecsElapsed() # get the nanoseconds time elapsed since started
            print('click number:', len(numCount)) # print the click number, from the length of the numcount list
            print('time-stamp (ns):', to) # print the time stamp of the click
            timeCount.append(to) # append the time stamp to the timecount list
            if len(numCount) == maxCount: # if number of counts is equal to maxcount
                # DTR reset is needed to restart the arduino sketch the next time it's run
                # since the numCount in arduino is initialized at the start
                # see https://arduino.stackexchange.com/questions/439/why-does-starting-the-serial-monitor-restart-the-sketch
                serial_port.setDataTerminalReady(0) # set dtr to 0
                serial_port.setDataTerminalReady(1) # set dtr to 1
                serial_port.setDataTerminalReady(0) # and 0 again
                serial_port.close() # close serial port
                app.quit() # quit pyqt event loop

#serial_port.clear() # maybe needed, if spaces are around 'C', if printed

serial_port.readyRead.connect(handle_ready_read) # when something is ready to read, signal is sent to run handle ready read slot

serial_port.writeData(bytes([value])) # encode value to bytes then write byte data to serial port
#app.setQuitOnLastWindowClosed(True) # could be needed 
app.exec_() # start qt eventloop

maxT = max(timeCount) # get max of timecount0
numZeros = 1000 # num zeros to use
timeZeros = np.linspace(0, maxT, numZeros) # 1D array from 0 to maxt of length numzeros
zeroValues = np.zeros(numZeros) # np array of zeros of numzeros shape
oneValues = np.ones(maxCount) # np array of ones of maxcount shape
plt.figure() # create plot figure, may be not needed
plt.plot(timeCount, oneValues, 'o') # plot one values vs timecounts
plt.plot(timeZeros, zeroValues, 'o') # plot zero values vs timezeros
plt.xlabel("Time (ns)") # x label
plt.ylabel("Spike") # y label
plt.show() # show plot, may be not needed
