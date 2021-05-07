# Slowest plotter, matplotlib plot is cleared and redrawn each iteration
from PyQt5 import QtCore, QtSerialPort, QtWidgets 
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


steps = 360
degsPerStep = 1     # This has to be calibrated by you 
verbose = 0         # if want to see more details

arryAll = []        # Declare arrays for storing data.
stepCounts=[]       # Step indexes
adcValues = []      # ADC readings
device = 'COM4'     # Set COM port used by arduino

# Most of this was explained in laserInterface_pyqt5.py
if verbose: print("Verbose mode activated")

class MplCanvas(FigureCanvas): # canvas object for plot

    def __init__(self, parent = None, width = 5, height = 4, dpi = 100): # initialization of canvas and default settings
        fig = Figure(figsize = (width, height), dpi = dpi) # create a figure with set parameters
        self.axes = fig.add_subplot(111) # create a subplot and get axes
        super(MplCanvas, self).__init__(fig) # initialize figure in FigureCanvas

class MainWindow(QtWidgets.QMainWindow): # main window object

    def __init__(self, verbose = 0, *args, **kwargs): # initialize with any arguments and keyword arguments, and verbose 
        super(MainWindow, self).__init__(*args, **kwargs) # initialize qmainwindow 

        self.verbose = verbose # get verbose as attribute
        self.attempts = []
        self.connected = False
        
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100) # instantiate canvas
        self.setCentralWidget(self.canvas) # set canvas as central widget

        self.x = [] # list to be used for plotting x
        self.y = [] # list for y

        self.canvas.axes.set_xlim(0-10, steps*degsPerStep+10) # setting x limits of canvas
        self.canvas.axes.set_xlabel('Step Index') # setting x label
        self.canvas.axes.set_ylabel('ADC Reading') # y label

        #self.show() # show main window, not needed, shown near bottom of code

        self.serial_port = QtSerialPort.QSerialPort(device) # COM? choose COM port number
        
        self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud115200)
        self.isopen = self.serial_port.open(QtCore.QIODevice.ReadWrite) 
        
        if self.isopen:
            if self.verbose: print(f'Device found at {device}')
            pass
            
        else:
            print('Device not found')
            self.serial_port.close()
            app.quit()
            sys.exit()

        self.serial_port.setDataTerminalReady(1)
        self.serial_port.setDataTerminalReady(0)
        self.serial_port.setDataTerminalReady(1)
        print('serial port:' , self.serial_port)
        print('description:', QtSerialPort.QSerialPortInfo(self.serial_port).description())
        print('baud rate:' , self.serial_port.baudRate())
        print('data bits:', self.serial_port.dataBits())
        print('parity:' , self.serial_port.parity())
        print('stop bits:', self.serial_port.StopBits())
        print('DTR signal:', self.serial_port.DataTerminalReadySignal) 
        print('flow control:', self.serial_port.flowControl())
        print('is DTR' , self.serial_port.isDataTerminalReady())

        self.serial_port.clear()  
        
        self.serial_port.readyRead.connect(self.handle_ready_read) 
        
    def update_plot(self, adc): # used to update plot

        if len(self.x) == 0: # if no x yet
            self.x.append(0) # start at 0
        else:
            self.x.append(self.x[-1] + 1 * degsPerStep) # add to x eacy plot
        self.y.append(adc)  # Add a new value to y

        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.set_xlabel('Step Index') # has to be reset each time, like other aspects
        self.canvas.axes.set_ylabel('ADC Reading') 
        self.canvas.axes.set_xlim(0-10, steps*degsPerStep+10)
        self.canvas.axes.set_ylim(0, max(self.y)+10) # setting y limit with max of y
        self.canvas.axes.plot(self.x, self.y, 'r') # plot on the canvas
        # Trigger the canvas to update and redraw.
        self.canvas.draw()
     
    def send(self, text):
        text = text + '\n'
        self.serial_port.write(text.encode())
        if self.verbose: print(f"Sent '{text}'")
        
    def handle_ready_read(self): 

        while self.serial_port.canReadLine():
            if self.verbose: print('Waiting for response...')
            resp = self.serial_port.readLine().data().decode().strip()
            #resp = serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip() # another way to read data
            if self.verbose: print(f"Got response: '{resp}'")
            if self.connected == False and resp == "LASER 2017":
                
                if self.verbose: print("Arduino is communicating")
                self.connected = True
                self.send("LASER 1360") # Laser control voltage
                self.send(f"STEPS {steps}") # Total number of steps
                self.send("DELAY 4") # Delay time before reading value (ms), >4 recommende
                self.send("START") # Start the stepping/reading
                self.send("STOP") # Sends a signal to change a variable on the arduino such that the motor stops after one full loop
            
            elif self.connected == False and len(self.attempts) < 5:
                
                if self.verbose: print("Exception")
                self.attempts.append(1)
            
            elif self.connected == False and len(self.attempts) == 5:
                
                print("Unable to communicate with Arduino...5 exceptions")
                self.send("LASER 0") 
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.close()
                app.quit()            
                
            if 9 == len(resp) and resp[4] == ':':
    
                arryAll.append(resp)               # Append raw response to array of raw serial data
                print("Got response ", resp, "\n")
                    
                words = str.split(resp, ":")  # Split the response by the colon delimiter
        
                step = int(words[0])            # Note step count and append to appropriate array
                stepCounts.append(step)
                
                adc = int(words[1])            # Note A0 ADC value and append to appropriate array
                self.update_plot(adc) # tries to update plot with each new value, but it's slow
                adcValues.append(adc)
            
            else:
                
                print(f"Unexpected response: {resp}")
                print(f"Length: {len(resp)}")   
            
            if len(stepCounts) == steps:

                print('Closing port')
                self.send("LASER 0") 
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.close()
                #app.quit() # If automatic backend is set, this is not needed and it would close the plot quickly, with inline it is, the latter using app = QtCore.QCoreApplication([])  
    
            if resp == 'Timeout!':
                
                print('Timeout occured, closing')
                self.send("LASER 0") 
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.close()
                app.quit()             


 

app = QtWidgets.QApplication(sys.argv) # create pyqt app
app.setQuitOnLastWindowClosed(True) # end app when last window is closed
w = MainWindow() # main window instance
w.show() # show main window
sys.exit(app.exec_()) # start pyqt eventloop, end program when done