# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 08:54:47 2016

@author: Jason
"""

import os
import sys

ui_filename= sys.argv[1]


os.system('python C:\Users\Jason\Anaconda2\Lib\site-packages\PyQt4\uic\pyuic.py %s.ui -o %s.py' %(ui_filename, ui_filename))
#os.system('python C:\Users\dugj2403\AppData\Local\Continuum\Anaconda2\Lib\site-packages\PyQt4\uic\pyuic.py %s.ui -o %s.py' %(ui_filename, ui_filename))


os.system('C:\Users\Jason\Anaconda2\Library\Bin\pyrcc4.exe -o .\icons_rc.py .\icons.qrc')