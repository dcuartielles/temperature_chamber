from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import time
import serial
import re
from logger_config import setup_logger

logger = setup_logger(__name__)


class TestBoardWorker(QThread):

    update_upper_listbox = pyqtSignal(str)  # signal to update instruction listbox
    expected_outcome_listbox = pyqtSignal(str)  # signal to show expected test outcome

    def __init__(self, test_data, port, baudrate, timeout=5):
        super().__init__()
        self.test_data = test_data
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
        self.is_open = True
        self.is_running = True  # flag to keep the thread running
        self.is_stopped = False  # flag to stop the read loop
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

    # main operating method for serial response readout
    def run(self):
        if not self.serial_setup():
            logger.error(f'test board worker failed to connect to {self.port}')
            return
        logger.info('test board thread is running')
        # wrap the whole while-loop in a try-except statement to prevent crashes in case of system failure
        try:
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
        except Exception as e:
            # catch any other unexpected exceptions
            logger.exception(f'unexpected error: {e}')
            self.is_running = False

        self.stop()

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            logger.info(f'connection to {self.port} closed now')
        self.quit()
        self.wait()

    # show serial response
    def show_response(self, response):
        if response:
            printout = f'{response}'
            if self.test_data:
                message = self.extract_deterministic_part(printout)  # extract deterministic output part
                self.update_upper_listbox.emit(message)  # emit signal to update listbox
                self.expected_outcome_listbox.emit(message)  # emit signal to update expected outcome
            else:
                self.update_upper_listbox.emit(printout)  # emit signal to update listbox
                self.expected_outcome_listbox.emit(printout)  # emit signal to update expected outcome

    # DETERMINISTIC AND NON-DETERMINISTIC OUTPUT READOUT
    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_expected_outputs = []
            all_tests = [key for key in test_data['tests'].keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data['tests'].get(test_key, {})
                expected_output = test.get('expected_output', '')  # get the expected output string
                if expected_output:
                    all_expected_outputs.append(expected_output)
            return all_expected_outputs
        return []

    # get expected pattern
    def get_expected_pattern(self):
        if self.test_data:
            exp_outputs = self.expected_output(self.test_data)
            regex_patterns = []
            for expected in exp_outputs:
                regex_pattern = self.encode_pattern(expected)
                regex_patterns.append(regex_pattern)
            logger.debug(f'getting expected pattern dict: {regex_patterns}')
            expected_pattern = regex_patterns[0]
            return expected_pattern
        else:
            return

    # encode pattern
    def encode_pattern(self, expected_pattern):
        if '***' in expected_pattern:
            # escape special characters and use '(.*)' as a placeholder for non-deterministic parts
            regex_pattern = re.escape(expected_pattern).replace(r'\*\*\*', '(.*)')
        else:
            regex_pattern = expected_pattern
        regex_pattern = f'^{regex_pattern}$'
        logger.debug(f'encoding pattern: {regex_pattern}')
        return regex_pattern

    # extract deterministic test output part
    def extract_deterministic_part(self, message):
        regex_pattern = self.get_expected_pattern()
        match = re.match(regex_pattern, message)
        logger.debug('about to search for matches')
        if match:
            if '(.*)' in regex_pattern:
                # non-deterministic part is captured as the first group in the match
                non_deterministic_part = match.group(1) if match.lastindex is not None else ''
                # extract non-deterministic captured group '(.*)'
                deterministic_parts = re.split(r'\(\.\*\)', regex_pattern)
                deterministic_output = "".join(deterministic_parts)
                if non_deterministic_part:
                    logger.info(f'non-deterministic output: {non_deterministic_part}')
                logger.debug(f'deterministic_output: {deterministic_output}')
                return deterministic_output
            else:
                # if the pattern is fully deterministic, return the message as-is
                logger.debug(f'fully deterministic match: {message}')
                return message
        logger.debug(f'no matches found, the message is: {message}')
        return message
