from utilities import *

class GuiTrix:
    def __init__(self):     #initialize class
        pass

    def on_dropdown_button_release(self, app_instance, command, *args):      # handle dropdown button release

        app_instance.send_command(None, command)

        # show the temperature input box only when "SET TEMP " is chosen
        if command == "SET TEMP ":
            if app_instance.temperature_input not in app_instance.layout.children:
                app_instance.layout.add_widget(app_instance.temperature_input)  # Insert below the label
                app_instance.layout.add_widget(app_instance.time_input)
                app_instance.layout.add_widget(app_instance.run_test_button)
        else:
            # If any other command is selected, remove the temperature input box
            if app_instance.temperature_input in app_instance.layout.children and app_instance.time_input in app_instance.layout.children:
                app_instance.layout.remove_widget(app_instance.temperature_input)
                app_instance.layout.remove_widget(app_instance.time_input)
                app_instance.layout.remove_widget(app_instance.run_test_button)