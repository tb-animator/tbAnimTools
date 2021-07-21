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
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import pymel.core.datatypes as dt
import math
import bisect
from Abstract import *
from tb_UI import *

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    #from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    #from pyside2uic import *
    from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

import maya.OpenMaya as om

import math
import sys
import pymel.core as pm
import pymel.core.datatypes as dt


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('gravity'))
        self.addCommand(self.tb_hkey(name='quickJump',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.doQuickJump()'],
                                     help=self.helpStrings.gravity.get('quickJump')))
        self.addCommand(self.tb_hkey(name='jumpAllKeypairs',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.jumpAllKeypairs()'],
                                     help=self.helpStrings.gravity.get('doJumpAllKeypairs')))
        self.addCommand(self.tb_hkey(name='jumpUsingInitialFrameVelocity',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.jumpUsingInitialFrameVelocity()'],
                                     help=self.helpStrings.gravity.get('doJumpUsingInitialFrameVelocity')))
        self.addCommand(self.tb_hkey(name='GravtiyToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.openMM()']))
        self.addCommand(self.tb_hkey(name='GravtiyToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['GravityTools.closeMM()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class GravityTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    #__metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'GravityTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    gravityOption = 'tbGravityOption'
    defaultGravity = -981

    def __new__(cls):
        if GravityTools.__instance is None:
            GravityTools.__instance = object.__new__(cls)

        GravityTools.__instance.val = cls.toolName
        GravityTools.__instance.loadData()

        return GravityTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.gravity = pm.optionVar.get(self.gravityOption, self.defaultGravity)
        self.uiUnit = om.MTime.uiUnit()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

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

    def build_MM(self):
        cmds.menuItem(label='tbGravtiyTools',
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick Aim',
                      command=self.quickAim,
                      )
        cmds.menuItem(label='tbGravtiyTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )

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

        for s in sel:
            if timeRange is None:
                keyTimes = self.funcs.get_object_key_times(s)
                idx = bisect.bisect_left(keyTimes, currentTime)
                if idx - 1 < 0:
                    start = currentTime
                else:
                    start = keyTimes[idx - 1]
                if idx >= len(keyTimes):
                    end = currentTime
                else:
                    end = keyTimes[idx]
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

        self.bakeJumpToControl(start, end, locs, sel)

    def bakeJumpToControl(self, start, end, locs, sel):
        constraints = list()
        if not isinstance(sel, list):
            sel = [sel]

        selectedLayer = self.funcs.get_selected_layers(ignoreBase=True)
        attrList = list()
        plugs = dict()
        curves = dict()
        curveDuplicates = dict()

        if len(selectedLayer):
            """
            Baking to a layer will remove the outside keys, as preserveOutsideKeys does not work with layers
            Need a function to snapshot the existing animation and merge it after baking
            """

            for s in sel:
                for attr in ['translateX', 'translateY', 'translateZ']:
                    attrList.append(s + '.' + attr)
                    # hack for pre maya 2020.4.3
                    plug = self.funcs.getPlugsFromLayer(str(s) + '.' + attr, selectedLayer[0])
                    plugs[s + '.' + attr] = plug
                    curve = cmds.listConnections(plug, source=True, destination=False)
                    if curve:
                        curves[s + '.' + attr] = curve[0]
                        curveDuplicates[s + '.' + attr] = cmds.duplicate(curve[0])[0]

        for s in sel:
            constraints.append(pm.pointConstraint(locs[s], s))

        if len(selectedLayer):
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

            for s in sel:
                for attr in ['translateX', 'translateY', 'translateZ']:
                    # hack for pre maya 2020.4.3
                    curve = curves.get(s + '.' + attr, None)
                    if not curve:
                        continue
                    curveOriginal = curveDuplicates.get(s + '.' + attr, None)
                    resultCurve = cmds.listConnections(plugs[s + '.' + attr] , source=True, destination=False)
                    cmds.copyKey(resultCurve, time=(start, end), option="curve")
                    cmds.pasteKey(curveOriginal, time=(start, end), animation="objects", option="fitReplace")
                    cmds.connectAttr(curveOriginal + '.output', plugs[s + '.' + attr], force=True)
                    cmds.delete(resultCurve)
        else:
            pm.bakeResults(sel, simulation=False,
                           disableImplicitControl=True,
                           # removeBakedAttributeFromLayer=False,
                           # destinationLayer=pm.animLayer(query=True, root=True),
                           # bakeOnOverrideLayer=False,
                           preserveOutsideKeys=True,
                           time=(start, end),
                           sampleBy=1)

        pm.delete(constraints)
        for s in sel:
            pm.delete(locs[s])

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
            arcX = self.arcCalc(endTranslation.x, initialVelocity.x, durationFrames, 0)
            arcY = self.arcCalc(endTranslation.y, initialVelocity.y, durationFrames,
                                self.gravity / self.funcs.unit_conversion())
            arcZ = self.arcCalc(endTranslation.z, initialVelocity.z, durationFrames, 0)
            self.keyJumpArc(arcX, arcY, arcZ, start, end, locs[s])

        self.bakeJumpToControl(start, end, locs, sel)

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
            self.bakeJumpToControl(keyTimes[0], keyTimes[-1], locs, s)

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
        displacement = endTranslation - startTranslation
        durationSeconds = float(durationFrames / self.funcs.time_conversion())
        velocityX = self.getJumpInitialVelocity(displacement.x, durationSeconds, 0)
        velocityY = self.getJumpInitialVelocity(displacement.y, durationSeconds,
                                                -self.gravity / self.funcs.unit_conversion())
        velocityZ = self.getJumpInitialVelocity(displacement.z, durationSeconds, 0)
        arcX = self.arcCalc(startTranslation.x, velocityX, durationFrames, 0)
        arcY = self.arcCalc(startTranslation.y, velocityY, durationFrames, self.gravity / self.funcs.unit_conversion())
        arcZ = self.arcCalc(startTranslation.z, velocityZ, durationFrames, 0)
        return arcX, arcY, arcZ

    def arcCalc(self, x0, v0, durationFrames, gravity):
        outVals = list()
        for x in range(0, int(durationFrames + 1)):
            timeStep = float(x / self.funcs.time_conversion())
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
