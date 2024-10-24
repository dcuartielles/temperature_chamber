from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import time
import serial
import logging


class TestBoardWorker(QThread):
    update_upper_listbox = pyqtSignal(str)  # signal to update instruction listbox

    def __init__(self, port, baudrate, timeout=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
        self.is_open = True
        self.is_running = True  # flag to keep the thread running
        self.is_stopped = False  # flag to stop the read loop
        self.test_data = None
        self.last_command_time = time.time()

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logging.info(f'test board worker connected to arduino port: {self.port}')
            print(f'connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            logging.error(f'error: {e}')
            return False

    # serial response readout
    def run(self):
        if not self.serial_setup():
            logging.error(f'test board worker failed to connect to {self.port}')
            print(f'failed to connect to {self.port}')
            return
        logging.info('test board thread is running')
        print('test board thread is running')

        while self.is_running:
            if not self.is_stopped:
                try:
                    if self.ser and self.ser.is_open:
                        # continuous readout from serial
                        response = self.ser.readline().decode('utf-8').strip()
                        if response:
                            self.show_response(response)
                        if time.time() - self.last_command_time > 5:
                            self.last_command_time = time.time()
                            logging.info('test worker thread is running')
                            print('test worker thread is running')
                except serial.SerialException as e:
                    logging.error(f'serial error: {e}')
                    print(f'serial error: {e}')
                    self.is_running = False
            time.sleep(0.1)  # avoid excessive cpu usage
        self.stop()

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            logging.info(f'connection to {self.port} closed now')
            print(f'connection to {self.port} closed now')
        self.quit()
        self.wait()

    # show serial response
    def show_response(self, response):
        if response:
            self.update_upper_listbox.emit(response)  # emit signal to update listbox