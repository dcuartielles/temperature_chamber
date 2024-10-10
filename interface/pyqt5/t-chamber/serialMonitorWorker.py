from PyQt5.QtCore import QThread, pyqtSignal

class SerialMonitorWorker(QThread):
    update_instruction_listbox = pyqtSignal(str)  # signal to update instruction_listbox with a message
    update_chamber_monitor = pyqtSignal(str)       # signal to update chamber monitor with a message

    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com
        self.is_running = True  # Control the thread's running state

    def run(self):
        while self.is_running:
            # Read from the serial port
            message = self.serial_com.read_data()

            # Process the message for test progress
            if message:
                self.process_test_progress(message)
                self.process_chamber_monitor(message)

    def process_test_progress(self, message):
        """Check for specific messages related to test progress."""
        if "TEST STARTED" in message:
            self.update_instruction_listbox.emit("Test has started.")
        elif "TEST PROGRESS" in message:
            self.update_instruction_listbox.emit("Test in progress...")
        elif "TEST COMPLETED" in message:
            self.update_instruction_listbox.emit("Test completed.")

    def process_chamber_monitor(self, message):
        """Check for messages related to chamber monitoring."""
        # Example: You can define specific messages related to the chamber
        chamber_messages = ['Chamber Temperature', 'Chamber Pressure', 'Chamber Status']
        if any(msg in message for msg in chamber_messages):
            self.update_chamber_monitor.emit(message)  # Emit the message to update the chamber monitor

    def stop(self):
        """Stop the thread."""
        self.is_running = False
        self.quit()
        self.wait()
