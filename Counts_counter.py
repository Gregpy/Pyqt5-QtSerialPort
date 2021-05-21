from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui # pyqt imports
import sys
import numpy as np
import datetime
import matplotlib.pyplot as plt


class MainWindow(QtWidgets.QMainWindow): # main gui window class
    def __init__(self, verbose = 0, *args, **kwargs): # initialized when window class called, default verbose is 0
        super().__init__(*args, **kwargs) # initializes any arguments or keyword arguments passed to qmainwindow also
        self.verbose = verbose # create class attribute of verbose
        self.setWindowIcon(QtGui.QIcon('mcgill_shield.png')) # set the icon the window uses, can be any png image in same folder location
        self.setWindowTitle("Geiger Counting")  # sets the title of the main window
        if verbose: print('Arduino main window class creator: Verbose mode activated') # prints if verbose > 0
        self.widget = QtWidgets.QWidget() # central widget in main window to fill with gui
        self.start_button = QtWidgets.QPushButton('Start', clicked = self.connect) # creates the start push button and connects clicking signal to the connect slot function
        self.quit_button = QtWidgets.QPushButton('Quit', clicked = self.close) # creates quit button, closes main window when clicked
        self.period_label = QtWidgets.QLabel('Period (ms)') # creates period label
        self.period = QtWidgets.QLineEdit('0.2') # creates a line edit widget for period, where values can be types, 0.2 is initial setting
        self.replicas_label = QtWidgets.QLabel('Replicas') # creates replicas label
        self.replicas = QtWidgets.QLineEdit('1') # line edit for replicas, initialized at 1
        self.intervals_label = QtWidgets.QLabel('Intervals') # intervals label
        self.intervals = QtWidgets.QLineEdit('100') # set intervals line edit at 100
        self.output = QtWidgets.QTextEdit() # textbox where output will show up
        self.prints = QtWidgets.QCheckBox() # a checkbox, to check whether to print out textbox output
        self.prints_label = QtWidgets.QLabel('Print textbox output') # print out label
        self.save_data = QtWidgets.QCheckBox() # save data check box
        self.save_data.setChecked(True) # set initial save data check box as checked
        self.save_data_label = QtWidgets.QLabel('Save data') # save data label
        hlayout_save_data = QtWidgets.QHBoxLayout() # horizontal layout to put save data widgets
        hlayout_save_data.addWidget(self.save_data_label) # adding save data label to previous
        hlayout_save_data.addWidget(self.save_data) # and save data check box
        hlayout_prints = QtWidgets.QHBoxLayout() # horizontal layout for printing out output option
        hlayout_prints.addWidget(self.prints_label) # print label added 
        hlayout_prints.addWidget(self.prints) # and prints checkbox added
        hlayout_period = QtWidgets.QHBoxLayout() # similar to previous explanations, adding horizontal layouts
        hlayout_period.addWidget(self.period_label)
        hlayout_period.addWidget(self.period)
        hlayout_replicas = QtWidgets.QHBoxLayout()
        hlayout_replicas.addWidget(self.replicas_label)
        hlayout_replicas.addWidget(self.replicas)
        hlayout_intervals = QtWidgets.QHBoxLayout()
        hlayout_intervals.addWidget(self.intervals_label)
        hlayout_intervals.addWidget(self.intervals)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.start_button)
        hlayout.addWidget(self.quit_button)
        vlayout = QtWidgets.QVBoxLayout() # vertical layout to put previous horizontal layouts in
        vlayout.addLayout(hlayout) # horizontal layout added, and so on
        vlayout.addLayout(hlayout_replicas)
        vlayout.addLayout(hlayout_intervals)
        vlayout.addLayout(hlayout_period)
        vlayout.addLayout(hlayout_prints)
        vlayout.addLayout(hlayout_save_data)
        vlayout.addWidget(self.output) # output textbox widget is added, it's not a layout
        self.widget.setLayout(vlayout) # layout of main widget is set to vertial layout made
        self.setCentralWidget(self.widget) # main widget is set as central widget

        
        
    def connect(self): # slot function fun when start button is pressed
        self.replicas_value = int(self.replicas.text()) # get the values in replicas line edit as int
        self.period_value = float(self.period.text()) # get the value in period line edit as float
        self.intervals_value = int(self.intervals.text()) # get value in intervals line edit as int
        self.output.append('Connecting to Arduino, press start again if Arduino is communicating is not shown') # shown in output textbox
        self.counter_comm = 0 # initialize counter_comm
        self.counter = 0 # initialize counter
        self.counts = [] # create counts list
        
        if QtSerialPort.QSerialPortInfo().availablePorts(): # May find arduino, or setting port manually may be required, if ports are there
            for port in QtSerialPort.QSerialPortInfo().availablePorts(): # loops through available ports
                self.serial_port = QtSerialPort.QSerialPort(port.portName()) # creates instance of serial port with port name from loop
                if self.verbose: print(f'Found device at {port.portName()}') # prints device found
                self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600) # set baud rate, though 9600 is default
                self.serial_port.errorOccurred.connect(self.handle_error) # signal for errors, sent to handle_error slot, could be used in pyqt5 file with no gui or others
                self.serial_port.open(QtCore.QIODevice.ReadWrite) # open serial port to read/write
                self.serial_port.setDataTerminalReady(1) # setting dtr to 1, 0 then 1, used with pyserial, not sure if needed here
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.readyRead.connect(self.handle_ready_read) # readyread signal sent to handle_ready_read slot function
                buf = self.serial_port.clear() # clear the buffer
                if self.verbose: print(f'Values in buffer cleared: {buf} ') # print buffer cleared if verbose

        else: # if nothing in ports
            self.output.append('No Arduino found, check connection and press start again') # print if no arduino found
   
    def handle_ready_read(self): # slot function to run when something is there to be read

        while self.serial_port.canReadLine(): # while a readline is there to be read

            try: # try unless an exception occurs

                if self.verbose: print('Waiting for response...') # print if verbose
                #resp = bytes(self.serial_port.readAll()).decode('ISO-8859-1').replace('\n','').replace('\r','') # Another way to read
                resp = self.serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # readline from serial port, get data, decode bytes with latin-1, get rid of \n and \r and strip any spaces
                if resp[:6] == 'DEBUG:': # if the response is debug
                    print("Got DEBUG response: " + resp) # most of the rest of this try statement is explained in geigerCounting_pyqt5_nogui.py
                else:
                    if self.counter == self.counter_comm + 4:
                        self.output.append('Starting data collection')
                    self.output.append('Got response: ' + resp)
                    if self.verbose: print('Got response: ' + resp)
                    if resp == 'HELLO':
                        self.output.append('Arduino is communicating, setting period')
                        self.serial_port.write((str(self.period_value*1000) + '\n\n').encode())
                        self.counter_comm = self.counter

                    if self.counter >= self.counter_comm + 4:
                        self.counts.append(float(resp))
                    if len(self.counts) == (self.intervals_value * self.replicas_value):
                        if self.prints.checkState() == 2: # if print out is selected
                            print(self.output.toPlainText()) # print out what is in the textbox
                        self.close()
                        break
                    self.counter += 1

            except ValueError as e:
                print("error", e)

    def handle_error(self, error): # serial port errors are handled here
        if error == QtSerialPort.QSerialPort.NoError: # if no error occurs
            return # return nothing
        print(error, self.serial_port.errorString()) # print error string if error
     
    def closeEvent(self, event): # slot function run when window is closed 
        super(MainWindow, self).closeEvent(event) # calls mainwindow method closeevent with event
        try: # try unless exception
            # closing runs plotting like explained in the nogui file
            heights = np.zeros((self.replicas_value, self.intervals_value), dtype = int) 
            for i in range(self.replicas_value):
                for k in range(self.intervals_value):
                    heights[i,k] = self.counts[i+k]
            print('Mean Count: ', np.mean(heights))
            if self.save_data.checkState() == 2:
                saveFileName=datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") +"_period"+str(self.period_value)+"_int"+str(self.intervals_value)+"_rep"+str(self.replicas_value)+ "_COUNTING_DATA.csv"
                np.savetxt(saveFileName,heights, delimiter=",") 
                print(f"Data saved to disk as: '{saveFileName}'")
            for i in range(self.replicas_value): # Histogram graphing section, to visually check if the data is decent. 
                plt.hist(heights[i,:],)
                plt.title(f"Replica #{i+1}")
            self.serial_port.close() # close the port
            QtWidgets.QApplication([]).quit() # end the pyqt5 eventloop, as below, if exceptions occur while closing the window
            print('Port is now closed')
        except IndexError: # If there is an error with filling in heights, if the window was closed early
            try:    
                self.serial_port.close()
                QtWidgets.QApplication([]).quit()
                print('Port is now closed, no data saved')
            except AttributeError: # If self.serial_port doesn't exist
                print('Port was not opened')
                QtWidgets.QApplication([]).quit()
        except AttributeError: # If self.serial_port doesn't exist
            print('Port was not opened')  
            QtWidgets.QApplication([]).quit()
        except: # Other errors could be found by removing the try statement if unsure
            QtWidgets.QApplication([]).quit()
            print('Closing error')


app = QtWidgets.QApplication(sys.argv) # create instance pyqt5 app, sys.argv gets arguments from the command line, which isn't need unless this if __name__ == '__main__': is used before this
w = MainWindow(verbose = 0) # create the main window instance 
w.show() # show the main window

sys.exit(app.exec_()) # start the pyqt eventloop and exit program once it ends



  