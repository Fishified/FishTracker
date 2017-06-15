# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 06:51:02 2017

@author: Thinkpad
"""


import sys
import numpy as np

from PyQt4 import QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class Qt4MplCanvas(FigureCanvas):

    def __init__(self):
# Standard Matplotlib code to generate the plot
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.x = np.arange(0.0, 3.0, 0.01)
        self.y = np.cos(2*np.pi*self.x)
        self.axes.plot(self.x, self.y)
        
# initialize the canvas where the Figure renders into
        FigureCanvas.__init__(self, self.fig)

# Create the GUI application
qApp = QtGui.QApplication(sys.argv)
# Create the Matplotlib widget
mpl = Qt4MplCanvas()
# show the widget
mpl.show()
# start the Qt main loop execution, exiting from this script
# with the same return code of Qt application
sys.exit(qApp.exec_())