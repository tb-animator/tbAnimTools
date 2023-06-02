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
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2
import pymel.core.datatypes as dt
import math
from Abstract import *
from tb_UI import *
import tb_helpStrings
import maya
import traceback

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

assetCommandName = 'meshPinControlCommand'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('TempControls'))
        self.addCommand(self.tb_hkey(name='createMeshPin',
                                     annotation='Merges all layers',
                                     category=self.category, command=['MeshPinTool.createMeshPin()'],
                                     help=maya.stringTable['tbCommand.createMeshPin']))

        self.setCategory(self.helpStrings.category.get('ignore'))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for temp controls',
                                     category=self.category, command=['MeshPinTool.assetRmbCommand()'],
                                     help='Do not assign to a hotkey'))

        return self.commandList

    def assignHotkeys(self):
        return


class MeshPinTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'MeshPinTool'
    hotkeyClass = hotkeys()
    funcs = functions()

    quickBakeSimOption = 'tbQuickBakeUseSim'

    quickBakeRemoveContainerOption = 'tbQuickBakeRemoveContainer'
    tbTempControlMotionTrailOption = 'tbTempControlMotionTrailOption'
    tbTempControlChannelOption = 'tbTempControlChannelOption'
    tbBakeSimObjectCountOption = 'tbBakeSimObjectCountOption'
    tbBakeLocatorSizeOption = 'tbBakeLocatorSize'
    tbBakeProximityPinSizeOption = 'tbBakeProximityPinSize'
    tbBakeWorldOffsetSizeOption = 'tbBakeWorldOffsetSize'
    tbMotionControlSizeOption = 'tbMotionControlSize'

    overrideLayerColour = 19
    additiveLayerColour = 18

    assetCommandName = 'tempControlCommand'

    assetName = 'meshPins'
    worldOffsetAssetName = 'WorldOffsetControls'
    constraintTargetAttr = 'constraintTarget'
    tempControlPairAttr = 'tempControlPair'

    def __new__(cls):
        if MeshPinTool.__instance is None:
            MeshPinTool.__instance = object.__new__(cls)

        MeshPinTool.__instance.val = cls.toolName
        return MeshPinTool.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(MeshPinTool, self).optionUI()
        proximityPinSizeWidget = intFieldWidget(optionVar=self.tbBakeProximityPinSizeOption,
                                         defaultValue=1.0,
                                         label='Proximity pin control size',
                                         minimum=0.1, maximum=100, step=0.1)
        proximityPinSizeWidget.changedSignal.connect(self.updatePreview)
        self.layout.addWidget(proximityPinSizeWidget)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    """
    Functions
    """

    def drawPreview(self):
        self.funcs.tempControl(name='temp',
                               suffix='Preview',
                               scale=pm.optionVar.get(self.tbBakeLocatorSizeOption, 1),
                               drawType='cross')

    def updatePreview(self, scale):
        if not cmds.objExists('temp_Preview'):
            self.drawPreview()

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = pm.ls(sl=True)
        asset = pm.container(query=True, findContainer=sel[0])

        # check asset message attribute

        cmds.menuItem(label='Mesh Pin Tools', enable=False, boldFont=True, image='container.svg')

    def createMeshPin(self, sel=list()):
        """
        Create a new transform relative to the selected verts for each selected vert
        Connect it to a proximity pin node and the build a constraint to a new temp control
        :param sel:
        :return:
        """
        if not sel:
            sel = cmds.ls(sl=True, fl=True)
        if not sel:
            return raiseError("Please select a vertex on your skinned mesh")

        polyMesh = cmds.listRelatives(cmds.ls(sel[0], o=True), p=True)

        if not polyMesh:
            return raiseError("selection needs to be a poly mesh")
        skinClusters = list()

        # look for skin clusters to disable and re-enable
        for s in sel:
            history = cmds.listHistory(s)
            if not history:
                continue
            for n in history:
                if cmds.nodeType(n) == 'skinCluster':
                    skinClusters.append(n)

        for c in skinClusters:
            try:
                cmds.setAttr('%s.envelope' % c, 0)
            except:
                cmds.warning('Unable to toggle skin cluster %s' % c)

        resultControls = list()

        # in theory all our skin clusters are now off, and back at the bind pose
        try:
            for s in sel:
                pos = cmds.xform(s, query=True, translation=True)
                inLoc = cmds.createNode('transform', name='s_%s' % 'pinInput')
                outLoc = self.funcs.tempControl(name=s, suffix='pinInput', drawType='orb',
                                                color=(0.136, 1.0, 0.016),
                                                scale=pm.optionVar.get(self.tbBakeProximityPinSizeOption, 1))
                resultControls.append(outLoc)
                cmds.xform(inLoc, translation=pos)
                cmds.select(polyMesh)

                existingPins = cmds.ls(type='proximityPin')

                newPin = cmds.ProximityPin()

                # had a hard time getting the proximity pin command to actually return anything, so hack away
                pins = [p for p in cmds.ls(type='proximityPin') if p not in existingPins]

                cmds.connectAttr(inLoc + '.worldMatrix', pins[0] + '.inputMatrix[0]')
                cmds.connectAttr(pins[0] + '.outputMatrix[0]', str(outLoc) + '.offsetParentMatrix')

                ps = pm.PyNode(s)
                ns = ps.namespace()
                if not cmds.objExists(ns + self.assetName):
                    self.createAsset(ns + self.assetName, imageName=None)
                asset = ns + self.assetName
                pm.container(asset, edit=True,
                             includeHierarchyBelow=True,
                             force=True,
                             addNode=[inLoc,outLoc])
        finally:
            for c in skinClusters:
                try:
                    cmds.setAttr('%s.envelope' % c, 1)
                except:
                    cmds.warning('Unable to toggle skin cluster %s' % c)

        return resultControls
