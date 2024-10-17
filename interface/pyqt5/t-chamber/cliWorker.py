import logging
from threading import Lock
from PyQt5.QtCore import QObject, pyqtSignal
import arduinoUtils


class CliWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, port, sketch_path):
        super().__init__()
        self.port = port
        self.sketch_path = sketch_path
        self.lock = Lock()

    def run(self):
        with self.lock:
            try:
                arduinoUtils.handle_board_and_upload(port=self.port, sketch_path=self.sketch_path)
                print('cli code is running')
            except Exception as e:
                logging.error(f'error in cli worker: {e}')
                print(f'error in cli worker: {e}')
            finally:
                self.finished.emit()
