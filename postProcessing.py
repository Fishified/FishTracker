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
    
    def __init__(self,name,ppfileobj,pp_TV,ppFileLoaded_L,plot_L):
        self.plot_L=plot_L
        self.name=name
        self.ppfileobj=ppfileobj
        self.pp_TV=pp_TV
        self.ppFileLoaded_L=ppFileLoaded_L


    def show(self):
        print self.name
        self.ppFileLoaded_L.setText(self.name)
        
        self.pdCSVfile=pd.read_csv(self.ppfileobj)
        self.pdCSVfile.columns= ['Image frame', 'x-coordinate (px)','y-coordinate (px)']
        self.model = PandasModel(self.pdCSVfile)
        self.pp_TV.setModel(self.model)
        
        ax=self.pdCSVfile.plot.scatter(x='x-coordinate (px)',y='y-coordinate (px)', color='DarkBlue')
        fig = ax.get_figure()
        fig.savefig('%s.png' % self.name)
        
        self.plot_L.setPixmap(QPixmap("%s.png" % self.name))
        #self.csvList_LW.addItem(self.ppfilename)

        

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