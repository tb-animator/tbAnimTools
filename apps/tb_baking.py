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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory('tbtools_baking')
        self.addCommand(self.tb_hkey(name='simpleBakeToOverride', annotation='constrain to objects with NO offset - post baked, constraint reversed',
                                     category=self.category, command=['bakeTools.bake_to_override()']))
        self.setCategory('tbtools_constraints')
        self.addCommand(self.tb_hkey(name='bakeToLocator', annotation='constrain to object to locator',
                                     category=self.category, command=['bakeTools.bake_to_locator(constrain=True, orientOnly=False)']))
        self.addCommand(self.tb_hkey(name='bakeToLocatorRotation', annotation='constrain to object to locator - rotate only',
                                     category=self.category, command=['bakeTools.bake_to_locator(constrain=True, orientOnly=True)']))

        self.addCommand(self.tb_hkey(name='simpleConstraintOffset', annotation='constrain to objects with offset',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=True, postBake=False)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffset', annotation='constrain to objects with NO offset',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=False, postBake=False)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintOffsetPostBake', annotation='constrain to objects with offset - post baked',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=True, postBake=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffsetPostBake', annotation='constrain to objects with NO offset - post baked',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=False, postBake=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintOffsetPostBakeReverse', annotation='constrain to objects with offset - post baked, constraint reversed',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=True, postBake=True, postReverseConst=True)']))
        self.addCommand(self.tb_hkey(name='simpleConstraintNoOffsetPostBakeReverse', annotation='constrain to objects with NO offset - post baked, constraint reversed',
                                     category=self.category, command=['bakeTools.parentConst(constrainGroup=False, offset=False, postBake=True, postReverseConst=True)']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')

class bakeTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'bakeTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if bakeTools.__instance is None:
            bakeTools.__instance = object.__new__(cls)

        bakeTools.__instance.val = cls.toolName
        return bakeTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(bakeTools, self).optionUI()
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    """
    Functions
    """

    def bake_to_override(self):
        sel = pm.ls(sl=True)
        preBakeLayers = pm.ls(type='animLayer')
        keyRange = list(sorted(set(cmds.keyframe(query=True, timeChange=True))))
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
            pm.setAttr(newAnimLayer + ".ghostColor", 16)
            pm.rename(newAnimLayer, sel[0].namespace()[:-1] + '_' + sel[0].stripNamespace() + '_baked')

    def bake_to_locator(self, constrain=False, orientOnly=False):
        sel = pm.ls(sl=True)
        locs = []
        constraints = []
        if sel:
            for s in sel:
                loc = pm.spaceLocator(name=s + '_baked')
                print loc
                loc.localScale.set(10, 10, 10)
                loc.rotateOrder.set(2)
                loc.getShape().overrideEnabled.set(True)
                loc.getShape().overrideColor.set(14)
                const = pm.parentConstraint(s, loc)
                locs.append(loc)
                constraints.append(const)
        if locs:
            pm.bakeResults(locs,
                           simulation=False,
                           disableImplicitControl=False,
                           time=[pm.playbackOptions(query=True, minTime=True),
                                 pm.playbackOptions(query=True, maxTime=True)],
                           sampleBy=1)
            if constrain:
                pm.delete(constraints)
                for cnt, loc in zip(sel, locs):
                    skipT =self.funcs.getAvailableTranslates(cnt)
                    skipR=self.funcs.getAvailableRotates(cnt)
                    pm.parentConstraint(loc, cnt, skipTranslate={True: ('x', 'y', 'z'), False: skipT}[orientOnly],
                                        skipRotate=skipR)

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


    def quickBake(self, node):
        pm.bakeResults(node,
                       simulation=False,
                       disableImplicitControl=False,
                       time=[pm.playbackOptions(query=True, minTime=True),
                             pm.playbackOptions(query=True, maxTime=True)],
                       sampleBy=1)

        pm.delete(node.listRelatives(type='constraint'))
        self.clearBlendAttrs(node)

'''    
class bakeToLayer():
    def __init__(self):
        self.sel = cmds.ls(selection=True)
        self.objs = dict()

        print self.sel

        for s in self.sel: self.objs[s] = self.makeLocator(s)

        isolator().isolateAll(state=True)


        isolator().isolateAll(state=False)

    def makeLocator(self, obj):
        loc = cmds.spaceLocator(name='%s_BAKED_' % obj)[0]
        cmds.parentConstraint(obj, loc, maintainOffset=False)
        return loc

    def bake(self):
        print 'Baking', self.objs

        # bake the keys down on the new layer
        cmds.bakeResults(list(self.objs.values()), simulation=False,
                         disableImplicitControl=False,
                         #removeBakedAttributeFromLayer=False,
                         #destinationLayer=resultLayer,
                         #bakeOnOverrideLayer=False,
                         time=(0, 100),
                         sampleBy=1)

        pass

    def unBake(self):
        pass

'''



def space_list_intersection(selection_dict):
    '''
    Returns only the spaces that are shared between all input nodes
    :param selection_dict:
    :return:
    '''
    ordered_spaces = []

    all_spaces = [pm.Attribute(key + '.' + value).getEnums() for key, value in selection_dict.items()]
    for space in all_spaces:
        ordered_sub_space = []
        for index in range(len(space)):
            ordered_sub_space.append(space.key(index))
        ordered_spaces.append(ordered_sub_space)

    return list(sorted(set(ordered_spaces[0]).intersection(*ordered_spaces), key=ordered_spaces[0].index))

def get_space_string(node):
    node = pm.PyNode(node)
    return node.SpaceSwitch.getEnums().keys()

def get_space_name(node, attr, spaceName):
    # print node.SpaceSwitch.getEnums().keys()
    matching_space = [space for space in pm.Attribute(attr, node=node).getEnums().keys() if spaceName.lower() in str(space).lower()]
    print node, spaceName, matching_space
    return matching_space[0]

def spaceMenu(_node, selection, cAttributes):
    #_spaces = _node.space.get()
    # print _spaces

    # we use this dict to store the space attribute and the object ( in case we have multiple names in use )
    obj_spaces_dict = {}
    for x in selection:
        for attr in cAttributes.spaceSwitchAttributes:
            if cmds.attributeQuery(attr, node=x, exists=True):
                obj_spaces_dict[x] = attr
    print '!! shared spaces !!'

    _space_list = space_list_intersection(obj_spaces_dict)
    _list_length = len(_space_list)

    mod = get_modifier()
    pm.menuItem(divider=True)
    pm.menuItem(label=mod, enablepic=False)

    for space in _space_list:
        pm.menuItem(label='   %s' % space, boldFont=True, command=pm.Callback(temp_space, obj_spaces_dict, space))

def get_modifier():
    mod = {0: None, 1: 'shift', 4: 'ctrl'}[cmds.getModifiers()]
    return mod

def temp_space(obj_spaces_dict, space):
    print obj_spaces_dict.items()
    print 'swap to %s'  % space