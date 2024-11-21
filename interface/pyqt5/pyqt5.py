import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setWindowTitle("first pyqt5 gui")
        self.setGeometry(600, 400, 500, 500)
        self.setWindowIcon(QIcon("arduino_logo.png"))
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        labelim = QLabel(self)
        labelim.setGeometry(0, 0, 250, 250)

        pixmap = QPixmap("arduino_logo.png")
        labelim.setPixmap(pixmap)
        labelim.setScaledContents(True)

        labelim.setGeometry((self.width() - labelim.width()) // 2, # double slashes for integer division!
                            (self.height() - labelim.height()) // 2,
                            labelim.width(),
                            labelim.height())

        label = QLabel("hello", self)
        label.setFont(QFont("Garamond", 34))
        label.setGeometry(0, 0, 500, 100)
        label.setStyleSheet("color: #009FAF;"
                            "background-color: grey;"
                            "font-weight: bold;"
                            "text-decoration: underline;")
        # label.setAlignment(Qt.AlignBottom) # vertically
        # label.setAlignment(Qt.AlignHCenter) # horizontally

        # label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        label.setAlignment(Qt.AlignCenter) # center

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()