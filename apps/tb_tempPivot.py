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
from functools import partial
from Abstract import *

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

assetCommandName = 'tempPivotControlCommand'

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('tempPivot'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='create_temp_pivot',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivot()']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for temp controls',
                                     category=self.category, command=['TempPivot.assetRmbCommand()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class TempPivot(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'TempPivot'
    hotkeyClass = hotkeys()
    funcs = functions()

    scriptJobs = list()
    crossSizeOption = 'tbBakeLocatorSize'
    assetName = 'TempPivotControls'
    constraintTargetAttr = 'constraintTarget'
    assetCommandName = assetCommandName

    def __new__(cls):
        if TempPivot.__instance is None:
            TempPivot.__instance = object.__new__(cls)

        TempPivot.__instance.val = cls.toolName
        return TempPivot.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(TempPivot, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = pm.ls(sl=True)
        asset = pm.container(query=True, findContainer=sel[0])

        # check asset message attribute
        # print ("asset", asset, sel)

        cmds.menuItem(label='Temp Pivot Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Bake selected temp pivots to layer',
                      command=pm.Callback(self.bakeSelectedCommand, asset, sel))
        cmds.menuItem(label='Bake all temp pivots to layer', command=pm.Callback(self.bakeAllCommand, asset, sel))
        # cmds.menuItem(label='Bake out to layer', command=pm.Callback(self.bakeOutCommand, asset))
        cmds.menuItem(label='Delete all temp pivots', command=pm.Callback(self.deleteControlsCommand, asset, sel))
        cmds.menuItem(divider=True)

    def bakeSelectedCommand(self, asset, sel):
        return

    def bakeAllCommand(self, asset, sel):
        return

    def deleteControlsCommand(self, asset, sel):
        return


    def createControl(self, target):
        loc = self.funcs.tempLocator(name=target, suffix='tmp')
        pm.delete(pm.parentConstraint(target, loc))
        return loc

    def completedScriptJob(self, targets, loc, frame):
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True, event=['SelectionChanged', partial(self.bake, targets, loc, frame)]))
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True, event=['ToolChanged', partial(self.bake, targets, loc, frame)]))
        # self.scriptJobs.append(pm.scriptJob(runOnce=True, timeChange=partial(self.bake, targets, loc, frame)))

    def clearScriptJobs(self):
        for j in self.scriptJobs:
            try:
                pm.scriptJob(kill=j)
            except:
                pass

    def bake(self, targets, loc, frame):
        self.clearScriptJobs()

        cmds.currentTime(frame)
        control = self.funcs.tempControl(name=targets[-1], suffix='Pivot', drawType='orb',
                                     scale=pm.optionVar.get(self.crossSizeOption, 1))
        pm.delete(pm.parentConstraint(loc, control))
        pm.delete(loc)

        mainConstraint = pm.parentConstraint(targets[-1], control, maintainOffset=True)
        keyRangeStart = cmds.playbackOptions(query=True, min=True)
        keyRangeEnd = cmds.playbackOptions(query=True, max=True)

        ps = pm.PyNode(targets[-1])
        ns = ps.namespace()
        if not cmds.objExists(ns + self.assetName):
            self.createAsset(ns + self.assetName, imageName=None)
        asset = ns + self.assetName

        pm.addAttr(control, ln=self.constraintTargetAttr, at='message')
        pm.connectAttr(targets[-1] + '.message', control + '.' + self.constraintTargetAttr)

        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=control)

        bakeTargets = list()
        targetParents = dict()
        targetConstraints = dict()

        for t in targets:
            grp = pm.createNode('transform', name=str(t) + '_tmpGrp')
            pm.parent(grp, control)
            targetParents[t] = grp
            targetConstraints[t] = pm.parentConstraint(t, grp)
            bakeTargets.append(grp)

            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=grp)

        bakeTargets.append(control)
        pm.bakeResults(bakeTargets,
                       time=(keyRangeStart, keyRangeEnd),
                       simulation=False,
                       sampleBy=1)
        pm.delete(mainConstraint)
        pm.delete(targetConstraints.values())
        for t in targets:
            pm.parentConstraint(targetParents[t], t)
        pm.select(control, replace=True)

    def createTempPivot(self, sel):
        loc = self.createControl(sel[-1])
        frame = cmds.currentTime(query=True)
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()
        self.completedScriptJob(sel, loc, frame)

    def createTempPivotFromSelection(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')
        self.createTempPivot(sel)

#cls = temp()
#cls.createTempPivot(cmds.ls(sl=True))

