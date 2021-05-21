# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui
import sys
import numpy as np
import datetime
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# most lines were explained in nogui, basic, timer or qthread(2) geigercounting files
class WorkerSignals(QtCore.QObject): # object for creating signals as before

    #finished = QtCore.pyqtSignal() # may be needed

    result = QtCore.pyqtSignal(object)

class GenericWorker(QtCore.QRunnable): # qrunnable is parent class here, used with qthreadpool

    def __init__(self, func):
        super().__init__()
        
        self.signals = WorkerSignals() # signals are from another object here
        self.func = func # create class attribute with function


# =============================================================================
#     @QtCore.pyqtSlot() # may be needed, but emitting is taken care of elsewhere
#     def run(self):
#         pass
# =============================================================================
# =============================================================================
#         try:
#             #result = self.fn(*self.args, **self.kwargs)
#             result = self.func(*self.args, **self.kwargs)
#         except:
#             pass
#         else:
#             self.signals.result.emit(result)  
#         finally:
# =============================================================================
            #self.signals.finished.emit()  
            
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, verbose = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.threadpool = QtCore.QThreadPool() # threadpool for multiple threads if needed
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

        self.widget.setLayout(vlayout)
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
                    if QtSerialPort.QSerialPortInfo(QtSerialPort.QSerialPort(port.portName())).description()[0:4] == 'Comm':
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
                #resp = bytes(self.serial_port.readAll()).decode('ISO-8859-1').replace('\n','').replace('\r','') # Another way to read
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

                        self.wg = MainWindowg()
                        self.wg.show()
                        self.worker = GenericWorker(self.wg.update_plot) # worker initialized with update plot

                        self.worker.signals.result.connect(self.wg.update_plot) # result signal is connected with updated plot

                        self.threadpool.start(self.worker) # threadpool is started with worker

                    if self.counter >= self.counter_comm + 4:

                        self.counts.append(float(resp))
                        self.worker.signals.result.emit(self.counts) # result signal emits counts

                    if len(self.counts) == (self.intervals_value * self.replicas_value):
                        if self.prints.checkState() == 2:
                            print(self.output.toPlainText())
                        
                        self.wg.close()
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
            self.wg.close()
        except:
            print('No plotting window started')
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

            QtWidgets.QApplication([]).quit()
            print('Port is now closed')

        except IndexError as ei: # If there is an error with filling in heights, if the window was closed early
            print(ei)
            try:    

                self.serial_port.close()

                QtWidgets.QApplication([]).quit()
                print('Port is now closed, no data saved')

            except AttributeError as ea: # If self.serial_port doesn't exist
                print('Port was not opened')
                print(ea)
                QtWidgets.QApplication([]).quit()        

        except AttributeError as ea: # If self.serial_port doesn't exist
            print('Port was not opened') 
            print(ea)
            QtWidgets.QApplication([]).quit()

        except: # Other errors could be found by removing the try statement if unsure
            print('Closing error')
            QtWidgets.QApplication([]).quit()



# like other thread plotting
class MainWindowg(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.setCentralWidget(self.canvas)

        self.show()

    @QtCore.pyqtSlot(object)
    def update_plot(self, counts):
        self.canvas.axes.cla()  

        self.canvas.axes.hist(counts)#, bins = bns)
        self.canvas.axes.set_ylabel('Occurrences')
        self.canvas.axes.set_xlabel('Counts per interval')
        self.canvas.axes.set_title('Geiger counter')

        self.canvas.draw()
        

class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        
app = QtWidgets.QApplication(sys.argv)
w = MainWindow(verbose = 1)
w.show()

sys.exit(app.exec_())



  
