from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QFileDialog
from functools import partial 
import sys
import cv2
import time
import imutils
import numpy as np
import pandas as pd
import tracker_ui
import os
import temp
from pandas.sandbox.qtpandas import DataFrameModel, DataFrameWidget

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


def appendAnything(self, app):
    app.textEdit.append("test")

class MainWindow(QMainWindow, tracker_ui.Ui_MainWindow):
    

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        
        self.scene=QGraphicsScene()
        self.scene2=QGraphicsScene()
        self.cameralist=[]
        self.trackButton.clicked.connect(self.play_movie)
        self.loadButton.clicked.connect(self.open)
        self.previewButton.clicked.connect(self.preview)
        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        self.kernelSlider.valueChanged.connect(self.kernelSliderChange)
        
        self.contourButton.clicked.connect(self.contour)
        self.loadcalibrateButton.clicked.connect(self.opencalibration)
        self.calibrateButton.clicked.connect(self.calibration)
        self.stitchButton.clicked.connect(self.stitch)
        self.stitchDirectoryButton.clicked.connect(self.openstitch)
        self.populatecameraslineEdit.returnPressed.connect(self.populatecameralist)
        
        try:
            self.reloadButton.clicked.connect(lambda: self.output(self.rawcoordinates, self.signalemission))
        except AttributeError:
            pass
        
    def populatecameralist(self):
        self.cameralist.append(self.populatecameraslineEdit.text())
        self.populatecameraslineEdit.clear()
    def gaussSliderChange(self):
        self.gaussValueLabel.setText(str(self.gaussSlider.value()))
    def medianSliderChange(self):
        self.medianValueLabel.setText(str(self.medianSlider.value()))
    def kernelSliderChange(self):
        self.kernelValueLabel.setText(str(self.kernelSlider.value()))


        
    def play_movie(self):
        path, filename=os.path.split(os.path.abspath(self.video))
        path='%s\\'%path
        cameraID=int(self.cameraIdLineEdit.text())
        try:
            tag=int(path[-15:-3])                     #extract tag number from path
            attempt=int(path[-2])
            trial=int(path[-17])
        except ValueError:
            tag=None
            attempt=None
            trial=None

        
        self.framerate=int(self.frameratelineEdit.text())
        self.label_3.setText(self.video)
        

#        treatedfishcoords=kn.kinematics(fishcoords,crop,cropstart,cropend,interpolate,framerate,rollingperiods,path,trial,tag,attempt)
        tree=str(self.video)
        cap = cv2.VideoCapture(tree)
        fgbg=cv2.BackgroundSubtractorMOG()
        
        count = 0
