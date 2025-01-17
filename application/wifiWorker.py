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
        # Ensure the serial setup is successful before entering the loop
        if not self.serial_setup():
            logger.error(f"WiFi worker failed to connect to port: {self.port}")
            return

        logger.info("WiFi worker thread started.")
        try:
            while self.is_running:  # Main thread loop
                if self.is_stopped:
                    logger.debug("WiFi worker is stopped. Waiting...")
                    time.sleep(0.1)  # Small delay to avoid excessive CPU usage
                    continue

                # Check if the serial connection is still valid
                if not self.ser or not self.ser.is_open:
                    logger.warning(f"WiFi worker lost connection to port: {self.port}")
                    self.stop()  # Gracefully stop the worker
                    break

                try:
                    # Read data from the serial port
                    response = self.ser.readline().decode('utf-8').strip()
                    if response:
                        self.show_response(response)  # Process and display the response

                    # Send periodic logs or actions to keep track of activity
                    if time.time() - self.last_command_time > 5:
                        self.last_command_time = time.time()
                        logger.info("WiFi worker thread is running smoothly.")

                except serial.SerialException as e:
                    logger.exception(f"Serial exception in WiFi worker: {e}")
                    self.is_running = False  # Exit the main loop

                time.sleep(0.1)  # Avoid excessive CPU usage

        except Exception as e:
            logger.exception(f"Unexpected exception in WiFi worker: {e}")
            self.is_running = False  # Stop the worker on unexpected error

        finally:
            self.stop()  # Ensure resources are released when exiting the thread

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
                logger.info("Wifi Worker thread exited successfully.")
            except Exception as e:
                logger.error(f"Error during thread termination: {e}")


    # show serial response
    def show_response(self, response):
        if response:
            printout = f'{response}'
            logger.info(printout)
