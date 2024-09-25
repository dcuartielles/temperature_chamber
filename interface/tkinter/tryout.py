import tkinter as tk
import serial
import time


#set temperature (user input)
def set_temp():
    
    temperature = ent_temp.get()

    if temperature.replace('.', '', 1).isdigit():
           lbl_monitor["text"] = f"{float(temperature):.2f} \N{DEGREE CELSIUS}"
    

    else:
           lbl_monitor["text"] = "digits only"


#read data from serial
def read_data():
      
      if ser and ser.is_open:
            try:
                send_command(ser, "SHOW DATA")  # Send command to request data
                time.sleep(1)  # Wait for Arduino to process the command

                response = ser.readline().decode('utf-8').strip()

                if response and "input available" not in response:
                    print(f"arduino responded: {response}")
                    lbl_monitor["text"] = "arduino responded: {response}"
                else:
                    print("received unexpected message or no valid data.")
                    lbl_monitor["text"] = "received unexpected message or no valid data."

            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                lbl_monitor["text"] = f"Error reading data: {e}"
            
            

#sends a command to arduino via serial      
def send_command(ser, command):     

        try:
            ser.reset_input_buffer() #clear the gates
            ser.write((command + '\n').encode('utf-8')) #encode command in serial
            print(f"sent command: {command}") #debug line
            time.sleep(1)   #small delay for command processing

        except serial.SerialException as e:
            print(f"error sending command: {e}")

        except Exception as e:
            print(f"unexpected error in sending command: {e}")

# set up serial communication
def serial_setup(port="COM13", baudrate=9600, timeout=5):          
            
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"connected to arduino port: {port}")
            #lbl_monitor["text"] = f"connected to arduino port: {port}"
            time.sleep(1)   #make sure arduino is ready
            return ser
        except serial.SerialException as e:
            print(f"error: {e}")
            #lbl_monitor["text"] = f"error: {e}"
            return None



#ser = serial.Serial("COM13", baudrate=9600, timeout=5)
ser = serial_setup()
window = tk.Tk()
window.title("temperature monitor")

window.rowconfigure(0, minsize=250, weight=1)
window.columnconfigure(1, minsize=800, weight=1)


lbl_monitor = tk.Label(window, text="arduino says things here")
frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_stop = tk.Button(master=frm_buttons, text="STOP THE OVEN")
btn_enter = tk.Button(master=frm_buttons, text="SET TEMPERATURE", command=set_temp)
ent_temp = tk.Entry(master=frm_buttons, width=30)


btn_stop.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_enter.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
ent_temp.grid(row=2, column=0, padx=5)

frm_buttons.grid(row=0, column=0, sticky="ns")
lbl_monitor.grid(row=0, column=1, sticky="nsew")

#set data reading from serial every 0.5 second
window.after(500, read_data)

window.mainloop()




'''
 # Initialize serial communication
        try:
            ser = serial.Serial("COM13", baudrate=9600, timeout=5)
            print("Connected to Arduino on COM13")
        except serial.SerialException as e:
            label.text = f"Serial Error: {e}"
            print(f"Serial Error: {e}")
        except PermissionError as pe:
            label.text = f"Permission Error: {pe}"
            print(f"Permission Error: {pe}")

while ser and ser.is_open:
            try:
                send_command("SHOW DATA")  # Send command to request data
                time.sleep(1)  # Wait for Arduino to process the command

                response = ser.readline().decode('utf-8').strip()
                if response and "input available" not in response:
                    print(f"Arduino responded: {response}")
                    Clock.schedule_once(lambda dt: update_label(response))
                else:
                    print("Received unexpected message or no valid data.")

            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                Clock.schedule_once(lambda dt: update_label(f"Error reading data: {e}"))
                break








from tkinter import tk
import serial

root = tk.Tk()
root.geometry("500x500")
ser = serial.Serial('COM10', 9600)

def foo(x,caller):
    ser.write(bytes(x, 'utf-8'))
    def bar():
        data = ser.readline()
        if caller == 'x': # If called by x
            xvalue.set(data) # Then write to x
        else:  
            yvalue.set(data) # Else write to y
    root.after(1,bar) # Same as 0.001s 

xv = '1'
yv = '2'

xvalue = tk.StringVar()
yvalue = tk.StringVar()

w = tk.Label(root, text="X").place(x=10, y=10)
w1 = tk.Label(root, text="Y").place(x=10, y=40)

display1 = tk.Entry(root, font=("Courier", 16), justify='right', textvariable=xvalue).place(x=50, y=10)
display2 = tk.Entry(root, font=("Courier", 16), justify='right', textvariable=yvalue).place(x=50, y=40)

# Call functions initially
foo(xv,'x')
foo(yv,'y')

root.mainloop()


from pyfirmata import Arduino, util
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import *
import time
import threading

board=Arduino('COM3')
iterator = util.Iterator(board)
iterator.start()
Tvl = board.get_pin('a:0:i')

class mclass(threading.Thread):
    def __init__(self,  window):
        threading.Thread.__init__(self)
        window = window
        box = Entry(window)
        box.pack ()
        button = Button (window, text="check", command=plot)
        button.pack()
        button2 = Button(window,text="stop", command=start_stop)
        button2.pack()
        w=Scale(window, from_=0, to=10000)
        w.pack()
        w2=Scale(window, from_=0, to=100000)
        w2.pack()
        t=[]
        v=[]
        ss=True
        fig = Figure(figsize=(6,6))
        a = fig.add_subplot(111)
        a.invert_yaxis()
        a.set_title ("Estimation Grid", fontsize=16)
        a.set_ylabel("Y", fontsize=14)
        a.set_xlabel("X", fontsize=14)
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=False)


    def plot (self):
        window.after(10, plot)
        if ss==True:
            v.append(Tvl.read())
            t.append(time.perf_counter())
            if t[0]<t[len(t)-1]-0.0001*w2.get():
                del v[0]
                del t[0]
            a.clear()
                a.set_ylim(Tvl.read()-0.0001*w.get(),Tvl.read()+0.0001*w.get())
            a.set_xlim(t[len(t)-1]-0.001*w2.get()+1,time.perf_counter())
            a.plot(t,v)
            canvas.draw()

    def start_stop(self):
        if ss==True:
            ss=False
        else:
            ss=True




window= Tk()
t= mclass(window)
t.start()
window.mainloop() 

'''