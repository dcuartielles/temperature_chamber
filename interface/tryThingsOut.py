from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
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

        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create a label to display the Arduino's responses
        self.response_label = Label(text="arduino responses will be displayed here", size_hint=(1, 1))

        # Create a dropdown menu
        dropdown = DropDown()
        commands = [
            "SET TEMP 25",
            "EMERGENCY STOP",
            "RESET",
            "REPORT",
            "SET TEMP "
        ]
        for command in commands:
            btn = Button(text=command, size_hint_y=None, size_hint_x=None, height=44, width=500, background_color=(.8, 0, .9))
            # Use partial to correctly bind the command
            btn.bind(on_release=partial(self.on_dropdown_button_release, command))
            dropdown.add_widget(btn)

        main_button = Button(text='choose what you want to do', size_hint=(None, None), height=44, width=500, background_color=(.8, 0, .9))
        main_button.bind(on_release=dropdown.open)

        dropdown.bind(on_select=self.send_command)

        # Create text input for setting temperature
        self.temperature_input = TextInput(hint_text="enter desired temperature and press ENTER", multiline=False, size_hint=(1, 0.2), background_color=(0, .5, .5), font_size='22sp', halign='center')
        self.temperature_input.bind(on_text_validate=self.set_temperature)  # Bind 'Enter' key to set_temperature

        # Add widgets to the main layout
        self.layout.add_widget(main_button)
        self.layout.add_widget(self.response_label)

        return self.layout

    def on_dropdown_button_release(self, command, *args):
        # Handle dropdown button release
        self.send_command(None, command)

    def set_temperature(self, instance):
        # Get the user input temperature
        temperature = self.temperature_input.text

        # Check if input is a valid number and not larger than max temperature (e.g., 100)
        if temperature.replace('.', '', 1).isdigit() and float(temperature) <= 100:
            # Send the "SET TEMP <value>" command to Arduino
            command = f"SET TEMP {temperature}"
            self.send_command(None, command)
        else:
            self.response_label.text = "invalid input: please enter a numeric value less than 100"

    def send_command(self, instance, command):
        if self.ser and self.ser.is_open:
            try:
                self.ser.reset_input_buffer()
                self.ser.write((command + '\n').encode('utf-8'))
                print(f"sent command: {command}")
                self.response_label.text = f"sent command: {command}"

                time.sleep(2)

                # Only show the temperature input if the "SET TEMP " command is selected
                if command == "SET TEMP ":
                    if self.temperature_input not in self.layout.children:
                        self.layout.add_widget(self.temperature_input, index=1)  # Insert below the label

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
