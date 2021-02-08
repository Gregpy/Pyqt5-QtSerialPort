import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtSerialPort
import sys
import matplotlib.pyplot as plt

times = []
clicks = []

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(100))  
        self.y = [0 for _ in range(100)] 

        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)

        self.serial_port = QtSerialPort.QSerialPort("COM3")
        self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600)
        self.serial_port.errorOccurred.connect(self.handle_error)
        self.serial_port.readyRead.connect(self.handle_ready_read)
        self.serial_port.open(QtCore.QIODevice.ReadWrite)


    def handle_ready_read(self):
        while self.serial_port.canReadLine():
            codec = QtCore.QTextCodec.codecForName("UTF-8")
            line = codec.toUnicode(self.serial_port.readLine()).strip().strip('\x00')
            try:
                print(line)
                value = float(line)
            except ValueError as e:
                print("error", e)
            else:
                self.update_plot(value)


    def handle_error(self, error):
        if error == QtSerialPort.QSerialPort.NoError:
            return
        print(error, self.serial_port.errorString())

    def update_plot(self, value):
        self.y = self.y[1:] + [value/255]
        self.x = self.x[1:]  
        self.x.append(self.x[-1] + 1)  
        self.data_line.setData(self.x, self.y) 
        if self.y[-1] > 0.3 and self.y[-3] < 0.3 and self.y[-2] < 0.3:
            times.append(self.x[-1]) # time values are dependent on rate information is sent from arduino
            #clicks.append(self.y[-1])
            clicks.append(1)
     
    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)
        self.serial_port.close()

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()

app.exec_()

plt.plot(times, clicks, 'o')
plt.xlabel('Time')
plt.ylabel('Clicks')
plt.show()
print('Timestamps: ', times)