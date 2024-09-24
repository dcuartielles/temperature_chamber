import tkinter as tk
import tkinter.ttk as ttk


#change the message label text METHODS RIGHT UNDER IMPORTS
def sadly():
    message["text"] = "but she doesn't miss you"


#def handle_click(event):
#    print("but she doesn't miss you")


window = tk.Tk()
window.title("lila lee la")

window.rowconfigure(0, minsize=800, weight=1)
window.columnconfigure(1, minsize=800, weight=1)

frame_a = tk.Frame()
frame_b = tk.Frame()


#activates the function (print in terminal) when you click on the button
#butt.bind("<Button-1>", handle_click) 

text_box = tk.Text(master=frame_b)
text_box.pack(padx=5, pady=5)
text_box.insert("1.0", "\n\n\nit’s all \nelectrifying, and turns me into a bundle \nof selves that all grow forth, \nmesmerized by the way you perceive the world, \nthe way you purr some of that into my ear.")

text_box.insert(tk.END, "\n\nin today’s postcard i use the word.")


entry = tk.Entry(master=frame_a) #Entry widgets get only a SINGLE LINE
entry.pack(padx=5, pady=5)
entry.insert(0, 'you miss her')

butt = tk.Button(
  master=frame_a,
  text='august 2023',
  fg="white",  # Set the text color to white
  bg="#0DB498",  # Set the background color to arduino teal
  width=13, #width and height are measured in text units!!!
  #height=3
  command=sadly #trigger the sadly() method & change message text on click
  )
butt.pack(padx=5, pady=5)


message = tk.Label(
  master=frame_a,
  text='sweaty doodle, spongy smudge, \ni crawled up her stairs on my last feet: existential decay into blind crumbs bleeding. \nand she stood there in the open door, awaiting me in her \ncrisp white apron straight from a bath house in budapest, \npure function in the name of health. all smile and caress, she kissed, \nunwavering in her knowledge of what was left alive in the body she held. i\'ll draw you a bath, \nshe resolved, the glow in her eyes transmuted the question into a path \nmy heart sheepishly followed.',
  bg="white"
  )
message.pack(padx=5, pady=5)



'''entry.delete(0,4) 
#delete characters from input by index number (here: from 0 to 4): works like string slicing, i.e. NOT including the 2nd argument index. 

entry.delete(0, tk.END) #remove all chars from entry

secret = entry.get() #get access to the input text
secret'''

themed = ttk.Label(
  master=frame_a,
  text='there is a character to this relationship of making up for lost time.'
  )
themed.pack(padx=5, pady=5)

frame_a.pack(padx=5, pady=5) #you swap them, the whole layout is swapped, too!
frame_b.pack(padx=5, pady=5)

window.mainloop()

'''window = tk.Tk()

for i in range(3):

    window.columnconfigure(i, weight=1, minsize=75)
    window.rowconfigure(i, weight=1, minsize=50)

    for j in range(3):
        frame = tk.Frame(
            master=window,
            relief=tk.RAISED,
            borderwidth=1
        )
        #padding on the outside of each label & setting it top right
        frame.grid(row=i, column=j, padx=5, pady=5, sticky="ne")     
        
        label = tk.Label(master=frame, text=f"Row {i}\nColumn {j}")
        label.pack(padx=5, pady=5)

window.mainloop()

#The important thing to realize here is that even though .grid() is called on each Frame object, the #geometry manager applies to the window object. Similarly, the layout of each frame is controlled with #the .pack() geometry manager.
'''

'''border_effects = {
    "flat": tk.FLAT,
    "sunken": tk.SUNKEN,
    "raised": tk.RAISED,
    "groove": tk.GROOVE,
    "ridge": tk.RIDGE,
}

window = tk.Tk()

for relief_name, relief in border_effects.items():
    frame = tk.Frame(master=window, relief=relief, borderwidth=5)
    frame.pack(side=tk.LEFT)
    label = tk.Label(master=frame, text=relief_name)
    label.pack()

window.mainloop()'''

'''import tkinter as tk
from tkinter import *
from tkinter import ttk

class karl( Frame ):
    def __init__( self ):
        tk.Frame.__init__(self)
        self.pack()
        self.master.title("Karlos")
        self.button1 = Button( self, text = "CLICK HERE", width = 25,
                               command = self.new_window )
        self.button1.grid( row = 0, column = 1, columnspan = 2, sticky = W+E+N+S )
    def new_window(self):
        self.newWindow = karl2()
class karl2(Frame):     
    def __init__(self):
        new =tk.Frame.__init__(self)
        new = Toplevel(self)
        new.title("karlos More Window")
        new.button = tk.Button(  text = "PRESS TO CLOSE", width = 25,
                                 command = self.close_window )
        new.button.pack()
    def close_window(self):
        self.destroy()
def main(): 
    karl().mainloop()
if __name__ == '__main__':
    main()'''