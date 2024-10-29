from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import json
import time
import serial
from logger_config import setup_logger

logger = setup_logger(__name__)


class CliWorker(QThread):

    finished = pyqtSignal()
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
        self.last_command_time = time.time()
        self.is_uploading = False
        self.is_compiling = False
        self.is_detecting = False
        self.checking_core = False
        self.core_installed = False
        self.boards_are_there = False
        self.test_data = None
        self.filepath = None

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f'cli worker connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            logger.error(f'error: {e}')
            return False

    def run(self):
        if not self.serial_setup():
            logger.error(f'cli worker failed to connect to {self.port}')
            return
        logger.info('cli worker thread is running')

        while self.is_running:
            if not self.is_stopped:
                self.run_all_tests(self.test_data, self.filepath)
                try:
                    if not self.is_stopped and self.ser and self.ser.is_open:
                        if time.time() - self.last_command_time > 5:
                            self.last_command_time = time.time()

                except serial.SerialException as e:
                    logger.exception(f'serial error in cli: {e}')
                    bye = f'serial error in cli worker: {str(e)}'
                    self.wave(bye)
                    self.is_running = False
                    break

            time.sleep(0.1)
        self.stop()

    def set_test_data(self, test_data, filepath):
        self.test_data = test_data
        self.filepath = filepath

    def wave(self, hello):
        if hello:
            self.update_upper_listbox.emit(hello)

    # method to stop the serial communication
    def stop(self):
        self.is_running = False  # stop the worker thread loop
        if self.ser and self.ser.is_open:
            self.ser.close()  # close the serial connection
            logger.info(f'connection to {self.port} closed now')
        self.quit()
        self.wait()

    @staticmethod
    def run_cli_command(command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logger.info(f'command succeeded: {" ".join(command)}')

            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.info(f'command failed: {e.stderr}')
            return None

    def get_arduino_boards(self):
        if self.boards_are_there:
            logger.warning('boards are already detected, moving on')
            return

        command = ["arduino-cli", "board", "list", "--format", "json"]
        output = self.run_cli_command(command)

        if output:
            self.boards_are_there = True
            try:
                boards_info = json.loads(output)
                arduino_ports = []

                for board in boards_info.get("detected_ports", []):
                    if "matching_boards" in board and board["matching_boards"]:
                        port = board.get("port", {}).get("address", "unknown port")
                        board_name = board["matching_boards"][0].get("name", "unknown board")
                        arduino_ports.append((port, board_name))
                return arduino_ports
            except json.JSONDecodeError:
                logger.info('error parsing arduino-cli board list output')
                return []
        return []

    def detect_board(self, port):
        if self.is_detecting:
            logger.warning('boards already detected: skipping new detect request')
            return

        command = ["arduino-cli", "board", "list", "--format", "json"]
        output = self.run_cli_command(command)

        if output:
            headsup = 'detecting test board'
            self.wave(headsup)
            boards_info = json.loads(output)
            for board in boards_info.get("detected_ports", []):
                if board["port"]["address"] == port:
                    if "matching_boards" in board and board["matching_boards"]:
                        fqbn = board["matching_boards"][0].get("fqbn", None)
                        if fqbn:
                            self.is_detecting = True
                            logger.info(f'detected fqbn: {fqbn}')
                            return fqbn
                        else:
                            logger.warning(f'no fqbn found for board on port {port}')
                            return None
        return None

    def is_core_installed(self, fqbn):
        if self.checking_core:
            logger.warning('checking core already: skipping new check core request')
            return

        core_name = fqbn.split(":")[0]
        command = ["arduino-cli", "core", "list"]
        output = self.run_cli_command(command)

        if output:
            self.checking_core = True
            installed_cores = output.splitlines()
            for core in installed_cores:
                if core_name in core:
                    logger.info(f'core {core_name} is already installed.')
                    return True
        return False

    def install_core_if_needed(self, fqbn):
        if self.core_installed:
            logger.warning('core already installed: skipping new core install request')
            return

        core_name = fqbn.split(":")[0]

        if not self.is_core_installed(fqbn):
            self.core_installed = True
            logger.info(f'core {core_name} not installed. installing...')
            update = 'installing core on test board'
            self.wave(update)
            command = ["arduino-cli", "core", "install", core_name]
            self.run_cli_command(command)

    def compile_sketch(self, fqbn, sketch_path):
        if self.is_compiling:
            logger.warning('compiling already: skipping new compile request')
            return

        logger.info(f'compiling sketch for the board with fqbn {fqbn}...')
        headsup = 'compiling sketch for test board'
        self.wave(headsup)
        command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
        ]
        result = self.run_cli_command(command)
        if result:
            self.is_compiling = True
            logger.info('compilation successful!')
            yes = 'compilation successful!'
            self.wave(yes)
            time.sleep(0.5)
            return True
        else:
            logger.warning('compilation failed')
            no = 'compilation failed'
            self.wave(no)
            time.sleep(0.5)
            return False

    def upload_sketch(self, fqbn, port, sketch_path):
        if self.is_uploading:
            logger.warning('uploading already: skipping new upload request')
            return

        logger.info(f'uploading sketch to board with fqbn {fqbn} on port {port}...')
        uploading = 'uploading sketch on test board'
        self.wave(uploading)
        time.sleep(0.5)

        command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
        ]
        try:
            if self.ser and not self.is_stopped:
                self.ser.close()

                result = self.run_cli_command(command)

                if result:
                    self.is_uploading = True
                    logger.info('upload successful!')
                    bye = 'upload successful!'
                    self.wave(bye)
                    time.sleep(2.5)
                    self.finished.emit()
                    return True
                else:
                    logger.warning('upload failed!')
                    bye = 'upload failed!'
                    self.wave(bye)

                    self.finished.emit()
                    return False
            else:
                logger.warning(f'cli worker port connection to {port} seems to fail')
                self.finished.emit()

        except serial.SerialException as e:
            logger.error(f'serial error on cli thread during upload: {e}')
            error = f'serial error on cli thread during upload: {str(e)}'
            self.wave(error)
            self.finished.emit()

    def handle_board_and_upload(self, port, sketch_path):
        fqbn = self.detect_board(port)
        if fqbn:
            self.install_core_if_needed(fqbn)
            if self.compile_sketch(fqbn, sketch_path):
                self.upload_sketch(fqbn, port, sketch_path)
                return True
            else:
                logger.error('aborting upload due to compilation failure.')
        else:
            logger.warning(f'failed to detect board on port {port}.')
        return False

    # run the entire test file
    def run_all_tests(self, test_data, filepath):
        if test_data and filepath:  # take test_data & port number from main
            logger.info(f'running test with testdata filepath: {filepath}')
            test_data_filepath = filepath.rsplit('/', 1)[0]
            all_tests = [key for key in test_data.keys()]

            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data.get(test_key, {})
                sketch_path = test.get('sketch', '')  # get .ino file path

                if sketch_path:  # if the sketch is available
                    sketch_filename = sketch_path.split('/')[-1]  # get ino file name
                    sketch_full_path = test_data_filepath + '/' + sketch_filename
                    self.handle_board_and_upload(port=self.port, sketch_path=sketch_full_path)

                else:
                    logger.warning('sketch path not found')
        else:
            # handle case when no test data is found
            logger.info('can\'t do it')

'''
    def reset_arduino(self):
        if self.ser:
            try:
                self.ser.setDTR(False)  # reset arduino by setting str to False
                time.sleep(0.5)  # time to reset
                self.ser.setDTR(True)  # re-enable dtr
                logger.info(f'arduino on {self.port} reset successfully')
                reset = 'test board reset successfully'
                self.wave(reset)
                time.sleep(0.5)

            except serial.SerialException as e:
                logger.exception(f'failed to reset arduino on {self.port}: {e}')'''
