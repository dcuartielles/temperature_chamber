import logging
from threading import Lock
from PyQt5.QtCore import QObject, pyqtSignal
import subprocess
import json


class CliWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, port, sketch_path):
        super().__init__()
        self.port = port
        self.sketch_path = sketch_path
        self.lock = Lock()

    def run(self):
        logging.info('cli worker starting')
        with self.lock:
            try:
                if self.handle_board_and_upload(port=self.port, sketch_path=self.sketch_path):
                    print('cli code is running')
                    logging.info('cli code is running')
                else:
                    logging.error('cli process encountered an issue')
            except Exception as e:
                logging.error(f'error in cli worker: {e}')
                print(f'error in cli worker: {e}')

    def run_cli_command(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f'command succeeded: {" ".join(command)}')
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.info(f'command failed: {e.stderr}')
            return None

    def get_arduino_boards(self):
        command = ["arduino-cli", "board", "list", "--format", "json"]
        output = self.run_cli_command(command)

        if output:
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
                logging.info('error parsing arduino-cli board list output')
                return []
        return []

    def detect_board(self, port):
        command = ["arduino-cli", "board", "list", "--format", "json"]
        output = self.run_cli_command(command)

        if output:
            boards_info = json.loads(output)
            for board in boards_info.get("detected_ports", []):
                if board["port"]["address"] == port:
                    if "matching_boards" in board and board["matching_boards"]:
                        fqbn = board["matching_boards"][0].get("fqbn", None)
                        if fqbn:
                            logging.info(f'detected fqbn: {fqbn}')
                            return fqbn
                        else:
                            logging.warning(f'no fqbn found for board on port {port}')
                            return None
        return None

    def is_core_installed(self, fqbn):
        core_name = fqbn.split(":")[0]
        command = ["arduino-cli", "core", "list"]
        output = self.run_cli_command(command)

        if output:
            installed_cores = output.splitlines()
            for core in installed_cores:
                if core_name in core:
                    logging.info(f'core {core_name} is already installed.')
                    return True
        return False

    def install_core_if_needed(self, fqbn):
        core_name = fqbn.split(":")[0]
        if not self.is_core_installed(fqbn):
            logging.info(f'core {core_name} not installed. installing...')
            command = ["arduino-cli", "core", "install", core_name]
            self.run_cli_command(command)
        else:
            logging.info(f'core {core_name} is already installed.')

    def compile_sketch(self, fqbn, sketch_path):
        logging.info(f'compiling {sketch_path} for the board with fqbn {fqbn}...')
        command = [
            "arduino-cli", "compile",
            "--fqbn", fqbn,
            sketch_path
        ]
        result = self.run_cli_command(command)
        if result:
            logging.info('compilation successful!')
            return True
        else:
            logging.warning('compilation failed')
            return False

    def upload_sketch(self, fqbn, port, sketch_path):
        logging.info(f'uploading {sketch_path} to board with fqbn {fqbn} on port {port}...')
        command = [
            "arduino-cli", "upload",
            "-p", port,
            "--fqbn", fqbn,
            sketch_path
        ]
        result = self.run_cli_command(command)
        if result:
            logging.info('upload successful!')
            return True
        else:
            logging.warning('upload failed!')
            return False

    def handle_board_and_upload(self, port, sketch_path):
        fqbn = self.detect_board(port)
        if fqbn:
            self.install_core_if_needed(fqbn)

            if self.compile_sketch(fqbn, sketch_path):
                if self.upload_sketch(fqbn, port, sketch_path):
                    self.finished.emit()
                    return True
                else:
                    logging.error('upload failed')
                    print('upload failed')
                    return False
            else:
                logging.error('aborting upload due to compilation failure.')
        else:
            logging.warning(f'failed to detect board on port {port}.')
        return False
