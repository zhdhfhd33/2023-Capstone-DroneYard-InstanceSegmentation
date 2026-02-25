from tkinter import ttk
from PIL import ImageTk, Image
from datetime import datetime

from frames.LeftFrame import LeftFrame
from frames.MainFrame import MainFrame
from frames.RightFrame import RightFrame

import Inferencer
import shutil

import tkinter as tk
import numpy as np
import logging
import os
import threading
import cv2
from aligner import *
import time

import multiprocessing

class ManagerApp(tk.Tk):
    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.manager = multiprocessing.Manager()

        self.init_state = True
        self.title("yard manager")
        self.minsize(width=1920, height=1080)
        self.resizable(False, False)
        
        self.left_frame = LeftFrame(self)
        self.main_frame = MainFrame(self)
        self.right_frame = RightFrame(self)

        self.data_dir = "./datas"
        self.current_map_name = None
        
        self.map_file_list = self.load_map_files()
        self.full_image = self.load_full_image()
        self.full_mask = self.load_masks()
        self.boundary = self.load_boundary()
        self.capacity = self.load_capacity_dict()
        
        self.log_queue = []
        self.log_queue_lock = threading.Lock()

        self.data_queue = dict()
        self.data_queue_lock = threading.Lock()
        self.queue_idx = 0


        self.yolo_weight = "./model_weight/bestDS.pt"
        self.sam_weight = "./model_weight/sam_vit_h.pth"
        self.inferencer = Inferencer.YOLAM(self.yolo_weight, self.sam_weight)

        self.queueing_init_state = True
        self.queueing_thread = threading.Thread(target=self.queueing_data)
        self.queueing_thread.daemon = True
        self.queueing_thread.start()

        self.infer_thread = threading.Thread(target=self.inference_datas)
        self.infer_thread.daemon = True
        self.infer_thread.start()

        self.draw_data_lock = False

        self.left_frame.display_maps(self.data_dir, self.map_file_list)
    
    def load_map_files(self):
        return os.listdir(os.path.join(self.data_dir, "full_maps"))
    def load_boundary(self):
        boundary = dict()
        for map_file in self.map_file_list:
            map_name = map_file[:-4]
            boundary[map_name] = cv2.imread(os.path.join(self.data_dir, "boundary", map_file))
        return boundary
    def load_masks(self):
        masks = dict()
        for map_file in self.map_file_list:
            map_name = map_file[:-4]
            try:
                masks[map_name] = cv2.imread(os.path.join(self.data_dir, "full_masks", map_file))
            except:
                masks[map_name] = np.zeros_like(self.full_image[map_name])
        return masks
    def load_full_image(self):
        full_image = dict()
        for map_file in self.map_file_list:
            map_name = map_file[:-4]
            full_image[map_name] = cv2.imread(os.path.join(self.data_dir, "full_maps", map_file))
        return full_image
    
    def load_capacity_dict(self):
        cap = dict()
        for file in self.map_file_list:
            cap[file[:-4]] = np.count_nonzero(self.full_mask[file[:-4]][:,:,1])/np.count_nonzero(self.boundary[file[:-4]][:,:,0])
        return cap
    
    def open(self, map_file):
        if self.draw_data_lock == True:
            return
        map_name = map_file[:-4]
        if (self.current_map_name != None) and (self.current_map_name == map_name): return
        map_file_path = os.path.join(self.data_dir, "full_maps", map_file)
        mask_file_path = os.path.join(self.data_dir, "full_masks", map_file)
        self.main_frame.open(map_file_path, mask_file_path)
        self.right_frame.open(self.data_queue[map_name], self.capacity[map_name])
        self.current_map_name = map_name
    def get_current_map_name(self):
        return self.current_map_name
    def get_data_dir(self):
        return self.data_dir
    def inference_datas(self):
        while True:
            time.sleep(0.1)
            prior_key = None
            image_file = None
            prior_value = 717823
            with self.data_queue_lock:
                for key in self.data_queue.keys():
                    if len(self.data_queue[key]) != 0:
                        image, value = self.data_queue[key][0]
                        if prior_value > value:
                            prior_key = key
                            image_file = image
                            prior_value = value
            
            if prior_key != None:
                image_file_path = os.path.join(self.data_dir, "queue_patch", prior_key, image_file)

                mask_big = self.full_mask[prior_key]
                try:
                    small_img = cv2.imread(image_file_path)
                except:
                    continue
                big_img = self.full_image[prior_key]

                M, mask = downsample_match(big_img, small_img, None)
                mask_small = self.inferencer.inference(image_file_path, None)

                transformed_small = cv2.warpPerspective(small_img, M, (big_img.shape[1], big_img.shape[0]))
                transformed_mask_small = cv2.warpPerspective(mask_small, M, (big_img.shape[1], big_img.shape[0]))
                transformed_small_gray = cv2.cvtColor(transformed_small, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(transformed_small_gray, 1, 255, cv2.THRESH_BINARY)
                mask_inv = cv2.bitwise_not(mask)
                large_image_with_overlay = cv2.bitwise_and(big_img, big_img, mask=mask_inv)
                matched_img = cv2.add(large_image_with_overlay, transformed_small)
                matched_mask = cv2.bitwise_or(mask_big, transformed_mask_small)
                ###
                
                # matched_img, matched_mask = downsample_match(big_img, small_img, mask_big, mask_small)
                
                matched_mask = np.bitwise_and(matched_mask, self.boundary[prior_key])

                cv2.imwrite(os.path.join(self.data_dir, "full_masks", prior_key+".jpg"), matched_mask)
                cv2.imwrite(os.path.join(self.data_dir, "full_maps", prior_key+".jpg"), matched_img)
                
                self.full_image[prior_key] = matched_img
                self.full_mask[prior_key] = matched_mask
                self.capacity[prior_key] = np.count_nonzero(matched_mask[:,:,1])/np.count_nonzero(self.boundary[prior_key][:,:,0])

                des_image_file_path = os.path.join(self.data_dir, "processed_patch", prior_key, image_file)
                shutil.move(image_file_path, des_image_file_path)
                
                
                self.data_queue[prior_key].pop(0)
                self.right_frame.remove_list(prior_key)
                self.queueing_log(0, "{}-processing done".format(image_file))

                if prior_key == self.current_map_name:
                    self.draw_data_lock = True
                    self.main_frame.redraw()
                    self.draw_data_lock = False

                    self.right_frame.update_capacity(round(self.capacity[prior_key], 3))

#### self.log_queue에 log 저장
    def queueing_data(self):
        while True:
            time.sleep(0.1)
            self.queue_idx = 0
            if self.queueing_init_state == True:
                self.queueing_init_state = False
                for map_file in self.map_file_list:
                    map_name = map_file[:-4]
                    datas = os.listdir(os.path.join(self.data_dir, "queue_patch", map_name))
                    idxes = range(self.queue_idx, self.queue_idx+len(datas))
                    self.queue_idx += len(datas)
                    if len(datas) == 0:
                        with self.data_queue_lock:
                            self.data_queue[map_name] = []
                    else:
                        with self.data_queue_lock:
                            self.data_queue[map_name] = [ [dt, i] for dt, i in zip(datas, idxes)]
                        ("init queue")
                self.queueing_log(0, "loading queue from the cache\n{} found".format(self.queue_idx))

            for map_file in self.map_file_list:
                map_name = map_file[:-4]
                datas = os.listdir(os.path.join(self.data_dir, "retrieved_patch", map_name))
                idxes = range(self.queue_idx, self.queue_idx+len(datas))
                self.queue_idx += len(datas)
                with self.data_queue_lock:
                    dt_list = [ [dt, i] for dt, i in zip(datas, idxes)]
                    self.data_queue[map_name] += dt_list
                    self.right_frame.append_list(dt_list, map_name)

                for data in datas:
                    shutil.move(os.path.join(self.data_dir, "retrieved_patch", map_name, data), 
                                os.path.join(self.data_dir, "queue_patch", map_name, data))
                    self.queueing_log(0, "retrieve-{}-{}".format(map_name, data))
     
    def queueing_log(self, levelnumber, text):
        levelnumber2levelstate = {
            0:"INFO",
            1:"WARN",
        }
        state = levelnumber2levelstate[levelnumber]
        time_stamp = datetime.now().strftime("%y.%m.%d %H:%M:%S")
        log = "[" +state + " - " + time_stamp + "]\n" +text+"\n\n"
        with self.log_queue_lock:
            self.log_queue.append(log)
####

    def update(self):
        #print("main.Manager.update call")
        while len(self.log_queue) != 0:
            with self.log_queue_lock:
                log = self.log_queue.pop(0)
                self.right_frame.write_log(log)
        self.after(100, self.update)

if __name__ == "__main__":

    app = ManagerApp(None)
    app.update()
    app.mainloop()