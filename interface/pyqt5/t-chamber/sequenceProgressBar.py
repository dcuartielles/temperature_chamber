import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen
from logger_config import setup_logger

logger = setup_logger(__name__)


class SequenceProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sequence_durations = []
        self.current_sequence_index = 0
        self.segment_color = '#009FAF'
        self.past_color = '#006A74'
        self.future_color = '#00D4EA'
        self.setFixedSize(450, 30)  # set a fixed size for the widget

    # get sequence data
    def set_sequence_data(self, sequence_durations, current_index):
        self.sequence_durations = sequence_durations
        self.current_sequence_index = current_index
        logger.debug('got sequence data from progress, about to repaint here')
        self.update()  # trigger a repaint
        logger.debug('repainted')

    # custom painting logic
    def paintEvent(self, event):
        if not self.sequence_durations:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        total_width = self.width()
        bar_height = self.height()

        if total_width == 0 or bar_height == 0:
            logger.warning('invalid dimensions for the sequence progress bar widget')
            return
        logger.debug('about to redraw sequence sen')

        current_x = 0  # starting point for drawing the first segment
        total_duration = sum(self.sequence_durations)

        # draw each segment for the sequences
        for index, duration in enumerate(self.sequence_durations):
            logger.debug('beginning to calculate segments')
            segment_width = (duration / total_duration) * total_width  # proportional width of the segment
            # convert segment width to int
            segment_width = int(segment_width)
            past_color = QColor(self.past_color)
            color = QColor(self.segment_color)
            future_color = QColor(self.future_color)

            # determine color to paint based on progress
            if index < self.current_sequence_index:
                painter.setBrush(past_color)  # completed segments get a darker shade
                logger.debug('completed segments get a darker shade')
            elif index == self.current_sequence_index:
                painter.setBrush(color)  # current segment in regular color
                logger.debug('current segment in regular color')
            else:
                painter.setBrush(future_color)  # upcoming segments get a lighter shade
                logger.debug('upcoming segments get a lighter shade')

            logger.debug('about to make partitions')
            painter.setPen(QPen(QColor('white'), 1))  # draw white borders between segments
            logger.debug('pen set to white')
            painter.drawRect(current_x, 0, segment_width, bar_height)
            logger.debug('has drawn partitions')
            current_x += segment_width  # move to the next segment
