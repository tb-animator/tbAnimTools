'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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

    this script holds a bunch of useful keyframe related functions to make life easier

    send issues/ requests to brimblashman@gmail.com
    visit tb-animator.blogspot.com for "stuff"

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
                                     category=self.category, command=['aimTools.quickAim()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['aimTools.openMM()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['aimTools.closeMM()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class aimTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'aimTools'
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
    defaultData = {'direction': 'xy', 'flipAim': False, 'flipUp': False, 'distance': 100.0}

    def __new__(cls):
        if aimTools.__instance is None:
            aimTools.__instance = object.__new__(cls)

        aimTools.__instance.val = cls.toolName
        aimTools.__instance.loadData()

        return aimTools.__instance

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
        super(aimTools, self).optionUI()
        return self.layout

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
        default = {'direction': 'xy', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict=self.aimData,
                           default=default)

    def quickAimXY(self, *args):
        default = {'direction': 'xy', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimZY(self, *args):
        default = {'direction': 'zy', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimXZ(self, *args):
        default = {'direction': 'xz', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimYZ(self, *args):
        default = {'direction': 'yz', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimYX(self, *args):
        default = {'direction': 'yx', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
        self.aimToLocators(directionDict={}, default=default)

    def quickAimZX(self, *args):
        default = {'direction': 'zx', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
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
            elif target not in directionDict[refName].keys():
                data = default
            else:
                data = directionDict[refName][target]
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
        targetPos = cmds.xform(target, query=True, worldSpace=True, translation=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])
        upVec = getLocalVecToWorldSpaceAPI(target, vec=upAxis, offset=targetPosMVector,
                                           mult=data['distance'] / self.funcs.locator_unit_conversion())
        fwdVec = getLocalVecToWorldSpaceAPI(target, vec=aimAxis, offset=targetPosMVector,
                                            mult=data['distance'] / self.funcs.locator_unit_conversion())

        up.translate.set(upVec)
        aim.translate.set(fwdVec)

        self.constraints.append(cmds.parentConstraint(target, str(up),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z')))
        self.constraints.append(cmds.parentConstraint(target, str(aim),
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
        flipVector = {True: [-1.0, 1.0], False: [1.0, -1.0]}  # make this data driven somehow?
        aimAxis = self.axisDict[data['aimAxis']] * flipVector[data['flipAim']][0]
        upAxis = self.axisDict[data['upAxis']] * flipVector[data['flipUp']][1]
        return aimAxis, upAxis

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
        flipAim = False,
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
        prompt = AimAxisDialog(controlName=sel[0],
                               title='Assign default aim for control',
                               text=sel[0],
                               itemList=['x', 'y', 'z'],
                               aimAxis=aimAxis,
                               upAxis=upAxis,
                               flipAim=flipAim,
                               flipUp=flipUp,
                               distance=distance)
        prompt.assignSignal.connect(self.assignDefault)

        if prompt.exec_():
            pass
        else:
            pass

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
        super(aimTools, self).loadData()
        self.aimData = self.rawJsonData.get('aimData', dict())

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['aimData'] = self.aimData

def getLocalVecToWorldSpaceAPI(node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
    selList = om.MSelectionList()
    selList.add(node)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    matrix = nodeDagPath.inclusiveMatrix()
    vec = ((vec * matrix).normal() * mult) + offset
    return vec.x, vec.y, vec.z
