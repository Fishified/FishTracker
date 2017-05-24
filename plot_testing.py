# -*- coding: utf-8 -*-
"""
Created on Wed May 24 09:11:35 2017

@author: Jason
"""
import os
import sys
from PyQt4.QtGui import *
 
import pandas as pd
#import matplotlib.pyplot as plt

pdCSVfile=pd.read_csv("10_raw.csv")
pdCSVfile.columns= ['Image frame', 'x-coordinate (px)','y-coordinate (px)']
pdCSVfile.plot.scatter(x='x-coordinate (px)',y='y-coordinate (px)', color='DarkBlue')


# Create window
app = QApplication(sys.argv)
w = QWidget()
w.setWindowTitle("PyQT4 Pixmap @ pythonspot.com ") 
 
# Create widget
label = QLabel(w)
pixmap = QPixmap(os.getcwd() + '/testplot.png')
label.setPixmap(pixmap)
w.resize(pixmap.width(),pixmap.height())
 
# Draw window
w.show()
app.exec_()