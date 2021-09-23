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
import maya.api.OpenMaya as om2
import pymel.core.datatypes as dt
import math
from Abstract import *
from tb_UI import *

import maya.api.OpenMaya as OpenMaya
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
kRotateOrderMapping = {
    'xyz': om.MEulerRotation.kXYZ,
    'yzx': om.MEulerRotation.kYZX,
    'zxy': om.MEulerRotation.kZXY,
    'xzy': om.MEulerRotation.kXZY,
    'yxz': om.MEulerRotation.kYXZ,
    'zyx': om.MEulerRotation.kZYX,
    '0': om.MEulerRotation.kXYZ,
    '1': om.MEulerRotation.kYZX,
    '2': om.MEulerRotation.kZXY,
    '3': om.MEulerRotation.kXZY,
    '4': om.MEulerRotation.kYXZ,
    '5': om.MEulerRotation.kZYX
}
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

assetCommandName = 'aimToolAssetMenu'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('constraints'))
        self.addCommand(self.tb_hkey(name='bakeAim',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAim()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.openMM()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.closeMM()']))

        self.addCommand(self.tb_hkey(name='aimAtTempControl',
                                     annotation='Creates a new control at your selection, position it then deselect to bake it out',
                                     category=self.category, command=['AimTools.aimAtTempControl()']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.assetRmbCommand()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class AimTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'AimTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    foundControls = dict()  # use this to save the last used settings to a file
    axisDict = {'x': om.MVector.xAxis,
                'y': om.MVector.yAxis,
                'z': om.MVector.zAxis,
                }

    distance = 100.0
    aimData = dict()
    lastUseData = dict()
    defaultData = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
    defaultAimData = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': 100.0}

    tempAimSizeOption = 'tbTempAimLocatorSize'
    aimFwdMotionTrailOption = 'aimFwdMotionTrailOption'
    aimUpMotionTrailOption = 'aimUpMotionTrailOption'
    aimTempMotionTrailOption = 'aimTempMotionTrailOption'
    mainAssetAttr = 'mainAsset'
    controlMessageAttr = 'aimedControl'

    aimAtTempControlScriptJobs = list()

    def __new__(cls):
        if AimTools.__instance is None:
            AimTools.__instance = object.__new__(cls)

        AimTools.__instance.val = cls.toolName
        AimTools.__instance.loadData()

        return AimTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.target = None
        self.Ptarget = None
        self.name = None
        self.pos = None
        self.up = None
        self.fwd = None
        self.constraints = list()

        self.aimAxis = None
        self.upAxis = None
        self.flipAim = False
        self.flipUp = False

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(AimTools, self).optionUI()
        infoText = QLabel()
        infoText.setText(
            'Set the default quick aim values here. If a control does not have a specific preset created, the tool will default to these values.\n'
            'The distance value will be used for quick anim bakes for specific axis')
        infoText.setWordWrap(True)
        self.aimWidget = AimAxisWidget(itemList=['x', 'y', 'z'],
                                       aimAxis=self.defaultAimData.get('aimAxis'),
                                       upAxis=self.defaultAimData.get('upAxis'),
                                       flipAim=self.defaultAimData.get('flipAim'),
                                       flipUp=self.defaultAimData.get('flipUp'),
                                       distance=self.defaultAimData.get('distance'))
        tempControlHeader = subHeader('Aim at temp control')
        tempControlInfo = infoLabel(['Creates a temp control at the current selection.',
                                     'Move it into the desired position and once deselected it will baked out relative to the control. The control will then be aimed at the new temp control'])
        crossSizeWidget = intFieldWidget(optionVar=self.tempAimSizeOption,
                                         defaultValue=1.0,
                                         label='Aim to temp control size',
                                         minimum=0.1, maximum=100, step=0.1)
        crossSizeWidget.changedSignal.connect(self.updateTempControlPreview)
        motionTrailHeader = subHeader('Motion Trails')
        motionTrailInfo = infoLabel(['Add motion trails to newly created temp controls.'])

        aimFwdMotionTrailWidget = optionVarBoolWidget('Motion Trail On Aim Forward',
                                                      self.aimFwdMotionTrailOption)
        aimUpMotionTrailWidget = optionVarBoolWidget('Motion Trail On Aim Up',
                                                     self.aimUpMotionTrailOption)
        aimTempMotionTrailWidget = optionVarBoolWidget('Motion Trail On Temp Control',
                                                       self.aimTempMotionTrailOption)

        self.aimWidget.itemLayout.addStretch()
        self.layout.addWidget(infoText)
        self.layout.addWidget(self.aimWidget)
        self.layout.addWidget(tempControlHeader)
        self.layout.addWidget(tempControlInfo)
        self.layout.addWidget(crossSizeWidget)
        self.layout.addWidget(motionTrailHeader)
        self.layout.addWidget(motionTrailInfo)
        self.layout.addWidget(aimFwdMotionTrailWidget)
        self.layout.addWidget(aimUpMotionTrailWidget)
        self.layout.addWidget(aimTempMotionTrailWidget)
        self.layout.addStretch()
        self.aimWidget.editedSignal.connect(self.updateDefault)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def build_MM(self):
        cmds.menuItem(label='tbAimTools',
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick Aim at Temp Control',
                      command=self.aimAtTempControl,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick Aim',
                      command=self.quickAim,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick aim X Y',
                      command=self.quickAimXY,
                      )
        cmds.menuItem(label='Quick aim Z Y',
                      command=self.quickAimZY,
                      )
        cmds.menuItem(label='Quick aim X Z',
                      command=self.quickAimXZ,
                      )
        cmds.menuItem(label='Quick aim Y Z',
                      command=self.quickAimYZ,
                      )
        cmds.menuItem(label='Quick aim Y X',
                      command=self.quickAimYX,
                      )
        cmds.menuItem(label='Quick aim Z X',
                      command=self.quickAimZX,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Set default for selection',
                      command=self.setDefaultUI,
                      )

    """
    Functions
    """

    def quickAim(self, *args):
        # TODO make this handle multiple objects
        self.aimToLocators(directionDict=self.aimData,
                           default=self.defaultAimData)

    def quickAimXY(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimZY(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimXZ(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'z', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimYZ(self, *args):
        default = {'aimAxis': 'y', 'upAxis': 'z', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimYX(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimZX(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'x', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def aimToLocators(self, directionDict=dict(), default=dict(), forceDefault=False):
        sel = cmds.ls(sl=True)
        if not sel: return
        self.targets = sel
        self.constraints = list()
        self.locators = list()
        self.controlInfo = dict()
        for target in self.targets:
            name = target.split(':')[-1]
            refName = self.funcs.getRefName(target)
            # compare to see if there is a preset in directionDict
            if refName not in directionDict.keys():
                data = default
            elif name not in directionDict[refName].keys():
                data = default
            else:
                if forceDefault:
                    # forcing an override to the preset aim, if there is a preset, grab it's distance value
                    data = default
                    data['distance'] = directionDict[refName][name]['distance']
                else:
                    data = directionDict[refName][name]
            self.aimToLocator(refName, name, target, data)
        self.bake()
        for key in self.controlInfo.keys():
            self.constraintControls(key)

    def aimToLocator(self, refName, name, target, data):
        asset = self.createAsset(name=name + '_asset')
        aimAxis, upAxis = self.getAimAxis(data)

        up = self.funcs.tempControl(name=name, suffix='upLoc', scale=data.get('scale', 1.0))
        aim = self.funcs.tempControl(name=name, suffix='fwdLoc', scale=data.get('scale', 1.0))

        pm.addAttr(up, ln=self.mainAssetAttr, at='message')
        pm.addAttr(aim, ln=self.mainAssetAttr, at='message')
        pm.addAttr(asset, ln=self.controlMessageAttr, at='message')
        pm.connectAttr(asset + '.message', up + '.' + self.mainAssetAttr)
        pm.connectAttr(asset + '.message', aim + '.' + self.mainAssetAttr)
        pm.connectAttr(target + '.message', asset + '.' + self.controlMessageAttr)

        self.locators.extend([str(up), str(aim)])
        self.controlInfo[target] = [str(aim), aimAxis, str(up), upAxis]
        targetPos = cmds.xform(target, query=True, worldSpace=True, absolute=True, rotatePivot=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])

        fwdPos = self.getPosition(target, self.getAxis(data['aimAxis'], data['flipAim']), data['distance'])
        upPos = self.getPosition(target, self.getAxis(data['upAxis'], data['flipUp']), data['distance'])
        aim.translate.set(fwdPos)
        up.translate.set(upPos)

        self.constraints.append(cmds.parentConstraint(target, str(aim),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z'))[0])
        self.constraints.append(cmds.parentConstraint(target, str(up),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z'))[0])

        if refName not in self.foundControls.keys():
            self.foundControls[refName] = dict()
        self.foundControls[refName][name] = {'aimAxis': aimAxis,
                                             'upAxis': upAxis,
                                             'flipAim': data['flipAim'],
                                             'flipUp': data['flipUp'],
                                             'distance': data['distance'],
                                             'scale': data.get('scale', 1.0)
                                             }

        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=[up, aim])
        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=self.constraints)

        if pm.optionVar.get(self.aimFwdMotionTrailOption, False):
            cmds.select(str(aim), replace=True)
            mel.eval('createMotionTrail')
        if pm.optionVar.get(self.aimUpMotionTrailOption, False):
            cmds.select(str(up), replace=True)
            mel.eval('createMotionTrail')

    def getAimAxis(self, data):
        flipVector = {True: -1.0, False: 1.0}  # make this data driven somehow?
        aimAxis = self.axisDict[data['aimAxis']] * flipVector[data['flipAim']]
        upAxis = self.axisDict[data['upAxis']] * flipVector[data['flipUp']]
        return aimAxis, upAxis

    def getAxis(self, axis, flip):
        flipVector = {True: -1.0, False: 1.0}  # make this data driven somehow?
        return self.axisDict[axis] * flipVector[flip]

    def bake(self):
        keyRange = self.funcs.get_all_layer_key_times(self.targets)
        if keyRange[0] is None:
            keyRange = self.funcs.getTimelineRange()
        bakeLayer = cmds.animLayer('AimBakeLocators', override=True)
        cmds.bakeResults(self.locators, time=(keyRange[0], keyRange[1]),
                         simulation=False,
                         attribute='translate',
                         destinationLayer=bakeLayer,
                         removeBakedAttributeFromLayer=False,
                         bakeOnOverrideLayer=True,
                         sampleBy=1,
                         preserveOutsideKeys=True)
        for layer in cmds.ls(type='animLayer'):
            cmds.animLayer(layer, edit=True, selected=False, preferred=False)
        cmds.animLayer(bakeLayer, edit=True, selected=True, preferred=True)

        pm.delete(self.constraints)

    def constraintControls(self, key):
        cmds.aimConstraint(self.controlInfo[key][0], key,
                           worldUpObject=self.controlInfo[key][2],
                           aimVector=[z for z in self.controlInfo[key][1]],
                           upVector=[y for y in self.controlInfo[key][3]],
                           worldUpVector=[y for y in self.controlInfo[key][3]],
                           worldUpType='object')

    def setDefaultUI(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        aimAxis = 'z'
        upAxis = 'y'
        flipAim = False
        flipUp = False
        distance = 100.0
        refName = self.funcs.getRefName(sel[0])
        if refName in self.aimData.keys():
            name = sel[0].split(':')[-1]
            if name in self.aimData[refName].keys():
                aimAxis = self.aimData[refName][name].get('aimAxis', 'z')
                upAxis = self.aimData[refName][name].get('upAxis', 'y')
                flipAim = self.aimData[refName][name].get('flipAim', False)
                flipUp = self.aimData[refName][name].get('flipUp', False)
                distance = self.aimData[refName][name].get('distance', 100)
                scale = self.aimData[refName][name].get('scale', 1.0)
        prompt = AimAxisDialog(parent=self.funcs.getMainWindow(),
                               controlName=sel[0],
                               title='Assign default aim for control',
                               text=sel[0],
                               itemList=['x', 'y', 'z'],
                               aimAxis=aimAxis,
                               upAxis=upAxis,
                               flipAim=flipAim,
                               flipUp=flipUp,
                               distance=distance)
        prompt.show()
        prompt.assignSignal.connect(self.assignDefault)
        prompt.editedSignal.connect(self.updatePreview)
        prompt.closeSignal.connect(self.deletePreview)
        prompt.aimWidget.widgetedited()
        '''
        if prompt.exec_():
            pass
        else:
            pass
        '''

    def updatePreview(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        fwdPreview = 'fwd_Preview'
        upPreview = 'up_Preview'
        if not cmds.objExists(fwdPreview):
            fwdPreview = self.funcs.tempControl(name='fwd', suffix='Preview', scale=scale)
            fwdAnn = pm.annotate(fwdPreview, tx='Aim Forward', p=(0, 1, 0))
            pm.parent(fwdAnn, fwdPreview)
        if not cmds.objExists(upPreview):
            upPreview = self.funcs.tempControl(name='up', suffix='Preview', scale=scale)
            upAnn = pm.annotate(upPreview, tx='Aim Up', p=(0, 1, 0))
            pm.parent(upAnn, upPreview)
        fwdPreview = pm.PyNode(fwdPreview)
        upPreview = pm.PyNode(upPreview)
        fwdPreview.scale.set(scale, scale, scale)
        upPreview.scale.set(scale, scale, scale)
        fwdPos = self.getPosition(controlName, self.getAxis(aimAxis, flipAim), distance)
        upPos = self.getPosition(controlName, self.getAxis(upAxis, flipUp), distance)
        fwdPreview.translate.set(fwdPos)
        upPreview.translate.set(upPos)

    def updateDefault(self, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        self.defaultAimData['aimAxis'] = aimAxis
        self.defaultAimData['upAxis'] = upAxis
        self.defaultAimData['flipAim'] = flipAim
        self.defaultAimData['flipUp'] = flipUp
        self.defaultAimData['distance'] = distance
        self.defaultAimData['scale'] = scale
        self.saveData()

    def deletePreview(self):
        fwdPreview = 'fwd_Preview'
        upPreview = 'up_Preview'
        if cmds.objExists(fwdPreview):
            cmds.delete(fwdPreview)
        if cmds.objExists(upPreview):
            cmds.delete(upPreview)

    def getPosition(self, target, axis, distance):
        targetPos = cmds.xform(target, query=True, worldSpace=True, absolute=True, rotatePivot=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])

        # depending on the rig this really doesn't work
        vec = getLocalVecToWorldSpaceAPI(target, vec=axis, offset=targetPosMVector,
                                         mult=distance / self.funcs.unit_conversion())
        return vec

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
        print ("asset", asset)

        cmds.menuItem(label='Aim Tool', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Re bake to fixed distance', command=pm.Callback(self.rebakeCommand, asset))
        cmds.menuItem(label='Bake out to layer', command=pm.Callback(self.bakeOutCommand, asset))
        cmds.menuItem(label='Delete all controls', command=pm.Callback(self.deletControlsCommand, asset))
        cmds.menuItem(divider=True)

    def rebakeCommand(self, asset):
        sel = cmds.ls(sl=True)
        control = cmds.listConnections(asset + '.' + self.controlMessageAttr)[0]
        locators = cmds.listConnections(asset + '.message')
        temp = list()
        constraints = list()
        for loc in locators:
            tmp = cmds.createNode('transform')
            cmds.delete(cmds.pointConstraint(loc, tmp))
            constraints.append(cmds.parentConstraint(control, tmp, maintainOffset=True, skipRotate=('x', 'y', 'z'))[0])
            temp.append(tmp)

        cmds.select(temp, replace=True)

        mel.eval("simpleBakeToBase")
        cmds.delete(constraints)
        for index, loc in enumerate(locators):
            pm.pointConstraint(temp[index], loc)

        cmds.select(locators, replace=True)
        mel.eval("simpleBakeToOverride")
        cmds.delete(temp)
        cmds.select(sel, replace=True)

    def bakeOutCommand(self, asset):
        control = cmds.listConnections(asset + '.' + self.controlMessageAttr)[0]
        locators = cmds.listConnections(asset + '.message')
        cmds.select(control, replace=True)
        cmds.select(locators, add=True)

        mel.eval("simpleBakeToOverride")
        pm.delete(asset)
        cmds.select(control)

    def deletControlsCommand(self, asset):
        pm.delete(asset)

    def assignDefault(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        refName = self.funcs.getRefName(controlName)
        if refName not in self.aimData.keys():
            self.aimData[refName] = dict()
        self.aimData[refName][controlName.split(':')[-1]] = {'aimAxis': aimAxis,
                                                             'upAxis': upAxis,
                                                             'flipAim': flipAim,
                                                             'flipUp': flipUp,
                                                             'distance': distance,
                                                             'scale': scale
                                                             }
        self.saveData()

    def loadData(self):
        super(AimTools, self).loadData()
        self.aimData = self.rawJsonData.get('aimData', dict())
        self.defaultAimData = self.rawJsonData.get('defaultAimData', self.defaultData)

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['aimData'] = self.aimData
        self.classData['defaultAimData'] = self.defaultAimData

    """
    Hacky stuff for aim at locator
    """

    def clearAimAtTempControlScriptJobs(self):
        allJobs = cmds.scriptJob(listJobs=True)
        allJobID = [int(i.split(':')[0]) for i in allJobs]
        for j in self.aimAtTempControlScriptJobs:
            if j in allJobID:
                try:
                    pm.scriptJob(kill=j)
                except:
                    pass

    def aimAtTempControl(self, *args):
        sel = pm.ls(selection=True)

        if not sel:
            return

        control = sel[0]
        cmds.undoInfo(openChunk=True, chunkName='aimAtTempControl', stateWithoutFlush=False)
        tempControl = self.funcs.tempLocator(name=control, suffix='AimTempNode')
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)
        pm.delete(pm.parentConstraint(control, tempControl))
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()

        self.clearAimAtTempControlScriptJobs()
        self.aimAtTempControlScriptJobs.append(cmds.scriptJob(runOnce=True,
                                                              killWithScene=True,
                                                              compressUndo=True,
                                                              event=("SelectionChanged",
                                                                     pm.Callback(self.bakeTempAim, control,
                                                                                 tempControl))))
        self.aimAtTempControlScriptJobs.append(cmds.scriptJob(runOnce=True,
                                                              killWithScene=True,
                                                              compressUndo=True,
                                                              event=("ToolChanged",
                                                                     pm.Callback(self.bakeTempAim, control,
                                                                                 tempControl))))

    def bakeTempAim(self, control, tempControl):

        aimLocator = self.funcs.tempControl(name=control, suffix='aim', scale=1.0, color=(1.0, 0.537, 0.016),
                                            drawType='orb')

        pm.delete(pm.orientConstraint(tempControl, aimLocator))
        pm.delete(pm.pointConstraint(tempControl, aimLocator))

        cmds.undoInfo(openChunk=True, chunkName='aimAtTempControl', stateWithoutFlush=False)
        pm.delete(tempControl)
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)

        tempConstraint = pm.parentConstraint(control, aimLocator, maintainOffset=True)
        keyTimes = self.funcs.get_object_key_times(str(control))

        min_key = min(keyTimes)
        max_key = max(keyTimes)

        pm.bakeResults(aimLocator,
                       attribute=['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'],
                       simulation=False,
                       minimizeRotation=False,
                       time=(min_key, max_key))
        pm.delete(tempConstraint)

        constraint = self.constrainAimToTarget(str(control), str(aimLocator))

        asset = self.createAsset(name=control + '_AimAsset')
        pm.addAttr(aimLocator, ln=self.mainAssetAttr, at='message')
        pm.addAttr(asset, ln=self.controlMessageAttr, at='message')
        pm.connectAttr(asset + '.message', aimLocator + '.' + self.mainAssetAttr)
        pm.connectAttr(control + '.message', asset + '.' + self.controlMessageAttr)

        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=str(aimLocator))
        pm.container(asset, edit=True,
                     includeHierarchyBelow=True,
                     force=True,
                     addNode=constraint)

        self.clearAimAtTempControlScriptJobs()

        if pm.optionVar.get(self.aimTempMotionTrailOption, False):
            cmds.select(str(aimLocator), replace=True)
            mel.eval('createMotionTrail')

    def constrainTargetToControl(self, control, target):
        keyTimes = self.funcs.get_object_key_times(control)

        min_key = min(keyTimes)
        max_key = max(keyTimes)

        constraint = pm.parentConstraint(control, target, maintainOffset=True)
        pm.bakeResults(target,
                       attribute=['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'],
                       simulation=False,
                       minimizeRotation=False,
                       time=(min_key, max_key))
        pm.delete(constraint)

    def getLocalVector(self, node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
        animNode = self.getDagNode(node)
        matrix = animNode.inclusiveMatrix()
        vec = ((vec * matrix).normal() * mult) + offset
        return dt.Vector(vec.x, vec.y, vec.z)

    def getWorldSpaceVectorOffset(self, control, target, vec=om.MVector.yAxis):
        controlNode = self.getDagNode(control)
        controlMatrix = controlNode.inclusiveMatrix()

        targetNode = self.getDagNode(target)
        targetMatrix = targetNode.inclusiveMatrix()

        vec = ((vec * controlMatrix) * targetMatrix.inverse()).normal()
        return dt.Vector(vec.x, vec.y, vec.z)

    def getDagNode(self, node):
        selList = om.MSelectionList()
        selList.add(node)
        nodeDagPath = om.MDagPath()
        selList.getDagPath(0, nodeDagPath)
        return nodeDagPath

    def constrainAimToTarget(self, control, target):
        locatorPos = dt.Vector(pm.xform(target, query=True, worldSpace=True,
                                        # translation=True,
                                        rotatePivot=True))
        controlPos = dt.Vector(pm.xform(control, query=True, worldSpace=True,
                                        # translation=True,
                                        rotatePivot=True))
        aimVec = (locatorPos - controlPos).normal()

        xDot = aimVec * om.MVector.xAxis
        yDot = aimVec * om.MVector.yAxis
        zDot = aimVec * om.MVector.zAxis

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [dt.Vector(1, 0, 0), dt.Vector(0, 1, 0), dt.Vector(0, 0, 1)]
        upXxisIndex = axisList.index(min(axisList))

        aimVector = self.getVectorToTarget(target, control)
        upVector = localAxisVecList[upXxisIndex]
        worldUpVector = self.getWorldSpaceVectorOffset(control, target, vec=axisMapping[upXxisIndex])
        aimConstraint = pm.aimConstraint(target, control,
                                         aimVector=aimVector,
                                         worldUpObject=target,
                                         worldUpVector=worldUpVector,
                                         upVector=upVector,
                                         worldUpType='objectRotation',
                                         maintainOffset=False)
        return aimConstraint

    def getMatrix(self, node):
        '''
        Gets the world matrix of an object based on name.
        # TODO - set the position of the mfn transform to match the rotate pivot
        '''
        selection = om2.MSelectionList()
        selection.add(node)
        MObjectA = selection.getDependNode(0)
        fnThisNode = om2.MFnDependencyNode(MObjectA)
        worldMatrixAttr = fnThisNode.attribute("worldMatrix")
        matrixPlug = om2.MPlug(MObjectA, worldMatrixAttr)
        matrixPlug = matrixPlug.elementByLogicalIndex(0)
        matrixObject = matrixPlug.asMObject()

        worldMatrixData = om2.MFnMatrixData(matrixObject)
        worldMatrix = worldMatrixData.matrix()

        return worldMatrix

    def getVectorToTarget(self, target, control):
        tempNode = cmds.createNode('transform')
        cmds.delete(cmds.parentConstraint(control, tempNode))
        controlMatrix = self.getMatrix(tempNode)
        targetMatrix = self.getMatrix(target)

        offset = targetMatrix * controlMatrix.inverse()
        mTransformMtx = om2.MTransformationMatrix(offset)
        trans = mTransformMtx.translation(om2.MSpace.kWorld)
        cmds.delete(tempNode)
        return trans

    def drawTempControlPreview(self):
        self.funcs.tempControl(name='temp',
                               suffix='Preview',
                               scale=pm.optionVar.get(self.tempAimSizeOption, 1),
                               drawType='orb')

    def updateTempControlPreview(self, scale):
        if not cmds.objExists('temp_Preview'):
            self.drawTempControlPreview()

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)


def getLocalVecToWorldSpaceAPI(node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
    selList = om.MSelectionList()
    selList.add(node)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    matrix = nodeDagPath.inclusiveMatrix()
    vec = ((vec * matrix).normal() * mult)
    vec += offset
    return vec.x, vec.y, vec.z
