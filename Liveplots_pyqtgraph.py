from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui
import sys
import numpy as np
import pyqtgraph as pg 
import datetime
import struct

# many comment explanations are given in pythoncontroller and module files, using pyserial and tkinter
device = 'COM4' # set device port used by arduino

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, device = 'COM3', verbose = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device = device # get device as attribute
        self.connected = False # used for when connected
        self.attempts = 0 # counts connection attempts
        self.outputArry = [] # list for init variable array
        self.trying = True # true while trying to get init values
        self.rowCount = 0 # for counting variables
        self.clearing = True # for clearing junk
        self.attemptCount = 0 # for attempting data acquisition
        self.running = True # true while collecting data
        self.labelTables = False # to check if label tables have been made
        self.started_data_collection = False # if data collection has started
        self.mainStorage = [] # where data is stored
        self.headerTable = [] # variable list
        self.unitTable = [] # unit list
        self.tempStorage = [] # temporary storage used in data collection
        self.x = [] # time index is x for plotting
        self.y_out = [] # out for y plotting and so on
        self.y_error = []
        self.y_e_temperature = []
        self.y_temperature = []        
        self.initVar = [] # list for initial variables
        self.initSetRecord = [] # list for initial settings
        self.initVarCount = 0 # counts initial variables
        self.recVarCount = 0 # counts recorded variables
        self.paused = 0 # use for pausing
        
        self.verbose = verbose # get verbose attribute
        
        self.setWindowIcon(QtGui.QIcon('mcgill_shield.png')) # sets the icon, can use any png image
        self.setWindowTitle("Arduino GUI Controller") # title of window
        if verbose: print('Arduino main window class creator: Verbose mode activated')
        self.widget = QtWidgets.QWidget() # main widget
        self.start_button = QtWidgets.QPushButton('Start', clicked = self.connect_ard) # start button connected to connect_ard
        self.pause_button = QtWidgets.QPushButton('Pause', clicked = self.pause) # pause button connected to pause
        self.quit_button = QtWidgets.QPushButton('Quit', clicked = self.close) # quit button connected to close window
        self.band_label = QtWidgets.QLabel('band (K)') # creating labels
        self.band = QtWidgets.QLineEdit('') # and empty line edits to input settings
        self.band_button = QtWidgets.QPushButton('Set', clicked = lambda: self.settings('band', self.band.text())) # set band button connected to settings function with band variable and text from band line edit
        self.band_button.setEnabled(False) # band set button disabled at start
        self.tset_label = QtWidgets.QLabel('Tset (K)') # similar setup for other settings and save
        self.tset = QtWidgets.QLineEdit('')  
        self.tset_button = QtWidgets.QPushButton('Set', clicked = lambda: self.settings('Tset', self.tset.text()))
        self.tset_button.setEnabled(False)
        self.dt_label = QtWidgets.QLabel('dt (s)')
        self.dt = QtWidgets.QLineEdit('')  
        self.dt_button = QtWidgets.QPushButton('Set', clicked = lambda: self.settings('dt', self.dt.text()))
        self.dt_button.setEnabled(False)
        self.save_label = QtWidgets.QLabel('Save Filename')
        self.save = QtWidgets.QLineEdit()
        self.save_button = QtWidgets.QPushButton('Save', clicked = self.save_file)
        self.save_button.setEnabled(False)
        self.output_label = QtWidgets.QLabel('') # output label that is filled with variables later
        self.output = QtWidgets.QTextEdit() # output text box

        hlayout_band = QtWidgets.QHBoxLayout() # these all create the widgets and layouts for buttons etc
        hlayout_band.addWidget(self.band_label)
        hlayout_band.addWidget(self.band)
        hlayout_band.addWidget(self.band_button)
        hlayout_tset = QtWidgets.QHBoxLayout()
        hlayout_tset.addWidget(self.tset_label)
        hlayout_tset.addWidget(self.tset)
        hlayout_tset.addWidget(self.tset_button)
        hlayout_dt = QtWidgets.QHBoxLayout()
        hlayout_dt.addWidget(self.dt_label)
        hlayout_dt.addWidget(self.dt)
        hlayout_dt.addWidget(self.dt_button)
        hlayout_save = QtWidgets.QHBoxLayout()
        hlayout_save.addWidget(self.save_label)
        hlayout_save.addWidget(self.save)
        hlayout_save.addWidget(self.save_button)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.start_button)
        hlayout.addWidget(self.pause_button)
        hlayout.addWidget(self.quit_button)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(hlayout_band)
        vlayout.addLayout(hlayout_tset)
        vlayout.addLayout(hlayout_dt)
        vlayout.addLayout(hlayout_save)
        vlayout.addWidget(self.output_label)
        vlayout.addWidget(self.output)
        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout2.addLayout(vlayout)
        horizontalGroupBox = QtWidgets.QGroupBox("Grid") # this is a group box for plots
        layout_plots = QtWidgets.QGridLayout() # grid layout for plots
        layout_plots.setColumnStretch(1, 2) # setting plot columns
        layout_plots.setColumnStretch(2, 2)
        plot_win = pg.GraphicsWindow()  # Automatically generates grids with multiple items
        plot_win.setBackground('w') # set white background on plots
        self.plot1 = plot_win.addPlot(row = 0, col = 0) # adding plots to graphics window
        self.plot2 = plot_win.addPlot(row = 0, col = 1)
        self.plot3 = plot_win.addPlot(row = 1, col = 0)
        self.plot4 = plot_win.addPlot(row = 1, col = 1)
        styles = {'color':'b', 'font-size':'20px'} # style for labels
        self.plot1.setLabel('left', 'out', **styles) # labels for plots
        self.plot1.setLabel('bottom', 'Time Steps', **styles) 
        self.plot2.setLabel('left', 'error', **styles)
        self.plot2.setLabel('bottom', 'Time Steps', **styles) 
        self.plot3.setLabel('left', 'e_temperature', **styles)
        self.plot3.setLabel('bottom', 'Time Steps', **styles) 
        self.plot4.setLabel('left', 'temperature', **styles)
        self.plot4.setLabel('bottom', 'Time Steps', **styles) 
        pen = pg.mkPen(color=(0, 0, 0)) # plot line setting
        self.data_line1 =  self.plot1.plot(self.x, self.y_out, pen = pen) # plots for each variable
        self.data_line2 =  self.plot2.plot(self.x, self.y_error, pen = pen)
        self.data_line3 =  self.plot3.plot(self.x, self.y_e_temperature, pen = pen)
        self.data_line4 =  self.plot4.plot(self.x, self.y_temperature, pen = pen)
        horizontalGroupBox.setLayout(layout_plots) # set group box layout with plots
        hlayout2.addWidget(plot_win) # add plot graphics window to horizonatl layout with other widges
        self.widget.setLayout(hlayout2) # set main layout as horizontal layout with all widgets
        self.setCentralWidget(self.widget) # set main widget as centered
      
    def connect_ard(self): # run with start button pressed
        
        if self.connected == False: # if not connected yet
            self.output.append('Connecting to Arduino') # output appends go to textbox
            try:
                self.serial_port = QtSerialPort.QSerialPort(self.device) # try connecting to set com device
            except:
                print('Could not open port')
    
            if self.verbose: print(f'Found device at {self.device}')
            self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud115200) # baud rate set same as arduino
            self.serial_port.errorOccurred.connect(self.handle_error) # serial port errors run handle_error
            self.serial_port.open(QtCore.QIODevice.ReadWrite) # open read write
            self.serial_port.setDataTerminalReady(1) # reset arduino with dtr
            self.serial_port.setDataTerminalReady(0)
            self.serial_port.setDataTerminalReady(1)
            self.serial_port.readyRead.connect(self.handle_ready_read) # readyread signals run handle_ready_read slot
            buf = self.serial_port.clear() # clear the buffer
            if self.verbose: print(f'Values in buffer cleared: {buf} ')
            self.send("HANDSHAKE\n") # send to arduino to wait for handshake
        
        if self.connected == True: # if already connected, reset arrays and send start again and running to true
            self.mainStorage = []
            self.initSetRecord = [] 
            self.x = []
            self.y_out = []
            self.y_error = []
            self.y_e_temperature = []
            self.y_temperature = [] 
            self.send('START')
            self.running = True
   
    def handle_ready_read(self):
        
        while self.serial_port.canReadLine() and self.running: # if running and readline available in input buffer

            try:
                if self.verbose: print('Waiting for response...')
                #resp = self.serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip()

                resp_raw = self.serial_port.readLine().data().decode('ISO-8859-1', errors='ignore')#.split('\r\n')[0].replace('\n', '') # raw response used to start, looks for first index, decodes single bytes with latin-1, ignores errors
                resp = resp_raw.split('\r\n')[0].replace('\n', '') # gets the raw response and splits along \r\n, gets first element and gets rid of \n
                #print('raw resp', resp_raw)
                if self.verbose: print('Got response', resp)
                
                if resp == "HANDSHAKE" and self.connected == False: # if get handshake response and not connected
                    print("Successful handshake, Arduino and Python are communicating\n")
                    self.connected = True # set as connected
                    self.band_button.setEnabled(True) # buttons are enabled
                    self.tset_button.setEnabled(True)
                    self.dt_button.setEnabled(True)
                    self.save_button.setEnabled(True)
                if self.connected == False: # if not connected
                    self.send('HANDSHAKE\n') # send handshake again
                    if self.verbose: print("Exception")
                    if self.attempts == 15: # if tried 15 times, raise exception and close window
                        raise Exception(f"\nUnable to handshake with Arduino...{self.attempts} exceptions")
                        self.close()
                    self.attempts += 1
                
                if self.connected == True and self.trying == True and resp != 'READY' and resp != 'HANDSHAKE': # if connected and trying to get init variables and the response isn't ready or handshake
                    splitVar = resp.split("\t")   # Clean it, split along tabs
                    self.rowCount += 1                     # Add to count
                    for i in splitVar:
                        if i != '=' and i != "": # cleans junk, ignores these parts
                            self.outputArry.append(i)    # Put into the variable array  

                if self.connected == True and resp == 'READY' and self.trying == True: # if response is ready, sent all init variables, and trying to get init variables
                    self.trying = False # no longer trying to get init variables after this
                    print("\nINIT variables acquired: ")
                    self.outputArry = np.reshape(self.outputArry, (self.rowCount-1, 4)) # Minus 1 because there's a junk line to remove
                    for i in self.outputArry:
                        i[2] = self.convertHexToDec(i[2])                   # Convert the values from hex float to dec float
                    print(self.outputArry) 
                    self.output.append(str(self.outputArry)) # show in text box
                    self.initVar = self.outputArry # initial variables set to output array
                    self.initVarCount = self.rowCount - 1 # counts initial variables 
                    self.send('START') # send start again to restart index

                if self.connected == True and self.trying == False and self.clearing == False and self.labelTables == True and resp != '':
                    if self.started_data_collection == False:
                        if self.verbose : 
                            print("\nStarting data collection")  
                        self.started_data_collection = True # collection has started
                
                    respSplit = resp.split("\t")    # Create table

                    if len(respSplit) != 5 and len(respSplit) != 3:  # Helps avoid processing junk
                        if self.verbose: print("\n\nGARBAGE FOUND IN dataCollection (", respSplit,") BAD RESPONSE LENGTH.\n\n")
                        
                    elif respSplit[0] == "INDEX":               # Get the time index
                        self.tempStorage.append(int(respSplit[2]))   # Append the index to tempStorage
                        
                    elif respSplit[0] == "VALUE":                       # Collect the unit
                        respConv = self.convertHexToDec(respSplit[3])   # Converts from hex float to decimal float
                        self.tempStorage.append(respConv)                    # Convert then add value to the tempStorage  
                        
                    else :
                        if self.verbose: print("\n\nGARBAGE FOUND IN dataCollection: ", resp, "\n\n")        # Catches the garbage of length 5 and 3
                        
                    #if (len(tempStorage) == (len(self.headerTable))) :  # Once a block has been completely read, it's time to append the data to the main storage array
                    if len(self.tempStorage) == len(self.headerTable):  # Once a block has been completely read, it's time to append the data to the main storage array
                            self.mainStorage.append(self.tempStorage)        # Add temp to main array
                            if self.verbose: print("DATA STORED AS: ", self.tempStorage, "\n")
                            if self.started_data_collection == True:
                                self.output.append(str([round(i, 4) for i in self.tempStorage])) # show data in textbox
                                self.update_plots(self.tempStorage) # update plots
                            self.tempStorage = []   

                if self.connected == True and self.trying == False and self.clearing == False and self.labelTables == False and resp != '': # getting label tables
                    if self.verbose: print("CREATING LABEL TABLES")
                    line = resp.split("\t")              # Split data by tab 
                    print("\nLINE: ", line)
                    if line[0] =="VALUE":              # Lines with VALUE in the first position represent the recorded variables
                        self.headerTable.append(line[1]) # Index one is where the variable names are stored
                        self.unitTable.append(line[4])   # Index four is where the variale's units are stored
                        if self.verbose : print("Header Table: ", self.headerTable)
                        if self.verbose : print("Unit Table: ", self.unitTable)
                    elif line[0] == "INDEX":           # If it begins with INDEX, then one full block has been completed
                        self.headerTable.append('Time Index')  # add to header table
                        self.recVarCount = len(self.headerTable) # number of variables received
                        if self.verbose : print("Header Table: ", self.headerTable)
                        self.labelTables = True # now have label tables
                        self.output_label.setText(str(self.headerTable)) # labels the output with variables
                        self.send('START') # send start again to restart index
                        
                if self.connected == True and self.trying == False and self.clearing == True and resp != 'READY': # clearing junk to be done
                    if resp_raw == 'INDEX\t0\t1\n': # excpected response  
                        self.clearing = False # no longer clearing junk
                        if self.verbose: print("Done clearing junk!") 
                    elif resp_raw == '': # if don't get wanted index response
                        self.send('START') # send again
                        if self.attemptCount == 5: # if tried for index response 5 times, raise exception
                            raise Exception("EXCEPTION: Unable to successfully start data acquisition.")
                        self.attemptCount += 1
                                     
            except ValueError as e: # if value error reading from serial port
                print("error", e)

    def handle_error(self, error): # handles serial port errors
        if error == QtSerialPort.QSerialPort.NoError:
            return # if no error to record, return nothing
        print(error, self.serial_port.errorString()) # print error if it exists
     
    def closeEvent(self, event): # when window is closed, which quit button also does
        super(MainWindow, self).closeEvent(event)
        try:
            self.send('STOP') # Stops data collection and data retention
            self.serial_port.setDataTerminalReady(0) # reset arduino to 0 so can be rerun
            self.serial_port.setDataTerminalReady(1)
            self.serial_port.setDataTerminalReady(0)
            self.serial_port.close() # close serial port

            app.quit() # end pyqt eventloop
            print('\nPort is now closed')

        except AttributeError: # If self.serial_port doesn't exist
            print('\nPort was not opened')  
            app.quit() # end eventloop

        except: # Other errors could be found by removing the try statement if unsure
            print('\nClosing error')
            app.quit() # end eventloop
            
        print('\nThank you for using Adruino GUI Controller, have a nice day.')

    def update_plots(self, data):
        
        self.x.append(data[4]) # adds time steps to x
        self.y_out.append(data[0]) # adds data to y, for each below
        self.y_error.append(data[1])
        self.y_e_temperature.append(data[2])
        self.y_temperature.append(data[3])
        
        #self.plot1.setXRange(int(max([data[4]])) - 100 , int(max([data[4]])), padding = 0) # can be used to set plot ranges, with the number being subtracted, e.g. 100
        #self.plot2.setXRange(int(max([data[4]])) - 100 , int(max([data[4]])), padding = 0) 
        #self.plot3.setXRange(int(max([data[4]])) - 100 , int(max([data[4]])), padding = 0) 
        #self.plot4.setXRange(int(max([data[4]])) - 100 , int(max([data[4]])), padding = 0) 
        
        self.data_line1.setData(self.x, self.y_out) # these update the data
        self.data_line2.setData(self.x, self.y_error)
        self.data_line3.setData(self.x, self.y_e_temperature)
        self.data_line4.setData(self.x, self.y_temperature)
        
    def send(self, text):
        text = text + '\n' # arduino code uses the \n
        self.serial_port.write(text.encode()) # encode string to bytes and write to serial port
        if self.verbose: print(f"Sent '{text}'")

    def pause(self):
        
        self.send('STOP') # Stops data collection and data retention
        self.running = False # stops data collection
        self.output.append('Paused ' + str(not self.running)) # show if paused in textbox

    ## Function to change parameters defined on the Arduino. Best used only when running, and could probably use a run condition based on the flag self.running
    def settings(self, varName, inputVal): 
        try:
            inputVal = str(float(inputVal)) # to check proper data type entered
        except:
            print("\nCANNOT SET, BAD INPUT: Only integer and float values are accepted.\n")
            return
            
        print("Sending to Arduino")                                                  
        packedMessage = "SET "+ varName + " " + str(inputVal) # put together set message
        if len(self.mainStorage) > 0: # if data in mainstorage
            latestVals = self.mainStorage[-1] # last value in main storage
        else:
            latestVals = [0] # if no values in main storage, probably should be [0,0,0,0], though set buttons are deactivated when program starts, so there should be some data 
        self.initSetRecord.append([varName, inputVal, latestVals[4]]) # gets variable name, new set value, and last time index
        
        self.send(packedMessage) # sends set message to arduino
        self.serial_port.flush() # Wait for the serial line to finish clearing
        self.send("\n")     # Add a newline character to finish the message
        
        print("Sent " + packedMessage + " to Arduino")                   

    ## Saves the data from main storage, and if there are any SET operations done, that also will be stored
    def save_file(self):   
        saveFileName = self.save.text()
        ## Handle the filename
        if saveFileName == '': # if no save file name
            timeDate = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # get datetime string
            saveFileName =  timeDate + " PRIMARY THERMAL DATA.csv" # create filename    
            initRecName =  timeDate + " INIT CHANGES.csv" # create init changes filename
        elif saveFileName != '': # if there is a save filename
            initRecName = saveFileName + " INIT CHANGES.csv" # add init changes to filename
            saveFileName = saveFileName + '.csv' # add .csv to filename
            
        ## Add the header table to the main storage array, for ease of reading when the data is examined later
        self.mainStorage.insert(0, self.headerTable) 
        if self.verbose: print("Main storage array:", self.mainStorage)
        
        ## Actually Save      
        np.savetxt(saveFileName, self.mainStorage, delimiter =",", fmt = '%s')
        print("\n\nSaved main storage under the filename: ", saveFileName, "\n\n")
        
        ## If there's any SET operations recorded, save them too
        if len(self.initSetRecord) > 0:
            initRecHeader =["Variable", "Value", "Time Index"]
            self.initSetRecord.insert(0, initRecHeader) # put header at top of record
            np.savetxt(initRecName, self.initSetRecord, delimiter = ',' , fmt = '%s')
            print("Changes to INIT variables have been recorded and saved as: ", (initRecName))
        
        self.save.clear()

    def convertHexToDec(self, hexVal): # Used to convert data sent from Arduino
        try:
            if hexVal == '0': # if just 0
                hexVal = "00000000" # turn into hexadecimal value
            value = struct.unpack('!f', bytes.fromhex(hexVal))[0] # struct module performs conversions between Python values and C structs represented as Python bytes objects. create bytes from hexadecimal value, unpack it as float from big-endian byte order, and take first value since result is tuple
            return value    
        except:
            print("JUNK DATA: " + hexVal)
            
        
app = QtWidgets.QApplication(sys.argv) # qt app instance, (sys.argv is used for values from command line, so probably not needed, unless run with if name is main syntax)
w = MainWindow(device = device, verbose = 0) # main window instance
w.show() # show window

sys.exit(app.exec_()) # start app and exit program when done



  
