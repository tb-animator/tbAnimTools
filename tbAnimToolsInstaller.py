from __future__ import absolute_import
from __future__ import print_function
'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2020-Tom Bailey
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    send issues/ requests to brimblashman@gmail.com
    visit https://tbanimtools.blogspot.com/ for "more info"

    usage


*******************************************************************************
'''
"""
Installer used to install the main tbAnimTools without having to go to github.
"""


import sys
import pymel.core as pm
import glob
if sys.version_info >= (2, 8):
    from urllib.request import *
else:
    from urllib2 import *

import zipfile
from distutils.dir_util import copy_tree, create_tree
import os
import inspect
import json
import datetime
import maya.OpenMayaUI as omUI

def onMayaDroppedPythonFile(*args):
    print(args)
    print(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    cls = tbAnimToolsInstaller()
    cls.show()


qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance

styleSheet = '''
QLabel
{
    font-weight: bold; font-size: 18px;
}
QPushButton
{
    color: #b1b1b1;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
    border-width: 1px;
    border-color: #1e1e1e;
    border-style: solid;
    border-radius: 6;
    padding: 3px;
    font-size: 12px;
    padding-left: 5px;
    padding-right: 5px;
}

QPushButton:pressed
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
}

QPushButton:hover
{
    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);
}
'''

class tbAnimToolsInstaller(QDialog):
    oldPos = None

    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(tbAnimToolsInstaller, self).__init__(parent=parent)
        self.datUrl = 'https://api.github.com/repos/tb-animator/tbAnimTools'
        self.master_url = 'https://raw.githubusercontent.com/tb-animator/tbtools/master/'
        self.latestZip = 'https://github.com/tb-animator/tbAnimTools/archive/refs/heads/main.zip'
        self.realPath = os.path.realpath(__file__)
        self.basename = os.path.basename(__file__)
        self.base_dir = os.path.normpath(os.path.dirname(__file__))
        self.subFolder = 'tbAnimTools'
        self.defaultInstallPath = os.path.join(self.base_dir, self.subFolder)
        self.versionDataFile = None
        self.dateFormat = '%Y-%m-%dT%H:%M'
        self.uiDateFormat = '%Y-%m-%d'
        self.timeFormat = '%H:%M'

        self.installPath = None
        # self.stylesheet = .getStyleSheet()
        # self.setStyleSheet(self.stylesheet)

        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)


        self.mainLayout = QVBoxLayout()
        self.layout = QVBoxLayout()

        self.titleText = QLabel('tbAnimTools installer')
        self.titleText.setStyleSheet(styleSheet)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.infoText = QLabel('Welcome to tbAnimTools, click install to choose the installation directory')
        self.installButton = QPushButton('Install')
        self.installButton.setStyleSheet(styleSheet)
        self.installButton.clicked.connect(self.installTools)

        self.filePathLayout = QHBoxLayout()
        self.pathLabel = QLabel('Install to ::')
        self.pathLineEdit = QLineEdit(self.defaultInstallPath)
        self.cle_action_pick = self.pathLineEdit.addAction(QIcon(":/folder-open.png"),
                                                              QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick destination folder to install tbAnimTools to')
        self.cle_action_pick.triggered.connect(self.pickInstallFolder)
        self.filePathLayout.addWidget(self.pathLabel)
        self.filePathLayout.addWidget(self.pathLineEdit)
        # self.infoText.setStyleSheet(self.stylesheet)

        self.mainLayout.addWidget(self.titleText)
        self.mainLayout.addLayout(self.layout)
        self.layout.addWidget(self.infoText)

        self.layout.addLayout(self.filePathLayout)
        self.layout.addWidget(self.installButton)

        self.setLayout(self.mainLayout)


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(tbAnimToolsInstaller, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def createVersionFile(self):
        dataPath = os.path.join(self.installPath, 'appData')
        self.versionDataFile = os.path.join(dataPath, 'tbVersion.json')
        if not os.path.isdir(dataPath):
            os.mkdir(dataPath)
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)

        jsonObjectInfo['version'] = datetime.datetime.utcnow().strftime(self.dateFormat)
        jsonString = json.dumps(jsonObjectInfo, indent=4, separators=(',', ': '))

        jsonFile = open(self.versionDataFile, 'w')

        jsonFile.write(jsonString)
        jsonFile.close()

    def pickInstallFolder(self):
        self.installPath = pm.fileDialog2(caption='tbAnimTools :: Choose installation directory',
                                          fileFilter='',
                                          dialogStyle=1,
                                          fileMode=3)
        if not self.installPath:
            return
        self.installPath = os.path.join(self.installPath[0], self.subFolder)
        self.pathLineEdit.setText(self.installPath)

    def installTools(self):
        self.installPath = self.pathLineEdit.text()
        self.download_project_files()
        self.createVersionFile()
        self.installModule()

    def download_project_files(self):
        if not os.path.isdir(self.installPath):
            os.mkdir(self.installPath)
        print("downloading zip file to", self.installPath)
        filedata = urlopen(self.latestZip)
        datatowrite = filedata.read()
        zipFile = os.path.join(self.installPath, 'tbAnimToolsLatest.zip')
        with open(zipFile, 'wb') as f:
            f.write(datatowrite)

        destinationPath = os.path.normpath(os.path.join(self.installPath, 'extract'))
        print("extracting zip file to %s" % destinationPath)
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(destinationPath)
        destinationPathFinal = os.path.normpath(os.path.join(self.installPath))

        print("copying extracted files to ", destinationPathFinal)
        extractedSubFolder = os.path.join(destinationPath, 'tbAnimTools-main')
        all_folders = list()
        for root, dirs, files in os.walk(extractedSubFolder):
            p = root[len(extractedSubFolder):]
            newPath = os.path.join(self.installPath + os.path.normpath(p))
            if not os.path.isdir(newPath):
                os.mkdir(newPath)
        copy_tree(extractedSubFolder, destinationPathFinal)

        message_state = pm.optionVar.get("inViewMessageEnable", 1)
        pm.optionVar(intValue=("inViewMessageEnable", 1))
        pm.inViewMessage(amg='tbAnimTools download complete',
                         pos='botRight',
                         dragKill=True,
                         fadeOutTime=10.0,
                         fade=False)
        pm.optionVar(intValue=("inViewMessageEnable", message_state))
        self.close()

    def installModule(self):
        sys.path.append(self.installPath)
        import tbtoolsInstaller as tbInstaller
        tbInstaller.install()


if __name__ == "__main__":
    cls = tbAnimToolsInstaller()
    cls.show()