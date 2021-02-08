from PyQt5 import QtCore, QtWidgets, QtSerialPort
import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.serial_port = QtSerialPort.QSerialPort("COM3")
        self.serial_port.setBaudRate(QtSerialPort.QSerialPort.Baud9600)
        self.serial_port.errorOccurred.connect(self.handle_error)
        self.serial_port.readyRead.connect(self.handle_ready_read)        
        self.serial_port.open(QtCore.QIODevice.ReadWrite)
          
    def handle_ready_read(self):
        while self.serial_port.canReadLine():
            #codec = QtCore.QTextCodec.codecForName("UTF-8") # only use one read option, comment out the others
            #line = codec.toUnicode(self.serial_port.readLine()).strip().strip('\x00')
            try:
                #print('serial port readall', bytes(self.serial_port.readAll()).decode())
                print('serial port readline data', self.serial_port.readLine().data().decode())
                #print(line)
            except ValueError as e:
                print("error", e)

    def handle_error(self, error):
        if error == QtSerialPort.QSerialPort.NoError:
            return
        print(error, self.serial_port.errorString())
     
    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)
        self.serial_port.close()

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()

app.exec_()




  