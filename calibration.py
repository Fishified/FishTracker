# -*- coding: utf-8 -*-
"""
Created on Tue May 23 09:11:42 2017

@author: dugj2403
"""
import cv2
import os


from PyQt4.QtGui import QFileDialog

class Calibration:
    
    def __init__(self,refcal_TE,refcalVideo_L,reftrialIndex_LE,refcameraID_LE,refdistance2pnts_LE,refrefDistance_LE,refpath):
        self.myrefcalVideo_L=refcalVideo_L
        self.myreftrialIndex_LE=reftrialIndex_LE
        self.myrefcameraID_LE=refcameraID_LE
        self.myrefdistance2pnts_LE=refdistance2pnts_LE
        self.myrefrefDistance_LE=refrefDistance_LE
        self.myrefcal_TE=refcal_TE
        self.refpath=refpath
        
    def openCalibration(self,fileobject):
        self.fileobject=fileobject
        self.myrefcalVideo_L.setText(self.fileobject)
        self.calibrationvideo=self.fileobject
        
        if not os.path.exists('%s\\Calibration_files' % self.refpath):
            os.makedirs('%s\\Calibration_files' % self.refpath)
            
    def doCalibration(self):

        self.video=str(self.calibrationvideo)
        self.camera = cv2.VideoCapture(self.video)
        
        success, firstFrame = self.camera.read() #reads only the first image of the video for calibration function
        
        self.xdist=[]
        self.ydist=[]
        self.count = 0
        #mouse callback function, draws points and captures coordinates
        def draw_circle(event,x,y,flags,param):
#            global ix,iy,count,xdist,ydist
        
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
        
        cv2.namedWindow('firstframe')
        cv2.setMouseCallback('firstframe',draw_circle)
        
        while self.count <= 3:#keeps window open as long as count is less than 3 so user can interact with setMouseCallback
            cv2.imshow('firstframe',firstFrame)
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
                cv2.putText(firstFrame, "Press 'q' to quit and enter parameters...", (10, 80),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                cv2.destroyAllWindows()
                break
            
    def outputCalFile(self):
          
        trial=self.myreftrialIndex_LE.text()
        cameraID=self.myrefcameraID_LE.text()
        
        seperation = self.myrefdistance2pnts_LE.text()
        distance = self.myrefrefDistance_LE.text()
        
        deltax=float(seperation)/((self.xdist[0]-self.xdist[1])**2+(self.ydist[0]-self.ydist[1])**2)**0.5
        pixperdist=0.1/deltax
        
        self.myrefcal_TE.append("O.k., each pixel equals %s meters in real life or 0.1 m equals %d pixels" % (deltax, pixperdist))
        self.myrefcal_TE.append("Point 1 and 2 are %.2f m and %.2f m from the flume entrance" % (float(distance)+(self.xdist[2]-self.xdist[0])*deltax,float(distance)+(self.xdist[2]-self.xdist[1])*deltax))
        
        f = open('%s/Calibration_files/%d.cal' %(self.refpath,float(cameraID)), 'w+') #opens file and allows it to be overwritten 
        f.write(trial+'\n')
        f.write(cameraID+'\n')
        f.write(str(deltax)+'\n')
        f.write(str(distance)+'\n')
        f.write(str(self.xdist[2])+'\n')
        f.write(str(self.ydist[2])+'\n')
        f.close()