
#imports
import sys
import os
import time
from glob import glob

from PyQt4.QtGui import *
from PyQt4.QtCore import *
#from PyQt4.QtGui import QFileDialog

import cv2
import numpy as np
import pandas as pd
from distutils.dir_util import copy_tree

from PyQt4 import QtCore
import tracker_ui
import calibration
import postProcessing
import videoTracking
import matplotlib
matplotlib.style.use('seaborn-darkgrid')
import matplotlib.pyplot as plt
plt.rc('font', family='serif') 
plt.rc('font', serif='Times New Roman') 


from matplotlib.backends.backend_qt4agg \
import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow, tracker_ui.Ui_MainWindow):
    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.scene=QGraphicsScene()
        self.scene2=QGraphicsScene()
        
        #intial values
        self.ppAdjustState=1
        self.framerate=int(self.trkFramerate_LE.text())
        
        #global lists
        self.cameralist=[]
        self.ppClasslist=[]
        self.calfile=[]
        self.trackList=[]
        self.master_calList=[]
        self.masks=[]
        
        #calibrate/setup
        self.calChosepath_B.clicked.connect(self.getProjectPath)
        self.calLoadCalibrate_B.clicked.connect(self.newCalibration)
        self.calMakeCalFile_B.clicked.connect(self.outputCalFile)
        self.calCalibrate_B.clicked.connect(self.doCalibration)
        self.calRectify_B.clicked.connect(self.doRectify)
        self.calChoseExisting_B.clicked.connect(self.openCalibration)

    
#        self.cal_LW.currentItemChanged.connect(self.calActivate)
        
        #track
        self.trkTrack_B.clicked.connect(self.trackVideo)
        self.trkLoad_B.clicked.connect(self.videoOpen)
        self.trkPreview_B.clicked.connect(self.previewVideo)
        self.trkContour_B.clicked.connect(self.contour)
        self.trkFramerate_LE.editingFinished.connect(self.framerateChange)

        self.gaussSlider.valueChanged.connect(self.gaussSliderChange)
        self.medianSlider.valueChanged.connect(self.medianSliderChange)
        self.kernelSlider.valueChanged.connect(self.kernelSliderChange)
        self.playbackSlider.valueChanged.connect(self.playbackSliderChange)
        
        #post-process
        self.ppFileOpen_B.clicked.connect(self.openCSV)
        self.ppClean_B.clicked.connect(self.cleanup)
        self.ppBlank_B.clicked.connect(self.blankRows)
        self.ppUndo_B.clicked.connect(self.changesUndo)
        self.ppStitch_B.clicked.connect(self.stitchPlot)
        self.ppAdjust_B.clicked.connect(self.shiftFrames)
        self.ppHorizontalCombine_B.clicked.connect(self.pphorizontalCombine)
        self.ppInterpolate_B.clicked.connect(self.interpolate)
        self.ppAdd_RB.toggled.connect(lambda:self.ppRBstate(self.ppAdd_RB))
        self.ppSubtract_RB.toggled.connect(lambda:self.ppRBstate(self.ppSubtract_RB))
        self.csvList_LW.currentItemChanged.connect(self.plotTrack)
        #self.csvList_LW.currentItemChanged.connect(self.update_graph)

    def populatecameralist(self):
        self.cameralist.append(self.populatecameraslineEdit.text())
        self.populatecameraslineEdit.clear()
    def gaussSliderChange(self):
        self.gaussValueLabel.setText(str(self.gaussSlider.value()))
    def medianSliderChange(self):
        self.medianValueLabel.setText(str(self.medianSlider.value()))
    def kernelSliderChange(self):
        self.kernelValueLabel.setText(str(self.kernelSlider.value()))
    def playbackSliderChange(self):
       pass
    def framerateChange(self):
        self.framerate=int(self.trkFramerate_LE.text())
        

    """
    video:
        previewVideo(self)    - quick preview of selected video
        trackVideo(self) - perform background subtraction tracking on video, output raw tracking data files
    """
        
    def previewVideo(self):
        
        self.tracking.preview() 

    def trackVideo(self):
        
        self.framerate=int(self.trkFramerate_LE.text())
        self.pathThrow, self.filename=os.path.split(os.path.abspath(self.video))
        
        self.cameraid=self.filename[0:2]
        transfoMat=0
        if self.trackRectify_CB.isChecked():
            
            for name in glob("%s\Calibration_files\*" % self.path):
                a="%s\Calibration_files\\%s_matrix.csv" % (self.path,self.cameraid)
                if name == a:
                    print "do I go in here"
                    transMatrix=np.genfromtxt('%s\Calibration_files\\%s_matrix.csv' % (self.path,self.cameraid),delimiter=',')
            try:
                print transMatrix
                print "Transformation matrix found"
                transfoMat=1
            except NameError:
                transfoMat=0
            
        self.vidstr=str(self.video)
        self.cap = cv2.VideoCapture(self.vidstr)
        self.fgbg=cv2.BackgroundSubtractorMOG()
        
        count = 0
        xcoord=[]
        ycoord=[]
        cx=0
        cy=0

        while(True):
            t0 = time.time()


            if count==0:
                self.track_TE.setText("Tracking. Click video window and press 'q' or click 'Stop' button to cancel")
            if self.trkTrack_B.isChecked()== False:
                self.scene.clear()
                self.trkTrack_B.setText('Play')
                break
            else:
                self.trkTrack_B.setText('Stop')
                
            (grabbed, frame) = self.cap.read()


            if not grabbed:
                
                self.trkTrack_B.setChecked(False)
                self.trkTrack_B.setText('Play')
                self.track_TE.append("Tracking complete!")
                break
            
            rows,cols,ch = frame.shape
            
            if transfoMat==1:
                adjusted=cv2.warpAffine(frame,transMatrix,(cols,rows))
                currentframe = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
            else:
                adjusted=frame
                currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#            currentframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
                if cv2.contourArea(c) < cntareathreshold:
                    continue
                cntarea.append(cv2.contourArea(c))
                (x, y, w, h) = cv2.boundingRect(c)
        
                M = cv2.moments(c)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
        
                
                
                
                xcntcoord.append(cx)
                ycntcoord.append(cy)
                self.track_TE.append("coutour area: %d" % float(cv2.contourArea(c)))
