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
import pymel.core as pm
import maya.cmds as cmds

from Abstract import *
import maya
import maya.OpenMayaUI as omui
# maya.utils.loadStringResourcesForModule(__name__)
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
__author__ = 'tom.bailey'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        return self.commandList

    def assignHotkeys(self):
        return


class ShotCam(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'ShotCam'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if ShotCam.__instance is None:
            ShotCam.__instance = object.__new__(cls)

        ShotCam.__instance.val = cls.toolName
        return ShotCam.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(ShotCam, self).optionUI()

    def showUI(self):
        self.shotCam = ShotCamViewport()
        self.shotCam.show()

    def drawMenuBar(self, parentMenu):
        return None
    @classmethod
    def create_simulated_model_panel(self):
        model_panel = cmds.modelPanel("shotCamModelPanel", label="shotCamModelPanel")
        cmds.modelEditor(model_panel, e=True, allObjects=False)
        cmds.modelEditor(model_panel, e=True, grid=False)
        return model_panel


class ShotCamViewport(QMainWindow):
    def __init__(self, parent=None):
        super(ShotCamViewport, self).__init__(parent)
        self.setWindowTitle("ShotCam")
        self.setGeometry(100, 100, 800, 600)

        self.model_panel = ShotCam.create_simulated_model_panel()
        self.model_panel_widget = wrapInstance(int(omui.MQtUtil.findControl(self.model_panel)), QWidget)

        layout = QVBoxLayout()
        layout.addWidget(self.model_panel_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
