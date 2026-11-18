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
GRAVITY_SCALE = 'gravityScale'
DAMPING = 'damping'
STIFFNESS = 'stiffness'
FRICTION = 'friction'
BOUNCE = 'bounce'
BLEND = 'blend'
LOCKED = 'Locked'
FRAME_DELAY = 'frameDelay'
typesList = ["Single Chain", "Multiple Chains", "Points", "Constraint"]
constraintAttrPrefix = 'target[0].targetOffset'

"""
TODO

Do a pass on the physpoint nodes, connect them to the control that will be the attribute control so I don't
have to look it up
 
fix rotation for up vector, try and favour sideways by default, make it editable
chain damping button in ui
setting falloff, look for regular controls too - see if connected to physics control
fix the namespace bug
make new chain linear falloff
NEW LIST

get tool to talk to rig definition for mirror sides etc
read the preset stuff again

improve the bake speed/toggle
add quick click n go for chains n stuff
look at stick constraints - make them squishier?
angle limits? 
capsule collision? low priority
FIX AIM CONSTRAINT AXIS STUFF

constraints are restoring from the scene file, not the rig file!

Deleting a chain
# Traceback (most recent call last):
#   File "D:\AnimationWork\tbAnimTools\proApps\tbPhysics\tb_physicsTool.py", line 3490, in deleteChain
#     self.cls.deleteChain()
#   File "D:\AnimationWork\tbAnimTools\proApps\tbPhysics\tb_physicsTool.py", line 1723, in deleteChain
#     controls = self.getAllPhysicsControls(allNodes)
#   File "D:\AnimationWork\tbAnimTools\proApps\tbPhysics\tb_physicsTool.py", line 1698, in getAllPhysicsControls
#     allNodes = [x for x in allNodes if namespace in x]
# TypeError: coercing to Unicode: need string or buffer, list found

# TODO - make up the chain with the ease mode as text so it can be reused
"""

import socket
import pickle
import hashlib
import sys
import maya
import math

import maya.cmds as cmds
import maya.api.OpenMaya as om2

import maya.OpenMaya as om
import maya.api.OpenMayaAnim as oma2
from contextlib import contextmanager
import base64

maya.utils.loadStringResourcesForModule(__name__)
tbPhyics = 'Physics'

if sys.version_info >= (2, 8):
    from urllib.request import *
    from urllib import request, parse, error
else:
    from urllib2 import *

import json
import maya.mel as mel
from functools import partial
import maya.OpenMayaUI as omUI
import getStyleSheet as getqss

styleSheet = getqss.getStyleSheet()
from Abstract import *

# TODO - dev
from importlib import reload

from apps.tb_UI import *

xAx = om.MVector.xAxis
yAx = om.MVector.yAxis
zAx = om.MVector.zAxis
rad_to_deg = 57.2958
axisMapping = {
    0: om2.MVector(1, 0, 0),
    1: om2.MVector(0, 1, 0),
    2: om2.MVector(0, 0, 1)
}

# TEMP CONSTANTS
maxIterations = 30
timeScale = (1.0 / 30.0)
gravityF = -98.1
gravity = om2.MVector(0, gravityF * timeScale * timeScale, 0)
dgravity = om2.MVector(0, gravityF * timeScale * timeScale, 0)

title_str = 'tbPhysics '
import os

IconPath = os.path.abspath(os.path.join(os.path.dirname(getqss.__file__), 'Icons'))
print('IconPath', IconPath)


def has_attr(node, attr):
    """
    Replicates PyMEL's node.hasAttr() using maya.cmds.
    Returns True if the attribute exists on the given node.
    """
    return cmds.objExists(f"{node}.{attr}")



def easeOutCirc(x):
    return ((1 - (x - 1) ** 2) ** 0.5) if x <= 1 else 0


class EasingBase(object):
    limit = (0, 1)

    def __init__(self, start=0, end=1, duration=1):
        self.start = start
        self.end = end
        self.duration = duration

    def func(self, t=float):
        raise NotImplementedError

    def ease(self, alpha=float):
        t = self.limit[0] * (1 - alpha) + self.limit[1] * alpha
        t /= self.duration
        a = self.func(t)
        return self.end * a + self.start * (1 - a)

    def __call__(self, alpha=float):
        return self.ease(alpha)


"""
Linear
"""


class LinearInOut(EasingBase):
    def func(self, t=float):
        return t


"""
Quadratic easing functions
"""


class easeOutCirc(EasingBase):
    def func(self, t=float):
        return ((1 - (t - 1) ** 2) ** 0.5) if t <= 1 else 0


class easeInCirc(EasingBase):
    def func(self, t=float):
        return 1 - math.sqrt(1 - t ** 2)


class easeInOutQuint(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 16 * t ** 5
        else:
            return 1 - 0.5 * (2 - 2 * t) ** 5


class easeOutQuint(EasingBase):
    def func(self, t=float):
        return 1 - pow(1 - t, 5)


class easeInQuint(EasingBase):
    def func(self, t=float):
        return t ** 5


class easeInSine(EasingBase):
    def func(self, t=float):
        return 1 - math.cos((t * math.pi) / 2)


class easeOutSine(EasingBase):
    def func(self, t=float):
        return math.sin((t * math.pi) / 2)


class easeInOutSine(EasingBase):
    def func(self, t=float):
        return -(math.cos(math.pi * t) - 1) / 2


class easeInQuad(EasingBase):
    def func(self, t=float):
        return t * t


class easeOutQuad(EasingBase):
    def func(self, t=float):
        return 1 - (1 - t) * (1 - t)


class easeInOutQuad(EasingBase):
    def func(self, t=float):
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


class easeInCubic(EasingBase):
    def func(self, t=float):
        return t * t * t


class easeOutCubic(EasingBase):
    def func(self, t=float):
        return 1 - pow(1 - t, 3)


class easeInOutCubic(EasingBase):
    def func(self, t=float):
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


class easeInQuart(EasingBase):
    def func(self, t=float):
        return t * t * t * t


class easeOutQuart(EasingBase):
    def func(self, t=float):
        return 1 - pow(1 - t, 4)


class QuadEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 2 * t * t
        return (-2 * t * t) + (4 * t) - 1


class QuadEaseIn(EasingBase):
    def func(self, t=float):
        return t * t


class QuadEaseOut(EasingBase):
    def func(self, t=float):
        return -(t * (t - 2))


"""
Cubic easing functions
"""


class CubicEaseIn(EasingBase):
    def func(self, t=float):
        return t * t * t


class CubicEaseOut(EasingBase):
    def func(self, t=float):
        return (t - 1) * (t - 1) * (t - 1) + 1


class CubicEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 4 * t * t * t
        p = 2 * t - 2
        return 0.5 * p * p * p + 1


"""
Quartic easing functions
"""


class QuarticEaseIn(EasingBase):
    def func(self, t=float):
        return t * t * t * t


class QuarticEaseOut(EasingBase):
    def func(self, t=float):
        return (t - 1) * (t - 1) * (t - 1) * (1 - t) + 1


class QuarticEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 8 * t * t * t * t
        p = t - 1
        return -8 * p * p * p * p + 1


"""
Quintic easing functions
"""


class QuinticEaseIn(EasingBase):
    def func(self, t=float):
        return t * t * t * t * t


class QuinticEaseOut(EasingBase):
    def func(self, t=float):
        return (t - 1) * (t - 1) * (t - 1) * (t - 1) * (t - 1) + 1


class QuinticEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 16 * t * t * t * t * t
        p = (2 * t) - 2
        return 0.5 * p * p * p * p * p + 1


"""
Sine easing functions
"""


class SineEaseIn(EasingBase):
    def func(self, t=float):
        return math.sin((t - 1) * math.pi / 2) + 1


class SineEaseOut(EasingBase):
    def func(self, t=float):
        return math.sin(t * math.pi / 2)


class SineEaseInOut(EasingBase):
    def func(self, t=float):
        return 0.5 * (1 - math.cos(t * math.pi))


"""
Circular easing functions
"""


class CircularEaseIn(EasingBase):
    def func(self, t=float):
        return 1 - math.sqrt(1 - (t * t))


class CircularEaseOut(EasingBase):
    def func(self, t=float):
        return math.sqrt((2 - t) * t)


class CircularEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 0.5 * (1 - math.sqrt(1 - 4 * (t * t)))
        return 0.5 * (math.sqrt(-((2 * t) - 3) * ((2 * t) - 1)) + 1)


"""
Exponential easing functions
"""


class ExponentialEaseIn(EasingBase):
    def func(self, t=float):
        if t == 0:
            return 0
        return math.pow(2, 10 * (t - 1))


class ExponentialEaseOut(EasingBase):
    def func(self, t=float):
        if t == 1:
            return 1
        return 1 - math.pow(2, -10 * t)


class ExponentialEaseInOut(EasingBase):
    def func(self, t=float):
        if t == 0 or t == 1:
            return t

        if t < 0.5:
            return 0.5 * math.pow(2, (20 * t) - 10)
        return -0.5 * math.pow(2, (-20 * t) + 10) + 1


"""
Elastic Easing Functions
"""


class ElasticEaseIn(EasingBase):
    def func(self, t=float):
        return math.sin(13 * math.pi / 2 * t) * math.pow(2, 10 * (t - 1))


class ElasticEaseOut(EasingBase):
    def func(self, t=float):
        return math.sin(-13 * math.pi / 2 * (t + 1)) * math.pow(2, -10 * t) + 1


class ElasticEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return (
                    0.5
                    * math.sin(13 * math.pi / 2 * (2 * t))
                    * math.pow(2, 10 * ((2 * t) - 1))
            )
        return 0.5 * (
                math.sin(-13 * math.pi / 2 * ((2 * t - 1) + 1))
                * math.pow(2, -10 * (2 * t - 1))
                + 2
        )


"""
Back Easing Functions
"""


class BackEaseIn(EasingBase):
    def func(self, t=float):
        return t * t * t - t * math.sin(t * math.pi)


class BackEaseOut(EasingBase):
    def func(self, t=float):
        p = 1 - t
        return 1 - (p * p * p - p * math.sin(p * math.pi))


class BackEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            p = 2 * t
            return 0.5 * (p * p * p - p * math.sin(p * math.pi))

        p = 1 - (2 * t - 1)

        return 0.5 * (1 - (p * p * p - p * math.sin(p * math.pi))) + 0.5


"""
Bounce Easing Functions
"""


class BounceEaseIn(EasingBase):
    def func(self, t=float):
        return 1 - BounceEaseOut().func(1 - t)


class BounceEaseOut(EasingBase):
    def func(self, t=float):
        if t < 4 / 11:
            return 121 * t * t / 16
        elif t < 8 / 11:
            return (363 / 40.0 * t * t) - (99 / 10.0 * t) + 17 / 5.0
        elif t < 9 / 10:
            return (4356 / 361.0 * t * t) - (35442 / 1805.0 * t) + 16061 / 1805.0
        return (54 / 5.0 * t * t) - (513 / 25.0 * t) + 268 / 25.0


class BounceEaseInOut(EasingBase):
    def func(self, t=float):
        if t < 0.5:
            return 0.5 * BounceEaseIn().func(t * 2)
        return 0.5 * BounceEaseOut().func(t * 2 - 1) + 0.5


easeTypes = ['linear',
             'easeInOutQuint',
             'easeInOutCubic',
             'easeInOutQuad',
             'easeInOutSine',
             'easeInSine',
             'easeInCirc',
             'easeInCubic',
             'easeInQuart',
             'easeInQuint',
             'easeOutSine',
             'easeOutCirc',
             'easeOutCubic',
             'easeOutQuart',
             'easeOutQuint',
             ]

easeTypesDict = {'easeOutCirc': easeOutCirc,
                 'easeInCirc': easeInCirc,
                 'easeInOutQuint': easeInOutQuint,
                 'easeOutQuint': easeOutQuint,
                 'easeInQuint': easeInQuint,
                 'easeInSine': easeInSine,
                 'easeOutSine': easeOutSine,
                 'easeInOutSine': easeInOutSine,
                 'easeInQuad': easeInQuad,
                 'easeOutQuad': easeOutQuad,
                 'easeInOutQuad': easeInOutQuad,
                 'easeInCubic': easeInCubic,
                 'easeOutCubic': easeOutCubic,
                 'easeInOutCubic': easeInOutCubic,
                 'easeInQuart': easeInQuart,
                 'easeOutQuart': easeOutQuart,
                 'QuadEaseInOut': QuadEaseInOut,
                 'QuadEaseIn': QuadEaseIn,
                 'QuadEaseOut': QuadEaseOut,
                 'linear': LinearInOut,
                 }
c_chain = 'Chain'
c_points = 'Points'

mainAttributes = ['rx', 'ry', 'rz', 'sx', 'sy', 'sz']
physicsAttributes = [GRAVITY_SCALE, DAMPING, STIFFNESS, FRICTION, BOUNCE, BLEND, LOCKED]
stickAttributes = ['defaultLength']
copyConstraintOffset = {'TranslateX': 0,
                        'TranslateY': 0,
                        'TranslateZ': 0,
                        'RotateX': 0,
                        'RotateY': 0,
                        'RotateZ': 0,
                        }
easeTypeAttr = 'easeType'


class PhysicsRigData(object):
    def __init__(self):
        self.controls = dict()
        self.constraints = dict()

    def addNode(self, name):
        node = name
        niceName = namme.rsplit(":")[-1]
        userAttributes = cmds.listAttr(name, userDefined=True, keyable=True)
        attrs = cmds.listAttr(name, userDefined=False, keyable=True)
        finalAttributes = [a for a in mainAttributes if a not in physicsAttributes]
        if userAttributes:
            finalAttributes.extend(userAttributes)
        self.controls[str(niceName)] = {a: cmds.getAttr(node + '.' + a) for a in mainAttributes}

        constraintDict = self.getConstraint(name)
        if constraintDict:
            self.constraints[str(niceName)] = constraintDict

    def getConstraintNode(self, node):
        constraints = cmds.listRelatives(node, type='parentConstraint')
        if constraints:
            return constraints[0]
        return None

    def getConstraint(self, node):
        constraintNode = self.getConstraintNode(node)
        if constraintNode:
            return self.cacheConstraint(constraintNode)
        return None

    def cacheConstraint(self, constraint):
        constraintOffset = dict()

        for key in copyConstraintOffset.keys():
            constraintOffset[key] = cmds.getAttr(constraint + '.target[0].targetOffset' + key)
        return constraintOffset

    def applyToAllNodes(self, namespace):
        for control in self.controls.keys():
            # print ('control', control)
            node = namespace + ':' + control
            if not cmds.objExists(node):
                continue
            self.applyToNode(node, self.controls)
        # print ('self.constraints', self.constraints)
        for constraint in self.constraints.keys():
            node = namespace + ':' + constraint
            # print ('node', node)
            if not cmds.objExists(node):
                continue
            constraint = self.getConstraintNode(node)
            # print('constraint', constraint)
            self.applyToConstraint(node.rsplit(':')[-1], constraint, self.constraints)

    def applyToNode(self, node, targetDict, attrPrefix=str()):
        c = node.split(':')[-1]
        if c not in targetDict.keys():
            return
        for attr, value in targetDict[c].items():
            if not cmds.attributeQuery(attr, node=node, exists=True):
                continue
            if cmds.attributeQuery(attr, node=node, keyable=True):
                try:
                    cmds.setAttr(node + '.' + attrPrefix + attr, value)
                except:
                    cmds.warning('unable to set attribute, ', node + '.' + attrPrefix + attr)
                    continue

    def applyToConstraint(self, key, node, targetDict):
        c = key.split(':')[-1]
        if c not in targetDict.keys():
            return
        for attr, value in targetDict[key].items():
            try:
                cmds.setAttr(node + '.' + constraintAttrPrefix + attr, value)
            except:
                cmds.warning('unable to set attribute, ', node + '.' + constraintAttrPrefix + attr)
                continue

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict = {k: self.__dict__[k] for k in self.__dict__.keys() if k not in returnDict.keys()}
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))
        for control, data in rawJsonData.get('controls', dict()).items():
            self.controls[control] = dict()
            for k, v in data.items():
                self.controls[control][k] = v
        for constraint, data in rawJsonData.get('constraints', dict()).items():
            self.constraints[constraint] = dict()
            for k, v in data.items():
                self.constraints[constraint][k] = v


