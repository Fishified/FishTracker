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

        
class postProcessing:
    
    def __init__(self,name,ppfileobj,pp_TV,ppFileLoaded_L,plot_L,calfile,origFlag,framerate):
        
        self.plot_L=plot_L
        self.name=name
        self.ppfileobj=ppfileobj
        self.pp_TV=pp_TV
        self.ppFileLoaded_L=ppFileLoaded_L
        self.origFlag=origFlag
        self.loadedFlag=0
        self.framerate=framerate
        self.pdCSVfile=pd.read_csv(self.ppfileobj)
        self.calfile=calfile
        with open(self.calfile) as f:
            self.calcontent = f.readlines()
  
        if origFlag == 0:

            self.cameraid=self.name[0:2]
            self.pdCSVfile.columns= ['Image frame', 'x_px','y_px']
            self.pdCSVfile=self.pdCSVfile.replace('0.0', np.nan)

            #add georeferenced coordinates
            self.pdCSVfile['x']=float(self.calcontent[3])+(float(self.calcontent[4])-self.pdCSVfile['x_px'])*float(self.calcontent[2])
            self.pdCSVfile['y']=(float(self.calcontent[5])-self.pdCSVfile['y_px'])*float(self.calcontent[2])
            self.pdCSVfile.to_csv('%s_orig.csv' %self.cameraid,index_label=False,sep=',')
            self.pdCSVfile.to_csv('%s_treated.csv' %self.cameraid,index_label=False,sep=',')
            self.treated=self.pdCSVfile
           

        if origFlag == 1:
            self.pdCSVfile.to_csv('Stitch_orig.csv', index_label=False,sep=',')
            self.pdCSVfile.to_csv('Stitch_treated.csv',index_label=False,sep=',')
            self.treated=self.pdCSVfile
            self.kinematics()

    def show(self,state):

        #show for first time
        if state == 0 and self.loadedFlag == 0:
            self.treated = pd.read_csv("%s_orig.csv" % self.cameraid,sep =',')
            self.kinematics()
            
        #show after treating
        if state == 0 and self.loadedFlag == 1:
            self.treated=self.treated
            self.kinematics()
            
        if state==1:
            self.treated=self.treated
            self.kinematics()
            
        #show after undoing changes
        if state == 2:
            if self.name == "Stitch":
                self.treated = pd.read_csv("Stitch_orig.csv",sep =',')
                self.treated.to_csv('Stitch_treated.csv',index_label=False,sep=',')
            else:
                self.treated = pd.read_csv("%s_orig.csv" % self.cameraid,sep =',')
                self.treated.to_csv('%s_treated.csv' %self.cameraid,index_label=False,sep=',')
        if state == 3:
            if self.name == "Stitch":
                self.treated = pd.read_csv("Stitch_orig.csv",sep =',')
                self.treated.to_csv('Stitch_treated.csv',index_label=False,sep=',')

        
        self.ppFileLoaded_L.setText("%s.csv" % self.name)        
        self.pp_TV.setModel(PandasModel(self.treated))
        
        if 'Interpolated' in self.treated.columns:
            self.treated = self.treated[['Image frame','x_px','y_px','x','y','u','v','up','down','Interpolated','Interpolated_x']]
        else:
            self.treated = self.treated[['Image frame','x_px','y_px','x','y','u','v','up','down']]        

        ax=self.treated.plot(x='up',y='y',kind='scatter',xlim=[0,10],ylim=[0,0.635],color='Red',figsize=(10,2))
        self.treated.plot(kind='scatter', x='down', y='y',ax=ax,color='Blue')
        if 'Interpolated' in self.treated.columns:
            self.treated.plot(kind='scatter', x='Interpolated_x', y='y',ax=ax,color='yellow')

        fig = ax.get_figure()
        fig.savefig('%s.png' % self.name)
        
        self.plot_L.setPixmap(QPixmap("%s.png" % self.name))
        self.loadedFlag=1
    
    def blank(self,rowIndices):
        
        self.rowIndices=rowIndices
        
        for i in range(len(self.rowIndices)):
            self.treated.iloc[self.rowIndices[i].row(),1:10]=None
                              
        if self.name == "Stitch":
            self.treated.to_csv("Stitch_treated.csv",sep =',')
        else :
            self.treated.to_csv("%s_treated.csv" % self.cameraid,sep =',')

        self.show(1)
        
    def ppAdjust(self,adjust,state):
        #
        self.state=state
        self.adjust=int(adjust)

        if state == 1:
            df = pd.DataFrame(index=range(0,self.adjust),columns=['Image frame','x_px','y_px','x','y','u','v','up','down'], dtype='float')
            
            self.treated= pd.concat([df,self.treated])
            self.treated=self.treated.reset_index(drop=True)
            self.treated['Image frame'] = self.treated.index

        if state == 0:
            
            self.treated = self.treated.ix[self.adjust:]
            self.treated=self.treated.reset_index(drop=True)
            self.treated['Image frame'] = self.treated.index
            
        self.treated.to_csv("%s_treated.csv" % self.cameraid,index_label=False,sep =',')
        self.show(1)
        
    def ppInterpolate(self):
        self.treated["Interpolated"]=0
        self.treated.ix[self.treated['x'].isnull(),'Interpolated']=1
        self.treated=self.treated.interpolate() #interpolate values to use .diff()
        self.treated['Interpolated_x'] = np.where(self.treated['Interpolated'] == 1, self.treated['x'],None)
        self.show(1)

    def kinematics(self):
        
        self.treated['u']=self.treated.x.diff()*self.framerate
        self.treated['v']=self.treated.y.diff()*self.framerate
        
        self.treated['up']=self.treated['x']
        self.treated['down']=self.treated['x']
    
        self.treated.ix[(self.treated['u']<0),'up']=None
        self.treated.ix[(self.treated['u']>=0),'down']=None
        self.treated.ix[self.treated['u'].isnull(),'down']=None
        self.treated.ix[self.treated['u'].isnull(),'up']=None
        

        

        
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