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
import tb_timeline as tl
import maya.mel as mel
import maya.cmds as cmds
import maya.api.OpenMaya as om2
import pymel.core.datatypes as dt
import math
from Abstract import *

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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_motionTrails')
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='createMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.createMotionPath()'],
                                     help=self.helpStrings.createMotionTrail))
        self.addCommand(self.tb_hkey(name='removeMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.removeMotionPath()'],
                                     help=self.helpStrings.removeMotionTrail))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class MotionTrails(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'MotionTrails'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if MotionTrails.__instance is None:
            MotionTrails.__instance = object.__new__(cls)

        MotionTrails.__instance.val = cls.toolName
        return MotionTrails.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(MotionTrails, self).optionUI()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def createMotionPath(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        with self.funcs.keepSelection():
            trials = []
            for s in sel:
                cmds.select(s, replace=True)
                moTrail = cmds.snapshot(motionTrail=True,
                                        increment=1,
                                        startTime=self.funcs.getTimelineMin(),
                                        endTime=self.funcs.getTimelineMax())
                cmds.select(moTrail, replace=True)
                mel.eval("addToIsolation")

    def removeMotionPath(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            motionTrail = cmds.listConnections(s, type='motionTrail')
            if motionTrail:
                cmds.delete(motionTrail)
