import pymel.core as pm
import os


qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance

qssFile = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'darkorange.qss'))

def getStyleSheet():
    if not os.path.isfile(qssFile):
        return pm.warning('stylesheet file not found')
    stream = QFile(qssFile)
    if stream.open(QFile.ReadOnly):
        st = str(stream.readAll())
        stream.close()
        return st
    else:
        print(stream.errorString())
        return pm.warning('Failing to load stylesheet')