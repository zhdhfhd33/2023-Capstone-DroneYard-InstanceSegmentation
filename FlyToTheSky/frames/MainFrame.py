import tkinter as tk
from tkinter import ttk
from widgets.VerticalScrollFrame import VerticalScrollFrame
from PIL import ImageTk, Image
from widgets import CanvasImage

class MainFrame(ttk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.main_frame = None
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.place(x=165, y=0, width=1505, height=1080)
        
    def open(self, map_file_path, mask_file_path):
        if self.main_frame is not None:
            self.main_frame.destroy()
        self.main_frame = CanvasImage.CanvasImage(self, map_file_path, mask_file_path, self.parent.draw_data_lock)
        self.main_frame.grid(row=0, column=0)     

    def redraw(self):
        # self.main_frame.lock =True
        self.main_frame.redraw()
        # self.main_frame.lock =False