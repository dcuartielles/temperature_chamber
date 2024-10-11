import time
from PyQt5.QtCore import QThread, pyqtSignal
import serial
import threading


class SerialCaptureWorker(QThread):
    update_listbox = pyqtSignal(str)  # signal to update instruction listbox
    update_chamber_monitor = pyqtSignal(str)  # signal to update chamber monitor

    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com
        self.is_running = True
        self.last_command_time = time.time()

    def run(self):

        while self.is_running:
            response = self.serial_com.ser.readline().decode('utf-8').strip()  # continuous readout from serial
            if response:
                self.process_response(response)

            if time.time() - self.last_command_time > 1.5:
                self.last_command_time = time.time()
                self.trigger_read_data()
            time.sleep(0.1)

    def trigger_read_data(self):
        response = self.serial_com.read_data()
        if response:
            self.update_chamber_monitor.emit(response)

    def process_response(self, response):
        trigger_responses = ['Setting', 'Running', 'Test complete', 'Target temp', 'Sequence complete']
        if any(response.strip().startswith(trigger) for trigger in trigger_responses):
            self.update_listbox.emit(response)

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
