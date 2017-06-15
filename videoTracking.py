# -*- coding: utf-8 -*-
"""
Created on Tue May 23 09:11:42 2017

@author: dugj2403
"""
import cv2

class VideoTracking():
    
    def __init__(self,refQtextEdit,refvideopath):
        self.myrefvideopath=refvideopath
        self.myrefQtextEdit=refQtextEdit
        self.myrefQtextEdit.append(self.myrefvideopath)
        
        
    def preview(self):
        cap = cv2.VideoCapture(self.myrefvideopath)
        self.myrefQtextEdit.append("Playing preview. Click video window and press 'q' or click 'Stop' button to cancel")
        while(True):
            (grabbed, frame) = cap.read()
            
            if not grabbed:
                break                 
            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            height, width = currentframe.shape[:2]
            
            cv2.namedWindow("Preview", cv2.WINDOW_NORMAL) 
            cv2.imshow("Preview",currentframe)  
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break  
        cap.release()
        cv2.destroyAllWindows()  
        