#        xdist=[]
#        ydist=[]
#        ix,iy=-1,-1
#        firstFrame = None
#        counter=0
        xcoord=[]
        ycoord=[]
        cx=0
        cy=0
        r=20

        while(True):
            if count==0:
                self.textEdit.setText("Tracking. Click video window and press 'q' or click 'Stop' button to cancel")
            if self.trackButton.isChecked()== False:
                self.scene.clear()
                self.trackButton.setText('Play')
                break
            else:
                self.trackButton.setText('Stop')
                
            (grabbed, frame) = cap.read()
            originalframe=frame
            
            if not grabbed:
                self.trackButton.setChecked(False)
                self.trackButton.setText('Play')
                self.textEdit.append("Tracking complete or program not able to grab video ... could be a format error. Check file type and try again.")
                break           
            
            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#            currentframe = imutils.resize(currentframe, width=800)
            
            #fills in timestamp digits to prevent detection
            if self.removeDigitsCheckBox.isChecked() == True:
                currentframe[np.where((currentframe == [255,255,255]).all(axis = 2))] = [0,0,0]            
            
            #backgroundSubtractor
            if self.backgroundCheckBox.isChecked() == True:
                currentframe = fgbg.apply(currentframe)
            
            #median filter
            medianFiltersize=int(self.medianSlider.value())
            if medianFiltersize % 2 == 0:
                    medianFiltersize=medianFiltersize +1
            
            if self.medianFilterCheckbox.isChecked() == True:
                currentframe = cv2.medianBlur(currentframe,medianFiltersize)
            
            #kernel size
            kernelsize=int(self.kernelSlider.value())
            if kernelsize % 2 == 0:
                    kernelsize=kernelsize +1
            kernel = np.ones((kernelsize,kernelsize),np.uint8)
            
            #erode and dilate
            if self.erodeCheckbox.isChecked() == True:
                currentframe = cv2.erode(currentframe,kernel,iterations=1)
            if self.dilateCheckbox.isChecked() == True:
                currentframe = cv2.dilate(currentframe,kernel,iterations=1)

            #pass Gaussian filter
            if self.gaussCheckBox.isChecked() == True:
                self.gauss=int(self.gaussSlider.value())
                if self.gauss % 2 == 0:
                    self.gauss=self.gauss +1
                currentframe = cv2.GaussianBlur(currentframe, (self.gauss,self.gauss), 0)
            try:
                cntareathreshold=self.cntareathreshold
            except AttributeError:
                cntareathreshold=100
            
            #-------------------------------------
            #--------------Tracking---------------
            #-------------------------------------
            (cnts, _) = cv2.findContours(currentframe.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        
            cntarea=[0]
            xcntcoord=[0]
            ycntcoord=[0]
            for c in cnts:
                if cv2.contourArea(c) < cntareathreshold:# Defense 1
                    continue
                cntarea.append(cv2.contourArea(c))
                (x, y, w, h) = cv2.boundingRect(c)
        
                M = cv2.moments(c)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
        
                xcntcoord.append(cx)
                ycntcoord.append(cy)
        
            biggestcontour=cntarea.index(max(cntarea))#almost always the fish, this is where glare can cause problems if the biggest contour is bigger than the fish's contour
            xcoord.append(xcntcoord[biggestcontour])
            ycoord.append(ycntcoord[biggestcontour])
            
            if xcntcoord[biggestcontour]==0:
                pass
            else:
                cv2.circle(originalframe, (xcntcoord[biggestcontour], ycntcoord[biggestcontour]),r,(0, 255, 0), 3)
                
            fishcoords=np.array((xcoord,ycoord),dtype=float) #attributes coordinates of largest contour to fish coordinates
             
            for i in range(len(xcoord)):
                if xcoord[i]==0:
                    pass
                else:
                    cv2.circle(originalframe, (xcoord[i], ycoord[i]),6, (0, 0, 255),thickness=-1)
                    if i == len(xcoord)-1:
                        self.textEdit.append("Detection on frame: %d" % count)
                

            if self.novidCheckBox.isChecked()==False:
                #time.sleep(0.00001)
                cv2.namedWindow("Background removed", cv2.WINDOW_NORMAL) 
                cv2.imshow("Background removed",currentframe)               
                cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL) 
                cv2.imshow("Tracking",originalframe)   
            
            #variables used to increase/decrease video playback speed
            self.vidSpeedMultiplier=int(self.playbackSlider.value())
            self.framerate=float(self.framerate)
            a=(1/self.framerate)*(100/(self.vidSpeedMultiplier))
            
            if self.novidCheckBox.isChecked()==False:
                time.sleep(a)
                #breaks out 
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.trackButton.setChecked(False)
                    self.trackButton.setText('Play')
                    self.textEdit.setText('')
                    break
            count = count +1
            
        cap.release()
        cv2.destroyAllWindows()
        

        
        fishcoords=np.transpose(fishcoords)
        fishcoords=pd.DataFrame(fishcoords)
        fishcoords.to_csv("%s%s_raw.csv" %(path,cameraID))
        
        self.rawDataTable.setColumnCount(len(fishcoords.columns))
        self.rawDataTable.setRowCount(len(fishcoords.index))
        for i in range(len(fishcoords.index)):
            for j in range(len(fishcoords.columns)):
                self.rawDataTable.setItem(i,j,QTableWidgetItem(str(fishcoords.iget_value(i, j))))
        
        self.rawcoordinates=fishcoords.as_matrix()
        self.signalemission=1
        if self.outputCheckBox.isChecked()==True:
            self.output(self.rawcoordinates, self.signalemission)
        
    
