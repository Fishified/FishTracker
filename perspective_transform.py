# -*- coding: utf-8 -*-
"""
Created on Mon Jun 05 09:11:17 2017

@author: dugj2403
"""

import cv2
import os
import numpy as np
import matplotlib.pyplot as plt

camera = cv2.VideoCapture("14.mp4")
        
success, firstFrame = camera.read()

cv2.imwrite("firstFrame.png",firstFrame)

#img = cv2.imread('sudoku.png')
rows,cols,ch = firstFrame.shape
pts1 = np.float32([[56,65],[368,52],[28,387],[389,390]])
pts2 = np.float32([[0,0],[300,0],[0,300],[300,300]])
M = cv2.getPerspectiveTransform(pts1,pts2)
dst = cv2.warpPerspective(firstFrame,M,(300,300))
plt.subplot(121),plt.imshow(firstFrame),plt.title('Input')
plt.subplot(122),plt.imshow(dst),plt.title('Output')
plt.show()


pts2 = np.float32([[229,180],[465,180],[229,428]])
np.savetxt("matrix.csv", pts2,delimiter=',')