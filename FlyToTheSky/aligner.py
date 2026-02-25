import cv2
import numpy as np

def downsample_match(large_image, small_image, ret):#, masked_big_image, masked_small_image):
    orig_big = large_image
    orig_small = small_image

    downscale_factor = 1/8
    large_image = cv2.resize(large_image, None, fx=downscale_factor, fy=downscale_factor)
    small_image = cv2.resize(small_image, None, fx=downscale_factor, fy=downscale_factor)


    large_gray = cv2.cvtColor(large_image, cv2.COLOR_BGR2GRAY)
    small_gray = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()

    keypoints_large, descriptors_large = sift.detectAndCompute(large_gray, None)
    keypoints_small, descriptors_small = sift.detectAndCompute(small_gray, None)

    bf = cv2.BFMatcher()

    matches = bf.knnMatch(descriptors_small, descriptors_large, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.99 * n.distance:
            good_matches.append(m)

    src_pts = np.float32([keypoints_small[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints_large[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    src_pts = src_pts*8
    dst_pts = dst_pts*8

    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)

    return M, mask