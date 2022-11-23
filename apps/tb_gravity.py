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
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import pymel.core.datatypes as dt
import math
import bisect
from Abstract import *
from tb_UI import *
import maya

mainNodeName = 'CoM_Nodes'
capsuleNodeName = 'Capsules'
comNodeName = 'CoM'
floorComNodeName = 'CoM_Floor'

capsuleSideA = 'tbCapsuleSideA'
capsuleSideB = 'tbCapsuleSideB'

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
import maya.api.OpenMaya as OpenMaya

import maya.OpenMaya as om

import math
import sys
import pymel.core as pm
import pymel.core.datatypes as dt
import maya.cmds as cmds


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('gravity'))
        self.addCommand(self.tb_hkey(name='quickJump',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.doQuickJump()'],
                                     help=maya.stringTable['tbCommand.doQuickJump']))
        self.addCommand(self.tb_hkey(name='jumpAllKeypairs',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.jumpAllKeypairs()'],
                                     help=maya.stringTable['tbCommand.doJumpAllKeypairs']))
        self.addCommand(self.tb_hkey(name='jumpUsingInitialFrameVelocity',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.jumpUsingInitialFrameVelocity()'],
                                     help=maya.stringTable['tbCommand.doJumpUsingInitialFrameVelocity']))
        self.addCommand(self.tb_hkey(name='quickDrop',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.quickDrop()'],
                                     help=''))
        self.addCommand(self.tb_hkey(name='GravtiyToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.openMM()']))
        self.addCommand(self.tb_hkey(name='GravtiyToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.closeMM()']))
        self.addCommand(self.tb_hkey(name='GravityToolsOpenUI',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.toolBoxUI()'],
                                     help=''))

        return self.commandList

    def assignHotkeys(self):
        return


class GravityTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'GravityTools'
    comTemplateSubFolder = 'comTemplates'
    hotkeyClass = hotkeys()
    funcs = functions()

    gravityOption = 'tbGravityOption'
    defaultGravity = -981
    toolbox = None

    copyData = {'scaleX': 0,
                'scaleY': 0,
                }
    copyConstraintOffset = {'TranslateX': 0,
                            'TranslateY': 0,
                            'TranslateZ': 0,
                            'RotateX': 0,
                            'RotateY': 0,
                            'RotateZ': 0,
                            }
    sides = [pm.optionVar.get(capsuleSideA, '_L'),
             pm.optionVar.get(capsuleSideB, '_R')]
    editMode = pm.optionVar.get('tbComEditMode', True)

    lastSelectedRig = None

    def __new__(cls):
        if GravityTools.__instance is None:
            GravityTools.__instance = object.__new__(cls)

        GravityTools.__instance.val = cls.toolName
        GravityTools.__instance.loadData()

        return GravityTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.gravity = pm.optionVar.get(self.gravityOption, self.defaultGravity)
        self.uiUnit = om.MTime.uiUnit()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def initData(self):
        super(GravityTools, self).initData()
        self.comTemplateDir = os.path.normpath(os.path.join(self.dataPath, self.comTemplateSubFolder))
        if not os.path.isdir(self.comTemplateDir):
            os.mkdir(self.comTemplateDir)

    def optionUI(self):
        super(GravityTools, self).optionUI()
        infoText = QLabel()
        infoText.setText(
            'Set the gravity value in cm here. Default is -981. Some rigs are built to odd units/dimensions so adjust accordingly')
        infoText.setWordWrap(True)
        gravityScale = intFieldWidget(optionVar=self.gravityOption,
                                      defaultValue=pm.optionVar.get(self.gravityOption, self.defaultGravity),
                                      label='Gravity Override (cm)', minimum=-9999, maximum=9999, step=0.1)
        self.layout.addWidget(infoText)
        self.layout.addWidget(gravityScale)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='Centre of Mass', image='CoM.png', command='GravityToolsOpenUI', sourceType='mel',
                    parent=parentMenu)

    def build_MM(self):
        return

    """
    Functions
    """
    '''
    a = gravity
    frame by frame calculation
    startVec + initialVec*time + (time * time * 0.5) * gravity
    
    calculation for takeoff velocity based on jump duration and height difference
    -(x / t + (0.5 * a * t))
    
    calculation for max height
    - (v0 * v0) / 2 * a)
    '''

    def getGravity(self):
        worldAxis = cmds.upAxis(query=True, axis=True)
        self.gravity = pm.optionVar.get(self.gravityOption, self.defaultGravity) / self.funcs.unit_conversion()
        gravityVector = {'y': [0, self.gravity, 0],
                         'z': [0, 0, self.gravity]}
        return gravityVector[worldAxis]

    def quickDrop(self):
        self.uiUnit = om.MTime.uiUnit()

        if self.funcs.isTimelineHighlighted():
            timeRange = self.funcs.getTimelineHighlightedRange()
        else:
            timeRange = cmds.currentTime(query=True), cmds.playbackOptions(query=True, maxTime=True)

        sel = cmds.ls(sl=True)
        if not sel:
            tempControl = self.funcs.tempControl(name='Gravity', suffix='', drawType='cross')
        else:
            tempControl = self.funcs.tempControl(name=sel[0], suffix='Gravity', drawType='cross')
            pm.delete(pm.pointConstraint(sel[0], tempControl))

        pm.select(tempControl, replace=True)
        self.doJumpUsingInitialFrameVelocity()

    def doQuickJump(self):
        with self.funcs.keepSelection():
            self.quickJump()

    def quickJump(self):
        self.uiUnit = om.MTime.uiUnit()
        sel = cmds.ls(sl=True)
        if not sel:
            return
        timeRange = None
        if self.funcs.isTimelineHighlighted():
            timeRange = self.funcs.getTimelineHighlightedRange()

        currentTime = cmds.currentTime(query=True)
        mobjDict = dict()
        locs = dict()
        keyTimesDict = dict()
        for s in sel:
            if timeRange is None:
                keyTimesDict[s] = self.funcs.get_object_key_times(s)
                idx = bisect.bisect_left(keyTimesDict[s], currentTime)
                if idx - 1 < 0:
                    start = currentTime
                else:
                    start = keyTimesDict[s][idx - 1]
                if idx >= len(keyTimesDict[s]):
                    end = currentTime
                else:
                    end = keyTimesDict[s][idx]
            else:
                start = timeRange[0]
                end = timeRange[1]
            duration = end - start

            locs[s] = self.funcs.tempLocator(name=s, suffix='gravity', scale=1.0, color=(1.0, 0.537, 0.016))
            mobjDict[s] = self.getMobject(s)
            startMx, endMtx = self.getJumpDisplacement(mobjDict[s], start, end)
            startTranslation = self.getMatrixTranslation(startMx)
            endTranslation = self.getMatrixTranslation(endMtx)
            arcX, arcY, arcZ = self.getJumpArc(startTranslation, endTranslation, duration)
            self.keyJumpArc(arcX, arcY, arcZ, start, end, locs[s])

            self.bakeJumpToControl(start, end, locs[s], s)

    def bakeJumpToControl(self, start, end, locs, sel):
        constraints = list()
        if not isinstance(sel, list):
            sel = [sel]

        plugs = dict()
        curves = dict()
        curveDuplicates = dict()

        for s in sel:
            selectedLayer = self.funcs.get_preferred_layers(s, ignoreBase=True)

            if len(selectedLayer):
                """
                Baking to a layer will remove the outside keys, as preserveOutsideKeys does not work with layers
                Need a function to snapshot the existing animation and merge it after baking
                """
                attrList = list()
                for attr in ['translateX', 'translateY', 'translateZ']:
                    attrList.append(s + '.' + attr)
                    # hack for pre maya 2020.4.3
                    plug = self.funcs.getPlugsFromLayer(str(s) + '.' + attr, selectedLayer[0])
                    plugs[s + '.' + attr] = plug
                    curve = cmds.listConnections(plug, source=True, destination=False)
                    if curve:
                        curves[s + '.' + attr] = curve[0]
                        curveDuplicates[s + '.' + attr] = cmds.duplicate(curve[0])[0]
                constraints.append(pm.pointConstraint(locs, s))
                pm.bakeResults(attrList,
                               simulation=False,
                               disableImplicitControl=True,
                               # removeBakedAttributeFromLayer=False,
                               destinationLayer=selectedLayer[0],
                               sampleBy=1,
                               oversamplingRate=1,
                               preserveOutsideKeys=True,
                               sparseAnimCurveBake=True,
                               removeBakedAttributeFromLayer=False,
                               removeBakedAnimFromLayer=False,
                               bakeOnOverrideLayer=False,
                               minimizeRotation=True,
                               controlPoints=False,
                               shape=False,
                               time=(start, end),
                               )
                pm.delete(constraints)
                if cmds.animLayer(selectedLayer[0], query=True, override=True):
                    for attr in ['translateX', 'translateY', 'translateZ']:
                        # hack for pre maya 2020.4.3
                        curve = curves.get(s + '.' + attr, None)
                        if not curve:
                            continue
                        curveOriginal = curveDuplicates.get(s + '.' + attr, None)
                        resultCurve = cmds.listConnections(plugs[s + '.' + attr], source=True, destination=False)
                        cmds.copyKey(resultCurve, time=(start, end), option="curve")
                        cmds.pasteKey(curveOriginal, time=(start, end), animation="objects", option="fitReplace")
                        cmds.connectAttr(curveOriginal + '.output', plugs[s + '.' + attr], force=True)
                        cmds.delete(resultCurve)
                else:  # additive layer
                    for attr in ['translateX', 'translateY', 'translateZ']:
                        # hack for pre maya 2020.4.3
                        curve = curves.get(s + '.' + attr, None)
                        if not curve:
                            continue
                        curveOriginal = curveDuplicates.get(s + '.' + attr, None)
                        resultCurve = cmds.listConnections(plugs[s + '.' + attr], source=True, destination=False)

                        layerValues = []
                        baseplug, layerplug = self.funcs.getLowerLayerPlugs(s + '.' + attr, selectedLayer[0])
                        animRange = int(end - start + 1)
                        for x in range(0, animRange):
                            baseVal = cmds.getAttr(baseplug, time=start + x)
                            layerVal = cmds.getAttr(layerplug, time=start + x)
                            delta = layerVal - baseVal
                            layerValues.append(delta)
                        for x in range(0, animRange):
                            cmds.setKeyframe(resultCurve, time=start + x, value=layerValues[x])
                        cmds.copyKey(resultCurve, time=(start, end), option="curve")
                        cmds.pasteKey(curveOriginal, time=(start, end), animation="objects", option="fitReplace")
                        cmds.connectAttr(curveOriginal + '.output', plugs[s + '.' + attr], force=True)
                        cmds.delete(resultCurve)
            else:
                constraints.append(pm.pointConstraint(locs, s))
                pm.bakeResults(sel, simulation=False,
                               disableImplicitControl=True,
                               preserveOutsideKeys=True,
                               time=(start, end),
                               sampleBy=1)
                pm.delete(constraints)

        pm.delete(locs)

    def doJumpUsingInitialFrameVelocity(self):
        with self.funcs.keepSelection():
            self.jumpUsingInitialFrameVelocity()

    def jumpUsingInitialFrameVelocity(self):
        self.uiUnit = om.MTime.uiUnit()
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.uiUnit = om.MTime.uiUnit()
        sel = cmds.ls(sl=True)
        if not sel:
            return
        if self.funcs.isTimelineHighlighted():
            timeRange = self.funcs.getTimelineHighlightedRange()
        else:
            timeRange = self.funcs.getTimelineRange()
            timeRange[0] = cmds.currentTime(query=True)
        velStart = timeRange[0] - 1
        velEnd = timeRange[0]
        start = timeRange[0]
        end = timeRange[1]
        locs = dict()
        durationFrames = end - start
        for s in sel:
            locs[s] = self.funcs.tempLocator(name=s, suffix='gravity', scale=1.0, color=(1.0, 0.537, 0.016))
            mobj = self.getMobject(s)
            startMx, endMtx = self.getJumpDisplacement(mobj, velStart, velEnd)
            startTranslation = self.getMatrixTranslation(startMx)
            endTranslation = self.getMatrixTranslation(endMtx)
            initialVelocity = (endTranslation - startTranslation) * self.funcs.time_conversion()
            gravityVector = self.getGravity()
            arcX = self.arcCalc(endTranslation.x, initialVelocity.x, durationFrames, gravityVector[0])
            arcY = self.arcCalc(endTranslation.y, initialVelocity.y, durationFrames, gravityVector[1])
            arcZ = self.arcCalc(endTranslation.z, initialVelocity.z, durationFrames, gravityVector[2])
            self.keyJumpArc(arcX, arcY, arcZ, start, end, locs[s])

            self.bakeJumpToControl(start, end, locs[s], s)

    def getMatrixTranslation(self, mtx):
        startMTransform = om2.MTransformationMatrix(mtx)
        startTranslation = startMTransform.translation(om2.MSpace.kWorld)
        startTranslation.x /= self.funcs.unit_conversion()
        startTranslation.y /= self.funcs.unit_conversion()
        startTranslation.z /= self.funcs.unit_conversion()
        return startTranslation

    def doJumpAllKeypairs(self):
        with self.funcs.keepSelection():
            self.jumpAllKeypairs()

    def jumpAllKeypairs(self):
        self.uiUnit = om.MTime.uiUnit()
        sel = cmds.ls(sl=True)
        if not sel:
            return
        locs = dict()
        for s in sel:
            keyTimes = self.funcs.get_object_key_times(s)
            if not keyTimes:
                continue
            if len(keyTimes) == 1:
                continue
            locs[s] = self.funcs.tempLocator(name=s, suffix='gravity', scale=1.0, color=(1.0, 0.537, 0.016))
            for i in range(1, len(keyTimes)):
                self.jumpTimeRange(s, locs[s], keyTimes[i - 1], keyTimes[i])
            self.bakeJumpToControl(keyTimes[0], keyTimes[-1], locs[s], s)

    def jumpTimeRange(self, ref, locator, start, end):
        """
        Makes a jump locator for each object, jump duration is the selected timeline range
        :return:
        """
        duration = end - start

        mobj = self.getMobject(ref)
        startMx, endMtx = self.getJumpDisplacement(mobj, start, end)

        startTranslation = self.getMatrixTranslation(startMx)
        endTranslation = self.getMatrixTranslation(endMtx)

        arcX, arcY, arcZ = self.getJumpArc(startTranslation, endTranslation, duration)
        self.keyJumpArc(arcX, arcY, arcZ, start, end, locator)

    def keyJumpArc(self, arcX, arcY, arcZ, start, end, loc):
        for t in range(int(end - start) + 1):
            pm.setKeyframe(loc + '.translateX', time=start + t, value=arcX[t])
            pm.setKeyframe(loc + '.translateY', time=start + t, value=arcY[t])
            pm.setKeyframe(loc + '.translateZ', time=start + t, value=arcZ[t])

    def getTranslationAtTime(self, target, time):
        mobj = self.getMobject(target)
        timeMdg = om2.MDGContext(om2.MTime(time, self.uiUnit))
        Mtx = self.getWworldMatrixAtTime('worldMatrix', mobj, timeMdg)
        MTransform = om2.MTransformationMatrix(Mtx)
        translation = MTransform.translation(om2.MSpace.kWorld)
        rotatePivot = MTransform.rotatePivot(om2.MSpace.kWorld)
        rotatePivotTranslation = MTransform.rotatePivotTranslation(om2.MSpace.kPostTransform)

    def getJumpDisplacement(self, target, startTime, endTime):
        startTimeMdg = om2.MDGContext(om2.MTime(startTime, self.uiUnit))
        startMtx = self.getWworldMatrixAtTime('worldMatrix', target, startTimeMdg)
        endTimeMdg = om2.MDGContext(om2.MTime(endTime, self.uiUnit))
        endMtx = self.getWworldMatrixAtTime('worldMatrix', target, endTimeMdg)

        return startMtx, endMtx

    def getJumpInitialVelocity(self, x, duration, gravity):
        return (x / duration + (0.5 * gravity * duration))

    def getJumpArc(self, startTranslation, endTranslation, durationFrames):
        # calculate time vs frames
        gravityVector = self.getGravity()
        displacement = endTranslation - startTranslation
        durationSeconds = float(durationFrames / self.funcs.time_conversion())
        velocityX = self.getJumpInitialVelocity(displacement.x, durationSeconds, -gravityVector[0])
        velocityY = self.getJumpInitialVelocity(displacement.y, durationSeconds, -gravityVector[1])
        velocityZ = self.getJumpInitialVelocity(displacement.z, durationSeconds, -gravityVector[2])
        arcX = self.arcCalc(startTranslation.x, velocityX, durationFrames, gravityVector[0])
        arcY = self.arcCalc(startTranslation.y, velocityY, durationFrames, gravityVector[1])
        arcZ = self.arcCalc(startTranslation.z, velocityZ, durationFrames, gravityVector[2])
        return arcX, arcY, arcZ

    def arcCalc(self, x0, v0, durationFrames, gravity):
        units = self.funcs.time_conversion()
        outVals = list()
        for x in range(0, int(durationFrames + 1)):
            timeStep = float(x / units)
            outVals.append((x0 + v0 * timeStep + 0.5 * (timeStep * timeStep * gravity)))
        return outVals

    def getMobject(self, s):
        selection = om2.MSelectionList()
        selection.add(s)
        return selection.getDependNode(0)

    def getWworldMatrixAtTime(self, matrix, dep_node, mdg):
        '''
        :param dep_node: object string name i.e. "pSphere1"
        :param attr: the attribute to check i.e. "tx"
        :return: a list of values per frame.
        '''

        objMfn = om2.MFnDependencyNode(dep_node)
        ## Get the plug of the node. (networkedplug = False, as it no longer profides a speed improvement)
        plug = objMfn.findPlug(matrix, False).elementByLogicalIndex(0)
        rotatePivotXPlug = objMfn.findPlug('rotatePivotX', False)
        rotatePivotYPlug = objMfn.findPlug('rotatePivotY', False)
        rotatePivotZPlug = objMfn.findPlug('rotatePivotZ', False)
        value = om2.MFnMatrixData(plug.asMObject(mdg)).matrix()
        rotatePivotValueX = rotatePivotXPlug.asFloat(mdg)
        rotatePivotValueY = rotatePivotYPlug.asFloat(mdg)
        rotatePivotValueZ = rotatePivotZPlug.asFloat(mdg)
        tfmMatrix = om2.MTransformationMatrix()
        tfmMatrix.setTranslation(om2.MVector(rotatePivotValueX, rotatePivotValueY, rotatePivotValueZ),
                                 om2.MSpace.kWorld)
        return tfmMatrix.asMatrix() * value

    def updateOffsets(self):
        """
        Updates all offsets for capsules in scene
        :param sel:
        :return:
        """
        mainCapsuleNodes = cmds.ls('*:Capsules*')
        if not mainCapsuleNodes:
            return
        for node in mainCapsuleNodes:
            capsules = self.getCapsules(node)
            if not capsules:
                continue
            for c in capsules:
                constraints = cmds.listRelatives(c, type='parentConstraint')
                if not constraints:
                    continue
                targetList = cmds.parentConstraint(constraints[0], query=True, targetList=True)
                cmds.parentConstraint(targetList, constraints[0], edit=True, maintainOffset=True)

    def getConstrainForNode(self, node, exactType='parentConstraint'):
        constraints = cmds.listRelatives(node, type=exactType)
        if constraints:
            return constraints[0]
        return None

    def updateMainComConstraint(self, sel):
        com, floorCom = self.centreOfMassNode(sel)

        constraints = cmds.listRelatives(com, type='pointConstraint')
        capsules = self.getCapsules(sel)

        if not capsules:
            return
        if not constraints:
            mainConstraint = cmds.pointConstraint(capsules, com)
        else:
            mainConstraint = constraints[0]
        if isinstance(mainConstraint, list):
            mainConstraint = mainConstraint[0]
        cmds.pointConstraint(capsules, com)
        targetList = cmds.pointConstraint(mainConstraint, query=True, targetList=True)
        weightList = cmds.pointConstraint(mainConstraint, query=True, weightAliasList=True)

        for t, w in zip(targetList, weightList):
            if cmds.listConnections(mainConstraint + '.' + w, source=True, destination=False):
                continue
            cmds.connectAttr(t + '.volume', mainConstraint + '.' + w)

    def getCapsules(self, sel):
        capsules = cmds.listRelatives(self.mainCapsuleNode(sel), children=True)
        capsules = [c for c in capsules if c.endswith('_cap')]
        return capsules

    def alignCapsule(self, capsule, axis='x'):
        constraints = cmds.listRelatives(capsule, type='parentConstraint')
        if not constraints:
            return
        offsets = {'x': [0, 0, 90],
                   'y': [90, 0, 0],
                   'z': [0, 90, 0],
                   }
        for index, k in enumerate(offsets.keys()):
            cmds.setAttr(constraints[0] + ".target[0].targetOffsetRotate%s" % k.upper(), offsets[axis][index])

    def centreOfMassNode(self, sel):
        """
        Builds the centre of mass node constrained to the capsules
        :param sel:
        :return:
        """
        sel = pm.PyNode(sel)
        namespace = sel.namespace()
        mainNode = self.mainCapsuleNode(sel)
        mainComNode = self.mainCoMNode(sel)
        if not cmds.objExists(namespace + comNodeName):
            com = cmds.spaceLocator(name=namespace + comNodeName)
            cmds.setAttr(com[0] + '.overrideEnabled', 1)
            cmds.setAttr(com[0] + '.overrideColor', 17)
            cmds.setAttr(com[0] + '.localScaleY', 0.1)
            cmds.parent(com, mainComNode)
        if not cmds.objExists(namespace + floorComNodeName):
            floorCom = cmds.spaceLocator(name=namespace + floorComNodeName)
            cmds.parent(floorCom, mainComNode)
            cmds.setAttr(com[0] + '.overrideEnabled', 1)
            cmds.setAttr(com[0] + '.overrideColor', 18)
            cmds.pointConstraint(com[0], floorCom[0], skip=cmds.upAxis(query=True, axis=True))
        return namespace + comNodeName, namespace + floorComNodeName


    def mainCoMNode(self, sel):
        sel = pm.PyNode(sel)
        namespace = sel.namespace()
        if not cmds.objExists(namespace + mainNodeName):
            node = cmds.createNode('transform', name=namespace + mainNodeName)
            cmds.addAttr(node, ln='rig', at='message')
            pm.connectAttr(sel.root().message, node + '.rig')
            return node
        return namespace + mainNodeName

    def mainCapsuleNode(self, sel):
        sel = pm.PyNode(sel)
        namespace = sel.namespace()
        mainComNode = self.mainCoMNode(sel)
        if not cmds.objExists(namespace + capsuleNodeName):
            node = cmds.createNode('transform', name=namespace + capsuleNodeName)
            cmds.addAttr(node, ln='rig', at='message')
            pm.connectAttr(sel.root().message, node + '.rig')
            pm.parent(node, mainComNode)
            return node
        return namespace + capsuleNodeName

    def createCapsuleAtSelection(self, sel=None, axis='x'):
        if not sel:
            sel = cmds.ls(sl=True, type='joint')
        if not sel:
            return cmds.warning('Please select a joint')
        if not isinstance(sel, list):
            sel = [sel]
        for s in sel:
            capsule = self.createCapsule(s)
            if cmds.getModifiers() == 1:
                cmds.select(capsule, replace=True)
                self.pasteCapsule(capsule)
            cmds.parentConstraint(s, capsule)
            self.alignCapsule(capsule, axis=axis)
            cmds.parent(capsule, self.mainCapsuleNode(s))
            self.centreOfMassNode(s)
            self.updateMainComConstraint(capsule)
            cmds.select(capsule, replace=True)
        return capsule

    def createCapsule(self, name):
        createDebug_shader(name='capsuleShader', colour=[1, 0, 0])
        mainNode = cmds.cylinder(name=name + '_cap', p=(0, 0, 0), ax=(0, 1, 0), ssw=0, esw=360, r=1, hr=2, d=3, ut=0,
                                 tol=0.01, s=8, nsp=1, ch=1)[0]
        assignDebug_shader(shader='capsuleShader', obj=mainNode)
        cmds.connectAttr(mainNode + '.scaleX', mainNode + '.scaleZ')
        cmds.addAttr(mainNode, ln='volume', at='float')
        cmds.setAttr(mainNode + '.volume', edit=True, keyable=False, channelBox=True)
        names = ['tip', 'base']
        offsets = [1, -1]
        start = [180, 0]
        end = [360, 180]
        for index, x in enumerate(names):
            node = cmds.sphere(name=mainNode + '_' + x,
                               p=(0, 0, 0),
                               ax=(0, 0, 1),
                               ssw=start[index],
                               esw=end[index],
                               r=1, d=3, ut=0, tol=0.01,
                               s=8, nsp=4, ch=1)[0]
            assignDebug_shader(shader='capsuleShader', obj=node)
            cmds.parent(node, mainNode)
            cmds.setAttr(node + '.translate', 0, offsets[index], 0, type='double3')
            cmds.setAttr(node + ".overrideEnabled", 1)
            cmds.setAttr(node + ".overrideDisplayType", 2)
            cmds.setAttr(node + '.inheritsTransform', 0)
            constraint = cmds.parentConstraint(mainNode, node, maintainOffset=True)
            scaleConstraint = cmds.scaleConstraint(mainNode, node, maintainOffset=True, skip='y')
            pma = cmds.createNode('plusMinusAverage')
            cmds.setAttr(pma + '.operation', 3)
            cmds.connectAttr(scaleConstraint[0] + '.constraintScaleX', pma + '.input1D[0]')
            cmds.connectAttr(scaleConstraint[0] + '.constraintScaleZ', pma + '.input1D[1]')
            cmds.connectAttr(pma + '.output1D', node + '.scaleY')

        r_h = cmds.createNode('plusMinusAverage', name='r_h')
        cmds.connectAttr(mainNode + '.scaleY', r_h + '.input1D[0]')
        cmds.connectAttr(mainNode + '.scaleY', r_h + '.input1D[1]')

        r_m = cmds.createNode('multDoubleLinear', name='r_m')
        cmds.setAttr(r_m + '.input1', 1.3333333333333333)
        cmds.connectAttr(mainNode + '.scaleX', r_m + '.input2')
        r_m_h = cmds.createNode('addDoubleLinear', name='r_m_h')
        cmds.connectAttr(r_m + '.output', r_m_h + '.input1')
        cmds.connectAttr(r_h + '.output1D', r_m_h + '.input2')
        r2 = cmds.createNode('multiplyDivide', name='r2')
        cmds.setAttr(r2 + '.operation', 3)
        cmds.setAttr(r2 + '.input2X', 2)
        cmds.connectAttr(mainNode + '.scaleX', r2 + '.input1X')
        pi_r = cmds.createNode('multDoubleLinear', name='pi_r')
        cmds.setAttr(pi_r + '.input1', 3.142)
        cmds.connectAttr(r2 + '.outputX', pi_r + '.input2')

        pi_r_h = cmds.createNode('multDoubleLinear', name='pi_r_h')
        cmds.connectAttr(pi_r + '.output', pi_r_h + '.input1')
        cmds.connectAttr(r_m_h + '.output', pi_r_h + '.input2')
        cmds.connectAttr(pi_r_h + '.output', mainNode + '.volume')
        return mainNode

    def copyCapsule(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return
        if not cmds.attributeQuery('volume', node=sel[0], exists=True):
            return cmds.warning(sel[0], 'is not a capsule')
        capsule = sel[0]
        self.updateOffsets()
        self.copyData, self.copyConstraintOffset = self.cacheCapsule(capsule)
        return cmds.warning('capsule copied')

    def cacheCapsule(self, capsule):
        copyData = dict()
        copyConstraintOffset = dict()
        constraint = self.getConstrainForNode(capsule, exactType='parentConstraint')
        for key in self.copyData.keys():
            copyData[key] = cmds.getAttr(capsule + '.' + key)
        if constraint:
            for key in self.copyConstraintOffset.keys():
                copyConstraintOffset[key] = cmds.getAttr(constraint + '.target[0].targetOffset' + key)
        return copyData, copyConstraintOffset

    def pasteCapsule(self, sel=None, copyData=None, copyConstraintOffset=None, mirror=False):
        scale = -1 if mirror else 1
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return
        if not isinstance(sel, list):
            sel = [sel]
        if not copyData:
            copyData = self.copyData
        if not copyConstraintOffset:
            copyConstraintOffset = self.copyConstraintOffset
        if not copyData.keys():
            return cmds.warning('no copied capsule data')
        for s in sel:
            constraint = None
            if not cmds.attributeQuery('volume', node=s, exists=True):
                cmds.warning(s, 'is not a capsule, attempting to create a new one')
                continue

            constraint = self.getConstrainForNode(s, exactType='parentConstraint')
            for key in copyData.keys():
                cmds.setAttr(s + '.' + key, copyData[key])
            if constraint:
                for key in copyConstraintOffset.keys():
                    cmds.setAttr(constraint + '.target[0].targetOffset' + key, scale * copyConstraintOffset[key])
        self.updateMainComConstraint(sel[0])

    def getMirrorName(self, node, sideList):
        for s in sideList:
            if s in node:
                return node.replace(s, sideList[not sideList.index(s)])
        return node

    def sideAUpdated(self, value):
        self.sides[0] = value
        pm.optionVar[capsuleSideA] = value

    def sideBUpdated(self, value):
        self.sides[1] = value
        pm.optionVar[capsuleSideB] = value

    def mirrorSelectedCapsules(self, sideList=None):
        if not sideList:
            sideList = self.sides

        sel = cmds.ls(sl=True)
        if not sel:
            return
        capsules = [s for s in sel if cmds.attributeQuery('volume', node=s, exists=True)]
        for c in capsules:
            baseName = c.rsplit('_cap')[0]
            mirrorObject = self.getMirrorName(baseName, sideList)
            if mirrorObject == baseName:
                continue
            self.copyCapsule([c])
            cmds.select(mirrorObject, replace=True)
            newCapsule = self.createCapsuleAtSelection()
            cmds.select(newCapsule)
            self.pasteCapsule([newCapsule], mirror=True)
        self.updateMainComConstraint(sel[0])

    def bakeNode(self, sel=None, target='COM'):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No last rig used')
        refname, namespace = self.funcs.getCurrentRig(sel)

        targetObject = namespace + ':' + target
        if not cmds.objExists(targetObject):
            return cmds.warning('Cannot find %s' % targetObject)
        if cmds.objExists(targetObject + '_Baked'):
            cmds.delete(targetObject + '_Baked')
        tempControl = self.funcs.tempControl(name=targetObject, suffix='Baked', drawType='cross', scale=0.1)
        if self.funcs.isTimelineHighlighted():
            bakeRange = self.funcs.getTimelineHighlightedRange()
        else:
            bakeRange = self.funcs.getTimelineRange()

        pm.pointConstraint(targetObject, tempControl)
        self.allTools.tools['BakeTools'].quickBake(tempControl, startTime=bakeRange[0], endTime=bakeRange[-1],
                                                   deleteConstraints=True)
        return tempControl

    def toggleCapsuleVis(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No last rig used')
        sel = pm.PyNode(sel[0])

        visState = cmds.getAttr(self.mainCapsuleNode(sel) + '.visibility')
        cmds.setAttr(self.mainCapsuleNode(sel) + '.visibility', not visState)

    def toggleNodeVis(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No last rig used')

        sel = pm.PyNode(sel[0])
        com, floorCom = self.centreOfMassNode(sel)
        visState = cmds.getAttr(com + '.visibility')
        cmds.setAttr(com + '.visibility', not visState)
        cmds.setAttr(floorCom + '.visibility', not visState)

    def bakeComToNode(self):
        self.bakeNode(target='COM')

    def bakeFloorComToNode(self):
        self.bakeNode(target='COM_Floor')

    def bakeSelToCOM(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        tempControl = self.bakeNode(target='COM')
        sel.append(tempControl)
        self.allTools.tools['BakeTools'].bake_to_locator_pinned(sel=sel, constrain=True)

    def bakeSelToFloorCOM(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        tempControl = self.bakeNode(target='COM_Floor')
        sel.append(tempControl)
        self.allTools.tools['BakeTools'].bake_to_locator_pinned(sel=sel, constrain=True)

    def setLastUsedRig(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No last rig used')
        if not isinstance(sel, list):
            sel = [sel]

        refname, namespace = self.funcs.getCurrentRig(sel)

        self.lastSelectedRig = refname

    def saveCurrentCapsules(self, sel=None):
        rigToSave = None
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            if not self.lastSelectedRig:
                return

    def loadCapsules(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        mainCapsule = self.mainCapsuleNode(sel[0])
        if not mainCapsule:
            refname, namespace = self.funcs.getCurrentRig(sel)
        else:
            rigRoot = cmds.listConnections(mainCapsule + '.rig', source=True, destination=False)
            refname, namespace = self.funcs.getCurrentRig(rigRoot)
            cmds.delete(mainCapsule)

        dataFile = os.path.join(self.comTemplateDir, refname + '.json')
        jsonData = json.load(open(dataFile))

        for key in jsonData['offsets'].keys():
            capsuleTarget = namespace + ':' + key.rsplit('_cap')[0]

            newCapsule = self.createCapsuleAtSelection(sel=capsuleTarget, axis='x')
            self.pasteCapsule([newCapsule], copyData=jsonData['offsets'][key],
                              copyConstraintOffset=jsonData['constraintOffsets'][key])

    def saveCapsules(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        mainCapsule = self.mainCapsuleNode(sel[0])
        if not mainCapsule:
            return cmds.warning('No main node for selection')
        capsules = self.getCapsules(sel[0])
        if not capsules:
            return cmds.warning('No capsules for selection')
        rigRoot = cmds.listConnections(mainCapsule + '.rig', source=True, destination=False)

        refname, namespace = self.funcs.getCurrentRig(rigRoot)
        jsonData = '''{}'''
        setData = json.loads(jsonData)
        setData['targets'] = dict()
        setData['offsets'] = dict()
        setData['constraintOffsets'] = dict()

        for cap in capsules:
            copyData, copyConstraintOffset = self.cacheCapsule(cap)
            pCap = pm.PyNode(cap)
            capName = pCap.stripNamespace()
            targetName = capName.rsplit('_cap')[0]

            setData['targets'][capName] = targetName
            setData['offsets'][capName] = copyData
            setData['constraintOffsets'][capName] = copyConstraintOffset
        dataFile = os.path.join(self.comTemplateDir, refname + '.json')

        self.saveJsonFile(dataFile, setData)

    def getToolboxWidget(self, widget):
        buttonWidth = 108
        buttonHeight = 40
        '''
        cmds.setParent()
        if cmds.menu(TOOLBOX_MENU, exists=True):
            cmds.deleteUI(TOOLBOX_MENU)
        menuBar = cmds.menu(TOOLBOX_MENU, label=TOOLBOX_MENU, tearOff=True)
        '''

        def setAnimMode():
            stackedWidget.setCurrentIndex(0)
            animButton.setEnabled(True)
            editButton.setDisabled(True)
            pm.optionVar['tbComEditMode'] = True

        def setEditMode():
            stackedWidget.setCurrentIndex(1)
            animButton.setDisabled(True)
            editButton.setEnabled(True)
            pm.optionVar['tbComEditMode'] = False

        toolBoxWidget = QWidget()
        toolBoxWidget.setContentsMargins(0, 0, 0, 0)
        toolBoxLayout = QVBoxLayout()
        toolBoxLayout.setContentsMargins(0, 0, 0, 0)
        toolBoxLayout.setSpacing(0)
        editMainWidget = QWidget()
        editMainWidget.setContentsMargins(0, 0, 0, 0)
        editMainLayout = QVBoxLayout()
        editMainLayout.setContentsMargins(0, 0, 0, 0)
        editMainLayout.setSpacing(0)
        editMainWidget.setLayout(editMainLayout)
        animMainLWidget = QWidget()
        animMainLWidget.setContentsMargins(0, 0, 0, 0)
        animMainLayout = QVBoxLayout()
        animMainLayout.setContentsMargins(0, 0, 0, 0)
        animMainLayout.setSpacing(0)
        animMainLWidget.setLayout(animMainLayout)

        toolBoxWidget.setLayout(toolBoxLayout)

        stackedWidget = QStackedWidget()

        editButton = QPushButton('Edit')
        editButton.clicked.connect(setAnimMode)
        animButton = QPushButton('Anim')
        animButton.clicked.connect(setEditMode)
        modeLayout = QHBoxLayout()
        modeLayout.addWidget(editButton)
        modeLayout.addWidget(animButton)

        menuBar = None
        viewLayout = QHBoxLayout()
        xrayJointButton = ToolButton(text='Toggle\nxray',
                                     imgLabel='Tips',
                                     width=buttonWidth,
                                     height=buttonHeight,
                                     icon=":/QR_xRay.png",
                                     command='ViewMode_xray_joints')

        isolateButton = ToolButton(text='Toggle\nIsolate',
                                   imgLabel='Tips',
                                   width=buttonWidth,
                                   height=buttonHeight,
                                   icon=":/IsolateSelected.png",
                                   command='toggle_isolate_selection')

        viewLayout.addWidget(isolateButton)
        viewLayout.addWidget(xrayJointButton)

        createLayout = QVBoxLayout()
        createLabel = QLabel('Create Capsule')
        colPoseButton = ToolButton(text='Create Capsule',
                                   imgLabel='Sel',
                                   width=2 * buttonWidth,
                                   icon=":/hairConvertConstraint.png",
                                   sourceType='py',
                                   command=self.createCapsuleAtSelection)

        updateOffsetsButton = ToolButton(text='Update offsets',
                                         imgLabel='Group',
                                         width=2 * buttonWidth,
                                         icon=":/hairConvertConstraint.png",
                                         sourceType='py',
                                         command=self.updateOffsets)

        createAlignLayout = QHBoxLayout()
        createXAlignButton = ToolButton(text='X',
                                        imgLabel='Sel',
                                        height=22,
                                        width=(2 * buttonWidth) / 3.0, sourceType='py',
                                        command=pm.Callback(self.createCapsuleAtSelection, None, 'x'))
        createYAlignButton = ToolButton(text='Y',
                                        imgLabel='All',
                                        height=22,
                                        width=(2 * buttonWidth) / 3.0, sourceType='py',
                                        command=pm.Callback(self.createCapsuleAtSelection, None, 'y'))
        createZAlignButton = ToolButton(text='Z',
                                        imgLabel='All',
                                        height=22,
                                        width=(2 * buttonWidth) / 3.0, sourceType='py',
                                        command=pm.Callback(self.createCapsuleAtSelection, None, 'z'))

        createAlignLayout.addWidget(createXAlignButton)
        createAlignLayout.addWidget(createYAlignButton)
        createAlignLayout.addWidget(createZAlignButton)
        createLayout.addWidget(createLabel)
        createLayout.addLayout(createAlignLayout)
        createLayout.addWidget(updateOffsetsButton)

        alignLayout = QHBoxLayout()
        xAlignButton = ToolButton(text='Align X',
                                  imgLabel='Sel',
                                  height=22,
                                  width=(2 * buttonWidth) / 3.0,
                                  command='tbBakeCollisionSelected')
        yAlignButton = ToolButton(text='Align Y',
                                  imgLabel='All',
                                  height=22,
                                  width=(2 * buttonWidth) / 3.0,
                                  command='tbBakeAllCollisionSelected')
        zAlignButton = ToolButton(text='Align Z',
                                  imgLabel='All',
                                  height=22,
                                  width=(2 * buttonWidth) / 3.0,
                                  command='tbBakeAllCollisionSelected')

        alignLayout.addWidget(xAlignButton)
        alignLayout.addWidget(yAlignButton)
        alignLayout.addWidget(zAlignButton)

        saveLoadLayout = QHBoxLayout()
        loadButton = ToolButton(text='Load',
                                icon=":/openScript.png", sourceType='py',
                                height=22,
                                command=self.loadCapsules)
        saveButton = ToolButton(text='Save',
                                icon=":/save.png", sourceType='py',
                                height=22,
                                command=self.saveCapsules)
        saveLoadLayout.addWidget(loadButton)
        saveLoadLayout.addWidget(saveButton)

        copyPasteLayout = QHBoxLayout()
        copyButton = ToolButton(text='Copy',
                                icon=":/copyUV.png", sourceType='py',
                                height=22,
                                command=self.copyCapsule)
        pasteButton = ToolButton(text='Paste',
                                 icon=":/pasteUV.png", sourceType='py',
                                 height=22,
                                 command=self.pasteCapsule)
        copyPasteLayout.addWidget(copyButton)
        copyPasteLayout.addWidget(pasteButton)

        mirrorLayout = QHBoxLayout()
        mirrorButton = ToolButton(text='Mirror',
                                  icon=":/delete.png", sourceType='py',
                                  width=(2 * buttonWidth) / 3.0,
                                  height=22,
                                  command=self.mirrorSelectedCapsules)
        sideALineEdit = QLineEdit(self.sides[0])
        sideALineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        sideALineEdit.textChanged.connect(self.sideAUpdated)
        sideBLineEdit = QLineEdit(self.sides[1])
        sideBLineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        sideBLineEdit.textChanged.connect(self.sideBUpdated)
        mirrorLayout.addWidget(mirrorButton)
        mirrorLayout.addWidget(sideALineEdit)
        mirrorLayout.addWidget(sideBLineEdit)

        editMainLayout.addLayout(viewLayout)
        editMainLayout.addLayout(createLayout)
        # editMainLayout.addLayout(alignLayout)
        editMainLayout.addLayout(mirrorLayout)
        editMainLayout.addLayout(copyPasteLayout)
        editMainLayout.addLayout(saveLoadLayout)

        toolBoxLayout.addLayout(modeLayout)
        toolBoxLayout.addWidget(stackedWidget)
        stackedWidget.addWidget(editMainWidget)
        stackedWidget.addWidget(animMainLWidget)

        # Anim layout
        bakeLayout = QVBoxLayout()
        bakeLabel = QLabel('Bake CoM')
        bakeButtonLayout = QVBoxLayout()
        toggleCapButton = ToolButton(text='Toggle Capsule Vis',
                                     icon=":RS_visible.png",
                                     sourceType='py',
                                     height=32,
                                     width=2 * buttonWidth,
                                     command=self.toggleCapsuleVis)
        toggleNodeButton = ToolButton(text='Toggle Node Vis',
                                     icon=":RS_visible.png",
                                     sourceType='py',
                                     height=32,
                                     width=2 * buttonWidth,
                                     command=self.toggleNodeVis)
        bakeCOMButton = ToolButton(text='Bake CoM to node',
                                   imgLabel='Sel',
                                   sourceType='py',
                                   height=22,
                                   width=2 * buttonWidth,
                                   command=self.bakeComToNode)
        bakeFloorCOMButton = ToolButton(text='Bake Floor CoM to node',
                                        imgLabel='Sel',
                                        sourceType='py',
                                        height=22,
                                        width=2 * buttonWidth,
                                        command=self.bakeFloorComToNode)
        bakeSelToCOMButton = ToolButton(text='Bake Selection to CoM',
                                        imgLabel='Sel',
                                        sourceType='py',
                                        height=22,
                                        width=2 * buttonWidth,
                                        command=self.bakeSelToCOM)
        bakeSelToFloorCOMButton = ToolButton(text='Bake Selection to Floor CoM',
                                             imgLabel='Sel',
                                             sourceType='py',
                                             height=22,
                                             width=2 * buttonWidth,
                                             command=self.bakeSelToFloorCOM)
        bakeLayout.addWidget(bakeLabel)
        bakeLayout.addLayout(bakeButtonLayout)
        bakeButtonLayout.addWidget(toggleCapButton)
        bakeButtonLayout.addWidget(toggleNodeButton)
        bakeButtonLayout.addWidget(bakeCOMButton)
        bakeButtonLayout.addWidget(bakeFloorCOMButton)
        bakeButtonLayout.addWidget(bakeSelToCOMButton)
        bakeButtonLayout.addWidget(bakeSelToFloorCOMButton)

        animMainLayout.addLayout(bakeLayout)

        editMode = pm.optionVar.get('tbComEditMode', True)
        if editMode:
            setAnimMode()
        else:
            setEditMode()
        return toolBoxWidget

    def toolBoxUI(self):
        # if not self.toolbox:
        self.toolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                                  title='tb Centre of Mass', text=str(),
                                  lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, )
        self.toolbox.mainLayout.addWidget(self.getToolboxWidget(self.toolbox))

        self.toolbox.show()
        self.toolbox.setFixedSize(self.toolbox.sizeHint())


def createDebug_shader(name='capsuleShader', colour=[0.034, 1, 0]):
    if not pm.objExists(name):
        shader = pm.shadingNode('lambert', asShader=True, name=name)
        shader.color.set(colour)
        shader.ambientColor.set(0.266, 0.266, 0.266)
        shader.transparency.set(0.75, 0.75, 0.75)
        # shader.incandescence.set(colour)
    else:
        shader = pm.PyNode(name)


def assignDebug_shader(shader='capsuleShader', obj=[]):
    if obj and cmds.objExists(shader):
        assignObjectListToShader(obj, shader)


def assignObjectListToShader(objList=None, shader=None):
    """
    Assign the shader to the object list
    arguments:
        objList: list of objects or faces
    """
    # assign selection to the shader
    shaderSG = getSGfromShader(shader)
    if objList:
        if shaderSG:
            cmds.sets(objList, e=True, forceElement=shaderSG)
        else:
            print ('The provided shader didn\'t returned a shaderSG')
    else:
        print ('Please select one or more objects')


def getSGfromShader(shader=None):
    if shader:
        if cmds.objExists(shader):
            sgq = cmds.listConnections(shader, d=True, et=True, t='shadingEngine')
            if sgq:
                return sgq[0]
            else:
                sqq = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + 'SG')
                cmds.defaultNavigation(connectToExisting=True, source=shader, destination=sqq)
                return sqq
    return None
