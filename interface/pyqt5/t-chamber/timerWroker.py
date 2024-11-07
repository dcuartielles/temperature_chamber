from PyQt5.QtCore import QThread, pyqtSignal
import time
from logger_config import setup_logger

logger = setup_logger(__name__)


class TimerWorker(QThread):
    timeout = pyqtSignal()  # signal to emit at each interval

    def __init__(self, interval=None, parent=None):
        super(TimerWorker, self).__init__(parent)
        self.interval = interval  # interval in seconds
        self.running = True

    def run(self):
        try:
            while self.running:
                time.sleep(self.interval)
                self.timeout.emit()
        except Exception as e:
            logger.exception(f"here's why: {e}")

    def stop(self):
        self.running = False

