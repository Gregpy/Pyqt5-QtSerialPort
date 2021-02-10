from PyQt5 import QtCore, QtWidgets, QtSerialPort
import sys
import time

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Counting clicks, close to stop and print time stamps")
        self.setFixedWidth(500)
        self.setFixedHeight(1)
        self.numCount = 0
        self.maxCounts = 10 # How many counts wanted
        self.clicks = []
        self.timeStamps = []
        self.startTime=time.time()
        self.serial_port = QtSerialPort.QSerialPort("COM3")
        self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600)
        self.serial_port.readyRead.connect(self.handle_ready_read)        
        self.serial_port.open(QtCore.QIODevice.ReadWrite)
   
    def handle_ready_read(self):
        while self.serial_port.canReadLine():
            value = self.serial_port.readLine().data().decode()
            self.timeStamp=time.time()-self.startTime
            self.numCount += 1
            print(value, self.numCount, 'Time stamp:', self.timeStamp)
            self.clicks.append(1)
            self.timeStamps.append(self.timeStamp)
            if len(self.clicks) == self.maxCounts: 
                self.serial_port.close()
                self.close()
                break

    def closeEvent(self, event):
        super().closeEvent(event)
        self.serial_port.close()
        print('Time Stamps:', self.timeStamps)

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()

app.exec_()





  