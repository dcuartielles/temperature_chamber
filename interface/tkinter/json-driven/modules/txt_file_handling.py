# imports
import tkinter as tk
from PIL import Image, ImageTk  # for images
import serial
import time
import json
from tkinter import messagebox, Listbox
from tkinter.filedialog import askopenfilename, asksaveasfilename


# save listbox putput to a text file (for now)
def save_text_file():
    filepath = asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if not filepath:
        return
    with open(filepath, mode="w", encoding="utf-8") as output_file:
        text = listbox.get(0, tk.END)
        text_str = "\n".join(text)
        output_file.write(text_str)
