from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import QEvent

# create entry functionality class
class EntryHandler:
    def __init__(self):
        self.entries = []  # store references to all entries

    # clear all registered entries
    def clear_entries(self):
        for entry in self.entries:
            entry.clear()
