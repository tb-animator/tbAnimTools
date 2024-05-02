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
    visit https://tbanimtools.blogspot.com/ for "stuff"


*******************************************************************************
'''
import os
import maya.cmds as cmds
from tb_UI import *
import pymel.core as pm
from pluginLookup import ClassFinder
import getStyleSheet as getqss
import re
if not pm.optionVar(exists='playblast_folder'):
    pm.optionVar(stringValue=('playblast_folder', "c:"))

script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

import maya.OpenMayaUI as omUI

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    #from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    #from pyside2uic import *
    from shiboken2 import wrapInstance


def getMainWindow():
    return wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)


def showOptions():
    optionWindow = mainOptionWindow()
    optionWindow.showUI()


class mainOptionWindow(QMainWindow):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __instance = None
    appWin = getMainWindow()
    win = None
    tbtoolsCLS = ClassFinder()

    def __init__(self):
        super(mainOptionWindow, self).__init__(self.appWin)

    def initColor(self):
        windowCss = '''
        QFrame {
            background-color: rgb(90,90,90);
            border: 1px solid rgb(90,70,30);
        }
        QFrame#SideBar {
            background-color: rgb(50,50,50);
            border: 1px solid rgb(255,255,255);
        QDialog::title {
            height: 24px;
            font-weight: bold;
            color: #000000;
            background: #ffffff;
         }
        }'''
        self.setStyleSheet(windowCss)

    def buildUI(self):
        self.win = QDialog(parent=self.appWin)
        self.win.setStyleSheet(getqss.getStyleSheet())
        self.win.setWindowTitle('tbAnimTools - option')
        self.win.setMinimumWidth(700)
        #self.win.setMinimumHeight(300)
        self.mainLayout = QHBoxLayout()

        self.toolTypeScrollArea = QScrollArea()
        self.toolWidget = QListWidget()
        self.toolTypeScrollArea.setWidget(self.toolWidget)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.toolTypeScrollArea.setFixedWidth(148)
        self.toolTypeScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.optionUIScrollArea = QScrollArea()
        self.optionUIScrollArea.setWidgetResizable(True)
        self.optionUIScrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.optionUIScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.toolLayout = QVBoxLayout()
        self.toolWidget.setLayout(self.toolLayout)

        self.toolOptionStack = QStackedWidget(self)
        self.toolOptionStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolOptionLayout = QVBoxLayout(self)

        self.toolHotkeyStack = QStackedWidget(self)
        self.toolHotkeyStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolHotkeyLayout = QVBoxLayout(self)

        self.leftLayout = QVBoxLayout()
        self.toolLabel = QLabel('Tools')
        self.leftLayout.addWidget(self.toolLabel)
        self.leftLayout.addWidget(self.toolTypeScrollArea)

        self.tabWidget = QTabWidget()

        self.win.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addWidget(self.tabWidget)


        self.tabWidget.addTab(self.toolOptionStack, "Tool Options")
        self.tabWidget.addTab(self.toolHotkeyStack, "Tool Hotkeys")

        # find tools with UI, make list of tool keys?
        for index, tool in enumerate(sorted(self.tbtoolsCLS.tools.keys(), key=lambda x: x.lower())):
            if self.tbtoolsCLS.tools[tool] is not None:
                optionUI = self.tbtoolsCLS.tools[tool].optionUI()
                hotkeyUI = self.tbtoolsCLS.tools[tool].hotkeyUI()
                if not optionUI:
                    continue
                self.toolWidget.insertItem(index, re.sub("([a-z])([A-Z])", "\g<1> \g<2>", tool))
                self.toolOptionStack.addWidget(optionUI)
                self.toolHotkeyStack.addWidget(hotkeyUI)

        self.toolWidget.currentRowChanged.connect(self.displayToolOptions)
        self.update()
        self.resize(self.sizeHint())

    def displayToolOptions(self, index):
        self.toolOptionStack.setCurrentIndex(index)
        self.toolHotkeyStack.setCurrentIndex(index)

    def showUI(self):
        self.buildUI()
        self.win.show()
        self.initColor()
