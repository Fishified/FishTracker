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
    
    def __init__(self,name,ppfileobj,pp_TV,ppFileLoaded_L,plot_L,calfile,origFlag,framerate,refpppath):
        
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
        self.pppath=refpppath
        
        with open(self.calfile) as f:
            self.calcontent = f.readlines()
  
        if origFlag == 0:

            self.cameraid=self.name[0:2]
            self.pdCSVfile.columns= ['Image frame', 'x_px','y_px']
            self.pdCSVfile=self.pdCSVfile.replace('0.0', np.nan)
            
            #add georeferenced coordinates
            self.pdCSVfile['x']=float(self.calcontent[3])+(float(self.calcontent[4])-self.pdCSVfile['x_px'])*float(self.calcontent[2])
            self.pdCSVfile['y']=(float(self.calcontent[5])-self.pdCSVfile['y_px'])*float(self.calcontent[2])
            self.pdCSVfile.to_csv('%s\\%s_orig.csv' % (self.pppath, self.cameraid),index_label=False,sep=',')
            self.pdCSVfile.to_csv('%s\\%s_treated.csv' %(self.pppath,self.cameraid),index_label=False,sep=',')
            self.treated=self.pdCSVfile
            self.kinematics()
           
        if origFlag == 1:
            self.pdCSVfile.to_csv('%s\Stitch_orig.csv'%self.pppath, index_label=False,sep=',')
            
            self.treated=self.pdCSVfile
            self.kinematics()
            self.treated = self.treated[['Image frame','x_px','y_px','x','y','u','v','up','down']]
            self.treated.to_csv('%s\Stitch_treated.csv'%self.pppath,index_label=False,sep=',')

    def show(self,state):

                  
        #show after undoing changes
        if state == 2:
            if self.name == "Stitch":              
                self.treated = pd.read_csv("%s\Stitch_orig.csv" %self.pppath,sep =',')
                self.kinematics()
                self.treated.to_csv('%s\Stitch_treated.csv'%self.pppath,index_label=False,sep=',')
            else:
                
                self.treated = pd.read_csv("%s\%s_orig.csv" % (self.pppath, self.cameraid),sep =',')
                self.kinematics()
 

        self.ppFileLoaded_L.setText("%s\%s.csv" % (self.pppath, self.name))      
        
        if 'Interpolated' in self.treated.columns:
            
            self.treated = self.treated[['Image frame','x_px','y_px','x','y','u','v','up','down','Interpolated','Interpolated_x']]
            
            
        else:
            
            self.treated = self.treated[['Image frame','x_px','y_px','x','y','u','v','up','down']]
            
#            try: self.cameraid
#            except NameError:
#                print "False"
#                self.treated.to_csv('%s\Stitch_treated.csv' % self.pppath, index_label=False,sep=',')
#            else:
#                print "True"
#                self.treated.to_csv('%s\%s_treated.csv' % (self.pppath, self.cameraid),index_label=False,sep=',')
#            
            
        self.pp_TV.setModel(PandasModel(self.treated))
#        self.pp_TV.setAlternatingRowColors(True)
#       se.setStyleSheet("alternate-background-color: yellow; background-color: red;")
        ax=self.treated.plot(x='up',y='y',kind='scatter',xlim=[0,10],ylim=[0,0.7],color='Red',figsize=(10,2))
        
        self.treated.plot(kind='scatter', x='down', y='y',ax=ax,color='Blue')
        
        if 'Interpolated' in self.treated.columns:
            self.treated.plot(kind='scatter', x='Interpolated_x', y='y',ax=ax,color='yellow')
            
        fig = ax.get_figure()
        fig.savefig('%s\%s.png' % (self.pppath,self.name))
        
        self.plot_L.setPixmap(QPixmap("%s\%s.png" % (self.pppath,self.name)))
        self.loadedFlag=1
    
    def blank(self,rowIndices):
        
        self.rowIndices=rowIndices
        
        for i in range(len(self.rowIndices)):
            self.treated.iloc[self.rowIndices[i].row(),1:10]=None
                              
        if self.name == "Stitch":
            self.treated.to_csv("%s\Stitch_treated.csv" %self.pppath,sep =',')
        else :
            self.treated.to_csv("%s\%s_treated.csv" % (self.pppath,self.cameraid),sep =',')

        self.show(0)
        
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
            
        self.treated.to_csv("%s\%s_treated.csv" % (self.pppath,self.cameraid),index_label=False,sep =',')
        self.show(1)
        
    def ppInterpolate(self):
        self.treated=self.treated.drop(['u','v','up','down'],axis=1)
        
        self.treated["Interpolated"]=0
        self.treated.ix[self.treated['x'].isnull(),'Interpolated']=1
        self.treated=self.treated.interpolate() 

        self.treated['Interpolated_x'] = np.where(self.treated['Interpolated'] == 1, self.treated['x'],None)
        self.kinematics()
        self.show(0)

    def kinematics(self):
        
        self.treated['u']=self.treated.x.diff()*self.framerate
        self.treated['v']=self.treated.y.diff()*self.framerate
        
        self.treated['up']=self.treated['x']
        self.treated['down']=self.treated['x']
    
        self.treated.ix[(self.treated['u']<0),'up']=None
        self.treated.ix[(self.treated['u']>=0),'down']=None
        self.treated.ix[self.treated['u'].isnull(),'down']=None
        self.treated.ix[self.treated['u'].isnull(),'up']=None
                        
    def errorRemoval(self):
        
        pass
        
        
        
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