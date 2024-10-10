from PyQt5.QtCore import QThread, pyqtSignal


class SerialCaptureWorker(QThread):
    update_instruction_listbox = pyqtSignal(str)  # signal to update instruction listbox

    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com
        self.is_running = True

    def run(self):
        while self.is_running:
            response = self.serial_com.capture_all_serial()
            if response:
                self.process_response(response)

    def process_response(self, response):
        trigger_responses = ['Setting', 'Running', 'Test complete', 'Target temp', 'Sequence complete']
        if any(response.strip().startswith(trigger) for trigger in trigger_responses):
            self.update_instruction_listbox.emit(response)

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
