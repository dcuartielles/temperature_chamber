import time

from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial


class ChamberMonitorWorker(QThread):
    update_chamber_monitor = pyqtSignal(str)  # signal to update chamber monitor

    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com
        self.is_running = True

    def run(self):
        while self.is_running:
            response = self.serial_com.read_data()  # call method that sends command and reads response
            if response:
                self.update_chamber_monitor.emit(response)
            time.sleep(1)

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
