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
from functools import partial
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
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()
        '''
        self.addCommand(self.tb_hkey(name='example',
                                     annotation='',
                                     category=self.category,
                                     command=['example.exampleFunc()']))
        '''
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class GraphEditor(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Graph Editor'
    hotkeyClass = hotkeys()
    funcs = functions()



    def __new__(cls):
        if GraphEditor.__instance is None:
            GraphEditor.__instance = object.__new__(cls)

        GraphEditor.__instance.val = cls.toolName
        return GraphEditor.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(GraphEditor, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def deferredLoad(self):
        try:
            self.createPopup()
        except:
            self.deferredLoadJob = cmds.scriptJob(runOnce=True,  event=('PostSceneRead', self.createPopup))

    def createPopup(self, *args):
        print ('createPopup')
        if self.deferredLoadDone:
            return
        name = 'canvasLayout|graphEditor1GraphEdanimCurveEditorMenu'
        print (name)
        popup = cmds.popupMenu(name,
                               ctrlModifier=False,
                               shiftModifier=True,
                               button=3,
                               allowOptionBoxes=False,
                               parent='graphEditor1GraphEd',
                               markingMenu=True,
                               postMenuCommandOnce=False,
                               postMenuCommand=partial(self.graphEditorMenu))
        self.deferredLoadDone = True

    def graphEditorMenu(self, menuName, *args):
        mode = self.getMoveKeyMode()
        cmds.popupMenu(menuName, edit=True, deleteAllItems=True)
        cmds.setParent(menuName, menu=True)
        cmds.menuItem('Key Move Mode', enable=False)
        cmds.menuItem(divider=True)

        constant = mode=='constant'
        linear = mode=='linear'
        power = mode=='power'
        images = {True:'checkboxOn.png', False:'checkboxOff.png'}
        cmds.menuItem('Constant',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'constant'),
                      image=images[mode=='constant'])
        cmds.menuItem('Linear',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'linear'),
                      image=images[mode=='linear'])
        cmds.menuItem('Power',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'power'),
                      image=images[mode=='power'])
        cmds.menuItem(parent=menuName,
                      divider=True)

    def getMoveKeyMode(self):
        mode = cmds.moveKeyCtx('moveKeyContext', query=True, moveFunction=True)
        return mode

    def setMoveKeyMode(self, mode, *args):
        cmds.moveKeyCtx('moveKeyContext', edit=True, moveFunction=mode)