#imports
import tkinter as tk
from PIL import Image, ImageTk #for images
import serial
import time
import json
from tkinter.filedialog import askopenfilename, asksaveasfilename  #in case you want to use file finder
from interface_functionality import *
from json_handling import *
from serial_interaction import *


# global flag for stopping the reading process
is_stopped = False

###############        GUI PART       ###############

ser = serial_setup()

#initialize a new window
window = tk.Tk()
window.title("temperature chamber")
window.configure(bg="white")
window.wm_minsize(600, 750) # Minimum width of 650px and height of 800px

#prepare the general grid
window.columnconfigure(0, minsize=600, weight=1) #make sure gui is vertically centered 

'''
# Define global fonts for specific widgets
window.option_add("*Label.Font", ("Arial", 14, "bold"))  # Apply to all Label widgets
window.option_add("*Button.Font", ("Arial", 12, "bold"))  # Apply to all Button widgets
window.option_add("*Entry.Font", ("Arial", 12))          # Apply to all Entry widgets
'''

#monitor frame and content
frm_monitor = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")
lbl_monitor = tk.Label(frm_monitor, text="arduino says things here", width=70, bg="white")
lbl_room = tk.Label(frm_monitor, text="current temperature", bg="white")
lbl_r_temp = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_desired = tk.Label(frm_monitor, text="desired temperature", bg="white")
lbl_d_temp = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_heater = tk.Label(frm_monitor, text="heater", bg="white")
lbl_cooler = tk.Label(frm_monitor, text="cooler", bg="white")
lbl_heater_status = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")
lbl_cooler_status = tk.Label(frm_monitor, bd=1, width=45, relief="solid", bg="white")

#position update labels
lbl_room.grid(row=1, column=0, sticky="w", padx=5, pady=5)
lbl_r_temp.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_desired.grid(row=2, column=0, sticky="w", padx=5, pady=5)
lbl_d_temp.grid(row=2, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_heater.grid(row=3, column=0, sticky="w", padx=5, pady=5)
lbl_heater_status.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

lbl_cooler.grid(row=4, column=0, sticky="w", padx=5, pady=5)
lbl_cooler_status.grid(row=4, column=1, columnspan=2, sticky="w", padx=5, pady=5)

#position monitor label
lbl_monitor.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)


#test frame & content & logo
frm_tests = tk.Frame(window, borderwidth=1, highlightthickness=0, bg="white")

# path to logo file 
image_path = "C:/Users/owenk/OneDrive/Desktop/Arduino/temperature chamber/temperature_chamber/interface/tkinter/json-driven/arduino_logo.png"  
# use PIL to open the image
logo_image = Image.open(image_path)
logo_image = logo_image.resize((100, 100))  # adjust size
logo_photo = ImageTk.PhotoImage(logo_image)
#create  label for the image
lbl_image = tk.Label(frm_tests, image=logo_photo, bg="white")
lbl_image.image = logo_photo  # keep a reference to avoid garbage collection
lbl_image.grid(row=0, column=0, columnspan=3, sticky="nsew")  #position image

#benchmark test part
lbl_benchmark = tk.Label(frm_tests, text="BENCHMARK TESTS", bg="white")
btn_test1 = tk.Button(frm_tests, text="test 1", bg="white")
btn_test2 = tk.Button(frm_tests, text="test 2", bg="white")
btn_test3 = tk.Button(frm_tests, text="test 3", bg="white")
btn_run_all_benchmark = tk.Button(frm_tests, text="RUN ALL BENCHMARK TESTS", bg="white")
#custom test part
lbl_custom = tk.Label(frm_tests, text="CUSTOM TEST", bg="white")
lbl_d_temp = tk.Label(frm_tests, width=30, text="temperature in °C: ", bd=0.5, relief="solid", bg="white")
ent_temp = tk.Entry(frm_tests, width=30, justify='center', bg="white", fg="black")
lbl_d_duration = tk.Label(frm_tests, text="duration in minutes: ", bd=0.5, relief="solid", width=30, bg="white")
ent_duration = tk.Entry(frm_tests, width=30, justify='center', bg="white", fg="black")
btn_add_custom = tk.Button(frm_tests, text="ADD CUSTOM TEST", bg="white", command=add_custom)
btn_run_custom = tk.Button(frm_tests, text="RUN CUSTOM TEST", bg="white", command=run_custom)
#run all tests
btn_run_all_tests = tk.Button(frm_tests, text="RUN ALL TESTS", bg="white")
#running test display
lbl_running = tk.Label(frm_tests, text="TEST RUNNING: ", bg="white")
lbl_running_info = tk.Label(frm_tests, bd=0.5, relief="solid", bg="white")

#position labels, buttons and user input widgets in test frame
lbl_benchmark.grid(row=1, column=0, sticky="w", padx=5, pady=5)
btn_test1.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
btn_test2.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
btn_test3.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
btn_run_all_benchmark.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
lbl_custom.grid(row=6, column=0, sticky="w", padx=5, pady=5)
lbl_d_temp.grid(row=7, column=1, sticky="w", padx=5, pady=5)
ent_temp.grid(row=7, column=2, sticky="ew", padx=5, pady=5)
lbl_d_duration.grid(row=8, column=1, sticky="w", padx=5, pady=5)
ent_duration.grid(row=8, column=2, sticky="ew", padx=5, pady=5)
btn_add_custom.grid(row=9, column=1, sticky="ew", padx=5, pady=5)
btn_run_custom.grid(row=9, column=2, sticky="ew", padx=5, pady=5)
btn_run_all_tests.grid(row=11, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
lbl_running.grid(row=12, column=0, sticky="w", padx=5, pady=5)
lbl_running_info.grid(row=12, rowspan=3, column=1, columnspan=2, sticky="ew", padx=5, pady=10)

# bind the focus event to the function for both entries
ent_temp.bind("<Button-1>", clear_entry_on_click)
ent_duration.bind("<Button-1>", clear_entry_on_click)
add_placeholder(ent_temp, "temperature in °C: ")  # ddd placeholder text
add_placeholder(ent_duration, "duration in minutes: ")

# create & position the STOP button to span across both columns
btn_stop = tk.Button(frm_tests, text="STOP", command=emergency_stop, bg="red", fg="white")
btn_stop.grid(row=15, column=0, columnspan=3, sticky="ew", padx=5, pady=5)  # Button spans across two columns

#position both frames
frm_tests.grid(row=0, column=0)
frm_monitor.grid(row=1, column=0, padx=5, pady=20)

#set data reading from serial every 0.5 second
window.after(500, read_data)

window.mainloop()