class PhysicsPresetData(object):
    def __init__(self):
        self.chains = dict()  # group name as key, paqrent as value
        self.twistChains = dict()
        self.points = dict()  # group as key, controls as values
        self.pointTwists = dict()  # group as key, controls as values
        self.sticks = dict()  # group as key, controls as values
        self.attributes = dict()
        self._fileName = str()

    def saveData(self, dataFile):
        # print ('dataFile', dataFile)
        fileName = os.path.join(dataFile)
        # TODO - strip out namespace here
        jsonString = json.dumps(self.toJson(), indent=4, separators=(',', ': '))
        jsonFile = open(fileName, 'w')

        jsonFile.write(jsonString)
        jsonFile.close()

    def toJson(self):
        jsonData = '''{}'''
        classData = json.loads(jsonData)
        for key, values in self.__dict__.items():
            if key.startswith('_'):
                continue
            classData[key] = values
        return classData

    def load(self, dataFile):
        jsonObjectInfo = json.load(open(dataFile))
        for key in jsonObjectInfo.keys():
            self.__dict__[key] = jsonObjectInfo[key]
        self._fileName = dataFile

    def removeOverlappingEntry(self, digitName, finalValues):
        valuesSet = set(finalValues)
        overlappingEntries = list()
        for key, value in self.collisionEntries.items():
            for k, v in value.items():
                s1 = set(v)
                if valuesSet.intersection(s1):
                    overlappingEntries.append(key)
        if overlappingEntries:
            raiseOk('Found some overlaps',
                    title='Duplicate Entry')
        if digitName in self.collisionEntries.keys():
            raiseOk('An entry containing these controls already exists, the existing entry has been replaced',
                    title='Duplicate Entry')
        return overlappingEntries

    def addNewDigit(self, groupName, name, collisionType, inputList=list(), mainControl=None):
        # print ('addNewDigit', groupName, name, collisionType, inputList)
        if not inputList:
            sel = cmds.ls(sl=True)
        else:
            sel = inputList
        if not sel or len(sel) < 2:
            self.collisionEntries[name] = {
                'mainControl': str(),  # the moving parent object (in legacy mode)
                'baseControl': str(),  # offset target (in legacy mode)
                'controls': list()  # list of controls that make up the local matrix
            }
        else:
            if not mainControl:
                mainControl = sel[0].split(':')[-1]
            self.collisionEntries[name] = {
                'mainControl': mainControl,
                'baseControl': sel[0].split(':')[-1],
                'controls': [x.split(':')[-1] for x in sel]
            }
        for key, value in self.collisionGroups.items():
            if name in value:
                self.collisionGroups[key].remove(name)
        if groupName not in self.collisionGroups.keys():
            self.collisionGroups[groupName] = list()
        self.collisionGroups[groupName].append(name)
        self.collisionTypes[name] = collisionType

    def reparentEntry(self, key, groupName):
        # print ('reparentEntry', key, groupName)
        for k, value in self.collisionGroups.items():
            if key in value:
                self.collisionGroups[k].remove(key)
        self.collisionGroups[groupName].append(key)

    def removeItem(self, key):
        self.collisionEntries.pop(key)
        for k, value in self.collisionGroups.items():
            if key in value:
                self.collisionGroups[k].remove(key)
                self.collisionTypes.pop(key)

    def removeGroup(self, key):
        if key not in self.collisionGroups.keys():
            return cmds.warning('Attempting to remove a group that does not seem to exist')

        for value in self.collisionGroups[key]:
            self.collisionEntries.pop(value)
        self.collisionGroups.pop(key)

    def validateContents(self, ns):
        # print ('collisionEntries', self.collisionEntries.values())
        if not list(self.collisionEntries.values()):
            return raiseError(maya.stringTable['y_tb_physicsTool.createErrorNoData'],
                              title=maya.stringTable['y_tb_physicsTool.createErrorNoDataTitle'])
        for key, value in self.collisionEntries.items():
            for control in value['controls']:
                if not cmds.objExists(ns + ':' + control):
                    return raiseError("Object from preset not found {o}".format(o=ns + ':' + control),
                                      title='Missing object in scene')
        return True


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory('tbtools_blank')
        self.addCommand(self.tb_hkey(name='blank',
                                     annotation='useful comment',
                                     category=self.category, command=['tbPhysicsTool.command()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class PhysicsTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'tbPhysicsTool'
    hotkeyClass = hotkeys()
    funcs = Functions()

    productID = 'ppPjq'
    version = 1.01

    loadedRigData = dict()

    mainFolder = 'physicsTools'
    presetFolder = 'physicsPresets'
    rigDataFolder = 'physicsRigData'
    toolbox = None
    cycleState = False
    fileHint = "Physics Preset files (*.json)"

    pointData = dict()
    stickData = dict()
    axisList = list()
    rotationList = list()
    chainPhysicsControls = dict()
    constrainTargetDict = dict()
    constrainTargetDict = dict()

    controlConstraintDict = dict()

    def __new__(cls):
        if PhysicsTool.__instance is None:
            PhysicsTool.__instance = object.__new__(cls)

        PhysicsTool.__instance.val = cls.toolName
        PhysicsTool.__instance.loadData()

        return PhysicsTool.__instance


    def initData(self):
        super(PhysicsTool, self).initData()
        self.mainDir = os.path.normpath(os.path.join(self.dataPath, self.mainFolder))
        self.presetDir = os.path.normpath(os.path.join(self.dataPath, self.mainFolder, self.presetFolder))
        self.rigDataDir = os.path.normpath(os.path.join(self.dataPath, self.mainFolder, self.rigDataFolder))
        if not os.path.isdir(self.mainDir):
            os.mkdir(self.mainDir)
        if not os.path.isdir(self.presetDir):
            os.mkdir(self.presetDir)
        if not os.path.isdir(self.rigDataDir):
            os.mkdir(self.rigDataDir)

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def setToComplimentaryColour(self, ref, control, complimentary=True, brightnessOffset=0):
        """
        Copies the colour override from ref to control
        :param ref:
        :param control:
        :return:
        """
        node = ref
        control = ref
        refObj = node
        overrideState = cmds.getAttr(node + ".overrideEnabled")
        if not overrideState:
            shape = self.funcs.getShape(node)
            if shape:
                overrideState = cmds.getAttr(shape + ".overrideEnabled")
                if overrideState:
                    refObj = shape
        cmds.setAttr(control + ".overrideEnabled", True)
        if not cmds.getAttr(refObj + ".overrideRGBColors"):

            if cmds.getAttr(refObj + ".overrideColor") == 0:
                rgbColour = [125, 125, 125]
            else:
                rgbColour = [x * 255 for x in cmds.colorIndex(cmds.getAttr(refObj + ".overrideColor"), q=True)]
        else:
            rgbColour = [x * 255 for x in cmds.getAttr(refObj + ".overrideColorRGB")]

        if complimentary:
            rgbColourOut = [255 - rgbColour[0], 255 - rgbColour[1], 255 - rgbColour[2]]
        else:
            rgbColourOut = [rgbColour[0], rgbColour[1], rgbColour[2]]
        rgbColourOut = self.funcs.adjust_color_lightness(rgbColourOut[0], rgbColourOut[1], rgbColourOut[2],
                                                         1 + brightnessOffset)
        rgbColourOut = [x / 255.0 for x in rgbColourOut]
        cmds.setAttr(control + ".overrideColorRGB", rgbColourOut)

        cmds.setAttr(control + ".overrideRGBColors", True)
        # control.overrideColor.set(refObj.overrideColor.get())
        for s in self.funcs.getShapes(control):
            cmds.setAttr(s + ".overrideEnabled", 0)

    def getCurrentRig(self, sel=None):
        """
        Gets the name of the rig file for the selection/namespace
        TODO - make it actually find the rig!!!!

        :param sel:
        :return:
        """

        refName = None
        mapName = None
        fname = None
        if sel is None:
            sel = cmds.ls(sl=True)
        namespace = str()
        if not sel:
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
            return refName, namespace
        s = str(sel[0])
        ps = s
        # TODO fix this for single chains
        refState = cmds.referenceQuery(s, isNodeReferenced=True)
        topParent = find_top_parent(s)
        control = None
        if not refState:
            # check if the control is a physics control
            if topParent == self.getPhysicsRoot():
                # see if it is a stick
                if has_attr(ps, 'pointA'):
                    conns = (cmds.listConnections(ps +".pointA", source=True, destination=False))
                    if conns:
                        ps = conns[0]
                while control is None:
                    if has_attr(ps, 'control'):
                        conns = (cmds.listConnections(ps + ".control", source=True, destination=False))
                        if conns:
                            control = conns[0]
                            break
                    ps = ps.getParent()
                    if ps == self.getPhysicsRoot():
                        control = 'failed'
        if control != 'failed':
            s = str(control)
            refState = cmds.referenceQuery(s, isNodeReferenced=True)
        if refState:
            # if it is referenced, check against pickwalk library entries
            refName = cmds.referenceQuery(s, filename=True, shortName=True).split('.')[0]
        else:
            # might just be working in the rig file itself
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        if ':' in s:
            namespace = s.split(':', 1)[0]
        return refName, namespace  # TODO - fix up data path etc

    def splitSelectionToCharacters(self, sel):
        """
        Returns a dictionary for all characters found in the selection, namespace as key, controls as items
        :param sel:
        :return:
        """
        if not sel:
            return

        # split selection by character
        sel = [x for x in sel if x is not None]
        namespaces = [x.split(':', 1)[0] for x in sel if ':' in x]

        characters = {k: list() for k in namespaces}
        for s in sel:
            splitString = s.split(':', 1)
            if len(splitString) == 1:
                if ('') not in characters.keys():
                    characters[''] = list()
                characters[''].append(s)
                continue
            for ns in namespaces:
                if splitString[0] == ns:
                    characters[ns].append(s)
                    continue
        return characters

    def loadDataForCharacters(self, characters):
        self.namespaceToCharDict = dict()
        for key, value in characters.items():
            # this appears to be broken
            refname, namespace = self.getCurrentRig([value[0]])
            self.namespaceToCharDict[namespace] = refname
            if refname not in self.loadedRigData.keys():
                collisionRigData = self.loadRigData(PhysicsRigData(), refname)
                self.loadedRigData[refname] = collisionRigData
        return self.namespaceToCharDict

    def restoreCurrentRigData(self, sel=list()):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return raiseError(
                'Unable to restore collision tip offsets. Please select part of the rig you wish to restore the collision poses for',
                title='No objects selected')
        namespace = self.funcs.namespace(sel[0])
        # print ('Selected namespace', namespace)
        characters = self.splitSelectionToCharacters(sel)
        self.namespaceToCharDict = self.loadDataForCharacters(characters)
        # print ('self.namespaceToCharDict', self.namespaceToCharDict)

        refName = self.namespaceToCharDict[namespace]
        self.loadedRigData[refName].applyToAllNodes(namespace)

    def saveCurrentRigData(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return raiseError(
                'Unable to store collision tip offsets. Please select part of the rig you wish to save the collision poses for',
                title='No objects selected')

        """
        Find all physics controls in scene
        Sort by rig
        
        """
        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        # physicsNodes = [c for c in allNodes if 'PhysicsNodes' in str(c)]

        characters = self.splitSelectionToCharacters(sel)
        self.namespaceToCharDict = self.loadDataForCharacters(characters)

        for namespace, character in self.namespaceToCharDict.items():
            controls = self.getAllPhysicsControls(namespace)
            for c in controls:
                self.loadedRigData[character].addNode(c)

            self.saveRigData(character, self.loadedRigData[character])
        # print (self.loadedRigData)
        return
        assets = cmds.ls(type='container')

        assets = [a for a in assets if cmds.attributeQuery(self.collisionAssetAttr, node=a, exists=True)]
        # print ('assets', assets)
        allNodes = list()
        if not assets:
            return
        for a in assets:
            nodes = cmds.ls(cmds.container(a, query=True, nodeList=True), transforms=True)
            allNodes.extend(nodes)
        # print ('allNodes', allNodes)

        if not allNodes:
            return cmds.warning('nothing selected')
        characters = self.splitSelectionToCharacters(allNodes)
        # print ('characters', characters)

        if not characters:
            return

        namespace = self.namespace(sel[0])
        if namespace.endswith(':'):
            namespace = namespace.rsplit(':', 1)
        # print ('Selected namespace', namespace)
        self.namespaceToCharDict = self.loadDataForCharacters(characters)
        # print ('self.namespaceToCharDict', self.namespaceToCharDict)

        refName = self.namespaceToCharDict[namespace]
        # print ('refName', refName)
        data = self.loadedRigData[refName]
        for node in characters[namespace]:
            data.addNode(node)
        self.saveRigData(refName, data)

        '''
        for character, nodes in characters.items():
            refName = self.namespaceToCharDict[character]
            data = self.loadedRigData[refName]
            for node in nodes:
                data.addNode(node)
            self.saveRigData(refName, data)
        '''
        """
        Look at all collision assets in the scene, find matching namespaces, don't bother with selection
        save out each name of each object in the collision assets to the data file
        data loaded on creation of new collisions from apply preset or new ui ones
        """
        raiseOk('Collision tip offsets successfully stored for {o}'.format(o=refName), title='Success')

    def saveRigFileIfNew(self, refname):
        # print ('saveRigFileIfNew', refname)
        dataFile = os.path.join(self.rigDataDir, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            collisionRigData = PhysicsRigData()
            data = collisionRigData.toJson()
            self.saveJsonFile(dataFile, json.loads(data))

    def saveRigData(self, refname, dataCLS):
        dataFile = os.path.join(self.rigDataDir, refname + '.json')
        self.saveJsonFile(dataFile, json.loads(dataCLS.toJson()))

    def loadRigData(self, dataCLS, rigName):
        self.saveRigFileIfNew(rigName)
        dataCLS.fromJson(os.path.join(self.rigDataDir, rigName + '.json'))
        return dataCLS

    def applyPresetFromFile(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return raiseError('Please select part of the rig to apply a collision preset to.',
                              title='Cannot load preset')
        win = FingerCollisionSetupUI(self)
        win.applyPreset()

    def optionUI(self):
        super(PhysicsTool, self).optionUI()
        return self.optionWidget

    def showUI(self):
        win = PhysicsQuickUI(self)
        win.show()
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def duplicateWithSuffix(self, node, suffix='suffix'):
        cmds.namespace(setNamespace=':')
        outNode = cmds.rename(cmds.duplicate(node, parentOnly=True)[0], node + '_' + suffix)
        cmds.setAttr(outNode + '.displayLocalAxis', 1)
        userAttrs = cmds.listAttr(outNode, userDefined=True)
        for a in userAttrs:
            cmds.deleteAttr(outNode + '.' + a)
        return outNode

    @staticmethod
    def getMDagPath(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDagPath(0)

    @staticmethod
    def getMObject(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDependNode(0)

    @staticmethod
    def getMFnCurveFromPlug(plug):
        omslist = om2.MSelectionList()
        omslist.add(plug)
        mplug = omslist.getPlug(0)
        mcurve = oma2.MFnAnimCurve(mplug)

        return mplug, mcurve

    @staticmethod
    def getMfnCurveValues(mfnCurve, mTimeArray):
        return [mfnCurve.evaluate(m) for m in mTimeArray]

    @staticmethod
    def getMfnCurveKeyValues(mfnCurve):
        # keyValues = accumulateProgress([mcurve.value(x) for x in range(mcurve.numKeys)])
        return [mfnCurve.value(x) for x in range(mfnCurve.numKeys)]

    @staticmethod
    def lerp(start, end, t):
        return start + (end - start) * t

    def lerp_loop(self, start, end, count):
        if count <= 1:
            return [self.lerp(start, end, 0.5)]

        step = 1 / (count - 1)
        lerp_values = []
        for i in range(count):
            t = i * step
            lerp_values.append(self.lerp(start, end, t))
        return lerp_values

    def evaluateMfnCurveKeyValues(self, mfnCurve, offset, startTime, endTime, count):
        # keyValues = accumulateProgress([mcurve.value(x) for x in range(mcurve.numKeys)])
        mTimeArrary = self.createMTimeArray(int(startTime), int(endTime - startTime) + 1, offset=offset)
        return self.getMfnCurveValues(mfnCurve, mTimeArrary)

    def evaluatePlugCurveValues(self, plugName, offset, startTime, endTime, count):
        plug, curve = self.getMFnCurveFromPlug(plugName)
        # print ('getPlugCurveValues', plug, curve)
        return self.evaluateMfnCurveKeyValues(curve, offset, startTime, endTime, count)

    def getPlugCurveValues(self, plugName):
        plug, curve = self.getMFnCurveFromPlug(plugName)
        # print ('getPlugCurveValues', plug, curve)
        return self.getMfnCurveKeyValues(curve)

    def getTranslationCurveValues(self, obj):
        # print ('getTranslationCurveValues', obj)
        MFnCurveDict = dict()
        for attribute in ['tx', 'ty', 'tz']:
            plugName = obj + '.' + attribute
            # print ('plugName', plugName)
            if not plugName:
                continue
            MFnCurveDict[attribute] = self.getPlugCurveValues(plugName)
        return MFnCurveDict

    def getAllTranslateValues(self, obj):
        """
        Get all the translation values from the bakes keys
        :param obj:
        :return:
        """
        return [om2.MVector(x, y, z) for x, y, z in zip(self.getPlugCurveValues(obj + '.tx'),
                                                        self.getPlugCurveValues(obj + '.ty'),
                                                        self.getPlugCurveValues(obj + '.tz'))]

    def evaluateAllTranslateValues(self, obj, offset, startTime, endTime):
        """
        Get all the translation values from the bakes keys
        :param obj:
        :return:
        """
        translateX = self.getAnimatedProperty(obj, 'translateX', startTime, endTime, offset)
        translateY = self.getAnimatedProperty(obj, 'translateY', startTime, endTime, offset)
        translateZ = self.getAnimatedProperty(obj, 'translateZ', startTime, endTime, offset)
        return [om2.MVector(x, y, z) for x, y, z in
                zip(translateX,
                    translateY,
                    translateZ)]

    def createMTimeArray(self, initialFrame, count, offset=0):
        mTimeArray = om2.MTimeArray(count, om2.MTime())
        for x in range(count):
            mTimeArray[x] = om2.MTime(initialFrame + x + offset, om2.MTime.uiUnit())
        return mTimeArray

    def getPhysicsRoot(self):
        """
        Create the main physics asset if it's not there
        :return:
        """
        if not cmds.objExists(tbPhyics + '_Main'):
            return str(self.funcs.tempControl(name=tbPhyics, suffix='Main', scale=1))
        return tbPhyics + '_Main'

    def getPhysicsData(self):
        """
        Create the main physics asset if it's not there
        :return:
        """
        if not cmds.objExists(tbPhyics + '_Data'):
            dataNode = str(cmds.createNode('network', name=tbPhyics + '_Data'))
        else:
            dataNode = tbPhyics + '_Data'
        if not cmds.attributeQuery('cycle', node=dataNode, exists=True):
            cmds.addAttr(dataNode, ln='cycle', at='bool')
        return tbPhyics + '_Data'

    def createPhysicsControl(self, target=str(), twist=False, parent=None):
        control = target
        shortName = control.stripNamespace()
        namespace = control.namespace()

        pointName = namespace + 'point_' + shortName
        rotationName = namespace + 'twist_' + shortName
        physControl = self.makeAttributeHolder(name=pointName,
                                               target=target,
                                               mainControl=parent,
                                               constrainTo=target,
                                               scale=0.05,
                                               type='diamond')

        self.setToComplimentaryColour(target, physControl, complimentary=False, brightnessOffset=0.1)

        self.tagControl(physControl, target)
        if twist:
            twistControl = self.makeAttributeHolder(name=rotationName,
                                                    target=target,
                                                    mainControl=physControl,
                                                    type='pin',
                                                    scale=0.05)
            self.setToComplimentaryColour(target, twistControl, brightnessOffset=0.1)
        else:
            twistControl = None

        return physControl, twistControl

    def createPhysicsRotationControl(self, target=str(), rotation=False, parent=None):
        control = target
        shortName = control.stripNamespace()
        namespace = control.namespace()

        pointName = namespace + 'point_' + shortName
        rotationName = namespace + 'rotation_' + shortName

        physControl = self.makeAttributeHolder(name=pointName,
                                               target=target,
                                               mainControl=parent,
                                               constrainTo=target,
                                               scale=0.1)

        self.tagControl(physControl, target)
        if rotation:
            twistControl = self.makeAttributeHolder(name=rotationName,
                                                    target=target,
                                                    mainControl=physControl,
                                                    type='pin',
                                                    scale=0.1)
            cmds.setAttr(twistControl + '.' + GRAVITY_SCALE, 0)
            cmds.setAttr(twistControl + '.' + GRAVITY_SCALE, edit=True, keyable=False)
        else:
            twistControl = None

        return physControl, twistControl

    def matrixOrientConstraint(self, root, axisList, target):
        fbfm = cmds.createNode('fourByFourMatrix', skipSelect=True)
        decomp = cmds.createNode('decomposeMatrix', skipSelect=True)

        for index, a in enumerate(axisList):
            pma = cmds.createNode('plusMinusAverage', skipSelect=True)
            cmds.setAttr(pma + '.operation', 2)
            cmds.connectAttr(a + '.translate', pma + '.input3D[0]')
            cmds.connectAttr(root + '.translate', pma + '.input3D[1]')

            cmds.connectAttr(pma + '.output3Dx', fbfm + '.in%s0' % index)
            cmds.connectAttr(pma + '.output3Dy', fbfm + '.in%s1' % index)
            cmds.connectAttr(pma + '.output3Dz', fbfm + '.in%s2' % index)

        cmds.connectAttr(fbfm + '.output', decomp + '.inputMatrix')
        cmds.connectAttr(decomp + '.outputRotate', target + '.rotate')

    def tagControl(self, physControl, target):
        cmds.addAttr(physControl, ln='control', at='message')
        cmds.connectAttr(target + '.message', physControl + '.control')

    def updateOffsets(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            constraints = cmds.listRelatives(s, type='parentConstraint')
            if not constraints:
                continue
            targetList = cmds.parentConstraint(constraints[0], query=True, targetList=True)
            cmds.parentConstraint(targetList, constraints[0], edit=True, maintainOffset=True)

    def selectChain(self, chainName=str()):
        controls = cmds.listRelatives(chainName, type='transform', children=True)
        controls = [c for c in controls if 'stick' not in c]
        modifiers = QApplication.keyboardModifiers()
        add = modifiers == Qt.ControlModifier
        cmds.select(controls, add=add)

    def editChainFalloff(self, chainName, inputDict):
        """
        Set the chain settings from the quick ui, redo of the function below as it's kinda crap
        :param chainName:
        :param inputDict:
        :return:
        """
        points = self.getPoints(chainName)
        # stiffness
        cmds.setAttr(chainName + '.' + easeTypeAttr, inputDict.get('falloffType'), type='string')
        self.setEaseAlongChain('startStiffness', 'endStiffness', 'falloffType', inputDict, points, STIFFNESS)
        self.setEaseAlongChain('startDamp', 'endDamp', 'falloffType', inputDict, points, DAMPING)
        self.setEaseAlongChain('startDelay', 'endDelay', 'falloffType', inputDict, points, FRAME_DELAY)

    def setEaseAlongChain(self, startKey, endKey, falloffType, inputDict, points, attr):
        startStiffness = inputDict.get(startKey)
        endStiffness = inputDict.get(endKey)

        easefunc = easeTypesDict[inputDict.get(falloffType)](start=startStiffness, end=endStiffness)
        alphas = self.getTotalDistance(points)
        for index, s in enumerate(points):
            value = easefunc.ease(alphas[index])
            try:
                cmds.setAttr(s + '.' + attr, value)
            except:
                cmds.warning('failed to set stiffness attr on', s)

    def setFalloff(self, startValue=0.5, endValue=0.1, falloffType=easeTypes[0], sel=None, attribute=STIFFNESS,
                   skipFirst=False):
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('please select at least one physics control')
        if not cmds.attributeQuery(STIFFNESS, node=sel[0], exists=True):
            return cmds.warning('please select at least one physics control')
        if len(sel) == 1:
            parent = cmds.listRelatives(sel[0], parent=True)[0]
            if parent.endswith('Chain'):

                sel = cmds.listRelatives(parent)
                sel = [s for s in sel if s.split(':')[-1].startswith('point')]

                if skipFirst:
                    sel = sel[1:]
        easefunc = easeTypesDict[falloffType](start=startValue, end=endValue)
        alphas = self.getTotalDistance(sel)
        for index, s in enumerate(sel):
            value = easefunc.ease(alphas[index])
            try:
                cmds.setAttr(s + '.' + attribute, value)
            except:
                cmds.warning('failed to set stiffness attr on', s)

    def getTotalDistance(self, nodeList):
        xforms = [om2.MVector(cmds.xform(x, query=True, rotatePivot=True, worldSpace=True)) for x in nodeList]

        distances = [om2.MVector(x - xforms[max(xforms.index(x) - 1, 0)]).length() for x in xforms]
        cumulativeDistance = list()
        for index, x in enumerate(distances):
            cumulativeDistance.append(sum(distances[:index + 1]))
        totalDistance = sum(distances)
        alphas = [d / totalDistance for d in cumulativeDistance]

        return alphas

    def buildPointControls(self, controlList=list(), rotation=False):
        with self.undoChunk():
            mainControl = str(self.funcs.tempNull(name=controlList[0] + '_Controls', suffix=c_points))
            cmds.parent(mainControl, self.getPhysicsRoot())

            physControlList = list()
            twistControlList = list()
            stickList = list()
            for index, x in enumerate(controlList):

                physControl, rotationControl = self.createPhysicsRotationControl(target=x, rotation=rotation,
                                                                                 parent=mainControl)
                physControlList.append(physControl)
                twistControlList.append(rotationControl)
                if rotation:
                    self.connectTwistControl(physControl, rotationControl)

        pass

    def buildChainControls(self,
                           controlList=list(),
                           twist=False,
                           upAxis='y',
                           lockFirst=False,
                           startStiffness=0.5,
                           endStiffness=0.1,
                           startDamp=0.1,
                           endDamp=0.1,
                           frameDelay=5,
                           falloffType='linear'):

        with self.undoChunk():
            mainControl = str(self.funcs.tempNull(name=controlList[0] + '_Controls', suffix=c_chain))
            # add string attribute to hold the falloff type
            cmds.addAttr(mainControl, ln=easeTypeAttr, dt='string')
            cmds.setAttr(mainControl + '.' + easeTypeAttr, falloffType, type='string')
            # parent the control to physics root
            cmds.parent(mainControl, self.getPhysicsRoot())
            physControlList = list()
            twistControlList = list()
            stickList = list()
            for index, x in enumerate(controlList):
                physControl, twistControl = self.createPhysicsControl(target=x, twist=twist, parent=mainControl)
                physControlList.append(physControl)
                twistControlList.append(twistControl)
                if not twist:
                    continue
                self.connectTwistControl(physControl, twistControl)

            cmds.setAttr(str(physControlList[0]) + '.Locked', lockFirst)
            control = controlList[-1]
            shortName = control.stripNamespace()
            namespace = control.namespace()

            pointName = namespace + 'point_end' + shortName

            physControl = self.makeAttributeHolder(name=pointName,
                                                   target=controlList[-1],
                                                   mainControl=mainControl,
                                                   constrainTo=None,
                                                   suffix=control,
                                                   scale=0.1)
            physControlList.append(physControl)
            posA = om2.MVector(cmds.xform(controlList[-1], query=True, worldSpace=True,
                                          # translation=True,
                                          rotatePivot=True))
            if len(controlList) == 1:
                omAxis = {'x': om.MVector.xAxis,
                          'y': om.MVector.yAxis,
                          'z': om.MVector.zAxis}

                offset = self.getLocalVector(controlList[-1], vec=omAxis[upAxis], mult=10)
                posB = posA + offset
            else:
                posB = om2.MVector(cmds.xform(controlList[-2], query=True, worldSpace=True,
                                              # translation=True,
                                              rotatePivot=True))
            pos = posA - (posB - posA)
            target = controlList[-1]

            cmds.xform(physControl, translation=pos)
            cmds.parentConstraint(controlList[-1], physControl, maintainOffset=True)
            # create sitcks
            for x in range(len(physControlList) - 1):
                stickList.append(self.createStick(physControlList[x], physControlList[x + 1]))
                self.connectNextChain(physControlList[x], physControlList[x + 1])
            cmds.parent(stickList, mainControl)

            self.restoreCurrentRigData(sel=physControlList + twistControlList)
            self.setFalloff(sel=physControlList,
                            startValue=startStiffness,
                            endValue=endStiffness,
                            falloffType=falloffType,
                            attribute=STIFFNESS,
                            skipFirst=False)
            # set the damping
            self.setFalloff(sel=physControlList,
                            startValue=startDamp,
                            endValue=endDamp,
                            falloffType=falloffType,
                            attribute=DAMPING,
                            skipFirst=False)
            # set the falloff for the frame delay
            self.setFalloff(sel=physControlList,
                            startValue=0,
                            endValue=frameDelay,
                            falloffType=falloffType,
                            attribute=FRAME_DELAY,
                            skipFirst=False)
            return physControlList, twistControlList

    def buildSimpleAim(self, sel, twist=False):
        if not sel:
            return
        for s in sel:
            self.buildChainControls([s], twist=twist)

    @contextmanager
    def undoChunk(self):
        cmds.undoInfo(openChunk=True)

        yield

        cmds.undoInfo(closeChunk=True)

    def connectNextChain(self, pointA, pointB):
        cmds.addAttr(pointA, ln='next', at='message')
        cmds.connectAttr(pointB + '.message', pointA + '.next')

    def connectTwistControl(self, base, twist):
        cmds.addAttr(base, ln='twist', at='message')
        cmds.connectAttr(twist + '.message', base + '.twist')

    def createStick(self, pointA, pointB):
        controlA = pointA
        controlB = pointB
        shortNameA = controlA.stripNamespace()
        namespaceA = controlA.namespace()
        shortNameB = controlB.stripNamespace()
        namespaceB = controlB.namespace()

        sitckName = namespaceA + 'stick_' + shortNameA + '_' + shortNameB
        pointAPos = om2.MVector(cmds.xform(pointA, query=True, translation=True))
        pointBPos = om2.MVector(cmds.xform(pointB, query=True, translation=True))
        distance = (pointAPos - pointBPos).length()
        curve = cmds.curve(name=sitckName, d=3, p=[pointAPos, pointBPos], k=[0, 0, 1, 1])

        cmds.addAttr(curve, ln='defaultLength', at='float')
        cmds.setAttr(curve + '.' + 'defaultLength', edit=True, channelBox=True)
        cmds.setAttr(curve + '.' + 'defaultLength', distance)
        cmds.connectAttr(pointA + '.translate', curve.getShape() + ".controlPoints[0]")
        cmds.connectAttr(pointB + '.translate', curve.getShape() + ".controlPoints[1]")
        cmds.addAttr(curve, ln='pointA', at='message')
        cmds.connectAttr(pointA + '.message', curve + '.pointA')
        cmds.addAttr(curve, ln='pointB', at='message')
        cmds.connectAttr(pointB + '.message', curve + '.pointB')

        return curve

    def hasTwist(self, point):
        children = cmds.listRelatives(point, children=True, type='transform')
        if not children:
            return False
        if any(x.rsplit(':', 1)[-1].startswith('twist') for x in children):
            return True
        return False

    def hasRotation(self, point):
        children = cmds.listRelatives(point, children=True, type='transform')

        if not children:
            return False
        if any(x.rsplit(':', 1)[-1].startswith('rotation') for x in children):
            return [x for x in children if x.rsplit(':', 1)[-1].startswith('rotation')][0]
        return False

    def getChains(self, chainRoot):
        children = cmds.listRelatives(chainRoot, children=True, type='transform')
        return [x for x in children if str(x).split(':')[-1].startswith('point')]

    def getPoints(self, chainRoot):
        children = cmds.listRelatives(chainRoot, children=True, type='transform')
        return [x for x in children if str(x).split(':')[-1].startswith('point')]

    def getControls(self, points):
        controls = list()
        for x in points:
            if not cmds.attributeQuery('control', node=x, exists=True):
                continue
            controls.append(cmds.listConnections(x + '.control')[0])
        return controls

    def getPhysicsControlFromAnimControl(self, animControl):
        connections = cmds.listConnections(animControl + '.message', source=False, destination=True)
        if not connections:
            return None
        for c in connections:
            if not cmds.attributeQuery('control', node=c, exists=True):
                continue
            return c

    def getResultNodesFromMain(self, animControl):
        connections = cmds.listConnections(animControl + '.message', source=False, destination=True)
        if not connections:
            return None
        for c in connections:
            if not cmds.attributeQuery('PhysicsNodes', node=c, exists=True):
                continue
            return c

    def getTwists(self, chainPoints):
        twists = list()
        for x in chainPoints:
            children = cmds.listRelatives(x, children=True, type='transform')
            if not children:
                continue
            children = [x for x in children if 'Constraint' not in cmds.objectType(x)]
            if not children:
                continue
            twists.append(children[0])
        return twists

    def getSticks(self, chainRoot):
        children = cmds.listRelatives(chainRoot, children=True, type='transform')
        return [x for x in children if str(x).split(':')[-1].startswith('stick')]

    def buildLocatorsFromScene(self):
        chains = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        if not chains:
            return
        physicsNodes = [c for c in chains if 'PhysicsNodes' in str(c)]
        chainNodes = [c for c in chains if str(c).endswith(c_chain)]
        pointNodes = [c for c in chains if str(c).endswith(c_points)]

        if physicsNodes:
            cmds.delete(physicsNodes)

        for chain in chainNodes:
            chainPoints = self.getChains(chain)

            twistState = self.hasTwist(chainPoints[0])

            self.buildChainLocators(controlList=chainPoints, twist=twistState)

        for point in pointNodes:
            chainPoints = self.getChains(point)
            self.buildPointLocators(chainPoints)

    def buildChainLocators(self, controlList=list(), twist=False):
        """
        Create the nodes for baking and applying the results to
        :param controlList:
        :return:
        """

        mainControl = str(self.funcs.tempNull(name=controlList[0], suffix='PhysicsNodes'))
        self.connectResultToMainGroup(controlList, mainControl)
        cmds.parent(mainControl, self.getPhysicsRoot())
        # make the bake targets

        chainPointsLocs, chainRoots, chainUpLocs, aimAxis, upAxis = self.placeChainLocators(controlList,
                                                                                            parent=mainControl,
                                                                                            twist=twist)

        # make the result nodes

        chainPointsLocsResult = [x + '_Result' for x in chainPointsLocs]
        if twist:
            chainRootsResult = [x + '_Result' for x in chainRoots]
            chainUpLocsResult = [x + '_Result' for x in chainUpLocs]

        for index in range(len(controlList) - 1):
            # constrain controls to locators
            # TODO - find the actual up vector

            if twist:
                print('MOOOOO', upAxis[index])
                cmds.aimConstraint(chainPointsLocsResult[index + 1], chainPointsLocsResult[index],
                                   worldUpObject=chainUpLocsResult[index],
                                   aimVector=[1, 0, 0],
                                   upVector=upAxis[index],
                                   worldUpVector=[0, 0, 0],
                                   worldUpType='object')
            else:
                aimVector = self.getVectorToTarget(chainPointsLocsResult[index + 1], chainPointsLocsResult[index])
                cmds.aimConstraint(chainPointsLocsResult[index + 1], chainPointsLocsResult[index],
                                   worldUpObject=chainPointsLocs[index],
                                   aimVector=aimVector,
                                   upVector=upAxis[index],
                                   worldUpVector=upAxis[index],
                                   worldUpType='objectRotation')

    def connectResultToMainGroup(self, controlList, mainControl):
        if not isinstance(controlList, list):
            controlList = [controlList]
        cmds.addAttr(mainControl, ln='PhysicsNodes', at='message')
        parentControl = cmds.listRelatives(controlList[0], parent=True)[0]
        cmds.connectAttr(parentControl + '.message', mainControl + '.PhysicsNodes')

    def buildPointLocators(self, controlList=list()):
        """
        Create the nodes for baking and applying the results to
        :param controlList:
        :return:
        """

        mainControl = str(self.funcs.tempNull(name=controlList[0], suffix='PhysicsNodes'))
        self.connectResultToMainGroup(controlList[0], mainControl)
        cmds.parent(mainControl, self.getPhysicsRoot())
        # make the bake targets
        for c in controlList:
            rotationState = self.hasRotation(c)
            loc, root, axisLocs = self.placePointLocators(c, parent=mainControl, rotationControl=rotationState)
            # make the result nodes
            '''
            chainPointsLocsResult = self.duplicateWithSuffix(loc, 'Result')
            if rotationState:
                rootResult = self.duplicateWithSuffix(root, 'Result')
                axisResults = [self.duplicateWithSuffix(x, 'Result') for x in axisLocs]
            '''
            '''
            # TODO - find the actual up vector
            if rotationState:
                cmds.aimConstraint(chainPointsLocsResult[index + 1], chainPointsLocsResult[index],
                                   worldUpObject=chainUpLocsResult[index],
                                   aimVector=[1, 0, 0],
                                   upVector=upAxis[index],
                                   worldUpVector=[0, 0, 0],
                                   worldUpType='object')
            else:
                cmds.aimConstraint(chainPointsLocsResult[index + 1], chainPointsLocsResult[index],
                                   worldUpObject=chainPointsLocs[index],
                                   aimVector=[1, 0, 0],
                                   upVector=upAxis[index],
                                   worldUpVector=[0, 1, 0],
                                   worldUpType='objectRotation')
            '''

    def activateConstraints(self):
        self.toggleConstraints(state=True)

    def deactivateConstraints(self):
        self.toggleConstraints(state=False)

    def toggleConstraints(self, state=True):
        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        physicsNodes = [c for c in allNodes if 'PhysicsNodes' in str(c)]
        controls = self.getAllAnimControls(allNodes)

        for c in controls:
            constraints = cmds.listRelatives(c, children=True, type='constraint')
            if not constraints:
                continue
            for x in constraints:
                if state:
                    cmds.setAttr(x + '.nodeState', 0)
                else:
                    cmds.setAttr(x + '.nodeState', 2)

    def getAllAnimControls(self, allNodes):
        """
        get all the rig controls for baking out/toggling constraints
        :param allNodes:
        :return:
        """
        chainControls = self.funcs.flattenList([cmds.listRelatives(c, children=True) for c in allNodes])
        physControls = [c for c in chainControls if cmds.attributeQuery('control', exists=True, node=c)]
        animControls = [cmds.listConnections(c + '.' + 'control', source=True, destination=False) for c in physControls]
        animControls = self.funcs.flattenList(animControls)

        return list(set(animControls))

    def getAllPhysicsControls(self, namespace):
        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        allNodes = [x for x in allNodes if str(namespace) in str(x)]
        allChains = [c for c in allNodes if str(c).endswith(c_chain)]
        allPoints = [c for c in allNodes if str(c).endswith(c_points)]
        allControls = list()
        for p in allPoints:
            pointList = self.getPoints(p)
            twists = self.getTwists(pointList)
            allControls.extend(pointList)
            if twists:
                allControls.extend(twists)
        for p in allChains:
            chainPoints = self.getChains(p)
            twists = self.getTwists(chainPoints)
            allControls.extend(chainPoints)
            if twists:
                allControls.extend(twists)
        return allControls

    def deleteChainByName(self, chainName=None):
        physNodes = self.getResultNodesFromMain(chainName)
        cmds.delete(physNodes)
        cmds.delete(chainName)

    def cacheAnim(self):
        cmds.refresh()
        self.buildLocatorsFromScene()
        self.activateConstraints()
        self.clearDicts()
        self.makePhysicsForScene()
        self.simulate(self.stickData, self.controlPointDict, self.axisList, self.minTime, self.maxTime)

    def deleteChain(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('Please select a physics control')
        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')

        controls = self.getAllPhysicsControls(allNodes)

        if not controls:
            return cmds.warning('Please select a physics control')
        nodesToDelete = list()

        for s in sel:
            control = self.getPhysicsControlFromAnimControl(s)

            if control:
                controlParent = cmds.listRelatives(control, parent=True)[0]
                if not controlParent:
                    continue

                physNodes = self.getResultNodesFromMain(controlParent)
                nodesToDelete.append(controlParent)
                nodesToDelete.append(physNodes)
        cmds.delete(list(set(nodesToDelete)))

    def clearDicts(self):
        self.chainDict = {}  # each chain as value
        self.pointDict = {}  # each chain as value
        self.chainTwistDict = {}  # each chain as value

        self.pointControls = dict()
        self.stickControls = dict()
        self.twistControls = dict()
        self.controlPointDict = dict()
        self.chainPointsLocs = dict()
        self.chainUpLocs = dict()
        self.chainSideLocs = dict()

        self.aimAxisDict = dict()
        self.upAxisDict = dict()

        self.chainPointBakedValues = dict()  # baked out translations values soted as mvectors
        self.chainUpBakedValues = dict()
        self.chainSideBakedValues = dict()

        self.chainRoots = dict()
        self.chainRotLocs = dict()

        self.chainPointsLocsResult = dict()
        self.chainRotLocsResult = dict()
        self.chainUpLocsResult = dict()
        self.chainRootsResult = dict()

        self.pointData = dict()
        self.stickData = dict()
        self.axisList = list()
        self.rotationList = list()
        self.chainPhysicsControls = dict()
        self.constrainTargetDict = dict()
        self.constrainTargetDict = dict()

        self.controlConstraintDict = dict()

    def getPointsAndSticks(self):
        """
        Get info from the scene to save as a preset
        :return:
        """

        presetData = PhysicsPresetData()

        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        if not allNodes:
            return presetData
        physicsNodes = [c for c in allNodes if 'PhysicsNodes' in str(c)]
        allChains = [c for c in allNodes if str(c).endswith(c_chain)]
        allPoints = [c for c in allNodes if str(c).endswith(c_points)]
        allTargets = list()
        for node in physicsNodes:
            children = cmds.listRelatives(node, children=True)
            physPoints = [p for p in children if cmds.attributeQuery('attrControl', node=p, exists=True)]
            allTargets.extend(physPoints)

        chainDict = {}  # each chain as value
        pointDict = {}  # each chain as value
        stickControls = dict()
        pointControls = dict()
        twistControls = dict()

        chainTwistDict = dict()
        controlConstraintDict = dict()

        attributes = dict()

        for points in allPoints:
            pointList = self.getPoints(points)
            pointDict[points] = pointList
            # attributes[points] = self.getPhysicsValues(point)

        for key, value in pointDict.items():
            # place the physics objects at each object
            sticks = self.getSticks(key)
            pointControls = self.getPoints(key)

            controlConstraintDict = self.getControls(pointControls)

            presetData.points[key] = [[p, c] for p, c in zip(pointControls, controlConstraintDict)]
            presetData.pointTwists[key] = list()
            for point in pointControls:
                presetData.attributes[point] = self.getPhysicsValues(point)
                twistControls = self.getTwists([point])
                if not twistControls:
                    continue

                presetData.attributes[twistControls[0]] = self.getPhysicsValues(twistControls[0])
                presetData.pointTwists[key].append([point, twistControls[0]])
                attributes[twistControls[0]] = self.getPhysicsValues(point)
            stickControls[key] = list()
            for s in sticks:
                pointA = cmds.listConnections(s + '.pointA')[0]
                pointB = cmds.listConnections(s + '.pointB')[0]
                stickControls[key].append({'pointA': pointA, 'pointB': pointB})
                presetData.attributes[s] = self.getPhysicsValues(point)

        for key in allChains:
            chainPoints = self.getChains(key)
            sticks = self.getSticks(key)
            stickControls[key] = list()
            for s in sticks:
                pointA = cmds.listConnections(s + '.pointA')[0]
                pointB = cmds.listConnections(s + '.pointB')[0]
                stickControls[key].append({'pointA': pointA, 'pointB': pointB})
                presetData.attributes[s] = self.getStickAttributes(s)

            for point in chainPoints:
                presetData.attributes[point] = self.getPhysicsValues(point)

            twistControls = self.getTwists(chainPoints)

            chainDict[key] = chainPoints

            presetData.chains[key] = chainPoints
            if not twistControls:
                continue
            presetData.twistChains[key] = list()
            presetData.twistChains[key] = [[p, c] for p, c in zip(chainPoints, twistControls)]

            for c in twistControls:
                presetData.attributes[c] = self.getPhysicsValues(c)

        for key, value in chainDict.items():
            stickControls[key] = list()
            pointControls = dict()
            twistControls = dict()

            sticks = self.getSticks(key)
            points = self.getPoints(key)
            twists = self.getTwists(pointControls)

            for s in sticks:
                pointA = cmds.listConnections(s + '.pointA')[0]
                pointB = cmds.listConnections(s + '.pointB')[0]
                stickControls[key].append({'pointA': pointA, 'pointB': pointB})
                presetData.attributes[s] = self.getStickAttributes(s)
        presetData.sticks = stickControls

        return presetData

    def getPhysicsValues(self, node):
        return {k: cmds.getAttr(node + '.' + k) for k in physicsAttributes}

    def getStickAttributes(self, node):
        return {k: cmds.getAttr(node + '.' + k) for k in stickAttributes}

    def makePhysicsForScene(self):
        """
        Placeholder for getting things working
        :return:
        """
        # sel = cmds.ls(sl=True)
        # if not sel: return

        self.minTime = cmds.playbackOptions(query=True, min=True)
        self.maxTime = cmds.playbackOptions(query=True, max=True)
        animLength = self.maxTime - self.minTime

        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        physicsNodes = [c for c in allNodes if 'PhysicsNodes' in str(c)]
        allChains = [c for c in allNodes if str(c).endswith(c_chain)]
        allPoints = [c for c in allNodes if str(c).endswith(c_points)]

        self.allTargets = list()

        for node in physicsNodes:
            children = cmds.listRelatives(node, children=True)
            physPoints = [p for p in children if cmds.attributeQuery('attrControl', node=p, exists=True)]
            self.allTargets.extend(physPoints)

        for points in allPoints:
            pointList = self.getPoints(points)
            self.pointDict[points] = pointList

        for key, value in self.pointDict.items():
            # place the physics objects at each object
            self.chainPointsLocs[key] = [c + '_physPoint' for c in value]
            self.chainRoots[key] = [c + '_physPoint_root' for c in value if cmds.objExists(c + '_physPoint_root')]
            self.chainRotLocs[key] = [c + '_physPoint_up' for c in value if cmds.objExists(c + '_physPoint_rot')]
            self.stickControls[key] = self.getSticks(key)
            self.pointControls[key] = self.getPoints(key)
            self.twistControls[key] = self.getTwists(self.pointControls[key])
            self.chainPointsLocsResult[key] = [c + '_Result' for c in self.chainPointsLocs[key]]
            self.chainRootsResult[key] = [c + '_Result' for c in self.chainRoots[key]]
            self.chainRotLocsResult[key] = [c + '_Result' for c in self.chainRotLocs[key]]

            self.controlConstraintDict[key] = self.getControls(self.pointControls[key])

        for chain in allChains:
            chainPoints = self.getChains(chain)
            twistState = self.hasTwist(chainPoints[0])
            self.chainDict[chain] = chainPoints
            self.chainTwistDict[chain] = twistState

        for key, value in self.chainDict.items():
            # place the physics objects at each object
            self.chainPointsLocs[key] = [c + '_physPoint' for c in value]
            self.chainRoots[key] = [c + '_physPoint_root' for c in value if cmds.objExists(c + '_physPoint_root')]
            self.chainUpLocs[key] = [c + '_physPoint_up' for c in value if cmds.objExists(c + '_physPoint_up')]
            self.stickControls[key] = self.getSticks(key)
            self.pointControls[key] = self.getPoints(key)
            self.twistControls[key] = self.getTwists(self.pointControls[key])
            self.chainPointsLocsResult[key] = [c + '_Result' for c in self.chainPointsLocs[key]]
            self.chainRootsResult[key] = [c + '_Result' for c in self.chainRoots[key]]
            self.chainUpLocsResult[key] = [c + '_Result' for c in self.chainUpLocs[key]]

            self.controlConstraintDict[key] = self.getControls(self.pointControls[key])
        '''
        with self.funcs.suspendUpdate():
            try:
        '''
        # better way to get all targets

        # allTargets.extend(self.chainPointsLocs.values())
        # allTargets.extend(self.chainRoots.values())
        # allTargets.extend(self.chainUpLocs.values())

        # allTargets = [str(item) for sublist in allTargets for item in sublist if item]
        # allPointTargets = list()
        # allPointTargets.extend(self.chainPointsLocs.values())
        # allPointTargets.extend(self.chainUpLocs.values())

        # allPointTargets = [item for sublist in allPointTargets for item in sublist if item]
        # with self.funcs.suspendUpdate():
        try:
            cmds.cycleCheck(evaluation=False)
            cmds.bakeResults(self.allTargets,
                             time=(self.minTime, self.maxTime),
                             simulation=True,
                             bakeOnOverrideLayer=False,
                             sampleBy=1)
        finally:
            cmds.delete([cmds.listRelatives(node, type='constraint')[0] for node in self.allTargets])
            # self.funcs.resumeSkinning()
            cmds.cycleCheck(evaluation=True)
            cmds.refresh()
            cmds.currentTime(cmds.currentTime(query=True))

        print ('hey hey self.cycleState', self.cycleState)
        if self.cycleState:
            cmds.setInfinity(self.allTargets, pri='cycleRelative')
            cmds.setInfinity(self.allTargets, poi='cycleRelative')

            # cmds.copyKey(self.allTargets, time=(self.minTime, self.maxTime), option="curve")
            # cmds.pasteKey(self.allTargets, option='merge', time=(self.minTime - (self.maxTime - self.minTime),),
            #               copies=1)

        # add all points - figure out the preset values later
        # TODO - put something here that offsets the values, by a variable/non destructive amount
        start = cmds.timerX()
        for t in self.allTargets:
            values = self.getAllTranslateValues(t)
            p = Point(position=om2.MVector(values[0][0], values[0][1], values[0][2]),
                      stiffness=0.1,
                      resultObject=t + '_Result',
                      bakeObject=t)
            p.attributeControl = cmds.listConnections(t + '.' + 'attrControl')[0]
            for v in values:
                p.animPosition.append(om2.MVector(v[0], v[1], v[2]))
            self.controlPointDict[t] = p

        for key in self.chainDict.keys():
            if not self.chainTwistDict[key]:
                for index, loc in enumerate(self.chainPointsLocs[key]):
                    posControl = self.pointControls[key][index]
                    mainPoint = self.controlPointDict[loc]
                    mainPoint.attributeControl = posControl
                    # axis = Axis(mainPoint=mainPoint, targetPoint=targetPoint, rootPoint=rootPoint, upPoint=upPoint)
                    # self.rotationList.append(axis)
            else:
                # lock the first element of the chain
                # self.controlPointDict[self.chainPointsLocs[key][0]].locked = True
                # self.twistControls[key] = list()
                # self.pointControls[key] = list()

                for index, loc in enumerate(self.chainPointsLocs[key][:-1]):
                    posControl = self.pointControls[key][index]
                    twistControl = self.twistControls[key][index]
                    aimControl = self.pointControls[key][index + 1]

                    mainPoint = self.controlPointDict[loc]
                    targetPoint = self.controlPointDict[self.chainPointsLocs[key][index + 1]]
                    rootPoint = self.controlPointDict[self.chainRoots[key][index]]
                    upPoint = self.controlPointDict[self.chainUpLocs[key][index]]
                    # assign the control to each point - root, up and main are shared right now
                    mainPoint.attributeControl = posControl
                    rootPoint.attributeControl = twistControl
                    upPoint.attributeControl = twistControl
                    targetPoint.attributeControl = aimControl

                    axis = Axis(mainPoint=mainPoint, targetPoint=targetPoint, rootPoint=rootPoint, upPoint=upPoint)

                    self.axisList.append(axis)
                    if index > 1:
                        upTarget = self.chainDict[key][index - 1]
                    else:
                        upTarget = cmds.listRelatives(self.chainDict[key][0], parent=True)[0]

        for k, value in self.controlConstraintDict.items():
            for result, control in zip(self.chainPointsLocsResult[k], value):
                rots = ['rx', 'ry', 'rz']
                trs = ['tx', 'ty', 'tz']
                channels = []
                if not cmds.getAttr(result + '.constrainRotation'):
                    channels += rots
                if not cmds.getAttr(result + '.constrainTranslation'):
                    channels += trs
                self.funcs.safeParentConstraint(result, control, maintainOffset=False, channels=channels)
                # cmds.parentConstraint()

        # define some sticks and points

        self.pointData[key] = list()
        self.stickData[key] = list()

        self.chainPointBakedValues[key] = list()
        self.chainUpBakedValues[key] = list()

        # loop over chains to assign the axis elements used to make a nice up vector

        for v in self.chainPointsLocs[key]:
            self.pointData[key].append(self.controlPointDict[v])

        for s in self.stickControls[key]:
            pointA = cmds.listConnections(s + '.pointA')[0]
            pointB = cmds.listConnections(s + '.pointB')[0]
            self.stickData[key].append(Stick(pointA=self.controlPointDict[pointA + '_physPoint'],
                                             pointB=self.controlPointDict[pointB + '_physPoint'],
                                             compensate=0.5))

        maxIterations = 10
        timeScale = (1.0 / 30.0)
        gravityF = -98.1
        gravity = om2.MVector(0, gravityF * timeScale * timeScale, 0)

        '''
        for p in self.chainPointsLocs[key]:
            values = self.getAllTranslateValues(p)
            self.chainPointBakedValues[key].append(values)
        for p in self.chainUpLocs[key]:
            values = self.getAllTranslateValues(p)
            self.chainUpBakedValues[key].append(values)
        for p in self.chainSideLocs[key]:
            values = self.getAllTranslateValues(p)
            self.chainSideBakedValues[key].append(values)
        '''
        '''
        for x in range(animLength):
            print (x)
        '''

        '''
            except Exception as e:
                self.funcs.resumeSkinning()
                cmds.warning(e)
        '''

        return self.stickData, self.controlPointDict, self.axisList, self.chainPhysicsControls, self.minTime, self.maxTime

    def GetClosestPoint(self, pos, point):
        closest = 0
        closestDist = 1000000

        for p in list(self.controlPointDict.values()):
            if point == p:
                continue
            distance = om2.MVector(p.position - point.position).length()
            if distance < closestDist:
                closest = p
                distance

        return closest

    def makeAttributeHolder(self, name=str(), target=str(), mainControl=None, suffix='', scale=0.1, constrainTo=None,
                            type='orb'):
        # place physics controls at regular controls
        if cmds.objExists(name):
            cmds.delete(name)
        c = str(self.funcs.tempControl(name='blankName', suffix=suffix, scale=scale, drawType=type))

        c = cmds.rename(c, name)
        # TODO - change to linear
        # cmds.addAttr(c, ln='Gravity', at='float', dt=-98.1)
        cmds.addAttr(c, ln=FRAME_DELAY, at='float', dv=0)
        cmds.addAttr(c, ln=GRAVITY_SCALE, at='float', dv=1)
        cmds.addAttr(c, ln=DAMPING, at='float', dv=0.01, min=0.0, max=1.0)
        cmds.addAttr(c, ln=STIFFNESS, at='float', dv=0.1, min=0.0, max=1.0)
        cmds.addAttr(c, ln=FRICTION, at='float', dv=0.5, min=0.0, max=1.0)
        cmds.addAttr(c, ln=BOUNCE, at='float', dv=0.5, min=0.0, max=1.0)
        cmds.addAttr(c, ln=BLEND, at='float', dv=1.0, min=0.0, max=1.0)
        cmds.addAttr(c, ln=LOCKED, at='bool', dv=False)
        cmds.setAttr(c + '.' + FRAME_DELAY, edit=True, keyable=True)
        cmds.setAttr(c + '.' + GRAVITY_SCALE, edit=True, keyable=True)
        cmds.setAttr(c + '.' + DAMPING, edit=True, keyable=True)
        cmds.setAttr(c + '.' + STIFFNESS, edit=True, keyable=True)
        cmds.setAttr(c + '.' + FRICTION, edit=True, keyable=True)
        cmds.setAttr(c + '.' + BOUNCE, edit=True, keyable=True)
        cmds.setAttr(c + '.' + BLEND, edit=True, keyable=True)
        cmds.setAttr(c + '.' + LOCKED, edit=True, keyable=True)
        cmds.delete(cmds.parentConstraint(target, c))
        if mainControl:
            cmds.parent(c, mainControl)
        if constrainTo:
            cmds.parentConstraint(constrainTo, c)

        # cmds.setAttr(c + '.translate', lock=True)
        # cmds.setAttr(c + '.rotate', lock=True)
        return c

    def connectToAttributeHolder(self, point, control):
        cmds.addAttr(point, ln='attrControl', at='message')
        cmds.connectAttr(control + '.message', point + '.' + 'attrControl')

    def makePhysPoint(self, name=str, control=str, parent=None):
        point = cmds.spaceLocator(name=name)[0]
        if parent:
            cmds.parent(point, parent)
        self.connectToAttributeHolder(point, control)
        return point

    def makePhysResult(self, name=str, control=str, parent=None):
        point = cmds.spaceLocator(name=name + '_Result')[0]
        cmds.addAttr(point, ln='constrainRotation', at='bool', defaultValue=False)
        cmds.addAttr(point, ln='constrainTranslation', at='bool', defaultValue=False)
        if parent:
            cmds.parent(point, parent)
        return point

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(QWidget(), 'Open file',
                                            self.presetDir,
                                            self.fileHint)
        return fname[0] or None

    def loadPreset(self):
        fname = self.browseToFile()
        if not fname:
            return None
        collisionPresetData = PhysicsPresetData()
        collisionPresetData.load(fname)
        return collisionPresetData

    def quickBakeFromPreset(self):
        cmds.currentTime(cmds.playbackOptions(query=True, min=True))
        collisionPresetData = self.loadPreset()
        self.createControlsFromPreset(collisionPresetData)
        self.buildLocatorsFromScene()
        self.activateConstraints()
        self.clearDicts()
        self.makePhysicsForScene()
        self.simulate(self.stickData, self.controlPointDict, self.axisList, self.minTime, self.maxTime)
        self.bakeAnim()

    def createControlsFromPreset(self, presetData):
        # print (presetData)
        # print (presetData.twistChains)
        # print (presetData.points)  # group as key, controls as values
        # print (presetData.pointTwists)  # group as key, controls as values
        # print (presetData.sticks)  # group as key, controls as values
        # print (presetData.attributes)
        # TODO - this is causing a flip, but adding as normal does not....

        # add chains
        for chain, chainObjects in presetData.chains.items():
            twist = chain in presetData.twistChains.keys()
            controls = self.getControlNameFromPhysicsControls(chainObjects, 'point_')

            physControls, twistControls = self.buildChainControls(controls, twist=twist, lockFirst=False,
                                                                  startStiffness=0.5, endStiffness=0.2,
                                                                  falloffType='linear')

            for p in physControls + twistControls:
                if p not in presetData.attributes.keys():
                    continue
                for a, v in presetData.attributes[p].items():
                    cmds.setAttr(p + '.' + a, v)

    def getControlNameFromPhysicsControls(self, controls, delim):
        out_controls = list()
        for c in controls[:-1]:
            head, tail = c.split(delim)
            out_controls.append(head + tail)
        return out_controls

    def placePointLocators(self, control=str, parent=None, rotationControl=False):
        '''
        Place a point at each control, and one just after the last one
        '''
        chainLocs = list()
        roots = list()
        ups = list()
        upAxisList = list()
        aimAxisList = list()
        sides = list()
        root = None
        # chainList.append(None)

        name = '%s_physPoint' % control
        loc = self.makePhysPoint(name='%s_physPoint' % control, control=control, parent=parent)
        resultLoc = self.makePhysResult(name='%s_physPoint' % control, control=control, parent=parent)
        cmds.parentConstraint(control, loc, maintainOffset=False)

        cmds.setAttr(resultLoc + '.constrainRotation', True)
        cmds.setAttr(resultLoc + '.constrainTranslation', False)

        axisLocs = list()
        axisResultLocs = list()
        if rotationControl:
            cmds.setAttr(resultLoc + '.constrainTranslation', True)
            controlPos = om2.MVector(cmds.xform(control,
                                                query=True,
                                                worldSpace=True,
                                                rotatePivot=True))
            axis = ['X', 'Y', 'Z']
            omAxis = [om.MVector.xAxis, om.MVector.yAxis, om.MVector.zAxis]

            root = self.makePhysPoint(name='%s_physpoint_rot' % (control),
                                      control=rotationControl,
                                      parent=parent)
            rootResult = self.makePhysResult(name='%s_physpoint_rot' % (control),
                                             control=rotationControl,
                                             parent=parent)
            cmds.parentConstraint(control, root, maintainOffset=False, skipRotate=('x', 'y', 'z'))
            for n, axis in zip(axis, omAxis):
                axisLoc = self.makePhysPoint(name='%s_physpoint_rot_%s' % (control, n),
                                             control=rotationControl,
                                             parent=parent)
                axisLocResult = self.makePhysResult(name='%s_physpoint_rot_%s' % (control, n),
                                                    control=rotationControl,
                                                    parent=parent)

                offset = self.getLocalVector(control, vec=axis, mult=10)
                twistPos = controlPos + om2.MVector(offset)
                cmds.xform(axisLoc, translation=[twistPos.x, twistPos.y, twistPos.z])
                cmds.parentConstraint(control, axisLoc, maintainOffset=True, skipRotate=('x', 'y', 'z'))
                axisLocs.append(axisLoc)
                axisResultLocs.append(axisLocResult)

            self.matrixOrientConstraint(rootResult, axisResultLocs, resultLoc)

        return loc, root, axisLocs

    def placeChainLocators(self, chainList=list(), parent=None, twist=False):
        '''
        Place a point at each control, and one just after the last one
        '''
        chainLocs = list()
        roots = list()
        ups = list()
        upAxisList = list()
        aimAxisList = list()
        sides = list()

        # chainList.append(None)

        for i, s in enumerate(chainList):
            # is the last objects?

            name = '%s_physPoint' % s
            pos = om2.MVector(cmds.xform(s, query=True, worldSpace=True,
                                         # translation=True,
                                         rotatePivot=True))
            target = s

            physpoint = self.makePhysPoint(name=name,
                                           control=s,
                                           parent=parent)

            physpointResult = self.makePhysResult(name=name,
                                                  control=s,
                                                  parent=parent)
            cmds.setAttr(physpoint + '.displayLocalAxis', True)
            cmds.xform(physpoint, translation=pos)
            cmds.delete(cmds.orientConstraint(target, physpoint))
            cmds.parentConstraint(target, physpoint, maintainOffset=True)
            cmds.delete(cmds.parentConstraint(physpoint, physpointResult))
            chainLocs.append(physpoint)

        allConstraints = list()

        for x in range(len(chainLocs) - 1):
            if twist:
                twistControl = self.getTwists([chainList[x]])
                root, up, up_axis, aim_axis = self.placeAimObjectsFromUpVector(chainLocs[x], chainLocs[x + 1],
                                                                               str(twistControl[0]),
                                                                               parent=parent)
                cmds.parentConstraint(chainLocs[x], up, maintainOffset=True, skipRotate=('x', 'y', 'z'))
                cmds.pointConstraint(chainLocs[x], root, maintainOffset=True)

            else:
                root, up, up_axis, aim_axis = self.placeAimObjectsNoTwist(chainLocs[x], chainLocs[x + 1], parent=parent)
            roots.append(root)
            ups.append(up)
            upAxisList.append(up_axis)
            aimAxisList.append(aim_axis)
            # sides.append(side)

        return chainLocs, roots, ups, aimAxisList, upAxisList

    '''    
    def placeChainLocators_deprecated(self, chainList=list(), parent=None, twist=False):
        chainLocs = list()
        roots = list()
        ups = list()
        upAxisList = list()
        aimAxisList = list()
        sides = list()

        # chainList.append(None)

        for i, s in enumerate(chainList):
            # is the last objects?
            print (i, s)

            name = '%s_physPoint' % s
            pos = om2.MVector(cmds.xform(s, query=True, worldSpace=True,
                                         # translation=True,
                                         rotatePivot=True))
            target = s

            loc = cmds.spaceLocator(name=name)
            if parent:
                cmds.parent(loc, parent)
            cmds.setAttr(loc[0] + '.displayLocalAxis', True)
            cmds.xform(loc[0], translation=pos)
            cmds.delete(cmds.orientConstraint(target, loc))
            cmds.parentConstraint(target, loc, maintainOffset=True)
            chainLocs.append(loc[0])

        allConstraints = list()

        if twist:
            for x in range(len(chainLocs) - 1):
                root, up, upAxis, aimAxis = self.placeAimObjects(chainLocs[x], chainLocs[x + 1])
                # print (chainLocs[x], upAxis, aimAxis)
                cmds.pointConstraint(chainLocs[x], root, maintainOffset=True)
                cmds.parentConstraint(chainLocs[x], up, maintainOffset=True, skipRotate=('x', 'y', 'z'))
                # cmds.parentConstraint(chainLocs[x], side, maintainOffset=True)
                if parent:
                    cmds.parent(root, up, parent)
                roots.append(root)
                ups.append(up)
                upAxisList.append(upAxis)
                aimAxisList.append(aimAxis)
                # sides.append(side)

        return chainLocs, roots, ups, aimAxisList, upAxisList
    '''
    """
    Functions
    """

    def placeAimObjectsFromUpVector(self, control, target, twistControl, parent=None):
        """
        Duplicate this and separate the object creation and aim stuff out
        use one to place the temp objects, and one to create the final aim constraint
        :param control:
        :param target:
        :return:
        """
        print('placeAimObjectsFromUpVector')
        """
        Get up vector from y axis on twistControl
        """
        locatorPos = om2.MVector(cmds.xform(target, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        controlPos = om2.MVector(cmds.xform(control, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        aimDistance = (locatorPos - controlPos).length()
        aimVector = (locatorPos - controlPos).normal()
        # print ('aimDistance', aimDistance)
        # print ('aim', aimVector)
        localAxisList = self.getAxis(control)
        xDot = aimVector * localAxisList[0]
        yDot = aimVector * localAxisList[1]
        zDot = aimVector * localAxisList[2]

        # print ('x', xDot, 'y', yDot, 'z', zDot)

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [om2.MVector(1, 0, 0), om2.MVector(0, 1, 0), om2.MVector(0, 0, 1)]

        upAxisIndex = axisList.index(min(axisList))
        # print ('aim axis', axisList.index(max(axisList)))
        # print ('up axis', axisList.index(min(axisList)))

        # aimVector = self.getVectorToTarget(target, control)
        aimNormal = aimVector.normal()
        upVector = localAxisList[upAxisIndex].normal()
        sideVector = aimNormal ^ upVector

        # print('control', control)
        # print ('aimVector', aimNormal)
        # print ('upVector', upVector)
        # print ('sideVector', sideVector)

        rootNull = self.makePhysPoint(name='%s_root' % control,
                                      control=twistControl,
                                      parent=parent)
        upNull = self.makePhysPoint(name='%s_up' % control,
                                    control=twistControl,
                                    parent=parent)
        rootNullResult = self.makePhysResult(name='%s_root' % control,
                                             control=twistControl,
                                             parent=parent)
        upNullResult = self.makePhysResult(name='%s_up' % control,
                                           control=twistControl,
                                           parent=parent)
        # sideNull = cmds.spaceLocator(name='%s_side' % control)[0]
        # tmpUp3 = cmds.spaceLocator(name='%s_sidex' % control)

        tmpUpVec1 = controlPos + (upVector * aimDistance)
        tmpUpVec2 = controlPos + (sideVector * aimDistance)
        # tmpUpVec3 = controlPos + (localAxisList[2] * aimDistance)

        twistOffset = self.getLocalVector(twistControl, mult=aimDistance * 2)
        twistPos = controlPos + om2.MVector(twistOffset)

        cmds.xform(rootNull, translation=[controlPos.x, controlPos.y, controlPos.z])
        cmds.xform(upNull, translation=[twistPos.x, twistPos.y, twistPos.z])

        vec = self.getVectorToTarget(upNull, control)

        # cmds.xform(sideNull, translation=[tmpUpVec2.x, tmpUpVec2.y, tmpUpVec2.z])
        # cmds.parent(upNull, rootNull)

        return rootNull, upNull, vec, aimVector

    def placeAimObjectsNoTwist(self, control, target, parent=None):
        """
        Duplicate this and separate the object creation and aim stuff out
        use one to place the temp objects, and one to create the final aim constraint
        :param control:
        :param target:
        :return:
        """
        locatorPos = om2.MVector(cmds.xform(target, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        controlPos = om2.MVector(cmds.xform(control, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        aimDistance = (locatorPos - controlPos).length()
        aimVector = (locatorPos - controlPos).normal()
        # print ('aimDistance', aimDistance)
        # print ('aim', aimVector)
        localAxisList = self.getAxis(control)
        xDot = aimVector * localAxisList[0]
        yDot = aimVector * localAxisList[1]
        zDot = aimVector * localAxisList[2]

        # print ('x', xDot, 'y', yDot, 'z', zDot)

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [om2.MVector(1, 0, 0), om2.MVector(0, 1, 0), om2.MVector(0, 0, 1)]

        upAxisIndex = axisList.index(min(axisList))
        # print ('aim axis', axisList.index(max(axisList)))
        # print ('up axis', axisList.index(min(axisList)))

        # aimVector = self.getVectorToTarget(target, control)
        aimNormal = aimVector.normal()
        upVector = localAxisList[upAxisIndex].normal()
        sideVector = aimNormal ^ upVector

        # print('control', control)
        # print ('aimVector', aimNormal)
        # print ('upVector', upVector)
        # print ('sideVector', sideVector)

        rootNull = self.makePhysPoint(name='%s_root' % control,
                                      control=control,
                                      parent=parent)
        upNull = self.makePhysPoint(name='%s_up' % control,
                                    control=control,
                                    parent=parent)
        rootNullResult = self.makePhysResult(name='%s_root' % control,
                                             control=control,
                                             parent=parent)
        upNullResult = self.makePhysResult(name='%s_up' % control,
                                           control=control,
                                           parent=parent)
        # sideNull = cmds.spaceLocator(name='%s_side' % control)[0]
        # tmpUp3 = cmds.spaceLocator(name='%s_sidex' % control)

        tmpUpVec1 = controlPos + (upVector * aimDistance)
        tmpUpVec2 = controlPos + (sideVector * aimDistance)
        # tmpUpVec3 = controlPos + (localAxisList[2] * aimDistance)

        cmds.xform(rootNull, translation=[controlPos.x, controlPos.y, controlPos.z])
        cmds.xform(upNull, translation=[tmpUpVec1.x, tmpUpVec1.y, tmpUpVec1.z])
        # cmds.xform(sideNull, translation=[tmpUpVec2.x, tmpUpVec2.y, tmpUpVec2.z])
        # cmds.parent(upNull, rootNull)

        upVector = self.getVectorToTarget(upNull, control)
        cmds.delete(rootNull, upNull)
        return None, None, upVector, aimVector

    def placeAimObjects(self, control, target):
        """
        Duplicate this and separate the object creation and aim stuff out
        use one to place the temp objects, and one to create the final aim constraint
        :param control:
        :param target:
        :return:
        """
        locatorPos = om2.MVector(cmds.xform(target, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        controlPos = om2.MVector(cmds.xform(control, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        aimDistance = (locatorPos - controlPos).length()
        aimVector = (locatorPos - controlPos).normal()
        # print ('aimDistance', aimDistance)
        # print ('aim', aimVector)
        localAxisList = self.getAxis(control)
        xDot = aimVector * localAxisList[0]
        yDot = aimVector * localAxisList[1]
        zDot = aimVector * localAxisList[2]

        # print ('x', xDot, 'y', yDot, 'z', zDot)

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [om2.MVector(1, 0, 0), om2.MVector(0, 1, 0), om2.MVector(0, 0, 1)]

        upAxisIndex = axisList.index(min(axisList))
        # print ('aim axis', axisList.index(max(axisList)))
        # print ('up axis', axisList.index(min(axisList)))

        # aimVector = self.getVectorToTarget(target, control)
        aimNormal = aimVector.normal()
        upVector = localAxisList[upAxisIndex].normal()
        sideVector = aimNormal ^ upVector

        # print('control', control)
        # print ('aimVector', aimNormal)
        # print ('upVector', upVector)
        # print ('sideVector', sideVector)

        rootNull = cmds.spaceLocator(name='%s_root' % control)[0]
        upNull = cmds.spaceLocator(name='%s_up' % control)[0]
        # sideNull = cmds.spaceLocator(name='%s_side' % control)[0]
        # tmpUp3 = cmds.spaceLocator(name='%s_sidex' % control)

        tmpUpVec1 = controlPos + (upVector * aimDistance)
        tmpUpVec2 = controlPos + (sideVector * aimDistance)
        # tmpUpVec3 = controlPos + (localAxisList[2] * aimDistance)

        cmds.xform(rootNull, translation=[controlPos.x, controlPos.y, controlPos.z])
        cmds.xform(upNull, translation=[tmpUpVec1.x, tmpUpVec1.y, tmpUpVec1.z])
        # cmds.xform(sideNull, translation=[tmpUpVec2.x, tmpUpVec2.y, tmpUpVec2.z])
        # cmds.parent(upNull, rootNull)
        upVector = self.getVectorToTarget(upNull, control)
        return rootNull, upNull, upVector, aimVector

    def constrainAimToTarget(self, control, target):
        """
        Duplicate this and separate the object creation and aim stuff out
        use one to place the temp objects, and one to create the final aim constraint
        :param control:
        :param target:
        :return:
        """
        locatorPos = om2.MVector(cmds.xform(target, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        controlPos = om2.MVector(cmds.xform(control, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        aimDistance = (locatorPos - controlPos).length()
        aimVector = (locatorPos - controlPos).normal()
        # print ('aimDistance', aimDistance)
        # print ('aim', aimVector)
        localAxisList = self.getAxis(control)
        xDot = aimVector * localAxisList[0]
        yDot = aimVector * localAxisList[1]
        zDot = aimVector * localAxisList[2]

        # print ('x', xDot, 'y', yDot, 'z', zDot)

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [om2.MVector(1, 0, 0), om2.MVector(0, 1, 0), om2.MVector(0, 0, 1)]

        upAxisIndex = axisList.index(min(axisList))
        # print ('aim axis', axisList.index(max(axisList)))
        # print ('up axis', axisList.index(min(axisList)))

        # aimVector = self.getVectorToTarget(target, control)
        aimNormal = aimVector.normal()
        upVector = localAxisList[upAxisIndex].normal()
        sideVector = aimNormal ^ upVector

        # print('control', control)
        # print ('aimVector', aimNormal)
        # print ('upVector', upVector)
        # print ('sideVector', sideVector)

        tmpUp1 = cmds.spaceLocator(name='%s_up' % control)[0]
        tmpUp2 = cmds.spaceLocator(name='%s_side' % control)[0]
        # tmpUp3 = cmds.spaceLocator(name='%s_sidex' % control)

        tmpUpVec1 = controlPos + (upVector * aimDistance)
        tmpUpVec2 = controlPos + (sideVector * aimDistance)
        # tmpUpVec3 = controlPos + (localAxisList[2] * aimDistance)

        cmds.xform(tmpUp1, translation=[tmpUpVec1.x, tmpUpVec1.y, tmpUpVec1.z])
        cmds.xform(tmpUp2, translation=[tmpUpVec2.x, tmpUpVec2.y, tmpUpVec2.z])

        aimConstraint = cmds.aimConstraint(target, control,
                                         aimVector=self.getVectorToTarget(target, control),
                                         worldUpVector=sideVector,
                                         upVector=upVector,
                                         worldUpType='vector',
                                         maintainOffset=False)
        return aimConstraint

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

    def getLocalVector(self, node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
        animNode = self.getDagNode(node)
        matrix = animNode.inclusiveMatrix()
        vec = ((vec * matrix).normal() * mult) + offset
        return om2.MVector(vec.x, vec.y, vec.z)

    def getAxis(self, control):
        controlNode = self.getDagNode(control)
        controlMatrix = om2.MMatrix(controlNode.inclusiveMatrix())
        x = om2.MVector(1, 0, 0) * controlMatrix
        y = om2.MVector(0, 1, 0) * controlMatrix
        z = om2.MVector(0, 0, 1) * controlMatrix
        return [x, y, z]

    def getWorldSpaceVectorOffset(self, control, target, vec=om2.MVector(0, 1, 0)):
        controlNode = self.getDagNode(control)
        controlMatrix = controlNode.inclusiveMatrix()

        targetNode = self.getDagNode(target)
        targetMatrix = targetNode.inclusiveMatrix()

        vec = ((vec * controlMatrix) * targetMatrix.inverse()).normal()
        return om2.MVector(vec.x, vec.y, vec.z)

    def getDagNode(self, node):
        selList = om.MSelectionList()
        selList.add(node)
        nodeDagPath = om.MDagPath()
        selList.getDagPath(0, nodeDagPath)
        return nodeDagPath

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

    @staticmethod
    def getMFnCurveFromPlug(plug):
        omslist = om2.MSelectionList()
        omslist.add(plug)
        mplug = omslist.getPlug(0)
        mcurve = oma2.MFnAnimCurve(mplug)

        return mplug, mcurve

    @staticmethod
    def getMfnCurveValues(mfnCurve, mTimeArray):
        return [mfnCurve.evaluate(m) for m in mTimeArray]

    @staticmethod
    def getStaticValues(value, mTimeArray):
        return [value for m in mTimeArray]

    def getAnimatedProperty(self, control, attribute, startTime, endTime, offset=0):
        plug, curve = self.getMFnCurveFromPlug(control + '.' + attribute)
        mTimeArrary = self.createMTimeArray(int(startTime), int(endTime - startTime) + 1, offset=offset)
        try:
            values = self.getMfnCurveValues(curve, mTimeArrary)
        except:
            values = self.getStaticValues(cmds.getAttr(control + '.' + attribute), mTimeArrary)
        return values

    def toggleCycle(self, state):
        self.cycleState = state
        dataNode = self.getPhysicsData()
        cmds.setAttr(dataNode + '.' + 'cycle', state)

    def getCycleState(self):
        dataNode = self.getPhysicsData()
        self.cycleState = cmds.getAttr(dataNode + '.' + 'cycle')
        return self.cycleState

    def simulate(self, sticks, points, axisList, startTime, endTime):
        # TODO - remove hack

        for point in list(points.values()):
            cmds.setKeyframe(point.resultObject + '.tx')
            cmds.setKeyframe(point.resultObject + '.ty')
            cmds.setKeyframe(point.resultObject + '.tz')

        # TODO - add switch / preroll here
        # startTime = - (endTime - startTime)
        originalStartTime = startTime
        simStartTime = - (endTime - startTime)
        # TODO - this will break if the user changes the timeline range!
        duration = endTime - startTime

        if self.cycleState:
            animStartTime = startTime - duration - duration
            animEndTime = endTime
        else:
            animStartTime = startTime
            animEndTime = endTime

        # print ('min',self.minTime)
        # print ('max',self.maxTime)
        #
        # print ('duration', duration)
        # print ('cycleState', self.cycleState)
        # print ('animStartTime', animStartTime)
        # print ('animStartTime', animEndTime)

        # clear the cached result data
        for index, p in enumerate(list(points.values())):
            p.resultPosition = list()
            p.position = om2.MVector(p.animPosition[0])
            p.prevPosition = om2.MVector(p.animPosition[0])
            p.gravityScale = self.getAnimatedProperty(p.attributeControl, GRAVITY_SCALE, startTime, endTime)
            p.damp = self.getAnimatedProperty(p.attributeControl, DAMPING, startTime, endTime)
            p.stiffness = self.getAnimatedProperty(p.attributeControl, STIFFNESS, startTime, endTime)
            p.friction = self.getAnimatedProperty(p.attributeControl, '%s' % FRICTION, startTime, endTime)
            p.bounce = self.getAnimatedProperty(p.attributeControl, BOUNCE, startTime, endTime)
            p.blend = self.getAnimatedProperty(p.attributeControl, BLEND, startTime, endTime)
            p.locked = cmds.getAttr(p.attributeControl + '.' + LOCKED)
            p.frameDelay = cmds.getAttr(p.attributeControl + '.' + FRAME_DELAY)

        # offset the translate values by shifting the lookup along the curve
        for index, p in enumerate(list(points.values())):
            p.animPosition = self.offsetAnimPosition(p.bakeObject, -p.frameDelay, animStartTime, animEndTime)

        worldAxis = cmds.upAxis(query=True, axis=True)
        if worldAxis == 'y':
            planeNormal = om2.MVector(0, 1, 0)
            gravity = om2.MVector(0, gravityF * timeScale * timeScale, 0)
        else:
            planeNormal = om2.MVector(0, 0, 1)
            gravity = om2.MVector(0, 0, gravityF * timeScale * timeScale)


        for timeIndex in range(len(list(points.values())[0].animPosition)):
            for index, p in enumerate(list(points.values())):
                collided = False
                if not p.locked:
                    preUpdatePosition = om2.MVector(p.position)
                    if p.floorContact:
                        friction = 1.0 - p.friction[timeIndex]
                    else:
                        friction = 1.0

                    loopedIndex = int(timeIndex % duration)

                    # print ('timeIndex', timeIndex)
                    # print ('loopedIndex', loopedIndex)

                    p.position += (p.position - p.prevPosition) * ((1.0 - p.damp[loopedIndex]) * friction)
                    if timeIndex > 0:
                        p.position += gravity * p.gravityScale[loopedIndex]

                    p.position += (p.animPosition[timeIndex] - p.position) * p.stiffness[loopedIndex]
                    p.position += (p.animPosition[timeIndex] - p.position) * (1.0 - p.blend[loopedIndex])
                    planePoint = om2.MVector(0, 0, 0)

                    rayDirection = (p.position - preUpdatePosition).normal()

                    Psi, resultPos, collided = self.LinePlaneCollision(planeNormal,
                                                                       planePoint,
                                                                       rayDirection,
                                                                       preUpdatePosition,
                                                                       p.position,
                                                                       )
                    # print (startTime+timeIndex, collided)

                    if collided and False:
                        velocity = p.position - preUpdatePosition
                        distance = (preUpdatePosition - p.position).length()
                        collidedDistance = (preUpdatePosition - resultPos).length()
                        bounceDistance = distance - collidedDistance
                        # print ('distance', distance)
                        # print ('collidedDistance', collidedDistance)

                        reflection = rayDirection - (2 * (rayDirection * planeNormal) * planeNormal)
                        reflectedVelocity = velocity - (2 * (velocity * planeNormal) * planeNormal)
                        reflectionResult = (reflection.normal() * bounceDistance * p.bounce[loopedIndex]) + resultPos
                        rayStart_new = reflectionResult - ((reflectionResult - resultPos).normal() * collidedDistance)
                        # TODO - fix this line
                        p.prevPosition = om2.MVector(reflectionResult - (reflectedVelocity * p.bounce[loopedIndex] * 0.9))
                        p.resultPosition.append(om2.MVector(reflectionResult))
                        p.position = om2.MVector(reflectionResult)
                    else:
                        p.prevPosition = preUpdatePosition
                        p.resultPosition.append(om2.MVector(p.position))
                else:
                    p.position = p.animPosition[timeIndex]
                    p.resultPosition.append(p.animPosition[timeIndex])

            for index, p in enumerate(list(points.values())):
                if not p.locked:
                    p.floorContact = False
            # print ('timeIndex', timeIndex)
            for x in range(maxIterations):
                # collision with floor hack
                # for s in random.sample(list(sticks.values()), len(sticks)):

                for s in list(sticks.values()):
                    index = 0
                    for stick in s:
                        positionA = stick.pointA.resultPosition[timeIndex]
                        positionB = stick.pointB.resultPosition[timeIndex]
                        delta = positionA - positionB
                        deltaLength = delta.length()
                        deltaNormal = delta.normal()

                        index += 1

                        deltaDiff = (deltaLength - stick.length) / deltaLength

                        # if not stick.pointA.locked:
                        #     stick.pointA.position -= delta * deltaDiff * stick.compensate
                        # if not stick.pointB.locked:
                        #     stick.pointB.position += delta * deltaDiff * stick.compensate

                        stickCentre = (positionA * 0.5) + (positionB * 0.5)
                        stickDir = (positionA - positionB).normal()

                        if not stick.pointA.locked:
                            # print('updating A', stickCentre + ((stickDir * stick.length) / 2.0) )
                            stick.pointA.resultPosition[timeIndex] = stickCentre + ((stickDir * stick.length) / 2.0)
                        if not stick.pointB.locked:
                            # print('updating B', stickCentre + ((stickDir * stick.length) / 2.0) )
                            stick.pointB.resultPosition[timeIndex] = stickCentre - ((stickDir * stick.length) / 2.0)

                        # print (x, 'deltaLength', deltaLength, stick.length)
                        # print ('result Length', (stick.pointA.resultPosition[timeIndex] - stick.pointB.resultPosition[timeIndex]).length())

                # for index, p in enumerate(list(points.values())):
                #     if not p.locked:
                #         if worldAxis == 'y':
                #             if p.position.y < 1.0:
                #                 p.position.y = 1.0
                #                 p.floorContact = True
                #         else:
                #             if p.position.z < 1.0:
                #                 p.position.z = 1.0
                #                 p.floorContact = True
                #
                #     # pass here for dependent up/side vector points
                #     # tag points to be coordinates, I.e. related to a main point and end point
                #     # output would be for an aim constraint up vector
                #     # don't actually need to place the up/side points in physics, just refer to the main anim ones

            for axis in axisList:
                # TODO - perform up vector correction here
                # up vector is to be used for aim constraint
                pos = axis.mainPoint.resultPosition[timeIndex]
                aim = axis.targetPoint.resultPosition[timeIndex]
                up = axis.upPoint.resultPosition[timeIndex]
                root = axis.rootPoint.resultPosition[timeIndex]
                upVec = (up - root).normalize()
                aimVec = (aim - pos).normalize()
                # print (upVec, aimVec)
                cross = aimVec ^ upVec
                upOut = cross ^ aimVec

                # axis.upPoint.resultPosition[timeIndex] = pos + upOut
                # axis.upPoint.position = pos + upOut
                axis.upPoint.resultPosition[timeIndex] = up - root + pos

            '''
            cmds.currentTime(timeIndex)  # TODO - correct for real frame
            for index, p in enumerate(points.values()):
                cmds.setAttr(p.resultObject + '.translate', *p.resultPosition[timeIndex])
            '''

        # set actual curves with api
        self.setFinalCurveValues(simStartTime=startTime,
                                 simEndTime=endTime,
                                 startFrame=animStartTime,
                                 endFrame=animEndTime,
                                 pointData=points,
                                 isycled=self.cycleState)

    def offsetAnimPosition(self, loc, offset, startTime, endTime):
        values = self.evaluateAllTranslateValues(loc, offset, startTime, endTime)
        return values

    def bakeAnim(self):
        allNodes = cmds.listRelatives(self.getPhysicsRoot(), type='transform')
        controls = self.getAllAnimControls(allNodes)

        bakeRange = self.funcs.getTimelineRange()
        newAnimLayer = cmds.animLayer('Physics', override=True, passthrough=True)
        newAnimLayer.rotationAccumulationMode.set(True)
        newAnimLayer.ghostColor.set(self.allTools.tools['BakeTools'].overrideLayerColour)
        with self.funcs.suspendUpdate():
            cmds.bakeResults(controls,
                             destinationLayer=str(newAnimLayer),
                             time=(bakeRange[0], bakeRange[1]),
                             simulation=True,
                             bakeOnOverrideLayer=True,
                             sampleBy=1)
        cmds.delete(self.getPhysicsRoot())

    def LinePlaneCollision(self, planeNormal, planePoint, rayDirection, rayStart, rayEnd, radius=1.0, epsilon=1e-6):

        ndotu = planeNormal * rayDirection
        if ndotu > 0:
            return rayDirection, rayEnd, False
        if abs(ndotu) < epsilon:
            return rayDirection, rayEnd, False

        w = rayStart - planePoint
        si = (-planeNormal * w) / ndotu
        Psi = w + si * rayDirection + planePoint
        if (Psi - rayStart).length() < (rayStart - rayEnd - rayDirection.normal()).length():
            angle = planeNormal.angle(-rayDirection)
            if angle != 0:
                hyp = radius / math.cos(angle)
            else:
                hyp = radius
            resultPos = Psi + (hyp * (-rayDirection).normal())
            return Psi, resultPos, True
        else:
            return Psi, rayEnd, False

    @staticmethod
    def getMFnCurveFromPlug(plug):
        omslist = om2.MSelectionList()
        omslist.add(plug)
        mplug = omslist.getPlug(0)
        mcurve = oma2.MFnAnimCurve(mplug)

        return mplug, mcurve

    def setFinalCurveValues(self,
                            simStartTime=-100,
                            simEndTime=100,
                            startFrame=0,
                            endFrame=100,
                            pointData=None,
                            isycled=False):
        # print ('pointData', pointData)
        # print('setFinalCurveValues')
        # print('simStartTime', simStartTime)
        # print('simEndTime', simEndTime)
        # print('startFrame', startFrame)
        # print('endFrame', endFrame)

        dg = om2.MDGModifier()

        midpoint = int(simEndTime - simStartTime + 1) // 2
        # print ('midpoint', midpoint)
        resultMTimeArray = self.createMTimeArray(startFrame, int(endFrame - startFrame + 1))
        # print ('resultMTimeArray', len(resultMTimeArray))
        for p in list(pointData.values()):
            for index, x in enumerate(['x', 'y', 'z']):
                plug, curve = self.getMFnCurveFromPlug(p.resultObject + '.t%s' % x)
                # print ('plug', x, plug, curve, curve.animCurveType)
                # if it is a cycle, grab the second half of the keys
                # if isycled:
                #     translationValues = [o[index] for o in p.resultPosition[midpoint:]]
                # else:
                #     translationValues = [o[index] for o in p.resultPosition]

                translationValues = [o[index] for o in p.resultPosition]

                # print ('len translationValues', len(translationValues))
                sources = plug.connectedTo(True, False)
                for i in range(len(sources)):
                    dg.disconnect(sources[i], plug)
                dg.doIt()
                newCurve = oma2.MFnAnimCurve(plug)
                # print (len(resultMTimeArray))
                # print (len(translationValues))
                newCurve.create(plug, curve.animCurveType, dg)
                newCurve.addKeys(resultMTimeArray,
                                 translationValues,
                                 oma2.MFnAnimCurve.kTangentGlobal,
                                 oma2.MFnAnimCurve.kTangentGlobal)
                dg.doIt()

    def PhysicsSetupUI(self, quick=True):
        if quick:
            win = PhysicsQuickUI(self)
        else:
            win = PhysicsSetupUI(self)
        win.show()

    def toolBoxUI(self, message=''):
        # print('toolBoxUI', self.toolbox)
        if not self.toolbox:
            self.toolbox = PhysicsToolbox(self)
        self.toolbox.show()
        self.toolbox.refreshUI()
        # self.toolboxWidget = self.getToolboxWidget(self.toolbox, message=message)
        # self.toolbox.setCentralWidget(self.toolboxWidget)
        # # self.toolbox.mainLayout.addWidget(self.toolboxWidget)
        #
        # self.toolbox.show()
        # self.toolbox.widgetClosed.connect(self.removeScriptJob)
        # self.toolbox.setFixedSize(self.toolbox.sizeHint())
        # self.toolbox.setFixedWidth(320 * dpiScale())
        # self.toolboxWidget.setEnabled(False)
        # self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.update], protected=False)
        # self.update()


class CollisionObject(object):
    def __init__(self, position=om2.MVector):
        self.position = position
        self.animPosition = list()


class Point(object):
    def __init__(self, position=om2.MVector, locked=False, stiffness=0.25, damp=0.1, gravityScale=1.0,
                 resultObject=str(), attributeControl=str(), bakeObject=str()):
        self.position = position
        self.prevPosition = om2.MVector(position[0], position[1], position[2])

        self.locked = locked
        self.stiffness = stiffness
        self.damp = damp
        self.floorContact = False
        self.bounce = list()
        self.animPosition = list()
        self.resultPosition = list()
        self.gravityScale = gravityScale
        self.resultObject = resultObject
        self.bakeObject = bakeObject
        self.attributeControl = attributeControl

    def createStickNode(self, physicsRoot=None):
        pass
        # stick = self.funcs


class Stick(object):
    def __init__(self, pointA=int, pointB=int, compensate=0.5):
        self.pointA = pointA
        self.pointB = pointB
        self.length = (pointA.position - pointB.position).length()
        self.compensate = compensate


class Axis(object):
    def __init__(self, mainPoint=Point, targetPoint=Point, upPoint=Point, rootPoint=Point):
        self.mainPoint = mainPoint
        self.targetPoint = targetPoint
        self.upPoint = upPoint
        self.rootPoint = rootPoint

    def getUpVector(self, timeIndex):
        pass


class PhysicsQuickUI(QMainWindow):
    fileHint = "Physics Preset files (*.json)"
    resized = Signal()

    def __init__(self, cls):
        super(PhysicsQuickUI, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setObjectName('tbPhysics_SetupUI')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)  # Hides minimize and maximize buttons

        self.collisionPresetData = None
        self.groupWidgets = dict()
        self.cls = cls

        self.collisionWidgets = dict()
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        windowTitle = title_str
        self.setWindowTitle(windowTitle)

        self.setWindowTitle('{o} :: v{v}'.format(o=windowTitle, v=PhysicsTool.version))

        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        def setAnimMode():
            # stackedWidget.setCurrentIndex(0)
            animButton.setEnabled(True)
            editButton.setDisabled(True)


        def setEditMode():
            # stackedWidget.setCurrentIndex(1)
            animButton.setDisabled(True)
            editButton.setEnabled(True)


        editButton = QPushButton('Create')
        editButton.clicked.connect(setAnimMode)
        animButton = QPushButton('Edit')
        animButton.clicked.connect(setEditMode)

        # animButton.clicked.connect()
        modeLayout = QHBoxLayout()
        modeLayout.addWidget(editButton)
        modeLayout.addWidget(animButton)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignTop)
        self.main_widget.setLayout(self.layout)

        self.layout.addLayout(modeLayout)

        self.controlsLayout = QVBoxLayout()
        self.controlsSpacerLayout = QVBoxLayout()
        self.controlsSpacerLayout.addStretch(100)
        self.controlsLayout.addLayout(self.controlsSpacerLayout)
        self.controlsLayout.setContentsMargins(4, 8, 0, 0)
        self.controlsLayout.setSpacing(0)
        self.controlsLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # group box for the top widget
        self.controlsGroupBox = QBoldGroupBox('Mode selection')
        self.controlsGroupBoxLayout = QHBoxLayout()
        self.controlsGroupBox.setLayout(self.controlsGroupBoxLayout)
        self.controlsGroupBoxLayout.setContentsMargins(8, 20, 0, 0)
        self.controlsGroupBoxLayout.setSpacing(0)

        # group box for the create widget
        self.createGroupBox = QBoldGroupBox('BLANKNAME')
        self.createGroupBox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.createLayout = QVBoxLayout()
        self.createLayout.setContentsMargins(2, 20, 2, 2)
        self.createGroupBox.setLayout(self.createLayout)

        self.falloffroupBox = QGroupBox('Falloff')
        self.falloffGroupBoxLayout = QVBoxLayout()
        self.falloffroupBox.setLayout(self.falloffGroupBoxLayout)

        self.controlsFrame = QFrame()

        self.typeCombo = QComboBox()
        self.typeCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for item in typesList:
            self.typeCombo.addItem(item)
        self.typeCombo.setFixedWidth(self.typeCombo.sizeHint().width())
        self.typeCombo.setFixedHeight(22 * dpiScale())
        self.typeCombo.currentIndexChanged.connect(self.typeChanged)

        self.createHelpButton = HelpButton(width=22, height=22)
        self.createHelpButton.clicked.connect(self.openCreateHelpWindow)

        self.chainsButton = QPushButton('Chains')
        self.singleChainButton = QPushButton('Single Chain')
        self.pointsButton = QPushButton('Single Controls')
        self.constraintsButton = QPushButton('Constraints')

        # self.chainsButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(0))
        # self.singleChainButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(1))
        # self.pointsButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(2))
        # self.constraintsButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(3))

        self.controlsGroupBoxLayout.addWidget(QLabel("Pick control type "))
        self.controlsGroupBoxLayout.addWidget(self.typeCombo)
        self.controlsGroupBoxLayout.addWidget(self.createHelpButton)

        # self.typeButtonLayout.addWidget(self.chainsButton)
        # self.typeButtonLayout.addWidget(self.singleChainButton)
        # self.typeButtonLayout.addWidget(self.pointsButton)
        # self.typeButtonLayout.addWidget(self.constraintsButton)

        self.typeStack = QStackedWidget(self)
        self.createLayout.addWidget(self.typeStack)
        # self.typeStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # self.controlsGroupBoxLayout.addWidget(self.typeStack)
        self.chainWidget = PhysicsChainQuickWidget(self, label='Single Chain',
                                                   help='Something about adding single chains of controls')
        self.chainWidget.addNewSignal.connect(self.addNewChain)
        self.typeStack.addWidget(self.chainWidget)
        #
        self.simpleAimWidget = PhysicsChainQuickWidget(self, label='Multiple Chains',
                                                       help='Make separate chains from each control yeah')
        self.simpleAimWidget.addNewSignal.connect(self.addNewSimpleAim)
        self.typeStack.addWidget(self.simpleAimWidget)

        self.pointWidget = PhysicsPointWidget(self)
        self.pointWidget.addNewSignal.connect(self.addNewPoint)
        self.typeStack.addWidget(self.pointWidget)

        self.stickWidget = SticksWidget(self)
        self.stickWidget.addNewSignal.connect(self.addNewStick)
        self.typeStack.addWidget(self.stickWidget)

        self.offsetButton = QPushButton('Update Constraint Offsets')
        self.offsetButton.clicked.connect(self.updateOffsets)

        self.stiffnessFalloffWidget = FalloffWidget(self)
        self.stiffnessFalloffWidget.pressedSignal.connect(self.setFalloff)
        self.falloffGroupBoxLayout.addWidget(self.stiffnessFalloffWidget)

        self.dragFalloffWidget = FalloffWidget(self, DAMPING, startDefault=0.2, endDefault=0.2)
        self.dragFalloffWidget.pressedSignal.connect(self.setFalloff)
        self.falloffGroupBoxLayout.addWidget(self.dragFalloffWidget)

        self.controlsScrollArea = QScrollArea()
        self.controlsScrollArea.setStyleSheet("QScrollArea{border: none;""background-color: black;"";}")

        self.controlsScrollArea.verticalScrollBar().setStyleSheet(styleSheet)
        self.controlsFrame.setStyleSheet(styleSheet)

        self.controlsScrollArea.setWidget(self.controlsFrame)
        self.controlsScrollArea.setWidgetResizable(True)
        self.controlsFrame.setLayout(self.controlsLayout)
        self.controlsGroupBoxLayout.addWidget(self.controlsScrollArea)

        menu = self.menuBar()

        file_menu = menu.addMenu('&File')
        new_action = QAction('New preset', self)
        new_action.setShortcut('Ctrl+N')
        file_menu.addAction(new_action)
        new_action.triggered.connect(self.newPreset)

        load_action = QAction('Load preset', self)
        load_action.setShortcut('Ctrl+O')
        file_menu.addAction(load_action)
        load_action.triggered.connect(self.loadPreset)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.savePreset)

        save_action = QAction('Save As', self)
        save_action.setShortcut('Ctrl+Shift+S')
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.saveAsPreset)

        apply_action = QAction('Apply preset from file', self)
        apply_action.setShortcut('Ctrl+Shift+O')
        file_menu.addAction(apply_action)
        apply_action.triggered.connect(self.applyPreset)

        help_menu = menu.addMenu('&Help')
        help_action = QAction('User Guide', self)
        help_action.setShortcut('F1')
        help_menu.addAction(help_action)
        help_action.triggered.connect(self.openHelpWindow)

        self.presetGroupBox = QGroupBox()
        # cuurent rig label
        self.currentPresetLabel = QLabel('Current Preset ::')
        self.currentPresetNameLabel = QLabel('None')

        self.rigLayout = QVBoxLayout()
        self.presetGroupBox.setLayout(self.rigLayout)
        self.rigLabelLayout = QHBoxLayout()
        self.rigLayout.addLayout(self.rigLabelLayout)
        self.rigLabelLayout.addWidget(self.currentPresetLabel)
        self.rigLabelLayout.addWidget(self.currentPresetNameLabel)

        self.cacheButton = QPushButton('Cache Anim')
        self.cacheButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.cacheButton.clicked.connect(self.cacheAnim)

        self.deactivateConstraintsButton = QPushButton('Deactivate Constraints')
        self.deactivateConstraintsButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.deactivateConstraintsButton.clicked.connect(self.deactivateConstraints)

        self.deleteChainButton = QPushButton('Delete Chain')
        self.deleteChainButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.deleteChainButton.clicked.connect(self.deleteChain)

        self.quickBakeButton = QPushButton('Quick Bake From Preset')
        self.quickBakeButton.clicked.connect(self.quickBakeFromPreset)

        self.toolboxButton = QPushButton('Open Toolbox')
        self.toolboxButton.clicked.connect(self.openToolbox)

        self.savePosesButton = QPushButton('Save Offsets')
        self.savePosesButton.clicked.connect(self.savePoses)

        self.cycleLabel = QLabel('Cycle')
        self.cycleCheckBox = AnimatedCheckBox('', width=32)
        self.cycleCheckBox.setChecked(self.cls.getCycleState())
        # self.cycleCheckBox.update_label(self.cls.getCycleState())
        self.SimulateButton = QPushButton('Simulate')
        self.cycleCheckBox.clicked.connect(self.toggleCycle)
        self.SimulateButton.clicked.connect(self.simulateAnim)

        self.bakeButton = QPushButton('Bake Animation to Controls')
        self.bakeButton.setFixedHeight(28 * dpiScale())
        self.bakeButton.clicked.connect(self.bakeAnimation)

        self.modifyGroupBox = QGroupBox('Edit')
        # Set the font size for the group box

        self.modifyLayout = QVBoxLayout()
        self.modifyLayout.setSpacing(2)
        self.modifyGroupBox.setLayout(self.modifyLayout)

        self.simulationGroupBox = QGroupBox('Simulation')
        self.simulationLayout = QVBoxLayout()
        self.simulationLayout.setContentsMargins(2, 16, 2, 2)
        self.simulationLayout.setSpacing(2)
        self.simulationGroupBox.setLayout(self.simulationLayout)

        # self.layout.addWidget(self.presetGroupBox)
        self.layout.addWidget(self.controlsGroupBox)
        self.layout.addWidget(self.createGroupBox)
        # self.layout.addWidget(self.falloffroupBox)
        # self.layout.addWidget(self.modifyGroupBox)
        self.layout.addWidget(self.simulationGroupBox)

        self.modifyLayout.addWidget(self.deactivateConstraintsButton)
        self.modifyLayout.addWidget(self.deleteChainButton)
        self.modifyLayout.addWidget(self.offsetButton)
        self.modifyLayout.addWidget(self.savePosesButton)

        self.simulateSubLayout = QHBoxLayout()
        self.cycleLayout = QHBoxLayout()
        self.cycleLayout.addWidget(self.cycleLabel)
        self.cycleLayout.addWidget(self.cycleCheckBox)

        self.simulationLayout.addWidget(self.savePosesButton)
        self.simulationLayout.addWidget(self.offsetButton)
        self.simulationLayout.addWidget(self.quickBakeButton)
        self.simulationLayout.addLayout(self.simulateSubLayout)
        self.simulateSubLayout.addLayout(self.cycleLayout)
        self.simulateSubLayout.addWidget(self.cacheButton)
        self.simulationLayout.addWidget(self.SimulateButton)
        self.simulationLayout.addWidget(self.toolboxButton)
        self.simulationLayout.addWidget(self.bakeButton)

        ####
        self.addNewEntryDialog = None
        self.addNewGroupDialog = None
        # self.controlsLayout.addStretch()
        # self.controlsLayout.addWidget(SwitchableObjectWidget(self))
        self.initPresetData()

    def resizeEvent(self, event):
        self.resized.emit()
        return super(PhysicsQuickUI, self).resizeEvent(event)

    def show(self):
        super(PhysicsQuickUI, self).show()
        self.resize(600, 300)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Warning',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            if self.addNewEntryDialog:
                try:
                    self.addNewEntryDialog.close()
                except:
                    pass
            if self.addNewGroupDialog:
                try:
                    self.addNewGroupDialog.close()
                except:
                    pass
        else:
            event.ignore()

        super(PhysicsQuickUI, self).closeEvent(event)

    def enableMainWidget(self):
        self.main_widget.setEnabled(True)

    def typeChanged(self, *args):
        self.typeStack.setCurrentIndex(args[0])
        self.createGroupBox.setTitle(self.typeCombo.currentText())
        # self.singleChainButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(1))
        # self.pointsButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(2))
        # self.constraintsButton.clicked.connect(lambda: self.typeStack.setCurrentIndex(3))

    @Slot()
    def toggleEnabledState(self, state):
        self.main_widget.setEnabled(state)

    def resizeOverlay(self):
        if self.overlay:
            self.overlay.resize(self.size())

    @Slot()
    def addNewChain(self, infoDict=dict()):

        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')

        self.cls.buildChainControls(sel,
                                    twist=infoDict.get('useTwist', False),
                                    lockFirst=infoDict.get('lockFirst', False),
                                    startStiffness=infoDict.get('startStiffness', 0.5),
                                    endStiffness=infoDict.get('endStiffness', 0.1),
                                    startDamp=infoDict.get('startDamp', 0.21),
                                    endDamp=infoDict.get('endDamp', 0.2),
                                    frameDelay=infoDict.get('endDelay', 1),
                                    falloffType=infoDict.get('falloffType', easeTypes[0]))

    @Slot()
    def addNewSimpleAim(self, twist):
        # TODO - need to update to dict
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')
        self.cls.buildSimpleAim(sel, twist=twist)

    @Slot()
    def addNewPoint(self, rotation):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')
        self.cls.buildPointControls(sel, rotation=rotation)

    @Slot()
    def addNewStick(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('select at least one control')
        controls = list()
        for s in sel:
            if cmds.attributeQuery('control', node=s, exists=True):
                controls.append(s)
                continue
            if cmds.attributeQuery(STIFFNESS, node=s, exists=True):
                controls.append(s)
                continue
            messageConnections = cmds.listConnections(s + '.message')
            if not messageConnections:
                continue
            for c in messageConnections:
                if cmds.attributeQuery('control', node=c, exists=True):
                    controls.append(c)
                    continue
        # print('controls', controls)
        if len(controls) < 2:
            return cmds.warning('Please select more than one control')

        for index, c in enumerate(controls[:-1]):
            stickParent = cmds.listRelatives(c, parent=True)[0]
            namespace, control = (':' + stickParent).rsplit(':', 1)
            stick = self.cls.createStick(c, controls[index + 1])
            cmds.parent(str(stick), stickParent)

    @Slot()
    def updateOffsets(self):
        self.cls.updateOffsets()

    @Slot()
    def setFalloff(self, startValue, endValue, mode, attribute, skipFirst):
        self.cls.setFalloff(startValue, endValue, mode, attribute, skipFirst)

    def remove(self):
        pass

    def initPresetData(self):
        self.collisionPresetData = PhysicsPresetData()

    def newPreset(self):
        self.initPresetData()
        self.refreshUI()
        self.currentPresetNameLabel.setText('untitled')

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            self.cls.presetDir,
                                            self.fileHint)
        return fname[0] or None

    def loadPreset(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.collisionPresetData = PhysicsPresetData()
        self.collisionPresetData.load(fname)
        self.cls.createControlsFromPreset(self.collisionPresetData)

        self.refreshUI()
        self.currentPresetNameLabel.setText(fname)

    def savePreset(self):
        preset = self.cls.getPointsAndSticks()
        currentFileName = self.collisionPresetData._fileName
        preset._fileName = str(currentFileName)
        self.collisionPresetData = preset
        if not self.collisionPresetData._fileName:
            self.saveAsPreset()
            return
        self.collisionPresetData.saveData(self.collisionPresetData._fileName)

    def saveAsPreset(self):
        save_filename = QFileDialog.getSaveFileName(self,
                                                    "Save file as",
                                                    self.cls.presetDir,
                                                    self.fileHint)
        if not save_filename:
            return

        self.collisionPresetData.saveData(save_filename[0])
        self.currentPresetNameLabel.setText(save_filename[0])
        self.collisionPresetData._fileName = save_filename[0]
        self.savePreset()
        return os.path.basename(save_filename[0])

    def openCreateHelpWindow(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.CreateHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.CreateHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.CreateIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.CreateHelp'])

    def openHelpWindow(self):
        # print ('openHelpWindow')
        helpFile = os.path.abspath(os.path.join(PhysicsTool().helpPath, 'tbCollisionToolsUserGuide.pdf'))
        os.startfile(helpFile)
        '''
        helpWidget = InfoPromptWidget(title='Coming soon',
                                      buttonText='Ok',
                                      # imagePath=IkFkTools().helpPath,
                                      error=False,
                                      # image=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpImage'],
                                      # gif=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpIsGif'],
                                      helpString="Full userguide is on it's way.")
        '''

    def applyPreset(self):
        """
        browse to preset and load it to the selected rig
        :return:
        """
        fname = self.browseToFile()
        if not fname:
            return None
        collisionPresetData = PhysicsPresetData()
        collisionPresetData.load(fname)
        self.cls.createControlsFromPreset(collisionPresetData)

    def savePoses(self):
        self.cls.saveCurrentRigData()

    def restoreSelectedPoses(self):
        self.cls.restoreCurrentRigData()

    def openToolbox(self):
        self.cls.toolBoxUI()

    def deactivateConstraints(self):
        self.cls.deactivateConstraints()

    def quickBakeFromPreset(self):
        self.cls.quickBakeFromPreset()

    def deleteChain(self):
        self.cls.deleteChain()

    def cacheAnim(self):
        self.cls.cacheAnim()

    def toggleCycle(self, state):
        self.cls.toggleCycle(state)

    def simulateAnim(self):
        if not self.cls.stickData:
            self.cls.cacheAnim()
        self.cls.simulate(self.cls.stickData, self.cls.controlPointDict, self.cls.axisList, self.cls.minTime,
                          self.cls.maxTime)

    def bakeAnimation(self):
        self.cls.bakeAnim()

    @staticmethod
    def clearLayout(layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refreshUI(self):
        """

        :return:
        """
        pass


class PhysicsSetupUI(QMainWindow):
    fileHint = "Physics Preset files (*.json)"
    resized = Signal()

    def __init__(self, cls):
        super(PhysicsSetupUI, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setObjectName('tbPhysics_SetupUI')

        self.collisionPresetData = None
        self.groupWidgets = dict()
        self.cls = cls
        self.rigName = str()
        self.namespace = str()
        self.collisionWidgets = dict()
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        windowTitle = title_str
        self.setWindowTitle(windowTitle)

        self.setWindowTitle('{o} :: v{v}'.format(o=windowTitle, v=PhysicsTool.version))

        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignTop)
        self.main_widget.setLayout(self.layout)

        self.controlsLayout = QVBoxLayout()
        self.controlsSpacerLayout = QVBoxLayout()
        self.controlsSpacerLayout.addStretch(100)
        self.controlsLayout.addLayout(self.controlsSpacerLayout)
        self.controlsLayout.setContentsMargins(4, 8, 0, 0)
        self.controlsLayout.setSpacing(0)
        self.controlsLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.controlsGroupBox = QBoldGroupBox('Mode selection')
        self.controlsGroupBoxLayout = QVBoxLayout()
        self.controlsGroupBox.setLayout(self.controlsGroupBoxLayout)

        self.falloffroupBox = QGroupBox('Falloff')
        self.falloffGroupBoxLayout = QVBoxLayout()
        self.falloffroupBox.setLayout(self.falloffGroupBoxLayout)

        self.controlsFrame = QFrame()

        self.chainWidget = PhysicsChainWidget(self, label='Chain')
        self.chainWidget.addNewSignal.connect(self.addNewChain)
        self.controlsGroupBoxLayout.addWidget(self.chainWidget)

        self.simpleAimWidget = PhysicsChainWidget(self, label='Singles')
        self.simpleAimWidget.addNewSignal.connect(self.addNewSimpleAim)
        self.controlsGroupBoxLayout.addWidget(self.simpleAimWidget)

        self.pointWidget = PhysicsPointWidget(self)
        self.pointWidget.addNewSignal.connect(self.addNewPoint)
        self.controlsGroupBoxLayout.addWidget(self.pointWidget)

        self.stickWidget = SticksWidget(self)
        self.stickWidget.addNewSignal.connect(self.addNewStick)
        self.controlsGroupBoxLayout.addWidget(self.stickWidget)

        self.offsetButton = QPushButton('Update Constraint Offsets')
        self.offsetButton.clicked.connect(self.updateOffsets)

        self.stiffnessFalloffWidget = FalloffWidget(self)
        self.stiffnessFalloffWidget.pressedSignal.connect(self.setFalloff)
        self.falloffGroupBoxLayout.addWidget(self.stiffnessFalloffWidget)

        self.dragFalloffWidget = FalloffWidget(self, DAMPING, startDefault=0.2, endDefault=0.2)
        self.dragFalloffWidget.pressedSignal.connect(self.setFalloff)
        self.falloffGroupBoxLayout.addWidget(self.dragFalloffWidget)

        self.controlsScrollArea = QScrollArea()
        self.controlsScrollArea.setStyleSheet("QScrollArea{border: none;""background-color: black;"";}")

        self.controlsScrollArea.verticalScrollBar().setStyleSheet(styleSheet)
        self.controlsFrame.setStyleSheet(styleSheet)

        self.controlsScrollArea.setWidget(self.controlsFrame)
        self.controlsScrollArea.setWidgetResizable(True)
        self.controlsFrame.setLayout(self.controlsLayout)
        self.controlsGroupBoxLayout.addWidget(self.controlsScrollArea)

        menu = self.menuBar()

        file_menu = menu.addMenu('&File')
        new_action = QAction('New preset', self)
        new_action.setShortcut('Ctrl+N')
        file_menu.addAction(new_action)
        new_action.triggered.connect(self.newPreset)

        load_action = QAction('Load preset', self)
        load_action.setShortcut('Ctrl+O')
        file_menu.addAction(load_action)
        load_action.triggered.connect(self.loadPreset)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.savePreset)

        save_action = QAction('Save As', self)
        save_action.setShortcut('Ctrl+Shift+S')
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.saveAsPreset)

        apply_action = QAction('Apply preset from file', self)
        apply_action.setShortcut('Ctrl+Shift+O')
        file_menu.addAction(apply_action)
        apply_action.triggered.connect(self.applyPreset)

        help_menu = menu.addMenu('&Help')
        help_action = QAction('User Guide', self)
        help_action.setShortcut('F1')
        help_menu.addAction(help_action)
        help_action.triggered.connect(self.openHelpWindow)

        self.presetGroupBox = QGroupBox()
        # cuurent rig label
        self.currentPresetLabel = QLabel('Current Preset ::')
        self.currentPresetNameLabel = QLabel('None')

        self.rigLayout = QVBoxLayout()
        self.presetGroupBox.setLayout(self.rigLayout)
        self.rigLabelLayout = QHBoxLayout()
        self.rigLayout.addLayout(self.rigLabelLayout)
        self.rigLabelLayout.addWidget(self.currentPresetLabel)
        self.rigLabelLayout.addWidget(self.currentPresetNameLabel)

        self.cacheButton = QPushButton('Cache Anim')
        self.cacheButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.cacheButton.clicked.connect(self.cacheAnim)

        self.deactivateConstraintsButton = QPushButton('Deactivate Constraints')
        self.deactivateConstraintsButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.deactivateConstraintsButton.clicked.connect(self.deactivateConstraints)

        self.deleteChainButton = QPushButton('Delete Chain')
        self.deleteChainButton.setToolTip(maya.stringTable['y_tb_physicsTool.create'])
        self.deleteChainButton.clicked.connect(self.deleteChain)

        self.toolboxButton = QPushButton('Open Toolbox')
        self.toolboxButton.clicked.connect(self.openToolbox)

        self.savePosesButton = QPushButton('Save Offsets')
        self.savePosesButton.clicked.connect(self.savePoses)

        self.cycleCheckBox = QPushButton('Cycle')
        self.SimulateButton = QPushButton('Simulate')
        self.SimulateButton.clicked.connect(self.simulateAnim)

        self.bakeButton = QPushButton('Bake Animation to Controls')
        self.bakeButton.setFixedHeight(42 * dpiScale())
        self.bakeButton.clicked.connect(self.bakeAnimation)

        self.createHelpButton = HelpButton(width=22, height=22)
        self.createHelpButton.clicked.connect(self.openCreateHelpWindow)

        self.modifyGroupBox = QGroupBox('Edit')
        self.modifyLayout = QHBoxLayout()
        self.modifyLayout.setSpacing(2)
        self.modifyGroupBox.setLayout(self.modifyLayout)

        self.simulationGroupBox = QGroupBox('Simulation')
        self.simulationLayout = QHBoxLayout()
        self.simulationLayout.setSpacing(2)
        self.simulationGroupBox.setLayout(self.simulationLayout)

        self.layout.addWidget(self.presetGroupBox)
        self.layout.addWidget(self.controlsGroupBox)
        self.layout.addWidget(self.falloffroupBox)
        self.layout.addWidget(self.modifyGroupBox)
        self.layout.addWidget(self.simulationGroupBox)

        self.modifyLayout.addWidget(self.deactivateConstraintsButton)
        self.modifyLayout.addWidget(self.deleteChainButton)
        self.modifyLayout.addWidget(self.offsetButton)
        self.modifyLayout.addWidget(self.savePosesButton)

        self.simulationLayout.addWidget(self.cacheButton)
        self.simulateSubLayout = QHBoxLayout()
        self.simulateSubLayout.addWidget(self.cycleCheckBox)
        self.simulateSubLayout.addWidget(self.SimulateButton)
        self.simulationLayout.addLayout(self.simulateSubLayout)
        self.simulationLayout.addWidget(self.toolboxButton)
        self.simulationLayout.addWidget(self.bakeButton)
        self.simulationLayout.addWidget(self.quickBakeButton)
        self.simulationLayout.addWidget(self.createHelpButton)

        ####
        self.addNewEntryDialog = None
        self.addNewGroupDialog = None
        # self.controlsLayout.addStretch()
        # self.controlsLayout.addWidget(SwitchableObjectWidget(self))
        self.initPresetData()

    def resizeEvent(self, event):
        self.resized.emit()
        return super(PhysicsSetupUI, self).resizeEvent(event)

    def show(self):
        super(PhysicsSetupUI, self).show()
        self.resize(600, 300)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Warning',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            if self.addNewEntryDialog:
                try:
                    self.addNewEntryDialog.close()
                except:
                    pass
            if self.addNewGroupDialog:
                try:
                    self.addNewGroupDialog.close()
                except:
                    pass
        else:
            event.ignore()

        super(PhysicsSetupUI, self).closeEvent(event)

    def enableMainWidget(self):
        self.main_widget.setEnabled(True)

    @Slot()
    def toggleEnabledState(self, state):
        self.main_widget.setEnabled(state)

    def resizeOverlay(self):
        if self.overlay:
            self.overlay.resize(self.size())

    @Slot()
    def addNewChain(self, twist):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')
        self.cls.buildChainControls(sel, twist=twist)

    @Slot()
    def addNewSimpleAim(self, twist):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')
        self.cls.buildSimpleAim(sel, twist=twist)

    @Slot()
    def addNewPoint(self, rotation):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('select at least one control')
        self.cls.buildPointControls(sel, rotation=rotation)

    @Slot()
    def addNewStick(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('select at least one control')
        controls = list()
        for s in sel:
            if cmds.attributeQuery('control', node=s, exists=True):
                controls.append(s)
                continue
            if cmds.attributeQuery(STIFFNESS, node=s, exists=True):
                controls.append(s)
                continue
            messageConnections = cmds.listConnections(s + '.message')
            if not messageConnections:
                continue
            for c in messageConnections:
                if cmds.attributeQuery('control', node=c, exists=True):
                    controls.append(c)
                    continue
        if len(controls) < 2:
            return cmds.warning('Please select more than one control')

        for index, c in enumerate(controls[:-1]):
            stickParent = cmds.listRelatives(c, parent=True)[0]
            namespace, control = (':' + stickParent).rsplit(':', 1)
            stick = self.cls.createStick(c, controls[index + 1])
            cmds.parent(str(stick), stickParent)

    @Slot()
    def updateOffsets(self):
        self.cls.updateOffsets()

    @Slot()
    def setFalloff(self, startValue, endValue, mode, attribute, skipFirst):
        self.cls.setFalloff(startValue, endValue, mode, attribute, skipFirst)

    def remove(self):
        pass

    def initPresetData(self):
        self.collisionPresetData = PhysicsPresetData()

    def newPreset(self):
        self.initPresetData()
        self.refreshUI()
        self.currentPresetNameLabel.setText('untitled')

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            self.cls.presetDir,
                                            self.fileHint)
        return fname[0] or None

    def loadPreset(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.collisionPresetData = PhysicsPresetData()
        self.collisionPresetData.load(fname)
        self.cls.createControlsFromPreset(self.collisionPresetData)

        self.refreshUI()
        self.currentPresetNameLabel.setText(fname)

    def savePreset(self):
        preset = self.cls.getPointsAndSticks()
        currentFileName = self.collisionPresetData._fileName
        preset._fileName = str(currentFileName)
        self.collisionPresetData = preset
        if not self.collisionPresetData._fileName:
            self.saveAsPreset()
            return
        self.collisionPresetData.saveData(self.collisionPresetData._fileName)

    def saveAsPreset(self):
        save_filename = QFileDialog.getSaveFileName(self,
                                                    "Save file as",
                                                    self.cls.presetDir,
                                                    self.fileHint)
        if not save_filename:
            return

        self.collisionPresetData.saveData(save_filename[0])
        self.currentPresetNameLabel.setText(save_filename[0])
        self.collisionPresetData._fileName = save_filename[0]
        return os.path.basename(save_filename[0])

    def openCreateHelpWindow(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.CreateHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.CreateHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.CreateIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.CreateHelp'])

    def openHelpWindow(self):
        # print ('openHelpWindow')
        helpFile = os.path.abspath(os.path.join(PhysicsTool().helpPath, 'tbCollisionToolsUserGuide.pdf'))
        os.startfile(helpFile)
        '''
        helpWidget = InfoPromptWidget(title='Coming soon',
                                      buttonText='Ok',
                                      # imagePath=IkFkTools().helpPath,
                                      error=False,
                                      # image=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpImage'],
                                      # gif=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpIsGif'],
                                      helpString="Full userguide is on it's way.")
        '''

    def applyPreset(self):
        """
        browse to preset and load it to the selected rig
        :return:
        """
        fname = self.browseToFile()
        if not fname:
            return None
        collisionPresetData = PhysicsPresetData()
        collisionPresetData.load(fname)
        self.cls.createControlsFromPreset(collisionPresetData)

    def savePoses(self):
        self.cls.saveCurrentRigData()

    def restoreSelectedPoses(self):
        self.cls.restoreCurrentRigData()

    def openToolbox(self):
        self.cls.toolBoxUI()

    def quickBakeFromPreset(self):
        self.cls.quickBakeFromPreset()

    def deactivateConstraints(self):
        print('deactivateConstraints')
        self.cls.deactivateConstraints()

    def deleteChain(self):
        self.cls.deleteChain()

    def cacheAnim(self):
        self.cls.buildLocatorsFromScene()
        self.cls.activateConstraints()
        self.cls.clearDicts()
        self.stickData, self.controlPointDict, self.axisList, self.physicsControls, self.startTime, self.endTime = self.cls.makePhysicsForScene()
        self.simulateAnim()

    def simulateAnim(self):
        self.cls.simulate(self.stickData, self.controlPointDict, self.axisList, self.startTime, self.endTime)

    def bakeAnimation(self):
        self.cls.bakeAnim()

    @staticmethod
    def clearLayout(layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refreshUI(self):
        """

        :return:
        """
        pass


class CollisionGroupWidget(QFrame):
    addControlsSignal = Signal(str)
    addNewCollisionEntrySignal = Signal(str, str)  # group name, limb name, limb type
    groupTypeChangedSignal = Signal(str, str)
    addNewChainEntrySignal = Signal(str, str)  # group name, limb name, limb type
    pickMainControlSignal = Signal(str, str)
    pickMainPathSignal = Signal(str, str)
    dropGroupSignal = Signal(str, str)
    dropControlSignal = Signal(str, str)
    useFootstepsSignal = Signal(bool, str)

    # send path creation signal to parent class
    createPathSignal = Signal(str)
    enableMainWidgetSignal = Signal(bool)
    removeGroupSignal = Signal(str)

    def __init__(self, mainWindow=None, label='Main', obj=str(), groupType=str(), *args, **kwargs):
        """
        Widget that houses the pathed objects, must specify path control, possible parent path
        :param obj:
        :param args:
        :param kwargs:
        """
        self.mainWindow = mainWindow
        QFrame.__init__(self, *args, **kwargs)
        self.setStyleSheet(styleSheet)

        self.setAcceptDrops(True)
        self.mainLayout = QVBoxLayout()
        self.subLayout = QVBoxLayout()
        self.subLayout.setContentsMargins(0, 0, 0, 0)
        self.subLayout.setSpacing(2)
        self.spacerItem = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.spacerItem2 = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controlsFrame = QGroupBox(label)

        self.controlsFrame.setLayout(self.subLayout)
        self.mainLayout.addWidget(self.controlsFrame)
        # self.controlsFrame.setFrameStyle(QFrame.Panel | QFrame.Raised)

        self.obj = obj
        self.groupType = groupType
        self.setLayout(self.mainLayout)
        self.nameLayout = QHBoxLayout()
        self.pathControlLayout = QHBoxLayout()
        self.topLayout = QHBoxLayout()
        self.secondLayout = QHBoxLayout()
        self.controlsLayout = QVBoxLayout()
        self.subPathLayout = QVBoxLayout()
        self.secondLayout.setContentsMargins(0, 0, 0, 0)
        self.controlsLayout.setContentsMargins(0, 0, 0, 0)
        self.subPathLayout.setContentsMargins(0, 0, 0, 0)

        self.subLayout.addLayout(self.nameLayout)
        self.subLayout.addLayout(self.pathControlLayout)
        self.subLayout.addLayout(self.topLayout)
        self.subLayout.addLayout(self.secondLayout)
        self.subLayout.addLayout(self.controlsLayout)
        self.subLayout.addLayout(self.subPathLayout)
        self.subLayout.addSpacerItem(self.spacerItem)
        self.subLayout.addStretch(100)

        self.groupName = label
        self.pathNameLabel = QLabel(self.groupName)
        self.controlLabel = QLabel('Group Name')
        self.controlLineEdit = QLineEdit(self.obj)
        # self.controlLineEdit.textChanged.connect(self.controlLineEditChanged)
        # self.controlLineEdit.setPlaceholderText(str_lbl_mainControl)
        self.cle_action_pick = self.controlLineEdit.addAction(QIcon(":/targetTransfoPlus.png"),
                                                              QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        # self.cle_action_pick.triggered.connect(self.pickMainControl)

        self.addChainEntryButton = QPushButton(maya.stringTable['y_tb_physicsTool.addChainLabel'])
        self.addChainEntryButton.setToolTip(maya.stringTable['y_tb_physicsTool.addChainToolTip'])
        self.addChainEntryButton.clicked.connect(self.addChainEntry)

        self.addCollisionEntryButton = QPushButton(maya.stringTable['y_tb_physicsTool.addFingerLabel'])
        self.addCollisionEntryButton.setToolTip(maya.stringTable['y_tb_physicsTool.addFingerEntryToolTip'])
        self.addCollisionEntryButton.clicked.connect(self.addCollisionEntry)

        self.deleteButton = QPushButton()
        self.deleteButton.setIcon((QIcon(':/deleteActive.png')))
        self.deleteButton.setFixedSize(24, 24)
        self.deleteButton.clicked.connect(self.removeGroupEntry)
        self.deleteButton.setToolTip(maya.stringTable['y_tb_physicsTool.deleteGroup'])
        self.addElementHelpButton = HelpButton(width=22, height=22)
        self.addElementHelpButton.clicked.connect(self.showAddElementHelp)

        # self.nameLayout.addWidget(self.pathNameLabel)
        self.nameLayout.addStretch()

        self.nameLayout.addWidget(self.addChainEntryButton)
        self.nameLayout.addWidget(self.addCollisionEntryButton)
        self.nameLayout.addWidget(self.deleteButton)
        self.nameLayout.addWidget(self.addElementHelpButton)
        self.mainLayout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def dragEnterEvent(self, e):
        # print ('dragEnterEvent', e.mimeData().text(), self.groupName)
        if hasattr(e.mimeData(), 'dataType'):
            self.setHoverSS()
            e.accept()

    def dragLeaveEvent(self, e):
        # print ('dragLeaveEvent', self.groupName)
        self.setNonHoverSS()
        e.accept()

    def setHoverSS(self):
        self.setStyleSheet("QGroupBox {"
                           "border-color: #ffa02f}"
                           )

    def setNonHoverSS(self):
        self.setStyleSheet("QGroupBox {"
                           "border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646)"
                           "}")

    def dropEvent(self, e):
        # TODO - make this actually reparent the collision entry
        e.setDropAction(Qt.MoveAction)
        self.setNonHoverSS()
        e.accept()
        if e.mimeData().dataType == 'control':
            self.dropControlSignal.emit(e.mimeData().text(), self.groupName)

    def showAddElementHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewElementHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewElementHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewElementIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewElementHelp'])

    '''
    def mouseMoveEvent(self, e):
        if e.buttons() != Qt.MiddleButton:
            return
        self.setHoverSS()
        mimeData = QMimeData()
        mimeData.setText(self.groupName)
        mimeData.dataType = 'group'
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())

        dropAction = drag.start(Qt.MoveAction)
        self.setNonHoverSS()
    '''


class FalloffWidget(QWidget):
    pressedSignal = Signal(float, float, str, str, bool)

    def __init__(self, cls, label=STIFFNESS, startDefault=0.5, endDefault=0.1):
        super(FalloffWidget, self).__init__()
        self.attribute = label
        self.mainWindow = cls
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('FalloffWidget')
        self.setLayout(self.mainLayout)

        self.stiffnessLabel = QLabel(label)
        self.stiffnessStartLabel = QLabel('Start')
        self.stiffnessEndLabel = QLabel('End')

        self.easeTypeCombo = QComboBox()
        for item in easeTypes:
            self.easeTypeCombo.addItem(item)
        self.easeTypeCombo.setFixedWidth(self.easeTypeCombo.sizeHint().width())
        # self.easeTypeCombo.setCurrentIndex(easeTypes.index(self.groupType))

        self.startSpinBox = QDoubleSpinBox()

        self.skipFirstCheckbox = QCheckBox()
        self.skipFirstLabel = QLabel('Skip First')
        # self.label.setFixedWidth(60)
        self.startSpinBox.setFixedWidth(48)
        self.startSpinBox.setValue(startDefault)
        self.startSpinBox.setSingleStep(0.01)
        self.startSpinBox.setMaximum(1.0)
        self.startSpinBox.setMinimum(0.0)

        self.endSpinBox = QDoubleSpinBox()
        # self.label.setFixedWidth(60)
        self.endSpinBox.setFixedWidth(48)
        self.endSpinBox.setValue(endDefault)
        self.endSpinBox.setSingleStep(0.01)
        self.endSpinBox.setMaximum(1.0)
        self.endSpinBox.setMinimum(0.0)

        self.editFalloffButton = QPushButton('Edit selection')
        self.editFalloffButton.setToolTip(maya.stringTable['y_tb_physicsTool.addChain'])
        self.addGroupHelpButton = HelpButton(width=22, height=22)
        self.addGroupHelpButton.clicked.connect(self.showAddGroupHelp)

        self.mainLayout.addWidget(self.stiffnessLabel)
        self.mainLayout.addStretch()

        self.mainLayout.addWidget(self.skipFirstLabel)
        self.mainLayout.addWidget(self.skipFirstCheckbox)
        self.mainLayout.addWidget(self.stiffnessStartLabel)
        self.mainLayout.addWidget(self.startSpinBox)
        self.mainLayout.addWidget(self.stiffnessEndLabel)
        self.mainLayout.addWidget(self.endSpinBox)
        self.mainLayout.addWidget(self.easeTypeCombo)
        self.mainLayout.addWidget(self.editFalloffButton)
        self.mainLayout.addWidget(self.addGroupHelpButton)

        # self.mainLayout.addStretch()

        self.editFalloffButton.clicked.connect(self.addNew)

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.pressedSignal.emit(self.startSpinBox.value(),
                                self.endSpinBox.value(),
                                self.easeTypeCombo.currentText(),
                                self.attribute,
                                self.skipFirstCheckbox.isChecked())


class FalloffMiniWidget(QWidget):
    # TODO - make this a data dict, not random variables
    # TODO - change the label, and add in damping/frame delay (softness)
    pressedSignal = Signal(float, float, str, str, bool)

    def __init__(self, cls, label=STIFFNESS, startDefault=0.5, endDefault=0.1):
        super(FalloffMiniWidget, self).__init__()
        self.attribute = label
        self.mainWindow = cls

        self.groupBox = QGroupBox(label)
        self.mainLayout = QVBoxLayout()
        self.groupBoxLayout = QFormLayout()
        self.groupBox.setLayout(self.groupBoxLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.groupBoxLayout.setContentsMargins(0, 16, 0, 0)
        self.setObjectName('FalloffWidget')
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.groupBox)

        self.stiffnessStartLabel = QLabel('Start')
        self.stiffnessEndLabel = QLabel('End')

        self.easeTypeCombo = QComboBox()
        self.easeTypeCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for item in easeTypes:
            self.easeTypeCombo.addItem(item)
        # self.easeTypeCombo.setFixedWidth(self.easeTypeCombo.sizeHint().width())
        # self.easeTypeCombo.setCurrentIndex(easeTypes.index(self.groupType))

        self.startSpinBox = QDoubleSpinBox()
        self.startSpinBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.label.setFixedWidth(60)
        # self.startSpinBox.setFixedWidth(48)
        self.startSpinBox.setValue(startDefault)
        self.startSpinBox.setSingleStep(0.01)
        self.startSpinBox.setMaximum(1.0)
        self.startSpinBox.setMinimum(0.0)

        self.endSpinBox = QDoubleSpinBox()
        self.endSpinBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # self.label.setFixedWidth(60)
        # self.endSpinBox.setFixedWidth(48)
        self.endSpinBox.setValue(endDefault)
        self.endSpinBox.setSingleStep(0.01)
        self.endSpinBox.setMaximum(1.0)
        self.endSpinBox.setMinimum(0.0)

        self.falloffButton = IconPushButton(width=64, height=64, icon=IconPath + '\easeInSine.png',
                                            comboBox=self.easeTypeCombo)
        self.falloffButton.setToolTip('Right click to pick falloff curve')
        self.falloffButton.setPopupMenu(FalloffTypePopup)
        self.falloffButton.returnSignal.connect(self.falloffPicked)
        self.falloffButton.clicked.connect(self.falloffButton._showMenu)
        self.easeTypeCombo.currentIndexChanged.connect(self.falloffButton.comboChanged)
        self.addGroupHelpButton = HelpButton(width=22, height=22)

        self.groupBoxLayout.addRow(self.stiffnessStartLabel, self.startSpinBox)
        self.groupBoxLayout.addRow(self.stiffnessEndLabel, self.endSpinBox)
        self.groupBoxLayout.addRow(self.falloffButton, self.easeTypeCombo)

        # self.mainLayout.addStretch()

    def falloffPicked(self, falloff):
        self.easeTypeCombo.setCurrentIndex(easeTypes.index(falloff))

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.pressedSignal.emit(self.startSpinBox.value(),
                                self.endSpinBox.value(),
                                self.easeTypeCombo.currentText(),
                                self.attribute,
                                self.skipFirstCheckbox.isChecked())


class FalloffCombinedWidget(QWidget):
    # TODO - make this a data dict, not random variables
    # TODO - change the label, and add in damping/frame delay (softness)
    pressedSignal = Signal(float, float, str, str, bool)

    def __init__(self, cls, label=STIFFNESS, startDefault=0.5, endDefault=0.1):
        super(FalloffCombinedWidget, self).__init__()
        self.attribute = label
        self.mainWindow = cls

        self.groupBox = QGroupBox(label)
        self.mainLayout = QVBoxLayout()
        self.groupBoxLayout = QFormLayout()
        self.groupBox.setLayout(self.groupBoxLayout)
        self.mainLayout.setContentsMargins(0, 12, 0, 0)
        self.groupBoxLayout.setContentsMargins(2, 16, 0, 0)
        self.setObjectName('FalloffWidget')
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.groupBox)

        self.stiffnessStartLabel = QLabel('Start')
        self.stiffnessEndLabel = QLabel('End')

        self.easeTypeCombo = QComboBox()
        self.easeTypeCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        for item in easeTypes:
            self.easeTypeCombo.addItem(item)
        # self.easeTypeCombo.setFixedWidth(self.easeTypeCombo.sizeHint().width())
        # self.easeTypeCombo.setCurrentIndex(easeTypes.index(self.groupType))

        self.stiffnessStartSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.5, step=0.01, expanding=True)
        self.stiffnessEndSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)

        self.dampingStartSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)
        self.dampingEndSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)

        self.frameDelaySpinBox = CustomSpinBox(defaultVal=1, step=0.01,
                                               setMin=False, setMax=False,
                                               expanding=True)
        self.lockFirstCheckbox = QCheckBox()
        self.lockFirstCheckbox.setChecked(True)
        self.lockFirstCheckbox.setFixedSize(24, 24)

        self.falloffButton = IconPushButton(width=64, height=64, icon=IconPath + '\easeInSine.png',
                                            comboBox=self.easeTypeCombo)
        self.falloffButton.setToolTip('Right click to pick falloff curve')
        self.falloffButton.setPopupMenu(FalloffTypePopup)
        self.falloffButton.returnSignal.connect(self.falloffPicked)
        self.falloffButton.clicked.connect(self.falloffButton._showMenu)
        self.easeTypeCombo.currentIndexChanged.connect(self.falloffButton.comboChanged)
        self.addGroupHelpButton = HelpButton(width=22, height=22)

        self.groupBoxLayout.addRow('Start stiffness', self.stiffnessStartSpinBox)
        self.groupBoxLayout.addRow('End stiffness', self.stiffnessEndSpinBox)
        self.groupBoxLayout.addRow('Start damping', self.dampingStartSpinBox)
        self.groupBoxLayout.addRow('End damping', self.dampingEndSpinBox)
        self.groupBoxLayout.addRow('Frame delay', self.frameDelaySpinBox)
        self.groupBoxLayout.addRow('Lock base', self.lockFirstCheckbox)
        self.groupBoxLayout.addRow(self.falloffButton, self.easeTypeCombo)

        # self.mainLayout.addStretch()

    def falloffPicked(self, falloff):
        self.easeTypeCombo.setCurrentIndex(easeTypes.index(falloff))

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.pressedSignal.emit(self.startSpinBox.value(),
                                self.endSpinBox.value(),
                                self.easeTypeCombo.currentText(),
                                self.attribute,
                                self.skipFirstCheckbox.isChecked())


class PhysicsChainWidget(QWidget):
    addNewSignal = Signal(bool)
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)
    sideUpdateSignal = Signal(str, str)

    def __init__(self, cls, label='Physics Chain ::'):
        super(PhysicsChainWidget, self).__init__()
        self.mainWindow = cls
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('PhysicsChainWidget')
        self.setLayout(self.mainLayout)

        self.groupTypeLabel = QLabel('%s ::' % label)
        self.twistCheckbox = AnimatedCheckBox('', width=32)
        self.twistLabel = QLabel('Use twist')
        self.addButton = QPushButton('Create from selection')
        self.addButton.setToolTip(maya.stringTable['y_tb_physicsTool.addChain'])
        self.addGroupHelpButton = HelpButton(width=22, height=22)
        self.addGroupHelpButton.clicked.connect(self.showAddGroupHelp)

        self.mainLayout.addWidget(self.groupTypeLabel)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.twistLabel)
        self.mainLayout.addWidget(self.twistCheckbox)

        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.addGroupHelpButton)

        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.addNewSignal.emit(self.twistCheckbox.isChecked())


class PhysicsChainQuickWidget(QWidget):
    addNewSignal = Signal(dict)
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)
    sideUpdateSignal = Signal(str, str)

    def __init__(self, cls, label='Physics Chain ::', help='Blah yeah'):
        super(PhysicsChainQuickWidget, self).__init__()
        self.mainWindow = cls
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('PhysicsChainWidget')
        self.setLayout(self.mainLayout)

        self.groupTypeLabel = QLabel(help)

        self.twistLabel = QLabel('Use Twist Control')
        self.twistCheckbox = AnimatedCheckBox('', width=32)
        # self.twistCheckbox.setFixedSize(24, 24)

        self.addButton = QPushButton('Create from selection')
        self.addButton.setToolTip(maya.stringTable['y_tb_physicsTool.addChain'])
        self.addGroupHelpButton = HelpButton(width=22, height=22)
        self.addGroupHelpButton.clicked.connect(self.showAddGroupHelp)
        # self.falloffButton = IconPushButton(width=64, height=64, icon=IconPath + '\easeInSine.png')
        # self.falloffButton.setToolTip('Right click to pick falloff curve')
        # self.falloffButton.setPopupMenu(FalloffTypePopup)
        # self.falloffButton.clicked.connect(self.adjustSelectedLayerDefault)

        # TODO - doesn't remember value
        self.constraintTypeWidget = RadioGroup(optionVarList=['Rotation',
                                                              'Position',
                                                              'Both'], defaultValue='Rotation',
                                               label='Constraint Type')
        self.checkBoxLayout = QVBoxLayout()
        self.checkBoxLayout.addWidget(self.constraintTypeWidget)

        self.constraintTypeWidget.formLayout.addRow(self.twistLabel, self.twistCheckbox)
        self.constraintTypeWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.falloffLayout = QVBoxLayout()
        self.stiffnessFalloffWidget = FalloffCombinedWidget(self, 'Falloff settings', startDefault=0.5, endDefault=0.05)
        # self.dragFalloffWidget = FalloffMiniWidget(self, DAMPING, startDefault=0.2, endDefault=0.2)

        self.falloffLayout.addWidget(self.stiffnessFalloffWidget)
        # self.falloffLayout.addWidget(self.dragFalloffWidget)

        ## UI arrangement
        self.mainLayout.addWidget(self.groupTypeLabel)
        self.mainLayout.addLayout(self.falloffLayout)
        self.mainLayout.addLayout(self.checkBoxLayout)
        # self.mainLayout.addWidget(self.falloffButton)
        self.mainLayout.addWidget(self.addButton)
        # self.mainLayout.addWidget(self.addGroupHelpButton)

        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        outData = {'startStiffness': self.stiffnessFalloffWidget.stiffnessStartSpinBox.value(),
                   'endStiffness': self.stiffnessFalloffWidget.stiffnessEndSpinBox.value(),
                   'startDamp': self.stiffnessFalloffWidget.dampingStartSpinBox.value(),
                   'endDamp': self.stiffnessFalloffWidget.dampingEndSpinBox.value(),
                   'falloffType': self.stiffnessFalloffWidget.easeTypeCombo.currentText(),
                   'lockFirst': self.stiffnessFalloffWidget.lockFirstCheckbox.isChecked(),
                   'startDelay': 0,
                   'endDelay': self.stiffnessFalloffWidget.frameDelaySpinBox.value(),
                   'useTwist': self.twistCheckbox.isChecked(),
                   'constraintType': 'TODO'
                   }

        self.addNewSignal.emit(outData)


class FalloffTypePopup(QWidget):
    pickedSignal = Signal(str, str)

    def __init__(self, name, parent=None, hideLabel=False):
        super(FalloffTypePopup, self).__init__(parent)
        self.hideLabel = hideLabel
        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.gridLayout = QGridLayout(self)
        self.setLayout(self.gridLayout)
        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        for i in range(len(easeTypes)):
            button = IconPushButton(width=64, height=64, icon=IconPath + '\{s}.png'.format(s=easeTypes[i]),
                                    value=easeTypes[i])
            row = i // 5
            col = i % 5
            self.gridLayout.addWidget(button, row, col)
            button.popupPicked.connect(self.picked)

    def create_layout(self):
        pass
        # layout.addRow("Size:", self.size_sb)
        # layout.addRow("Opacity:", self.opacity_sb)

    def picked(self, value, icon):
        self.pickedSignal.emit(value, icon)


class PhysicsPointWidget(QWidget):
    addNewSignal = Signal(bool)
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)
    sideUpdateSignal = Signal(str, str)

    def __init__(self, cls):
        super(PhysicsPointWidget, self).__init__()
        self.mainWindow = cls
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('PhysicsChainWidget')
        self.setLayout(self.mainLayout)

        self.groupTypeLabel = QLabel('Physics Points ::')
        self.twistCheckbox = QCheckBox()
        self.twistLabel = QLabel('Use rotation')
        self.addButton = QPushButton('Create from selection')
        self.addButton.setToolTip(maya.stringTable['y_tb_physicsTool.addPoint'])
        self.addGroupHelpButton = HelpButton(width=22, height=22)
        self.addGroupHelpButton.clicked.connect(self.showAddGroupHelp)

        self.mainLayout.addWidget(self.groupTypeLabel)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.twistLabel)
        self.mainLayout.addWidget(self.twistCheckbox)

        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.addGroupHelpButton)

        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.addNewSignal.emit(self.twistCheckbox.isChecked())


class SticksWidget(QWidget):
    addNewSignal = Signal()

    def __init__(self, cls):
        super(SticksWidget, self).__init__()
        self.mainWindow = cls
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('SticksWidget')
        self.setLayout(self.mainLayout)

        self.groupTypeLabel = QLabel('Stick Constraints ::')
        self.twistCheckbox = QCheckBox()
        self.twistLabel = QLabel('Use rotation')
        self.addButton = QPushButton('Connect selection')
        self.addButton.setToolTip(maya.stringTable['y_tb_physicsTool.addPoint'])
        self.addGroupHelpButton = HelpButton(width=22, height=22)
        self.addGroupHelpButton.clicked.connect(self.showAddGroupHelp)

        self.mainLayout.addWidget(self.groupTypeLabel)
        self.mainLayout.addStretch()
        # self.mainLayout.addWidget(self.twistCheckbox)
        # self.mainLayout.addWidget(self.twistLabel)

        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.addGroupHelpButton)

        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)

    def showAddGroupHelp(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=PhysicsTool().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'],
                                      gif=maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'],
                                      helpString=maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'])

    def addNew(self):
        self.addNewSignal.emit()

    def toJson(self):
        pass


class ObjectListWidget(QWidget):
    editedSignalKey = Signal(str, list)

    def __init__(self, key=str(), label=str()):
        super(ObjectListWidget, self).__init__()
        self.key = key
        self.mainListItem = str()
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(self.mainLayout)
        self.topLayout = QHBoxLayout()
        self.topLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label = QLabel(label)
        self.pickButtonLayout = QVBoxLayout()
        self.pickButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.pickButtonLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.pickButton = QPushButton('< Pick from selection')

        self.listwidget = QListWidget()

        self.topLayout.addWidget(self.label)
        self.mainLayout.addLayout(self.topLayout)
        # self.mainLayout.addStretch(100)
        self.mainLayout.addWidget(self.listwidget)
        # self.pickButtonLayout.addWidget(self.pickButton)
        self.mainLayout.addLayout(self.pickButtonLayout)

        self.pickButton.clicked.connect(self.pickButtonPressed)

    def currentItems(self):
        return [self.listwidget.item(x).text() for x in range(self.listwidget.count())]

    def recieveMainDestinationClicked(self, item):
        self.mainListItem = item

    @Slot()
    def sendUpdateSignal(self):
        self.editedSignalKey.emit(self.key, self.currentItems())

    def pickButtonPressed(self, override=None):
        if not override:
            sel = cmds.ls(selection=True, type='transform')
        else:
            sel = override
        self.listwidget.clear()
        if sel:
            items = [s.stripNamespace() for s in sel]
            self.listwidget.addItems(items)
        self.sendUpdateSignal()

    def addButtonPressed(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return
        items = [s.stripNamespace() for s in sel]
        currentItems = self.currentItems()
        resultItems = self.currentItems()
        # print 'before', currentItems
        self.listwidget.clear()
        for i in items:
            if i not in currentItems:
                resultItems.append(i)
        # print 'after', resultItems
        self.listwidget.addItems(resultItems)
        self.sendUpdateSignal()

    def addFromDestinationPressed(self):
        currentItems = self.currentItems()
        resultItems = self.currentItems()

        self.listwidget.clear()
        resultItems.append(self.mainListItem)

        self.listwidget.addItems(resultItems)
        self.sendUpdateSignal()

    def removeButtonPressed(self):
        listItems = self.listwidget.selectedItems()
        if not listItems: return
        for item in listItems:
            self.listwidget.takeItem(self.listwidget.row(item))
        self.sendUpdateSignal()

    def setCurrentItems(self, itemList):
        self.listwidget.clear()
        self.listwidget.addItems(itemList)

    def refreshUI(self, targets):
        self.listwidget.clear()
        self.listwidget.addItems(targets)


class CollisionToolbox(BaseDialog):
    def __init__(self, rigName=str, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                 title='Collision Toolbox', text=str()):
        super(CollisionToolbox, self).__init__(parent=parent, title=title, text=text)
        self.rigName = rigName

        self.setFixedSize(self.sizeHint())


def raiseOk(errorMessage, title='Success'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              error=False,
                              # image='curves.png',
                              helpString=errorMessage)


def raiseError(errorMessage, title='Failed'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              error=True,
                              helpString=errorMessage)
    return False


class IconPushButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """
    pickedSignal = Signal(str, str)
    popupPicked = Signal(str, str)
    returnSignal = Signal(str)

    def __init__(self, icon='', toolTip='', width=18, height=18, value=str(), comboBox=None):
        super(IconPushButton, self).__init__()
        self.icon = icon
        self.comboBox = comboBox
        self.iconWidth = width
        self.iconHeight = height
        self.setCurrentIcon()
        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)
        self.pop_up_window = None
        self.value = value
        self.clicked.connect(self.popupItemPicked)

    def setCurrentIcon(self):
        self.pixmap = QPixmap("{0}".format(self.icon)).scaled(self.iconWidth - 4, self.iconHeight - 4)
        self.setIcon(QIcon(self.pixmap))
        self.setIconSize(self.pixmap.size())
        self.setFixedSize(self.iconWidth, self.iconHeight)

    def comboChanged(self):
        self.icon = IconPath + '\{s}.png'.format(s=self.comboBox.currentText())
        self.setCurrentIcon()

    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)
        self.pop_up_window.pickedSignal.connect(self.picked)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)
            self.pop_up_window.show()

    @Slot()
    def popupItemPicked(self):
        self.popupPicked.emit(self.value, self.icon)

    def picked(self, value, icon):
        pixmap = QPixmap("{0}".format(icon)).scaled(self.iconWidth - 4, self.iconHeight - 4)
        self.setIcon(QIcon(pixmap))
        self.setIconSize(pixmap.size())
        self.setFixedSize(self.iconWidth, self.iconHeight)
        self.returnSignal.emit(value)
        self.pop_up_window.hide()


# TODO
"""
Make the point/aim constraints
align the axis for the up stuff
Bake out the up axis itself on the aim constraint
Figure out how to pass on the correct objects for constraining
Aim use local vector up, maybe just cross product the side and up, and the next target-current?
"""


class RadioGroup(QWidget):
    editedSignal = Signal(str)
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionValue = str()

    def __init__(self, optionVarList=list(), optionVar='defaultOptionVar', defaultValue=str(), label=str(),
                 tooltips=list()):
        super(RadioGroup, self).__init__()
        self.tooltips = tooltips
        self.optionVarList = optionVarList
        self.defaultValue = defaultValue
        self.optionVar = optionVar
        self.optionValue = get_option_var(self.optionVar, defaultValue)
        self.formLayout = QFormLayout()
        self.setLayout(self.formLayout)
        self.btnGrp = QButtonGroup()  # Letter group
        self.returnedWidgets = list()
        self.buttons = list()
        for index, option in enumerate(self.optionVarList):
            button = QRadioButton(option)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.buttons.append(button)
            self.btnGrp.addButton(self.buttons[index])
            self.returnedWidgets.append(['option', self.buttons[index]])
            self.buttons[index].setChecked(self.optionValue == option)
            self.buttons[index].toggled.connect(self.buttonChecked)
            if index == 0:
                self.formLayout.addRow(label, self.buttons[index])
            else:
                self.formLayout.addRow('', self.buttons[index])

            try:
                self.buttons[index].setToolTip(self.tooltips[index])
            except:
                pass

    def buttonChecked(self, value):
        for button in self.buttons:
            if button.isChecked() == True:
                self.editedSignal.emit(button.text())
                set_option_var(self.optionVar, button.text())


def find_top_parent(obj):
    parent = cmds.listRelatives(obj, parent=True)
    if parent:
        return find_top_parent(parent[0])
    else:
        return obj


class DeleteButton(QPushButton):
    """
    Just an icon button with a bin for the image
    """

    def __init__(self, text='', icon=":delete.png"):
        super(DeleteButton, self).__init__()
        self.setFlat(False)
        self.setText(text)
        # self.setIconSize(QSize(22, 22))
        self.setFixedSize(QSize(22 * dpiScale(), 22 * dpiScale()))
        self.setIcon(QIcon(icon))


class SearchProxyModel(QSortFilterProxyModel):
    def setFilterRegExp(self, pattern):
        if isinstance(pattern, str):
            pattern = QRegExp(pattern, Qt.CaseInsensitive, QRegExp.FixedString)
        super(SearchProxyModel, self).setFilterRegExp(pattern)

    def _accept_index(self, idx):
        if idx.isValid():
            text = idx.data(Qt.DisplayRole)
            if self.filterRegExp().indexIn(text.lower()) >= 0:
                return True
            for row in range(idx.model().rowCount(idx)):
                if self._accept_index(idx.model().index(row, 0, idx)):
                    return True
        return False

    def filterAcceptsRow(self, sourceRow, sourceParent):
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self._accept_index(idx)


class ReOrderListWidget(QListWidget):
    checkedSignal = Signal(int, str, Qt.CheckState)
    currentItemChangedSignal = Signal(list)

    """
    Re orderable list widget with checkboxes for maintain offset
    """

    def __init__(self):
        super(ReOrderListWidget, self).__init__()
        self.itemChanged.connect(self.__sendCheckedSignal)
        self.currentItemChanged.connect(self.__sendCurrentItemSignal)

    def __sendCurrentItemSignal(self, item):
        # print ('__sendCurrentItemSignal, ', self.count())
        try:
            itemStrings = [str(self.item(x).widget.text) for x in range(self.count())]
        except:
            return
        # print ('__sendCurrentItemSignal', itemStrings)
        self.currentItemChangedSignal.emit(itemStrings)

    def __sendCheckedSignal(self, item):
        r_idx = self.row(item)
        r_str = item.text()
        state = item.checkState()
        self.checkedSignal.emit(r_idx, r_str, state)

    def setListItems(self, widgets):
        # print ('setListItems', widgets)
        self.blockSignals(True)
        self.clear()
        for w in widgets:
            w.blockSignals(True)
            item = QListWidgetItem(self)
            item.widget = w
            self.addItem(item)
            item.setSizeHint(w.minimumSizeHint())
            self.setItemWidget(item, w)
        for w in widgets:
            w.blockSignals(False)
        self.blockSignals(False)
        self.setDragDropMode(self.InternalMove)

    def dropEvent(self, event):
        super(ReOrderListWidget, self).dropEvent(event)
        # print ('drop event', event)
        self.__sendCurrentItemSignal(None)


class PhysicsToolbox(QMainWindow):
    widgets = list()
    deleteButtons = list()

    def __init__(self, cls):
        super(PhysicsToolbox, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setObjectName('tbPhysics_EditUI')
        self.setWindowTitle('tbPhysics - Edit')
        self.cls = cls
        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        self.mainLayout = QVBoxLayout()
        self.main_widget.setLayout(self.mainLayout)
        self.chainLayout = QGridLayout()
        self.mainLayout.addLayout(self.chainLayout)

        self.treeView = QListView()
        self.filter_line_edit = QLineEdit()
        self.filter_line_edit.setPlaceholderText('Type to filter...')

        self.model = QStringListModel()
        items = ['Apple', 'Banana', 'Cherry', 'Date', 'Fig', 'Grape', 'Kiwi', 'Lemon', 'Mango', 'Nectarine']
        self.model.setStringList(items)

        # Set up the proxy model for filtering
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)  # Assuming filtering on the first column
        self.treeView.setSelectionMode(QListView.MultiSelection)
        # Connect the line edit to the proxy model filter
        self.filter_line_edit.textChanged.connect(self.proxy_model.setFilterFixedString)

        # Set the proxy model on the list view
        self.treeView.setModel(self.proxy_model)
        self.treeView.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Set the layout on the main widget

        self.mainLayout.addWidget(self.filter_line_edit)
        self.mainLayout.addWidget(self.treeView)

    def on_selection_changed(self, selected, deselected):
        # Get the selected items
        selected_indexes = self.treeView.selectionModel().selectedIndexes()
        selected_items = [index.data() for index in selected_indexes]

        print("Selected items:", selected_items)

    def filterRegExpChanged(self, value):
        self.proxyModel.setFilterRegExp(value.lower())

    def itemClicked(self, item):
        print('item', item)

    def add_Row(self, chainName):
        # Create widgets for the row
        # TODO - make data for chain here and send it to the widget to set the values
        widget = ChainWidget(chainName)
        widget.setObjectName(chainName)
        widget.chainEditedSignal.connect(self.cls.editChainFalloff)
        widget.selectSignal.connect(self.cls.selectChain)

        widget.deleteButton.clicked.connect(self.button_pushed)
        self.mainLayout.addWidget(widget)

        rowCount = len(self.widgets)
        # Add widgets to the layout
        # print(widget.getWidgets())
        for i, w in enumerate(widget.getWidgets()):
            # print("adding", rowCount, i)
            self.chainLayout.addWidget(w, rowCount, i)

        # Store widgets in a list
        self.widgets.append(widget)
        self.deleteButtons.append(widget.deleteButton)
        self.setStyleSheet(getqss.getStyleSheet())

    def refreshUI(self):
        physicsData = self.cls.getPointsAndSticks()
        existingNames = [x.objectName() for x in self.widgets]

        for chainName, chain in physicsData.chains.items():

            if chainName in existingNames:
                continue
            self.add_Row(chainName)

        self.treeView.clear()
        customWidgets = [DefinedPhysicsChainWidget for k in physicsData.chains.keys()]
        for w in customWidgets:
            w.blockSignals(True)
        self.treeView.setListItems(customWidgets)
        for widget in customWidgets:
            # widget.editedSignal.connect(self.sendSpaceEditedSignal)
            widget.blockSignals(False)

    def button_pushed(self):
        senderIdx = self.deleteButtons.index(self.sender())
        widget = self.widgets[senderIdx]
        self.cls.deleteChainByName(chainName=self.widgets[senderIdx].chainName)
        self.remove_row(senderIdx)

    def remove_row(self, row):
        # Remove widgets from layout
        for col in range(self.chainLayout.columnCount()):
            item = self.chainLayout.itemAtPosition(row, col)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        # Remove widgets from the list
        del self.widgets[row]
        del self.deleteButtons[row]

        # Adjust layout
        for r in range(row, len(self.widgets)):
            for c in range(self.chainLayout.columnCount()):
                item = self.chainLayout.itemAtPosition(r + 1, c)
                if item is not None:
                    self.chainLayout.addWidget(item.widget(), r, c)


class DefinedPhysicsChainWidget(QWidget):
    editedSignal = Signal(str, str, str)
    """
    Widget for an individual space element
    """

    def __init__(self, spaceName=str(), driver=str()):
        super(DefinedPhysicsChainWidget, self).__init__()
        self.text = spaceName
        self.driver = driver
        self.row = QHBoxLayout()
        self.row.setContentsMargins(0, 0, 0, 0)
        self.spaceNameLineEdit = QLineEdit(spaceName)
        self.spaceNameLineEdit.textEdited.connect(self.sendEditedSignal)
        self.spaceDriverLineEdit = ObjectSelectLineEditEnforced(label='Driver')
        self.spaceDriverLineEdit.setTextNoUpdate(driver)

        self.setLayout(self.row)
        self.row.addWidget(self.spaceNameLineEdit)
        self.row.addWidget(self.spaceDriverLineEdit)

        # self.setStyleSheet(loadStyle.loadStyleSheet())

    def sendEditedSignal(self, *args):
        self.editedSignal.emit(self.text, args[0], self.spaceDriverLineEdit.lineEdit.text())
        self.text = args[0]


class ChainWidget(QWidget):
    chainEditedSignal = Signal(str, dict)
    selectSignal = Signal(str)

    def __init__(self, chain=None):
        super(ChainWidget, self).__init__()
        self.chainName = chain
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.nameLabel = QLabel(chain)
        self.nameLabel.setFont(semiBoldFont())
        self.deleteButton = DeleteButton()
        self.selectButton = QPushButton('Select')
        # self.reSimButton = QPushButton('Re-Sim')
        self.easeTypeCombo = QComboBox()
        for item in easeTypes:
            self.easeTypeCombo.addItem(item)
        self.falloffButton = IconPushButton(width=36, height=36, icon=IconPath + '\easeInSine.png',
                                            comboBox=self.easeTypeCombo)
        self.falloffButton.setToolTip('Right click to pick falloff curve')
        self.falloffButton.setPopupMenu(FalloffTypePopup)
        self.falloffButton.returnSignal.connect(self.falloffPicked)
        self.falloffButton.clicked.connect(self.falloffButton._showMenu)
        self.easeTypeCombo.currentIndexChanged.connect(self.falloffButton.comboChanged)

        self.stiffnessLabel = QLabel('Stiffness ->')
        self.stiffnessLabel.setFont(semiBoldFont())
        self.stiffnessStartLabel = QLabel('Start')
        self.stiffnessEndLabel = QLabel('End')
        self.dampingLabel = QLabel('Damping ->')
        self.dampingLabel.setFont(semiBoldFont())
        self.dampStartLabel = QLabel('Start')
        self.dampEndLabel = QLabel('End')

        self.stiffnessStartSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.5, step=0.01, expanding=True)
        self.stiffnessEndSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)

        self.dampingStartSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)
        self.dampingEndSpinBox = CustomSpinBox(minVal=0, maxVal=1, defaultVal=0.1, step=0.01, expanding=True)

        self.delaylabel = QLabel('Delay ->')
        self.delaylabel.setFont(semiBoldFont())
        self.delayStartLabel = QLabel('Start')
        self.delayEndLabel = QLabel('End')
        self.frameDelayStartSpinBox = CustomSpinBox(defaultVal=0, step=0.01,
                                                    setMin=False, setMax=False, expanding=True)
        self.frameDelayEndSpinBox = CustomSpinBox(defaultVal=5, step=0.01,
                                                  setMin=False, setMax=False, expanding=True)
        self.skipFirstCheckbox = QCheckBox()
        self.skipFirstLabel = QLabel('Skip First')

        self.editFalloffButton = QPushButton('Edit selection')

        self.mainLayout.addWidget(self.deleteButton)
        self.mainLayout.addWidget(self.nameLabel)
        self.mainLayout.addWidget(self.falloffButton)
        self.mainLayout.addWidget(self.easeTypeCombo)
        self.mainLayout.addWidget(self.skipFirstLabel)
        self.mainLayout.addWidget(self.skipFirstCheckbox)
        self.mainLayout.addWidget(self.stiffnessLabel)
        self.mainLayout.addWidget(self.stiffnessStartLabel)
        self.mainLayout.addWidget(self.stiffnessStartSpinBox)
        self.mainLayout.addWidget(self.stiffnessEndLabel)
        self.mainLayout.addWidget(self.stiffnessEndSpinBox)
        self.mainLayout.addWidget(self.dampingLabel)
        self.mainLayout.addWidget(self.dampStartLabel)
        self.mainLayout.addWidget(self.dampingStartSpinBox)
        self.mainLayout.addWidget(self.dampEndLabel)
        self.mainLayout.addWidget(self.dampingEndSpinBox)
        self.mainLayout.addWidget(self.delaylabel)
        self.mainLayout.addWidget(self.delayStartLabel)
        self.mainLayout.addWidget(self.delayEndLabel)
        self.mainLayout.addWidget(self.frameDelayStartSpinBox)
        self.mainLayout.addWidget(self.frameDelayEndSpinBox)

        self.mainLayout.addWidget(self.editFalloffButton)
        self.mainLayout.addWidget(self.selectButton)

        self.editFalloffButton.clicked.connect(self.editChain)
        self.selectButton.clicked.connect(self.selectChain)

    def selectChain(self):
        self.selectSignal.emit(self.chainName)

    def editChain(self):
        outDict = {'startStiffness': self.stiffnessStartSpinBox.value(),
                   'endStiffness': self.stiffnessEndSpinBox.value(),
                   'startDamp': self.stiffnessStartSpinBox.value(),
                   'endDamp': self.stiffnessEndSpinBox.value(),
                   'falloffType': self.easeTypeCombo.currentText(),
                   'skipFirst': self.skipFirstCheckbox.isChecked(),
                   'startDelay': 0,
                   'endDelay': 0,
                   'chain': None
                   }
        self.chainEditedSignal.emit(self.chainName, outDict)

    def falloffPicked(self, falloff):
        self.easeTypeCombo.setCurrentIndex(easeTypes.index(falloff))

    def getWidgets(self):
        return [
            self.deleteButton,
            self.nameLabel,
            self.falloffButton,
            self.easeTypeCombo,
            self.skipFirstLabel,

            self.skipFirstCheckbox,
            self.stiffnessLabel,
            self.stiffnessStartLabel,
            self.stiffnessStartSpinBox,
            self.stiffnessEndLabel,
            self.stiffnessEndSpinBox,
            self.dampingLabel,
            self.dampStartLabel,
            self.dampingStartSpinBox,
            self.dampEndLabel,
            self.dampingEndSpinBox,
            self.delaylabel,
            self.delayStartLabel,
            self.delayEndLabel,
            self.frameDelayStartSpinBox,
            self.frameDelayEndSpinBox,

            self.editFalloffButton,
            self.selectButton
        ]


class CustomSpinBox(QDoubleSpinBox):
    def __init__(self, minVal=0, maxVal=1, defaultVal=0, step=0.01, setMin=True, setMax=True, expanding=False, *args,
                 **kwargs):
        super(CustomSpinBox, self).__init__(*args, **kwargs)
        # self.label.setFixedWidth(60)
        if not expanding:
            self.setFixedWidth(48)
        else:
            self.setMinimumWidth(self.sizeHint().width())
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setValue(defaultVal)
        self.setSingleStep(step)
        if setMax:
            self.setMaximum(maxVal)
        if setMin:
            self.setMinimum(minVal)
        else:
            self.setMinimum(-999999999)


class CheckableButton(AnimatedCheckBox):
    def __init__(self, on_label, off_label, *args, **kwargs):
        super(CheckableButton, self).__init__(*args, **kwargs)
        # self.setCheckable(True)
        self.on_label = on_label
        self.off_label = off_label
        self.toggled.connect(self.update_label)

    def update_label(self, checked):
        if checked:
            self.setText(self.on_label)
        else:
            self.setText(self.off_label)
