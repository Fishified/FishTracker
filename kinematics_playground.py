# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 11:19:04 2017

@author: dugj2403
"""
import pandas as pd

df1=pd.read_csv("Camera_10_treated.csv")
df2=pd.read_csv("Camera_10_treated.csv")


ax = df1.plot.scatter(x='x', y='u', color='DarkBlue', label='Group 1')
#df2.plot.scatter(x='Image frame', y='y', color='Yellow', label='Group 2', ax=ax)


