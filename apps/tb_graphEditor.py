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
import maya.mel as mel
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
import maya.OpenMayaUI as omui


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbSetMoveKeyConstant',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyConstant()']))
        self.addCommand(self.tb_hkey(name='tbSetMoveKeyLinear',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyLinear()']))
        self.addCommand(self.tb_hkey(name='tbSetMoveKeyPower',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyPower()']))
        return self.commandList

    def assignHotkeys(self):
        return


class GraphEditor(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'GraphEditor'
    hotkeyClass = hotkeys()
    funcs = functions()

    customUiLocationOption = 'tbCustomGEUILocation'
    customUiLocation = ['AboveButtons', 'BelowButtons', 'BeforeButtons', 'AfterButtons', 'MenuBar']
    graphEditorToolbarOption = 'tbGraphEditorToolbarOption'

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
        super(GraphEditor, self).optionUI()
        useTumbleOptionWidget = optionVarBoolWidget('Use modified graph editor toolbar ', self.graphEditorToolbarOption)
        self.layout.addWidget(useTumbleOptionWidget)
        self.uiLocationWidget = comboBoxWidget(optionVar=self.customUiLocationOption,
                                                  values=self.customUiLocation,
                                                  defaultValue=pm.optionVar.get(self.customUiLocationOption,
                                                                                self.customUiLocation[0]),
                                                  label='Custom UI location')
        self.layout.addWidget(self.uiLocationWidget)
        # connect the checkbox changed event to the function that handles removing/adding the camera scriptJobs
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def deferredLoad(self):
        self.deferredLoadJob = cmds.scriptJob(event=('graphEditorChanged', self.loadGraphEditorModifications), runOnce=True)

    def loadGraphEditorModifications(self, *args):
        ge = cmds.getPanel(scriptType="graphEditor")
        for g in ge:
            control = omui.MQtUtil.findControl(g)
            if not control:
                continue
            pge = wrapInstance(int(control), QWidget)
            if pm.optionVar.get(self.graphEditorToolbarOption, False):
                self.allTools.tools['SlideTools'].modifyGraphEditorToolbar(pge)
            #self.createPopup(pge)

    def createPopup(self, graphEditor):
        if not hasattr(graphEditor, 'hasShiftPopup'):
            setattr(graphEditor, 'hasShiftPopup', False)
        if getattr(graphEditor, 'hasShiftPopup'):
            return
        name = 'graphEditor1GraphEdanimCurveEditorMenu'
        try:
            if cmds.popupMenu(name, query=True, exists=True):
                popup = cmds.popupMenu(name,
                                       ctrlModifier=False,
                                       shiftModifier=True,
                                       button=3,
                                       allowOptionBoxes=False,
                                       parent='graphEditor1GraphEd',
                                       markingMenu=True,
                                       postMenuCommandOnce=False,
                                       postMenuCommand=partial(self.graphEditorMenu, name))
                setattr(graphEditor, 'hasShiftPopup', True)
        except:
            pass

    def graphEditorMenu(self, menuName, *args):
        mode = self.getMoveKeyMode()
        cmds.popupMenu(menuName, edit=True, deleteAllItems=True)
        cmds.setParent(menuName, menu=True)
        cmds.menuItem('Key Move Mode', enable=False)
        cmds.menuItem(divider=True)

        constant = mode == 'constant'
        linear = mode == 'linear'
        power = mode == 'power'
        images = {True: 'checkboxOn.png', False: 'checkboxOff.png'}
        cmds.menuItem('Constant',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'constant'),
                      image=images[mode == 'constant'])
        cmds.menuItem('Linear',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'linear'),
                      image=images[mode == 'linear'])
        cmds.menuItem('Power',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'power'),
                      image=images[mode == 'power'])
        cmds.menuItem(parent=menuName,
                      divider=True)

    def getMoveKeyMode(self):
        mode = cmds.moveKeyCtx('moveKeyContext', query=True, moveFunction=True)
        return mode

    def setMoveKeyMode(self, mode, *args):
        cmds.moveKeyCtx('moveKeyContext', edit=True, moveFunction=mode)

    def setMoveKeyLinear(self):
        cmds.setToolTo('moveKeyContext')
        mel.eval("setToolTo $gMove;")
        self.setMoveKeyMode('linear')

    def setMoveKeyConstant(self):
        cmds.setToolTo('moveKeyContext')
        mel.eval("setToolTo $gMove;")
        self.setMoveKeyMode('constant')

    def setMoveKeyPower(self):
        mel.eval("setToolTo $gMove;")
        cmds.setToolTo('moveKeyContext')
        self.setMoveKeyMode('power')