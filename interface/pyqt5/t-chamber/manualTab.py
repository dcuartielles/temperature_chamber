from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
                             QLineEdit, QHBoxLayout, QMessageBox, QListWidgetItem, QSpacerItem)
from logger_config import setup_logger
import popups

logger = setup_logger(__name__)


class ManualTab(QWidget):
    # signals to and from main
    send_temp_data = pyqtSignal(list)
    test_interrupted = pyqtSignal(str)

    def __init__(self, parent=None):
        self.input_dictionary = []
        super().__init__(parent)
        self.test_is_running = False
        self.initUI()

    def initUI(self):
        # create a vertical layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # add padding around the entire layout

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        # info label
        self.info_label = QLabel('type in desired temperature & duration, then press enter to set', self)
        layout.addWidget(self.info_label)

        # set temperature and duration in their own layout part
        input_layout = QHBoxLayout()

        # add input widgets for setting temp & duration
        self.set_temp_input = QLineEdit(self)
        self.set_temp_input.setPlaceholderText('temperature in °C')
        self.set_temp_input.setStyleSheet('color: #009FAF;')
        self.set_duration_input = QLineEdit(self)
        self.set_duration_input.setPlaceholderText('duration in minutes')
        self.set_duration_input.setStyleSheet('color: #009FAF;')

        # place elements
        input_layout.addWidget(self.set_temp_input)
        input_layout.addWidget(self.set_duration_input)

        # add input layout part to main layout
        layout.addLayout(input_layout)

        self.current_setting = QLabel('', self)
        layout.addWidget(self.current_setting)

        # add space btw sections: vertical 20px
        layout.addSpacerItem(QSpacerItem(0, 20))

        self.set_temp_input.returnPressed.connect(self.on_enter_key)
        self.set_duration_input.returnPressed.connect(self.on_enter_key)

        self.setLayout(layout)

    # enter for temp & duration inputs
    def on_enter_key(self):
        # check both inputs only when the user presses enter
        temp_string = self.set_temp_input.text().strip()
        duration_string = self.set_duration_input.text().strip()

        if temp_string and duration_string:  # make sure both fields are filled
            is_valid = self.check_inputs(temp_string, duration_string)  # validate inputs

            if is_valid and self.input_dictionary:  # if valid inputs
                if self.test_is_running:
                    response = popups.show_dialog(
                        'a test is running: are you sure you want to interrupt it and proceed?')
                    if response == QMessageBox.Yes:
                        message = 'test interrupted'
                        self.test_interrupted.emit(message)
                        self.test_is_running = False
                        logger.warning(message)
                    elif response == QMessageBox.No:
                        return
                self.send_temp_data.emit(self.input_dictionary)  # set temp in arduino
                if duration_string == '1':
                    current_string = f'temperature set to {temp_string}°C for the duration of {duration_string} minute'
                else:
                    current_string = f'temperature set to {temp_string}°C for the duration of {duration_string} minutes'
                self.current_setting.setText(current_string)
                logger.info(f'sent to arduino: {self.input_dictionary}')

    # make sure both temp & duration are submitted by user
    def check_inputs(self, temp_string, duration_string):
        is_valid = True  # track overall validity

        try:
            temp = float(temp_string)
            if temp >= 100:
                popups.show_error_message('error', 'max temperature = 100°C')
                is_valid = False
        except ValueError:
            popups.show_error_message('error', 'numbers only')
            is_valid = False

        try:
            duration = int(duration_string)
            if duration < 1:  # check for minimum duration
                popups.show_error_message('error', 'minimum duration is 1 minute')
                is_valid = False
        except ValueError:
            popups.show_error_message('error', 'numbers only')  #
            is_valid = False

        if is_valid:
            self.input_dictionary.clear()  # clear previous input
            new_sequence = {'temp': temp, 'duration': duration * 60000}  # convert duration to milliseconds
            self.input_dictionary.append(new_sequence)  # append valid input to the dictionary
            logger.info(self.input_dictionary)  # log temp & duration
        return is_valid

    # auxiliary method for emergency stop
    def clear_entries(self):
        self.set_temp_input.clear()
        self.set_temp_input.setPlaceholderText('temperature in °C')
        self.set_duration_input.clear()
        self.set_duration_input.setPlaceholderText('duration in minutes')

    def clear_current_setting_label(self):
        self.current_setting.setText('')
        self.clear_entries()
