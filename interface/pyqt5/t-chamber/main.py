# system and PyQt5 imports
import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QLineEdit, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTabWidget
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal

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
import popups

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

        # create a dictionary for setting temp & duration and space for test file accessible from the worker thread
        self.input_dictionary = []
        self.test_data = None
        self.filepath = None
        self.exp_output = None

        # tabs
        self.main_tab = MainTab(self.test_data)
        self.manual_tab = ManualTab()

        # flag for preventing user from interrupting a test
        self.test_is_running = False

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
        layout.setContentsMargins(10, 10, 10, 10)  # add padding around the entire layout

        # logo
        self.im_label = QLabel(self)
        pixmap = QPixmap('arduino_logo.png')
        self.im_label.setPixmap(pixmap)
        self.im_label.setScaledContents(True)
        self.im_label.setFixedSize(100, 100)  # define logo dimensions
        layout.addWidget(self.im_label, alignment=Qt.AlignLeft)  # add logo to the layout

        # port selector
        layout.addWidget(self.port_selector)

        # add space btw sections: vertical 15px
        layout.addSpacerItem(QSpacerItem(0, 15))

        # start button
        self.start_button = QPushButton('start')
        self.start_button.setStyleSheet('background-color: #009FAF;'
                                        'color: white;'
                                        'font-size: 20px;'
                                        'font-weight: bold;')
        layout.addWidget(self.start_button)

        # add space btw sections: vertical 10px
        layout.addSpacerItem(QSpacerItem(0, 10))

        # QTab widget to hold both tabs
        self.tab_widget = QTabWidget()

        # add tabs to tab widget
        self.tab_widget.addTab(self.main_tab, 'test control')
        self.tab_widget.addTab(self.manual_tab, 'manual temperature setting')
        layout.addWidget(self.tab_widget)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # listbox for test updates
        self.serial_label = QLabel('running test info', self)
        self.listbox = QListWidget(self)
        self.listbox.setFixedHeight(135)
        layout.addWidget(self.serial_label)
        layout.addWidget(self.listbox)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

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


        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 30))

        # emergency stop button
        self.emergency_stop_button = QPushButton('emergency stop', self)
        self.emergency_stop_button.setStyleSheet('background-color: grey;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 'font-weight: bold;')
        layout.addWidget(self.emergency_stop_button)

        # add space btw sections: vertical 11px
        layout.addSpacerItem(QSpacerItem(0, 11))

        # connect functionality
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.main_tab.load_button.clicked.connect(self.load_test_file)
        self.emergency_stop_button.clicked.connect(self.manual_tab.clear_current_setting_label)
        self.main_tab.run_button.clicked.connect(self.on_run_button_clicked)

        # set layout to the central widget
        self.central_widget.setLayout(layout)
        # automatically adjust window size
        self.adjustSize()

    # GUI FUNCTIONALITY-RELATED METHODS

    # method to start running threads after ports have been selected
    def on_start_button_clicked(self):
        self.light_up()
        # disable the start button to prevent double-clicks
        self.start_button.setDisabled(True)

        # retrieve selected ports after user has had a chance to pick them
        self.selected_c_port = self.port_selector.get_selected_c_port()
        self.selected_t_port = self.port_selector.get_selected_t_port()

        # only now create the worker threads with the selected ports
        self.serial_worker = SerialCaptureWorker(port=self.selected_c_port, baudrate=9600)
        self.serial_worker.update_listbox.connect(self.update_listbox_gui)
        self.serial_worker.update_chamber_monitor.connect(self.update_chamber_monitor_gui)
        self.serial_worker.start()  # start the worker thread
        self.emergency_stop_button.clicked.connect(self.serial_worker.emergency_stop)
        self.manual_tab.send_temp_data.connect(self.serial_worker.set_temp)
        self.manual_tab.test_interrupted.connect(self.test_interrupted_gui)
        self.manual_tab.set_flag_to_false.connect(self.set_flag_to_false)

        self.port_selector.ports_refreshed.connect(self.re_enable_start)

        # create test board worker thread
        self.test_board = TestBoardWorker(port=self.selected_t_port, baudrate=9600)
        self.test_board.start()  # start test board thread

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
        item = QListWidgetItem(message)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        self.listbox.addItem(item)
        self.listbox.scrollToBottom()

    # similar method for new test
    def new_test(self, message):
        item = QListWidgetItem(message)
        font = QFont()
        font.setBold(True)
        item.setFont(font)
        self.listbox.addItem(item)
        self.listbox.scrollToBottom()

    # the actual chamber_monitor QList updates
    def update_chamber_monitor_gui(self, message):
        self.chamber_monitor.clear()  # clear old data
        item = QListWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        self.chamber_monitor.addItem(item)

    # load test file and store it in the app
    def load_test_file(self):
        self.test_data = self.json_handler.open_file()
        self.filepath = self.json_handler.get_filepath()
        self.expected_output(self.test_data)

    # button click handlers
    # connect run_tests signal from main to serial worker thread
    def trigger_run_t(self):
        self.serial_worker.trigger_run_tests.emit(self.test_data)

    # extract expected test outcome from test file
    def expected_output(self, test_data):
        if test_data is not None and 'tests' in test_data:
            all_expected_outputs = []
            all_tests = [key for key in test_data['tests'].keys()]
            # iterate through each test and run it
            for test_key in all_tests:
                test = test_data['tests'].get(test_key, {})
                expected_output = test.get('expected output', '')  # get the expected output string
                if expected_output:
                    all_expected_outputs.append(expected_output)
            self.exp_output = all_expected_outputs[0]
            logger.info(self.exp_output)
            return all_expected_outputs
        return []

    def trigger_compare(self):
        self.main_tab.expected_outcome_listbox_signal.emit(self.exp_output)

    # run all benchmark tests
    def on_run_button_clicked(self):
        if self.test_data and self.selected_t_port:  # ensure test data is loaded and t-port is there
            # check if test is running
            if self.test_is_running:
                response = popups.show_dialog(
                    'a test is running: are you sure you want to interrupt it and proceed?')
                if response == QMessageBox.Yes:
                    if self.cli_worker.is_running:
                        message = 'test interrupted'
                        self.test_interrupted_gui(message)
                        logger.warning(message)
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        self.on_cli_test_interrupted()

                    else:
                        self.test_is_running = False
                        self.manual_tab.test_is_running = False
                        message = 'test interrupted'
                        self.test_interrupted_gui(message)
                        logger.warning(message)
                elif response == QMessageBox.No:
                    return

            self.test_is_running = True
            self.manual_tab.test_is_running = True
            message = 'test starting'
            self.new_test(message)
            logger.info(message)

            # if running tests for nth time, come back to original gui layout to start with
            self.main_tab.on_run_test_gui()

            if not self.serial_worker.is_stopped:
                self.trigger_run_t()  # send signal to serial capture worker thread to run all tests
                self.manual_tab.clear_current_setting_label()
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
        else:
            popups.show_error_message('error', 'no test data loaded')

    # on cli test interrupted
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
            self.test_board = TestBoardWorker(port=self.selected_t_port, baudrate=9600)
            self.test_board.start()  # start test board thread
            self.test_board.is_running = True
            logger.info('test board worker restarted through cli interrupted')
            self.main_tab.on_run_test_gui()

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
        self.test_board = TestBoardWorker(port=self.selected_t_port, baudrate=9600)
        self.test_board.update_upper_listbox.connect(self.main_tab.update_test_output_listbox_gui)
        self.test_board.update_upper_listbox.connect(self.main_tab.check_output)
        logger.info('connect signals')
        self.main_tab.incorrect_output.connect(self.incorrect_output_gui)
        self.test_board.empty_output.connect(self.main_tab.reset_gui_for_waiting)
        self.test_board.start()  # start test board thread
        self.test_board.is_running = True
        logger.info('test board worker restarted')
        self.trigger_compare()
        logger.info('trigger compare')

        # update the gui
        self.main_tab.change_test_part_gui(self.test_data)

    # method to set test_is_runing to False when test_interrupted from manual
    def set_flag_to_false(self):
        self.test_is_running = False

    # re-enable start button after refreshing ports
    def re_enable_start(self):
        self.start_button.setEnabled(True)

    def light_up(self):
        self.setWindowTitle('temperature chamber app is running')
        self.chamber_monitor.setStyleSheet('color: #009FAF;'
                                           )
        self.emergency_stop_button.setStyleSheet('background-color: red;'
                                                 'font-weight: bold;'
                                                 'color: white;'
                                                 'font-size: 20px;'
                                                 )
        self.port_selector.setStyleSheet('color: #009FAF;'
                                         'background-color: white;'
                                         'alignment: right;'
                                         'font-weight: bold;')

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


# self.manual_tab.test_interrupted.connect(self.update_listbox_gui)