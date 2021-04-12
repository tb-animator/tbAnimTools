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
import maya.mel as mel
import os, stat
import pickle

from Abstract import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_selection')
        self.commandList = list()
        # all curve selector
        self.addCommand(self.tb_hkey(name='select_all_anim_curves',
                                     annotation='',
                                     category=self.category,
                                     command=['SelectionTools.select_all_non_referenced_curves()']))
        # char set selector
        self.addCommand(self.tb_hkey(name='select_character_set_objs',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'SelectionTools.select_cheracter_set()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')

class SelectionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'SelectionTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if SelectionTools.__instance is None:
            SelectionTools.__instance = object.__new__(cls)

        SelectionTools.__instance.val = cls.toolName
        return SelectionTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(SelectionTools, self).optionUI()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    @staticmethod
    def select_all_non_referenced_curves():
        cmds.select([curve for curve in cmds.ls(type=["animCurveTL", "animCurveTU", "animCurveTA", "animCurveTT"]) if
                     not cmds.referenceQuery(curve, isNodeReferenced=True) and not
                     cmds.lockNode(curve, query=True, lock=True)[0]], replace=True)

    def select_cheracter_set(self):
        selection = pm.ls(selection=True)
        _characters = []  # will be a list of all associated character sets to seleciton
        if selection:
            for obj in selection:
                _char = pm.listConnections(obj, destination=True,
                                           connections=True,
                                           type='character')
                if _char:
                    if not _char[0][1] in _characters:
                        _characters.append(_char[0][1])

            out_obj = []
            for char in _characters:
                _obj_list = pm.sets(char, query=True, nodesOnly=True)
                for obj in _obj_list:
                    out_obj.append(obj)
            pm.select(out_obj, add=True)
        else:
            msg = 'no character sets found for selection'
            self.funcs.errorMessage(position="botRight", prefix="Error", message=msg, fadeStayTime=3.0, fadeOutTime=4.0)


'''    


# class for pickwalking, supports message attributes (more reliable)
class pickwalker(object):
    """
    OLD
    """

    def __init__(self):
        self.up = 'cgTkPickWalkup'
        self.down = 'cgTkPickWalkdown'
        self.left = 'cgTkPickWalkleft'
        self.right = 'cgTkPickWalkright'

    def walk(self, up=False, down=False, left=False, right=False, add=False):
        if up:
            dir = self.up
            cmd = "pickWalkUp"
        elif down:
            dir = self.down
            cmd = "pickWalkDown"
        elif left:
            dir = self.left
            cmd = "pickWalkLeft"
        elif right:
            dir = self.right
            cmd = "pickWalkRight"

        allObj = pm.ls(selection=True)
        if allObj:
            return_objs = []
            for obj in allObj:
                try:
                    attribute = pm.Attribute(obj + "." + dir)
                    print attribute
                    print attribute, attribute.exists(), attribute.type()
                    if attribute.exists():
                        # check if the attribute is a message attr
                        if attribute.type() == 'message':
                            destination = pm.listConnections(attribute)
                            return_objs.append(destination)
                        else:
                            # get string attr
                            destination = pm.PyNode("%s%s" % (obj.namespace(), attribute.get()))
                            return_objs.append(destination)
                except:
                    pass
            if return_objs:
                pm.select(return_objs, replace=not add, add=add)
            else:
                mel.eval(cmd)
                if add:
                    pm.select(allObj, add=True)

'''