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
                                     command=['TempPivot.createTempPivotFromSelection()']))
        self.addCommand(self.tb_hkey(name='createTempParent', annotation='',
                                     category=self.category, command=['TempPivot.tempParent()']))
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
        crossSizeWidget.changedSignal.connect(self.updatePreview)
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

    def updatePreview(self, scale):
        if not cmds.objExists('temp_Preview'):
            self.drawPreview()

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)

    def drawPreview(self):
        self.funcs.tempControl(name='temp',
                               suffix='Preview',
                               scale=pm.optionVar.get(self.tempControlSizeOption, 1),
                               drawType='orb')

    def bakeSelectedCommand(self, asset, sel):
        targets = [x for x in sel if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)
        self.allTools.tools['BakeTools'].quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                                                   deleteConstraints=True)
        pm.delete(filteredTargets)

    def bakeAllCommand(self, asset, sel):
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)
        self.allTools.tools['BakeTools'].quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1], deleteConstraints=True)
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

            print ('!!', constraintState, inputs, constraints)
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

        tempControl = self.funcs.tempControl(name=pivotControl, suffix='tempParent',
                                             scale=pm.optionVar.get(self.tempControlSizeOption, 1))
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
            pm.scriptJob(runOnce=True, event=['SelectionChanged', partial(self.poseTempControl, sel, tempControl)]))
        self.tempParentScriptJobs.append(
            pm.scriptJob(runOnce=True, event=['ToolChanged', partial(self.poseTempControl, sel, tempControl)]))

    def poseTempControl(self, sel, tempControl):
        constraints = list()
        for s in sel:
            print ('poseTempControl', s)
            constraints.append(pm.parentConstraint(tempControl, s,
                                                   skipTranslate=self.funcs.getAvailableTranslates(s),
                                                   skipRotate=self.funcs.getAvailableRotates(s),
                                                   maintainOffset=True))
        pm.select(tempControl, replace=True)

        self.tempParentScriptJob(sel, tempControl)

    def tempParentScriptJob(self, sel, tempControl):
        self.cleartempParentScriptJobs()
        self.tempParentScriptJobs.append(
            pm.scriptJob(runOnce=True, event=['SelectionChanged', partial(self.bakeTempControl, sel, tempControl)]))

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


#cls = temp()
#cls.createTempPivot(cmds.ls(sl=True))

