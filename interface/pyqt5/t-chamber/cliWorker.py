import logging
from threading import Semaphore
from PyQt5.QtCore import QObject, pyqtSignal
import arduinoUtils
import time


class CliWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, port, sketch_path, semaphore):
        super().__init__()
        self.port = port
        self.sketch_path = sketch_path
        self.semaphore = semaphore

    def run(self):
        logging.info('cli worker starting')
        self.semaphore.acquire()

        try:
            if arduinoUtils.handle_board_and_upload(port=self.port, sketch_path=self.sketch_path):
                print('cli code is running')
                logging.info('cli code is running')
            else:
                logging.error('cli process encountered an issue')
        except Exception as e:
            logging.error(f'error in cli worker: {e}')
            print(f'error in cli worker: {e}')
        finally:
            logging.info('cli worker releasing the semaphore')
            print('cli worker releasing the semaphore')
            self.semaphore.release()
            self.finished.emit()
