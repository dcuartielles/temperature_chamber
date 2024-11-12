import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
from logger_config import setup_logger

logger = setup_logger(__name__)

class ProgressBar(QWidget):

    start_progress_signal = pyqtSignal(dict, int)  # signal from main to start timer for progress bars

    def __init__(self, parent=None):
        super().__init__(parent)

        self.test_data = None

        # initialize progress tracking variables
        self.current_sequence_index = 0
        self.sequence_durations = []
        self.sequence_duration = 0
        self.total_duration = 0
        self.current_temp = 0
        self.temperatures = []

        # set up the timer for updating progress
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_progress)
        self.elapsed_time = 0

        # separate timer for sequence progress bar
        self.sequence_timer = QTimer(self)
        self.sequence_timer.timeout.connect(self.update_sequence_progress)
        # progress value
        self.progress_value = 0

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
        self.sequence_progress_bar = QProgressBar()
        self.sequence_progress_bar.setValue(0)  # initial value of the progress bar
        self.sequence_progress_bar.setTextVisible(False)  # hide percentage text
        self.sequence_progress_bar.setMaximum(100)  # represent progress as percent
        sequence_progress_layout.addWidget(self.sequence_label)
        sequence_progress_layout.addWidget(self.sequence_progress_bar)

        # create time progress bar and label
        self.time_label = QLabel('estimated run time', self)
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
        logger.debug('progress gui set up')

    # start processing progress bar for general test time
    def start_progress(self, test_data, current_temp):
        self.current_temp = current_temp
        self.test_data = test_data
        self.sequence_durations = self.get_sequence_durations()
        self.total_duration = self.estimate_total_time()
        if self.total_duration:
            self.update_test_bar_label()
            self.elapsed_time = 0
            self.time_progress_bar.setValue(0)
            self.timer.start(100)  # timer updates every 100 milliseconds
            self.time_progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: #009FAF; }}")

    # update the actual progress bar for general test time
    def update_time_progress(self):
        if self.test_data:
            logger.debug('starting timer progress')
            self.elapsed_time += 100  # increment elapsed time by 100 milliseconds
            total_progress = (self.elapsed_time / self.total_duration) * 100
            self.time_progress_bar.setValue(int(total_progress))
            logger.debug(f'time progress: {int(total_progress)}%')

            if self.elapsed_time >= self.total_duration:
                self.timer.stop()  # stop timer when total progress is complete
        else:
            logger.debug('setting up overall test time progress bar, no test data here yet')
            return

    # start processing new sequence progress bar
    def start_next_sequence(self):
        if self.current_sequence_index < len(self.sequence_durations):
            logger.debug('starting new sequence progress bar')
            self.sequence_duration = self.sequence_durations[self.current_sequence_index]
            self.progress_value = 0  # reset progress for the new sequence
            self.sequence_progress_bar.setValue(0)
            self.sequence_timer.start(100)  # timer updates every 100 milliseconds

            # set color for the current sequence in the progress bar
            color = self.get_color_for_sequence(self.current_sequence_index)
            self.sequence_progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    # display visually sequence progress
    def update_sequence_progress(self):
        if self.test_data:
            self.progress_value += 100 / (self.sequence_duration / 100)  # increment progress proportionally
            self.sequence_progress_bar.setValue(int(self.progress_value))
            logger.debug(f'sequence progress: {int(self.progress_value)}%')

            if self.progress_value >= 100:
                self.sequence_timer.stop()  # stop when sequence is complete
                self.progress_value = 0  # reset for next sequence
        else:
            logger.debug('setting up sequence progress, no test data here yet')
            return

    # trigger new sequence bar
    def advance_sequence(self, current_sequence):
        # set current sequence index from current sequence number received from serial worker
        logger.debug('triggering a new sequence')
        self.current_sequence_index = current_sequence - 1
        self.start_next_sequence()

    # get target temperatures from test_data
    def get_temperatures(self):
        temperatures = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    temperatures.append(sequence.get('temp', 0))
        logger.info(temperatures)
        self.temperatures = temperatures
        return self.temperatures

    # estimate total running time
    def estimate_total_time(self):
        # start by adding total test sequence duration
        self.total_duration += sum(self.sequence_durations)

        # calculate degrees to reach target temp for first sequence
        degrees_to_target = int(self.temperatures[0]) - self.current_temp
        prep_time = 0
        # if chamber needs to heat up
        if degrees_to_target > 0:
            prep_time = degrees_to_target * 13200  # ca 2.2 minutes per degree, in milliseconds

        # if chamber needs cooling
        elif degrees_to_target < 0:
            prep_time = abs(degrees_to_target) * 52800  # ca 9 minutes per degree, in milliseconds, absolute value

        # add prep time
        self.total_duration += prep_time

        time_between = 0

        # calculate time for temperature changes between subsequent target temperatures
        for i in range(1, len(self.temperatures)):
            degrees_difference = int(self.temperatures[i]) - int(self.temperatures[i - 1])
            # if chamber needs to heat up
            if degrees_difference > 0:
                time_between = degrees_difference * 13200  # 2.2 minutes per degree, in milliseconds
            # if chamber needs cooling
            elif degrees_difference < 0:
                time_between = abs(degrees_difference) * 52800  # 8.8 minutes per degree, in milliseconds

        self.total_duration += time_between

        return self.total_duration

    # update test progress bar label with estimated total time
    def update_test_bar_label(self):
        estimated_time = self.total_duration / 60.000
        formatted_est_time = f"{estimated_time:.2f}"
        self.time_label.setText(f'estimated run time: {formatted_est_time} min')

    # get a dictionary of sequences for sequence progress bar
    def get_sequence_durations(self):
        durations = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    durations.append(sequence.get('duration', 0))
        logger.info(durations)
        return durations

    def get_color_for_sequence(self, index):
        # define a list of colors to use for sequence progress bar
        colors = ['#10DDDD', '#E1DA0F', '#E10F85', '#3289DF', '#EC8F74']
        return colors[index % len(colors)]

    '''# start processing progress bar for general test time
    def start_progress(self, test_data):
        self.test_data = test_data
        self.sequence_durations = self.get_sequence_durations()
        self.estimate_total_time()
        if self.total_duration:
            self.elapsed_time = 0
            self.time_progress_bar.setValue(0)
            self.timer.start(100)  # timer updates every 100 milliseconds
            self.update_time_progress()

    # update the actual progress bar for general test time
    def update_time_progress(self):
        if self.test_data:
            logger.debug('starting timer progress')
            self.elapsed_time += 100  # increment elapsed time by 100 milliseconds
            total_progress = (self.elapsed_time / self.total_duration) * 100
            self.time_progress_bar.setValue(int(total_progress))
            if self.elapsed_time >= self.total_duration:
                self.timer.stop()  # stop timer when total progress is complete
        else:
            logger.debug('setting up overall test time progress bar, no test data here yet')
            return

    # start processing new sequence progress bar
    def start_next_sequence(self):
        logger.debug('starting new sequence progress bar')
        if self.current_sequence_index < len(self.sequence_durations):
            # set up the current sequence
            self.sequence_duration = self.sequence_durations[self.current_sequence_index]
            self.sequence_progress_bar.setValue(0)  # reset progress bar
            self.update_sequence_progress()
            # set color for the current sequence in the progress bar
            color = self.get_color_for_sequence(self.current_sequence_index)
            self.sequence_progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            # self.current_sequence_index += 1

    # display visually sequence progress
    def update_sequence_progress(self):
        if self.test_data:
            self.progress_value += 100 / (self.sequence_duration / 100)  # increment progress proportionally
            self.sequence_timer.start(100)
            if self.progress_value >= 100:
                self.sequence_timer.stop()  # stop when the sequence is complete
                self.progress_value = 0
            else:
                self.sequence_progress_bar.setValue(int(self.progress_value))
        else:
            logger.debug('setting up sequence progress, no test data here yet')
            return

    
    def advance_sequence(self, current_sequence):
        # set current sequence index from current sequence number received from serial worker
        self.current_sequence_index = current_sequence - 1
        logger.debug('triggering a new sequence')
        # trigger this sequence progress bar
        self.start_next_sequence()

    # estimate total running time
    def estimate_total_time(self):
        sequence_durations = self.get_sequence_durations()
        self.total_duration = sum(sequence_durations)  # sum of all sequence durations in milliseconds
        return self.total_duration

    # get number of sequences for sequence progress bar
    def get_sequence_durations(self):
        durations = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    durations.append(sequence.get('duration', 0))

        logger.info(durations)
        return durations

    def get_color_for_sequence(self, index):
        # define a list of colors to use for the sequences
        colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33F3']
        return colors[index % len(colors)]  # cycle through colors if there are more sequences'''
