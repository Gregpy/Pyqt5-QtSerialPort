# Fastest and recommended way to live plot quickly, using pyqtgraph https://pyqtgraph.readthedocs.io/en/latest/introduction.html
from PyQt5 import QtCore, QtSerialPort, QtWidgets 
import sys
import pyqtgraph as pg # conda install -c anaconda pyqtgraph or conda install pyqtgraph or pip install pyqtgraph 

steps = 360
degsPerStep = 1     # This has to be calibrated by you 
verbose = 0         # if want to see more details

arryAll = []        # Declare arrays for storing data.
stepCounts=[]       # Step indexes
adcValues = []      # ADC readings
device = 'COM4'     # Set COM port used by arduino

# Most of this was explained in laserInterface_pyqt5.py or laserInterfaceGraph_pyqt5.py 
if verbose: print("Verbose mode activated")

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, verbose = 0, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.verbose = verbose
        self.attempts = []
        self.connected = False
        
        self.graphWidget = pg.PlotWidget() # create pyqtgraph widget
        self.setCentralWidget(self.graphWidget) # set plot as central widget
        self.x = []
        self.y = [] 
        
        self.graphWidget.setBackground('w') # set the plot background as white
        styles = {'color':'b', 'font-size':'20px'} # set the style to be used for labels
        self.graphWidget.setLabel('left', 'ADC Reading', **styles) # set the y label
        self.graphWidget.setLabel('bottom', 'Step Index', **styles) # set the x label
        self.graphWidget.setXRange(0, steps*degsPerStep) # set the x range 
        pen = pg.mkPen(color=(0, 0, 0)) # set a black pen to be used for plot line
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen = pen) # plot x and y and get the data line

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

    def update_plot_data(self, adc): # used to update plot
        
        if len(self.x) == 0:
            self.x.append(0)
        else:
            self.x.append(self.x[-1] + 1*degsPerStep)
        self.y.append(adc)  # Add a new value.
        self.graphWidget.setYRange(0, max(self.y)) # sets the y range to max of y
        self.data_line.setData(self.x, self.y)  # Update the plot line data

     
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

                self.update_plot_data(adc) # update plot
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
                #app.quit() # would close window at end
    
            if resp == 'Timeout!':
                
                print('Timeout occured, closing')
                self.send("LASER 0") 
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.close()
                app.quit()             


 

app = QtWidgets.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(True)
w = MainWindow()
w.show()
sys.exit(app.exec_())