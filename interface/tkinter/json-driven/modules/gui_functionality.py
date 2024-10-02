# imports
import tkinter as tk


# function to clear the entry widget
def clear_entry_on_click(event):
    if event.widget.get() in ['temperature in °C: ', 'numbers only', 'duration in minutes: ', 'max temperature = 100°C',
                              'enter a number',
                              'minimum duration is 1 minute']:  # check for placeholder or warning text
        event.widget.delete(0, tk.END)  # clear the entry widget
        event.widget['fg'] = 'black'  # change text color to normal if needed


def clear_entry_on_stop():
    ent_duration.delete(0, tk.END)
    ent_temp.delete(0, tk.END)


def add_placeholder(entry, placeholder_text):
    entry.insert(0, placeholder_text)
    entry['fg'] = 'grey'  # set the color to a lighter grey for the placeholder text

    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)  # Clear the placeholder text when focused
            entry['fg'] = 'black'  # Set the text color to normal

    def on_focus_out(event):
        if entry.get() == '':  # If the user didn't type anything, put the placeholder back
            entry.insert(0, placeholder_text)
            entry['fg'] = 'grey'

    # bind the events
    entry.bind('<FocusIn>', on_focus_in)
    entry.bind('<FocusOut>', on_focus_out)

