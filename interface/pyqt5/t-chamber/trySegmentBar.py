from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

class SegmentedBar(QWidget):
    def __init__(self, sequence_durations):
        super().__init__()
        self.sequence_durations = sequence_durations
        self.segment_colors = ['#009FAF', '#004F7F', '#00BFCF', '#007F9F']  # Example colors
        self.completed_segments = []  # To track which segments are completed

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        total_duration = sum(self.sequence_durations)
        current_x = 0
        bar_width = self.width()
        bar_height = self.height()

        # Draw each segment
        for index, duration in enumerate(self.sequence_durations):
            segment_width = (duration / total_duration) * bar_width
            color = self.segment_colors[index % len(self.segment_colors)]

            # Check if the segment is completed
            if index in self.completed_segments:
                painter.setBrush(QColor('#004F7F'))  # Dark color for completed segments
            else:
                painter.setBrush(QColor(color))  # Bright color for active segments

            painter.setPen(QPen(Qt.white, 1))  # White lines between segments
            painter.drawRect(current_x, 0, segment_width, bar_height)
            current_x += segment_width

    def mark_segment_completed(self, index):
        if index not in self.completed_segments:
            self.completed_segments.append(index)
            self.update()  # Repaint the widget to reflect the change
