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

import pymel.core.datatypes as dt
import maya.OpenMaya as om

xAx = om.MVector.xAxis
yAx = om.MVector.yAxis
zAx = om.MVector.zAxis
rad_to_deg = 57.2958
axisMapping = {
    0: xAx,
    1: yAx,
    2: zAx
}

__author__ = 'tom.bailey'

assetCommandName = 'tempPivotControlCommand'
class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('tempPivot'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='create_temp_pivot',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotFromSelection()']))
        self.addCommand(self.tb_hkey(name='createTempPivotHierarchy',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotHierarchy()']))
        self.addCommand(self.tb_hkey(name='createTempParent', annotation='',
                                     category=self.category, command=['TempPivot.tempParent()']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for temp controls',
                                     category=self.category, command=['TempPivot.assetRmbCommand()']))
        return self.commandList

    def assignHotkeys(self):
        return


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
    tempParentScriptJobs = list()
    crossSizeOption = 'tbBakeLocatorSize'
    assetName = 'TempPivotControls'
    constraintTargetAttr = 'constraintTarget'
    assetCommandName = assetCommandName
    tempControlSizeOption = 'tbTempParentSizeOption'

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
        super(TempPivot, self).optionUI()

        crossSizeWidget = intFieldWidget(optionVar=self.tempControlSizeOption,
                                         defaultValue=1.0,
                                         label='Temp Parent Control size',
                                         minimum=0.1, maximum=100, step=0.1)
        crossSizeWidget.changedSignal.connect(partial(self.updatePreview, optionVar=self.tempControlSizeOption))
        self.layout.addWidget(crossSizeWidget)
        self.layout.addStretch()
        return self.optionWidget

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

        cmds.menuItem(label='Temp Pivot Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Bake selected temp pivots to layer',
                      command=pm.Callback(self.bakeSelectedCommand, asset, sel))
        cmds.menuItem(label='Bake all temp pivots to layer', command=pm.Callback(self.bakeAllCommand, asset, sel))
        # cmds.menuItem(label='Bake out to layer', command=pm.Callback(self.bakeOutCommand, asset))
        cmds.menuItem(label='Delete all temp pivots', command=pm.Callback(self.deleteControlsCommand, asset, sel))
        cmds.menuItem(divider=True)

    def bakeSelectedCommand(self, asset, sel):
        targets = [x for x in sel if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)

        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        pm.delete(targets)

    def bakeAllCommand(self, asset, sel):
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        '''
        self.allTools.tools['BakeTools'].quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                                                   deleteConstraints=True)
        '''
        pm.delete(asset)

    def deleteControlsCommand(self, asset, sel):
        pm.delete(asset)

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

        with self.funcs.undoChunk():
            cmds.currentTime(frame)
            mainTarget = targets[-1]
            constraints = list()
            control = self.funcs.tempControl(name=mainTarget, suffix='Pivot', drawType='orb',
                                             scale=pm.optionVar.get(self.crossSizeOption, 1))
            constraintState, inputs, constraints = self.funcs.isConstrained(mainTarget)

            controlParent = cmds.createNode('transform', name=mainTarget + '_Pivot_grp')
            pm.parent(control, controlParent)

            if constraintState and constraints:
                constrainTargets = self.funcs.getConstrainTargets(constraints[0])
                constraintWeightAliases = self.funcs.getConstrainWeights(constraints[0])
                pm.parentConstraint(constrainTargets[0], controlParent)  # TODO = make this support blended constraints?
            else:
                parentNode = cmds.listRelatives(mainTarget, parent=True)
                if parentNode:
                    pm.parentConstraint(parentNode, controlParent)

            pm.delete(pm.parentConstraint(loc, control))

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

            if constraints:
                pm.delete(constraints)

            pm.bakeResults(bakeTargets,
                           time=(keyRangeStart, keyRangeEnd),
                           simulation=False,
                           sampleBy=1)
            pm.delete(mainConstraint)
            pm.delete(targetConstraints.values())
            for t in targets:
                pm.parentConstraint(targetParents[t], t)
            pm.select(control, replace=True)

            pm.delete(loc)

    def createTempPivot(self, sel):
        mainControl = sel[-1]

        loc = self.createControl(mainControl)
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
        with self.funcs.undoChunk():
            self.createTempPivot(sel)

    def tempParent(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        pivotControl = sel[-1]
        cmds.undoInfo(openChunk=True, chunkName='tempParent', stateWithoutFlush=False)
        tempControl = self.funcs.tempLocator(name=pivotControl, suffix='tempParentRoot',
                                             scale=pm.optionVar.get(self.tempControlSizeOption, 1))
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)
        pm.delete(pm.parentConstraint(pivotControl, tempControl))

        pm.select(tempControl, replace=True)
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()
        self.tempParentPlacedScriptJob(sel, tempControl)

    def tempParentPlacedScriptJob(self, sel, tempControl):
        self.cleartempParentScriptJobs()
        self.tempParentScriptJobs.append(
            pm.scriptJob(runOnce=True,
                         compressUndo=True,
                         event=['SelectionChanged', partial(self.poseTempControl, sel, tempControl)]))
        self.tempParentScriptJobs.append(
            pm.scriptJob(runOnce=True,
                         compressUndo=True,
                         event=['ToolChanged', partial(self.poseTempControl, sel, tempControl)]))

    def poseTempControl(self, sel, tempControl):
        constraints = list()
        tempParentControl = self.funcs.tempControl(name=sel[-1], suffix='tempParent',
                                                   scale=pm.optionVar.get(self.tempControlSizeOption, 1))
        pm.delete(pm.parentConstraint(tempControl, tempParentControl))
        cmds.undoInfo(openChunk=True, chunkName='aimAtTempControl', stateWithoutFlush=False)
        pm.delete(tempControl)
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)

        for s in sel:
            constraints.append(pm.parentConstraint(tempParentControl, s,
                                                   skipTranslate=self.funcs.getAvailableTranslates(s),
                                                   skipRotate=self.funcs.getAvailableRotates(s),
                                                   maintainOffset=True))
        pm.select(tempParentControl, replace=True)

        self.tempParentScriptJob(sel, tempParentControl)

    def tempParentScriptJob(self, sel, tempControl):
        self.cleartempParentScriptJobs()
        self.tempParentScriptJobs.append(
            pm.scriptJob(runOnce=True,
                         compressUndo=True,
                         event=['SelectionChanged', partial(self.bakeTempControl, sel, tempControl)]))

    def bakeTempControl(self, controls, tempControl):
        if not pm.objExists(tempControl):
            return
        pm.setKeyframe(controls)
        pm.delete(tempControl)
        self.cleartempParentScriptJobs()

    def cleartempParentScriptJobs(self):
        allJobs = cmds.scriptJob(listJobs=True)
        allJobID = [int(i.split(':')[0]) for i in allJobs]
        for j in self.tempParentScriptJobs:
            if j in allJobID:
                try:
                    pm.scriptJob(kill=j)
                except:
                    pass

    def createTempPivotHierarchy(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')
        with self.funcs.undoChunk():
            self.createTempPivotForHierarchy(sel)

    def createTempPivotForHierarchy(self, sel):
        mainControl = sel[-1]

        loc = self.createControl(mainControl)
        frame = cmds.currentTime(query=True)
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()
        self.completedHierarchyScriptJob(sel, loc, frame)

    def completedHierarchyScriptJob(self, targets, loc, frame):
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True,
                         event=['SelectionChanged', partial(self.bakeTempHierarchy, targets, loc, frame)]))
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True, event=['ToolChanged', partial(self.bakeTempHierarchy, targets, loc, frame)]))
        # self.scriptJobs.append(pm.scriptJob(runOnce=True, timeChange=partial(self.bake, targets, loc, frame)))

    def bakeTempHierarchy(self, targets, loc, frame):
        self.clearScriptJobs()

        with self.funcs.undoChunk():
            cmds.currentTime(frame)
            mainTarget = targets[-1]
            constraints = list()
            tempControls = list()
            tempControlsGrps = list()
            targetParents = dict()
            targetConstraints = dict()
            bakeTargets = dict()
            ps = pm.PyNode(targets[-1])
            ns = ps.namespace()
            if not cmds.objExists(ns + self.assetName):
                self.createAsset(ns + self.assetName, imageName=None)
            asset = ns + self.assetName

            targetDict = dict()
            mainControl = self.funcs.tempControl(name=mainTarget, suffix='PivotControl', drawType='orb',
                                                 scale=pm.optionVar.get(self.crossSizeOption, 0.25))
            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=mainControl)
            pm.delete(pm.parentConstraint(loc, mainControl))
            pm.delete(loc)

            for s in targets:
                control = self.funcs.tempControl(name=s, suffix='_pivot', scale=0.25)
                tempControls.append(control)
                constraint = pm.parentConstraint(s, control)
                constraints.append(constraint)
                pm.addAttr(control, ln=self.constraintTargetAttr, at='message')
                pm.connectAttr(s + '.message', control + '.' + self.constraintTargetAttr)

                pm.container(asset, edit=True,
                             includeHierarchyBelow=True,
                             force=True,
                             addNode=[control])

            for index in range(len(tempControls)-1):
                pm.parent(tempControls[index], tempControls[index + 1])

            constraints.append(pm.parentConstraint(targets[-1], mainControl, maintainOffset=True))
            pm.parent(tempControls[-1], mainControl)
            tempControls.append(mainControl)

            for index, c in enumerate(tempControls):
                cmds.select(clear=True)
                pivotNull = cmds.group(empty=True, world=True, name="%s_pivotNull" % c)
                tempControlsGrps.append(pivotNull)
                targetParents[index] = pivotNull
                pm.delete(pm.parentConstraint(tempControls[index], pivotNull))
            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=tempControlsGrps)
            controlsReversed = list(reversed(tempControls))
            for index, c in enumerate(tempControlsGrps[1:]):
                pm.parent(tempControlsGrps[index], tempControlsGrps[index + 1])

            for index in range(len(tempControlsGrps) - 1, -1, -1):
                pm.pointConstraint(tempControls[index], tempControlsGrps[index])
                if index > 0:
                    constraint = self.constrainAimToTarget(constrainedControl = str(tempControlsGrps[index]),
                                                           aimTarget = str(tempControls[index-1]),
                                                           upObject = str(tempControls[index]))
                    '''
                    aimConstraint = pm.aimConstraint(tempControls[index-1], tempControlsGrps[index],
                                                     worldUpObject=tempControls[index],
                                                     aimVector=[1,0,0],
                                                     upVector=[0,1,0],
                                                     worldUpVector=[0,1,0],
                                                     worldUpType='objectrotation')
                    '''

            keyRangeStart = cmds.playbackOptions(query=True, min=True)
            keyRangeEnd = cmds.playbackOptions(query=True, max=True)

            pm.bakeResults(tempControls,
                           time=(keyRangeStart, keyRangeEnd),
                           simulation=False,
                           sampleBy=1)
            self.funcs.resumeSkinning()

            pm.delete(constraints)

            for index, t in enumerate(targets):
                self.funcs.safeParentConstraint(tempControlsGrps[index+1], t, orientOnly=False, maintainOffset=True)

            pm.select(mainControl, replace=True)


    def constrainAimToTarget(self, constrainedControl=str(), aimTarget=str(), upObject=str()):
        locatorPos = dt.Vector(pm.xform(aimTarget, query=True, worldSpace=True,
                                        # translation=True,
                                        rotatePivot=True))
        controlPos = dt.Vector(pm.xform(constrainedControl, query=True, worldSpace=True,
                                        # translation=True,
                                        rotatePivot=True))
        aimVec = (locatorPos - controlPos).normal()

        xDot = aimVec * om.MVector.xAxis
        yDot = aimVec * om.MVector.yAxis
        zDot = aimVec * om.MVector.zAxis

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [dt.Vector(1, 0, 0), dt.Vector(0, 1, 0), dt.Vector(0, 0, 1)]
        upXxisIndex = axisList.index(min(axisList))

        aimVector = self.funcs.getVectorToTarget(aimTarget, constrainedControl)
        upVector = localAxisVecList[upXxisIndex]
        worldUpVector = self.funcs.getWorldSpaceVectorOffset(constrainedControl, upObject, vec=axisMapping[upXxisIndex])
        aimConstraint = pm.aimConstraint(aimTarget, constrainedControl,
                                         aimVector=aimVector,
                                         worldUpObject=aimTarget,
                                         worldUpVector=worldUpVector,
                                         upVector=upVector,
                                         worldUpType='objectRotation',
                                         maintainOffset=False)
        return aimConstraint
# cls = temp()
# cls.createTempPivot(cmds.ls(sl=True))
