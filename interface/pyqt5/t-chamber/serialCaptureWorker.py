from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import json
import logging
# from jsonFunctionality import FileHandler

class SerialCaptureWorker(QThread):
    update_listbox = pyqtSignal(str)  # signal to update listbox
    update_chamber_monitor = pyqtSignal(str)  # signal to update chamber monitor

    def __init__(self, port, baudrate, timeout=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
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

    # method to run the thread
    def run(self):
        while self.is_running:
            if not self.is_stopped:
                if self.ser and self.ser.is_open:
                    logging.info('serial capture thread is running')
                    print('serial capture thread is running')
                    # read incoming serial data
                    response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                    if response:
                        self.process_response(response)

                    if time.time() - self.last_command_time > 1.5:
                        self.last_command_time = time.time()
                        self.trigger_read_data()
            time.sleep(0.1)  # avoid excessive cpu usage

    # pause flag for stopping communication temporarily when test board thread is dealing with cli
    def pause(self):
        self.is_stopped = True
        print('serial capture worker is paused')

    def resume(self):
        self.is_stopped = False
        self.last_command_time = time.time()  # reset the timing
        print('resuming serial capture worker')

    # sends a command to arduino via serial
    def send_command(self, command):
        try:
            if self.ser and self.ser.is_open:
                self.ser.reset_input_buffer()  # clear the gates
                self.ser.write((command + '\n').encode('utf-8'))  # encode command in serial
                logging.info(f'sent command: {command}')
                time.sleep(0.01)  # small delay for command processing
            else:
                logging.warning('serial capture connection is not open')
                print('serial capture connection is not open')

        except serial.SerialException as e:
            logging.error(f'error sending command: {e}')
        except Exception as e:
            logging.warning(f'unexpected error: {e}')

    # senf json to arduino
    def send_json_to_arduino(self, test_data):
        json_data = json.dumps(test_data)  # convert python dictionary to json
        try:
            if self.ser and self.ser.is_open:
                self.ser.write((json_data + '\n').encode('utf-8'))
                time.sleep(0.01)
                logging.info(f'sent to arduino: {json_data}')

                # continuously read arduino output (blocking method, runs inside the thread)
                while self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    logging.info(f'arduino says: {response}')
            else:
                logging.warning('serial capture communication is not open')
                print('serial capture communication is not open')
        except serial.SerialException as e:
            logging.error(f'error sending JSON: {e}')

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            logging.info(f'connection to {self.port} closed')
        self.quit()
        self.wait()

    # read data
    def read_data(self):
        if not self.is_stopped and self.ser and self.ser.is_open:
            try:
                self.send_command('SHOW DATA')
                response = self.ser.readline().decode('utf-8').strip()

                if response:
                    logging.info(f'arduino says: {response}')
                    return response
                else:
                    logging.info('there was nothing worth saying here')
                    return None
            except serial.SerialException as e:
                logging.error(f'error reading data: {e}')
                return None
        else:
            logging.warning('serial capture communication is closed or stopped')
            print('serial capture communication is closed or stopped')
            return None

    # run the entire test file
    def run_all_tests(self, test_data):
        if test_data is not None:
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:

                test = test_data.get(test_key, {})
                chamber_sequences = test.get('chamber_sequences', [])  # get temp & duration sequences

                if chamber_sequences:  # if the test data is available
                    for sequence in chamber_sequences:
                        self.send_json_to_arduino(sequence)  # send the data to arduino
                        # print status and update the listbox
                        logging.info(f'running {sequence}')
                else:
                    logging.warning(f'{chamber_sequences} not found')

        else:
            # handle case when no test data is found
            logging.warning('no test data found on file')

    # run custom only
    def run_custom(self, test_data):
        if test_data is not None:
            custom_test = test_data.get('custom', [])
            if custom_test:
                self.send_json_to_arduino(custom_test)
                logging.info(f'running {custom_test}')
            else:
                logging.info('no custom test found')
        else:
            logging.info('no such test on file')

    # set temp & duration from the gui
    def set_temp(self, input_dictionary):
        if input_dictionary is not None:
            logging.info(input_dictionary)
            self.send_json_to_arduino(input_dictionary)
        else:
            logging.warning('nothing to set the t-chamber to')

    def trigger_read_data(self):
        response = self.read_data()  # read data using custom method
        if response:
            self.update_chamber_monitor.emit(response)  # emit signal to update the chamber monitor

    # process serial response
    def process_response(self, response):
        # list of responses to be picked up
        trigger_responses = ['Setting', 'Running', 'Test complete', 'Target temp', 'Sequence complete']
        if any(response.strip().startswith(trigger) for trigger in trigger_responses):
            self.update_listbox.emit(response)  # emit signal to update listbox

    # emergency stop
    def emergency_stop(self):
        self.is_stopped = True  # set flag to stop the read_data loop
        self.send_command('EMERGENCY STOP')
        logging.info('emergency stop issued')
