# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 09:43:02 2017

@author: dugj2403
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time
from glob import glob

        
class stitchPlot:
    
    def __init__(self,items):
        self.items=items
        self.dfs=[]
        
        colors=['red','blue','black','darkgrey','green','magenta']
        
        for i in range(len(self.items)):
            self.dfs.append(self.items[i].dfTreated)
            if i == 0:
                ax=self.dfs[0].plot(x='x',y='u',kind='scatter',xlim=[0,10],color=colors[i],figsize=(10,2))
            else:
                self.dfs[i].plot(kind='scatter', x='x', y='u',ax=ax,color=colors[i]) 
                
        fig = ax.get_figure()
        fig.savefig('%s\stitchPlot.png' % self.items[0].path)
        
        time.sleep(0.1)
        
        self.dfsStacked=pd.concat(self.dfs)
        self.dfsStacked.to_csv("stacked.csv")

        
#    def plotTrend(self):
#        
# 
        
        
        
        #return fig