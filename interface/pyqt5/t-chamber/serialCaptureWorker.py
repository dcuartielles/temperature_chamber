from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import json
from logger_config import setup_logger
import commands
from datetime import datetime
from queue import Queue

logger = setup_logger(__name__)


class SerialCaptureWorker(QThread):

    update_chamber_monitor = pyqtSignal(dict)  # signal to update chamber monitor
    trigger_run_tests = pyqtSignal(dict)  # signal from main to run tests
    trigger_reset = pyqtSignal()  # signal form main to reset control board
    update_listbox = pyqtSignal(str)  # signal to update listbox
    trigger_emergency_stop = pyqtSignal()
    machine_state_signal = pyqtSignal(str)
    ping_timestamp_signal = pyqtSignal(str)
    # signals to main to update running test info
    update_test_label_signal = pyqtSignal(dict)
    no_port_connection = pyqtSignal()
    serial_running_and_happy = pyqtSignal()
    next_sequence_progress = pyqtSignal()
    sequence_complete = pyqtSignal(str)
    test_number_signal = pyqtSignal(int)
    # signal to main to trigger sketch uploads for each new test
    upload_sketch_again_signal = pyqtSignal(str, int)

    def __init__(self, port, baudrate, timeout=5):
        super().__init__()
        # serial setup variables
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.ser = None  # future serial connection object
        self.is_open = True
        self.is_running = True  # flag to keep the thread running
        self.is_stopped = False  # flag to stop the read loop

        # timing setup to control thread flow and communication with control board
        self.last_ping = time.time()
        self.last_readout = time.time()

        # connect signals from main
        self.trigger_run_tests.connect(self.run_all_tests)
        self.trigger_reset.connect(self.reset_control_board)
        self.trigger_emergency_stop.connect(self.emergency_stop)

        # flag to prevent test sequence segments to advance too fast
        self.sequence_has_been_advanced = False

        # class variables
        self.test_data = None
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
        self.test_number = 0
        # set up que for processing responses from serial
        self.response_queue = Queue()

    # CORE THREAD METHODS
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

    # main method to run the thread
    def run(self):
        if not self.serial_setup():
            logger.error(f'failed to connect to {self.port}')
            self.no_port_connection.emit()
            return
        logger.info('thread is running')
        # wrap the whole while-loop in a try-except statement to prevent crashes in case of system failure
        try:
            while self.is_running:
                if not self.is_stopped:
                    try:
                        if self.ser and self.ser.is_open:
                            self.serial_running_and_happy.emit()
                            # send handshake
                            self.handshake()
                            time.sleep(0.1)
                            # read incoming serial data
                            response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                            if response:
                                self.process_response(response)  # update and show curated responses

                            # make sure responses added to que by send_json be processed as well
                            if not self.response_queue.empty():
                                response = self.response_queue.get()
                                self.process_response(response)

                            if time.time() - self.last_ping >= 0.5:
                                self.last_ping = time.time()
                                self.trigger_ping()

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
            logger.info(f'connection to {self.port} closed')
        self.quit()
        self.wait()

    # BASIC COMMUNICATION WITH CONTROL BOARD
    # handshake
    def handshake(self):
        logger.info(f"attempting handshake, sent_handshake: {self.sent_handshake}")
        if not self.sent_handshake:
            time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            # insert timestamp into handshake
            handshake = commands.handshake(time)
            logger.info(f'sending handshake: {handshake}')
            # send handshake to arduino
            self.send_json_to_arduino(handshake)
            logger.info(f'handshake sent to arduino: {handshake}')

            try:
                # decode arduino response
                handshake_response = self.ser.readline().decode('utf-8').strip()
                # convert response string to dictionary
                parsed_response = json.loads(handshake_response)
                logger.info(parsed_response)
            except json.JSONDecodeError:
                logger.exception('failed to parse arduino response')

            # prevent handshake from being sent again
            self.sent_handshake = True

    # trigger ping
    def trigger_ping(self):
        self.ping()

    # ping
    def ping(self):
        logger.info(f'test number: {self.test_number}')
        ping = commands.ping()  # create ping command
        self.send_json_to_arduino(ping)  # send ping to arduino
        try:
            ping_response = self.ser.readline().decode('utf-8').strip()
            # convert response string to dictionary
            parsed_response = json.loads(ping_response)
            if 'ping_response' in parsed_response:
                ping_data = parsed_response['ping_response']
                # get all the data from ping & store it in class variables
                self.alive = ping_data.get('alive', False)
                logger.info(self.alive)
                self.timestamp = ping_data.get('timestamp', '')
                self.ping_timestamp_signal.emit(self.timestamp)
                self.machine_state = ping_data.get('machine_state', '')
                logger.info(self.machine_state)
                self.machine_state_signal.emit(self.machine_state)
                # extract test status information and emit signals for gui updates
                self.current_temperature = ping_data.get('current_temp', 0)
                test_status = ping_data.get('test_status', {})
                self.is_test_running = test_status.get('is_test_running', False)
                self.current_test = test_status.get('current_test', '')
                self.current_sequence = test_status.get('current_sequence', 0)
                self.desired_temp = test_status.get('desired_temp', 0)
                # get duration and time left, and convert them for display
                self.current_duration = test_status.get('current_duration', 0) / 60000
                self.time_left = test_status.get('time_left', 0) / 60
                self.emit_test_status()
                self.display_info()
        except json.JSONDecodeError:
            logger.exception('failed to decode ping response as json')

    # MORE ADVANCED COMMUNICATION WITH TEST BOARD
    # run the entire test file
    def run_all_tests(self, test_data):
        self.test_number = 0
        if test_data is not None and 'tests' in test_data:
            full_tests_json = {'tests': test_data["tests"]}
            self.send_json_to_arduino(full_tests_json)  # send the data to arduino
            # log and print status
            logger.info(f'sending full tests data with {len(test_data["tests"])} tests')
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

    # reset test board
    def reset_control_board(self):
        reset = commands.reset()
        self.send_json_to_arduino(reset)
        logger.info('resetting control board')

    # emergency stop
    def emergency_stop(self):
        stop = commands.emergency_stop()
        logger.info('emergency stop should be sending now')
        self.send_json_to_arduino(stop)
        logger.info('emergency stop issued')

    # SENDING STUFF TO MAIN APP
    # prep running test info updates to be emitted
    def emit_test_status(self):
        test_status_data = {
            'test': self.current_test,
            'sequence': self.current_sequence,
            'time_left': self.time_left,
            'current_duration': self.current_duration
        }
        self.update_test_label_signal.emit(test_status_data)

    # extract relevant info for display in serial monitor
    def display_info(self):
        relevant_info = {
            'current_temp': self.current_temperature,
            'desired_temp': self.desired_temp,
            'machine_state': self.machine_state
        }
        self.update_chamber_monitor.emit(relevant_info)

    # DECODING AND ENCODING TOOLS
    # senf json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert python dictionary to json
        try:
            if self.ser and self.ser.is_open:
                self.ser.write((json_data + '\n').encode('utf-8'))
                time.sleep(0.01)
                logger.info(f'sent to arduino: {json_data}')
                # blocking method within thread
                while self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    logger.info(f'arduino says: {response}')
                    # capture all serial responses for thread to process properly
                    self.response_queue.put(response)
            else:
                logger.warning('serial not open')
        except serial.SerialException as e:
            logger.error(f'error sending JSON: {e}')

    # process serial response
    def process_response(self, response):
        logger.debug(f"raw response: {repr(response)}")
        clean_response = response.strip()  # remove leading/trailing whitespace
        logger.debug(f"cleaned response: {repr(clean_response)}")

        # list of responses to be picked up
        trigger_responses = ['Setting', 'Target temperature reached!']
        if any(response.strip().startswith(trigger) for trigger in trigger_responses):
            self.update_listbox.emit(response)  # emit signal to update listbox
            logger.info(f'{response}')
        elif 'Test complete' in response.strip():
            logger.info(f'arduino says {response}, sending signal to upload sketch for new test')
            self.test_number += 1
            logger.info(f'test number: {self.test_number}')
            self.test_number_signal.emit(self.test_number)
            message = f'test {self.test_number} complete'
            self.upload_sketch_again_signal.emit(message, self.test_number)
        elif response.strip().startswith('Waiting'):
            self.sequence_has_been_advanced = False
            self.update_listbox.emit(response)  # emit signal to update listbox
            logger.info(f'{response}')
        elif response.strip().startswith('Sequence complete'):
            if not self.sequence_has_been_advanced:
                self.next_sequence_progress.emit()
                logger.info('sending signal to start new sequence progress bar')
                self.sequence_complete.emit('sequence complete')
                self.sequence_has_been_advanced = True
        else:
            logger.info(f'complete response from arduino: {response}')
