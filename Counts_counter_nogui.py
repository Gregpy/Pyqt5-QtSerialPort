from PyQt5 import QtCore, QtSerialPort, QtWidgets
import numpy as np
import datetime
import matplotlib.pyplot as plt


replicas = 1 # set the replicas
intervals = 100 # set the intervals
period = 0.3 # set the period
verbose = 0 # set verbose True or False, or 1 or 0 if want to see more info
save_data = False # set True or False or 1 or 0 to save data
counter_comm = 0 # counter initialized, has to be global so can be used in function
counter = [] # counter list avoids need to be made global
counts = [] # list to store counts


#app = QtCore.QCoreApplication([])      
app = QtWidgets.QApplication([]) # used with automatic plotting
print('Connecting to Arduino') # prints

serial_port = QtSerialPort.QSerialPort('COM4') # com port set by user, creates an instance of serial port

serial_port.open(QtCore.QIODevice.ReadWrite) # port opened and set to read/write

serial_port.setDataTerminalReady(1) # dtr set to 1,0,1, so reset arduino, used with pyserial, may not be needed here
serial_port.setDataTerminalReady(0)
serial_port.setDataTerminalReady(1)


def handle_ready_read(): # slot function to handle readyread signals, when something is there to be read
    global counter_comm # made global so can be read in function but initialized elsewhere
    while serial_port.canReadLine(): # while a readline is in the input buffer
        
        try: # try unless exception occurs
            if verbose: print('Waiting for response...') # printed if verbose > 0
            resp = serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # read a line from serial port, get the data, decode the single bytes with latin-1, get rid of \n and \r and get rid of spaces
            if resp[:6] == 'DEBUG:': # if the readline starts with DEBUG
                print("Got DEBUG response: " + resp) # print with response        
            else: # else do this if not debug
                if verbose: print('Got response: ' + resp) # if verbose, print response
                if resp == 'HELLO': # if the readline is HELLO
                    print('Arduino is communicating, setting period') # print out
                    serial_port.write((str(period*1000) + '\n\n').encode()) # convert period to seconds and string, at end of line characters and encode to bytes
                    counter_comm = len(counter) # make counter_comm equal to the length of counter, so a few readlines can go by before data is taken
                if len(counter) == counter_comm + 4: # start data collection if 4 readlines have occurred
                    print('Starting data collection') # print out          
                if len(counter) >= counter_comm + 4: # if more than 4 readlines have gove by since starting communication
                    counts.append(int(resp)) # append counts as int to counts list
                if len(counts) == (intervals * replicas): # if the number of counts are equal to the total data to take, intervals * replicas 
                    print('counts:', counts) # print the counts
                    serial_port.close() # close the serial port
                    app.quit() # quit the pyqt eventloop
                    break # break out of loop (though app.quit should leave it)
                counter.append(1) # append 1 to counter list, works as counter

        except ValueError as e: # if a value error occurs when reading a line from serial port
            print("error", e) # print the error and info about it


serial_port.readyRead.connect(handle_ready_read) # signal function for when something is ready to be read from serial port, running handle_ready_read slot function
buf = serial_port.clear() # clear the buffer
if verbose: print(f'Values in buffer cleared: {buf} ') # print if verbose, how much cleared from buffer
#app.setQuitOnLastWindowClosed(True) # could be needed 
app.exec_() # start pyqt eventloop

heights = np.zeros((replicas, intervals), dtype = int) # np array of ints of shape of replicas and intervals created
for i in range(replicas): # loop through number of replicas
    for k in range(intervals): # loop through number of intervals
        heights[i,k] = counts[i+k] # fill heights array with counts based on replica number and interval number
print('Mean Count: ', np.mean(heights)) # print mean of heights
if save_data == True: # if save_data set to true
    saveFileName = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") +"_period"+str(period)+"_int"+str(intervals)+"_rep"+str(replicas)+ "_COUNTING_DATA.csv" # saving filename based on the date and time, periods, intervals and replicas 
    np.savetxt(saveFileName,heights, delimiter = ",") # save the heights as in the csv filename
    print(f"Data saved to disk as: '{saveFileName}'") # print out data saved and filename
for i in range(replicas): # Histogram graphing section, to visually check if the data is decent. 
    plt.hist(heights[i,:],) # histogram plot for each replica
    plt.title(f"Replica #{i+1}") # title with number of replicas












