'''


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