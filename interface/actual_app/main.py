from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from kivy.clock import Clock
import serial


class ArduinoApp(app):

    def build(self):
        
        #set up asynchronous work mode
        self.executor = ThreadPoolExecutor(max_workers=2)

        # set up serial communication
        try:
            self.ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            print("connected to arduino port: COM13")
        except serial.SerialException as e:
            print(f"error: {e}")
            self.ser = None
    
    def on_stop(self):
        # Clean up when the app stops
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
        self.executor.shutdown()

if __name__ == '__main__':
    ArduinoApp().run()