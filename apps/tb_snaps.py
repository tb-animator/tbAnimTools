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
from . import *
maya.utils.loadStringResourcesForModule(__name__)


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('snap'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='store_ctrl_transform', annotation='store object transform',
                                     help=maya.stringTable['tbCommand.store_ctrl_transform'],
                                     category=self.category, command=[
                'SnapTools.store_transform()']))
        self.addCommand(self.tb_hkey(name='restore_ctrl_transform', annotation='restore object transform',
                                     help=maya.stringTable['tbCommand.restore_ctrl_transform'],
                                     category=self.category, command=[
                'SnapTools.restore_transform()']))
        self.addCommand(self.tb_hkey(name='store_relative_transform', annotation='store relative transform',
                                     help=maya.stringTable['tbCommand.store_relative_transform'],
                                     category=self.category, command=[
                'SnapTools.store_relative_transform()']))
        self.addCommand(self.tb_hkey(name='restore_relative_transform', annotation='restore relative transform',
                                     help=maya.stringTable['tbCommand.restore_relative_transform'],
                                     category=self.category, command=[
                'SnapTools.restore_relative_transform_for_target()']))
        self.addCommand(
            self.tb_hkey(name='restore_relative_transform_last_used', annotation='restore relative transform',
                         help=maya.stringTable['tbCommand.restore_relative_transform_last_used'],
                         category=self.category, command=[
                    'SnapTools.restore_relative_transform_for_last_used_target()']))
        self.addCommand(self.tb_hkey(name='snap_objects', annotation='snap selection',
                                     help=maya.stringTable['tbCommand.snap_objects'],
                                     category=self.category, command=[
                'SnapTools.snap_selection()']))
        self.addCommand(self.tb_hkey(name='point_snap_objects', annotation='point snap selection',
                                     help=maya.stringTable['tbCommand.point_snap_objects'],
                                     category=self.category, command=[
                'SnapTools.point_snap_selection()']))
        self.addCommand(self.tb_hkey(name='orient_snap_objects', annotation='orient snap selection',
                                     help=maya.stringTable['tbCommand.orient_snap_objects'],
                                     category=self.category, command=[
                'SnapTools.orient_snap_selection()']))

        return self.commandList

    def assignHotkeys(self):
        return


class SnapTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'SnapTools'
    hotkeyClass = None
    funcs = None

    transformTranslateDict = dict()
    transformClipboard = dict()
    relativeTransformClipboard = dict()
    relativeTransformLastParent = str()
    relativeTransformLastControls = list()
    transformRotateDict = dict()
    transformMatrixDict = dict()

    selectionOrderOption = 'tbSnapSelectionOrder'
    relativeSelectionOrderOption = 'tbRelativeSnapSelectionOrder'
    relativeSelectionConstraintOption = 'tbRelativeSnapConstraintMethod'
    relativeSelectionChannelFilterOption = 'tbRelativeChannelFilter'

    def __new__(cls):
        if SnapTools.__instance is None:
            SnapTools.__instance = object.__new__(cls)

        SnapTools.__instance.val = cls.toolName
        return SnapTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    def loadData(self):
        super(SnapTools, self).loadData()
        self.transformClipboard = self.rawJsonData.get('transformClipboard', dict())
        self.relativeTransformClipboard = self.rawJsonData.get('relativeTransformClipboard', dict())
        self.transformTranslateDict = self.rawJsonData.get('transformTranslateDict', dict())
        self.transformRotateDict = self.rawJsonData.get('transformRotateDict', dict())
        self.transformMatrixDict = self.rawJsonData.get('transformMatrixDict', dict())

        self.relativeTransformLastParent = self.rawJsonData.get('relativeTransformLastParent', str())
        self.relativeTransformLastControls = self.rawJsonData.get('relativeTransformLastControls', list())

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['relativeTransformClipboard'] = dict()
        self.classData['transformTranslateDict'] = dict()
        self.classData['transformRotateDict'] = dict()
        self.classData['transformMatrixDict'] = dict()
        self.classData['relativeTransformLastParent'] = self.relativeTransformLastParent
        self.classData['relativeTransformLastControls'] = self.relativeTransformLastControls

        for key, value in self.transformClipboard.items():
            value = [value(i, j) for i in range(4) for j in range(4)]
            self.classData['transformClipboard'][key] = value

        for key, value in self.transformTranslateDict.items():
            # value = [value(i, j) for i in range(4) for j in range(4)]
            self.classData['transformTranslateDict'][key] = value

        for key, value in self.transformRotateDict.items():
            # value = [value(i, j) for i in range(4) for j in range(4)]
            self.classData['transformRotateDict'][key] = value

        for key, value in self.transformMatrixDict.items():
            # value = [value(i, j) for i in range(4) for j in range(4)]
            self.classData['transformMatrixDict'][key] = value

        for key, value in self.relativeTransformClipboard.items():
            self.classData['relativeTransformClipboard'][key] = dict()
            for subKey, v in value.items():
                self.classData['relativeTransformClipboard'][key][subKey] = [x for x in v]

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(SnapTools, self).optionUI()

        snapOrderHeader = subHeader('Snap Order')
        selectionOrderInfo = infoLabel([maya.stringTable['SnapTools.selectionOrderInfo']])

        selectionOrderOptionWidget = optionVarBoolWidget(maya.stringTable['SnapTools.selectionOrderOption'],
                                                         self.selectionOrderOption)
        relativeSnapOrderHeader = subHeader(maya.stringTable['SnapTools.relativeSnapOrderHeader'])
        relativeOrderInfo = infoLabel([maya.stringTable['SnapTools.relativeOrderInfo']])
        relativeOrderOptionWidget = optionVarBoolWidget(maya.stringTable['SnapTools.relativeOrderOptionWidget'],
                                                        self.relativeSelectionOrderOption)
        relativeSelectionConstraintOptionWidget = optionVarBoolWidget(
            maya.stringTable['SnapTools.relativeSelectionConstraintOptionWidget'],
            self.relativeSelectionConstraintOption)
        relativeSelectionChannelOptionWidget = optionVarBoolWidget(
            maya.stringTable['SnapTools.relativeSelectionChannelOptionWidget'],
            self.relativeSelectionChannelFilterOption)
        self.layout.addWidget(snapOrderHeader)
        self.layout.addWidget(selectionOrderInfo)
        self.layout.addWidget(selectionOrderOptionWidget)
        self.layout.addWidget(relativeSnapOrderHeader)
        self.layout.addWidget(relativeOrderInfo)
        self.layout.addWidget(relativeOrderOptionWidget)
        self.layout.addWidget(relativeSelectionConstraintOptionWidget)
        self.layout.addWidget(relativeSelectionChannelOptionWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    @staticmethod
    def minus(vector1, vector2):
        # TODO use actual vectors
        return [vector1[0] - vector2[0], vector1[1] - vector2[1], vector1[2] - vector2[2]]

    @staticmethod
    def plus(vector1, vector2):
        # TODO use actual vectors
        return [vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2]]

    def snap_selection(self, translate=True, orient=True):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        if len(sel) >= 2:
            state = get_option_var(self.selectionOrderOption, False)
            original = {True: sel[1], False: sel[0]}[state]
            target = {True: sel[0], False: sel[1]}[state]

        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            for x in range(int(startTime), int(endTime)):
                cmds.currentTime(x)
                self.snap_object(original, target, translate, orient)
        else:
            self.snap_object(original, target, translate, orient)

    def point_snap_selection(self):
        self.snap_selection(translate=True, orient=False)

    def orient_snap_selection(self):
        self.snap_selection(translate=False, orient=True)

    def snap_object(self, original, target, translate, orient):
        original_rotation = self.get_world_rotation(original)
        original_pivot_position = self.get_world_pivot(original)
        original_world_position = self.get_world_space(original)

        target_rotation = self.get_world_rotation(target)
        target_pivot_position = self.get_world_pivot(target)
        target_world_position = self.get_world_space(target)

        _pivot_difference = self.minus(target_pivot_position, original_pivot_position)
        _out_position = self.plus(original_world_position, _pivot_difference)

        if translate:
            self.set_world_translation(original, _out_position)

        if orient:
            self.set_world_rotation(original, target_rotation)
            rot = cmds.xform(target, query=True, absolute=True, worldSpace=True, rotation=True)
            node_ro = cmds.xform(original, query=True, rotateOrder=True)
            ro = cmds.xform(target, query=True, rotateOrder=True)
            cmds.xform(original, absolute=True, worldSpace=True, rotation=rot, rotateOrder=ro, preserve=True)
            cmds.xform(original, rotateOrder=node_ro, preserve=True)

    def init_relative_transform_key(self, key):
        self.relativeTransformClipboard[key] = self.relativeTransformClipboard.get(key, dict())

    def store_relative_transform(self):
        sel = cmds.ls(selection=True)
        if len(sel) < 2:
            return

        state = get_option_var(self.relativeSelectionOrderOption, False)
        parent = {True: sel[0], False: sel[-1]}[state]
        targets = {True: sel[1:], False: sel[:-1]}[state]

        self.init_relative_transform_key(parent)

        parentMatrix = om2.MMatrix(self.get_world_matrix(parent))
        for target in targets:
            targetMatrix = om2.MMatrix(self.get_world_matrix(target))
            self.relativeTransformClipboard[parent][target] = targetMatrix * parentMatrix.inverse()

        self.relativeTransformLastParent = parent
        self.relativeTransformLastControls = targets

        self.saveData()

    def restore_relative_transform_for_target(self):
        sel = cmds.ls(selection=True)
        # TODO - make it restore on single selection using last used reference
        if len(sel) < 2:
            return

        state = get_option_var(self.relativeSelectionOrderOption, False)
        parent = {True: sel[0], False: sel[-1]}[state]
        targets = {True: sel[1:], False: sel[:-1]}[state]
        with self.funcs.keepSelection():
            self.restore_relative_transform(parent, targets)

    def restore_relative_transform_for_last_used_target(self):
        sel = cmds.ls(selection=True)
        # TODO - make it restore on single selection using last used reference
        if len(sel) == 1:
            if str(sel[0]) == self.relativeTransformLastParent:
                sel = self.relativeTransformLastControls
        if not sel:
            sel = self.relativeTransformLastControls
        if not sel:
            return  # TODO - make this use all the last stored controls
        self.loadData()
        parent = self.relativeTransformLastParent
        with self.funcs.keepSelection():
            self.restore_relative_transform(parent, sel)

    def restore_relative_transform(self, parent, targets):
        self.loadData()
        channels = self.funcs.getChannels()
        #print ('channels', channels)
        self.init_relative_transform_key(parent)

        startTime = cmds.currentTime(query=True)
        endTime = cmds.currentTime(query=True)
        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()

        constrain = get_option_var(self.relativeSelectionConstraintOption, False)
        for x in range(int(startTime), int(endTime) + 1):
            if int(cmds.currentTime(query=True)) != x:
                cmds.currentTime(x)
            tempNodes = list()
            tempConstraints = list()
            parentMatrix = om2.MMatrix(self.get_world_matrix(parent))
            for target in targets:
                targetMatrix = self.relativeTransformClipboard[parent].get(target, None)
                if not targetMatrix:
                    continue
                targetMatrix = om2.MMatrix(targetMatrix)
                if constrain:
                    tempNode, tempConstraint = self.set_transform(target, targetMatrix * parentMatrix,
                                                                  channels=channels)
                    tempNodes.append(tempNode)
                    tempConstraints.append(tempConstraint)
                else:
                    self.set_world_matrix(target, targetMatrix * parentMatrix, channels=channels)
            if constrain:
                cmds.setKeyframe(targets)
                cmds.delete(tempNodes)

    def store_transform(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        pos = list()
        rot = list()
        mtx = list()
        for s in sel:
            pos = self.get_world_space(s)
            rot = self.get_world_rotation(s)
            mtx = self.funcs.getMatrix(s)
            self.transformTranslateDict[s] = [x for x in pos]
            self.transformRotateDict[s] = [x for x in rot]
            self.transformMatrixDict[s] = [x for x in mtx]

        self.transformTranslateDict['LASTUSED'] = [x for x in pos]
        self.transformRotateDict['LASTUSED'] = [x for x in rot]
        self.transformMatrixDict['LASTUSED'] = [x for x in mtx]

        self.saveData()

    def restore_transform(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return
        self.loadData()
        if self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
            for x in range(int(startTime), int(endTime)):
                cmds.currentTime(x)
                self.restoreTansformToSelection(sel)
        else:
            self.restoreTansformToSelection(sel)

    def restoreTansformToSelection(self, sel):
        if len(sel) == 1:
            pos = self.transformTranslateDict.get('LASTUSED', None)
            rot = self.transformRotateDict.get('LASTUSED', None)
            storedMtx = om2.MMatrix(self.transformMatrixDict.get('LASTUSED', None))
            postMtx = om2.MMatrix(self.funcs.getMatrix(sel[0]))
            parentMtx = om2.MMatrix(self.funcs.getMatrix(sel[0], matrix='parentMatrix'))

            # if joint orient is being used, just set the values directly for now
            if cmds.attributeQuery('jointOrient', node=sel[0], exists=True):
                jointOrient = cmds.getAttr(sel[0] + '.jointOrient')[0]
            else:
                jointOrient = [0]

            if any(jointOrient) != 0:
                cmds.xform(sel[0], relative=False, worldSpace=True, translation=pos)
                cmds.xform(sel[0], relative=False, worldSpace=True, rotation=rot)
            else:
                pos, rot = self.funcs.getMatrixOffset(sel[0], storedMtx, postMtx, parentMtx)
                if rot:
                    #self.set_world_rotation(sel[0], rot)
                    cmds.xform(sel[0], relative=True, rotation=rot)
                postMtx = self.funcs.getMatrix(sel[0])
                parentMtx = self.funcs.getMatrix(sel[0], matrix='parentMatrix')
                pos, rot = self.funcs.getMatrixOffset(sel[0], storedMtx, postMtx, parentMtx)

                if pos:
                    #self.set_world_translation(sel[0], pos)
                    cmds.xform(sel[0], relative=True, translation=pos)
            return
        for s in sel:
            pos = self.transformTranslateDict.get(s, self.transformTranslateDict.get('LASTUSED', None))
            rot = self.transformRotateDict.get(s, self.transformRotateDict.get('LASTUSED', None))
            if cmds.attributeQuery('jointOrient', node=s, exists=True):
                jointOrient = cmds.getAttr(s + '.jointOrient')[0]
            else:
                jointOrient = [0]
            if any(jointOrient) != 0:
                cmds.xform(s, relative=False, rotation=rot, absolute=True, worldSpace=True)
                cmds.xform(s, relative=False, translation=pos, absolute=True, worldSpace=True)
                continue
            else:
                storedMtx = om2.MMatrix(self.transformMatrixDict.get(s, self.transformMatrixDict.get('LASTUSED', None)))
                if rot:
                    #self.set_world_rotation(s, rot)
                    postMtx = self.funcs.getMatrix(s)
                    parentMtx = self.funcs.getMatrix(s, matrix='parentMatrix')
                    pos, rot = self.funcs.getMatrixOffset(s, storedMtx, postMtx, parentMtx)
                    cmds.xform(s, relative=True, rotation=rot)

                if pos:
                    #self.set_world_translation(s, pos)
                    postMtx = self.funcs.getMatrix(s)
                    parentMtx = self.funcs.getMatrix(s, matrix='parentMatrix')
                    pos, rot = self.funcs.getMatrixOffset(s, storedMtx, postMtx, parentMtx)
                    cmds.xform(s, relative=True, translation=pos)


    def get_world_pivot(self, node):
        # get the world pivot
        return cmds.xform(node, query=True, worldSpace=True, rotatePivot=True)

    def get_world_space(self, node):
        # gets the world space, not really world space tho, just what maya thinks is world space
        return cmds.xform(node, query=True, relative=True, worldSpace=True, translation=True)

    def set_world_translation(self, node, position):
        # set the world space position on the object
        cmds.xform(node, absolute=True, worldSpace=True, translation=position)

    def get_world_rotation(self, node):
        # get the absolute world rotation of the object
        return cmds.xform(node, query=True, absolute=True, worldSpace=True, rotation=True)

    def set_world_rotation(self, node, rotation):
        # set the absolute world rotation
        cmds.xform(node, absolute=True, worldSpace=True, rotation=rotation)

    def get_world_matrix(self, node):
        #
        return cmds.xform(node, query=True, absolute=True, worldSpace=True, matrix=True)

    def set_world_matrix(self, node, matrix, channels=list()):
        #
        cmds.xform(node, absolute=True, worldSpace=True, matrix=matrix)
        '''
        print ('currentMatrix', currentMatrix)
        print ('matrix', matrix)
        offset = matrix * om2.MMatrix(currentMatrix).inverse()
        print ('offset', offset)
        transform_fn = om2.MTransformationMatrix(offset)
        print ('transform_fn', transform_fn)
        translation = transform_fn.translation(om.MSpace.kObject)
        rotation = transform_fn.rotation(asQuaternion=False)
        print (translation)
        print (rotation)
        outRotation = [0.0, 0.0, 0.0]
        outTranslation = [0.0, 0.0, 0.0]
        if 'rx' in channels: outRotation[0] = rotation[0]
        if 'ry' in channels: outRotation[1] = rotation[1]
        if 'rz' in channels: outRotation[2] = rotation[2]

        if 'tx' in channels: outTranslation[0] = rotation[0]
        if 'ty' in channels: outTranslation[1] = rotation[1]
        if 'tz' in channels: outTranslation[2] = rotation[2]
        print (outTranslation)
        print (outRotation)
        '''

    def set_transform(self, node, matrix, channels=list()):
        """
        use a temp node and a constraint
        :param node:
        :param matrix:
        :return:
        """
        n = cmds.createNode('transform')
        self.set_world_matrix(n, matrix)
        if not get_option_var(self.relativeSelectionChannelFilterOption, False):
            channels = list()
        constraint = self.funcs.safeParentConstraint(n, node, channels=channels)
        return n, constraint
