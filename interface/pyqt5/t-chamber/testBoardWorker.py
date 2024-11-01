from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import time
import serial
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger(__name__)


class TestBoardWorker(QThread):

    update_upper_listbox = pyqtSignal(str)  # signal to show t-board output
    expected_outcome_listbox = pyqtSignal(str)  # signal to show expected test outcome
    empty_output = pyqtSignal(str)  # signal for waiting for output
    incorrect_output = pyqtSignal(str)  # signal to update main
    correct_or_not = pyqtSignal(bool)


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
            logger.info(f'test board worker connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException:
            logger.exception('error')
            return False

    # serial response readout
    def run(self):
        if not self.serial_setup():
            logger.error(f'test board worker failed to connect to {self.port}')
            return
        logger.info('test board thread is running')

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
                            logger.info('test worker thread is running')
                except serial.SerialException as e:
                    logger.exception(f'serial error: {e}')
                    self.is_running = False
            time.sleep(0.1)  # avoid excessive cpu usage
        self.stop()

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            logger.info(f'connection to {self.port} closed now')
        self.quit()
        self.wait()

    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_expected_outputs = []
            all_tests = [key for key in test_data['tests'].keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data['tests'].get(test_key, {})
                expected_output = test.get('expected output', '')  # get the expected output string
                if expected_output:
                    all_expected_outputs.append(expected_output)
            return all_expected_outputs
        return []

    # display expected output
    def display_expected(self):
        expected = self.exp_output()
        self.expected_outcome_listbox.emit(expected)

    # return the firs expected output as all expected output is the same per test
    def exp_output(self):
        exp_outputs = self.expected_output(self.test_data)
        exp_output = exp_outputs[0]
        return exp_output

    # show serial response and check if output is as expected
    def show_response(self, response):
        self.update_upper_listbox.emit(response)

        # notify user test board is working but has nothing to print yet
        if response == '':
            message = 'waiting for test board output...'
            logger.info(message)
            self.empty_output.emit(message)
        else:
            self.check_output(response)

    # compare t-board output with expected test outcome
    def check_output(self, response):
        expected = self.exp_output()
        if str(expected) == response:
            logger.info("correct test output")
            self.correct_or_not.emit(True)
        else:
            date_str = datetime.now().strftime("%m/%d %H:%M:%S")
            error_message = f"{date_str}    incorrect test board output"
            self.incorrect_output.emit(error_message)
            self.correct_or_not.emit(False)
            logger.error(response)