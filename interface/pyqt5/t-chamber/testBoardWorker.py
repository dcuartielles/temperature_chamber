from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import arduinoUtils
from cliWorker import CliWorker

import logging
import threading


class TestBoardWorker(QThread):
    # _serial_lock = threading.Lock()  # shared lock for serial communication
    update_upper_listbox = pyqtSignal(str)  # signal to update instruction listbox
    pause_serial = pyqtSignal()  # signal to pause serial worker thread
    resume_serial = pyqtSignal()  # signal to resume it

    def __init__(self, port, baudrate, timeout=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
        self.is_open = True
        self.is_running = True  # flag to keep the thread running
        self.is_stopped = False  # flag to stop the read loop
        self.last_command_time = time.time()
        self.test_data = None

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logging.info(f'connected to arduino port: {self.port}')
            print(f'connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            logging.error(f'error: {e}')
            return False

    # serial response readout
    def run(self):
        if not self.serial_setup():
            logging.error(f'failed to connect to {self.port}')
            print(f'failed to connect to {self.port}')
            return
        logging.info('test board thread is running')
        print('test board thread is running')

        while self.is_running:
            if not self.is_stopped:
                try:
                    if self.ser and self.ser.is_open:
                        logging.info('test worker thread is running')
                        print('test worker thread is running')
                        # read incoming serial data
                        response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                        if response:
                            self.show_response(response)
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

    # run the entire test file
    def run_all_tests(self, test_data, selected_t_port):
        if test_data and selected_t_port:  # take test_data & port number from main
            self.pause_serial.emit()  # emit pause signal to serial capture worker thread to avoid conflicts
            all_tests = [key for key in test_data.keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, {})
                sketch_path = test.get('sketch', '')  # get .ino file path
                if sketch_path:  # if the sketch is available

                    self.pause_test_board()  # pause this thread
                    self.cli_worker = CliWorker(selected_t_port, sketch_path)  # create a cli worker
                    self.cli_thread = QThread()
                    self.cli_worker.moveToThread(self.cli_thread)  # move cli worker to its thread

                    # connect signals and slots
                    self.cli_thread.started.connect(self.cli_worker.run)
                    self.cli_worker.finished.connect(self.cli_thread.quit)
                    self.cli_worker.finished.connect(self.resume_test_board)
                    self.cli_worker.finished.connect(self.cli_worker.deleteLater)
                    self.cli_thread.finished.connect(self.cli_thread.deleteLater)

                    # start the thread
                    self.cli_thread.start()

                    # wait for the thread to finish before moving to the next test/task
                    self.cli_thread.wait()
                else:
                    logging.warning('sketch path not found')
            self.resume_serial.emit()  # emit resume signal to serial capture worker
        else:
            # handle case when no test data is found
            print('can\'t do it')

    def pause_test_board(self):
        self.is_stopped = True
        print('test board worker is paused')

    def resume_test_board(self):
        self.is_stopped = False
        print('resuming test board worker')

    # show serial response
    def show_response(self, response):
        if response:
            self.update_upper_listbox.emit(response)  # emit signal to update listbox
