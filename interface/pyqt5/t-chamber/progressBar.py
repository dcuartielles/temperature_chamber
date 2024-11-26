import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen
from logger_config import setup_logger
from sequenceProgressBar import SequenceProgressBar


logger = setup_logger(__name__)


class ProgressBar(QWidget):

    start_progress_signal = pyqtSignal(dict, int)  # signal from main to start timer for progress bars
    alert_all_tests_complete_signal = pyqtSignal(str)  # signal to update gui when last test sequence is complete

    def __init__(self, parent=None):
        super().__init__(parent)

        self.test_data = None

        self.sequence_progress_bar = SequenceProgressBar(self)

        # initialize progress tracking variables
        self.current_sequence_index = 0
        self.sequence_durations = []
        self.sequence_duration = 0
        self.number_of_sequences = 0
        self.total_duration = 0
        self.current_temp = None
        self.temperatures = []
        self.number_of_tests = 0

        # set up the timer for updating progress
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_progress)
        self.elapsed_time = 0
        self.elapsed_minutes = 0

        # timer to measure the actual runtime
        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)
        self.actual_runtime = 0  # in milliseconds

        self.start_progress_signal.connect(self.start_progress)

        self.initUI()

    def initUI(self):

        # set up the main layout
        layout = QVBoxLayout()

        # set up layout for progress bars to be next to one another
        horizontal = QHBoxLayout()

        # create a layout per progress bar
        sequence_progress_layout = QVBoxLayout()
        time_progress_layout = QVBoxLayout()

        # create sequence progress bar and label
        self.sequence_label = QLabel('sequence progress', self)
        sequence_progress_layout.addWidget(self.sequence_label)
        sequence_progress_layout.addWidget(self.sequence_progress_bar)

        # create time progress bar and label
        self.time_label = QLabel('estimated runtime', self)
        self.time_progress_bar = QProgressBar()
        self.time_progress_bar.setValue(0)
        time_progress_layout.addWidget(self.time_label)
        time_progress_layout.addWidget(self.time_progress_bar)

        # place progress bars and their labels next to one another
        horizontal.addLayout(sequence_progress_layout)
        horizontal.addLayout(time_progress_layout)

        # add progress bars to general layout
        layout.addLayout(horizontal)

        # set the layout
        self.setLayout(layout)
        self.show()
        logger.debug('progress gui set up')

    # start processing progress bar for general test time
    def start_progress(self, test_data, current_temp):
        # get all the necessary variables filled
        self.current_temp = current_temp
        self.test_data = test_data
        self.sequence_durations = self.get_sequence_durations()
        self.temperatures = self.get_temperatures()
        # reset overall runtime progress bar
        self.total_duration = 0
        self.total_duration = self.estimate_total_time()
        self.update_test_bar_label()
        self.elapsed_time = 0
        self.time_progress_bar.setValue(0)
        self.timer.start(100)  # timer updates every 100 milliseconds
        self.time_progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: #009FAF; }}")
        # reset sequence progress bar
        self.current_sequence_index = 0
        self.sequence_progress_bar.set_sequence_data(self.sequence_durations, self.current_sequence_index)
        # start stopwatch
        self.actual_runtime = 0
        self.stopwatch_timer.start(1000)  # update / store every second

    # update the actual progress bar for overall test time
    def update_time_progress(self):
        if self.test_data:
            self.elapsed_time += 100  # increment elapsed time by 100 milliseconds
            total_progress = (self.elapsed_time / self.total_duration) * 100
            self.time_progress_bar.setValue(int(total_progress))

            if self.elapsed_time >= self.total_duration:
                self.timer.stop()  # stop timer when total progress is complete
        else:
            logger.debug('setting up overall test time progress bar, no test data here yet')
            return

    # stopwatch methods
    def update_stopwatch(self):
        self.actual_runtime += 1000  # increment actual runtime by 1 second

    # stop stopwatch and save the actual runtime
    def stop_stopwatch(self):
        self.stopwatch_timer.stop()
        self.timer.stop()
        # force progress bar to 100%
        self.time_progress_bar.setValue(100)
        # make it green-ish for success
        self.time_progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #06e59b; }")
        self.elapsed_minutes = int(self.actual_runtime / 60000)
        elapsed_hours, elapsed_minutes = divmod(self.elapsed_minutes, 60)
        formatted_elapsed_time = f"{int(elapsed_hours)}h {int(elapsed_minutes)}m" if elapsed_hours > 0 else f"{int(elapsed_minutes)}m"
        logger.info(f'parsing elapsed time for clear display, actual runtime was {formatted_elapsed_time}')
        self.time_label.setText(f'done in {formatted_elapsed_time}')
        return formatted_elapsed_time

    # trigger new sequence progress bar update
    def advance_sequence(self):
        logger.debug('triggering a new sequence')
        self.current_sequence_index += 1
        if self.current_sequence_index <= len(self.sequence_durations):
            self.sequence_progress_bar.set_sequence_data(self.sequence_durations, self.current_sequence_index)
            self.number_of_sequences += 1
            logger.debug(self.number_of_sequences)
            if self.number_of_sequences == len(self.sequence_durations):
                done_in = self.stop_stopwatch()
                alert = f'all tests complete in {done_in}'
                self.alert_all_tests_complete_signal.emit(alert)
            elif self.number_of_sequences > len(self.sequence_durations):
                return
        else:
            return

    # get target temperatures from test_data
    def get_temperatures(self):
        self.number_of_tests = 0
        temperatures = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                self.number_of_tests += 1
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    temperatures.append(sequence.get('temp', 0))
        logger.info(temperatures)
        self.temperatures = temperatures
        return self.temperatures

    # estimate total running time
    def estimate_total_time(self):
        # reset total duration
        self.total_duration = 0
        # start by adding total test sequence duration
        self.total_duration += sum(self.sequence_durations)
        logger.debug('start by adding total test sequence duration')

        # calculate degrees to reach target temp for first sequence
        degrees_to_target = int(self.temperatures[0]) - int(self.current_temp)
        logger.debug('calculate degrees to reach target temp for first sequence')

        prep_time = 0
        # if chamber needs to heat up
        if degrees_to_target > 0:
            prep_time = degrees_to_target * 30000  # 0.5 min per degree, in milliseconds
            logger.debug('ca 2.2 minutes per degree, in milliseconds')
        # if chamber needs cooling
        elif degrees_to_target < 0:
            prep_time = abs(degrees_to_target) * 120000  # 2 minutes per degree, in milliseconds, absolute value
            logger.debug('ca 9 minutes per degree, in milliseconds, absolute value')
        # add prep time
        self.total_duration += prep_time
        logger.debug('add prep time')

        # calculate time for temperature changes between subsequent target temperatures
        for i in range(1, len(self.temperatures)):
            degrees_difference = int(self.temperatures[i]) - int(self.temperatures[i - 1])
            logger.debug('calculate time for temperature changes between subsequent target temperatures')
            # if chamber needs to heat up
            if degrees_difference > 0:
                self.total_duration += degrees_difference * 30000  # 0.5 min per degree, in milliseconds

            # if chamber needs cooling
            elif degrees_difference < 0:
                self.total_duration += abs(
                    degrees_difference) * 120000  # 2 min per degree, in millis, absolute value

        # adjust total duration according to what practice shows to be more realistic
        # self.total_duration = self.total_duration * 0.93

        return self.total_duration

    # update test progress bar label with estimated total time
    def update_test_bar_label(self):
        estimated_time = int(self.total_duration / 60000)  # estimated time in minutes
        est_hours, est_minutes = divmod(estimated_time, 60)
        formatted_estimated_time = f"{int(est_hours)}h {int(est_minutes)}m" if est_hours > 0 else f"{int(est_minutes)}m"
        logger.info(f'parsing estimated runtime for clear display, actual runtime was {formatted_estimated_time}')
        tests = self.number_of_tests
        if tests > 1:
            self.time_label.setText(f'{tests} tests | estimated runtime: {formatted_estimated_time}')
        else:
            self.time_label.setText(f'one test | estimated runtime: {formatted_estimated_time}')

    # get a dictionary of sequences for sequence progress bar
    def get_sequence_durations(self):
        durations = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    durations.append(sequence.get('duration', 0))
        logger.info(f'all durations: {durations}')
        return durations

    # signal to update main and sequence when all tests are complete
    def alert_all_tests_complete(self, message):
        alert = message
        self.alert_all_tests_complete_signal.emit(alert)

