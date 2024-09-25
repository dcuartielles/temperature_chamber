from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from functools import partial
import serial
import time

class DropMenu(App):
    def build(self):
        # Set up serial communication
        try:
            self.ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            print("connected to arduino port: COM13")
        except serial.SerialException as e:
            print(f"error: {e}")
            self.ser = None

        # Create a label to display the Arduino's responses
        self.response_label = Label(text="arduino responses will be displayed here", size_hint=(1, 1))

        # Create a dropdown menu
        dropdown = DropDown()
        commands = [
            "SET TEMP 25",
            "EMERGENCY STOP",
            "RESET",
            "REPORT"
        ]
        for command in commands:
            btn = Button(text=command, size_hint_y=None, size_hint_x=None, height=44, width=500, background_color=(.8, 0, .9))
            # Use partial to correctly bind the command
            btn.bind(on_release=partial(self.on_dropdown_button_release, command))
            dropdown.add_widget(btn)

        main_button = Button(text='choose what you want to do', size_hint=(None, None), height=44, width=500, background_color=(.8, 0, .9))
        main_button.bind(on_release=dropdown.open)

        dropdown.bind(on_select=self.send_command)

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(main_button)
        layout.add_widget(self.response_label)

        return layout

    def on_dropdown_button_release(self, command, *args):
        # Handle dropdown button release
        self.send_command(None, command)

    def send_command(self, instance, command):
        if self.ser and self.ser.is_open:
            try:
                self.ser.reset_input_buffer()
                self.ser.write((command + '\n').encode('utf-8'))
                print(f"sent command: {command}")
                self.response_label.text = f"sent command: {command}"

                time.sleep(2)

                arduino_responses = []
                while self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    if response:
                        arduino_responses.append(response)

                if arduino_responses:
                    self.response_label.text = f"arduino responded: {arduino_responses[-1]}"
                else:
                    self.response_label.text = "no response from arduino"

                time.sleep(1)
            except serial.SerialException as e:
                print(f"error sending command: {e}")
                self.response_label.text = "error sending command"
        else:
            print("serial connection is not available.")
            self.response_label.text = "serial connection is not available"

    def on_stop(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("serial port closed.")
            self.response_label.text = "serial port closed"

if __name__ == '__main__':
    DropMenu().run()
