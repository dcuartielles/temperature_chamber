# system and PyQt5 imports
import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTabWidget, QProgressBar
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from datetime import datetime, timedelta
from dateutil import parser
# functionality imports
from jsonFunctionality import FileHandler
from serialCaptureWorker import SerialCaptureWorker
from portSelector import PortSelector
from testBoardWorker import TestBoardWorker
from cliWorker import CliWorker
from wifiWorker import WifiWorker
from config import Config
from logger_config import setup_logger
from mainTab import MainTab
from manualTab import ManualTab
from progressBar import ProgressBar
from queueTab import QueueTab
import popups

# set up logger that takes the file name
logger = setup_logger(__name__)


# create window class
class MainWindow(QMainWindow):



    def __init__(self):
        super().__init__()

        logger.info('app started')

        # create an instance of config
        self.config = Config('config.json')

        # create an instance of json file handler
        self.json_handler = FileHandler(self.config)

        # create an instance of port selector
        self.port_selector = PortSelector(self.config)
        self.selected_c_port = None
        self.selected_t_port = None
        self.selected_t_wifi = None

        # prepare space for worker threads to appear later
        self.serial_worker = None
        self.test_board = None
        self.cli_worker = None
        self.wifi_worker = None

        # create a dictionary for setting temp & duration
        self.input_dictionary = []

        # space for test file accessible from worker threads
        self.test_data = None
        self.filepath = None
        # test number (index, actually) for correct upload and exp output check
        self.test_number = 0
        self.sequences_in_test = 0

        # class variables to keep updates from ping
        self.current_temperature = None
        self.machine_state = None
        self.timestamp = None

        # create qtimer instance: after 5 minutes of communication break with serial, control board is reset
        self.no_ping_timer = QTimer(self)
        self.no_ping_timer.timeout.connect(self.no_ping_for_five)  # connect to the method
        self.no_ping_timer.setInterval(5000)  # set interval in milliseconds
        self.no_ping_alert = False  # flag to only have the 5-min alert show once

        # create qtimer instance: if serial connection with control board is broken, warn
        self.connection_broken_timer = QTimer(self)
        self.connection_broken_timer.timeout.connect(self.no_serial_cable)
        self.connection_broken_timer.setInterval(5000)
        self.connection_broken_alert = False

        # create qtimer instance: if serial connection with test board is broken, warn
        self.test_broken_timer = QTimer(self)
        self.test_broken_timer.timeout.connect(self.no_test_cable)
        self.test_broken_timer.setInterval(60000)
        self.test_broken_alert = False

        # create a qtimer for emergency stop alert popup
        self.emergency_stop_popup_shown = False
        self.emergency_stop_timer = QTimer()
        self.emergency_stop_timer.setInterval(15000)  # 15000 ms = 15 seconds
        self.emergency_stop_timer.setSingleShot(True)  # ensure the timer only triggers once
        self.emergency_stop_timer.timeout.connect(self.show_emergency_stop_popup)

        # create an instance of progress bar
        self.progress = ProgressBar()
        self.progress.hide()

        # instantiate tabs
        self.main_tab = MainTab(self.test_data)
        self.manual_tab = ManualTab()
        self.queue_tab = QueueTab()

        # flag for alerting user in case test is running
        self.test_is_running = False

        # build the gui
        self.initUI()

    # method responsible for all gui elements
    def initUI(self):
        # main window and window logo
        self.setWindowTitle('t-chamber')
        self.setGeometry(600, 50, 0, 0)  # decide where on the screen the window will appear (from left, from top)
        self.setWindowIcon(QIcon('arduino_logo.png'))
        self.setStyleSheet('background-color: white;'
                           'color: black;')

        # central widget to hold layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # create a vertical layout
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(10, 0, 10, 10)  # add padding around the entire layout

        # logo
        self.im_label = QLabel(self)
        pixmap = QPixmap('arduino_logo.png')
        self.im_label.setPixmap(pixmap)
        self.im_label.setScaledContents(True)
        self.im_label.setFixedSize(100, 100)  # define logo dimensions
        layout.addWidget(self.im_label, alignment=Qt.AlignLeft)  # add logo to the layout

        # port selector
        layout.addWidget(self.port_selector)

        # add space btw sections: vertical 12px
        layout.addSpacerItem(QSpacerItem(0, 12))

        # start button
        self.start_button = QPushButton('start')
        self.start_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-size: 20px;'
                                        'font-weight: bold;')
        layout.addWidget(self.start_button)

        # add space btw sections: vertical 8px
        layout.addSpacerItem(QSpacerItem(0, 8))

        # QTab widget to hold both tabs
        self.tab_widget = QTabWidget()

        # add tabs to tab widget
        self.tab_widget.addTab(self.main_tab, 'running test info')
        self.tab_widget.addTab(self.manual_tab, 'manual temperature setting')
        self.tab_widget.addTab(self.queue_tab, 'test upload and queue')
        layout.addWidget(self.tab_widget)

        # add space btw sections: vertical 12px
        layout.addSpacerItem(QSpacerItem(0, 12))

        # listbox for test updates
        self.serial_label = QLabel('running test info', self)
        self.listbox = QListWidget(self)
        self.listbox.setFixedHeight(135)
        layout.addWidget(self.serial_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.listbox)

        # add space btw sections: vertical 12px
        layout.addSpacerItem(QSpacerItem(0, 12))

        # listbox for temperature chamber monitoring
        self.chamber_label = QLabel('temperature chamber situation', self)
        self.chamber_monitor = QListWidget(self)
        self.chamber_monitor.setFixedHeight(40)
        # create a QListWidgetItem with centered text
        item = QListWidgetItem('arduino will keep you posted on current temperature and such')
        item.setTextAlignment(Qt.AlignCenter)  # center text
        self.chamber_monitor.addItem(item)
        layout.addWidget(self.chamber_label)
        layout.addWidget(self.chamber_monitor)

        # add space btw sections: vertical 12px
        layout.addSpacerItem(QSpacerItem(0, 12))

        # reset control board button
        self.reset_button = QPushButton('reset control board')
        self.reset_button.setStyleSheet('background-color: grey;'
                                        'color: white;'
                                        'font-weight: bold;'
                                        'font-size: 20px;')
        layout.addWidget(self.reset_button)

        # add space btw sections: vertical 8px
        layout.addSpacerItem(QSpacerItem(0, 8))

        # emergency stop button
        self.emergency_stop_button = QPushButton('emergency stop', self)
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        layout.addWidget(self.emergency_stop_button)

        # add space btw sections: vertical 7px
        layout.addSpacerItem(QSpacerItem(0, 7))

        # initially deactivate reset & emergency stop buttons (should only work when connection with control board)
        self.reset_button.setEnabled(False)
        self.emergency_stop_button.setEnabled(False)

        # connect functionality
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.emergency_stop_button.clicked.connect(self.manual_tab.clear_current_setting_label)
        self.main_tab.run_button.clicked.connect(self.on_run_button_clicked)

        # set layout to the central widget
        self.central_widget.setLayout(layout)

        # automatically adjust window size
        self.adjustSize()

        logger.info('gui built')

    # ESSENTIAL FUNCTIONALITY METHODS
    # method to start running threads after ports have been selected
    def on_start_button_clicked(self):
        logger.info('start button clicked')

        # get selected ports
        self.selected_c_port = self.port_selector.get_selected_c_port()
        self.selected_t_port = self.port_selector.get_selected_t_port()

        # validate selected ports

        logger.info('check if ports are selected')
        # visually signal app activation
        if self.selected_c_port and self.selected_t_port:
            if not hasattr(self, 'serial_worker') or self.serial_worker is None or not self.serial_worker.is_running:
                try:
                    self.serial_worker = SerialCaptureWorker(port=self.selected_c_port, baudrate=9600)
                    self.serial_worker.update_listbox.connect(self.update_listbox_gui)
                    self.serial_worker.update_chamber_monitor.connect(self.update_chamber_monitor_gui)
                    self.emergency_stop_button.clicked.connect(self.on_emergency_stop_button_clicked)
                    self.queue_tab.load_button.clicked.connect(self.load_test_file)
                    self.queue_tab.clear_queue_button.clicked.connect(self.clear_test_queue)
                    self.serial_worker.update_test_data_from_queue.connect(self.update_test_data)
                    self.reset_button.clicked.connect(self.reset_control_board)
                    self.serial_worker.alert_all_tests_complete_signal.connect(self.progress.get_actual_runtime)
                    self.serial_worker.no_port_connection.connect(self.on_no_port_connection_gui)
                    self.serial_worker.serial_running_and_happy.connect(self.show_reset_button)
                    self.serial_worker.ping_timestamp_signal.connect(self.get_timestamp)
                    self.serial_worker.machine_state_signal.connect(self.emergency_stop_from_arduino)
                    self.serial_worker.test_number_signal.connect(self.update_test_number)
                    self.serial_worker.start()  # start the worker thread
                    logger.info('serial worker started successfully')
                    self.no_ping_alert = False
                    self.no_ping_timer.start()
                    self.connection_broken_alert = False
                    self.connection_broken_timer.start()
                    logger.info('qtimer started to check for pings every 5 seconds')

                    # connect manual tab signals
                    self.manual_tab.send_temp_data.connect(self.serial_worker.set_temp)
                    self.manual_tab.test_interrupted.connect(self.test_interrupted__manual_temp_setting_gui)

                except Exception as e:
                    logger.exception(f'failed to start serial worker: {e}')
                    popups.show_error_message('error', f'failed to start serial worker: {e}')

                    return

            if not hasattr(self, 'test_board') or self.test_board is None or not self.test_board.is_running:
                try:
                    self.test_board = TestBoardWorker(self.test_data, self.test_number, port=self.selected_t_port, baudrate=9600)
                    self.test_board.all_good.connect(self.reset_b_t_timer)
                    self.test_board.start()  # start worker thread

                except Exception as e:
                    logger.exception(f'failed to start test board worker: {e}')
                    popups.show_error_message('error', f'failed to start test board worker: {e}')

                    return

            if hasattr(self, 'cli_worker') or self.cli_worker.is_running:
                return
        try:
            self.selected_t_wifi = self.port_selector.get_selected_wifi()
            logger.debug(self.selected_t_wifi)
            if self.selected_t_wifi:
                if not hasattr(self, 'wifi_worker') or self.wifi_worker is None or not self.wifi_worker.is_running:
                    try:
                        self.wifi_worker = WifiWorker(port=self.selected_t_wifi, baudrate=9600)
                        self.wifi_worker.start()  # start worker thread
                    except Exception as e:
                        logger.exception(f'failed to start wifi worker: {e}')
                        popups.show_error_message('error', f'failed to start wifi worker: {e}')

                        return
            else:
                return
        except:
            logger.exception('wifi dropdown failed')

    # trigger emergency stop
    def on_emergency_stop_button_clicked(self):
        self.serial_worker.trigger_emergency_stop.emit()
        message = 'EMERGENCY STOP'
        self.test_interrupted_gui(message)

    # TEST PART
    # run all benchmark tests
    def on_run_button_clicked(self):
        if self.test_data:  # ensure test data is loaded
            # check if test is running
            if self.test_is_running:
                response = popups.show_dialog(
                    'a test is running: are you sure you want to interrupt it and proceed?')
                if response == QMessageBox.Yes:
                    self.check_temp()  # check if desired temp is not too far away from current temp, and let user decide
                    if self.cli_worker.is_running:
                        self.test_number = 0
                        message = 'test interrupted'
                        self.reset_control_board()
                        logger.warning(message)
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        self.on_cli_test_interrupted()
                    else:
                        self.test_number = 0
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        message = 'test was interrupted'
                        self.reset_control_board()
                        logger.info(message)
                elif response == QMessageBox.No:
                    return
            try:
                self.check_temp()  # check if desired temp is not too far away from current temp, and let user decide
                self.test_is_running = True
                self.manual_tab.test_is_running = True
                message = 'test starting'
                self.new_test(message)
                logger.info(message)
                self.progress.show()

                logger.debug('emitting signal to start progress bars')

                # if running tests for nth time, come back to original gui layout to start with
                self.main_tab.on_run_test_gui()
                logger.info(f'about to emit test_data and current_temperature to progress bar, and current temp is {self.current_temperature}')
                self.progress.start_progress_signal.emit(self.test_data, self.current_temperature)
                self.progress.alert_all_tests_complete_signal.connect(self.all_tests_complete)

                if not self.serial_worker.is_stopped:
                    self.trigger_run_t()  # send signal to serial capture worker thread to run all tests
                    self.manual_tab.clear_current_setting_label()
                    self.serial_worker.update_test_label_signal.connect(self.update_test_label)
                    self.serial_worker.next_sequence_progress.connect(self.progress.advance_sequence)
                    self.serial_worker.sequence_complete.connect(self.new_test)
                    self.serial_worker.upload_sketch_again_signal.connect(self.upload_sketch_for_new_test)
                if not self.test_board.is_stopped:
                    self.test_board.is_running = False
                    self.test_broken_timer.stop()
                    self.test_board.stop()
                    self.test_board.deleteLater()
                    logger.info('test board worker temporarily deleted')
                    # initiate cli worker thread
                    self.cli_worker = CliWorker(port=self.selected_t_port, baudrate=9600)
                    self.cli_worker.finished.connect(self.cleanup_cli_worker)  # connect finished signal
                    self.cli_worker.update_upper_listbox.connect(self.main_tab.cli_update_upper_listbox_gui)
                    self.cli_worker.start()  # start cli worker thread
                    self.cli_worker.set_test_data_signal.emit(self.test_data, self.filepath, self.test_number)
                    logger.info('cli worker started')
                    time.sleep(0.1)
            except:
                logger.exception('something went wrong')
                popups.show_error_message('error', 'no serial connection')
        else:
            popups.show_error_message('error', 'no test data loaded')

    # clean up cli worker after it's done
    def cleanup_cli_worker(self):
        self.cli_worker.is_running = False
        self.cli_worker.stop()
        self.cli_worker.quit()
        self.cli_worker.wait()
        logger.info('cli worker quit')
        self.cli_worker.deleteLater()
        logger.info('cli worker deleted')

        time.sleep(1.5)  # time for the port to fully close before restarting
        # restart test board worker thread
        self.test_board = TestBoardWorker(self.test_data, self.test_number, port=self.selected_t_port, baudrate=9600)
        self.test_board.update_upper_listbox.connect(self.main_tab.update_test_output_listbox_gui)
        self.test_board.update_upper_listbox.connect(self.check_output)
        self.test_board.all_good.connect(self.reset_b_t_timer)
        self.test_board.start()  # start test board thread
        self.test_board.is_running = True

        logger.info('test board worker restarted')
        # update the gui
        self.main_tab.change_test_part_gui(self.test_data)
        self.test_board.expected_outcome_listbox.connect(self.main_tab.check_output)

    # update test number for test coordination
    def update_test_number(self, message):
        self.test_number = message
        logger.info(f'current test number: {self.test_number}')
        self.main_tab.update_test_number(self.test_number)

    # upload sketch for each test separately
    def upload_sketch_for_new_test(self, message):
        self.new_test(message)
        info = 'uploading sketch for next test'
        self.update_listbox_gui(info)
        if not self.test_board.is_stopped:
            self.main_tab.sketch_upload_between_tests_gui()
            self.test_broken_timer.stop()
            self.test_board.is_running = False
            self.test_board.stop()
            self.test_board.deleteLater()
            logger.info('test board worker temporarily deleted for subsequent sketch upload')
            # initiate cli worker thread
            self.cli_worker = CliWorker(port=self.selected_t_port, baudrate=9600)
            self.cli_worker.finished.connect(self.cleanup_cli_worker)  # connect finished signal
            self.cli_worker.update_upper_listbox.connect(self.main_tab.cli_update_upper_listbox_gui)
            self.cli_worker.start()  # start cli worker thread
            self.cli_worker.set_test_data_signal.emit(self.test_data, self.filepath, self.test_number)
            logger.info('cli worker started for new test upload')
            time.sleep(0.1)

    # on cli test interrupted by another test
    def on_cli_test_interrupted(self):
        logger.info(self.test_number)
        if self.cli_worker and self.cli_worker.is_running:
            logger.info('cli being interrupted')
            self.cli_worker.finished.disconnect(self.cleanup_cli_worker)
            self.cli_worker.is_running = False
            self.cli_worker.stop()
            self.cli_worker.quit()
            self.cli_worker.wait()
            logger.info('cli worker quit bcs interrupted')
            self.cli_worker.deleteLater()
            logger.info('cli worker deleted bcs interrupted')
            time.sleep(1.5)  # time for the port to fully close before restarting

            # restart test board worker thread
            self.test_board = TestBoardWorker(self.test_data, self.test_number, port=self.selected_t_port, baudrate=9600)
            self.test_board.all_good.connect(self.reset_b_t_timer)
            self.test_board.start()  # start test board thread
            self.test_board.is_running = True
            logger.info('test board worker restarted through cli interrupted')
            self.main_tab.on_run_test_gui()

    # load test file and store it in the app
    def load_test_file(self):
        test_data = self.json_handler.open_file()
        self.serial_worker.trigger_add_test_data_to_queue.emit(test_data)
        self.filepath = self.json_handler.get_filepath()
        logger.info(f'filepath from file handler: {self.filepath}')
        popups.show_info_message('info', 'test file added to test queue')

    # update self.test_data from test queue from arduino
    def update_test_data(self, test_data):
        self.test_data = test_data
        self.get_test_file_name()
        self.get_test_names_from_queue()

    # retrieve test directory names from test data and send to queue tab
    def get_test_file_name(self):
        directories = [test["sketch"].split('/')[-2] for test in self.test_data["tests"] if '/' in test["sketch"]]
        result_string = "\n".join(directories)
        self.queue_tab.get_test_file_name.emit(result_string)

    # get test titles from test data and send to queue tab
    def get_test_names_from_queue(self):
        names = [test["name"] for test in self.test_data["tests"]]
        result_string = "\n".join(names)
        self.queue_tab.display_queue_from_arduino.emit(result_string)

    # TEST-RELATED GUI UPDATES
    # the actual listbox updates
    def update_listbox_gui(self, message):
        self.listbox.addItem(message)
        self.listbox.scrollToBottom()

    # similar method for incorrect test board output notice
    def incorrect_output_gui(self, message):
        item = QListWidgetItem(message)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        item.setForeground(QColor('red'))
        self.listbox.addItem(item)
        self.listbox.scrollToBottom()

    # similar method to be triggered separately when a test is interrupted
    def test_interrupted_gui(self, message):
        self.test_is_running = False
        self.manual_tab.set_test_flag_to_false_signal.emit()
        self.test_label_no_test()
        self.progress.hide()
        self.main_tab.test_interrupted_gui()
        self.new_test(message)

    # similar method to be triggered separately when a test is interrupted by manual temp setting
    def test_interrupted__manual_temp_setting_gui(self, message):
        self.test_is_running = False
        self.manual_tab.set_test_flag_to_false_signal.emit()
        self.test_label_no_test()
        self.progress.hide()
        self.main_tab.test_interrupted_gui()
        self.new_test(message)

    # similar method for new test
    def new_test(self, message):
        item = QListWidgetItem(message)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        self.listbox.addItem(item)
        self.listbox.scrollToBottom()

    # update test label if no test is running
    def test_label_no_test(self):
        if self.test_is_running:
            return
        else:
            self.serial_label.setText(
                'running test info:  no test currently running')
            self.serial_label.setStyleSheet('font-weight: normal;')

    # calculate number of sequences in current test
    def calculate_number_of_sequences_in_current_test(self, current_test):
        self.sequences_in_test = 0
        if self.test_data and 'tests' in self.test_data:
            test = self.test_data['tests'].get(current_test)
            if test:
                sequences = test.get('chamber_sequences', [])
                self.sequences_in_test = len(sequences)
        return self.sequences_in_test

    # update running test info label
    def update_test_label(self, test_info):
        if self.test_is_running:
            test = test_info.get('test')
            sequence = test_info.get('sequence')
            time_left = test_info.get('time_left') * 60  # convert minutes to seconds
            duration = test_info.get('current_duration') * 60  # convert minutes to seconds

            # calculate number of sequences in current test
            number_of_sequences = self.calculate_number_of_sequences_in_current_test(test)

            # calculate hours, minutes, and seconds
            duration_hours, duration_rem = divmod(duration, 3600)
            duration_minutes, duration_seconds = divmod(duration_rem, 60)

            # format duration
            if duration_hours > 0:
                formatted_duration = f"{int(duration_hours)}h {int(duration_minutes)}m"
            elif duration_minutes > 0:
                formatted_duration = f"{int(duration_minutes)}m {int(duration_seconds)}s"
            else:
                formatted_duration = f"{int(duration_seconds)}s"

            logger.info('parsing test info to update running sequence label')

            # update label text
            if time_left <= 0:  # handle waiting state
                self.progress.sequence_label.setText(
                    f'{test}  |  sequence {sequence} of {number_of_sequences}  |  waiting')
                self.serial_label.hide()
            else:
                self.progress.sequence_label.setText(
                    f'{test}  |  sequence {sequence} of {number_of_sequences}  |  duration: {formatted_duration}')
                self.serial_label.hide()
        else:
            self.serial_label.show()

    # display info about all tests being complete
    def all_tests_complete(self, message):
        self.test_is_running = False
        all_done = 'all tests complete'
        self.progress.sequence_label.setText(all_done)
        self.new_test(message)
        self.serial_label.hide()

    # check the difference btw current temp & first desired test temp to potentially warn user about long wait time
    def check_temp(self):
        test_keys = list(self.test_data["tests"].keys())
        first_test_key = test_keys[0]
        first_temp = float(self.test_data["tests"][first_test_key]["chamber_sequences"][0]["temp"])
        # check absolute difference
        if self.current_temperature - first_temp >= 10:
            temp_situation = 'the difference between current and desired temperature in the upcoming test sequence is greater than 10°C, and you will need to wait a while before the chamber reaches it. do you want to proceed?'
            response = popups.show_dialog(temp_situation)
            if response == QMessageBox.No:
                return

    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_tests = [key for key in test_data['tests'].keys()]
            current_test_index = self.test_number
            if current_test_index < len(all_tests):
                current_test_key = all_tests[current_test_index]
                test = self.test_data['tests'][current_test_key]
                expected_output = test.get('expected_output', '')  # get pertinent exp output
                logger.info(f'expected output: {expected_output}')
                return expected_output
            else:
                return

    # compare expected test outcome with actual test board output
    def check_output(self, output):
        output = str(output)
        expected_output = self.expected_output(self.test_data)
        if output == '':
            message = 'waiting for test board output'
            self.update_listbox_gui(message)
        if output == expected_output:
            return
        else:
            date_str = datetime.now().strftime("%H:%M:%S")
            error_message = f"{date_str}   {output}"
            self.incorrect_output_gui(error_message)

    # WORKER THREAD TRIGGERS AND GETTERS + THEIR GUI PARTS
    # CONTROL BOARD: the actual chamber_monitor QList updates from ping
    def update_chamber_monitor_gui(self, message):
        # retrieve current temperature from ping and convert it
        temp = message.get('current_temp')
        logger.info(f'current temp from ping to update serial monitor: {temp}')
        self.current_temperature = temp
        logger.info(f'self.current_temperature: {self.current_temperature}')
        formatted_current_temp = f"{temp:.2f}"
        logger.info(f'formatted current temp: {formatted_current_temp}')
        # retrieve desired temp
        desired_temp = message.get('desired_temp')
        # retrieve machine state
        self.machine_state = message.get('machine_state')
        # create a displayable info string
        status = f'current temp: {formatted_current_temp}°C | target temp: {desired_temp}°C | machine state: {self.machine_state}'
        self.chamber_monitor.clear()  # clear old data
        item = QListWidgetItem(status)  # add string as a widget
        item.setTextAlignment(Qt.AlignCenter)   # align it to center
        self.chamber_monitor.addItem(item)  # display it

    # get timestamp from ping
    def get_timestamp(self, timestamp):
        if not timestamp:
            self.timestamp = None
            logger.warning('received None for timestamp')
            return
        logger.debug(f"raw timestamp received: {timestamp}")

        try:
            clean_timestamp = timestamp.strip()
            self.timestamp = parser.isoparse(clean_timestamp)
            logger.info(f'timestamp from ping: {self.timestamp}')

        except Exception as e:
            logger.exception(f"error while processing timestamp: {e}")
            self.timestamp = None

    # intercept emergency stop machine state
    def emergency_stop_from_arduino(self, machine_state):
        self.machine_state = machine_state
        logger.info(self.machine_state)

        if self.machine_state == 'EMERGENCY_STOP':
            # if alert popup has not been shown, show it
            if not self.emergency_stop_popup_shown:
                message = 'the system is off: DO SOMETHING!'
                popups.show_error_message('warning', 'the system is off: DO SOMETHING!')
                self.emergency_stop_popup_shown = True
                logger.info(message)
                # if the issue has not been solved within 15 seconds, show popup again
                self.emergency_stop_timer.start()
                self.test_interrupted_gui(message)
            else:
                return

    # emergency stop alert popup method to be triggered by qtimer
    def show_emergency_stop_popup(self):
        # check if the machine state is still in EMERGENCY_STOP
        if self.machine_state == 'EMERGENCY_STOP':
            message = 'system is still off: DO SOMETHING NOW!'
            popups.show_error_message('warning', message)
            logger.info(message)
            self.emergency_stop_popup_shown = True
            self.test_interrupted_gui(message)
        else:
            self.reset_emergency_stop()

    # reset emergency stop alert popup flag
    def reset_emergency_stop(self):
        self.emergency_stop_popup_shown = False
        self.emergency_stop_timer.stop()

    # if no ping comes through for over 5 minutes
    def no_ping_for_five(self):
        if self.timestamp and datetime.now() - self.timestamp >= timedelta(minutes=5):
            if not self.no_ping_alert:
                self.manual_tab.set_serial_is_running_to_false()
                self.no_ping_gui()
                message = 'due to lack of communication for at least 5 minutes, control board is reset\n you can reconnect the board(s) and click start again'
                popups.show_error_message('warning', message)
                logger.warning(message)
                self.no_ping_alert = True

    # visually signal that there has been no connection to control board for at least 5 minutes
    def no_ping_gui(self):
        logger.info('changing gui to no ping for 5')
        self.setWindowTitle('no connection to control board')
        self.chamber_monitor.setStyleSheet('color: grey;'
                                           )
        self.reset_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;')
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        message = 'serial connection to control board was lost over 5 minutes ago, control board is reset now'
        popups.show_error_message('warning', message)

    # if no ping for 10 seconds (cable issues?)
    def no_serial_cable(self):
        if self.timestamp and datetime.now() - self.timestamp >= timedelta(seconds=15):
            if not self.connection_broken_alert:
                self.manual_tab.set_serial_is_running_to_false()
                message = 'no serial connection for 15 seconds, check cable'
                logger.warning(message)
                popups.show_error_message('warning', message)
                self.connection_broken_alert = True

    # if no readout from test board for 10 seconds (cable issues?)
    def no_test_cable(self):
        if not self.test_broken_alert:
            self.test_broken_timer.stop()
            message = 'no serial connection with test board for 1 minute, check cable'
            logger.warning(message)
            self.no_test_connection_gui()
            popups.show_error_message('warning', message)
            self.test_broken_alert = True

    # reset test board cable connection timer, triggered by signal from test board worker
    def reset_b_t_timer(self):
        self.test_broken_timer.start()
        self.test_broken_alert = False

    # visually signal that there has been no connection to test board for at least 10 seconds
    def no_test_connection_gui(self):
        logger.info('changing gui to no test connection for 10 sec')
        self.update_listbox_gui('test board has been disconnected for at least 30 seconds')

    # connect run_tests signal from main to serial worker thread
    def trigger_run_t(self):
        self.serial_worker.trigger_run_tests.emit()

    # GUI HELPER METHODS: START AND RESET BUTTONS
    # on start button clicked in case no port connection
    def on_no_port_connection_gui(self):
        popups.show_error_message('warning',
                                  'ports are either not selected or already busy.')
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        self.chamber_monitor.setStyleSheet('color: grey;'
                                           )
        self.reset_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;')

    # light up colors for reset and emergency stop buttons when serial worker starts
    def show_reset_button(self):
        self.reset_button.setEnabled(True)
        self.emergency_stop_button.setEnabled(True)
        self.reset_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-weight: bold;'
                                        'font-size: 20px;')
        self.setWindowTitle('temperature chamber app is running')
        self.chamber_monitor.setStyleSheet('color: #009FAF;'
                                           )
        self.emergency_stop_button.setStyleSheet('background-color: red;'
                                                 'font-weight: bold;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 )
        self.manual_tab.set_serial_is_running_flag_to_true()
        self.queue_tab.set_serial_is_running_flag_to_true()
        self.queue_tab.serial_is_running_gui()
        self.main_tab.serial_is_running_gui()

    # reset control board
    def reset_control_board(self):
        if self.serial_worker and self.serial_worker.is_running:
            self.serial_worker.trigger_reset.emit()
            if self.test_is_running:
                if self.cli_worker and self.cli_worker.is_running:
                    self.on_cli_test_interrupted()
                    logger.info('test interrupted, reset signal emitted')
                    message = 'test interrupted'
                    self.test_interrupted_gui(message)
                else:
                    logger.info('reset signal emitted')
                    message = 'test interrupted'
                    self.test_interrupted_gui(message)
            else:
                message = 'control board is reset'
                self.new_test(message)

    def clear_test_queue(self):
        if self.serial_worker and self.serial_worker.is_running:
            self.serial_worker.trigger_reset.emit()
            if self.test_is_running:
                response = popups.show_dialog(
                    'a test is running: are you sure you want to interrupt it and proceed?')
                if response == QMessageBox.Yes:
                    if self.cli_worker and self.cli_worker.is_running:
                        self.test_number = 0
                        self.on_cli_test_interrupted()
                        logger.info('test interrupted, test queue is cleared')
                        message = 'test interrupted, test queue is cleared'
                        self.test_interrupted_gui(message)
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        self.on_cli_test_interrupted()
                    else:
                        logger.info('test interrupted, test queue is cleared')
                        message = 'test interrupted, test queue is cleared'
                        self.test_interrupted_gui(message)
                        self.test_number = 0
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                elif response == QMessageBox.No:
                    return
            else:
                message = 'test queue is cleared'
                self.new_test(message)

    # HIDDEN FUNCTIONALITY
    # stop both workers
    def closeEvent(self, event):
        self.serial_worker.stop()
        self.test_board.stop()
        event.accept()  # ensure the application closes


# method responsible for running the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

main()

