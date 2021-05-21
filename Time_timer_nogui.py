from PyQt5 import QtCore, QtSerialPort, QtWidgets
import numpy as np
import datetime
import matplotlib.pyplot as plt


intervalNum = 100 # Number of intervals to be recorded
replicaNum = 2 # Number of replicas to record
verbose = 0 # set verbose True or False, or 1 or 0 if want to see more info
save_data = False # set True or False or 1 or 0 to save data
counter_comm = 0 # counter to start data taking
counter = [] # counter list of data taken
interval_nums = [] # interval numbers
intervals = np.ones((replicaNum,intervalNum)) # Declare intervals array, and fill it with ones, shape of replica number and interval number
replica = 0 # replicas started at 0
interval = 0 # intervals started at 0
#take_data = False # taking data set to false, not needed but was used with pyserial so was put here at first

#app = QtCore.QCoreApplication([])      
app = QtWidgets.QApplication([]) # qapp initialization 
print('Connecting to Arduino') # print out

serial_port = QtSerialPort.QSerialPort('COM4') # set the com port and create serial port instance

serial_port.open(QtCore.QIODevice.ReadWrite) # open serial port to read and write

serial_port.setDataTerminalReady(1) # set dtr to 1,0, then 1
serial_port.setDataTerminalReady(0)
serial_port.setDataTerminalReady(1)


def handle_ready_read(): # slot function handle readyread signal
    global counter_comm # made global so can be read in and out of function
    global replica
    global interval
    #global take_data
    while serial_port.canReadLine(): # while a readline is available
        try: # try if no exception
            if verbose: print('Waiting for response...') # print if verbose
            resp = serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # readline from serial port, get data, decode single bytes with latin-1, get rid of \n, \r and spaces 
            if verbose: print('Got response: ' + resp) # print resp if verbose
            if resp == "Overrun": # if resp is overrun
                serial_port.close() # close port
                raise RuntimeError("Arduino reports overrun") # this could be tested, raise error
                app.quit() # quit pyqt eventloop
                #break
            if resp == 'Geiger 2018': # if resp is this
                print('Arduino is communicating') # print out
                counter_comm = len(counter) # set counter_comm to length of counter so can wait a few passes to take data
                #take_data = True # set to true, here if needed for some reason
            if len(counter) == counter_comm + 3:# and take_data == True: # if 3 have pass, start taking data
                print('Starting data collection') # print out
            if len(counter) > counter_comm + 3:# and take_data == True: # take data after more than 3 passes
                interval_nums.append(int(resp)) # add interval as int
                print(f"Replica # {replica+1}. Interval # {interval+1}. Interval length received: {resp}\n") # print info
                intervals[replica,interval] = interval_nums[(replica+1)*(interval+1)-1] # fill intervals array with intervals
                interval += 1 # increment interval
            if len(interval_nums) == (replica+1)*intervalNum: # if length of intervalnum has been reached
                replica += 1 # increment replica
                interval = 0 # reset interval to 0
            if len(interval_nums) == (intervalNum * replicaNum): # if total data has been taken
                print('Intervals:', interval_nums) # print intervals
                serial_port.close() # closer serial port
                app.quit() # quit pyqt eventloop
                #break
            counter.append(1) # add to counter

        except ValueError as e: # if readline gives error
            print("error", e) # print error


serial_port.readyRead.connect(handle_ready_read) # signal for readyread to be handled
buf = serial_port.clear() # clear the buffer 
if verbose: print(f'Values in buffer cleared: {buf} ') # print amount from cleared buffer
#app.setQuitOnLastWindowClosed(True) # could be needed 
app.exec_() # run pyqt eventloop


for i in range(replicaNum): # Histogram graphing section, to visually check if the data is decent.
    plt.hist(intervals[i,:],) # plot histograms of intervals per replica
    plt.title(f"Replica #{i+1}") # print title of replicas

# Save the file and close the serial device
if save_data: # if save data true
    fileName = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + "_int" + str(intervalNum) + "_rep" + str(replicaNum) + "_DWELL_TIME_DATA.csv" # create save data filename
    print("Data saved as ", fileName) # print file saved
    np.savetxt(fileName, intervals, delimiter =",") # save file











