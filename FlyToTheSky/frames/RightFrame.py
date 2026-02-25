import tkinter as tk
from tkinter import ttk
import os
from PIL import ImageTk, Image
import time
from tkinter import scrolledtext


class RightFrame(ttk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)     
        self.parent = parent

        self.data_list_title = ttk.Label(self, text="Data Queue", font="Helvetica 10 bold", anchor='s')
        self.data_list_title.place(x=10, y=0, width=230, height=25)

        self.data_list = tk.Listbox(self)
        self.data_list.bind("<<ListboxSelect>>", lambda e: self.show_data())
        self.data_list.place(x=10, y=25, width=230, height=225)

        self.sample_viewer_title = ttk.Label(self, text="Sample Viewer", font="Helvetica 10 bold", anchor='s')
        self.sample_viewer_title.place(x=10, y=250, width=230, height=25)

        self.sample_viewer = tk.Canvas(self, width=230, height=180, highlightthickness=1, highlightbackground="black")
        self.sample_viewer.place(x=10, y=275, width=230, height=180)

        self.log_title = ttk.Label(self, text="Log", font="Helvetica 10 bold", anchor='s')
        self.log_title.place(x=10, y=455, width=230, height=25)

        self.log = scrolledtext.ScrolledText(self)
        self.log.place(x=10, y=480, width=230, height=500)
        self.log.config(state="disabled")

        self.capacity_title = ttk.Label(self, text="Capacity", font="Helvetica 10 bold", anchor='s')
        self.capacity_title.place(x=10, y=980, width=230, height=35)
        self.capacity = ttk.Label(self, text="0.0", anchor='s')
        self.capacity.place(x=10, y=1015, width=230, height=35)
        
        self.place(x=1670, y=0, width=250, height=1080)

    def open(self, data_list, capacity):
        self.data_list.delete(0,tk.END)
        for idx, item in enumerate(data_list):
            self.data_list.insert(idx, item[0])
        self.sample_viewer.delete("all")
        self.update_capacity(round(capacity, 3))

    def append_list(self, data_list, map_name):
        if self.parent.get_current_map_name() != map_name:
            return
        cur_idx = self.data_list.size()
        for item in data_list:
            self.data_list.insert(cur_idx, item[0])

    def remove_list(self, map_name):
        if self.parent.get_current_map_name() != map_name:
            return
        self.data_list.delete(0)
    
    def write_log(self, log):
#        print("main.rightframe.write_log")
        self.log.config(state="normal")
        self.log.insert("1.0", log) #("current", log)
        self.log.config(state="disabled")

    def update_capacity(self, value):
        self.capacity.configure(text=str(value))

    def show_data(self):
        map_name = self.parent.get_current_map_name()
        data_dir = self.parent.get_data_dir()

        idx = self.data_list.curselection()
        if idx:
            data_file = self.data_list.get(idx)
            try:
                img=Image.open(os.path.join(data_dir, "queue_patch", map_name, data_file)).resize((230,180))
            except:
                return
            img = ImageTk.PhotoImage(img)
            self.sample_viewer.delete("all")
            self.sample_viewer.create_image(0, 0, anchor=tk.NW, image = img)
            self.sample_viewer.image_names=img

        