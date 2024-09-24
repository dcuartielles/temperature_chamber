from PyQt5 import QtCore, QtSerialPort
import sys 

app = QtCore.QCoreApplication([]) 

serial_port = QtSerialPort.QSerialPort('COM3') 

serial_port.open(QtCore.QIODevice.ReadWrite) 

def handle_ready_read(): 
    print('to read')
    while serial_port.canReadLine():
        serialrd = serial_port.readLine().data().decode().strip()
        print(serialrd)
        serial_port.close()
        app.quit() 

serial_port.readyRead.connect(handle_ready_read) 

serial_port.write(bytes([100])) 
print('start')
sys.exit(app.exec_())