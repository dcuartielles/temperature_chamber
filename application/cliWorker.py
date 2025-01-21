from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import subprocess
import json
import time
import serial
from threading import Lock
import threading
from logger_config import setup_logger

logger = setup_logger(__name__)

cli_lock = Lock()


class CliWorker(QThread):

    finished = pyqtSignal()  # signal to main when the thread's work is done
    update_upper_listbox = pyqtSignal(str)  # signal to update instruction listbox
    set_test_data_signal = pyqtSignal(dict, str, int)

    def __init__(self, port, baudrate, timeout=5):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None  # future serial connection object
        self.is_open = True
        self.is_running = True  # flag to keep the thread running
        self.is_stopped = False  # flag to stop the read loop
        # flags preventing each and every one operation from running twice and interrupting the work
        self.is_uploading = False
        self.is_compiling = False
        self.is_detecting = False
        self.checking_core = False
        self.core_installed = False
        self.boards_are_there = False
        # class variables
        self.test_data = None
        self.filepath = None
        # test number (index, actually) for correct upload
        self.test_number = 0
        # connect signal from main to update test data
        self.set_test_data_signal.connect(self.set_test_data)

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f'CLI worker connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            logger.error(f'Error: {e}')
            return False

    # core run method
    def run(self):
        if not self.serial_setup():
            logger.error(f'CLI worker failed to connect to {self.port}')
            return
        logger.info('CLI worker thread is running')
        # wrap the whole while-loop in a try-except statement to prevent crashes in case of system failure
        try:
            while self.is_running and not self.is_stopped:
                try:
                    # this worker thread's only task is to correctly upload a test sketch onto test board
                    self.run_all_tests(self.test_data, self.filepath)
                except serial.SerialException as e:
                    logger.exception(f'Serial error in CLI worker thread: {e}')
                    bye = f'serial error in CLI worker thread: {str(e)}'
                    self.wave(bye)
                    self.is_running = False
                    break
                time.sleep(0.1)  # prevent jamming
        except Exception as e:
            # catch any other unexpected exceptions
            logger.exception(f'Unexpected error: {e}')
            self.is_running = False

        self.stop()

    # assign test file and file path to class variables
    def set_test_data(self, test_data, filepath, test_number):
        self.test_data = test_data
        self.filepath = filepath
        self.test_number = test_number

    # emit message (via signal) to be displayed in main
    def wave(self, hello):
        if hello:
            self.update_upper_listbox.emit(hello)

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # Stop the worker thread loop
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()  # Close the serial connection
                logger.info(f"Connection to {self.port} closed successfully.")
        except serial.SerialException as e:
            logger.error(f"Serial exception while closing connection to {self.port}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while closing connection to {self.port}: {e}")
        finally:
            try:
                self.quit()  # Gracefully terminate the thread
                self.wait()  # Ensure thread termination before cleanup
                logger.info("CLI Worker thread exited successfully.")
            except Exception as e:
                logger.error(f"Error during thread termination: {e}")

    # static method for running cli commands
    @staticmethod
    def run_cli_command(command):
        with cli_lock:
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                logger.info(f'[{threading.current_thread().name}] Command succeeded: {" ".join(command)}')

                return result.stdout
            except subprocess.CalledProcessError as e:
                logger.info(f'Command failed: {e.stderr}')
                return None

    # detect test board
    def detect_board(self, port):
        if self.is_detecting:
            logger.warning('Boards already detected: skipping new detect request')
            return

        command = ["arduino-cli", "board", "list", "--format", "json"]
        output = self.run_cli_command(command)

        if not output:
            return None

        headsup = 'detecting test board'
        self.wave(headsup)
        boards_info = json.loads(output)
        for board in boards_info.get("detected_ports", []):
            if board["port"]["address"] != port:
                return None
            if "matching_boards" in board and board["matching_boards"]:
                fqbn = board["matching_boards"][0].get("fqbn", None)
                if fqbn:
                    self.is_detecting = True
                    logger.info(f'Detected fqbn: {fqbn}')
                    return fqbn
                logger.warning(f'No fqbn found for board on port {port}')
                return None

    # check if core is installed on test board
    def is_core_installed(self, fqbn):
        if self.checking_core:
            logger.warning('Checking core already: skipping new check core request')
            return

        core_name = fqbn.split(":")[0]
        command = ["arduino-cli", "core", "list"]
        output = self.run_cli_command(command)

        if not output:
            return False

        self.checking_core = True
        installed_cores = output.splitlines()
        for core in installed_cores:
            if core_name in core:
                logger.info(f'Core {core_name} is already installed.')
                return True

    # install core on test board, if necessary
    def install_core_if_needed(self, fqbn):
        if self.core_installed:
            logger.warning('Core already installed: skipping new core install request')
            return

        core_name = fqbn.split(":")[0]

        if not self.is_core_installed(fqbn):
            self.core_installed = True
            logger.info(f'Core {core_name} not installed. installing...')
            update = 'Installing core on test board'
            self.wave(update)
            command = ["arduino-cli", "core", "install", core_name]
            self.run_cli_command(command)

    # compile sketch before upload
    def compile_sketch(self, fqbn, sketch_path):
        if self.is_compiling:
            logger.warning('Compiling already: skipping new compile request')
            return

        logger.info(f'Compiling sketch for the board with fqbn {fqbn}...')
        headsup = 'Compiling sketch for test board'
        self.wave(headsup)
        command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
        ]
        result = self.run_cli_command(command)
        if result:
            self.is_compiling = True
            logger.info('Compilation successful!')
            yes = 'Compilation successful!'
            self.wave(yes)
            time.sleep(0.5)
            return True
        else:
            logger.warning('Compilation failed')
            no = 'Compilation failed'
            self.wave(no)
            time.sleep(0.5)
            return False

    # upload sketch on test board
    def upload_sketch(self, fqbn, port, sketch_path):
        if self.is_uploading:
            logger.warning('Uploading already: skipping new upload request')
            return

        logger.info(f'Uploading sketch to board with fqbn {fqbn} on port {port}...')
        uploading = 'Uploading sketch on test board'
        self.wave(uploading)
        time.sleep(0.5)

        command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
        ]
        try:
            if not self.ser or self.is_stopped:
                logger.warning(f'Serial connection stopped or missing on port: {port}')

            self.ser.close()
            result = self.run_cli_command(command)
            if result:
                self.is_uploading = True
                logger.info('Upload successful!')
                bye = 'Upload successful!'
                self.wave(bye)
                time.sleep(2)
                self.finished.emit()    # signal to main the cli worker's job is finished
                return True
            else:
                logger.warning('Upload failed!')
                bye = 'Upload failed!'
                self.wave(bye)
                self.finished.emit()    # signal to main the cli worker's job can't be completed
                return False

        except serial.SerialException as e:
            logger.error(f'Serial error on cli thread during upload: {e}')
            error = f'Serial error on cli thread during upload: {str(e)}'
            self.wave(error)
            self.finished.emit()    # signal to main the cli worker's job can't be completed

    # all-in method for handling sketch upload
    def handle_board_and_upload(self, port, sketch_path):
        fqbn = self.detect_board(port)
        if fqbn:
            self.install_core_if_needed(fqbn)
            if self.compile_sketch(fqbn, sketch_path):
                self.upload_sketch(fqbn, port, sketch_path)
                return True
            else:
                logger.error('Aborting upload due to compilation failure.')
        else:
            logger.warning(f'Failed to detect board on port: {port}')
        return False

    # run the entire test file
    def run_all_tests(self, test_data, filepath):
        if not test_data or not filepath:  # take test_data & file path from main
            # handle case when no test data is found
            logger.info("Could not run tests, missing test data or file path")

        logger.info(f'Running test with testdata filepath: {filepath}')
        # split file path in preparation for sketch file path recreation
        test_data_filepath = filepath.rsplit('/', 2)[0]
        logger.info(f'Test data filepath that will be processed further: {test_data_filepath}')
        if not 'tests' in test_data:
            logger.info("Couldn't find key 'tests' in test data")
            return None

        all_tests = [key for key in test_data['tests'].keys()]
        current_test_index = self.test_number
        if not current_test_index < len(all_tests):
            return None

        current_test_key = all_tests[current_test_index]
        test = self.test_data['tests'][current_test_key]
        logger.info(test)
        sketch_path = test.get('sketch', '')  # get .ino file path
        if sketch_path:  # if the sketch is available
            # Remove './' from the beginning of the sketch path if present
            if sketch_path.startswith('./'):
                sketch_path = sketch_path[2:]

            sketch_group_directory = sketch_path.split('/')[-3]  # get the overarching test group directory
            logger.info(f'Sketch group directory: {sketch_group_directory}')

            sketch_full_path = test_data_filepath + '/' + sketch_path
            logger.info(f'Full sketch path: {sketch_full_path}')
            self.handle_board_and_upload(port=self.port, sketch_path=sketch_full_path)
        else:
            logger.warning('Sketch path not found')




