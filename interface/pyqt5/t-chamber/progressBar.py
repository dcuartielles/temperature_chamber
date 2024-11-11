import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer

class ProgressBar(QWidget):
    def __init__(self, test_data, parent=None):
        super().__init__(parent)
        self.test_data = test_data
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
        self.sequence_label = QLabel('test progress', self)
        self.sequence_progress_bar = QProgressBar()
        self.sequence_progress_bar.setValue(0)  # initial value of the progress bar
        self.sequence_progress_bar.setTextVisible(False)  # hide percentage text
        self.sequence_progress_bar.setMaximum(100)  # represent progress as percent
        sequence_progress_layout.addWidget(self.sequence_label)
        sequence_progress_layout.addWidget(self.sequence_progress_bar)

        # create time progress bar and label
        self.time_label = QLabel('estimated time progress', self)
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
        self.total_duration = self.estimate_total_time(self.test_data)

        # set up the timer for updating progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_progress)

        # initialize progress tracking variables
        self.current_sequence_index = 0
        self.sequence_durations = self.get_sequence_durations()
        self.elapsed_time = 0

        # progress value
        self.progress_value = 0

    def start_progress(self):
        if self.sequence_durations:
            self.elapsed_time = 0
            self.current_sequence_index = 0
            self.time_progress_bar.setValue(0)
            self.sequence_progress_bar.setValue(0)
            self.timer.start(100)  # timer updates every 100 milliseconds
            self.start_next_sequence()  # start the first sequence


    def update_time_progress(self):
        self.elapsed_time += 100  # increment elapsed time by 100 milliseconds
        total_progress = (self.elapsed_time / self.total_duration) * 100
        self.time_progress_bar.setValue(int(total_progress))

        if self.elapsed_time >= self.total_duration:
            self.timer.stop()  # stop timer when total progress is complete

    def start_next_sequence(self):
        if self.current_sequence_index < len(self.sequence_durations):
            # set up the current sequence
            sequence_duration = self.sequence_durations[self.current_sequence_index]
            self.timer.singleShot(sequence_duration, self.advance_sequence)  # wait for the duration to finish

            # set color for the current sequence in the progress bar
            color = self.get_color_for_sequence(self.current_sequence_index)
            self.sequence_progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

            self.current_sequence_index += 1

    def advance_sequence(self):
        # when a sequence is done, trigger the next one
        self.start_next_sequence()

    # estimate total running time
    def estimate_total_time(self, test_data):
        if test_data is not None and 'tests' in test_data:
            total_duration = 0
            for test_key in test_data['tests']:
                test = test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    duration = sequence.get('duration', 0)  # get duration for every test sequence
                    total_duration += int(duration)  # add to total duration, in milliseconds
                return total_duration
        return 0

    # get number of sequences for sequence progress bar
    def get_sequence_durations(self):
        durations = []
        if self.test_data and 'tests' in self.test_data:
            for test_key in self.test_data['tests']:
                test = self.test_data['tests'][test_key]
                sequences = test.get('chamber_sequences', [])
                for sequence in sequences:
                    durations.append(sequence.get('duration', 0))
        return durations

    def get_color_for_sequence(self, index):
        # define a list of colors to use for the sequences
        colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33F3']
        return colors[index % len(colors)]  # cycle through colors if there are more sequences
