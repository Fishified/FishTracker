# -*- coding: utf-8 -*-
"""
Created on Thu Jun 08 11:19:04 2017

@author: dugj2403
"""
import pandas as pd

df=pd.read_csv("10_raw.csv")



df['u']=df.x.diff()*27
df['v']=df.y.diff()*27
df['up_x']=df['x']
df['down_x']=df['x']

df.ix[(df['u']<0),'up_x']=None
df.ix[(df['u']>=0),'down_x']=None
df.ix[df['u'].isnull(),'down_x']=None
df.ix[df['u'].isnull(),'up_x']=None
df.ix[df['u'].shift(-1).isnull,'up
   #df2.plot.scatter(x='Image frame', y='y', color='Yellow', label='Group 2', ax=ax)


