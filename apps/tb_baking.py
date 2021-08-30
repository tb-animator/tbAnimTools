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

assetCommandName = 'tempControlCommand'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('layers'))
        self.addCommand(self.tb_hkey(name='quickMergeAllLayers',
                                     annotation='Merges all layers',
                                     category=self.category, command=['BakeTools.quickMergeAllLayers()'],
                                     help=self.helpStrings.simpleBakeToOverride))
        self.addCommand(self.tb_hkey(name='quickMergeSelectionToNew',
                                     annotation='',
                                     category=self.category, command=['BakeTools.quickMergeSelectionToNew()'],
                                     help=self.helpStrings.quickMergeSelectionToNew))
        self.addCommand(self.tb_hkey(name='quickMergeSelectionToBase',
                                     annotation='',
                                     category=self.category, command=['BakeTools.quickMergeSelectionToBase()'],
                                     help=self.helpStrings.quickMergeSelectionToBase
                                     ))

        self.addCommand(self.tb_hkey(name='bakeConstraintToAdditive',
                                     annotation='',
                                     category=self.category, command=['BakeTools.bakeConstraintToAdditiveSelection()']
                                     ))
        self.addCommand(self.tb_hkey(name='additiveExtractSelection',
                                     annotation='',
                                     category=self.category, command=['BakeTools.additiveExtractSelection()']
                                     ))
        self.addCommand(self.tb_hkey(name='simpleBakeToOverride',
                                     annotation='',
                                     category=self.category, command=['BakeTools.bake_to_override()'],
                                     help=self.helpStrings.simpleBakeToOverride))
        self.addCommand(self.tb_hkey(name='simpleBakeToBase',
                                     annotation='',
                                     category=self.category, command=['BakeTools.simpleBake()'],
                                     help=self.helpStrings.simpleBakeToOverride))

        self.addCommand(self.tb_hkey(name='quickCreateAdditiveLayer',
                                     annotation='',
                                     category=self.category, command=['BakeTools.addAdditiveLayer()'],
                                     help=self.helpStrings.quickCreateAdditiveLayer))
        self.addCommand(self.tb_hkey(name='quickCreateOverrideLayer',
                                     annotation='',
                                     category=self.category, command=['BakeTools.addOverrideLayer()'],
                                     help=self.helpStrings.quickCreateOverrideLayer))
        self.addCommand(self.tb_hkey(name='counterAnimLayer',
                                     annotation='',
                                     category=self.category, command=['BakeTools.counterLayerAnimation()'],
                                     help=self.helpStrings.counterAnimLayer))
        self.setCategory(self.helpStrings.category.get('constraints'))
        self.addCommand(self.tb_hkey(name='bakeToLocator', annotation='',
                                     category=self.category,
                                     command=['BakeTools.bake_to_locator(constrain=True, orientOnly=False)'],
                                     help=self.helpStrings.bakeToLocator))
        self.addCommand(
            self.tb_hkey(name='bakeToLocatorRotation', annotation='constrain to object to locator - rotate only',
                         category=self.category,
                         command=['BakeTools.bake_to_locator(constrain=True, orientOnly=True)']))

        self.addCommand(self.tb_hkey(name='simpleConstraintOffset', annotation='constrain to objects with offset',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=True, postBake=False)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffset', annotation='constrain to objects with NO offset',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=False, postBake=False)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintOffsetPostBake',
                                     annotation='constrain to objects with offset - post baked',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=True, postBake=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffsetPostBake',
                                     annotation='constrain to objects with NO offset - post baked',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=False, postBake=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintOffsetPostBakeReverse',
                                     annotation='constrain to objects with offset - post baked, constraint reversed',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=True, postBake=True, postReverseConst=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffsetPostBakeReverse',
                                     annotation='constrain to objects with NO offset - post baked, constraint reversed',
                                     category=self.category, command=[
                'BakeTools.parentConst(constrainGroup=False, offset=False, postBake=True, postReverseConst=True)']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for temp controls',
                                     category=self.category, command=['BakeTools.assetRmbCommand()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class BakeTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'BakeTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    quickBakeSimOption = 'tbQuickBakeUseSim'
    quickBakeRemoveContainerOption = 'tbQuickBakeRemoveContainer'
    tempControlMotionTrailOption = 'tbTempControlMotionTrailOption'
    bakeSimObjectCountOption = 'tbBakeSimObjectCountOption'
    overrideLayerColour = 19
    additiveLayerColour = 18

    crossSizeOption = 'tbBakeLocatorSize'
    assetName = 'TempControls'
    constraintTargetAttr = 'constraintTarget'

    def __new__(cls):
        if BakeTools.__instance is None:
            BakeTools.__instance = object.__new__(cls)

        BakeTools.__instance.val = cls.toolName
        return BakeTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(BakeTools, self).optionUI()
        simOptionWidget = optionVarBoolWidget('Bake to locator uses Simulation ', self.quickBakeSimOption)
        containerOptionWidget = optionVarBoolWidget('Remove containers post bake     ',
                                                    self.quickBakeRemoveContainerOption)
        crossSizeWidget = intFieldWidget(optionVar=self.crossSizeOption,
                                         defaultValue=1.0,
                                         label='Baked locator control size',
                                         minimum=0.1, maximum=100, step=0.1)
        crossSizeWidget.changedSignal.connect(self.updatePreview)
        tempControlHeader = subHeader('Bake Simulation')
        tempControlInfo = infoLabel(['When baking many objects it is often faster to use simulation.',
                                     'Experiment to see where the threshold lies on your machine. Set the value below to automatically toggle bake sim when baking many objects'])

        bakeSimThresholdWidget = intFieldWidget(optionVar=self.bakeSimObjectCountOption,
                                                defaultValue=10,
                                                label='Bake Simulation when baking more than > objects',
                                                minimum=1, maximum=100, step=1)
        motionTrailHeader = subHeader('Motion Trails')
        motionTrailInfo = infoLabel(['Add motion trails to newly created temp controls.'])
        motionTrailWidget = optionVarBoolWidget('Motion Trail On Temp Controls',
                                                self.tempControlMotionTrailOption)

        self.layout.addWidget(simOptionWidget)
        self.layout.addWidget(containerOptionWidget)
        self.layout.addWidget(crossSizeWidget)
        self.layout.addWidget(tempControlHeader)
        self.layout.addWidget(tempControlInfo)
        self.layout.addWidget(bakeSimThresholdWidget)
        self.layout.addWidget(motionTrailHeader)
        self.layout.addWidget(motionTrailInfo)
        self.layout.addWidget(motionTrailWidget)
        self.layout.addStretch()
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
                               scale=pm.optionVar.get(self.crossSizeOption, 1),
                               drawType='cross')

    def updatePreview(self, scale):
        if not cmds.objExists('temp_Preview'):
            self.drawPreview()

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)

    def bake_to_override(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        with self.funcs.keepSelection():
            preContainers = set(pm.ls(type='container'))
            preBakeLayers = pm.ls(type='animLayer')
            keyRange = self.funcs.get_all_layer_key_times(sel)
            if not keyRange or keyRange[0] == None:
                keyRange = self.funcs.getTimelineRange()

            pm.bakeResults(sel,
                           time=(keyRange[0], keyRange[-1]),
                           simulation=False,
                           sampleBy=1,
                           oversamplingRate=1,
                           disableImplicitControl=True,
                           preserveOutsideKeys=False,
                           sparseAnimCurveBake=True,
                           removeBakedAttributeFromLayer=False,
                           removeBakedAnimFromLayer=False,
                           bakeOnOverrideLayer=True,
                           minimizeRotation=True,
                           controlPoints=False,
                           shape=False)
            postBakeLayer = [x for x in pm.ls(type='animLayer') if x not in preBakeLayers]
            for newAnimLayer in postBakeLayer:
                pm.setAttr(newAnimLayer + ".ghostColor", self.overrideLayerColour)
                pm.rename(newAnimLayer, 'OverrideBaked')

            self.removeContainersPostBake(preContainers)
        self.funcs.select_layer(postBakeLayer)

    def simpleBake(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        with self.funcs.keepSelection():
            keyRange = self.funcs.get_all_layer_key_times(sel)
            if not keyRange[0]:
                keyRange = self.funcs.getTimelineRange()
            pm.bakeResults(sel,
                           time=(keyRange[0], keyRange[-1]),
                           simulation=False,
                           sampleBy=1,
                           oversamplingRate=1,
                           disableImplicitControl=True,
                           preserveOutsideKeys=False,
                           sparseAnimCurveBake=True,
                           removeBakedAttributeFromLayer=False,
                           removeBakedAnimFromLayer=False,
                           bakeOnOverrideLayer=False,
                           minimizeRotation=True,
                           controlPoints=False,
                           shape=False)

    def removeContainersPostBake(self, preContainers):
        if pm.optionVar.get(self.quickBakeRemoveContainerOption, False):
            resultContainer = list(set(pm.ls(type='container')).difference(set(preContainers)))
            if not resultContainer:
                return
            pm.select(resultContainer, replace=True)
            mel.eval('SelectContainerContents')
            mel.eval('doRemoveFromContainer(1, {"container -e -includeShapes -includeTransform "})')
            pm.delete(resultContainer)

    def bake_to_locator(self, sel=list(), constrain=False, orientOnly=False, select=True):
        if not sel:
            sel = pm.ls(sl=True)
        locs = []
        constraints = []
        if sel:
            for s in sel:
                # loc = self.funcs.tempLocator(name=s, suffix='baked')
                ps = pm.PyNode(s)
                ns = ps.namespace()
                if not cmds.objExists(ns + self.assetName):
                    self.createAsset(ns + self.assetName, imageName=None)
                asset = ns + self.assetName
                loc = self.funcs.tempControl(name=s, suffix='baked', drawType='cross',
                                             scale=pm.optionVar.get(self.crossSizeOption, 1))
                pm.addAttr(loc, ln=self.constraintTargetAttr, at='message')
                pm.connectAttr(s + '.message', loc + '.' + self.constraintTargetAttr)
                const = pm.parentConstraint(s, loc)
                locs.append(loc)
                constraints.append(const)
                pm.container(asset, edit=True,
                             includeHierarchyBelow=True,
                             force=True,
                             addNode=loc)
        if locs:
            preContainers = set(pm.ls(type='container'))
            pm.bakeResults(locs,
                           simulation=pm.optionVar.get(self.quickBakeSimOption, False),
                           sampleBy=1,
                           oversamplingRate=1,
                           disableImplicitControl=True,
                           preserveOutsideKeys=False,
                           sparseAnimCurveBake=True,
                           removeBakedAttributeFromLayer=False,
                           removeBakedAnimFromLayer=False,
                           bakeOnOverrideLayer=False,
                           minimizeRotation=True,
                           controlPoints=False,
                           shape=False,
                           time=[pm.playbackOptions(query=True, minTime=True),
                                 pm.playbackOptions(query=True, maxTime=True)],
                           )
            self.removeContainersPostBake(preContainers)
            if constrain:
                pm.delete(constraints)
                for cnt, loc in zip(sel, locs):
                    skipT = self.funcs.getAvailableTranslates(cnt)
                    skipR = self.funcs.getAvailableRotates(cnt)
                    constraint = pm.parentConstraint(loc, cnt, skipTranslate={True: ('x', 'y', 'z'),
                                                                              False: [x.split('translate')[-1] for x in
                                                                                      skipT]}[
                        orientOnly],
                                                     skipRotate=[x.split('rotate')[-1] for x in skipR])
                    pm.container(asset, edit=True,
                                 includeHierarchyBelow=True,
                                 force=True,
                                 addNode=constraint)
        if pm.optionVar.get(self.tempControlMotionTrailOption, False):
            for l in locs:
                cmds.select(str(l), replace=True)
                mel.eval('createMotionTrail')
        if select:
            pm.select(locs, replace=True)
        return locs

    def createAsset(self, name, imageName=None):
        asset = cmds.container(name=name,
                               includeHierarchyBelow=False,
                               includeTransform=True,
                               )
        if imageName:
            pm.setAttr(asset + '.iconName', imageName, type="string")
        cmds.setAttr(asset + '.rmbCommand', assetCommandName, type='string')
        return asset

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = pm.ls(sl=True)
        asset = pm.container(query=True, findContainer=sel[0])

        # check asset message attribute

        cmds.menuItem(label='Bake Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Bake selected temp controls to layer',
                      command=pm.Callback(self.bakeSelectedCommand, asset, sel))
        cmds.menuItem(label='Bake all temp controls to layer', command=pm.Callback(self.bakeAllCommand, asset, sel))
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Delete selected temp controls',
                      command=pm.Callback(self.deleteSelectedControlsCommand, asset, sel))
        cmds.menuItem(label='Delete all temp controls', command=pm.Callback(self.deleteControlsCommand, asset, sel))
        cmds.menuItem(divider=True)

    def createAsset(self, name, imageName=None):
        asset = cmds.container(name=name,
                               includeHierarchyBelow=False,
                               includeTransform=True,
                               )
        if imageName:
            pm.setAttr(asset + '.iconName', imageName, type="string")
        cmds.setAttr(asset + '.rmbCommand', assetCommandName, type='string')
        return asset

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = pm.ls(sl=True)
        asset = pm.container(query=True, findContainer=sel[0])

        # check asset message attribute
        # print ("asset", asset, sel)

        cmds.menuItem(label='Bake Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Bake selected temp controls to layer',
                      command=pm.Callback(self.bakeSelectedCommand, asset, sel))
        cmds.menuItem(label='Bake all temp controls to layer', command=pm.Callback(self.bakeAllCommand, asset, sel))
        # cmds.menuItem(label='Bake out to layer', command=pm.Callback(self.bakeOutCommand, asset))
        cmds.menuItem(label='Delete all temp controls', command=pm.Callback(self.deleteControlsCommand, asset, sel))
        cmds.menuItem(divider=True)

    def get_available_attrs(self, node):
        '''
        returns 2 lists of attrs that are not available for constraining
        '''
        attrs = ['X', 'Y', 'Z']

        lockedTranslates = []
        lockedRotates = []
        for attr in attrs:
            if not pm.getAttr(node + '.' + 'translate' + attr, settable=True):
                lockedTranslates.append(attr.lower())
            if not pm.getAttr(node + '.' + 'rotate' + attr, settable=True):
                lockedRotates.append(attr.lower())

        return lockedTranslates, lockedRotates

    def bakeSelectedCommand(self, asset, sel):
        tempControls = [x for x in sel if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        targets = [cmds.listConnections(s + '.' + self.constraintTargetAttr) for s in tempControls]
        filteredTargets = [item for sublist in targets for item in sublist if item]
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        pm.delete(tempControls)

    def bakeAllCommand(self, asset, sel):
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        pm.delete(asset)

    def deleteSelectedControlsCommand(self, asset, sel):
        pm.delete(sel)

    def deleteControlsCommand(self, asset, sel):
        pm.delete(asset)

    def bakeSelectedCommand(self, asset, sel):
        # print ('rebakeCommand', asset, sel)
        targets = [cmds.listConnections(s + '.' + self.constraintTargetAttr) for s in sel]
        filteredTargets = [item for sublist in targets for item in sublist if item]
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")

    def bakeAllCommand(self, asset, sel):
        # print ('bakeAllCommand', asset, sel)
        nodes = pm.ls(pm.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if pm.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [pm.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        # print ('filteredTargets', filteredTargets)
        pm.select(filteredTargets, replace=True)
        mel.eval("simpleBakeToOverride")
        pm.delete(asset)

    def deleteControlsCommand(self, asset, sel):
        pm.delete(asset)

    def parentConst(self, constrainGroup=False, offset=True, postBake=False, postReverseConst=False):
        drivers = pm.ls(sl=True)
        if not len(drivers) > 1:
            return pm.warning('not enough objects selected to constrain, please select at least 2')
        target = drivers.pop(-1)

        if constrainGroup:
            if not target.getParent():
                pm.warning("trying to constrain object's parent, but it is parented to the world")
            else:
                target = target.getParent()

        pm.parentConstraint(drivers, target,
                            skipTranslate=self.funcs.getAvailableTranslates(target),
                            skipRotate=self.funcs.getAvailableRotates(target),
                            maintainOffset=offset)
        if postBake:
            self.quickBake(target)
            if postReverseConst:
                if len(drivers) != 1:
                    return pm.warning('Can only post reverse constraint if 2 objects are used')
                else:
                    pm.parentConstraint(target, drivers[0],
                                        skipTranslate=self.funcs.getAvailableTranslates(drivers[0]),
                                        skipRotate=self.funcs.getAvailableRotates(drivers[0]),
                                        maintainOffset=True)

    def clearBlendAttrs(self, node):
        for attr in pm.listAttr(node):
            if 'blendParent' in str(attr):
                pm.deleteAttr(node, at=attr)

    def quickBake(self, node, startTime=None, endTime=None, deleteConstraints=True):
        if not startTime:
            startTime = pm.playbackOptions(query=True, minTime=True)
        if not endTime:
            endTime = pm.playbackOptions(query=True, maxTime=True)
        pm.bakeResults(node,
                       simulation=False,
                       disableImplicitControl=False,
                       time=[startTime,
                             endTime],
                       sampleBy=1)
        if deleteConstraints:
            pm.delete(node.listRelatives(type='constraint'))
            self.clearBlendAttrs(node)

    def addOverrideLayer(self):
        self.add_layer(mode=True)

    def addAdditiveLayer(self):
        self.add_layer(mode=False)

    def add_layer(self, mode=False):
        suffix = {True: ['Override', self.overrideLayerColour], False: ['Additive', self.additiveLayerColour]}

        newAnimLayer = pm.animLayer(suffix[mode][0],
                                    override=mode,
                                    excludeScale=True,
                                    # excludeEnum=True,
                                    addSelectedObjects=True,
                                    passthrough=False,
                                    lock=False)
        newAnimLayer.ghostColor.set(suffix[mode][1])
        self.deselect_layers()
        newAnimLayer.selected.set(True)
        newAnimLayer.preferred.set(True)
        newAnimLayer.scaleAccumulationMode.set(0)
        if not self.funcs.isTimelineHighlighted():
            return
        if not mode:
            return

        timeRange = self.funcs.getTimelineHighlightedRange()
        cmds.setKeyframe(animLayer=newAnimLayer,
                         time=((timeRange[0]), timeRange[1]),
                         respectKeyable=True,
                         hierarchy=False,
                         breakdown=False,
                         dirtyDG=True,
                         controlPoints=False,
                         shape=False,
                         identity=True)
        # in case there's something to do automatically to the objects?
        sel = pm.ls(selection=True)
        if not sel:
            return

    def deselect_layers(self):
        for layers in pm.ls(type='animLayer'):
            layers.selected.set(False)

    def counterLayerAnimation(self):
        """
        Counters the animation of the last selected object in the layer, outputs the countered
        animation into a new layer under the other.
        :return:
        """
        sel = pm.ls(sl=True)
        if not sel:
            return cmds.warning('nothing selected')
        if len(sel) == 1:
            return cmds.warning('please select at least one controller to counter, followed by the driver')
        animLayer = self.funcs.get_selected_layers()
        if not animLayer:
            return cmds.warning('no anim layer selected')
        driver = sel[-1]
        targets = sel[:-1]

        affectedLayers = cmds.animLayer([driver], q=True, affectedLayers=True)
        if animLayer[0] not in affectedLayers:
            return cmds.warning('driver control is not found in the selected layer')
        keyRange = self.funcs.get_all_key_times(str(driver), selected=False)
        if not keyRange:
            return cmds.warning('driver control does not appear to have any keys in the selected layer')
        resultLayer = pm.animLayer(animLayer[0] + '_Counter')
        pm.setAttr(resultLayer + '.scaleAccumulationMode', 0)
        pm.animLayer(resultLayer, edit=True, override=True, parent=animLayer[0])
        allAttrs = list()
        for target in targets:
            translates = self.funcs.getAvailableTranslates(target)
            rotates = self.funcs.getAvailableRotates(target)
            attrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
            layerAttrs = [target + '.' + x for x in attrs if x not in translates + rotates]
            pm.animLayer(resultLayer, edit=True, attribute=layerAttrs)
            allAttrs.extend(layerAttrs)

        # mut the layer to get the underlying animtion
        pm.animLayer(animLayer[0], edit=True, mute=True)
        # bake the controls to locators
        locators = self.bake_to_locator(sel=targets, constrain=True, select=False)
        # restore the animation layer
        pm.animLayer(animLayer[0], edit=True, mute=False)

        # bake out the result values

        preContainers = set(pm.ls(type='container'))
        pm.bakeResults(allAttrs,
                       time=(keyRange[0], keyRange[-1]),
                       destinationLayer=resultLayer,
                       simulation=False,
                       sampleBy=1,
                       oversamplingRate=1,
                       disableImplicitControl=True,
                       preserveOutsideKeys=False,
                       sparseAnimCurveBake=True,
                       removeBakedAttributeFromLayer=False,
                       removeBakedAnimFromLayer=False,
                       bakeOnOverrideLayer=True,
                       minimizeRotation=True,
                       controlPoints=False,
                       shape=False)
        pm.delete(locators)
        self.removeContainersPostBake(preContainers)

        for v in allAttrs:
            layerValues = []
            baseplug, layerplug = self.funcs.getLowerLayerPlugs(v, resultLayer)
            animRange = int(keyRange[-1] - keyRange[0] + 1)
            for x in range(0, animRange):
                baseVal = cmds.getAttr(baseplug, time=keyRange[0] + x)
                layerVal = cmds.getAttr(layerplug, time=keyRange[0] + x)
                delta = layerVal - baseVal
                layerValues.append(delta)

            for x in range(0, animRange):
                cmds.setKeyframe(layerplug, time=keyRange[0] + x, value=layerValues[x])
        pm.animLayer(resultLayer, edit=True, override=False)

    def additiveExtractSelection(self):
        sel = cmds.ls(sl=True)
        if sel:
            self.additiveExtract(sel)

    def bakeConstraintToAdditiveSelection(self):
        sel = cmds.ls(sl=True)
        if sel:
            self.bakeConstraintToAdditive(sel)

    def bakeConstraintToAdditive(self, selection):
        """
        Bakes out controls with constraints to an additive layer.
        :param selection:
        :return:
        """
        if not selection:
            return cmds.warning('No objects selected')

        constraints = [cmds.listConnections(s, type='constraint') for s in selection]
        filteredConstraints = list(set([item for sublist in constraints for item in sublist if item]))
        if not filteredConstraints:
            return cmds.warning('No constraints found')

        additiveLayer = cmds.animLayer('AdditiveExtract', override=True)

        keyRange = self.funcs.get_all_layer_key_times(selection)
        cmds.bakeResults(selection,
                         time=(keyRange[0], keyRange[-1]),
                         destinationLayer=additiveLayer,
                         simulation=False,
                         sampleBy=1,
                         oversamplingRate=1,
                         disableImplicitControl=True,
                         preserveOutsideKeys=False,
                         sparseAnimCurveBake=False,
                         removeBakedAttributeFromLayer=False,
                         removeBakedAnimFromLayer=False,
                         bakeOnOverrideLayer=True,
                         minimizeRotation=True,
                         controlPoints=False,
                         shape=False)

        nodesToRemove = list()
        for s in selection:
            constraints = cmds.listRelatives(s, type='constraint')
            if not constraints:
                continue
            for c in constraints:
                connections = cmds.listConnections(c, type='transform')
                if connections:
                    for con in connections:
                        if con in selection:
                            continue
                        if con not in nodesToRemove:
                            nodesToRemove.append(con)
        for c in nodesToRemove:
            if cmds.objExists(c): cmds.delete(nodesToRemove)

        cmds.animLayer(additiveLayer, edit=True, mute=True, lock=True)

        cmds.currentTime(cmds.currentTime(query=True))

        overrideLayer = cmds.animLayer('ConstraintBase', override=True)
        cmds.bakeResults(selection,
                         time=(keyRange[0], keyRange[-1]),
                         destinationLayer=overrideLayer,
                         simulation=False,
                         sampleBy=1,
                         oversamplingRate=1,
                         disableImplicitControl=True,
                         preserveOutsideKeys=False,
                         sparseAnimCurveBake=False,
                         removeBakedAttributeFromLayer=False,
                         removeBakedAnimFromLayer=False,
                         bakeOnOverrideLayer=True,
                         minimizeRotation=True,
                         controlPoints=False,
                         shape=False)

        cmds.animLayer(additiveLayer, edit=True, mute=False, lock=False)
        cmds.animLayer(additiveLayer, edit=True, override=False)
        cmds.setAttr(additiveLayer + '.scaleAccumulationMode', 0)

        cmds.currentTime(cmds.currentTime(query=True))

        attributes = cmds.animLayer(overrideLayer, query=True, attribute=True)

        baseLayerMPlugs, baseLayerMFnAnimCurves = self.funcs.omGetPlugsFromLayer(str(overrideLayer), attributes)
        additiveLayerMPlugs, additiveMFnAnimCurves = self.funcs.omGetPlugsFromLayer(str(additiveLayer), attributes)

        overrideValues = dict()
        additiveValues = dict()
        additiveMTimeArray = None
        overrideMTimeArray = None

        for attr, curve in baseLayerMFnAnimCurves.items():
            keyTimes = [om2.MTime(curve.input(key).value, om2.MTime.uiUnit()) for key in xrange(curve.numKeys)]

            baseKeyValues = [curve.value(key) for key in xrange(curve.numKeys)]
            additiveKeyValues = [additiveMFnAnimCurves[attr].value(key) for key in xrange(curve.numKeys)]

            initialVal = baseKeyValues[0]
            finalVal = baseKeyValues[-1]

            blendedValues = []
            for index, key in enumerate(keyTimes):
                blendedValues.append(baseKeyValues[index] - additiveKeyValues[index])
            additiveValues[attr] = blendedValues
            overrideValues[attr] = [initialVal, finalVal]
            if not additiveMTimeArray:
                additiveMTimeArray = self.funcs.createMTimeArray(keyTimes[0].value,
                                                                 int(keyTimes[-1].value) - int(keyTimes[0].value) + 1)
                overrideMTimeArray = self.funcs.createMTimePairArray(keyTimes[0], keyTimes[-1])
        dg = om2.MDGModifier()
        for key, mcurve in additiveMFnAnimCurves.items():
            sources = additiveLayerMPlugs[key].connectedTo(True, False)
            for i in xrange(len(sources)):
                dg.disconnect(sources[i], additiveLayerMPlugs[key])

            dg.doIt()

            adjustedCurve = oma2.MFnAnimCurve(additiveLayerMPlugs[key])
            adjustedCurve.create(additiveLayerMPlugs[key], additiveMFnAnimCurves[key].animCurveType, dg)

            adjustedCurve.addKeys(additiveMTimeArray,
                                  additiveValues[key],
                                  oma2.MFnAnimCurve.kTangentGlobal,
                                  oma2.MFnAnimCurve.kTangentGlobal)
            dg.doIt()

            sources = baseLayerMPlugs[key].connectedTo(True, False)
            for i in xrange(len(sources)):
                dg.disconnect(sources[i], baseLayerMPlugs[key])

            dg.doIt()

            adjustedCurve = oma2.MFnAnimCurve(baseLayerMPlugs[key])
            adjustedCurve.create(baseLayerMPlugs[key], baseLayerMFnAnimCurves[key].animCurveType, dg)

            adjustedCurve.addKeys(overrideMTimeArray,
                                  overrideValues[key],
                                  oma2.MFnAnimCurve.kTangentGlobal,
                                  oma2.MFnAnimCurve.kTangentGlobal)
            dg.doIt()

        for attr in attributes:
            if 'visibility' in attr.split('.')[-1]:
                cmds.animLayer(additiveLayer, edit=True, removeAttribute=attr)
        cmds.delete(overrideLayer)

    def additiveExtract(self, nodes):
        """
        TODO - fix bad calculation on non-zero start time
        :param nodes:
        :return:
        """
        keyRange = self.funcs.getTimelineHighlightedRange()
        if keyRange[0] == keyRange[1]:
            keyRange = self.funcs.getTimelineRange()
        overrideLayer = cmds.animLayer('AdditiveBase', override=True)

        cmds.bakeResults(nodes,
                         time=(keyRange[0], keyRange[-1]),
                         destinationLayer=overrideLayer,
                         simulation=False,
                         sampleBy=1,
                         oversamplingRate=1,
                         disableImplicitControl=True,
                         preserveOutsideKeys=False,
                         sparseAnimCurveBake=True,
                         removeBakedAttributeFromLayer=False,
                         removeBakedAnimFromLayer=False,
                         bakeOnOverrideLayer=True,
                         minimizeRotation=True,
                         controlPoints=False,
                         shape=False)
        additiveLayer = cmds.animLayer('AdditiveExtract', copy=overrideLayer, parent=overrideLayer)
        cmds.animLayer(additiveLayer, edit=True, override=False)
        cmds.setAttr(additiveLayer + '.scaleAccumulationMode', 0)

        attributes = cmds.animLayer(overrideLayer, query=True, attribute=True)
        for attr in attributes:
            if 'visibility' in attr.split('.')[-1]:
                cmds.animLayer(additiveLayer, edit=True, removeAttribute=attr)
        layeredPlugs = list()
        basePlugs = list()
        baseLayerMPlugs, baseLayerMFnAnimCurves = self.funcs.omGetPlugsFromLayer(str(overrideLayer), attributes)
        additiveLayerMPlugs, additiveMFnAnimCurves = self.funcs.omGetPlugsFromLayer(str(additiveLayer), attributes)
        # print (baseLayerMFnAnimCurves)
        overrideValues = dict()
        additiveValues = dict()
        additiveMTimeArray = None
        overrideMTimeArray = None

        for attr, curve in baseLayerMFnAnimCurves.items():
            # print (attr, curve.numKeys)
            keyTimes = [om2.MTime(curve.input(key).value, om2.MTime.uiUnit()) for key in xrange(curve.numKeys)]

            # print (keyTimes)
            keyValues = [curve.value(key) for key in xrange(curve.numKeys)]
            # print (keyValues)
            initialVal = keyValues[0]
            finalVal = keyValues[-1]
            keyRange = keyTimes[-1] - keyTimes[0]
            # print (initialVal, finalVal, keyRange)
            blendedValues = []
            for index, key in enumerate(keyTimes):
                alpha = key.value / keyRange.value
                progress = ((finalVal - initialVal) * alpha) + initialVal
                blendedValues.append(progress - keyValues[index])
            additiveValues[attr] = blendedValues
            overrideValues[attr] = [initialVal, finalVal]
            if not additiveMTimeArray:
                additiveMTimeArray = self.funcs.createMTimeArray(keyTimes[0].value,
                                                                 int(keyTimes[-1].value) - int(keyTimes[0].value) + 1)
                overrideMTimeArray = self.funcs.createMTimePairArray(keyTimes[0], keyTimes[-1])
        dg = om2.MDGModifier()
        for key, mcurve in additiveMFnAnimCurves.items():
            sources = additiveLayerMPlugs[key].connectedTo(True, False)
            for i in xrange(len(sources)):
                dg.disconnect(sources[i], additiveLayerMPlugs[key])

            dg.doIt()

            adjustedCurve = oma2.MFnAnimCurve(additiveLayerMPlugs[key])
            adjustedCurve.create(additiveLayerMPlugs[key], additiveMFnAnimCurves[key].animCurveType, dg)

            adjustedCurve.addKeys(additiveMTimeArray,
                                  additiveValues[key],
                                  oma2.MFnAnimCurve.kTangentGlobal,
                                  oma2.MFnAnimCurve.kTangentGlobal)
            dg.doIt()

            sources = baseLayerMPlugs[key].connectedTo(True, False)
            for i in xrange(len(sources)):
                dg.disconnect(sources[i], baseLayerMPlugs[key])

            dg.doIt()

            adjustedCurve = oma2.MFnAnimCurve(baseLayerMPlugs[key])
            adjustedCurve.create(baseLayerMPlugs[key], baseLayerMFnAnimCurves[key].animCurveType, dg)

            adjustedCurve.addKeys(overrideMTimeArray,
                                  overrideValues[key],
                                  oma2.MFnAnimCurve.kTangentGlobal,
                                  oma2.MFnAnimCurve.kTangentGlobal)
            dg.doIt()
            # layeredPlugs.append(layerPlug)
            # basePlugs.append(basePlug)
        return

    def quickMergeAllLayers(self):
        try:
            with self.funcs.suspendUpdate():
                allLayers = cmds.ls(type='animLayer')
                rootLayer = cmds.animLayer(query=True, root=True)

                allAttrs = list()
                allNodes = list()
                for layer in allLayers:
                    attrs = cmds.animLayer(layer, query=True, attribute=True)
                    if not attrs:
                        continue
                    for attr in attrs:
                        if attr not in allAttrs:
                            allAttrs.append(attr)
                        node = mel.eval('plugNode "{0}"'.format(attrs[-1]))
                        if node not in allNodes:
                            allNodes.append(node)

                allLayers.remove(rootLayer)
                if not allNodes:
                    return cmds.warning('No controls found in layers, aborting')
                if not allAttrs:
                    return cmds.warning('No controls found in layers, aborting')
                keyRange = self.funcs.get_all_layer_key_times(allNodes)
                if not keyRange or keyRange[0] is None:
                    keyRange = self.funcs.getTimelineRange()

                cmds.bakeResults(allAttrs,
                                 time=(keyRange[0], keyRange[-1]),
                                 # destinationLayer=rootLayer,
                                 simulation=True,
                                 sampleBy=1,
                                 oversamplingRate=1,
                                 disableImplicitControl=True,
                                 preserveOutsideKeys=False,
                                 sparseAnimCurveBake=True,
                                 removeBakedAttributeFromLayer=True,
                                 removeBakedAnimFromLayer=True,
                                 # bakeOnOverrideLayer=False,
                                 minimizeRotation=True,
                                 controlPoints=False,
                                 shape=False)

                cmds.delete(allLayers)
        except Exception as e:
            self.funcs.resumeSkinning()

    def quickMergeSelectionToNew(self):
        self.quickMergeSelection(base=False)

    def quickMergeSelectionToBase(self):
        self.quickMergeSelection(base=True)

    def quickMergeSelection(self, base=True):
        selection = cmds.ls(sl=True)
        if not selection:
            return cmds.warning('No objects selected')
        try:
            with self.funcs.suspendUpdate():
                allLayers = cmds.ls(type='animLayer')
                rootLayer = cmds.animLayer(query=True, root=True)
                affectedLayers = cmds.animLayer(query=True, affectedLayers=True)
                if rootLayer in affectedLayers: affectedLayers.remove(rootLayer)
                if not affectedLayers:
                    return cmds.warning('Objects do not appear to be in any animation layers')

                resultLayer = cmds.animLayer(override=True)
                keyRange = self.funcs.get_all_layer_key_times(selection)
                if not keyRange or keyRange[0] == None:
                    keyRange = self.funcs.getTimelineRange()

                if base:
                    cmds.bakeResults(selection,
                                     time=(keyRange[0], keyRange[-1]),
                                     # destinationLayer=rootLayer,
                                     simulation=len(selection) > pm.optionVar.get(self.bakeSimObjectCountOption, 10),
                                     sampleBy=1,
                                     oversamplingRate=1,
                                     disableImplicitControl=True,
                                     preserveOutsideKeys=False,
                                     sparseAnimCurveBake=True,
                                     removeBakedAttributeFromLayer=True,
                                     removeBakedAnimFromLayer=True,
                                     # bakeOnOverrideLayer=False,
                                     minimizeRotation=True,
                                     controlPoints=False,
                                     shape=False)

                else:
                    cmds.bakeResults(selection,
                                 time=(keyRange[0], keyRange[-1]),
                                 destinationLayer=resultLayer,
                                 simulation=len(selection) > pm.optionVar.get(self.bakeSimObjectCountOption, 10),
                                 sampleBy=1,
                                 oversamplingRate=1,
                                 disableImplicitControl=True,
                                 preserveOutsideKeys=False,
                                 sparseAnimCurveBake=True,
                                 removeBakedAttributeFromLayer=True,
                                 removeBakedAnimFromLayer=True,
                                 # bakeOnOverrideLayer=False,
                                 minimizeRotation=True,
                                 controlPoints=False,
                                 shape=False)
                mel.eval('deleteEmptyAnimLayers')

        except Exception as e:
            self.funcs.resumeSkinning()
