# -*- coding: utf-8 -*-
"""
Created on Tue May 23 13:09:10 2017

@author: dugj2403
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QFileDialog
from functools import partial 
import sys
import cv2
import time
import videoTracking
import numpy as np
import pandas as pd
import tracker_ui
import calibration
import os


def open(self):
    fileobj=QFileDialog.getOpenFileName(self)# 'Open Video File', '', None, QFileDialog.DontUseNativeDialog)
    self.pathLabel.setText(fileobj)
    self.video=fileobj
    self.tracking=videoTracking.VideoTracking(self.track_TE, self.video)
    
def preview(self):
    self.tracking.preview() 
      
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