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

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
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
        self.setCategory('tbtools_constraints')
        self.addCommand(self.tb_hkey(name='bakeAim',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAim()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.openMM()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.closeMM()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class AimTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
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

    def __new__(cls):
        if AimTools.__instance is None:
            AimTools.__instance = object.__new__(cls)

        AimTools.__instance.val = cls.toolName
        AimTools.__instance.loadData()

        return AimTools.__instance

    def __init__(self, **kwargs):
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
        self.aimWidget = AimAxisWidget(itemList=['x','y','z'],
                                       aimAxis=self.defaultAimData.get('aimAxis'),
                                       upAxis=self.defaultAimData.get('upAxis'),
                                       flipAim=self.defaultAimData.get('flipAim'),
                                       flipUp=self.defaultAimData.get('flipUp'),
                                       distance=self.defaultAimData.get('distance'))
        self.aimWidget.itemLayout.addStretch()
        self.layout.addWidget(infoText)
        self.layout.addWidget(self.aimWidget)
        self.layout.addStretch()
        self.aimWidget.editedSignal.connect(self.updateDefault)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def build_MM(self):
        cmds.menuItem(label='tbAimTools',
                      divider=0,
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
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimZY(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimXZ(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'z', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimYZ(self, *args):
        default = {'aimAxis': 'y', 'upAxis': 'z', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimYX(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimZX(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'x', 'flipAim': False, 'flipUp': False, 'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict={}, default=default)

    def aimToLocators(self, directionDict=dict(), default=dict()):
        sel = cmds.ls(sl=True)
        if not sel: return
        self.targets = sel
        self.constraints = list()
        self.locators = list()
        self.controlInfo = dict()
        for target in self.targets:
            name = target.split(':')[-1]
            refName = self.funcs.getRefName(target)
            if refName not in directionDict.keys():
                data = default
            elif name not in directionDict[refName].keys():
                data = default
            else:
                data = directionDict[refName][name]
            self.aimToLocator(refName, name, target, data)
        self.bake()
        for key in self.controlInfo.keys():
            self.constraintControls(key)

    def aimToLocator(self, refName, name, target, data):
        aimAxis, upAxis = self.getAimAxis(data)

        up = self.funcs.tempLocator(name=name, suffix='upLoc')
        aim = self.funcs.tempLocator(name=name, suffix='fwdLoc')

        self.locators.extend([str(up), str(aim)])
        self.controlInfo[target] = [str(aim), aimAxis, str(up), upAxis]
        targetPos = cmds.xform(target, query=True, worldSpace=True, absolute=True, rotatePivot=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])

        # depending on the rig this really doesn't work
        upVec = getLocalVecToWorldSpaceAPI(target, vec=upAxis, offset=targetPosMVector,
                                           mult=data['distance'] / self.funcs.locator_unit_conversion())
        fwdVec = getLocalVecToWorldSpaceAPI(target, vec=aimAxis, offset=targetPosMVector,
                                            mult=data['distance'] / self.funcs.locator_unit_conversion())

        fwdPos = self.getPosition(target, self.getAxis(data['aimAxis'], data['flipAim']), data['distance'])
        upPos = self.getPosition(target, self.getAxis(data['upAxis'], data['flipUp']), data['distance'])
        aim.translate.set(fwdPos)
        up.translate.set(upPos)

        self.constraints.append(cmds.parentConstraint(target, str(aim),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z')))
        self.constraints.append(cmds.parentConstraint(target, str(up),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z')))

        if refName not in self.foundControls.keys():
            self.foundControls[refName] = dict()
        self.foundControls[refName][name] = {'aimAxis': aimAxis,
                                             'upAxis': upAxis,
                                             'flipAim': data['flipAim'],
                                             'flipUp': data['flipUp'],
                                             'distance': data['distance']
                                             }

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
        if not keyRange:
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
        distance = 10.0
        refName = self.funcs.getRefName(sel[0])
        if refName in self.aimData.keys():
            name = sel[0].split(':')[-1]
            if name in self.aimData[refName].keys():
                aimAxis = self.aimData[refName][name]['aimAxis']
                upAxis = self.aimData[refName][name]['upAxis']
                flipAim = self.aimData[refName][name]['flipAim']
                flipUp = self.aimData[refName][name]['flipUp']
                distance = self.aimData[refName][name]['distance']
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

    def updatePreview(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance):
        fwdPreview = 'fwd_Preview'
        upPreview = 'up_Preview'
        if not cmds.objExists(fwdPreview):
            fwdPreview = self.funcs.tempLocator(name='fwd', suffix='Preview')
            fwdAnn = pm.annotate(fwdPreview, tx='Aim Forward', p=(0, 1, 0))
            pm.parent(fwdAnn, fwdPreview)
        if not cmds.objExists(upPreview):
            upPreview = self.funcs.tempLocator(name='up', suffix='Preview')
            upAnn = pm.annotate(upPreview, tx='Aim Up', p=(0, 1, 0))
            pm.parent(upAnn, upPreview)
        fwdPreview = pm.PyNode(fwdPreview)
        upPreview = pm.PyNode(upPreview)
        fwdPos = self.getPosition(controlName, self.getAxis(aimAxis, flipAim), distance)
        upPos = self.getPosition(controlName, self.getAxis(upAxis, flipUp), distance)
        fwdPreview.translate.set(fwdPos)
        upPreview.translate.set(upPos)

    def updateDefault(self, aimAxis, upAxis, flipAim, flipUp, distance):
        self.defaultAimData['aimAxis'] = aimAxis
        self.defaultAimData['upAxis'] = upAxis
        self.defaultAimData['flipAim'] = flipAim
        self.defaultAimData['flipUp'] = flipUp
        self.defaultAimData['distance'] = distance
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
                                           mult=distance / self.funcs.locator_unit_conversion())
        return vec

    def assignDefault(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance):
        refName = self.funcs.getRefName(controlName)
        if refName not in self.aimData.keys():
            self.aimData[refName] = dict()
        self.aimData[refName][controlName.split(':')[-1]] = {'aimAxis': aimAxis,
                                                             'upAxis': upAxis,
                                                             'flipAim': flipAim,
                                                             'flipUp': flipUp,
                                                             'distance': distance
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


def getLocalVecToWorldSpaceAPI(node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
    selList = om.MSelectionList()
    selList.add(node)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    matrix = nodeDagPath.inclusiveMatrix()
    vec = ((vec * matrix).normal() * mult)
    vec += offset
    return vec.x, vec.y, vec.z

