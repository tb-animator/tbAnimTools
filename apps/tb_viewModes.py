'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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
    visit tb-animator.blogspot.com for "stuff"

    usage


*******************************************************************************
'''
import pymel.core as pm
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
import maya.cmds as cmds
import pymel.core as pm
from Abstract import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_view')
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='ViewMode_xray_joints', annotation='',
                                     category=self.category,
                                     command=['viewModeTool.toggleXrayJoints()']))
        self.addCommand(self.tb_hkey(name='ViewMode_xray',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.toggleXray()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_Joints',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewControls()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_Meshes',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewMeshes()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_All',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewAll()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class viewModeTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'viewModeTool'
    hotkeyClass = None
    funcs = None

    def __new__(cls):
        if viewModeTool.__instance is None:
            viewModeTool.__instance = object.__new__(cls)

        viewModeTool.__instance.val = cls.toolName
        return viewModeTool.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(viewModeTool, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def viewNone(self, panel):
        cmds.modelEditor(panel, edit=True,
                         allObjects=False)

    def viewMeshes(self):
        panel = self.funcs.getModelPanel()
        self.viewNone(panel)
        cmds.modelEditor(panel, edit=True,
                         polymeshes=True,
                         nurbsSurfaces=True)
        cmds.modelEditor(panel, edit=True,
                         pluginObjects=('gpuCacheDisplayFilter', True))

    def viewControls(self):
        panel = self.funcs.getModelPanel()
        self.viewNone(panel)
        cmds.modelEditor(panel, edit=True,
                         joints=True,
                         nurbsCurves=True)
        cmds.modelEditor(panel, edit=True,
                         pluginObjects=('gpuCacheDisplayFilter', True))
        cmds.modelEditor(panel, edit=True,
                         greasePencils=True)

    def viewAll(self):
        panel = self.funcs.getModelPanel()
        cmds.modelEditor(panel, edit=True,
                         allObjects=True)

    def toggleXrayJoints(self):
        panel = self.funcs.getModelPanel()
        cmds.modelEditor(panel, edit=True,
                         jointXray=not cmds.modelEditor(panel, query=True, jointXray=True))

    def toggleXray(self):
        panel = self.funcs.getModelPanel()
        cmds.modelEditor(panel, edit=True,
                         xray=not cmds.modelEditor(panel, query=True, xray=True))
