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
import maya.mel as mel
import pymel.core.datatypes as dt
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
        self.setCategory(self.helpStrings.category.get('snap'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='store_ctrl_transform', annotation='store object transform',
                                     category=self.category, command=[
                'SnapTools.store_transform()']))
        self.addCommand(self.tb_hkey(name='restore_ctrl_transform', annotation='restore object transform',
                                     category=self.category, command=[
                'SnapTools.restore_transform()']))
        self.addCommand(self.tb_hkey(name='snap_objects', annotation='snap selection',
                                     category=self.category, command=[
                'SnapTools.snap_selection()']))
        self.addCommand(self.tb_hkey(name='point_snap_objects', annotation='point snap selection',
                                     category=self.category, command=[
                'SnapTools.point_snap_selection()']))
        self.addCommand(self.tb_hkey(name='orient_snap_objects', annotation='orient snap selection',
                                     category=self.category, command=[
                'SnapTools.orient_snap_selection()']))

        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class SnapTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'SnapTools'
    hotkeyClass = None
    funcs = None

    transformTranslateDict = dict()
    transformRotateDict = dict()

    def __new__(cls):
        if SnapTools.__instance is None:
            SnapTools.__instance = object.__new__(cls)

        SnapTools.__instance.val = cls.toolName
        return SnapTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(SnapTools, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    @staticmethod
    def minus(vector1, vector2):
        # TODO use actual vectors
        return [vector1[0] - vector2[0], vector1[1] - vector2[1], vector1[2] - vector2[2]]

    @staticmethod
    def plus(vector1, vector2):
        # TODO use actual vectors
        return [vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2]]

    def snap_selection(self, translate=True, orient=True):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        if len(sel) >= 2:
            original = sel[0]
            target = sel[1]

        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            for x in xrange(int(startTime), int(endTime)):
                cmds.currentTime(x)
                self.snap_object(original, target, translate, orient)
        else:
            self.snap_object(original, target, translate, orient)

    def point_snap_selection(self):
        self.snap_selection(translate=True, orient=False)

    def orient_snap_selection(self):
        self.snap_selection(translate=False, orient=True)

    def snap_object(self, original, target, translate, orient):
        original_rotation = self.get_world_rotation(original)
        original_pivot_position = self.get_world_pivot(original)
        original_world_position = self.get_world_space(original)

        target_rotation = self.get_world_rotation(target)
        target_pivot_position = self.get_world_pivot(target)
        target_world_position = self.get_world_space(target)

        _pivot_difference = self.minus(target_pivot_position, original_pivot_position)
        _out_position = self.plus(original_world_position, _pivot_difference)

        if translate:
            self.set_world_translation(original, _out_position)

        if not orient:
            self.set_world_rotation(original, target_rotation)

            rot = pm.xform(target, query=True, absolute=True, worldSpace=True, rotation=True)
            node_ro = pm.xform(original, query=True, rotateOrder=True)
            ro = pm.xform(target, query=True, rotateOrder=True)
            pm.xform(original, absolute=True, worldSpace=True, rotation=rot, rotateOrder=ro, preserve=True)
            pm.xform(original, rotateOrder=node_ro, preserve=True)

    def store_transform(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        for s in sel:
            pos = self.get_world_space(s)
            rot = self.get_world_rotation(s)
            self.transformTranslateDict[s] = pos
            self.transformRotateDict[s] = rot

        self.transformTranslateDict['LASTUSED'] = pos
        self.transformRotateDict['LASTUSED'] = rot
        pass

    def restore_transform(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            for x in xrange(int(startTime), int(endTime)):
                cmds.currentTime(x)
                self.restoreTansformToSelection(sel)
        else:
            self.restoreTansformToSelection(sel)

    def restoreTansformToSelection(self, sel):
        if len(sel) == 1:
            pos = self.transformTranslateDict.get('LASTUSED', None)
            rot = self.transformRotateDict.get('LASTUSED', None)
            if pos:
                self.set_world_translation(sel[0], pos)
            if rot:
                self.set_world_rotation(sel[0], rot)
            return
        for s in sel:
            pos = self.transformTranslateDict.get(s, self.transformTranslateDict.get('LASTUSED', None))
            rot = self.transformRotateDict.get(s, self.transformRotateDict.get('LASTUSED', None))
            if pos:
                self.set_world_translation(s, pos)
            if rot:
                self.set_world_rotation(s, rot)

    @staticmethod
    def get_world_pivot(node):
        # get the world pivot
        return pm.xform(node, query=True, worldSpace=True, rotatePivot=True)

    @staticmethod
    def get_world_space(node):
        # gets the world space, not really world space tho, just what maya thinks is world space
        return pm.xform(node, query=True, relative=True, worldSpace=True, translation=True)

    @staticmethod
    def set_world_translation(node, position):
        # set the world space position on the object
        pm.xform(node, absolute=True, worldSpace=True, translation=position)

    @staticmethod
    def get_world_rotation(node):
        # get the absolute world rotation of the object
        return pm.xform(node, query=True, absolute=True, worldSpace=True, rotation=True)

    @staticmethod
    def set_world_rotation(node, rotation):
        # set the absolute world rotation
        pm.xform(node, absolute=True, worldSpace=True, rotation=rotation)
