import tkinter as tk


def get_temp():
    
    temperature = ent_temp.get()

    if temperature.replace('.', '', 1).isdigit():
           lbl_monitor["text"] = f"{float(temperature):.2f} \N{DEGREE CELSIUS}"
    

    else:
           lbl_monitor["text"] = "digits only"
    


window = tk.Tk()
window.title("temperature monitor")

window.rowconfigure(0, minsize=250, weight=1)
window.columnconfigure(1, minsize=800, weight=1)


lbl_monitor = tk.Label(window, text="arduino says things here")
frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_stop = tk.Button(master=frm_buttons, text="STOP THE OVEN")
btn_enter = tk.Button(master=frm_buttons, text="SET TEMPERATURE", command=get_temp)
ent_temp = tk.Entry(master=frm_buttons, width=30)


btn_stop.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_enter.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
ent_temp.grid(row=2, column=0, padx=5)

frm_buttons.grid(row=0, column=0, sticky="ns")
lbl_monitor.grid(row=0, column=1, sticky="nsew")

window.mainloop()
