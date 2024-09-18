from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import serial
import time

class RealTimeDisplay(BoxLayout):
    def __init__(self, **kwargs):
        super(RealTimeDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Create label to display data
        self.label = Label(text="Waiting for data...", font_size='20sp')
        self.add_widget(self.label)
        
        # Initialize serial communication
        self.ser = serial.Serial('COM5', 9600, timeout=5)
        time.sleep(2)  # Allow Arduino to reset

        # Schedule the updateData method to be called every second
        Clock.schedule_interval(self.updateData, 1)

    def updateData(self, dt):
        if self.ser.in_waiting > 0:
            response = self.ser.readline().decode('utf-8').strip()
            if response and not response.startswith("Enter a value:"):
                data = response.split(",")
                if len(data) == 6:
                    RealTemp, ThermocoupleTemp1, ThermocoupleTemp2, ThermocoupleAverage, CurrentError, CurrentErrorPercentage = data
                    self.label.text = (f"RealTemp: {RealTemp}°C\n"
                                       f"ThermocoupleTemp1: {ThermocoupleTemp1}°C\n"
                                       f"ThermocoupleTemp2: {ThermocoupleTemp2}°C\n"
                                       f"Avg Temp: {ThermocoupleAverage}°C\n"
                                       f"Error: {CurrentError}°C\n"
                                       f"Error %: {CurrentErrorPercentage}%")
            else:
                self.label.text = "Waiting for valid data..."

    def close(self):
        if self.ser.is_open:
            self.ser.close()

class RealTimeApp(App):
    def build(self):
        return RealTimeDisplay()

    def on_stop(self):
        self.root.close()

if __name__ == '__main__':
    RealTimeApp().run()
