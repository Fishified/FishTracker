# -*- coding: utf-8 -*-
"""
Created on Tue May 23 14:42:49 2017

@author: dugj2403
"""
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QFileDialog
from PyQt4 import QtCore
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

"""
Erroneous data removal approaches:

Spurious data mostly results from surface glare causing movement contours with roughly the same surface area (pixels)
as the size of the fish. The first approach (1) against spuriuos data is to vary cntareathreshold (defined at top) to try and eliminate small erroneous contours.
Usually this is a good approach, especially if the fish is large and you have low glare on the surface. Nevertheless, there are some erroneous
contours that leak in. So I came up with approaches 2 and 3 to deal further with these. Approach (2) checks detected coordinates to see if they are
alone (i.e. the rows above and below are zero), if they are alone then they get taken out. Defense (3) calculates a 2 period rolling standard deviation
(rSTD) over the xCoord key. By default the rSTD threshold is 200, this helps remove groups of two or three spurious detections. The downside is that 
the first row of good data in a block is lost becuase it will inevitably have a rSTD > 200. A small price to pay for good data. 
"""
        
class postProcessing:
    
    def __init__(self,name,ppfileobj,pp_TV,ppFileLoaded_L,plot_L,calfile):
        self.plot_L=plot_L
        self.name=name
        self.cameraid=self.name[0:2]
        self.ppfileobj=ppfileobj
        self.pp_TV=pp_TV
        self.ppFileLoaded_L=ppFileLoaded_L
        self.loadedFlag=0
        
        #read calibration file
        self.calfile=calfile
        with open(self.calfile) as f:
            self.calcontent = f.readlines()
        
        #load file and create dataframe 
        self.pdCSVfile=pd.read_csv(self.ppfileobj)
        self.pdCSVfile.columns= ['Image frame', 'x_px','y_px']
        self.pdCSVfile=self.pdCSVfile.replace('0.0', np.nan)
        
        #add georeferenced coordinates
        self.pdCSVfile['x']=float(self.calcontent[3])+(float(self.calcontent[4])-self.pdCSVfile['x_px'])*float(self.calcontent[2])
        self.pdCSVfile['y']=(float(self.calcontent[5])-self.pdCSVfile['y_px'])*float(self.calcontent[2])
        self.pdCSVfile.to_csv('%s_orig.csv' %self.cameraid,index_label=False,sep=',')
        self.treated=self.pdCSVfile
        

    def show(self,state):
        
        #show for first time
        if state == 0 and self.loadedFlag == 0:
            CSVinput = pd.read_csv("%s_orig.csv" % self.cameraid,sep =',')
        #show after treating
        if state == 0 and self.loadedFlag == 1:
            CSVinput=self.treated
        if state==1:
            CSVinput=self.treated
        #show after undoing changes
        if state == 2:
            CSVinput = pd.read_csv("%s_orig.csv" % self.cameraid,sep =',')
            self.treated=CSVinput
        
        self.ppFileLoaded_L.setText(self.name)        
        self.pp_TV.setModel(PandasModel(CSVinput))
        
        
        ax=CSVinput.plot.scatter(x='x',y='y', color='DarkBlue')
        fig = ax.get_figure()
        fig.savefig('%s.png' % self.name)
        
        self.plot_L.setPixmap(QPixmap("%s.png" % self.name))
        self.loadedFlag=1
    
    def blank(self,rowIndices):
        self.rowIndices=rowIndices

        for i in range(len(self.rowIndices)):
            self.treated.iloc[self.rowIndices[i].row(),1:5]=None

        self.treated.to_csv("%s_treated.csv" % self.cameraid,sep =',')
        self.show(1)
        

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