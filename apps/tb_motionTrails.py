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

assetCommandName = 'motionPathRmbCommand'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('motionTrails'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='toggleMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.toggleMotionTrail()'],
                                     help=maya.stringTable['tbCommand.toggleMotionTrail']))
        self.addCommand(self.tb_hkey(name='createCameraRelativeMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.createCameraRelativeMotionTrail()'],
                                     help=maya.stringTable['tbCommand.createCameraRelativeMotionTrail']))
        self.addCommand(self.tb_hkey(name='toggleMotionTrailCameraRelative',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.toggleMotionTrailCameraRelative()'],
                                     help=maya.stringTable['tbCommand.toggleMotionTrailCameraRelative']))
        self.addCommand(self.tb_hkey(name='createMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.createMotionTrail()'],
                                     help=maya.stringTable['tbCommand.createMotionTrail']))
        self.addCommand(self.tb_hkey(name='removeMotionTrail',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.removeMotionTrail()'],
                                     help=maya.stringTable['tbCommand.removeMotionTrail']))
        self.addCommand(self.tb_hkey(name='motionPathSelected',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.motionPathSelected()'],
                                     help=maya.stringTable['tbCommand.motionPathSelected']))
        self.addCommand(self.tb_hkey(name='offlineMotionTrailSelected',
                                     annotation='',
                                     category=self.category, command=['MotionTrails.offlineMotionTrailSelected()'],
                                     help=maya.stringTable['tbCommand.motionPathSelected']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for offline motion trails',
                                     category=self.category, command=['MotionTrails.assetRmbCommand()']))
        return self.commandList

    def assignHotkeys(self):
        return


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
    motionControlSizeOption = 'tbMotionControlSize'
    motionTrailNodes = ['motionTrailShape', 'motionTrail1Handle', 'motionTrail']
    mainCurveAttr = 'mainCurve'
    assetCommandName = 'motionPathRmbCommand'
    assetTitleLabel = 'MotionTrails'

    ignoredAttributes = ['points', 'boundingBox', 'drawOverride', 'frames', 'boundingBoxMax']
    assetName = 'offlineMotionTrail'

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
        fadeLayout = QVBoxLayout()
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
        widgets = [trailFadeFramesWidget,
                   trailPreFramesWidget,
                   trailPostFramesWidget,
                   trailThicknessWidget,
                   trailframeMarkerSizesWidget,
                   showTicksOptionWidget]
        for wd in widgets:
            wd.setFixedWidth(150)
        self.layout.addWidget(infoText)

        self.layout.addLayout(fadeLayout)
        # self.layout.addLayout(markerLayout)
        fadeLayout.addWidget(trailFadeFramesWidget)
        fadeLayout.addWidget(trailPreFramesWidget)
        fadeLayout.addWidget(trailPostFramesWidget)
        fadeLayout.addWidget(trailThicknessWidget)
        fadeLayout.addWidget(trailframeMarkerSizesWidget)
        fadeLayout.addWidget(showTicksOptionWidget)

        motionControlSizeWidget = intFieldWidget(optionVar=self.motionControlSizeOption,
                                                 defaultValue=0.5,
                                                 label='Motion path control size',
                                                 minimum=0.1, maximum=100, step=0.1)

        self.layout.addWidget(motionControlSizeWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def assetRmbCommand(self, *args):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = cmds.ls(sl=True)
        if not sel:
            cursorPos = QCursor.pos()
            screens = QApplication.screens()
            screen = None
            for s in screens:
                if s.availableGeometry().contains(QCursor.pos()):
                    screen = s
            screenGeo = screen.availableGeometry()
            sel = self.funcs.selectFromScreenApi(cursorPos.x(), cursorPos.y(), screenGeo.width(), screenGeo.height())

        if not sel:
            return True
        sel = [s.split('.')[0] for s in sel]
        allAssets = list(set([cmds.container(query=True, findContainer=s) for s in sel]))
        allControls = list()

        for a in allAssets:
            if not a:
                continue
            if not cmds.attributeQuery('control', node=a, exists=True):
                continue
            c = cmds.listConnections(a + '.control', source=True, destination=False)
            if not c:
                continue
            allControls.extend(c)

        sel = sel[0]
        asset = cmds.container(query=True, findContainer=sel)

        if cmds.attributeQuery('offlinePath', node=asset, exists=True):
            control = cmds.listConnections(sel + '.control')
            path = cmds.listConnections(sel + '.path')
            refNode = cmds.listConnections(sel + '.ref')

            cmds.menuItem(label=self.assetTitleLabel, enable=False, boldFont=True, image='container.svg')
            cmds.menuItem(divider=True)
            cmds.menuItem(label='Rebuild Path - replace old',
                          command=pm.Callback(self.rebuildOfflinePath, control, path=[path[0], refNode[0], sel]))
            cmds.menuItem(label='Rebuild Path - create new',
                          command=pm.Callback(self.rebuildOfflinePath, control))
            cmds.menuItem(divider=True)
            cmds.menuItem(label='Constrain Control to Path',
                          command=pm.Callback(self.constrainControlToPath, control, refNode[0]))
            cmds.menuItem(divider=True)
            cmds.menuItem(label='Remove Path - selected',
                          command=pm.Callback(self.removeSelectedOfflinePath, asset, [path[0], refNode[0], sel]))
            cmds.menuItem(label='Remove Path - all',
                          command=pm.Callback(self.removeAllOfflinePath, asset))
        elif cmds.attributeQuery('liveMotionPath', node=asset, exists=True):
            mainCurve = self.getAssetMainCurve(asset)
            allCurves = [self.getAssetMainCurve(a) for a in allAssets]
            try:
                lockState = pm.getAttr(mainCurve.getShape().lockLength)
            except:
                # print('fail')
                lockState = False
            # labelling
            fractionState = self.getMode(mainCurve)
            fractionImage = {True: 'unlockLength.png', False: 'lockLength.png'}[fractionState]
            mainLabel = {True: 'Keys slide', False: 'Keys locked'}[fractionState]
            fractionLabel = {True: 'Switch to keys fixed on curve', False: 'Switch to keys slide on curve'}[
                fractionState]

            cmds.menuItem(label='Select First CV', rp='W', command=pm.Callback(self.selectFirstCV, asset))
            cmds.menuItem(label='Select Last CV', rp='E', command=pm.Callback(self.selectLastCV, asset))
            cmds.menuItem(label='Edit CV', rp='N', command=pm.Callback(self.editCV, asset))

            cmds.menuItem(label='MotionPath : %s' % mainLabel, enable=False, boldFont=True, image='container.svg')
            cmds.menuItem(divider=True)

            lockImage = {True: 'unlockLength.png', False: 'lockLength.png'}[lockState]
            lockCommand = {True: self.unlockCurveLength, False: self.lockCurveLength}[lockState]
            lockLabel = {True: 'Unlock Curve Length', False: 'Lock Curve Length'}[lockState]

            cmds.menuItem(label=lockLabel, rp='SE', image=lockImage, command=pm.Callback(lockCommand, mainCurve))
            cmds.menuItem(label='Toggle Markers', rp='SW', image='',
                          command=pm.Callback(self.toggleMarkers, mainCurve + '.showMarkers'))

            cmds.menuItem(label=fractionLabel, image='', command=pm.Callback(self.toggleMode, mainCurve))
            cmds.menuItem(divider=True)
            cmds.menuItem(label='Resample curve', image='', command=str(), enable=False)
            cmds.menuItem(label='Bake selected to layer', image='',
                          command=pm.Callback(self.bakeSelectedCommand, allAssets, allControls, False))
            cmds.menuItem(label='Bake selected to layer and delete curve', image='',
                          command=pm.Callback(self.bakeSelectedCommand, allAssets, allControls, True))
            # cmds.menuItem(label='Bake all to layer', image='', command=pm.Callback(self.bakeSelectedCommand, asset, allControls))
            cmds.menuItem(label='Rebuild curve', image='',
                          command=pm.Callback(self.rebuildMotionPath, allControls, allCurves))
            cmds.menuItem(label='Delete', image='', command=pm.Callback(self.deleteControlsCommand, allAssets, sel))

            '''
            make asset menu for offline trail
            constrain control to cached curve
            rebake control to cached curve
            redraw control, replace/new
            add transparency keys to match fade frames
            add options for colours, trail
            '''

    def bakeSelectedCommand(self, asset, sel, deleteAll):
        pm.select(sel, replace=True)
        mel.eval("simpleBakeToOverride")
        if deleteAll:
            pm.delete(asset)

    def bakeAllCommand(self, asset, sel):
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        pm.delete(asset)

    def createInfoNode(self):
        if not cmds.objExists('motionTrailInfo'):
            cmds.createNode("network", name='motionTrailInfo')
            self.funcs.getNotesAttr('motionTrailInfo')
            data = '''{}'''
            jsonObjectInfo = json.loads(data)
            jsonObjectInfo['camera'] = dict()
            jsonObjectInfo['target'] = dict()
            jsonObjectInfo['motionTrail'] = dict()
            jsonObjectInfo['motionTrailShape'] = dict()
            output = json.dumps(jsonObjectInfo, indent=4, separators=(',', ': '))
            cmds.setAttr('motionTrailInfo.notes', output, type='string')

    def getMotionTrailInfo(self):
        self.createInfoNode()
        allMotionTrails = self.getAllMotionTrails()
        jsonObjectInfo = self.readFromScene()

        for m in allMotionTrails:
            shape = self.getMotionTrailShape(m)[0]

            jsonObjectInfo['camera'][m] = self.getMotionTrailCamera(m)
            jsonObjectInfo['target'][m] = self.getNodeFromMotionTrail(m)[0]
            jsonObjectInfo['motionTrail'][m] = {x: self.readAttr(m, x) for x in self.getAttributes(m)}
            jsonObjectInfo['motionTrailShape'][m] = {x: self.readAttr(shape, x) for x in self.getAttributes(shape)}

        output = json.dumps(jsonObjectInfo, indent=4, separators=(',', ': '))
        cmds.setAttr('motionTrailInfo.notes', output, type='string')

    def readFromScene(self):
        self.createInfoNode()
        jsonData = self.funcs.getNotesAttr('motionTrailInfo')
        jsonObjectInfo = json.loads(jsonData)
        for key, value in jsonObjectInfo["target"].items():
            if not cmds.objExists(value):
                jsonObjectInfo["target"].pop(key)
                jsonObjectInfo["camera"].pop(key)
                jsonObjectInfo["motionTrail"].pop(key)
                jsonObjectInfo["motionTrailShape"].pop(key)
        return jsonObjectInfo

    def createFromSceneInfo(self, key=None):
        data = self.readFromScene()
        if not data: return
        if key:
            self.createFromData(data, key)
            return
        for key in data['motionTrail'].keys():
            self.createFromData(data, key)

    def createFromData(self, data, key):
        if not cmds.objExists(key):
            trail = self.createMotionTrail(sel=data['target'][key], camera=data['camera'][key])
            if not trail:
                return
            for attr, value in data['motionTrail'][key].items():
                if not pm.getAttr(trail[0][1] + '.' + attr, keyable=True):
                    continue
                if isinstance(value, list):
                    pm.setAttr(trail[0][1] + '.' + attr, *value)
                else:
                    pm.setAttr(trail[0][1] + '.' + attr, value)

    def getAttributes(self, node):
        allAttrs = cmds.listAttr(node)
        allAttrs = [a.split('.')[-1] for a in allAttrs if self.isValidAttribute(node, a)]
        return allAttrs

    def readAttr(self, node, attr):
        try:
            return cmds.getAttr(node + '.' + attr)
        except:
            pass

    def isValidAttribute(self, node, attribute):
        if ('.') in str(attribute):
            return False
        if str(attribute) in self.ignoredAttributes: return False
        if cmds.attributeQuery(attribute.split('.')[-1], node=node, multi=True): return False
        if cmds.attributeQuery(attribute.split('.')[-1], node=node, message=True): return False

        return True

    def toggleMotionTrail(self):
        """
        toggling off will delete all trails, save trail to scene before deletion
        :return:
        """
        sel = cmds.ls(sl=True)
        disable = True
        self.getMotionTrailInfo()
        data = self.readFromScene()

        if not sel:
            allMotionTrails = data['motionTrail'].keys()
            if not allMotionTrails:
                return
        else:
            for s in sel:
                if self.isMotionTrail(s):
                    continue
                if not self.hasMotionTrail(s):
                    self.createMotionTrail([s])
                    disable = False
            if not disable:
                return
            allMotionTrails = self.getAllMotionTrailsFromSelection(sel=sel)
        if not allMotionTrails:
            return

        if all([cmds.objExists(m) for m in allMotionTrails]):
            disable = True
        else:
            disable = False

        for motionTrail in allMotionTrails:
            if disable:
                motionTrailShape = self.getMotionTrailShape(motionTrail)
                # self.disableMotionTrail(motionTrail, motionTrailShape[0])
                pm.delete(motionTrail, motionTrailShape[0])
            else:
                self.createFromSceneInfo(key=motionTrail)
                # self.getMotionTrailInfo()

    def getCurrentCamera(self):
        view = omUI.M3dView.active3dView()
        cam = om.MDagPath()
        view.getCamera(cam)
        camPath = cam.partialPathName()

        return camPath

    def toggleMotionTrailCameraRelative(self):
        sel = cmds.ls(sl=True)
        trails = None
        if not sel:
            trails = self.findAllMotionTrails()

            sel = [self.getNodeFromMotionTrail(t) for t in trails]
            sel = [item for sublist in sel for item in sublist if item]
        if not sel:
            return
        if not trails:
            trails = self.getAllMotionTrailsFromSelection(sel)
            sel = [self.getNodeFromMotionTrail(t) for t in trails]
            sel = [item for sublist in sel for item in sublist if item]
        camera = {True: None, False: self.getCurrentCamera()}[self.isCameraRelative(trails)]

        self.removeMotionTrail(sel)
        self.createMotionTrail(sel=sel, camera=camera)

    def createCameraRelativeMotionTrail(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.createMotionTrail(sel=sel, camera=self.getCurrentCamera())

    def createMotionTrail(self, sel=None, camera=None):
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return
        if not isinstance(sel, list):
            sel = [sel]
        with self.funcs.keepSelection():
            trials = []
            for s in sel:
                if self.hasMotionTrail(s):
                    continue
                cmds.select(s, replace=True)
                moTrail = cmds.snapshot(name=s + '_motionTrail',
                                        motionTrail=True,
                                        increment=1,
                                        startTime=self.funcs.getTimelineMin(),
                                        endTime=self.funcs.getTimelineMax())
                cmds.setAttr(moTrail[0] + '.trailThickness', pm.optionVar.get(self.trailThicknessOption, 1))
                cmds.setAttr(moTrail[0] + '.fadeInoutFrames', pm.optionVar.get(self.trailFadeFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.preFrame', pm.optionVar.get(self.trailPreFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.postFrame', pm.optionVar.get(self.trailPostFramesOption, 0))
                cmds.setAttr(moTrail[0] + '.frameMarkerSize', pm.optionVar.get(self.trailframeMarkerSizesOption, 1))
                cmds.setAttr(moTrail[0] + '.showFrameMarkers', pm.optionVar.get(self.showframeMarkerOption, 0))

                trials.append(moTrail)
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
        return trials

    def isMotionTrail(self, s):
        childNodes = cmds.listRelatives(s, children=True)
        if not childNodes:
            return False
        return any([cmds.nodeType(c) == 'motionTrailShape' for c in childNodes])

    def hasMotionTrail(self, s):
        if not cmds.objExists(s):
            return False
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

    def isCameraRelative(self, sel):
        return any([cmds.attributeQuery('camera', node=s, exists=True) for s in sel])

    def getMotionTrailCamera(self, m):
        if not cmds.attributeQuery('camera', node=m, exists=True):
            return None
        conns = cmds.listConnections(m + '.camera', source=True,
                                     destination=False,
                                     plugs=False)
        if not conns:
            return None
        return conns[0]

    def findAllMotionTrails(self):
        return cmds.ls(type='motionTrail')

    def disableMotionTrail(self, motionTrail, trialShape):
        cmds.setAttr("{0}.nodeState".format(motionTrail), 2)
        cmds.setAttr("{0}.visibility".format(trialShape), False)

    def enableMotionTrail(self, motionTrail, trialShape):
        cmds.setAttr("{0}.nodeState".format(motionTrail), 0)
        cmds.setAttr("{0}.visibility".format(trialShape), True)
        if cmds.attributeQuery('camera', node=motionTrail, exists=True):
            pass

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
            for m in messageConnection:
                childNodes = cmds.listRelatives(m, children=True)
                if childNodes:
                    for c in childNodes:
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
        conns = cmds.listConnections(node,
                                     source=True,
                                     destination=False,
                                     plugs=False,
                                     type='transform'
                                     )
        if not conns:
            return list()
        return list(set(conns))

    def rebuildMotionPath(self, sel=list(), existingCurves=list()):
        self.motionPathSelected(sel=sel)
        cmds.delete([str(x) for x in existingCurves])

    def motionPathSelected(self, sel=list()):
        # TODO - undo chunk
        # TODO - add asset, menu, bake functions
        # asset
        # toggle fraction mode boolean on temp control

        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return

        startTime = self.funcs.getTimelineMin()
        endTime = self.funcs.getTimelineMax()
        isCroppped = False

        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            isCroppped = True

        tempNodes = dict()
        tempConstraints = dict()
        motionPaths = list()

        cmds.undoInfo(openChunk=True, chunkName="motionPathSelected")

        for s in sel:
            # create an asset if it doesn't exist
            asset = s + '_' + 'MotionPath'
            if not cmds.objExists(asset):
                self.createAsset(asset, imageName=None)
                cmds.addAttr(asset, ln="liveMotionPath", at='bool')
                cmds.addAttr(asset, ln="control", at='message')
                cmds.addAttr(asset, ln=self.mainCurveAttr, at='message')
                cmds.connectAttr(s + '.message', asset + '.control')

            tmp = str(self.funcs.tempControl(name=s, suffix='refMotion', drawType='cross',
                                             scale=pm.optionVar.get(self.motionControlSizeOption, 0.5)))
            cmds.container(s + '_' + 'MotionPath', edit=True, addNode=tmp)

            cnst = cmds.pointConstraint(s, tmp)
            tempNodes[s] = tmp
            tempConstraints[s] = cnst

        cmds.bakeResults(list(tempNodes.values()),
                         time=(startTime, endTime),
                         simulation=False,
                         bakeOnOverrideLayer=False,
                         sampleBy=1)   
        pm.delete(list(tempConstraints.values()))

        resultLayer = cmds.animLayer('motionPath', override=True)
        for s in sel:
            keyValues = cmds.keyframe(tempNodes[s],
                                      at=('translateX', 'translateY', 'translateZ'),
                                      q=True,
                                      valueChange=True)

            offset = int(len(keyValues) / 3)
            curveInfo = list()
            for i in range(0, offset):
                curveInfo.append([keyValues[i], keyValues[i + offset], keyValues[i + offset + offset]])
            divisions = int(endTime - startTime)
            curve = cmds.curve(name=s + '_path', worldSpace=True, p=curveInfo)
            cmds.addAttr(curve, ln="showMarkers", at='bool', dv=True)
            cmds.setAttr(curve + ".showMarkers", edit=True, keyable=True)
            cmds.addAttr(curve, ln='motionPath', at='message')

            resampledCurve = cmds.rebuildCurve(curve,
                                               ch=False,
                                               replaceOriginal=True,
                                               rebuildType=0,
                                               end=True,
                                               keepRange=False,
                                               keepControlPoints=True,
                                               keepEndPoints=True,
                                               keepTangents=False,
                                               spans=divisions,
                                               degree=3,
                                               tolerance=0.01)[0]

            cmds.select(tempNodes[s], replace=True)
            cmds.cutKey()
            cmds.select(curve, add=True)

            motionPath = cmds.pathAnimation(fractionMode=False,
                                            follow=False,
                                            startTimeU=startTime,
                                            endTimeU=endTime)

            motionPaths.append(motionPath)
            cmds.connectAttr(motionPath + '.message', curve + '.motionPath')
            pCurve = pm.PyNode(curve)
            cmds.container(s + '_' + 'MotionPath', edit=True, addNode=curve)
            cmds.connectAttr(curve + '.message', s + '_' + 'MotionPath' + '.' + self.mainCurveAttr, force=True)
            maxValue = len(curveInfo)
            lastParam = -1
            nearestPointOnCurve = cmds.createNode('nearestPointOnCurve')
            cmds.connectAttr(curve + '.worldSpace', nearestPointOnCurve + '.inputCurve')

            for index in range(int(endTime - startTime) + 1):
                cmds.setAttr(nearestPointOnCurve + '.inPosition', curveInfo[index][0], curveInfo[index][1],
                             curveInfo[index][2])
                uParam = cmds.getAttr(nearestPointOnCurve + '.parameter')

                cmds.setKeyframe(motionPath + '.u', value=uParam, time=index + int(startTime))
            self.hidePositionMarkers(curve, s + '_' + 'MotionPath', "showMarkers")

            cmds.select(tempNodes[s], s, replace=True)
            pm.parentConstraint(layer=resultLayer, skipRotate=('x', 'y', 'z'), weight=1)
            cmds.setAttr(motionPath + '.fractionMode', 1)
            cmds.delete(nearestPointOnCurve)

        # resultLayer
        if isCroppped:
            timeWeightDict = {startTime - 1: 0,
                              startTime: 1,
                              endTime: 1, endTime + 1: 0}
            for time, value in timeWeightDict.items():
                cmds.setKeyframe('{0}.weight'.format(resultLayer), time=(time,), value=value)
                cmds.keyTangent('{0}.weight'.format(resultLayer), time=(time,), inTangentType='flat',
                                outTangentType='flat')

        cmds.undoInfo(closeChunk=True)

    def offlineMotionTrailSelected(self, sel=list(), cameraSpace=False):
        """
        Bakes anim to a node, then makes a motion trail object. Use a standard maya motion trail
        Screen space should bake temp control to camera
        Make option to re attach original object
        :return:
        """
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return

        seek = 0.5
        trailPre = pm.optionVar.get(self.trailFadeFramesOption, 5)
        trailPost = pm.optionVar.get(self.trailFadeFramesOption, 5)
        trailScale = 0.5
        markerScale = 0.5
        keyScale = 0.5
        startTime = self.funcs.getTimelineMin()
        endTime = self.funcs.getTimelineMax()
        isCroppped = False

        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            isCroppped = True

        tempNodes = dict()
        curveParents = dict()
        tempConstraints = dict()
        motionPaths = list()

        cmds.undoInfo(openChunk=True, chunkName="motionPathSelected")
        nodeDict = dict()
        assetDict = dict()
        curveDict = dict()
        brushList = list()

        baseColour = [0, 0, 0]
        preTrailColour = [1, 0.3, 0]
        postTrailColour = [0, 0, 1]
        keyColour = [1, 0, 0]
        currentColour = [0, 1, 0]
        knotRadius = 0.101

        for s in sel:
            # create an asset if it doesn't exist
            asset = s + '_' + self.assetName
            if not cmds.objExists(asset):
                self.createAsset(asset, imageName=None)
                cmds.addAttr(asset, ln="offlinePath", at='bool')
                cmds.addAttr(asset, ln="pathWidth", at='double', dv=trailScale)
                cmds.setAttr(asset + ".pathWidth", edit=True, keyable=True)
                cmds.addAttr(asset, ln="keySize", at='double', dv=trailScale)
                cmds.setAttr(asset + ".keySize", edit=True, keyable=True)
                cmds.addAttr(asset, ln="frameMarkerSize", at='double', dv=trailScale)
                cmds.setAttr(asset + ".frameMarkerSize", edit=True, keyable=True)

            tmp = str(self.funcs.tempNull(name=s, suffix='Motion'))
            curveParent = str(self.funcs.tempNull(name=s, suffix='Crv'))
            cmds.addAttr(curveParent, ln="start", at='float')
            cmds.addAttr(curveParent, ln="end", at='float')
            cmds.addAttr(curveParent, ln="cameraSpace", at='message')
            cmds.addAttr(tmp, ln="control", at='message')
            cmds.addAttr(curveParent, ln="control", at='message')
            cmds.addAttr(curveParent, ln="path", at='message')
            cmds.addAttr(curveParent, ln="ref", at='message')

            cmds.connectAttr(s + '.message', tmp + '.control')
            cmds.connectAttr(tmp + '.message', curveParent + '.ref')
            cmds.connectAttr(s + '.message', curveParent + '.control')

            cmds.setAttr(curveParent + ".start", startTime)
            cmds.setAttr(curveParent + ".start", endTime)

            pm.container(asset, edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=[tmp, curveParent])
            cnst = cmds.pointConstraint(s, tmp)
            curveParents[s] = curveParent
            tempNodes[s] = tmp
            tempConstraints[s] = cnst

            nodeDict[s] = tmp
            assetDict[s] = asset

        cmds.bakeResults(list(tempNodes.values()),
                         time=(startTime, endTime),
                         simulation=False,
                         bakeOnOverrideLayer=False,
                         sampleBy=1)
        pm.delete(list(tempConstraints.values()))

        for s in sel:
            keyValues = cmds.keyframe(tempNodes[s],
                                      at=('translateX', 'translateY', 'translateZ'),
                                      q=True,
                                      valueChange=True)

            offset = int(len(keyValues) / 3)
            curveInfo = list()
            for i in range(0, offset):
                curveInfo.append([keyValues[i], keyValues[i + offset], keyValues[i + offset + offset]])
            divisions = int(endTime - startTime)
            curve = cmds.curve(name=s + '_path', worldSpace=True, p=curveInfo)

            resampledCurve = cmds.rebuildCurve(curve,
                                               ch=False,
                                               replaceOriginal=True,
                                               rebuildType=0,
                                               end=True,
                                               keepRange=False,
                                               keepControlPoints=True,
                                               keepEndPoints=True,
                                               keepTangents=False,
                                               spans=divisions,
                                               degree=1,
                                               tolerance=0.01)[0]
            cmds.connectAttr(resampledCurve + '.message', curveParents[s] + '.path')

            delList = list()

            for index, k in enumerate(curveInfo):
                frameMarker = cmds.circle(constructionHistory=False, radius=knotRadius, sections=4)[0]
                keyStroke = self.strokeCurve(frameMarker, colour=[0.66, 0.22, 0.55],
                                             width=0.2857142857142857 * trailScale)
                cmds.setAttr(frameMarker + '.translate', k[0], k[1], k[2])
                cmds.delete(
                    cmds.tangentConstraint(resampledCurve, frameMarker, aimVector=(0, 0, 1), worldUpType='scene'))
                strokeShape = cmds.listRelatives(keyStroke, shapes=True)[0]
                connections = cmds.listConnections(strokeShape + '.pathCurve[0].curve', source=True, destination=False,
                                                   plugs=True)
                cmds.disconnectAttr(frameMarker + '.worldSpace[0]', strokeShape + '.pathCurve[0].curve')
                brush = cmds.listConnections(strokeShape + '.brush', destination=False)[0]

                cmds.setAttr(brush + '.color1R', 0)
                cmds.setAttr(brush + '.color1G', 0)
                cmds.setAttr(brush + '.color1B', 0)
                # for t in int(endTime-startTime+1):
                cmds.setKeyframe(brush, attribute='color1G', value=0,
                                 time=(startTime + index - 1, startTime + index + 1))
                cmds.setKeyframe(brush, attribute='color1G', value=1, time=(startTime + index,))

                if cmds.keyframe(s, time=((index + startTime - seek), (index + startTime + seek)), query=True):
                    cmds.setKeyframe(brush, attribute='color1R', value=1, time=(startTime + index,))
                    cmds.connectAttr(assetDict[s] + '.keySize', brush + '.globalScale')

                else:
                    cmds.connectAttr(assetDict[s] + '.frameMarkerSize', brush + '.globalScale')
                    cmds.setKeyframe(brush, attribute='color1R', value=0,
                                     time=(startTime + index - trailPre,))
                    cmds.setKeyframe(brush, attribute='color1R', value=1,
                                     time=(startTime + index - 1))
                    cmds.setKeyframe(brush, attribute='color1B', value=0,
                                     time=(startTime + index + trailPost))
                    cmds.setKeyframe(brush, attribute='color1B', value=1,
                                     time=(startTime + index + 1))
                    cmds.setKeyframe(brush, attribute='color1B', value=0, time=(startTime + index))
                    cmds.setKeyframe(brush, attribute='color1R', value=0, time=(startTime + index))

                delList.append(frameMarker)
                delList.append(keyStroke)

                cmds.parent(strokeShape, curveParents[s], relative=True, shape=True)
            cmds.delete(delList)
            # cmds.delete(keyStroke)
            cmds.select(tempNodes[s], replace=True)
            cmds.select(resampledCurve, replace=True)
            stroke = self.strokeCurve(resampledCurve, width=trailScale)
            strokeShape = cmds.listRelatives(stroke, shapes=True)[0]
            brush = cmds.listConnections(strokeShape + '.brush', destination=False)[0]
            cmds.connectAttr(assetDict[s] + '.pathWidth', brush + '.globalScale')
            cmds.disconnectAttr(resampledCurve + '.worldSpace[0]', strokeShape + '.pathCurve[0].curve')
            cmds.parent(strokeShape, curveParents[s], relative=True, shape=True)
            cmds.delete(stroke)
            pm.container(assetDict[s], edit=True,
                         includeHierarchyBelow=True,
                         force=True,
                         addNode=[resampledCurve, nodeDict[s]])
        cmds.select(sel, replace=True)
        """
        tempControls = self.allTools.tools['BakeTools'].bake_to_locator(sel=sel, constrain=False, orientOnly=False, select=False, skipMotionTrails=True)
        pm.select(tempControls)
        sel = cmds.ls(sl=True)
        camera = self.getCurrentCamera()
        if cameraSpace:
            print ('getCurrentCamera()', camera)
            self.createMotionTrail(sel=sel, camera=camera)
        else:
            self.createMotionTrail(sel=sel)

        """

    def strokeCurve(self, curve, colour=[0.075999, 0.075999, 0.539], width=1):
        '''
        Simply applies the paint effects brush to the curve with the settings we want.
        '''
        # cmds.select(curve, replace=True)
        cmds.AttachBrushToCurves(curve)
        stroke = cmds.ls(sl=True)[0]
        brush = cmds.listConnections(stroke + '.brush', destination=False)[0]
        brush = cmds.rename(brush, 'pathBrush_#')

        cmds.setAttr(stroke + '.overrideEnabled', 1)
        cmds.setAttr(stroke + '.overrideDisplayType', 2)

        cmds.setAttr(stroke + '.displayPercent', 92)
        cmds.setAttr(stroke + '.sampleDensity', 0.5)
        cmds.setAttr(stroke + '.inheritsTransform', 0)
        cmds.setAttr(stroke + '.translate', 0, 0, 0)
        cmds.setAttr(stroke + '.rotate', 0, 0, 0)
        cmds.setAttr(brush + '.screenspaceWidth', 1)
        cmds.setAttr(brush + '.distanceScaling', 0.2)
        cmds.setAttr(brush + '.minPixelWidth', 0.25)
        cmds.setAttr(brush + '.maxPixelWidth', 10)

        cmds.setAttr(brush + '.globalScale', width)
        cmds.setAttr(brush + '.color1', colour[0], colour[1], colour[2])

        return stroke

    def rebuildOfflinePath(self, control, path=None):
        # get the path camera space value
        cmds.delete(path)
        self.offlineMotionTrailSelected(sel=list(control), cameraSpace=False)

    def removeAllOfflinePath(self, asset):
        cmds.delete(str(asset))

    def removeSelectedOfflinePath(self, asset, nodes):
        cmds.delete(nodes)
        remainingNodes = cmds.container(asset, query=True, nodeList=True)
        if not remainingNodes:
            cmds.delete(asset)

    def constrainControlToPath(self, control, refNode):
        cmds.pointConstraint(refNode, control)

    def hidePositionMarkers(self, path, asset, attr=None):
        markers = pm.PyNode(path).getShape().listRelatives(type='positionMarker', allDescendents=True)
        for m in markers:
            if attr:
                cmds.connectAttr(path + '.' + attr, str(m) + '.visibility')
            else:
                m.visibility.set(False)
        '''
        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=markers)
        '''

    def nurbsSoftSelectionWeights(self):
        ''' create and return a list of the soft selection weights '''
        symmetryOn = cmds.symmetricModelling(q=True, symmetry=True)
        if symmetryOn:
            cmds.symmetricModelling(e=True, symmetry=False)

        selection = om.MSelectionList()
        softSelection = om.MRichSelection()
        om.MGlobal.getRichSelection(softSelection)
        softSelection.getSelection(selection)

        dagPath = om.MDagPath()
        selection.getDagPath(0, dagPath)
        component = om.MObject()
        nurbsIter = om.MItCurveCV(dagPath)
        pointCount = 0
        while not nurbsIter.isDone():
            pointCount += 1
            nurbsIter.next()

        weightArray = [0.0] * pointCount

        iter = om.MItSelectionList(selection, om.MFn.kCurveCVComponent)
        iter.getDagPath(dagPath, component)
        fnComp = om.MFnSingleIndexedComponent(component)
        if fnComp.hasWeights():
            for i in range(fnComp.elementCount()):
                element = fnComp.element(i)
                weight = fnComp.weight(i).influence()
                weightArray[element] = weight

        cmds.symmetricModelling(e=True, symmetry=symmetryOn)
        return weightArray

    def getAssetMainCurve(self, asset):
        # print('connections', pm.listConnections(asset + '.' + self.mainCurveAttr, source=True, destination=False))
        if not asset:
            return None
        return pm.listConnections(asset + '.' + self.mainCurveAttr, source=True, destination=False)[0]

    def lockCurveLength(self, curve):
        pm.select(curve, replace=True)
        mel.eval('LockCurveLength')

    def unlockCurveLength(self, curve):
        pm.select(curve, replace=True)
        mel.eval('UnlockCurveLength')

    def selectFirstCV(self, asset):
        mainCurve = pm.listConnections(asset + '.' + self.mainCurveAttr, source=True, destination=False)[0]
        pm.select(mainCurve, replace=True)
        mel.eval('selectCurveCV first')

    def selectLastCV(self, asset):
        mainCurve = pm.listConnections(asset + '.' + self.mainCurveAttr, source=True, destination=False)[0]
        pm.select(mainCurve, replace=True)
        mel.eval('selectCurveCV last')

    def editCV(self, asset):
        mainCurve = pm.listConnections(asset + '.' + self.mainCurveAttr, source=True, destination=False)[0]
        mel.eval('doMenuNURBComponentSelection("%s", "controlVertex")' % mainCurve)

    def toggleMarkers(self, attr):
        cmds.setAttr(attr, not cmds.getAttr(attr))

    def getMode(self, curve):
        motionPath = cmds.listConnections(curve + '.motionPath', source=True, destination=False)[0]
        return cmds.getAttr(motionPath + '.fractionMode')

    def toggleMode(self, curve):
        motionPath = cmds.listConnections(curve + '.motionPath', source=True, destination=False)[0]
        cmds.setAttr(motionPath + '.fractionMode', not cmds.getAttr(motionPath + '.fractionMode'))

    def rebuildCurve(self, curve, divisions):
        cmds.rebuildCurve(curve,
                          ch=False,
                          replaceOriginal=True,
                          rebuildType=0,
                          end=True,
                          keepRange=False,
                          keepControlPoints=True,
                          keepEndPoints=True,
                          keepTangents=False,
                          spans=divisions,
                          degree=1,
                          tolerance=0.01)[0]


"""
TODO 
make asset menu for offline trail 
constrain control to cached curve
rebake control to cached curve
redraw control, replace/new
add transparency keys to match fade frames
add options for colours, trail
"""
