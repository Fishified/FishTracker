# -*- coding: utf-8 -*-
"""
Created on Tue May 23 09:11:42 2017

@author: dugj2403
"""
import cv2
import os
import numpy as np
from PyQt4.QtGui import *


from PyQt4.QtGui import QFileDialog

class Calibration:
    
    def __init__(self,videoPath,cal_TE):

        self.videoPath=videoPath
        self.projectDirectory=os.path.dirname(self.videoPath)
        self.cal_TE=cal_TE
    
        try:
            os.makedirs('%s\\Calibration_files' % self.projectDirectory)
        except WindowsError:
            pass


    def doCalibration(self,rectify):
        self.cal_TE.append("Calibration window open:")
        self.rectify=rectify
        
        self.video=str(self.videoPath)
        self.camera = cv2.VideoCapture(self.video)
        success, firstFrame = self.camera.read() 

#        if check==True:

        if rectify==True:
            rows,cols,ch = firstFrame.shape
            firstFrame = cv2.warpAffine(firstFrame,self.M,(cols,rows))
                
        self.xdist=[]
        self.ydist=[]
        self.count = 0
        #mouse callback function, draws points and captures coordinates
        def draw_circle(event,x,y,flags,param):
            global ix,iy,count,xdist,ydist
        
            if event == cv2.EVENT_LBUTTONDOWN:
                cv2.circle(firstFrame,(x,y),2,(0,255,0),-1)
                cv2.circle(firstFrame,(x,y),10,(255,0,0),1)
                cv2.circle(firstFrame,(x,y),15,(255,0,0),1)
                cv2.putText(firstFrame, label, (x+20, y+20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                self.count=self.count+1
                
                ix=x
                iy=y
                self.xdist.append(ix)
                self.ydist.append(iy)
                self.cal_TE.append("Point %d chosen with x-pixel coordinates of %d and y-pixel coordinates of %d" % (self.count, ix, iy))
            
        cv2.namedWindow('Calibration frame')
        cv2.setMouseCallback('Calibration frame',draw_circle)

        while self.count <= 3:
            cv2.imshow('Calibration frame',firstFrame)

            if self.count==0:
                cv2.putText(firstFrame, "1. Place first point (1)", (10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Point 1"
                
            if self.count==1:
                cv2.putText(firstFrame, "2. Place second point (2)", (10, 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Point 2"
                
            if self.count==2:
                cv2.putText(firstFrame, "3. Place point of known distance from flume entrance and bottom wall", (10, 60),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Known point"
                
            if self.count==3:
                cv2.putText(firstFrame, "Exit pop-up and enter parameters ...", (10, 80),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            self.k = cv2.waitKey(1) & 0xFF
            if self.k == ord('q'):
                self.cal_TE.append("Enter calibration parameters and then click output calibration")
                cv2.camera.release()
                cv2.destroyAllwindows()

                
         
    def perspectiveTransform(self):

        self.video=str(self.videoPath)
        self.camera = cv2.VideoCapture(self.video)
        
        success, firstFrame = self.camera.read() #reads only the first image of the video for calibration function
        rows,cols,ch = firstFrame.shape
        self.xdist=[]
        self.ydist=[]
        self.pts1 = []
        self.pts2 = []
        self.count = 0
        #mouse callback function, draws points and captures coordinates
        def draw_circle(event,x,y,flags,param):
#            global ix,iy,count,xdist,ydist
        
            if event == cv2.EVENT_LBUTTONDOWN:
                
#                    break
                cv2.circle(firstFrame,(x,y),2,(0,255,0),-1)
                cv2.circle(firstFrame,(x,y),10,(255,0,0),1)
                cv2.circle(firstFrame,(x,y),15,(255,0,0),1)
                cv2.putText(firstFrame, label, (x+20, y+20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                ix=x
                iy=y
                self.xdist.append(ix)
                self.ydist.append(iy)
                a=[ix,iy]
                self.pts1.append(a)
                
                if self.count==0:
                    toAppend=[ix,iy]
                    self.pts2.append(toAppend)
                if self.count == 1:
                    toAppendix=ix
                    toAppendiy=self.pts2[0][1]
                    toAppend=[toAppendix,toAppendiy]
                    self.pts2.append(toAppend)
                if self.count == 2:
                    toAppendix=self.pts2[0][0]
                    toAppendiy=iy
                    toAppend=[toAppendix,toAppendiy]
                    self.pts2.append(toAppend)
                self.count=self.count+1
        
        cv2.namedWindow('firstframe')
        cv2.setMouseCallback('firstframe',draw_circle)
        
        while self.count <= 2:#keeps window open as long as count is less than 3 so user can interact with setMouseCallback
            cv2.imshow('firstframe',firstFrame)
            if self.count==0:
                cv2.putText(firstFrame, "1. Choose top left corner: (1)", (10, 20),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Point 1"
                
            if self.count==1:
                cv2.putText(firstFrame, "2. Choose top right corner:", (10, 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Point 2"
                
            if self.count==2:
                cv2.putText(firstFrame, "3. Choose bottom right corner", (10, 60),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                label="Point 3"
                
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                cv2.camera.release()
                cv2.destroyAllwindows()
                break
        if k == ord('q'):
            cv2.camera.release()
            cv2.destroyAllwindows()
            

        self.pts1 = np.float32(self.pts1)
        self.pts2 = np.float32(self.pts2)

        self.M = cv2.getAffineTransform(self.pts1,self.pts2)
        dst = cv2.warpAffine(firstFrame,self.M,(cols,rows))
        cv2.imshow('dst',dst)
        
        print self.M

    def outputCalFile(self,trialIndex,cameraID,distance2pnts,refDistance):
        self.trailIndex=trialIndex
        self.cameraID=cameraID
        self.distance2pnts=distance2pnts
        self.refDistance=refDistance
        
        self.trial=trialIndex
        self.cameraID=cameraID
        
        self.seperation = distance2pnts
        self.distance = refDistance
    
        deltax=float(self.seperation)/((self.xdist[0]-self.xdist[1])**2+(self.ydist[0]-self.ydist[1])**2)**0.5
        pixperdist=0.1/deltax
    
        self.cal_TE.append("O.k., each pixel equals %s meters in real life or 0.1 m equals %d pixels" % (deltax, pixperdist))
        self.cal_TE.append("Point 1 and 2 are %.2f m and %.2f m from the flume entrance" % (float(self.distance)+(self.xdist[2]-self.xdist[0])*deltax,float(self.distance)+(self.xdist[2]-self.xdist[1])*deltax))
        
        f = open('%s/Calibration_files/%d.cal' %(self.projectDirectory,float(self.cameraID)), 'w+') #opens file and allows it to be overwritten 
        print "hi"
                
        f.write(self.trial+'\n')
        f.write(self.cameraID+'\n')
        f.write(str(deltax)+'\n')
        f.write(str(self.distance)+'\n')
        f.write(str(self.xdist[2])+'\n')
        f.write(str(self.ydist[2])+'\n')
        f.close()
        
        self.cal_TE.append("Calibration file saved")
        
        
        #np.savetxt('%s/Calibration_files/%d_matrix.csv' %(self.path,float(self.cameraID)), self.M, delimiter=',')