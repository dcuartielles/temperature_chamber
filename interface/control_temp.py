from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
import serial
import time

class TemperatureControlApp(App):
    def build(self):
        # Set up serial communication with Arduino
        try:
            self.ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            print("connected to Arduino port: COM13")
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.ser = None

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create a label to display status
        self.response_label = Label(text="arduino will tell you things over here", size_hint=(1, 1), font_size='22sp')

        # Create text input for setting temperature
        self.temperature_input = TextInput(hint_text="enter desired temperature", multiline=False, size_hint=(1, 0.2), background_color=(0, .5, .5))

        # Create a button to send the temperature command
        set_temp_button = Button(text="set temperature", size_hint=(1, 0.2))
        set_temp_button.bind(on_release=self.set_temperature)

        # Add widgets to the layout
        layout.add_widget(Label(text="temperature control", size_hint=(1, 0.3)))
        layout.add_widget(self.temperature_input)
        layout.add_widget(set_temp_button)
        layout.add_widget(self.response_label)

        return layout

    def set_temperature(self, instance):
        # Get the user input temperature
        temperature = self.temperature_input.text

        # Check if input is a valid number
        if temperature.replace('.', '', 1).isdigit():
            # Send the "SET TEMP <value>" command to Arduino
            command = f"SET TEMP {temperature}"
            self.send_command(command)
        else:
            self.response_label.text = "invalid input: elease enter a numeric value"

    def send_command(self, command):
        if self.ser and self.ser.is_open:
            try:
                self.ser.reset_input_buffer()
                self.ser.write((command + '\n').encode('utf-8'))
                print(f"sent command: {command}")
                #self.response_label.text = f"sent command: {command}"

                time.sleep(2)

                # Read Arduino's response
                arduino_responses = []
                while self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    if response == "status: 1":
                        self.response_label.text = "heating patiently"
                    
                    elif response:
                        arduino_responses.append(response)

                # Update the label with Arduino's response
                if arduino_responses:
                    self.response_label.text = f"{arduino_responses[-1]}"
                else:
                    self.response_label.text = "no response from arduino"

            except serial.SerialException as e:
                print(f"error sending command: {e}")
                self.response_label.text = "error sending command"
        else:
            print("serial connection is not available.")
            self.response_label.text = "serial connection is not available"

    def on_stop(self):
        # Close serial communication on app close
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("serial port closed.")
            self.response_label.text = "serial port closed"

if __name__ == '__main__':
    TemperatureControlApp().run()