#                self.track_TE.append("x position : %d" % float(xcntcoord[-1]))
#                self.track_TE.append("y position : %d" % float(ycntcoord[-1]))
            
            if self.splitCorrect_CB.isChecked() == True and len(xcntcoord)>2:
                del xcntcoord[0]
                del ycntcoord[0]
                
                xcoordCorrected=sum(xcntcoord)/len(xcntcoord)
                ycoordCorrected=sum(ycntcoord)/len(ycntcoord)
                xcoord.append(xcoordCorrected)
                ycoord.append(ycoordCorrected)
                self.track_TE.append("Split correction applied: x-coord %d, y-coord %d" % (xcoord[-1], ycoord[-1]))
                #self.track_TE.append("Contour 1: x-coord %d, y-coord %d" % (xcntcoord[0], ycntcoord[0]))
                #self.track_TE.append("Contour 2: x-coord %d, y-coord %d" % (xcntcoord[1], ycntcoord[1]))
                
                
            else:

                biggestcontour=cntarea.index(max(cntarea))
                xcoord.append(xcntcoord[biggestcontour])
                ycoord.append(ycntcoord[biggestcontour])
                #self.track_TE.append("Single detection: x-coord %d, y-coord %d" % (xcoord[-1], ycoord[-1]))

                
            self.fishcoords=np.array((xcoord,ycoord),dtype=float) 
             
            for i in range(len(xcoord)):
                if xcoord[i]==0:
                    pass
                else:
                    cv2.circle(adjusted, (xcoord[i], ycoord[i]),6, (0, 0, 255),thickness=-1)
                    if i == len(xcoord)-1:
                        self.track_TE.append("Detection on frame: %d" % count)
                        
            
            cv2.namedWindow("Background removed", cv2.WINDOW_NORMAL) 
            cv2.imshow("Background removed",currentframe)               
            cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL) 
            cv2.imshow("Tracking",adjusted)   
            
            #variables used to increase/decrease video playback speed
            self.vidSpeedMultiplier=int(self.playbackSlider.value())
            self.framerate=float(self.framerate)
            a=(1/self.framerate)*(100/(self.vidSpeedMultiplier))
            
            t1 = time.time()
            total = t1-t0
            print total
            time.sleep(a)
                #breaks out 
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.trkTrack_B.setChecked(False)
                self.trkTrack_B.setText('Play')
                break
            count = count +1
            
        self.cap.release()
        cv2.destroyAllWindows()
        
        self.fishcoords=np.transpose(self.fishcoords)
        self.fishcoords=pd.DataFrame(self.fishcoords)
        self.fishcoords.to_csv("%s\\%s_raw.csv" %(self.path,self.cameraid))


    """
    open file dialogs:
        
        getPath(self)          - set project path, copy last project calibration, clear main thread of last project
        videoOpen(self)        - get video and set active video label
        openCalibration(self)  - mkdir if absent, copy calibration contents over
        openCSV(self)          - populate trackList with postProcessing instances
        
    """
    def getProjectPath(self):
        try:
            self.lastpath=self.path
            self.path=QFileDialog.getExistingDirectory(self,"Choose project folder", self.lastpath)
        except AttributeError:
            self.path=QFileDialog.getExistingDirectory(self,"Choose project folder", "C:\\Users\\tempo\\Desktop\\Trial_1")

        self.calLabelPath_L.setText(self.path)
        self.activePath_L.setText(self.path)
    
        if self.calReuse_CB.isChecked()==True:
            try:
                os.makedirs('%s\\Calibration_files' % self.path)
                copy_tree("%s\\Calibration_files\\" % self.lastpath,'%s\\Calibration_files' % self.path)
            except WindowsError:
                copy_tree("%s\\Calibration_files\\" % self.lastpath,'%s\\Calibration_files' % self.path)
                        
    def videoOpen(self): 
        fileobj=QFileDialog.getOpenFileName(self,"Video file", self.path,filter="Video Files( *.mp4 *.h264)")
        self.pathLabel.setText(fileobj)
        self.video=fileobj
        self.tracking=videoTracking.VideoTracking(self.track_TE, self.video)
           
    def openCalibration(self):
        self.calpath=QFileDialog.getExistingDirectory(self)
        try:
            os.makedirs('%s\\Calibration_files' % self.path)
        except WindowsError:
            pass
        copy_tree("%s\\" % self.calpath, "%s\\Calibration_files\\" % self.path)

    def openCSV(self):
        self.fileobj=QFileDialog.getOpenFileNames(self,"CSV files", self.path, filter="Text Files (*.csv)")
        self.appendTrackList=[postProcessing.postProcessing(self.fileobj[i],self.framerate) for i in range(len(self.fileobj))]

        if len(self.trackList) == 0:
            self.trackList=self.appendTrackList
        else:
            self.trackList=self.trackList+self.appendTrackList
            
        for i in range(len(self.trackList)):
            self.csvList_LW.addItem(self.trackList[i].name)


    """
    Calibration:
        
        newCalibration(self) - create a new 
    """
    
    def doCalibration(self):
        if self.calRectify_CB.isChecked()==True:
            self.rectify=True
        else:
            self.rectify=False
            
        listindex = self.cal_LW.currentRow()
        self.master_calList[listindex].doCalibration(self.rectify)
        
    def newCalibration(self):
        
        self.calBasenames=[]
        self.master_calList=[]
        self.calFileobj=QFileDialog.getOpenFileNames(self,"Chose a video to calibrate", self.path, filter="Video files (*.mp4 *.h264)")
       
        for i in range(len(self.calFileobj)):
            basename=os.path.basename(self.calFileobj[i])
            print basename
            self.cal_LW.addItem(basename)

        self.toAppend_calList=[calibration.Calibration(self.calFileobj[i],
                                                       self.cal_TE) for i in range(len(self.calFileobj))]

        if len(self.master_calList) == 0:
            self.master_calList=self.toAppend_calList
        else:
            self.master_calList=self.master_calList+self.toAppend_calList
        
    def doRectify(self):
        listindex = self.cal_LW.currentRow()
        self.master_calList[listindex].perspectiveTransform()
        
    def outputCalFile(self):
        listindex = self.cal_LW.currentRow()
        self.master_calList[listindex].outputCalFile(self.trialIndex_LE.text(),self.cameraID_LE.text(),self.distance2pnts_LE.text(),self.refDistance_LE.text())

    """
    post-processing
    """

    def plotTrack(self):
        try:
            listindex = self.csvList_LW.currentRow()
            self.trackList[listindex].plotTrack(self.pp_TV,self.ppFileLoaded_L,self.trackPlot_L)
        except IndexError:
            pass
 
    def stitchPlot(self):
        colors=['red','blue','black','darkgrey','green','magenta']
        
        for i in range(len(self.trackList)):
            if i == 0:
                ax=self.trackList[i].dfTreated.plot(kind='scatter', x='up_x',y='u',xlim=[0,10],color=colors[i])
                self.trackList[i].dfTreated.plot(kind='scatter', x='down_x', y='u',ax=ax,color=colors[i],alpha=0.5, figsize=[7,2], label = self.trackList[i].name)                
            else:
                self.trackList[i].dfTreated.plot(kind='scatter', x='up_x', y='u',ax=ax,color=colors[i])
                self.trackList[i].dfTreated.plot(kind='scatter', x='down_x', y='u',ax=ax,color=colors[i],alpha=0.5, figsize=[7,2], label = self.trackList[i].name )
                
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('u (m/s)')
        plt.legend(loc='best',prop={'size':10}, frameon=True, shadow=True, bbox_to_anchor=(1.1, 1.1))
        plt.title('Velocity Plot', style='italic')
        fig = ax.get_figure()
        fig.savefig('%s\stitchPlot.png' % self.path)
        time.sleep(0.1)
        
        self.stitchPlot_L.setPixmap(QPixmap("%s\stitchPlot.png" %self.path))
        
    def ppPopulateStitchList(self):
        self.trackList=[]
        for index in xrange(self.csvList_LW.count()):
            if self.csvList_LW.item(index).text()=="Stitch":
                continue
            filename="%s\%s_treated.csv" % (self.path,self.csvList_LW.item(index).text())
            self.trackList.append(pd.read_csv('%s' % (filename)))
    
        f = open('%s\\Calibration_files\stitch.cal' % self.path, 'w+')
        f.write("Dummy calibration file for stitch")
        f.close()

    def blankRows(self):
        listindex = self.csvList_LW.currentRow()
        self.trackList[listindex].blankRows(self.pp_TV.selectionModel().selectedRows())
        
    def changesUndo(self):
        listindex = self.csvList_LW.currentRow()
        self.trackList[listindex].defineDataFrame()
        
    def pphorizontalCombine(self):
        self.ppPopulateStitchList()
        self.horizontalStack = pd.concat(self.trackList, axis=1)
        self.pp_TV.setModel(PandasModel(self.horizontalStack))
        
    def ppRBstate(self,b):
	
      if b.text() == "Add rows":
         if b.isChecked() == True:
            self.ppAdjustState=1
				
      if b.text() == "Subtract rows":
         if b.isChecked() == True:
            self.ppAdjustState=0
    
    def shiftFrames(self):
        listindex = self.csvList_LW.currentRow()
        self.trackList[listindex].shiftFrames(self.ppAdjust_LE.text(),self.ppAdjustState)
        
    def interpolate(self):
        listindex = self.csvList_LW.currentRow()
        self.trackList[listindex].interpolate()
        
    #utilities

    def cleanup(self):
        
        for fl in glob("%s\\*_orig.csv" %self.path):
            os.remove(fl)
        for fl in glob("%s\\*_treated.csv" %self.path):
            os.remove(fl)
        for fl in glob("%s\\Stitch.csv" %self.path):
            os.remove(fl)
        for fl in glob("%s\\*.png" %self.path):
            os.remove(fl)
        
        self.pp_TV.clearSpans()
        del self.trackList[:]
        self.csvList_LW.clear()
        self.ppFileLoaded_L.clear()
        self.trackPlot_L.setText("Trace will appear when a trajectory file is selected ...")

    def contour(self):
        self.cntareathreshold=int(self.contourLineEdit.text())
        self.track_TE.append("Threshold contour area changed to %d" % self.cntareathreshold)
        
    def update_graph(self):
        listindex = self.csvList_LW.currentRow()
        df=pd.read_csv(self.trackList[listindex].filename)
        df.columns= ['Image frame', 'x_px','y_px']
        self.mpl.canvas.ax.clear()
        
        self.mpl.canvas.ax.bar(5, [20,33,25,99,100], width=0.5)
        self.mpl.canvas.draw()
        
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
    



        
app = QApplication(sys.argv)
app.aboutToQuit.connect(app.deleteLater)
form = MainWindow()
form.show()
app.exec_()
