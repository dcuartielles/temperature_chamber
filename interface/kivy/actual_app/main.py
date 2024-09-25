from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from kivy.clock import Clock
from utilities import *


class ArduinoApp(App):

    def build(self):

        self.ser = serial_setup()                               #set up serial communication
        self.executor = ThreadPoolExecutor(max_workers=3)       #set up asynchronous work mode
        
        
        
        # start reading Arduino data in the background
        if self.ser:
            read_arduino_data(self.ser, self.update_display, self.executor)

        # Call send_command when needed
        send_command(self.ser, "SET TEMP", self.executor)

    def update_display(self, data):
        # Update the Kivy label or UI with Arduino data
        print(data)  # This would update a label in your Kivy app instead
       
    def on_stop(self):
        # Clean up when the app stops
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("serial port closed.")
        self.executor.shutdown()

if __name__ == '__main__':
    ArduinoApp().run()