#        """
#        Erroneous data approaches:
#        
#        Spurious data mostly results from surface glare causing movement contours with roughly the same surface area (pixels)
#        as the size of the fish. The first approach (1) against spuriuos data is to vary cntareathreshold (defined at top) to try and eliminate small erroneous contours.
#        Usually this is a good approach, especially if the fish is large and you have low glare on the surface. Nevertheless, there are some erroneous
#        contours that leak in. So I came up with approaches 2 and 3 to deal further with these. Approach (2) checks detected coordinates to see if they are
#        alone (i.e. the rows above and below are zero), if they are alone then they get taken out. Defense (3) calculates a 2 period rolling standard deviation
#        (rSTD) over the xCoord key. By default the rSTD threshold is 200, this helps remove groups of two or three spurious detections. The downside is that 
#        the first row of good data in a block is lost becuase it will inevitably have a rSTD > 200. A small price to pay for good data. 
#        """
            
        first=className.className()#create instance of className called 'first'
        first.createName('bucky') #create a name using the createName method available in className
        self.textEdit.append(first.name) #output first's name to the text console
        
    def output(self,x,y):
        
        fishcoords=pd.DataFrame(self.rawcoordinates)
        
        self.framerate=int(self.frameratelineEdit.text())
        framerate=self.framerate
        
        if self.signalemission==1:
            path, filename=os.path.split(os.path.abspath(self.video))
            path='%s\\'%path
            
        if self.signalemission==2:
            path=str(self.stitchdirectory)
            path='%s\\'%path   
 
        crop=None
        cropstart=None
        cropend=None
        
        if self.cropCheckBox.isChecked()==True:
            crop='yes'
            cropstart=int(self.cropstartLineEdit.text())
            cropend=int(self.cropendLineEdit.text())
            
        interpolate=None
        
        if self.interpolateCheckBox.isChecked()==True:
            interpolate='yes'
            
        rollingperiods=int(self.maLineEdit.text())        
        
        try:
            tag=int(path[-15:-3])                     #extract tag number from path
            attempt=int(path[-2])
            trial=int(path[-17])
        except ValueError:
            tag=None
            attempt=None
            trial=None

        def georeferencex(xpixel):
            return calibration[3]+(calibration[4]-xpixel)*calibration[2]
        def georeferencey(ypixel):
            return (calibration[5]-ypixel)*calibration[2]
 
 
        if self.signalemission ==1:
            cameraID=int(self.cameraIdLineEdit.text())
            calibration=np.genfromtxt('./Calibration_Files/trial1_camera%d.cal'% cameraID)

        if self.removelonersCheckBox.isChecked()==True:
            npfishcoords=fishcoords.as_matrix()
            for i in range(len(npfishcoords)):
                try:
                    if npfishcoords[i,0]==0 and npfishcoords[i+1,0]!=0 and npfishcoords[i+2,0]==0:
                        npfishcoords[i+1,0]=0
                        npfishcoords[i+1,1]=0
                except IndexError:
                    break
            fishcoords=pd.DataFrame(npfishcoords)
            
        if self.signalemission == 1:    
            fishcoords.columns = ['xpixel','ypixel']
            fishcoords['xCoord']=fishcoords.apply(lambda row: georeferencex(row['xpixel']), axis=1)
            fishcoords['yCoord']=fishcoords.apply(lambda row: georeferencey(row['ypixel']), axis=1)
            fishcoords['Tag']=tag
            fishcoords['Attempt']=attempt
            fishcoords['Trial']=trial
        else:
            pass
        
        if self.rSTDCheckBox.isChecked()==True:
            rSTDperiods=int(self.rstd_periods_LineEdit.text())
            rSTD_threshold=int(self.rstd_threshold_LineEdit.text())
            fishcoords['rSTD']=pd.rolling_std(fishcoords['xpixel'],rSTDperiods)
            fishcoords.ix[fishcoords['rSTD']>rSTD_threshold,('xpixel','ypixel','xCoord','yCoord')]=None
