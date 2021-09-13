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
from Abstract import *
import itertools

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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('motionTrails'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='toggleMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.toggleMotionTrail()'],
                                     help=self.helpStrings.toggleMotionTrail))
        self.addCommand(self.tb_hkey(name='createCameraRelativeMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.createMotionTrail()'],
                                     help=self.helpStrings.createMotionTrail))
        self.addCommand(self.tb_hkey(name='createMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.createMotionTrail()'],
                                     help=self.helpStrings.createMotionTrail))
        self.addCommand(self.tb_hkey(name='removeMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.removeMotionTrail()'],
                                     help=self.helpStrings.removeMotionTrail))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class MotionTrails(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'MotionTrails'
    hotkeyClass = hotkeys()
    funcs = functions()

    trailFadeFramesOption = 'tbMotrailFadeFramesOption'
    trailPreFramesOption = 'tbMotrailPreFramesOption'
    trailPostFramesOption = 'tbMotrailPostFramesOption'
    trailThicknessOption = 'tbMotrailThicknessOption'
    trailframeMarkerSizesOption = 'tbMotrailframeMarkerSizesOption'
    showframeMarkerOption = 'tbMotrailshowFrameMarkerOption'

    motionTrailNodes = ['motionTrailShape', 'motionTrail1Handle', 'motionTrail']

    def __new__(cls):
        if MotionTrails.__instance is None:
            MotionTrails.__instance = object.__new__(cls)

        MotionTrails.__instance.val = cls.toolName
        return MotionTrails.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(MotionTrails, self).optionUI()
        infoText = QLabel()
        infoText.setText('Motion trail display settings')
        infoText.setWordWrap(True)
        fadeLayout = QHBoxLayout()
        markerLayout = QHBoxLayout()

        trailFadeFramesWidget = intFieldWidget(optionVar=self.trailFadeFramesOption,
                                               defaultValue=5,
                                               label='Fade Frames',
                                               minimum=0, maximum=100, step=1)
        trailPreFramesWidget = intFieldWidget(optionVar=self.trailPreFramesOption,
                                              defaultValue=15,
                                              label='Pre Frames',
                                              minimum=0, maximum=100, step=1)
        trailPostFramesWidget = intFieldWidget(optionVar=self.trailPostFramesOption,
                                               defaultValue=15,
                                               label='Post frames',
                                               minimum=0, maximum=100, step=1)
        trailThicknessWidget = intFieldWidget(optionVar=self.trailThicknessOption,
                                              defaultValue=1.0,
                                              label='Thickness',
                                              minimum=1, maximum=10, step=1)
        trailframeMarkerSizesWidget = intFieldWidget(optionVar=self.trailframeMarkerSizesOption,
                                                     defaultValue=0,
                                                     label='Marker Size',
                                                     minimum=1, maximum=10, step=1)
        showTicksOptionWidget = optionVarBoolWidget('Show frame markers',
                                                    self.showframeMarkerOption)

        self.layout.addWidget(infoText)

        self.layout.addLayout(fadeLayout)
        self.layout.addLayout(markerLayout)
        fadeLayout.addWidget(trailFadeFramesWidget)
        fadeLayout.addWidget(trailPreFramesWidget)
        fadeLayout.addWidget(trailPostFramesWidget)
        markerLayout.addWidget(trailThicknessWidget)
        markerLayout.addWidget(trailframeMarkerSizesWidget)
        markerLayout.addWidget(showTicksOptionWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def toggleMotionTrail(self):
        sel = cmds.ls(sl=True)
        disable = True
        if not sel:
            allMotionTrails = self.getAllMotionTrails()
            if not allMotionTrails:
                return
        else:
            for s in sel:
                if self.isMotionTrail(s):
                    continue
                if not self.hasMotionTrail(s):
                    self.createMotionTrail([s])
                    disable = False
            allMotionTrails = self.getAllMotionTrailsFromSelection(sel=sel)
        if not allMotionTrails:
            return
        if all([cmds.getAttr("{0}.nodeState".format(m)) == 2 for m in allMotionTrails]):
            disable = False

        for motionTrail in allMotionTrails:
            motionTrailShape = self.getMotionTrailShape(motionTrail)
            if disable:
                self.disableMotionTrail(motionTrail, motionTrailShape[0])
            else:
                self.enableMotionTrail(motionTrail, motionTrailShape[0])

    def getCurrentCamera(self):
        view = omUI.M3dView.active3dView()
        cam = om.MDagPath()
        view.getCamera(cam)
        camPath = cam.partialPathName()
        print (camPath)

        return camPath

    def createCameraRelativeMotionTrail(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.createMotionTrail(sel=sel, camera=self.getCurrentCamera())

    def createMotionTrail(self, sel=None, camera=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return
        with self.funcs.keepSelection():
            trials = []
            for s in sel:
                if self.hasMotionTrail(s):
                    continue
                cmds.select(s, replace=True)
                moTrail = cmds.snapshot(motionTrail=True,
                                        increment=1,
                                        startTime=self.funcs.getTimelineMin(),
                                        endTime=self.funcs.getTimelineMax())
                cmds.setAttr(moTrail[0] + '.trailThickness', pm.optionVar.get(self.trailThicknessOption, 1))
                cmds.setAttr(moTrail[0] + '.fadeInoutFrames', pm.optionVar.get(self.trailFadeFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.preFrame', pm.optionVar.get(self.trailPreFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.postFrame', pm.optionVar.get(self.trailPostFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.frameMarkerSize', pm.optionVar.get(self.trailframeMarkerSizesOption, 1))
                cmds.setAttr(moTrail[0] + '.showFrameMarkers', pm.optionVar.get(self.showframeMarkerOption, 0))
                print('moTrail', moTrail)
                cmds.select(moTrail, replace=True)
                if camera:
                    cmds.addAttr(moTrail[1], ln='camera', at='message')
                    cmds.connectAttr('{0}.message'.format(camera), '{0}.camera'.format(moTrail[1]))
                    camInverse = cmds.createNode('multMatrix', name=s + '_' + camera + '_trailLocal')

                    trailDecomp = cmds.createNode('decomposeMatrix', name=s + '_' + camera + '_localDecomp')

                    cmds.connectAttr('{0}.worldMatrix'.format(s), '{0}.matrixIn[0]'.format(camInverse))
                    cmds.connectAttr('{0}.worldInverseMatrix'.format(camera), '{0}.matrixIn[1]'.format(camInverse))
                    cmds.connectAttr('{0}.matrixSum'.format(camInverse), '{0}.inputMatrix'.format(moTrail[1]),
                                     force=True)

                    cmds.setAttr('{0}.translate'.format(moTrail[0]), lock=False)
                    cmds.setAttr('{0}.rotate'.format(moTrail[0]), lock=False)
                    cmds.setAttr('{0}.scale'.format(moTrail[0]), lock=False)
                    cmds.setAttr('{0}.scale'.format(moTrail[0]), 0.05, 0.05, 0.05, type='double3')
                    cmds.connectAttr('{0}.worldMatrix'.format(camera), '{0}.inputMatrix'.format(trailDecomp))
                    cmds.connectAttr('{0}.outputTranslate'.format(trailDecomp), '{0}.translate'.format(moTrail[0]),
                                     force=True)
                    cmds.connectAttr('{0}.outputRotate'.format(trailDecomp), '{0}.rotate'.format(moTrail[0]),
                                     force=True)
                mel.eval("addToIsolation")

    def isMotionTrail(self, s):
        childNodes = cmds.listRelatives(s, children=True)
        if not childNodes:
            return False
        return any([cmds.nodeType(c) == 'motionTrailShape' for c in childNodes])

    def hasMotionTrail(self, s):
        messageConnection = cmds.listConnections(s + '.message', source=False, destination=True, plugs=False)
        if not messageConnection:
            return False
        for m in messageConnection:
            childNodes = cmds.listRelatives(m, children=True)
            if childNodes:
                for c in childNodes:
                    if cmds.nodeType(c) in self.motionTrailNodes:
                        return True
            if cmds.nodeType(m) in self.motionTrailNodes:
                return True
        return False

    def findAllMotionTrails(self):
        return cmds.ls(type='motionTrail')

    def disableMotionTrail(self, motionTrail, trialShape):
        cmds.setAttr("{0}.nodeState".format(motionTrail), 2)
        cmds.setAttr("{0}.visibility".format(trialShape), False)

    def enableMotionTrail(self, motionTrail, trialShape):
        cmds.setAttr("{0}.nodeState".format(motionTrail), 0)
        cmds.setAttr("{0}.visibility".format(trialShape), True)
        if cmds.attributeQuery('camera', node=motionTrail, exists=True):
            print ('is camera relative')

    def getMotionTrailShape(self, motionTrail):
        return list(set(cmds.listConnections(motionTrail, source=False, destination=True, plugs=False)))

    def getAllMotionTrails(self):
        return cmds.ls(type='motionTrail')

    def getAllMotionTrailsFromSelection(self, sel):
        allMotionTrails = list()
        for s in sel:
            connections = cmds.listConnections(s, source=False, destination=True, plugs=False, type='motionTrail')
            if connections is None:
                if self.isMotionTrail(s):
                    rel = list(set([c for c in cmds.listRelatives(s) if cmds.nodeType(c) == 'motionTrailShape']))
                    for r in rel:
                        allMotionTrails.append(list(set(cmds.listConnections(r,
                                                                             source=True,
                                                                             destination=False,
                                                                             plugs=False,
                                                                             type='motionTrail'))))
            else:
                allMotionTrails.append(list(set(connections)))
        return list(set([y for x in allMotionTrails for y in x]))

    def getMotionTrailNodes(self, node):
        """
        Get the motion trails associated with the input node
        :param node:
        :return:
        """
        messageConnection = cmds.listConnections(node + '.message', source=False, destination=True, plugs=False)
        shape = list()
        trail = list()
        if messageConnection:
            print ('message', messageConnection)
            for m in messageConnection:
                childNodes = cmds.listRelatives(m, children=True)
                if childNodes:
                    for c in childNodes:
                        print ('    c', c)
                        if cmds.nodeType(c) == 'motionTrailShape':
                            shape.append(c)
                        if cmds.nodeType(c) == 'motionTrail':
                            trail.append(c)

                if cmds.nodeType(m) == 'motionTrailShape':
                    shape.append(m)
                if cmds.nodeType(m) == 'motionTrail':
                    trail.append(m)

        return trail, shape

    def removeMotionTrail(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            allMotionTrails = self.getAllMotionTrails()
            sel = [self.getNodeFromMotionTrail(x)[0] for x in allMotionTrails]
        if not sel:
            return

        for s in sel:
            messageConnection = cmds.listConnections('{0}.message'.format(s),
                                                     source=False,
                                                     destination=True,
                                                     plugs=False)
            nodesToRemove = list()
            if messageConnection:
                for m in messageConnection:
                    childNodes = cmds.listRelatives(m, children=True)
                    if childNodes:
                        for c in childNodes:
                            if cmds.nodeType(c) in self.motionTrailNodes:
                                nodesToRemove.append(m)
                    if cmds.nodeType(m) in self.motionTrailNodes:
                        nodesToRemove.append(m)

            if nodesToRemove:
                cmds.delete(nodesToRemove)

    def getNodeFromMotionTrail(self, node):
        return list(set(cmds.listConnections(node,
                                             source=True,
                                             destination=False,
                                             plugs=False,
                                             type='transform')))
