import threading
from PyQt5.QtCore import QObject, pyqtSignal
import arduinoUtils


class CliWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, port, sketch_path):
        super().__init__()
        self.port = port
        self.sketch_path = sketch_path

    def run(self):
        arduinoUtils.handle_board_and_upload(port=self.port, sketch_path=self.sketch_path)
        self.finished.emit()
