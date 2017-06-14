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
        
#    def play_movie(self):
#        
#        self.framerate=int(self.trkFramerate_LE.text())
#        self.pathThrow, self.filename=os.path.split(os.path.abspath(self.video))
#        
#        self.cameraid=self.filename[0:2]
#        transfoMat=0
#        if self.trackRectify_CB.isChecked():
#            
#            for name in glob("%s\Calibration_files\*" % self.path):
#                a="%s\Calibration_files\\%s_matrix.csv" % (self.path,self.cameraid)
#                if name == a:
#                    print "do I go in here"
#                    transMatrix=np.genfromtxt('%s\Calibration_files\\%s_matrix.csv' % (self.path,self.cameraid),delimiter=',')
#            try:
#                print transMatrix
#                print "Transformation matrix found"
#                transfoMat=1
#            except NameError:
#                transfoMat=0
#            
#        self.vidstr=str(self.video)
#        self.cap = cv2.VideoCapture(self.vidstr)
#        self.fgbg=cv2.BackgroundSubtractorMOG()
#        
#        count = 0
#        xcoord=[]
#        ycoord=[]
#        cx=0
#        cy=0
#        r=20
#
#        while(True):
#            
#            if count==0:
#                self.track_TE.setText("Tracking. Click video window and press 'q' or click 'Stop' button to cancel")
#            if self.trkTrack_B.isChecked()== False:
#                self.scene.clear()
#                self.trkTrack_B.setText('Play')
#                break
#            else:
#                self.trkTrack_B.setText('Stop')
#                
#            (grabbed, frame) = self.cap.read()
#
#
#            if not grabbed:
#                
#                self.trkTrack_B.setChecked(False)
#                self.trkTrack_B.setText('Play')
#                self.track_TE.append("Tracking complete!")
#                break
#            
#            originalframe=frame
#            rows,cols,ch = frame.shape
#            
#            if transfoMat==1:
#                adjusted=cv2.warpAffine(frame,transMatrix,(cols,rows))
#                currentframe = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
#            else:
#                adjusted=frame
#                currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
##            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#            #fills in timestamp digits to prevent detection
#            if self.removeDigitsCheckBox.isChecked() == True:
#                currentframe[np.where((currentframe == [255,255,255]).all(axis = 2))] = [0,0,0]            
#            
#            #backgroundSubtractor
#            if self.backgroundCheckBox.isChecked() == True:
#                currentframe = self.fgbg.apply(currentframe)
#            
#            #median filter
#            medianFiltersize=int(self.medianSlider.value())
#            if medianFiltersize % 2 == 0:
#                    medianFiltersize=medianFiltersize +1
#            
#            if self.medianFilterCheckbox.isChecked() == True:
#                currentframe = cv2.medianBlur(currentframe,medianFiltersize)
#            
#            #kernel size
#            kernelsize=int(self.kernelSlider.value())
#            if kernelsize % 2 == 0:
#                    kernelsize=kernelsize +1
#            kernel = np.ones((kernelsize,kernelsize),np.uint8)
#            
#            #erode and dilate
#            if self.erodeCheckbox.isChecked() == True:
#                currentframe = cv2.erode(currentframe,kernel,iterations=1)
#            if self.dilateCheckbox.isChecked() == True:
#                currentframe = cv2.dilate(currentframe,kernel,iterations=1)
#
#            #pass Gaussian filter
#            if self.gaussCheckBox.isChecked() == True:
#                self.gauss=int(self.gaussSlider.value())
#                if self.gauss % 2 == 0:
#                    self.gauss=self.gauss +1
#                currentframe = cv2.GaussianBlur(currentframe, (self.gauss,self.gauss), 0)
#            try:
#                cntareathreshold=self.cntareathreshold
#            except AttributeError:
#                cntareathreshold=100
#            
#            #-------------------------------------
#            #--------------Tracking---------------
#            #-------------------------------------
#            (cnts, _) = cv2.findContours(currentframe.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
#        
#            cntarea=[0]
#            xcntcoord=[0]
#            ycntcoord=[0]
#            for c in cnts:
#                if cv2.contourArea(c) < cntareathreshold:
#                    continue
#                cntarea.append(cv2.contourArea(c))
#                (x, y, w, h) = cv2.boundingRect(c)
#        
#                M = cv2.moments(c)
#                cx = int(M['m10']/M['m00'])
#                cy = int(M['m01']/M['m00'])
#        
#                xcntcoord.append(cx)
#                ycntcoord.append(cy)
#                self.track_TE.append("coutour area: %d" % float(cv2.contourArea(c)))
#        
#            biggestcontour=cntarea.index(max(cntarea))
#            xcoord.append(xcntcoord[biggestcontour])
#            ycoord.append(ycntcoord[biggestcontour])
#            
#            if xcntcoord[biggestcontour]==0:
#                pass
#            else:
#                cv2.circle(originalframe, (xcntcoord[biggestcontour], ycntcoord[biggestcontour]),r,(0, 255, 0), 3)
#                
#            self.fishcoords=np.array((xcoord,ycoord),dtype=float) 
#             
#            for i in range(len(xcoord)):
#                if xcoord[i]==0:
#                    pass
#                else:
#                    cv2.circle(adjusted, (xcoord[i], ycoord[i]),6, (0, 0, 255),thickness=-1)
#                    if i == len(xcoord)-1:
#                        self.track_TE.append("Detection on frame: %d" % count)
#                        
#            
#            cv2.namedWindow("Background removed", cv2.WINDOW_NORMAL) 
#            cv2.imshow("Background removed",currentframe)               
#            cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL) 
#            cv2.imshow("Tracking",adjusted)   
#            
#            #variables used to increase/decrease video playback speed
#            self.vidSpeedMultiplier=int(self.playbackSlider.value())
#            self.framerate=float(self.framerate)
#            a=(1/self.framerate)*(100/(self.vidSpeedMultiplier))
#            
#            
#            time.sleep(a)
#                #breaks out 
#            if cv2.waitKey(1) & 0xFF == ord('q'):
#                self.trkTrack_B.setChecked(False)
#                self.trkTrack_B.setText('Play')
#                break
#            count = count +1
#            
#        self.cap.release()
#        cv2.destroyAllWindows()
#        
#        self.fishcoords=np.transpose(self.fishcoords)
#        self.fishcoords=pd.DataFrame(self.fishcoords)
#        self.fishcoords.to_csv("%s\\%s_raw.csv" %(self.path,self.cameraid))
       