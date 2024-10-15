from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import arduinoUtils
# from jsonFunctionality import FileHandler

class TestBoardWorker(QThread):
    update_upper_listbox = pyqtSignal(str)  # signal to update instruction listbox

    def __init__(self, port, baudrate=9600, timeout=5):
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
            print(f'connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            print(f'error: {e}')
            return False


    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            print(f'connection to {self.port} closed')
        self.quit()
        self.wait()

    # run the entire test file REFACTOR FOR CLI
    def run_all_tests(self, test_data, selected_t_port):
        if test_data is not None and selected_t_port is not None:  # take test_data & port number from main
            all_tests = [key for key in test_data.keys()]
            # iterate through each test and run it
            for test_key in all_tests:

                test = test_data.get(test_key, {})
                sketch_path = test.get('sketch', "")  # get .ino file path

                if sketch_path:  # if the test data is available
                    arduinoUtils.upload_sketch(board_type=None, port=selected_t_port, sketch_path=sketch_path)
                else:
                    print('file path not found')

        else:
            # handle case when no test data is found
            print('can\'t do it')

    # serial response readout
    def run(self):
        print('thread is running')
        while self.is_running:
            if self.ser and self.ser.is_open:
                # read incoming serial data
                response = self.ser.readline().decode('utf-8').strip()  # continuous readout from serial
                if response:
                    self.show_response(response)
            time.sleep(0.1)  # avoid excessive cpu usage

    # show serial response
    def show_response(self, response):
        if response:
            self.update_upper_listbox.emit(response)  # emit signal to update listbox
