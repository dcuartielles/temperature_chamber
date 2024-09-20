from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from concurrent.futures import ThreadPoolExecutor
import serial
import time

class RealTimeDisplay(BoxLayout):
    def __init__(self, **kwargs):
        super(RealTimeDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.executor = ThreadPoolExecutor(max_workers=2)
        self.executor.submit(self.updateData)
        
        # Create label to display data
        self.label = Label(text="waiting for data...", font_size='20sp')
        self.add_widget(self.label)
        
        # Initialize serial communication
        try:
            self.ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            time.sleep(1)  # Allow Arduino to reset
            print("connected to Arduino on COM13")
        except serial.SerialException as e:
            self.label.text = f"serial Error: {e}"
            print(f"serial Error: {e}")
            self.ser = None

        # Schedule the updateData method to be called every second
        if self.ser:
            Clock.schedule_interval(self.updateData, 1)
        else:
            self.label.text = "failed to open serial port"


    def updateData(self, dt):
        if self.ser and self.ser.in_waiting > 0:
            try:
                response = self.ser.readline().decode('utf-8').strip()
                print(f"received: {response}")  # Debug print
                self.label.text = f"{response}"
                if response and not response.startswith("enter a value:"):
                    data = response.split("|")
                    if len(data) == 6:
                        RealTemp, ThermocoupleTemp1, ThermocoupleTemp2, ThermocoupleAverage, CurrentError, CurrentErrorPercentage = data
                        self.label.text = (f"RealTemp: {RealTemp}°C\n"
                                           f"ThermocoupleTemp1: {ThermocoupleTemp1}°C\n"
                                           f"ThermocoupleTemp2: {ThermocoupleTemp2}°C\n"
                                           f"Avg Temp: {ThermocoupleAverage}°C\n"
                                           f"Error: {CurrentError}°C\n"
                                           f"Error %: {CurrentErrorPercentage}%")
                else:
                    self.label.text = "waiting for valid data..."
            except Exception as e:
                self.label.text = f"error reading data: {e}"
                print(f"error reading data: {e}")

    def on_stop(self):
        # Clean up when the app stops
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
        self.executor.shutdown()

class RealTimeApp(App):
    def build(self):
        return RealTimeDisplay()

if __name__ == '__main__':
    RealTimeApp().run()
