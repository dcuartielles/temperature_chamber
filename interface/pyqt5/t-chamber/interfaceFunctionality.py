from PyQt5.QtWidgets import QLineEdit


# create entry functionality class
class EntryHandler:
    def __init__(self):
        self.entries = []  # store references to all entries

    def add_entry(self, entry: QLineEdit, placeholder_text: str):
        """
        adds an entry with placeholder text
        :param entry: QLineEdit widget
        :param placeholder_text: placeholder text for the entry
        """
        entry.setPlaceholderText(placeholder_text)  # set placeholder
        entry.setStyleSheet("color: grey;")  # set initial color to grey for placeholder

        # add focus in and out events for the entry
        entry.focusInEvent = lambda event: self.on_focus_in(entry, event, placeholder_text)
        entry.focusOutEvent = lambda event: self.on_focus_out(entry, event, placeholder_text)

        # store the entry for clearing later if needed
        self.entries.append(entry)

    def on_focus_in(self, entry: QLineEdit, event, placeholder_text: str):
        """
        event when the entry gets focus
        :param entry: QLineEdit widget
        :param event: focus event
        :param placeholder_text: placeholder text to check
        """
        if entry.text() == placeholder_text:
            entry.clear()  # clear placeholder text
            entry.setStyleSheet("color: black;")  # change text color to black
        super(QLineEdit, entry).focusInEvent(event)  # keep default behavior

    def on_focus_out(self, entry: QLineEdit, event, placeholder_text: str):
        """
        event when the entry loses focus
        :param entry: QLineEdit widget
        :param event: focus event
        :param placeholder_text: placeholder text to check
        """
        if entry.text().strip() == '':
            entry.setText(placeholder_text)  # reinsert placeholder text
            entry.setStyleSheet("color: grey;")  # set color back to grey
        super(QLineEdit, entry).focusOutEvent(event)  # keep default behavior

    # clear all registered entries
    def clear_entries(self):
        for entry in self.entries:
            entry.clear()
