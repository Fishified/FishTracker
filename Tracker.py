
#imports
import sys
import os
import time
from glob import glob
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtCore
#from PyQt4.QtGui import QFileDialog

import cv2
import numpy as np
import pandas as pd
import shutil
from distutils.dir_util import copy_tree


import tracker_ui
import calibration
import postProcessing
import videoTracking
import stitchPlot


from PyQt4 import QtGui
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
        
        #calibrate/setup
        self.calChosepath_B.clicked.connect(self.getPath)
        self.calLoadCalibrate_B.clicked.connect(self.newCalibration)
        self.calMakeCalFile_B.clicked.connect(self.outputCalFile)
        self.calCalibrate_B.clicked.connect(self.doCalibration)
        self.calRectify_B.clicked.connect(self.doRectify)
        self.calChoseExisting_B.clicked.connect(self.openCalibration)

    
#        self.cal_LW.currentItemChanged.connect(self.calActivate)
        
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
    def framerateChange(self):
        self.framerate=int(self.trkFramerate_LE.text())

    def play_movie(self):
        
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


            if not grabbed:
                
                self.trkTrack_B.setChecked(False)
                self.trkTrack_B.setText('Play')
                self.track_TE.append("Tracking complete!")
                break
            
            originalframe=frame
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
                self.track_TE.append("Contour 1: x-coord %d, y-coord %d" % (xcntcoord[0], ycntcoord[0]))
                self.track_TE.append("Contour 2: x-coord %d, y-coord %d" % (xcntcoord[1], ycntcoord[1]))
                
                
            else:

                biggestcontour=cntarea.index(max(cntarea))
                xcoord.append(xcntcoord[biggestcontour])
                ycoord.append(ycntcoord[biggestcontour])
                self.track_TE.append("Single detection: x-coord %d, y-coord %d" % (xcoord[-1], ycoord[-1]))

#            
#            if xcntcoord[biggestcontour]==0 or passFlag==True :
#                pass
#            else:
#                cv2.circle(originalframe, (xcoord[-1], ycoord[-1]),r,(0, 255, 0), 3)
                
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
       
        
    def open(self):
    
        fileobj=QFileDialog.getOpenFileName(self,"Video file", self.path,filter="Video Files *.h264")

        self.pathLabel.setText(fileobj)
        self.video=fileobj
        self.tracking=videoTracking.VideoTracking(self.track_TE, self.video)
           
    def preview(self):
        
        self.tracking.preview() 

    """
    Calibration
    """
    
    def openCalibration(self):
        self.calpath=QFileDialog.getExistingDirectory(self)
        try:
            os.makedirs('%s\\Calibration_files' % self.path)
        except WindowsError:
            pass
        
        dest="%s\\Calibration_files\\" % self.path
        copy_tree("%s\\" % self.calpath, "%s\\Calibration_files\\" % self.path)
        
    def doCalibration(self):
        if self.calRectify_CB.isChecked()==True:
            self.rectify=True
        else:
            self.rectify=False
            
        listindex = self.cal_LW.currentRow()
        self.master_calList[listindex].doCalibration(self.rectify)
        
    def newCalibration(self):
        
        self.calNamelist=[]
        self.calFileobj=[]
        self.calCameraID=[]
        self.fullPath=[]

        self.calFileobj=QFileDialog.getOpenFileNames(self,"Video files", self.path, filter="Video files (*.h264)")
       
        for i in range(len(self.calFileobj)):
            self.pathThrow, self.calFilename=os.path.split(os.path.abspath(self.calFileobj[i]))
            self.fullPath.append(os.path.abspath(self.calFileobj[i]))
            slicestr=self.calFilename[0:6]
            self.calCameraID=self.calFilename[0:2]
            self.calNamelist.append(slicestr)
            self.cal_LW.addItem(self.calNamelist[i])

        self.toAppend_calList=[calibration.Calibration(self.calNamelist[i],self.path,self.fullPath[i],
                                                       self.cal_TE) for i in range(len(self.calNamelist))]

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
    def openCSV(self):

        self.fileobj=QFileDialog.getOpenFileNames(self,"CSV files", self.path, filter="Text Files (*.csv)")
        self.appendTrackList=[postProcessing.postProcessing(self.fileobj[i],self.framerate) for i in range(len(self.fileobj))]

        if len(self.trackList) == 0:
            self.trackList=self.appendTrackList
        else:
            self.trackList=self.trackList+self.appendTrackList
            
        for i in range(len(self.trackList)):
            self.csvList_LW.addItem(self.trackList[i].name)
        
        
    def plotTrack(self):
        try:
            listindex = self.csvList_LW.currentRow()
            self.trackList[listindex].plotTrack(self.pp_TV,self.ppFileLoaded_L,self.trackPlot_L)

        except IndexError:
            pass

        
    def stitchPlot(self):
        stitchPlot.stitchPlot(self.trackList)
        
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
    def getPath(self):
        
        try:
            self.lastpath=self.path
            self.path=QFileDialog.getExistingDirectory(self,"Choose project folder", self.lastpath)
            check=True
            
        except AttributeError:
            self.path=QFileDialog.getExistingDirectory(self,"Choose project folder", "G:\\CutVideo\\")
            check=False
            
#        if check==True:
#            choice = QtGui.QMessageBox.question(self, "This will change project folders ...","Are you sure?",QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
#                    if choice == QtGui.QMessageBox.Yes:
#                        print("Okay, project folder changed")
#                        sys.exit()
#                    else:
                        
        self.calLabelPath_L.setText(self.path)
        self.activePath_L.setText(self.path)
        
        if self.calReuse_CB.isChecked()==True:
            try:
                os.makedirs('%s\\Calibration_files' % self.path)
                copy_tree("%s\\Calibration_files\\" % self.lastpath,'%s\\Calibration_files' % self.path)
            except WindowsError:
                copy_tree("%s\\Calibration_files\\" % self.lastpath,'%s\\Calibration_files' % self.path)
                
    def cleanup(self):
        #self.pwd=os.getcwd()
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
