from PyQt4.QtGui import *
from PyQt4.QtCore import *


from PyQt4.QtGui import QFileDialog
import sys
import cv2
import time
import videoTracking
import numpy as np
import pandas as pd
import tracker_ui
import calibration
import os
import postProcessing


#from pandas.sandbox.qtpandas import DataFrameModel, DataFrameWidget
#
#from matplotlib.figure import Figure
#from matplotlib.backends.backend_qt4agg import (
#    FigureCanvasQTAgg as FigureCanvas,
#    NavigationToolbar2QT as NavigationToolbar)

class Person(object):
    def __init__(self, name, profession):
        self.name = name
        self.profession = profession
        
#class postProcessing:
#    
##    def __init__(self,refname,refpp_TV,ppFileLoaded_L):
##        self.myrefname=refname
##        self.myrefpp_TV=refpp_TV
##        self.myppFileLoaded_L=ppFileLoaded_L
#    def __init__(self,refname):
#        self.refname=refname
 

class MainWindow(QMainWindow, tracker_ui.Ui_MainWindow):
    
    #initiation function on start-up
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.scene=QGraphicsScene()
        self.scene2=QGraphicsScene()
        
        #initiate global lists
        self.cameralist=[]
        self.ppnamelist=[]
        self.ppClasslist=[]
      
        
        #initiate signals
        
        #buttons
        self.trackButton.clicked.connect(self.play_movie)
        self.loadButton.clicked.connect(self.open)
        self.previewButton.clicked.connect(self.preview)
        self.contourButton.clicked.connect(self.contour)
        self.ppFileOpen_B.clicked.connect(self.pp_openCSV)
        self.ppExecute_B.clicked.connect(self.initiatepostProcessing)
        self.loadcalibrate_B.clicked.connect(self.initiateCalibrate)
        self.makeCalFile_B.clicked.connect(self.outputCalFile)
        self.calClearTE_B.clicked.connect(self.textEditClear)
        self.csvList_LW.currentItemChanged.connect(self.ppShow)
        
        self.calibrate_B.clicked.connect(self.doCalibration)
        self.stitchButton.clicked.connect(self.stitch)
        self.stitchDirectoryButton.clicked.connect(self.openstitch)
        
        #sliders
        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        self.kernelSlider.valueChanged.connect(self.kernelSliderChange)
        
        
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
        
    
        self.framerate=int(self.frameratelineEdit.text())
        self.cameraID=int(self.cameraIdLineEdit.text())
        
        self.path, filename=os.path.split(os.path.abspath(self.video))
        self.path='%s\\'%self.path
        

        try:
            self.tag=int(self.path[-15:-3])                     #extract tag number from path
            self.attempt=int(self.path[-2])
            self.trial=int(self.path[-17])
        except ValueError:
            self.tag=None
            self.attempt=None
            self.trial=None

        self.vidstr=str(self.video)
        self.cap = cv2.VideoCapture(self.vidstr)
        self.fgbg=cv2.BackgroundSubtractorMOG()
        
        count = 0
        xcoord=[]
        ycoord=[]
        cx=0
        cy=0
        r=20

        while(True):
            
            if count==0:
                self.track_TE.setText("Tracking. Click video window and press 'q' or click 'Stop' button to cancel")
            if self.trackButton.isChecked()== False:
                self.scene.clear()
                self.trackButton.setText('Play')
                break
            else:
                self.trackButton.setText('Stop')
                
            (grabbed, frame) = self.cap.read()
            originalframe=frame
            
            if not grabbed:
                
                self.trackButton.setChecked(False)
                self.trackButton.setText('Play')
                self.track_TE.append("Tracking complete or program not able to grab video ... could be a format error. Check file type and try again.")
                break           
            
            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            #fills in timestamp digits to prevent detection
            if self.removeDigitsCheckBox.isChecked() == True:
                currentframe[np.where((currentframe == [255,255,255]).all(axis = 2))] = [0,0,0]            
            
            #backgroundSubtractor
            if self.backgroundCheckBox.isChecked() == True:
                currentframe = self.fgbg.apply(currentframe)
            
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
                
            self.fishcoords=np.array((xcoord,ycoord),dtype=float) #attributes coordinates of largest contour to fish coordinates
             
            for i in range(len(xcoord)):
                if xcoord[i]==0:
                    pass
                else:
                    cv2.circle(originalframe, (xcoord[i], ycoord[i]),6, (0, 0, 255),thickness=-1)
                    if i == len(xcoord)-1:
                        self.track_TE.append("Detection on frame: %d" % count)
                

            if self.novidCheckBox.isChecked()==False:
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
                    break
            count = count +1
            
        self.cap.release()
        cv2.destroyAllWindows()
        
        self.fishcoords=np.transpose(self.fishcoords)
        self.fishcoords=pd.DataFrame(self.fishcoords)
        self.fishcoords.to_csv("%s%s_raw.csv" %(self.path,self.cameraID))
        
    def open(self):
        fileobj=QFileDialog.getOpenFileName(self)# 'Open Video File', '', None, QFileDialog.DontUseNativeDialog)
        self.pathLabel.setText(fileobj)
        self.video=fileobj
        self.tracking=videoTracking.VideoTracking(self.track_TE, self.video)
        
    def openCSV(self):
        fileobj=QFileDialog.getOpenFileName(self)# 'Open Video File', '', None, QFileDialog.DontUseNativeDialog)
        self.ppFileLoaded_L.setText(fileobj)
        self.CSVfile=fileobj
        
    def preview(self):
        self.tracking.preview() 
        


    """
    Calibration
    """
          
    def initiateCalibrate(self):
        self.cal=calibration.Calibration(refcal_TE=self.cal_TE,
                                          refcalVideo_L=self.calVideo_L,
                                          reftrialIndex_LE=self.trialIndex_LE,
                                          refcameraID_LE=self.cameraID_LE,
                                          refdistance2pnts_LE=self.distance2pnts_LE,
                                          refrefDistance_LE=self.refDistance_LE)
        self.cal.openCalibration()
        
    def doCalibration(self):
        self.cal.doCalibration()
        
    def outputCalFile(self):
        self.cal.outputCalFile()
        
    def textEditClear(self):
    
            self.cal_TE.clear()
            
    """
    post-processing
    """
        
    def initiatepostProcessing(self):
        pass

    def pp_openCSV(self):
        
        self.ppfileobj=QFileDialog.getOpenFileNames(self, filter="Text Files (*.csv)")
        
        for i in range(len(self.ppfileobj)):
           
            self.pppath, self.ppfilename=os.path.split(os.path.abspath(self.ppfileobj[i]))
            slicestr=self.ppfilename[0:6]
            self.ppnamelist.append(slicestr)
            self.csvList_LW.addItem(self.ppnamelist[i])
            self.simplelist = [postProcessing.postProcessing(self.ppnamelist[i],self.pppath,self.pp_TV,self.ppFileLoaded_L) for i in range(len(self.ppnamelist))]
            print self.simplelist[i].name
    

#        self.pp.openCSV()
#        self.plot_L.setPixmap(QPixmap("testplot.png"))
#        self.csvList_LW.addItem(self.ppfilename)

    def ppShow(self):
        listindex = self.csvList_LW.currentRow()
        
        self.simplelist[listindex].show()

    def openstitch(self):
        fileobj=QFileDialog.getExistingDirectory(self)
        
        self.pathLabel.setText(fileobj)
        self.stitchdirectory=fileobj

    def contour(self):
        self.cntareathreshold=int(self.contourLineEdit.text())
        
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
