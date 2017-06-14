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
import os
from glob import glob

        
class postProcessing:
    
    def __init__(self,fileobj,framerate):
        
        self.fileobj=fileobj
        self.framerate=framerate
        self.df=pd.read_csv(self.fileobj)
        self.path, self.filename=os.path.split(os.path.abspath(self.fileobj))
        self.cameraid=self.filename[0:2]
        self.name="Camera_%s" % self.cameraid

        for name in glob("%s\Calibration_files\*" % self.path):
            if name == "%s\Calibration_files\\%s.cal" % (self.path,self.cameraid):
                self.calfile = name
        with open(self.calfile) as f:
            self.calcontent = f.readlines()

        self.df.columns= ['Image frame', 'x_px','y_px']
        self.df=self.df.replace(0.0, np.nan)
        
        self.df['x']=float(self.calcontent[3])+(float(self.calcontent[4])-self.df['x_px'])*float(self.calcontent[2])
        self.df['y']=(float(self.calcontent[5])-self.df['y_px'])*float(self.calcontent[2])
        
        self.defineDataFrame()
        
    def defineDataFrame(self):
        
        self.dfTreated=self.df
        self.kinematics()
        self.write()
        
        try:
            self.plotTrack(self.tableView,self.textLabel,self.plotLabel)
        except AttributeError:
            pass
        
    def kinematics(self):
        
        self.dfTreated['u']=self.dfTreated.x.diff()*self.framerate
        
        self.dfTreated['v']=self.dfTreated.y.diff()*self.framerate
        self.dfTreated['up']=self.dfTreated['x']
        self.dfTreated['down']=self.dfTreated['x']
        self.dfTreated.ix[(self.dfTreated['u']<0),'up']=None
        self.dfTreated.ix[(self.dfTreated['u']>=0),'down']=None
        self.dfTreated.ix[self.dfTreated['u'].isnull(),'down']=None
        self.dfTreated.ix[self.dfTreated['u'].isnull(),'up']=None
       
        if 'Interpolated' in self.dfTreated.columns:
            self.dfTreated = self.dfTreated[['Image frame','x_px','y_px','x','y','u','v','up','down','Interpolated','Interpolated_x']]
        else:
            self.dfTreated = self.dfTreated[['Image frame','x_px','y_px','x','y','u','v','up','down']]
        
    def plotTrack(self,tableView,textLabel,plotLabel):
        
        self.textLabel=textLabel
        self.tableView=tableView
        self.plotLabel=plotLabel
        self.textLabel.setText("%s\%s.csv" % (self.path, self.name))      
        self.tableView.setModel(PandasModel(self.dfTreated))
        
        ax=self.dfTreated.plot(x='up',y='y',kind='scatter',xlim=[0,10],ylim=[0,0.7],color='Red',figsize=(10,2))
        self.dfTreated.plot(kind='scatter', x='down', y='y',ax=ax,color='Blue')
        
        if 'Interpolated' in self.dfTreated.columns:
            self.dfTreated.plot(kind='scatter', x='Interpolated_x', y='y',ax=ax,color='yellow') 
        fig = ax.get_figure()
        fig.savefig('%s\%s.png' % (self.path,self.name))
        self.plotLabel.setPixmap(QPixmap("%s\%s.png" % (self.path,self.name)))
    
    def blankRows(self,rowIndices):
        
        self.rowIndices=rowIndices
        for i in range(len(self.rowIndices)):
            self.dfTreated.iloc[self.rowIndices[i].row(),1:10]=None              
        self.plotTrack(self.tableView,self.textLabel,self.plotLabel)
        
    def shiftFrames(self,adjust,state):
        
        self.state=state
        self.adjust=int(adjust)

        if state == 1:
            df = pd.DataFrame(index=range(0,self.adjust),columns=['Image frame','x_px','y_px','x','y','u','v','up','down'], dtype='float')
            self.dfTreated= pd.concat([df,self.dfTreated])
            self.dfTreated=self.dfTreated.reset_index(drop=True)
            self.dfTreated['Image frame'] = self.dfTreated.index

        if state == 0:
            self.dfTreated = self.dfTreated.ix[self.adjust:]
            self.dfTreated=self.dfTreated.reset_index(drop=True)
            self.dfTreated['Image frame'] = self.dfTreated.index
            
        self.plotTrack(self.tableView,self.textLabel,self.plotLabel)
        
    def interpolate(self):
        
        self.dfTreated=self.dfTreated.drop(['u','v','up','down'],axis=1)
        self.dfTreated["Interpolated"]=0
        self.dfTreated.ix[self.dfTreated['x'].isnull(),'Interpolated']=1
        self.dfTreated=self.dfTreated.interpolate() 
        self.dfTreated['Interpolated_x'] = np.where(self.dfTreated['Interpolated'] == 1, self.dfTreated['x'],None)
        self.kinematics()
        self.plotTrack(self.tableView,self.textLabel,self.plotLabel)

    def write(self):
        self.dfTreated.to_csv("%s\%s_treated.csv" % (self.path,self.name),sep =',')

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