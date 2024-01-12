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

maya.utils.loadStringResourcesForModule(__name__)
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
assetPointCommandName = 'tempPivotControlPointCommand'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('tempPivot'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='create_temp_pivot',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotFromSelection()']))
        self.addCommand(self.tb_hkey(name='createTempPivotInteractive',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotFromSelection()']))

        self.addCommand(self.tb_hkey(name='createTempPivotAtSelection',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotAtSelection()']))

        self.addCommand(self.tb_hkey(name='createPersistentTempPivotInteractive',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createPersistentTempPivotInteractive()']))

        self.addCommand(self.tb_hkey(name='createPersistentTempPivotNodeAtSelection',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotNode()']))
        # createPersistentTempPivotFromAtSelection
        self.addCommand(self.tb_hkey(name='restorePersistentPivots',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.loadPivotsForControl()']))
        self.addCommand(self.tb_hkey(name='bakePersistentPivotFromSel',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.bakeTempPivotFromSel()']))

        self.addCommand(self.tb_hkey(name='createTempPivotHierarchy',
                                     annotation='',
                                     category=self.category,
                                     command=['TempPivot.createTempPivotHierarchy()']))

        self.addCommand(self.tb_hkey(name='createTempParentInteractive', annotation='',
                                     category=self.category, command=['TempPivot.tempParent()']))
        self.addCommand(self.tb_hkey(name='createTempParentLastSelected', annotation='',
                                     category=self.category, command=['TempPivot.tempParentLastSelected()']))

        self.setCategory(self.helpStrings.category.get('ignore'))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='NOT FOR HOTKEYS',
                                     category=self.category, command=['TempPivot.assetRmbCommand()']))
        self.addCommand(self.tb_hkey(name=assetPointCommandName,
                                     annotation='NOT FOR HOTKEYS',
                                     category=self.category, command=['TempPivot.assetRmbPointCommand()']))
        return self.commandList

    def assignHotkeys(self):
        return


class PivotOffsetData(object):
    def __init__(self, jsonInfo):
        self.offsetTranslate = [0, 0, 0]
        self.offsetRotate = [0, 0, 0]
        self.fromJson(jsonInfo)

    def fromJson(self, jsonInfo):
        for k, v in jsonInfo.items():
            self.__dict__[k] = v

    def json_serialize(self):
        returnDict = {}

        returnDict['offsetTranslate'] = self.offsetTranslate
        returnDict['offsetRotate'] = self.offsetRotate
        return returnDict

    def toJson(self):
        jsonData = '''{}'''
        classData = json.loads(jsonData)
        for k, v in self.__dict__.items():
            if k.startswith('__'):
                continue
            classData[k] = v
        return classData

    def getOffset(self, control):
        parentConstraint = cmds.listRelatives(control, type='parentConstraint')
        if not parentConstraint:
            return cmds.warning('No valid constraint found for pivot')
        self.offsetTranslate = cmds.getAttr(parentConstraint[0] + '.target[0].targetOffsetTranslate')[0]
        self.offsetRotate = cmds.getAttr(parentConstraint[0] + '.target[0].targetOffsetRotate')[0]
        pass

        # controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
        # jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
        # resultMatrix = controlMMatrix * jointMMatrix.inverse()
        # self.fkControlOffsets[c] = [x for x in resultMatrix]


class PivotData(object):
    def __init__(self):
        self.persistentPivots = dict()  # key is control, value is translation / rotate offsets

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}

        returnDict['persistentPivots'] = self.persistentPivots
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))
        self.persistentPivots = dict()
        # TODO - fix this to use actual pivot info
        persistentPivots = rawJsonData.get('persistentPivots', list())
        for key, items in persistentPivots.items():
            self.persistentPivots[key] = dict()
            for itemKey, offset in items.items():
                self.persistentPivots[key][itemKey] = PivotOffsetData(offset)

    def addPersistentPivotInfo(self, animControl, pivotControl):
        print ('addPersistentPivotInfo', animControl, pivotControl)
        if not cmds.attributeQuery(TempPivot.pivotControlAttr, node=str(pivotControl), exists=True):
            return
        controls = cmds.listConnections(str(pivotControl) + '.' + TempPivot.pivotControlAttr)
        if not controls:
            return
        data = PivotOffsetData({})
        data.getOffset(pivotControl)
        key = pivotControl.rsplit(':', 1)[-1]
        shortName = animControl.rsplit(':', 1)[-1]
        print ('key', key)
        print ('shortName', shortName)
        if shortName not in self.persistentPivots.keys():
            self.persistentPivots[shortName] = dict()
        print ('heyeeeee')
        print (self.persistentPivots[shortName] )
        self.persistentPivots[shortName][key] = data
        print()


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
    assetTempName = 'TempPivotPoints'
    constraintTargetAttr = 'constraintTarget'
    pivotControlAttr = 'pivotControl'
    assetCommandName = assetCommandName
    tempControlSizeOption = 'tbTempParentSizeOption'

    loadedPivotData = dict()
    namespaceToCharDict = dict()

    def __new__(cls):
        if TempPivot.__instance is None:
            TempPivot.__instance = object.__new__(cls)

        TempPivot.__instance.val = cls.toolName
        return TempPivot.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.initData()

    def initData(self):
        super(TempPivot, self).initData()
        self.pivotDataDir = os.path.normpath(os.path.join(self.dataPath, self.toolName))
        if not os.path.isdir(self.pivotDataDir):
            os.mkdir(self.pivotDataDir)

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

    def loadRigData(self, dataCLS, rigName):
        subPath = os.path.join(self.dataPath, self.toolName)
        dataCLS.fromJson(os.path.join(subPath, rigName + '.json'))
        return dataCLS

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        for key, value in characters.items():
            '''
            if not key:
                continue  # skip non referenced chars
            '''
            refname, namespace = self.funcs.getCurrentRig([value[0]])
            if namespace.startswith(':'):
                namespace = namespace.split(':', 1)[-1]
            namespaceToCharDict[namespace] = refname

            if refname not in self.loadedPivotData.keys():
                print(
                    'refname', refname
                )
                self.saveRigFileIfNew(refname, PivotData().toJson())
            pivotData = self.loadPivotData(refname)

            self.loadedPivotData[refname] = pivotData
        self.namespaceToCharDict = namespaceToCharDict

    def loadPivotData(self, refname):
        return self.loadRigData(PivotData(), refname)

    def saveRigData(self, refname, jsonData):
        """
        Pass in a json object
        :param dataCLS:
        :param rigName:
        :return:
        """
        dataFile = os.path.join(self.subFolder, refname + '.json')
        self.saveJsonFile(dataFile, json.loads(jsonData))

    def saveRigFileIfNew(self, refname, jsonData):
        self.subFolder = os.path.join(self.dataPath, self.toolName)
        if not os.path.isdir(self.subFolder):
            os.mkdir(self.subFolder)
        dataFile = os.path.join(self.subFolder, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            self.saveJsonFile(dataFile, json.loads(jsonData))

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

    def assetRmbPointCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = pm.ls(sl=True)
        asset = pm.container(query=True, findContainer=sel[0])

        cmds.menuItem(label='Temp Pivot Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label=maya.stringTable['TempPivot.updatePivot'],
                      command=pm.Callback(self.updateTempPivotPositions, asset, sel))
        cmds.menuItem(label=maya.stringTable['TempPivot.bakePointToControl'],
                      command=pm.Callback(self.createTempPivotControlFromPoint, asset, sel))
        cmds.menuItem(label=maya.stringTable['TempPivot.saveTempPivots'],
                      command=pm.Callback(self.savePivotsForControl, asset, sel))

    def updateTempPivotPositions(self, asset, sel):
        if not sel:
            return
        for s in sel:
            constraints = cmds.listRelatives(str(s), type='parentConstraint')
            if not constraints:
                continue
            targetList = cmds.parentConstraint(constraints[0], query=True, targetList=True)
            cmds.parentConstraint(targetList, constraints[0], edit=True, maintainOffset=True)

    def savePivotsForControl(self, asset, sel):
        if not sel:
            return
        sel = [str(s) for s in sel]
        """
        Only look at the connections to the temp pivot
        """
        baseControls = dict()
        for s in sel:
            if not cmds.attributeQuery(self.pivotControlAttr, node=str(s), exists=True):
                continue
            controls = cmds.listConnections(str(s) + '.' + self.pivotControlAttr)
            print ('linked controls', controls)
            if not controls:
                continue
            if controls[0] not in baseControls.keys():
                baseControls[controls[0]] = list()
            baseControls[controls[0]].append(s)
        if not baseControls:
            return cmds.warning('No controls found')
        characters = self.funcs.splitSelectionToCharacters(list(baseControls.keys()))
        print('characters', characters)
        print('baseControls', baseControls)
        self.loadDataForCharacters(characters)
        print('savePivotsForControl', sel)

        # actual saving here
        # loop over the dict and store the offsets
        for key, values in baseControls.items():
            print('key', key)
            print('values', values)
            refname, namespace = self.funcs.getCurrentRig([key])
            print('refname', refname)
            for v in values:
                self.loadedPivotData[refname].addPersistentPivotInfo(key, v)

            print(self.loadedPivotData[refname].toJson())
            self.saveRigData(refname, self.loadedPivotData[refname].toJson())


    def loadPivotsForControl(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')

        characters = self.funcs.splitSelectionToCharacters(sel)
        print('characters', characters)
        print('')
        self.loadDataForCharacters(characters)
        newNodes = list()
        for s in sel:
            refname, namespace = self.funcs.getCurrentRig(s)
            pivotData = self.loadedPivotData[refname]
            print(s, refname)
            shortName = s.rsplit(':', 1)[-1]
            print('shortName', shortName)
            print(pivotData.persistentPivots)
            if shortName not in pivotData.persistentPivots.keys():
                continue
            for p in pivotData.persistentPivots[shortName]:
                tempNode = self.createTempPivotNode(control=s, tempPivotNodeName=namespace + ':' + p)
                print (tempNode)

                parentConstraint = cmds.listRelatives(str(tempNode), type='parentConstraint')
                print ('parentConstraint', parentConstraint)
                if not parentConstraint:
                    return cmds.warning('No valid constraint found for pivot')
                offset = pivotData.persistentPivots[shortName][p]

                cmds.setAttr(parentConstraint[0] + '.target[0].targetOffsetTranslate', *offset.offsetTranslate,
                             type='double3')
                cmds.setAttr(parentConstraint[0] + '.target[0].targetOffsetRotate',
                             *offset.offsetRotate,
                             type='double3')
                newNodes.append(tempNode)
        return newNodes

    def bakeTempPivotFromSel(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')

        self.createTempPivotControlFromPoint(None, sel)

    def createTempPivotControlFromPoint(self, asset, sel):
        if not sel:
            return
        newNodes = list()
        pivots = list()
        for s in sel:
            currentControl = str(s)
            frame = cmds.currentTime(query=True)
            if not cmds.attributeQuery(self.pivotControlAttr, node=currentControl, exists=True):
                pivots = self.loadPivotsForControl(sel=[currentControl])
                if not pivots:
                    continue
                currentControl = pivots[-1]
            control = cmds.listConnections(currentControl + '.' + self.pivotControlAttr)
            if not control:
                return cmds.warning('Control connection not found')
            self.completedScriptJob(control[0], currentControl, frame)
            self.bake(control, currentControl, frame, deletePoint=False)


    def bakeSelectedCommand(self, asset, sel):
        print('sel', sel)
        targets = [x for x in sel if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = self.funcs.flattenList(
            [pm.listConnections(x + '.' + self.constraintTargetAttr) for x in targets])
        #
        # print ('targets', targets)
        # print ('filteredTargets', filteredTargets)
        #

        keyRange = self.funcs.getBestTimelineRangeForBake(sel)
        print('bakeAllCommand', 'keyRange', keyRange)
        self.allTools.tools['BakeTools'].bake_to_override(sel=filteredTargets)
        pm.delete(targets)
        pm.select(filteredTargets, replace=True)

    def bakeAllCommand(self, asset, sel):
        """

        :param asset:
        :param sel:
        :return:
        """
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]

        self.allTools.tools['BakeTools'].bake_to_override(sel=filteredTargets)
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

    def bake(self, targets, loc, frame, deletePoint=True):
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
                if cmds.listConnections(mainTarget + '.offsetParentMatrix'):
                    print('offsetParentMatrix')
                    pass
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
                self.createAsset(ns + self.assetName, imageName=None, assetCommandName=assetCommandName)
            asset = ns + self.assetName

            # connect all the constrained controls to the new temp control
            self.funcs.connect_message_attrs_to_multi_attr(targets, str(control), self.constraintTargetAttr)

            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=[control, controlParent])

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
            keyRange = self.funcs.getBestTimelineRangeForBake()
            pm.bakeResults(bakeTargets,
                           time=(keyRange[0], keyRange[1]),
                           simulation=False,
                           sampleBy=1)
            pm.delete(mainConstraint)
            pm.delete(targetConstraints.values())
            for t in targets:
                pm.parentConstraint(targetParents[t], t)
            pm.select(control, replace=True)

            if deletePoint: pm.delete(loc)

    def createTempPivot(self, sel):
        mainControl = sel[-1]

        loc = self.createControl(mainControl)
        frame = cmds.currentTime(query=True)
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()
        self.completedScriptJob(sel, loc, frame)

    def createPersistentTempPivotInteractive(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')
        with self.funcs.undoChunk():
            self.createPersistentTempPivot(sel)

    def createPersistentTempPivotFromAtSelection(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')

    def createPersistentTempPivot(self, sel):
        """
        Create a temp control, moved to where you want it
        After deselecting it, bake the main control to this
        Leave a small node behind that can be repositioned and rebaked to quickly
        :param sel:
        :return:
        """
        mainControl = sel[-1]
        keyRange = self.funcs.getBestTimelineRangeForBake()

        loc = self.createControl(mainControl)
        frame = cmds.currentTime(query=True)
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()
        self.createPersistentTempPivotScriptJob(sel, loc, frame, keyRange)

    def createPersistentTempPivotScriptJob(self, targets, loc, frame, keyRange):
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True, event=['SelectionChanged',
                                              partial(self.bakePersistentTempPivot, targets, loc, frame, keyRange)]))
        self.scriptJobs.append(
            pm.scriptJob(runOnce=True,
                         event=['ToolChanged', partial(self.bakePersistentTempPivot, targets, loc, frame, keyRange)]))
        # self.scriptJobs.append(pm.scriptJob(runOnce=True, timeChange=partial(self.bake, targets, loc, frame)))

    def quickBakeTempPivotSelected(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('no valid selection')
        # is the selection a temp node or a control?

        pivotNodes = list()
        animationControls = list()
        for s in sel:
            control = None
            messageConnections = cmds.listConnections(s + '.message')

            # is this a pivot node?
            if cmds.attributeQuery(TempPivot.pivotControlAttr, node=s, exists=True):
                connectedNodes = cmds.listConnections(s + '.' + self.pivotControlAttr)

                if not connectedNodes:
                    return cmds.error('No connected controls')
                for n in connectedNodes:
                    if n not in animationControls:
                        control = s
                    animationControls.append(n)

            elif messageConnections:
                for m in messageConnections:
                    if control:
                        continue
                    if cmds.attributeQuery(TempPivot.pivotControlAttr, node=m, exists=True):
                        control = m
                        animationControls.append(s)

            if control:
                pivotNodes.append(control)
        print('pivot nodes', pivotNodes)
        if not pivotNodes:
            return
        keyRange = self.funcs.getBestTimelineRangeForBake()
        frame = cmds.currentTime(query=True)
        # TODO - fix this so one bake
        self.createTempPivotControlFromPoint(None, pivotNodes)

    def createTempPivotNode(self, control=None, transformControl=None, tempPivotNodeName=None):
        """
        Create the temp pivot node at the location of the transformControl
        :param control:
        :return:
        """
        if control is None:
            sel = cmds.ls(sl=True, type='transform')
            if not sel:
                return cmds.error('No selection or control specified')
            control = sel[0]
            if transformControl is None:
                if not sel:
                    return cmds.error('No selection or control specified')
                transformControl = sel[-1]
        else:
            transformControl = control

        if tempPivotNodeName is None:
            if control is not transformControl:
                tempPivotNodeName = control + '__' + transformControl.split(':')[-1]
            else:
                tempPivotNodeName = control

        print('transformControl', transformControl)

        tempNull = self.funcs.tempNull(name=tempPivotNodeName, suffix='')
        tempNull.displayHandle.set(True)

        self.funcs.getSetColour(control, tempNull, brightnessOffset=0.05)
        # self.funcs.boldControl(tempNull, mainTarget, offset=1.0)

        pm.delete(pm.parentConstraint(transformControl, tempNull))
        pm.parentConstraint(control, tempNull, maintainOffset=True)

        ps = pm.PyNode(control)
        ns = ps.namespace()

        # make the temp node assets
        if not cmds.objExists(ns + self.assetTempName):
            self.createAsset(ns + self.assetTempName, imageName=None, assetCommandName=assetPointCommandName)
        tempAsset = ns + self.assetTempName

        # tag the temp node back to the control
        pm.addAttr(tempNull, ln=self.pivotControlAttr, at='message')
        pm.connectAttr(control + '.message', tempNull + '.' + self.pivotControlAttr)

        pm.container(tempAsset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=[tempNull])
        return tempNull

    def bakePersistentTempPivot(self, targets, loc, frame, keyRange):
        self.clearScriptJobs()

        with self.funcs.undoChunk():
            cmds.currentTime(frame)
            mainTarget = targets[-1]
            constraints = list()
            tempNull = self.funcs.tempNull(name=mainTarget, suffix='piv')
            tempNull.displayHandle.set(True)

            self.funcs.getSetColour(mainTarget, tempNull, brightnessOffset=0.05)
            # self.funcs.boldControl(tempNull, mainTarget, offset=1.0)

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
            pm.delete(pm.parentConstraint(loc, tempNull))
            pm.parentConstraint(targets[-1], tempNull, maintainOffset=True)

            mainConstraint = pm.parentConstraint(targets[-1], control, maintainOffset=True)
            keyRangeStart = cmds.playbackOptions(query=True, min=True)
            keyRangeEnd = cmds.playbackOptions(query=True, max=True)

            ps = pm.PyNode(targets[-1])
            ns = ps.namespace()
            if not cmds.objExists(ns + self.assetName):
                self.createAsset(ns + self.assetName, imageName=None)
            asset = ns + self.assetName

            # connect all the constrained controls to the new temp control
            self.funcs.connect_message_attrs_to_multi_attr(targets, str(control), self.constraintTargetAttr)

            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=[control, controlParent])

            # make the temp node assets
            if not cmds.objExists(ns + self.assetTempName):
                self.createAsset(ns + self.assetTempName, imageName=None, assetCommandName=assetPointCommandName)
            tempAsset = ns + self.assetTempName

            # tag the temp node back to the control
            pm.addAttr(tempNull, ln=self.pivotControlAttr, at='message')
            pm.connectAttr(mainTarget + '.message', tempNull + '.' + self.pivotControlAttr)

            pm.container(tempAsset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=[tempNull])

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
            # keyRange = self.funcs.getBestTimelineRangeForBake()
            pm.bakeResults(bakeTargets,
                           time=(keyRange[0], keyRange[1]),
                           simulation=False,
                           sampleBy=1)
            pm.delete(mainConstraint)
            pm.delete(targetConstraints.values())
            for t in targets:
                pm.parentConstraint(targetParents[t], t)
            pm.select(control, replace=True)

            pm.delete(loc)

    def createTempPivotAtSelection(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('please select at least 2 controls')
        if not len(sel) > 1:
            return cmds.warning('please select at least 2 controls')

        loc = self.createControl(sel[-1])
        frame = cmds.currentTime(query=True)

        self.bake(sel, loc, frame)

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

    def tempParentLastSelected(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        if not len(sel) > 1:
            return cmds.warning('Please select at least 2 controls')

        pivotControl = sel[-1]
        controls = sel[:-1]

        self.poseTempControl(controls, pivotControl)

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
                self.createAsset(ns + self.assetName, imageName='addWrapInfluence.png')
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

            for index in range(len(tempControls) - 1):
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
                    constraint = self.constrainAimToTarget(constrainedControl=str(tempControlsGrps[index]),
                                                           aimTarget=str(tempControls[index - 1]),
                                                           upObject=str(tempControls[index]))
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
            keyRange = self.funcs.getBestTimelineRangeForBake()
            pm.bakeResults(tempControls,
                           time=(keyRange[0], keyRange[1]),
                           simulation=False,
                           sampleBy=1)
            self.funcs.resumeSkinning()

            pm.delete(constraints)

            for index, t in enumerate(targets):
                self.funcs.safeParentConstraint(tempControlsGrps[index + 1], t, orientOnly=False, maintainOffset=True)

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
