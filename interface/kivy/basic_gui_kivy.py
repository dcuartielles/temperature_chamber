import serial
import threading
import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class RealTimeDisplay(BoxLayout):
    def __init__(self, **kwargs):
        super(RealTimeDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # Create label to display data
        self.label = Label(text="waiting for data...", font_size='20sp')
        self.add_widget(self.label)

        self.ser = None

        # Initialize serial communication
        try:
            self.ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            print("Connected to Arduino on COM13")
        except serial.SerialException as e:
            self.label.text = f"Serial Error: {e}"
            print(f"Serial Error: {e}")
        except PermissionError as pe:
            self.label.text = f"Permission Error: {pe}"
            print(f"Permission Error: {pe}")

        if self.ser:
            # Start a separate thread to continuously read from the serial port
            self.read_thread = threading.Thread(target=self.read_arduino_data, daemon=True)
            self.read_thread.start()

    def send_command(self, command):
        # Submit the command to be sent in the background
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()
            self.ser.write((command + '\n').encode('utf-8'))
            print(f"Sent command: {command}")

    def read_arduino_data(self):
        """Continuously read from Arduino in a separate thread."""
        while self.ser and self.ser.is_open:
            try:
                self.send_command("SHOW DATA")  # Send command to request data
                time.sleep(1)  # Wait for Arduino to process the command

                response = self.ser.readline().decode('utf-8').strip()
                if response and "input available" not in response:
                    print(f"Arduino responded: {response}")
                    Clock.schedule_once(lambda dt: self.update_label(response))
                else:
                    print("Received unexpected message or no valid data.")

            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                Clock.schedule_once(lambda dt: self.update_label(f"Error reading data: {e}"))
                break


    def update_label(self, text):
        """Update the label in the UI."""
        self.label.text = text

    def on_stop(self):
        """Stop serial communication when the app is closed."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

class RealTimeApp(App):
    def build(self):
        return RealTimeDisplay()

if __name__ == '__main__':
    RealTimeApp().run()
