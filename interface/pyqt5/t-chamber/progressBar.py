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

        # set up the timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

        # set the layout
        self.setLayout(layout)

        # progress value
        self.progress_value = 0

    def start_progress(self):
        self.progress_value = 0
        self.time_progress_bar.setValue(self.progress_value)
        self.timer.start(100)  # timer updates every 100 milliseconds

    def update_progress(self):
        total_duration = self.estimate_total_time(self.test_data)
        if self.progress_value >= total_duration:
            self.timer.stop()  # stop the timer when progress is complete
        else:
            self.progress_value += 1
            self.time_progress_bar.setValue(self.progress_value)

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

