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

maya.utils.loadStringResourcesForModule(__name__)
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

        self.addCommand(self.tb_hkey(name='toggle_isolate_selection',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.toggle_isolate_selection'],
                                     command=['isolator.toggle_isolate()']))
        self.addCommand(self.tb_hkey(name='addToIsolation',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.addToIsolation'],
                                     command=['isolator.addToIsolation()']))

        return self.commandList

    def assignHotkeys(self):
        return


class isolator(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'isolator'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if isolator.__instance is None:
            isolator.__instance = object.__new__(cls)

        isolator.__instance.val = cls.toolName
        return isolator.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(isolator, self).optionUI()

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def toggle_isolate(self):
        '''
        import isolate as iso
        reload (iso)
        iso.isolate()
        '''
        panel = self.funcs.getModelPanel()

        state = cmds.isolateSelect(panel, query=True, state=True)
        if state:
            cmds.isolateSelect(panel, state=0)
            pm.isolateSelect(panel, removeSelected=True)
        else:
            cmds.isolateSelect(panel, state=1)
            cmds.isolateSelect(panel, addSelected=True)

    def addToIsolation(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        panels = self.funcs.getAllModelPanels()
        if not panels:
            return
        for p in panels:
            state = pm.isolateSelect(p, query=True, state=True)
            if state:
                cmds.isolateSelect(p, addSelected=True)
