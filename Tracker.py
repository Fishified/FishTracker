
#imports
import sys
import os
import time
from glob import glob
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtCore
from PyQt4.QtGui import QFileDialog

import cv2
import numpy as np
import pandas as pd

import tracker_ui
import calibration
import postProcessing
import videoTracking

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None
        

class MainWindow(QMainWindow, tracker_ui.Ui_MainWindow):
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.scene=QGraphicsScene()
        self.scene2=QGraphicsScene()
        
        #intial values
        self.ppAdjustState=1
        self.framerate=int(self.trkFramerate_LE.text())
        
        #lists
        self.cameralist=[]
        self.ppnamelist=[]
        self.ppClasslist=[]
        self.calfile=[]
        self.simplelist=[]
        
        #calibrate
        self.calLoadCalibrate_B.clicked.connect(self.initiateCalibrate)
        self.calMakeCalFile_B.clicked.connect(self.outputCalFile)
        self.calClearTE_B.clicked.connect(self.textEditClear)
        self.calCalibrate_B.clicked.connect(self.doCalibration)
        
        #track
        self.trkTrack_B.clicked.connect(self.play_movie)
        self.trkLoad_B.clicked.connect(self.open)
        self.trkPreview_B.clicked.connect(self.preview)
        self.trkContour_B.clicked.connect(self.contour)
        self.trkFramerate_LE.editingFinished.connect(self.framerateChange)

        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        self.kernelSlider.valueChanged.connect(self.kernelSliderChange)
        
        #post-process
        self.ppFileOpen_B.clicked.connect(self.pp_openCSV)
        self.ppClean_B.clicked.connect(self.cleanup)#attached to clean case routine
        self.ppBlank_B.clicked.connect(self.ppBlank)
        self.ppUndo_B.clicked.connect(self.ppUndo)
        self.ppStitch_B.clicked.connect(self.ppStitch)
        self.ppAdjust_B.clicked.connect(self.ppAdjust)
        self.ppHorizontalCombine_B.clicked.connect(self.pphorizontalCombine)
        self.ppInterpolate_B.clicked.connect(self.ppInterpolate)

        self.ppAdd_RB.toggled.connect(lambda:self.ppRBstate(self.ppAdd_RB))
        self.ppSubtract_RB.toggled.connect(lambda:self.ppRBstate(self.ppSubtract_RB))
    
        self.csvList_LW.currentItemChanged.connect(self.ppShow)

    def populatecameralist(self):
        self.cameralist.append(self.populatecameraslineEdit.text())
        self.populatecameraslineEdit.clear()
    def gaussSliderChange(self):
        self.gaussValueLabel.setText(str(self.gaussSlider.value()))
    def medianSliderChange(self):
        self.medianValueLabel.setText(str(self.medianSlider.value()))
    def kernelSliderChange(self):
        self.kernelValueLabel.setText(str(self.kernelSlider.value()))
    def framerateChange(self):
        self.framerate=int(self.trkFramerate_LE.text())

    def play_movie(self):
        

        self.framerate=int(self.trkFramerate_LE.text())
        self.cameraID=int(self.cameraIdLineEdit.text())
        print self.framerate
        
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
            if self.trkTrack_B.isChecked()== False:
                self.scene.clear()
                self.trkTrack_B.setText('Play')
                break
            else:
                self.trkTrack_B.setText('Stop')
                
            (grabbed, frame) = self.cap.read()
            originalframe=frame

            if not grabbed:
                
                self.trkTrack_B.setChecked(False)
                self.trkTrack_B.setText('Play')
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

    def pp_openCSV(self):
        self.ppnamelist=[]
        self.ppfileobj=[]
        self.calfile=[]
        
        self.ppfileobj=QFileDialog.getOpenFileNames(self, filter="Text Files (*.csv)")
       
        for i in range(len(self.ppfileobj)):
            self.pppath, self.ppfilename=os.path.split(os.path.abspath(self.ppfileobj[i]))
            slicestr=self.ppfilename[0:6]
            self.cameraid=self.ppfilename[0:2]
            self.ppnamelist.append(slicestr)
            self.csvList_LW.addItem(self.ppnamelist[i])

            
            for name in glob("%s\Calibration_files\*" % self.pppath):
                a="%s\Calibration_files\\%s.cal" % (self.pppath,self.cameraid)
                if name == a:
                    self.calfile.append(name)
        
        self.newlist=[postProcessing.postProcessing(self.ppnamelist[i],self.ppfileobj[i],self.pp_TV,self.ppFileLoaded_L,self.plot_L,self.calfile[i],0,self.framerate) for i in range(len(self.ppnamelist))]
       
        if len(self.simplelist) == 0:
            self.simplelist=self.newlist
        else:
            self.simplelist=self.simplelist+self.newlist
            
    def ppShow(self):
        listindex = self.csvList_LW.currentRow()
        self.simplelist[listindex].show(0)
        
    def ppStitch(self):
        
        for i in range(len(self.simplelist)):
            if self.simplelist[i].name=="Stitch":
                del self.simplelist[i]
                
        self.csvList_LW.clear()
        for i in range(len(self.simplelist)):
            self.csvList_LW.addItem(self.simplelist[i].name)
                
                
        self.ppPopulateStitchList()
        csvcombined=self.stitchlist[0]#initiate list with first camera list
        for i in range(len(self.stitchlist)):
        	try:
        		csvcombined=csvcombined.combine_first(self.stitchlist[i+1])
        	except IndexError:
        		break

        csvcombined.to_csv("stitch.csv",index_label=False,sep=',')    
        
        stitchPPinstance= postProcessing.postProcessing("Stitch","stitch.csv",self.pp_TV,self.ppFileLoaded_L,self.plot_L,'./Calibration_files/stitch.cal',1,self.framerate)
        
        self.simplelist.append(stitchPPinstance)
        self.csvList_LW.addItem( self.simplelist[-1].name)
    
        self.simplelist[-1].show(3)

    def ppPopulateStitchList(self):
        self.stitchlist=[]
        self.pwd=os.getcwd()
        
        for index in xrange(self.csvList_LW.count()):
            if self.csvList_LW.item(index).text()=="Stitch":
                continue
            filename="%s_treated.csv" % self.csvList_LW.item(index).text()[0:2]
            self.stitchlist.append(pd.read_csv('%s\%s' % (self.pwd,filename)))
            
        f = open('./Calibration_files/stitch.cal', 'w+') #opens file and allows it to be overwritten 
        f.write("Dummy calibration file for stitch")
        f.close()

    def ppBlank(self):
        
        listindex = self.csvList_LW.currentRow()
        self.simplelist[listindex].blank(self.pp_TV.selectionModel().selectedRows())
        
    def ppUndo(self):
        listindex = self.csvList_LW.currentRow()
        self.simplelist[listindex].show(2)
        
    def pphorizontalCombine(self):
        self.ppPopulateStitchList()
        self.horizontalStack = pd.concat(self.stitchlist, axis=1)
        self.pp_TV.setModel(PandasModel(self.horizontalStack))
        
    def ppRBstate(self,b):
	
      if b.text() == "Add rows":
         if b.isChecked() == True:
            self.ppAdjustState=1
				
      if b.text() == "Subtract rows":
         if b.isChecked() == True:
            self.ppAdjustState=0
    
    def ppAdjust(self):
        listindex = self.csvList_LW.currentRow()
        self.simplelist[listindex].ppAdjust(self.ppAdjust_LE.text(),self.ppAdjustState)
        
    def ppInterpolate(self):
        listindex = self.csvList_LW.currentRow()
        self.simplelist[listindex].ppInterpolate()
        
    #utilities
    def cleanup(self):
        self.pwd=os.getcwd()
        for fl in glob("%s\\*_orig.csv" %self.pwd):
            os.remove(fl)
        for fl in glob("%s\\*_treated.csv" %self.pwd):
            os.remove(fl)
        for fl in glob("%s\\Stitch.csv" %self.pwd):
            os.remove(fl)
        
        del self.simplelist[:]
        self.ppnamelist=[]
        self.csvList_LW.clear()
        self.ppFileLoaded_L.clear()
        self.plot_L.setText("Trace will appear when a trajectory file is selected ...")
        self.pp_TV.clearSpans()
        
    def contour(self):
        self.cntareathreshold=int(self.contourLineEdit.text())
               


app = QApplication(sys.argv)
app.aboutToQuit.connect(app.deleteLater)
form = MainWindow()
form.show()
app.exec_()
