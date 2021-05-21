from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui
import sys
import numpy as np
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # canvas for matplotlib plot
from matplotlib.figure import Figure # figure module used for making figure

# most lines have been explained in geigerCounting_pyqt5_nogui.py and geigerCounting_pyqt5.py 
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, verbose = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = MplCanvas(self, width = 5, height = 4, dpi = 100) # setup parameters of the matplotlib canvas 

        self.ydata = []  
        self.verbose = verbose
        self.setWindowIcon(QtGui.QIcon('mcgill_shield.png'))
        self.setWindowTitle("Geiger Counting")  
        if verbose: print('Arduino main window class creator: Verbose mode activated')
        self.widget = QtWidgets.QWidget()
        self.start_button = QtWidgets.QPushButton('Start', clicked = self.connect_ard)
        self.quit_button = QtWidgets.QPushButton('Quit', clicked = self.close)
        self.period_label = QtWidgets.QLabel('Period (ms)')
        self.period = QtWidgets.QLineEdit('0.2')
        self.replicas_label = QtWidgets.QLabel('Replicas')
        self.replicas = QtWidgets.QLineEdit('1')
        self.intervals_label = QtWidgets.QLabel('Intervals')
        self.intervals = QtWidgets.QLineEdit('100')
        self.output = QtWidgets.QTextEdit()
        self.prints = QtWidgets.QCheckBox()
        self.prints_label = QtWidgets.QLabel('Print textbox output')
        self.save_data = QtWidgets.QCheckBox()
        self.save_data.setChecked(True)
        self.save_data_label = QtWidgets.QLabel('Save data')
        hlayout_save_data = QtWidgets.QHBoxLayout()
        hlayout_save_data.addWidget(self.save_data_label)
        hlayout_save_data.addWidget(self.save_data)
        hlayout_prints = QtWidgets.QHBoxLayout()
        hlayout_prints.addWidget(self.prints_label)
        hlayout_prints.addWidget(self.prints)
        hlayout_period = QtWidgets.QHBoxLayout()
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
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(hlayout_replicas)
        vlayout.addLayout(hlayout_intervals)
        vlayout.addLayout(hlayout_period)
        vlayout.addLayout(hlayout_prints)
        vlayout.addLayout(hlayout_save_data)
        vlayout.addWidget(self.output)
        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout2.addLayout(vlayout)
        hlayout2.addWidget(self.canvas)
        #self.widget.setLayout(vlayout)
        self.widget.setLayout(hlayout2)
        self.setCentralWidget(self.widget)
      
    def connect_ard(self):
        self.replicas_value = int(self.replicas.text())
        self.period_value = float(self.period.text())
        self.intervals_value = int(self.intervals.text())
        self.output.append('Connecting to Arduino, press start again if Arduino is communicating is not shown')
        self.counter_comm = 0
        self.counter = 0
        self.counts = []
        
        if QtSerialPort.QSerialPortInfo().availablePorts(): # Finds Arduino   
            for port in QtSerialPort.QSerialPortInfo().availablePorts():
                try:
                    print('Port', port.portName(), QtSerialPort.QSerialPortInfo(QtSerialPort.QSerialPort(port.portName())).description())
                    if QtSerialPort.QSerialPortInfo(QtSerialPort.QSerialPort(port.portName())).description()[0:4] == 'Comm': # this checks if port is comm, then skips if it is
                        continue
                    self.serial_port = QtSerialPort.QSerialPort(port.portName())
                except:
                    print('Could not open port')
                    continue
                if self.verbose: print(f'Found device at {port.portName()}')
                self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600)
                self.serial_port.errorOccurred.connect(self.handle_error)
                self.serial_port.open(QtCore.QIODevice.ReadWrite)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.setDataTerminalReady(0)
                self.serial_port.setDataTerminalReady(1)
                self.serial_port.readyRead.connect(self.handle_ready_read) 
                buf = self.serial_port.clear() # clear the buffer
                if self.verbose: print(f'Values in buffer cleared: {buf} ')

        else:
            self.output.append('No Arduino found, check connection and press start again')
   
    def handle_ready_read(self):

        while self.serial_port.canReadLine():

            try:

                if self.verbose: print('Waiting for response...')
                resp = self.serial_port.readLine().data().decode('ISO-8859-1').replace('\n','').replace('\r','').strip()
                if resp[:6] == 'DEBUG:':
                    print("Got DEBUG response: " + resp)
                else:
                    if self.counter == self.counter_comm + 4:
                        self.output.append('Starting data collection')
                    self.output.append('Got response: ' + resp)
                    if self.verbose: print('Got response: ' + resp)
                    if resp == 'HELLO':
                        self.output.append('Arduino is communicating, setting period')
                        self.serial_port.write((str(self.period_value*1000) + '\n\n').encode())
                        self.counter_comm = self.counter
                        self.timer = QtCore.QTimer() # this is like a thread started for plotting, but a timer that updates at intervals 
                        self.timer.setInterval(int(self.period_value)) # intervals timer updates set by period so it updates at the same rate as the data
                        self.timer.timeout.connect(self.update_plot) # connect timeout signal (occurs at intervals set) to update_plot slot
                        self.timer.start() # start the timer, and hence the plotting
                    if self.counter >= self.counter_comm + 4:
                        self.counts.append(float(resp))
                    if len(self.counts) == (self.intervals_value * self.replicas_value):
                        if self.prints.checkState() == 2:
                            print(self.output.toPlainText())
                        self.close()
                        break
                    self.counter += 1

            except ValueError as e:
                print("error", e)

    def handle_error(self, error):
        if error == QtSerialPort.QSerialPort.NoError:
            return
        print(error, self.serial_port.errorString())
     
    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)
        try:
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
        
            self.serial_port.close()
            self.timer.stop()
            QtWidgets.QApplication([]).quit()
            print('Port is now closed')

        except IndexError: # If there is an error with filling in heights, if the window was closed early
            try:    

                self.serial_port.close()
                self.timer.stop()
                QtWidgets.QApplication([]).quit()
                print('Port is now closed, no data saved')

            except AttributeError: # If self.serial_port doesn't exist
                print('Port was not opened')
                QtWidgets.QApplication([]).quit()        

        except AttributeError: # If self.serial_port doesn't exist
            print('Port was not opened')  
            QtWidgets.QApplication([]).quit()

        except: # Other errors could be found by removing the try statement if unsure
            print('Closing error')
            QtWidgets.QApplication([]).quit()

    def update_plot(self): # slot function that runs at timer intervals
        self.canvas.axes.cla()  # clears the plot (not the fastest way to plot, but filling up a histogram usually isn't that fast)

        self.canvas.axes.hist(self.counts)#, bins = bns) # plot of histogram of the current counts
        self.canvas.axes.set_ylabel('Occurrences') # set the y label
        self.canvas.axes.set_xlabel('Counts per interval') # set the x label
        self.canvas.axes.set_title('Geiger counter') # set the title

        self.canvas.draw() # draw the plot in the canvas


class MplCanvas(FigureCanvas): # the figure canvas object where a matplotlib plot goes

    def __init__(self, parent = None, width = 5, height = 4, dpi = 100): # setup initial canvas parameters
        fig = Figure(figsize = (width, height), dpi = dpi) # create the matplotlib figure
        self.axes = fig.add_subplot(111) # add a subplot, the only one
        super(MplCanvas, self).__init__(fig) # initialize parent class figurecanvas with fig
        
app = QtWidgets.QApplication(sys.argv) # create instance of qapp
w = MainWindow(verbose = 0) # create instance of mainwindow
w.show() # show main window

sys.exit(app.exec_()) # start pyqt eventloop, exit when done



  
