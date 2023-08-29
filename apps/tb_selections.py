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
import re
from difflib import SequenceMatcher, get_close_matches, ndiff
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

import maya.cmds as cmds
import maya.mel as mel
import os, stat
import pickle

from Abstract import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('selection'))
        self.commandList = list()
        # all curve selector

        self.addCommand(self.tb_hkey(name='select_all_character',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.select_all_character'],
                                     command=['SelectionTools.selectAllCharacter()']))
        self.addCommand(self.tb_hkey(name='select_all_anim_curves',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.select_all_anim_curves'],
                                     command=['SelectionTools.select_all_non_referenced_curves()']))
        # char set selector
        self.addCommand(self.tb_hkey(name='select_character_set_objs',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.select_character_set_objs'],
                                     command=[
                                         'SelectionTools.select_cheracter_set()']))
        return self.commandList

    def assignHotkeys(self):
        return


class SelectionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'SelectionTools'
    hotkeyClass = hotkeys()
    funcs = functions()
    lastSelected = None

    def __new__(cls):
        if SelectionTools.__instance is None:
            SelectionTools.__instance = object.__new__(cls)

        SelectionTools.__instance.val = cls.toolName
        return SelectionTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(SelectionTools, self).optionUI()
        return None

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

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

    def selectAllCharacter(self):
        """
        Attempts to select all logically named controls for a single character.
        If there is no selection, it will reselect the last known character
        :return:
        """
        finalControls = list()
        namespace = str()
        sel = cmds.ls(sl=True)
        if not sel:
            if self.lastSelected is None:
                return
            if cmds.objExists(self.lastSelected):
                sel = [self.lastSelected]
        CharacterTool = self.allTools.tools['CharacterTool']
        characters = self.funcs.splitSelectionToCharacters(sel)

        for ch, controls in characters.items():
            refname, namespace = CharacterTool.getSelectedChar(controls[0])
            allControls = CharacterTool.getCharacterByName(refname).controls
            if allControls:
                finalControls.extend([namespace + c for c in allControls])
            else:
                if ':' in controls[0]:
                    splitName = controls[0].split(':')
                    mainNamespace = controls[0].rsplit(':', 1)
                    if len(splitName) > 1:
                        namespace = splitName[0]
                    s = splitName[-1]
                else:
                    mainNamespace = ':'
                    s = controls[0]
                prefix = re.split('[^a-zA-Z0-9]+', s)

                matchingPrefix = self.getSimilarControls(mainNamespace[0], controls, prefix)

                if matchingPrefix:
                    finalControls.extend(matchingPrefix)
        finalControls = [c for c in finalControls if cmds.objExists(c)]
        cmds.select(finalControls, add=True)
        self.lastSelected = sel[0]

    def getOppositeControl(self, name, constraint=False, shape=True):
        if ':' in name:
            namespace, control = name.rsplit(':', 1)
        else:
            namespace = str()
            control = str(name)
        prefix = re.split('[^a-zA-Z0-9]+', control)
        matchingPrefix = self.getSimilarControls(namespace, control, prefix, constraint=False, shape=True)
        st = self.funcs.stripTailDigits(control)
        tailLen = len(control) - len(st)

        strippedMatches = [c.rsplit(':', 1)[-1] for c in matchingPrefix if st not in c]
        if st in strippedMatches:
            strippedMatches.remove(st)

        matches = get_close_matches(st, [x[:len(x) - tailLen] for x in strippedMatches], cutoff=0.5)
        opposites = [m for m in matches if m != st]

        if opposites:
            if tailLen > 0:
                op = opposites[0] + control[-tailLen:]
            else:
                op = opposites[0]
            return namespace + ':' + op

    def getLowerControl(self, input):
        s = input.split(':')[-1]
        prefix = re.split('[^a-zA-Z0-9]+', s)
        matchingPrefix = self.getSimilarControls(input, prefix)
        st = self.funcs.stripTailDigits(s)
        tailLen = len(s) - len(st)

        matches = get_close_matches(st, [x[:len(x) - tailLen] for x in matchingPrefix])

    def getSimilarControls(self, namespace, sel, prefix, constraint=False, shape=True):
        matching = cmds.ls('{ns}:{ct}*'.format(ns=namespace, ct=prefix[0]), type='transform')
        if not constraint:
            matching = [x for x in matching if 'Constraint' not in cmds.objectType(x)]
        if shape:
            matching = [x for x in matching if cmds.listRelatives(x, shapes=True)]
        if sel in matching:
            matching.remove(sel)
        return matching