#            npfishcoords=fishcoords.as_matrix()
#            for i in range(len(npfishcoords)):
#                try:
#                    if npfishcoords[i,0]==0 and npfishcoords[i+1,0]!=0 and npfishcoords[i+2,0]==0:
#                        npfishcoords[i+1,0]=0
#                        npfishcoords[i+1,1]=0
#                except IndexError:
#                    break
#            fishcoords=pd.DataFrame(npfishcoords)

        if self.signalemission ==1:
            fishcoords.ix[fishcoords.xpixel==0,('xCoord','yCoord','xpixel','ypixel')]=None
        
        if self.signalemission==1:
            fishcoords.to_csv("%s%s_raw.csv" %(path,cameraID))#used in stitch.py
        if self.signalemission==2:
            fishcoords.columns=['Attempt','Tag','Trial','xCoord','xpixel','yCoord','ypixel']
            fishcoords.to_csv("%s%s_raw_stitched.csv" %(path,attempt))#used in stitch.py
        self.df=kinematics(fishcoords,crop,cropstart,cropend,interpolate,framerate,rollingperiods,path,trial,tag,attempt).get_dataFrame()
#            treatedfishcoords=treatedfishcoords.df
        if self.signalemission==1:
            self.df.to_csv("%s%d_%d_%d_%d_kin.csv" %(path,trial,tag,cameraID,attempt))
        if self.signalemission==2:
            self.df.to_csv("%s%d_%d_%d_stitched.csv" %(path,trial,tag,attempt))
        
        self.treatedDataTable.setColumnCount(len(self.df.columns))
        self.treatedDataTable.setRowCount(len(self.df.index))
        for i in range(len(self.df.index)):
            for j in range(len(self.df.columns)):
                self.treatedDataTable.setItem(i,j,QTableWidgetItem(str(self.df.iget_value(i, j))))
        self.scene.clear()
        self.scene.addPixmap(QPixmap('%sstitch.jpg'% path))
        self.scene.update()
        self.graphicsView.setScene(self.scene)
        
    def preview(self):
        cap = cv2.VideoCapture(self.video)
        
        while(True):
            (grabbed, frame) = cap.read()
            
            if not grabbed:
                break                 
            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            height, width = currentframe.shape[:2]
            
            cv2.namedWindow("Preview", cv2.WINDOW_NORMAL) 
            cv2.imshow("Preview",currentframe)  
            self.textEdit.setText("Playing preview. Click video window and press 'q' or click 'Stop' button to cancel")
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break  
        cap.release()
        cv2.destroyAllWindows()
        
    def open(self):
        fileobj=QFileDialog.getOpenFileName(self)# 'Open Video File', '', None, QFileDialog.DontUseNativeDialog)
        
        self.pathLabel.setText(fileobj)
        self.video=fileobj
        
    def opencalibration(self):
        fileobj=QFileDialog.getOpenFileName(self) #'Open Video File', '', None, QFileDialog.DontUseNativeDialog)
        
        self.pathLabel.setText(fileobj)
        self.calibrationvideo=fileobj
    
    def openstitch(self):
        fileobj=QFileDialog.getExistingDirectory(self)
        
        self.pathLabel.setText(fileobj)
        self.stitchdirectory=fileobj

    def contour(self):
        self.cntareathreshold=int(self.contourLineEdit.text())
        

    def calibration(self):
        
        self.createCalibrationDir()
        video=str(self.calibrationvideo)
        camera = cv2.VideoCapture(video)
        
        success, firstFrame = camera.read() #reads the first image of the video for calibration function
        
        xdist=[]
        ydist=[]
        knownpoint=0
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
                xdist.append(ix)
                ydist.append(iy)
        self.count = 0
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
        
        trial=self.calTrialIndexLineEdit.text()
        cameraID=self.calCamIDLineEdit.text()
        
        seperation = self.calDist2pointsLineEdit.text()
        distance = self.calreferenceLineEdit.text()
        
        deltax=float(seperation)/((xdist[0]-xdist[1])**2+(ydist[0]-ydist[1])**2)**0.5
        pixperdist=0.1/deltax
        print "O.k., each pixel equals %s meters in real life or 0.1 m equals %d pixels" % (deltax, pixperdist)
        print "Point 1 and 2 are %.2f m and %.2f m from the flume entrance" % (float(distance)+(xdist[2]-xdist[0])*deltax,float(distance)+(xdist[2]-xdist[1])*deltax)
        
        f = open('./Calibration_files/trial%d_camera%d.cal' %(float(trial),float(cameraID)), 'w+') #opens file and allows it to be overwritten 
        f.write(trial+'\n')
        f.write(cameraID+'\n')
        f.write(str(deltax)+'\n')
        f.write(str(distance)+'\n')
        f.write(str(xdist[2])+'\n')
        f.write(str(ydist[2])+'\n')
        f.close()
        
    def createCalibrationDir(self):
        if not os.path.exists('./Calibration_files'):
            os.makedirs('./Calibration_files')


    def stitch(self):
        self.signalemission=2
        path=str(self.stitchdirectory)
        path='%s\\'%path          
        
        #bring last two digits of each cameras ip adress
        
        try:
            tag=int(path[-15:-3])                     #extract tag number from path
            attempt=int(path[-2])
            trial=int(path[-17])
        except ValueError:
            tag=None
            attempt=None
            trial=None

        csvlist=[]
        for i in range(len(self.cameralist)):
        	csvlist.append(pd.read_csv('%s%s_raw.csv' % (path,str(self.cameralist[i]))))
        
        
        """
        Slightly out of sync camera?
        
        Try your hardest to have the cameras perfectly synced. This will save many headaches. When the attempts are cut from the raw video
        I used an approach assuming each camera starts at the same time. Then the attempt is cut by counting the number of seconds from the
        start of the video to the start of the attempt (first registry on the TIRIS system) minus a three second buffer and then cutting out the
        video until the end of the attempt plus a three second buffer. Works perfectly if the cameras started at the same time, which is most of the time.
        But if one had a small delay, then it can cause some problems. I wrote the code below to add empty rows to the affected camera.
        """
        
        #if one camera is out of sync with the rest, this code can help. Makes empty dataFrame with length equal to estimated duration of lagtime
        data = np.zeros([30,6])
        timelag=pd.DataFrame(data)
        timelag.columns=['index','Tag','Trial','Attempt','xCoord','yCoord']
        timelag.reset_index()
        
        #append the timelag to the start of the affected camera data
        csvlist[0]=timelag.append(csvlist[0])
        csvlist[0]=csvlist[0].reset_index()
        
        for i in range(len(csvlist)):
        	csvlist[i].ix[csvlist[i].xCoord==0,('xCoord','yCoord','xpixel','ypixel')]=None
        
        horizontalStack = pd.concat(csvlist, axis=1)#this is only here to allow user to check alignment of xCoord and yCoord
