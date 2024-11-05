from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import json

import popups
from logger_config import setup_logger
import commands
from datetime import datetime

logger = setup_logger(__name__)

class SerialCaptureWorker(QThread):

    update_listbox = pyqtSignal(str)  # signal to update listbox
    update_chamber_monitor = pyqtSignal(dict)  # signal to update chamber monitor
    trigger_run_tests = pyqtSignal(dict)  # signal from main to run tests
    trigger_interrupt_test = pyqtSignal()  # signal form main to send interrupt test command to arduino
    machine_state_signal = pyqtSignal(str)
    no_ping = pyqtSignal()

    # signals to main to update running test info
    is_test_running_signal = pyqtSignal(bool)
    update_test_label_signal = pyqtSignal(dict)
    current_test_signal = pyqtSignal(str)
    current_sequence_signal = pyqtSignal(int)
    desired_temp_signal = pyqtSignal(int)
    current_duration_signal = pyqtSignal(int)
    time_left_signal = pyqtSignal(int)
    # current_temp_signal = pyqtSignal(int)

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
        self.last_ping = time.time()
        self.last_readout = time.time()
        self.test_data = None
        self.trigger_run_tests.connect(self.run_all_tests)
        self.trigger_interrupt_test.connect(self.interrupt_test)
        self.sent_handshake = False
        self.alive = False
        self.timestamp = None
        self.machine_state = None
        self.is_test_running = None
        self.current_test = None
        self.current_sequence = None
        self.current_duration = None
        self.desired_temp = None
        self.time_left = None
        self.current_temperature = None


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
                        # send handshake
                        self.handshake()
                        time.sleep(0.1)
                        # read incoming serial data
                        '''response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                        if response:
                            self.process_response(response)'''

                        if time.time() - self.last_ping >= 0.6:
                            self.last_ping = time.time()
                            self.ping()

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

    # handshake
    def handshake(self):
        if not self.sent_handshake:
            time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            handshake = commands.handshake(time)
            logger.info(handshake)
            self.send_json_to_arduino(handshake)
            logger.info(f'handshake sent to arduino: {handshake}')
            # decode arduino response
            handshake_response = self.ser.readline().decode('utf-8').strip()

            try:
                # convert response string to dictionary
                parsed_response = json.loads(handshake_response)
                logger.info(parsed_response)
                if 'handshake' in parsed_response:
                    self.machine_state = parsed_response["handshake"].get('machine_state', '')
                    logger.info('extract machine state')
                    self.machine_state_signal.emit(self.machine_state)
            except json.JSONDecodeError:
                logger.exception('failed to parse arduino response')

            # prevent handshake from being sent again
            self.sent_handshake = True

    # ping
    def ping(self):
        ping = commands.ping()  # create ping command
        self.send_json_to_arduino(ping)  # send ping to arduino
        ping_response = self.ser.readline().decode('utf-8').strip()
        # convert response string to dictionary
        parsed_response = json.loads(ping_response)
        if 'ping_response' in parsed_response:
            ping_data = parsed_response['ping_response']
            # get all the data from ping & store it in class variables
            self.alive = ping_data.get('alive', False)
            self.timestamp = ping_data.get('timestamp', '')
            self.machine_state = ping_data.get('machine_state', '')
            self.machine_state_signal.emit(self.machine_state)
            # extract test status information and emit signals for gui updates
            self.current_temperature = ping_data.get('current_temp', 0)
            test_status = ping_data.get('test_status', {})
            self.is_test_running = test_status.get('is_test_running', False)
            self.is_test_running_signal.emit(self.is_test_running)
            self.current_test = test_status.get('current_test', '')
            self.current_sequence = test_status.get('current_sequence', 0)
            self.desired_temp = test_status.get('desired_temp', 0)
            # get duration and time left, and convert them for display
            self.current_duration = test_status.get('current_duration', 0) / 60000
            self.time_left = test_status.get('time_left', 0) / 60
            self.emit_test_status()
            self.display_info()

    # prep running test info updates to be emitted
    def emit_test_status(self):
        test_status_data = {
            'test': self.current_test,
            'sequence': self.current_sequence,
            'time_left': int(self.time_left)
        }
        self.update_test_label_signal.emit(test_status_data)
        logger.info(f'emitting test status data: {test_status_data}')

    # extract relevant info for display in serial monitor
    def display_info(self):
        relevant_info = {
            'current_temp': self.current_temperature,
            'desired_temp': self.desired_temp,
            'machine_state': self.machine_state
        }
        self.update_chamber_monitor.emit(relevant_info)

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

    # interrupt test on arduino
    def interrupt_test(self):
        interrupt = commands.interrupt_test()
        self.send_json_to_arduino(interrupt)

    # run the entire test file
    def run_all_tests(self, test_data):
        if test_data is not None and 'tests' in test_data:
            full_tests_json = {'tests': test_data["tests"]}
            self.send_json_to_arduino(full_tests_json)  # send the data to arduino
            # log and print status
            logger.info(f'Sending full tests data with {len(test_data["tests"])} tests')
        else:
            # handle case when no test data is found
            logger.warning('no test data found on file')

    # set temp & duration from the gui
    def set_temp(self, input_dictionary):
        if input_dictionary is not None:
            logger.info(input_dictionary)
            data = input_dictionary[0]
            set_temp_data = commands.set_temp(data)
            self.send_json_to_arduino(set_temp_data)
        else:
            logger.warning('nothing to set the t-chamber to')

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
        stop = commands.emergency_stop()
        logger.info('emergency stop should be sending now')
        self.send_json_to_arduino(stop)
        logger.info('emergency stop issued')
        message = 'EMERGENCY STOP'
        self.update_listbox.emit(message)
