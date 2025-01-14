from PyQt5.QtCore import QThread, pyqtSignal
import time
import serial
import json
from logger_config import setup_logger
import commands
from datetime import datetime
from queue import Queue

logger = setup_logger(__name__)


class WifiWorker(QThread):

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
        self.last_command_time = time.time()
        # test number (index, actually) for checking exp output correctly

    # set up serial communication
    def serial_setup(self, port=None, baudrate=None):
        if port:
            self.port = port  # allow dynamic port change
        if baudrate:
            self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f'Wifi worker connected to arduino port: {self.port}')
            time.sleep(1)  # make sure arduino is ready
            return True
        except serial.SerialException as e:
            logger.exception(f'Error during serial setup of Wifi worker: {e}')
            return False

    # main operating method for serial response readout
    def run(self):
        if not self.serial_setup():
            logger.error(f'Wifi worker failed to connect to {self.port}')
            return
        logger.info('Wifi thread is running')
        # wrap the whole while-loop in a try-except statement to prevent crashes in case of system failure
        try:
            while self.is_running:
                if self.is_stopped:
                    time.sleep(0.1)
                    continue
                try:
                    if not self.ser or not self.ser.is_open:
                        time.sleep(0.1)
                        continue
                    logger.debug('Wifi worker says hello')
                    # continuous readout from serial
                    response = self.ser.readline().decode('utf-8').strip()
                    if response:
                        self.show_response(response)
                    if time.time() - self.last_command_time > 5:
                        self.last_command_time = time.time()
                        logger.info('Wifi thread is running')
                except serial.SerialException as e:
                    logger.exception(f'Serial error in Wifi worker thread: {e}')
                    self.is_running = False
                time.sleep(0.1)  # avoid excessive cpu usage
        except Exception as e:
            # catch any other unexpected exceptions
            logger.exception(f'Unexpected error in Wifi worker thread: {e}')
            self.is_running = False

        self.stop()

    # method to stop the serial communication

    def stop(self):
        self.is_running = False  # stop the worker thread loop
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()  # close the serial connection
                logger.info(f'Connection to {self.port} closed now')
        except Exception as e:
            logger.error(f'Failed to close the connection to {self.port}: {e}')
        finally:
            self.quit()
            self.wait()


    # show serial response
    def show_response(self, response):
        if response:
            printout = f'{response}'
            logger.info(printout)
