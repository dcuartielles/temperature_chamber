from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import json
from logger_config import setup_logger

logger = setup_logger(__name__)

class SerialCaptureWorker(QThread):

    update_listbox = pyqtSignal(str)  # signal to update listbox
    update_chamber_monitor = pyqtSignal(str)  # signal to update chamber monitor
    trigger_run_tests = pyqtSignal(dict)  # signal from main to run tests

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
        self.last_readout = time.time()
        self.test_data = None
        self.trigger_run_tests.connect(self.run_all_tests)

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            time.sleep(0.1)
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f'connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready

            return True
        except serial.SerialException:
            logger.exception('error')
            return False

    # method to run the thread
    def run(self):
        if not self.serial_setup():
            logger.error(f'failed to connect to {self.port}')
            return
        logger.info('thread is running')

        while self.is_running:
            if not self.is_stopped:
                try:
                    if self.ser and self.ser.is_open:
                        # read incoming serial data
                        response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                        if response:
                            self.process_response(response)

                        if time.time() - self.last_command_time > 1:
                            self.last_command_time = time.time()
                            self.trigger_read_data()
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
            logger.info(f'connection to {self.port} closed')
        self.quit()
        self.wait()

    # sends a command to arduino via serial
    def send_command(self, command):
        try:
            if self.ser and self.ser.is_open:
                self.ser.reset_input_buffer()  # clear the gates
                self.ser.write((command + '\n').encode('utf-8'))  # encode command in serial
                logger.info(f'sent command: {command}')
                time.sleep(0.01)  # small delay for command processing
            else:
                logger.warning('connection is not open')

        except serial.SerialException as e:
            logger.exception(f'error sending command: {e}')
        except Exception as e:
            logger.exception(f'unexpected error: {e}')

    # senf json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert python dictionary to json
        try:
            if self.ser and self.ser.is_open:
                self.ser.write((json_data + '\n').encode('utf-8'))
                time.sleep(0.01)
                logger.info(f'sent to arduino: {json_data}')

                # continuously read arduino output (blocking method, runs inside the thread)
                while self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    logger.info(f'arduino says: {response}')
            else:
                logger.warning('serial not open')
        except serial.SerialException as e:
            logger.error(f'error sending JSON: {e}')

    # read data
    def read_data(self):
        if not self.is_stopped and self.ser and self.ser.is_open:
            try:
                self.send_command('SHOW DATA')
                response = self.ser.readline().decode('utf-8').strip()
                if response:
                    if response.lower().startswith('error'):
                        logger.info(response)
                        return
                    logger.info(f'arduino says: {response}')
                    return response
                else:
                    logger.info('there was nothing worth saying here')
                    return None
            except serial.SerialException as e:
                logger.exception(f'error reading data from control board serial: {e}')
                return None
        else:
            logger.warning('serial closed or stopped')
            return None

    # run the entire test file
    def run_all_tests(self, test_data):
        if test_data is not None:
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, {})
                if 'chamber_sequences' in test:  # if the test data is available
                    self.send_json_to_arduino({test_key: test})  # send the data to arduino
                    # print status and update the listbox
                    logger.info(f'sending full test {test_key}')
                else:
                    logger.warning(f'{test_key} not found')
        else:
            # handle case when no test data is found
            logger.warning('no test data found on file')

    # set temp & duration from the gui
    def set_temp(self, input_dictionary):
        if input_dictionary is not None:
            logger.info(input_dictionary)
            set_temp_data = input_dictionary[0]
            self.send_json_to_arduino(set_temp_data)
        else:
            logger.warning('nothing to set the t-chamber to')

    def trigger_read_data(self):
        response = self.read_data()  # read data using custom method
        if response:
            self.update_chamber_monitor.emit(response)  # emit signal to update the chamber monitor

    # process serial response
    def process_response(self, response):
        # list of responses to be picked up
        trigger_responses = ['Setting', 'Running', 'Waiting', 'Test complete', 'Target temp', 'Sequence complete']
        if any(response.strip().startswith(trigger) for trigger in trigger_responses):
            self.update_listbox.emit(response)  # emit signal to update listbox
            logger.info(f'{response}')
        else:
            logger.info(response)

    # emergency stop
    def emergency_stop(self):
        self.send_command('EMERGENCY STOP')
        logger.info('emergency stop issued')
        message = 'EMERGENCY STOP'
        self.update_listbox.emit(message)
