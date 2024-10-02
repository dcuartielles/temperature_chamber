# imports
import tkinter as tk
from PIL import Image, ImageTk  # for images
import serial
import time
import json
from tkinter import Listbox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from serial_interaction import *
from gui_functionality import *
from json_handling import *
from txt_file_handling import *

# global flag for stopping the reading process
is_stopped = False

# global flag for starting a new test sequence
starting = False

# declare listbox as it's used in functions below
listbox = None


ser = serial_setup()  # necessary start for interactions with arduino

# initialize a new window
window = tk.Tk()
window.title('temperature chamber')
window.configure(bg='white')
# set an initial size for the window (width, height)
window.geometry("680x700")

# prepare the general grid
window.columnconfigure(0, weight=1)  # make sure gui is vertically expandable
window.rowconfigure(0, weight=1)  # and horizontally

# create a canvas to allow scrolling
canvas = tk.Canvas(window, bg='white')
canvas.grid(row=0, column=0, sticky='nsew')  # extend it across the whole window

# add vertical scrollbar
vertical_scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
vertical_scrollbar.grid(row=0, column=1, sticky='ns')

# add horizontal scrollbar
horizontal_scrollbar = tk.Scrollbar(window, orient="horizontal", command=canvas.xview)
horizontal_scrollbar.grid(row=1, column=0, sticky='ew')

# configure the canvas to use the scrollbars
canvas.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

# bind the resizing event of the canvas to update the scrollable region dynamically
def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


canvas.bind('<Configure>', update_scrollregion)

# create a frame inside the canvas to hold the rest of the gui
main_frame = tk.Frame(canvas, bg='white')
canvas.create_window((340, 350), window=main_frame, anchor='center')

'''
# define global fonts for specific widgets
window.option_add('*Label.Font', ('Arial', 14, 'bold'))  # Apply to all Label widgets
window.option_add('*Button.Font', ('Arial', 12, 'bold'))  # Apply to all Button widgets
window.option_add('*Entry.Font', ('Arial', 12))          # Apply to all Entry widgets
'''

# TEST FRAME & CONTENT + LOGO + SERIAL MONITOR READOUT BELOW EVERYTHING ELSE
frm_tests = tk.Frame(main_frame, borderwidth=1, highlightthickness=0, bg='white')

# LOGO
image_path = 'C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/arduino_logo.png'  # path to logo file
# use PIL to open the image
logo_image = Image.open(image_path)
logo_image = logo_image.resize((100, 100))  # adjust size
logo_photo = ImageTk.PhotoImage(logo_image)
# create  label for the image
lbl_image = tk.Label(frm_tests, image=logo_photo, bg='white')
lbl_image.image = logo_photo  # keep a reference to avoid garbage collection
lbl_image.grid(row=0, column=0, columnspan=3, sticky='nsew')  # position image

# BENCHMARK TEST PART
lbl_benchmark = tk.Label(frm_tests, text='BENCHMARK TESTS', bg='white')
btn_test1 = tk.Button(frm_tests, text='test 1', bg='white', command=lambda: pick_your_test('test 1'))
btn_test2 = tk.Button(frm_tests, text='test 2', bg='white', command=lambda: pick_your_test('test 2'))
btn_test3 = tk.Button(frm_tests, text='test 3', bg='white', command=lambda: pick_your_test('test 3'))
btn_run_all_benchmark = tk.Button(frm_tests, text='RUN ALL BENCHMARK TESTS', bg='white', command=run_all_benchmark)
btn_save_file = tk.Button(frm_tests, text='save custom test to file', bg="red", command=save_text_file)

# CUSTOM TEST PART
lbl_custom = tk.Label(frm_tests, text='CUSTOM TEST', bg='white')
# buttons to add, remove, and modify steps
btn_add = tk.Button(frm_tests, text='add step', command=add_step, width=30, justify='center', bg='white', fg='black')
btn_remove = tk.Button(frm_tests, text='remove step', command=remove_step, width=30, justify='center', bg='white',
                       fg='black')
btn_modify = tk.Button(frm_tests, text='modify step', command=modify_step, width=30, justify='center', bg='white',
                       fg='black')

# listbox to display the current steps
listbox = Listbox(frm_tests, height=10, width=50)
# temp & duration entries & custom test step handling buttons
ent_temp = tk.Entry(frm_tests, width=30, justify='center', bg='white', fg='black')
ent_duration = tk.Entry(frm_tests, width=30, justify='center', bg='white', fg='black')
btn_add_custom = tk.Button(frm_tests, text='ADD CUSTOM TEST', width=30, justify='center', bg='white', fg='black',
                           command=add_custom)
btn_run_custom = tk.Button(frm_tests, text='RUN CUSTOM TEST', width=30, justify='center', bg='white', fg='black',
                           command=lambda: pick_your_test('custom'))

# run all tests
btn_run_all_tests = tk.Button(frm_tests, text='RUN ALL TESTS', bg='white', command=run_all_tests)

# position labels, buttons and user input widgets in test frame
lbl_benchmark.grid(row=1, column=0, sticky='w', padx=5, pady=5)
btn_save_file.grid(row=2, column=2, rowspan=3, sticky='nsew', padx=5, pady=5)
btn_test1.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
btn_test2.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
btn_test3.grid(row=4, column=1, sticky='ew', padx=5, pady=5)
btn_run_all_benchmark.grid(row=5, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
# custom
lbl_custom.grid(row=6, column=0, sticky='w', padx=5, pady=5)
ent_duration.grid(row=7, column=1, sticky='ew', padx=5, pady=5)
ent_temp.grid(row=7, column=0, sticky='ew', padx=5, pady=5)
btn_add.grid(row=7, column=2, sticky='ew', padx=5, pady=5)
btn_modify.grid(row=8, column=2, sticky='ew', padx=5, pady=5)
btn_remove.grid(row=9, column=2, sticky='ew', padx=5, pady=5)

listbox.grid(row=8, rowspan=5, columnspan=2, sticky='nsew', padx=5, pady=5)

btn_add_custom.grid(row=10, column=2, sticky='ew', padx=5, pady=5)
btn_run_custom.grid(row=11, column=2, sticky='ew', padx=5, pady=5)
btn_run_all_tests.grid(row=16, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

# bind the focus event to the function for both entries
ent_temp.bind('<Button-1>', clear_entry_on_click)
ent_duration.bind('<Button-1>', clear_entry_on_click)
add_placeholder(ent_temp, 'temperature in °C: ')  # ddd placeholder text
add_placeholder(ent_duration, 'duration in minutes: ')

# create & position the STOP button to span across all columns
btn_stop = tk.Button(frm_tests, text='STOP', command=emergency_stop, bg='red', fg='white')
btn_stop.grid(row=19, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

# create and position serial monitor readout lbl
lbl_monitor = tk.Label(frm_tests, text='arduino says things here', bg='#009FAF', fg='white', font='bold')
lbl_monitor.grid(row=20, column=0, columnspan=3, sticky='ew', padx=5, pady=5)


# position both frames
frm_tests.grid(row=0, column=0)

# set data reading from serial every 0.5 second
window.after(500, read_data)
window.after(1000, clear_out_custom)

window.mainloop()