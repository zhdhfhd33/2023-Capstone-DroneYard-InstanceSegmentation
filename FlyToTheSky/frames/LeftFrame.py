import tkinter as tk
from tkinter import ttk
from widgets.VerticalScrollFrame import VerticalScrollFrame
from PIL import ImageTk, Image
import os
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

class LeftFrame(ttk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.place(x=0, y=0, width=165, height=1080)
        self.parent = parent
        self.map_image_list = None
        self.main_frame = VerticalScrollFrame(self)     
        self.main_frame.place(x=0, y=0, width=165, height=1080)

    def display_maps(self, data_dir, map_file_list):
        self.map_image_list = [ cv2.imread(os.path.join(data_dir, "full_maps", map_file)) for map_file in map_file_list ]
        temp = []
        for map in self.map_image_list:
            small = np.array(Image.fromarray(cv2.cvtColor(map, cv2.COLOR_BGR2RGB)).resize((150, 150)))
            blur_img = np.empty_like(small)
            for i in range(3):
                blur_img[:,:,i] = gaussian_filter(small[:,:,i], 3)
            temp.append(ImageTk.PhotoImage(Image.fromarray(blur_img)))
            
#            temp.append(ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(blur_img, cv2.COLOR_BGR2RGB)).resize((150,150))))
        self.map_image_list = temp
#        self.map_image_list = [ ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(map, cv2.COLOR_BGR2RGB)).resize((150,150))) for map in self.map_image_list ]
        for map_file, map_image in zip(map_file_list, self.map_image_list):
            map_name = map_file[:-4]
            label = ttk.Label(self.main_frame.interior, image=map_image, compound='top', text=map_name)
            label.bind("<Button-1>", lambda e, map_file=map_file: self.parent.open(map_file))
            label.pack()