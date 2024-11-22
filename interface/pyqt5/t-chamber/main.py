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
from config import Config
from logger_config import setup_logger
from mainTab import MainTab
from manualTab import ManualTab
from progressBar import ProgressBar
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

        # prepare space for worker threads to appear later
        self.serial_worker = None
        self.test_board = None
        self.cli_worker = None

        # create a dictionary for setting temp & duration
        self.input_dictionary = []

        # space for test file accessible from worker threads
        self.test_data = None
        self.filepath = None

        # class variables to keep updates from ping
        self.current_temperature = None
        self.machine_state = None
        self.timestamp = None

        # create qtimer instance: after 5 minutes of communication break with serial, control board is reset
        self.no_ping_timer = QTimer(self)
        self.no_ping_timer.timeout.connect(self.no_ping_for_five)  # connect to the method
        self.no_ping_timer.setInterval(5000)  # set interval in milliseconds
        self.no_ping_alert = False  # flag to only have the 5-min alert show once

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

        # flag for alerting user in case test is running
        self.test_is_running = False

        # build the gui
        self.initUI()

    # method responsible for all gui elements
    def initUI(self):
        # main window and window logo
        self.setWindowTitle('t-chamber')
        self.setGeometry(600, 110, 0, 0)  # decide where on the screen the window will appear
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

        # reset control board button
        self.reset_button = QPushButton('reset control board')
        self.reset_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-size: 20px;')
        self.reset_button.hide()
        layout.addWidget(self.reset_button)

        # add space btw sections: vertical 8px
        layout.addSpacerItem(QSpacerItem(0, 8))

        # QTab widget to hold both tabs
        self.tab_widget = QTabWidget()

        # add tabs to tab widget
        self.tab_widget.addTab(self.main_tab, 'test control')
        self.tab_widget.addTab(self.manual_tab, 'manual temperature setting')
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

        # emergency stop button
        self.emergency_stop_button = QPushButton('emergency stop', self)
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        layout.addWidget(self.emergency_stop_button)

        # add space btw sections: vertical 7px
        layout.addSpacerItem(QSpacerItem(0, 7))

        # connect functionality
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.reset_button.clicked.connect(self.reset_control_board)
        self.main_tab.load_button.clicked.connect(self.load_test_file)
        self.emergency_stop_button.clicked.connect(self.manual_tab.clear_current_setting_label)
        self.main_tab.run_button.clicked.connect(self.on_run_button_clicked)
        self.port_selector.ports_refreshed.connect(self.re_enable_start)

        # set layout to the central widget
        self.central_widget.setLayout(layout)

        # automatically adjust window size
        self.adjustSize()

        logger.info('gui built')

    # ESSENTIAL FUNCTIONALITY METHODS
    # method to start running threads after ports have been selected
    def on_start_button_clicked(self):
        logger.info('start button clicked')
        self.start_button.setDisabled(True)  # disable to prevent double-clicks
        self.inactivated_start_button()

        # get selected ports
        self.selected_c_port = self.port_selector.get_selected_c_port()
        self.selected_t_port = self.port_selector.get_selected_t_port()

        # validate selected ports

        logger.info('check if ports are selected')
        # visually signal app activation
        self.light_up()
        if self.selected_c_port and self.selected_t_port:
            if not hasattr(self, 'serial_worker') or self.serial_worker is None or not self.serial_worker.is_running:
                try:
                    self.serial_worker = SerialCaptureWorker(port=self.selected_c_port, baudrate=9600)
                    self.serial_worker.update_listbox.connect(self.update_listbox_gui)
                    self.serial_worker.update_chamber_monitor.connect(self.update_chamber_monitor_gui)
                    self.emergency_stop_button.clicked.connect(self.on_emergency_stop_button_clicked)
                    self.serial_worker.no_port_connection.connect(self.on_no_port_connection_gui)
                    self.serial_worker.serial_running_and_happy.connect(self.show_reset_button)
                    self.serial_worker.ping_timestamp_signal.connect(self.get_timestamp)
                    self.serial_worker.machine_state_signal.connect(self.emergency_stop_from_arduino)
                    self.serial_worker.start()  # start the worker thread
                    logger.info('serial worker started successfully')
                    self.no_ping_alert = False
                    self.no_ping_timer.start()
                    logger.info('qtimer started to check for pings every 5 seconds')

                    # connect manual tab signals
                    self.manual_tab.send_temp_data.connect(self.serial_worker.set_temp)
                    self.manual_tab.test_interrupted.connect(self.test_interrupted_gui)

                except Exception as e:
                    logger.exception(f'failed to start serial worker: {e}')
                    popups.show_error_message('error', f'failed to start serial worker: {e}')
                    self.start_button.setEnabled(True)
                    self.reactivated_start_button()
                    return

            if not hasattr(self, 'test_board') or self.test_board is None or not self.test_board.is_running:
                try:
                    self.test_board = TestBoardWorker(self.test_data, port=self.selected_t_port, baudrate=9600)
                    self.test_board.start()  # start worker thread

                except Exception as e:
                    logger.exception(f'failed to start test board worker: {e}')
                    popups.show_error_message('error', f'failed to start test board worker: {e}')
                    self.start_button.setEnabled(True)
                    return

            if hasattr(self, 'cli_worker') or self.cli_worker.is_running:
                return

    # trigger emergency stop
    def on_emergency_stop_button_clicked(self):
        self.serial_worker.trigger_emergency_stop.emit()
        message = 'EMERGENCY STOP'
        self.emergency_stop_gui(message)

    # TEST PART
    # run all benchmark tests
    def on_run_button_clicked(self):
        if self.test_data and self.selected_t_port:  # ensure test data is loaded and t-port is there
            # check if test is running
            if self.test_is_running:
                response = popups.show_dialog(
                    'a test is running: are you sure you want to interrupt it and proceed?')
                if response == QMessageBox.Yes:
                    self.check_temp()  # check if desired temp is not too far away from current temp, and let user decide
                    if self.cli_worker.is_running:
                        #vself.reset_control_board()
                        message = 'test interrupted'
                        self.test_interrupted_gui(message)
                        logger.warning(message)
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        self.on_cli_test_interrupted()
                    else:
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        message = 'test was interrupted'
                        # self.reset_control_board()
                        self.test_interrupted_gui(message)
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
                    self.test_board.stop()
                    self.test_board.deleteLater()
                    logger.info('test board worker temporarily deleted')
                    # initiate cli worker thread
                    self.cli_worker = CliWorker(port=self.selected_t_port, baudrate=9600)
                    self.cli_worker.set_test_data(self.test_data, self.filepath)
                    self.cli_worker.finished.connect(self.cleanup_cli_worker)  # connect finished signal
                    self.cli_worker.update_upper_listbox.connect(self.main_tab.cli_update_upper_listbox_gui)
                    self.cli_worker.start()  # start cli worker thread
                    logger.info('cli worker started')
                    time.sleep(0.1)
            except:
                logger.exception('no serial connection')
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
        self.test_board = TestBoardWorker(self.test_data, port=self.selected_t_port, baudrate=9600)
        self.test_board.update_upper_listbox.connect(self.main_tab.update_test_output_listbox_gui)
        self.test_board.update_upper_listbox.connect(self.check_output)
        self.test_board.start()  # start test board thread
        self.test_board.is_running = True
        logger.info('test board worker restarted')
        # update the gui
        self.main_tab.change_test_part_gui(self.test_data)
        self.test_board.expected_outcome_listbox.connect(self.main_tab.check_output)

    # upload sketch for each test separately
    def upload_sketch_for_new_test(self, message):
        self.new_test(message)
        if not self.test_board.is_stopped:
            try:
                self.main_tab.sketch_upload_between_tests_gui()
                self.test_board.is_running = False
                self.test_board.stop()
                self.test_board.deleteLater()
                logger.info('test board worker temporarily deleted for subsequent sketch upload')
                # initiate cli worker thread
                self.cli_worker = CliWorker(port=self.selected_t_port, baudrate=9600)
                self.cli_worker.set_test_data(self.test_data, self.filepath)
                self.cli_worker.finished.connect(self.cleanup_cli_worker)  # connect finished signal
                self.cli_worker.update_upper_listbox.connect(self.main_tab.cli_update_upper_listbox_gui)
                self.cli_worker.start()  # start cli worker thread
                logger.info('cli worker started for new test upload')
                time.sleep(0.1)
            except:
                logger.exception('method for sketch upload btw tests failed')

    # on cli test interrupted by another test
    def on_cli_test_interrupted(self):
        if self.cli_worker:
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
            self.test_board = TestBoardWorker(self.test_data, port=self.selected_t_port, baudrate=9600)
            self.test_board.start()  # start test board thread
            self.test_board.is_running = True
            logger.info('test board worker restarted through cli interrupted')
            self.main_tab.on_run_test_gui()

    # load test file and store it in the app
    def load_test_file(self):
        self.test_data = self.json_handler.open_file()
        self.filepath = self.json_handler.get_filepath()

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

    # emergency stop gui
    def emergency_stop_gui(self, message):
        self.test_interrupted_gui(message)
        item = QListWidgetItem(message)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        self.listbox.addItem(item)
        self.listbox.scrollToBottom()

    # similar method to be triggered separately when a test is interrupted
    def test_interrupted_gui(self, message):
        self.test_is_running = False
        self.manual_tab.set_test_flag_to_false_signal.emit()
        self.reset_control_board()
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

    # update running test info label
    def update_test_label(self, test_info):
        if self.test_is_running:
            test = test_info.get('test')
            sequence = test_info.get('sequence')
            time_left = test_info.get('time_left')
            duration = test_info.get('current_duration')
            formatted_time_left = f"{time_left:.2f}"
            logger.info('parsing test info to update running sequence label')
            if str(formatted_time_left) == '0.00':
                self.progress.sequence_label.setText(
                    f'{test}  |  sequence {sequence}  |  waiting')
                self.serial_label.hide()
            else:
                self.progress.sequence_label.setText(f'{test}  |  sequence {sequence}  |  duration: {duration} min')
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
        first_temp = int(self.test_data["tests"][first_test_key]["chamber_sequences"][0]["temp"])
        # check absolute difference
        if self.current_temperature - first_temp >= 10:
            temp_situation = 'the difference between current and desired temperature in the upcoming test sequence is greater than 10°C, and you will need to wait a while before the chamber reaches it. do you want to proceed?'
            response = popups.show_dialog(temp_situation)
            if response == QMessageBox.No:
                return

    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_expected_outputs = []
            all_tests = [key for key in test_data['tests'].keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data['tests'].get(test_key, {})
                expected_output = test.get('expected_output', '')  # get the expected output string
                if expected_output:
                    all_expected_outputs.append(expected_output)
            output = all_expected_outputs[0]
            return output
        return []

    # compare expected test outcome with actual test board output
    def check_output(self, output):
        output = str(output)
        exp_output = self.expected_output(self.test_data)
        if output == '':
            message = 'waiting for test board output'
            self.update_listbox_gui(message)
        if output == exp_output:
            return
        else:
            date_str = datetime.now().strftime("%H:%M:%S")
            error_message = f"{date_str}   {output}"
            self.incorrect_output_gui(error_message)

    # WORKER THREAD TRIGGERS AND GETTERS + THEIR GUI PARTS
    # CONTROL BOARD: the actual chamber_monitor QList updates from ping
    def update_chamber_monitor_gui(self, message):
        # retrieve current temperature from ping and convert it to int
        self.current_temperature = int(message.get('current_temp'))
        # retrieve desired temp
        desired_temp = message.get('desired_temp')
        # retrieve machine state
        self.machine_state = message.get('machine_state')
        # create a displayable info string
        status = f'current temp: {self.current_temperature}°C | target temp: {desired_temp}°C | machine state: {self.machine_state}'
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
                popups.show_error_message('warning', 'the system is off: DO SOMETHING!')
                self.emergency_stop_popup_shown = True
                logger.info('the system is off: DO SOMETHING!')
                # if the issue has not been solved within 15 seconds, show popup again
                self.emergency_stop_timer.start()

    # emergency stop alert popup method to be triggered by qtimer
    def show_emergency_stop_popup(self):
        # check if the machine state is still in EMERGENCY_STOP
        if self.machine_state == 'EMERGENCY_STOP':
            popups.show_error_message('warning', 'system is still off: DO SOMETHING NOW!')
            logger.info('system is still off: DO SOMETHING NOW!')
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
                logger.warning("no ping received for 5 minutes or more")
                self.no_ping_gui()
                message = 'due to lack of communication for at least 5 minutes, control board is reset\n you can reconnect the board(s) and click start again'
                popups.show_error_message('warning', message)
                logger.warning(message)
                self.re_enable_start()
                self.no_ping_alert = True

    # visually signal that there has been no connection to control board for at least 5 minutes
    def no_ping_gui(self):
        logger.info('changing gui to no ping for 5')
        self.setWindowTitle('no connection to control board')
        self.reactivated_start_button()
        self.chamber_monitor.setStyleSheet('color: grey;'
                                           )
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')

    # intercept reset machine state
    def reset_from_arduino(self, machine_state):
        self.machine_state = machine_state
        logger.info(self.machine_state)

    # connect run_tests signal from main to serial worker thread
    def trigger_run_t(self):
        self.serial_worker.trigger_run_tests.emit(self.test_data)

    # GUI HELPER METHODS: START AND RESET BUTTONS
    # visually signal that the app is running
    def light_up(self):
        self.setWindowTitle('temperature chamber app is running')
        self.chamber_monitor.setStyleSheet('color: #009FAF;'
                                           )
        self.emergency_stop_button.setStyleSheet('background-color: red;'
                                                 'font-weight: bold;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 )

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
        self.start_button.setEnabled(True)  # re-enable button to try again
        self.reactivated_start_button()

    # inactive start button gui
    def inactivated_start_button(self):
        self.start_button.setStyleSheet('background-color: grey;'
                                        'color: white;'
                                        'font-size: 20px;'
                                        'font-weight: bold;')

    # reactivated start button gui
    def reactivated_start_button(self):
        self.start_button.show()
        self.reset_button.hide()
        self.start_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-size: 20px;'
                                        'font-weight: bold;')

    # show reset button when serial worker starts
    def show_reset_button(self):
        self.start_button.hide()
        self.reset_button.show()

    # reset control board
    def reset_control_board(self):
        if self.serial_worker and self.serial_worker.is_running:
            self.serial_worker.trigger_reset.emit()
            logger.info('reset signal emitted')

    # re-enable start button after refreshing ports
    def re_enable_start(self):
        self.reactivated_start_button()
        self.start_button.setEnabled(True)
        logger.info('start button re-enabled')

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