#        self.rawDataTable.setColumnCount(len(horizontalStack.columns))
#        self.rawDataTable.setRowCount(len(horizontalStack.index))
#        for i in range(len(horizontalStack.index)):
#            for j in range(len(horizontalStack.columns)):
#                self.rawDataTable.setItem(i,j,QTableWidgetItem(str(horizontalStack.iget_value(i, j))))
        """
        This next bit of code combines the lists horizontally. Rows that do not appear in the first carmera are filled by values
        present in the second, third, fourth camera, etc. The sync code (above) helps to reduce errors where the index of the first array
        actually correspond to a different time in the other cameras. 
        """
        csvcombined=csvlist[0]#initiate list
        for i in range(len(self.cameralist)):
        	try:
        		csvcombined=csvcombined.combine_first(csvlist[i+1])
        	except IndexError:
        		break
        csvcombined=csvcombined[['Attempt','Tag','Trial','xCoord','xpixel','yCoord','ypixel']]
        #---------save before kinematics-----------
        csvcombined.to_csv("%s%d_%d_%d_stitch_raw.csv" %(path,trial,tag,attempt))
        
        self.rawcoordinates=csvcombined.as_matrix()
        self.output(self.rawcoordinates, self.signalemission)
        
class kinematics:
    
    def __init__(self,df,crop,cropstart,cropend,interpolate,framerate,rollingperiods,path,trial,tag,attempt):
        
        if crop=='yes':
            df=df[(df.index.values>cropstart)&(df.index.values<cropend)]
        #mark interpolated rows
        def findinterpolatedvalues(state,xCoord):
            if state==1:
                return xCoord
        df['Interpolated']=0
        df.ix[df['xCoord'].isnull(),'Interpolated']=1
        
    
        #---------Calculate velocities--------------
        if interpolate=='yes':
            df=df.interpolate() #interpolate values to use .diff()
    
        df['xVel']=df.xCoord.diff()*framerate
        df['yVel']=df.yCoord.diff()*framerate
        df.to_csv("C:/Users/Jason/Desktop/testing.csv")
        #	df.ix[(df.xVel>10)|(df.xVel<-10)]=None #knock out unrealistically high velocities due to stitching errors
        #
        #	if interpolate=='yes':
        #		df=df.interpolate() #interpolate to fill knocked out values
        
        df['Interpolated']=df.apply(lambda row: findinterpolatedvalues(row['Interpolated'],row['xCoord']), axis=1)
        #df=df.reset_index()
        #---------Include "up" and "down" rows------
        df['up']=df['xCoord']
        df['down']=df['xCoord']
    
        df.ix[(df['xVel']<0),'up']=None
        df.ix[(df['xVel']>=0),'down']=None
        df.ix[df['xVel'].isnull(),'down']=None
        df.ix[df['xVel'].isnull(),'up']=None
        #---------Get out moving averaged velocities-----
        df['MAxVel']=pd.rolling_mean(df['xVel'],rollingperiods)
        df['MAyVel']=pd.rolling_mean(df['yVel'],rollingperiods)
        df['xAcc']=df.MAxVel.diff()*framerate
        df['yAcc']=df.MAyVel.diff()*framerate
    
        df['MAxCoord']=pd.rolling_mean(df['xCoord'],3)
        df['MAyCoord']=pd.rolling_mean(df['yCoord'],3)
    
        #print compiled image
        df.to_csv("%s10_check.csv" %(path))
        ax=df.plot(x='up',y='yCoord',kind='scatter',xlim=[0,10],ylim=[0,0.635],color='Red',figsize=(10,2))
        df.plot(kind='scatter', x='down', y='yCoord',ax=ax,color='Blue')
        df.plot(kind='scatter', x='Interpolated', y='yCoord',ax=ax,color='yellow')
        #df.plot(kind='scatter', x='MAxCoord', y='yCoord',ax=ax,color='white',label='Moving Average')  
        fig = ax.get_figure()
        
        fig.savefig('%sstitch.jpg'% path)
        interpolatedrows=df[df.Interpolated>=0]['xCoord']
        self.df=df
        self.fig=fig

    def get_dataFrame(self):
        return self.df
    def get_figure(self):
        return self.fig

app = QApplication(sys.argv)
app.aboutToQuit.connect(app.deleteLater)
form = MainWindow()
form.show()
app.exec_()
