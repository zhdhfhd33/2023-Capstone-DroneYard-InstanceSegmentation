from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor
import os
import numpy as np
import torch
import cv2
from scipy import ndimage

class YOLAM():

    def __init__(self, detector_path, segmentor_path, bboxsize=25):
        self.bboxsize=25
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else 'cpu')
        self.Detector = YOLO(detector_path)
        self.Detector.info(False, False)
        self.Segmentor = sam_model_registry["vit_h"](checkpoint=segmentor_path).to(device=self.device)
        self.Segmentor = SamPredictor(self.Segmentor)
        
    def inference(self, image_path, infer_ret):
        boxes = self.Detector(image_path)[0].boxes

        img = cv2.imread(image_path)
        self.Segmentor.set_image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        box_list = np.array(boxes.xyxy.cpu())
        box_list[:, :2] -= self.bboxsize
        box_list[:, 2:] += self.bboxsize
        box_list = torch.tensor(box_list).to(self.device)

        cls_list = (boxes.cls > 0).cpu()

        transformed_boxes = self.Segmentor.transform.apply_boxes_torch(box_list, img.shape[:2])
        if transformed_boxes.shape[0] == 0:
            return img

        masks, _, _ = self.Segmentor.predict_torch(
            point_coords=None,
            point_labels=None,
            boxes=transformed_boxes,
            multimask_output=False)
        
        class0_index = np.where(~cls_list)[0]
        class1_index = np.where(cls_list)[0]

        class0_mask = masks[class0_index].sum(dim=0, keepdim=True).squeeze(dim=0).permute(1,2,0)
        class1_mask = masks[class1_index].sum(dim=0, keepdim=True).squeeze(dim=0).permute(1,2,0)

        class0_mask = class0_mask.cpu().numpy()[:,:,0]
        class1_mask = class1_mask.cpu().numpy()[:,:,0]

        combined_mask = np.logical_or(class0_mask, class1_mask)

        combined_mask = edge_remove(combined_mask)
        combined_mask = combined_mask * 255


        overlay = np.zeros_like(img, "uint8")
        overlay[:,:,1] = combined_mask.astype(np.uint8)

        #masked_img = cv2.addWeighted(img, 1, overlay, 0.7, 0)

        #infer_ret['mask'] = overlay
        return overlay


if __name__ == "__main__":

    yolo_weight = "./model_weight/bestDS.pt"
    sam_weight = "./model_weight/sam_vit_h.pth"
    test_image = r"C:\Users\yuilhae\yuilhaePNU\graduation\yard_manage_program\DJI_20230503104636_0008_W.JPG"

    yolam = YOLAM(yolo_weight, sam_weight)
    masked_image = yolam.inference()
    cv2.imshow("inference test", test_image)
    

def edge_remove(array):
    # Label connected components
    labeled_array, num_features = ndimage.label(array)

    # Find the labels connected to the edge
    edge_labels = set(
        labeled_array[10, :].tolist() +        # Top edge
        labeled_array[-10, :].tolist() +       # Bottom edge
        labeled_array[:, 10].tolist() +        # Left edge
        labeled_array[:, -10].tolist()         # Right edge
    )

    # Remove segments connected to the edge
    for label in edge_labels:
        if label > 0:
            labeled_array[labeled_array == label] = 0

    # The result is the modified labeled array with edge-connected segments removed
    result_array = (labeled_array > 0)

    return result_array