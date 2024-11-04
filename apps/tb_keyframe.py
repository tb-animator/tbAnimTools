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
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='match_tangent_start_to_end', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.matchStartTangentsToEndTangents()']))
        self.addCommand(self.tb_hkey(name='match_tangent_end_to_start', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.matchEndTangentsToStartTangents()']))
        self.addCommand(self.tb_hkey(name='shift_selected_keys_to_start_at_current_time', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.shiftKeySelection()']))
        self.addCommand(self.tb_hkey(name='shift_selected_keys_to_end_at_current_time', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.shiftKeySelection(start=False)']))

        self.addCommand(self.tb_hkey(name='flip_selected_key_values', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.flipKeyValues()']))
        self.addCommand(self.tb_hkey(name='flip_selected_key_values_start', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.flipKeyValues(first=True)']))
        self.addCommand(self.tb_hkey(name='flip_selected_key_values_end', annotation='',
                                     category=self.category,
                                     command=['KeyModifiers.flipKeyValues(last=True)']))

        self.addCommand(self.tb_hkey(name='filter_channelBox',
                                     annotation='filters the current channelBox selection in the graph editor',
                                     category=self.category, command=['KeyModifiers.filterChannels()']))

        self.addCommand(self.tb_hkey(name='setTangentsLinear',
                                     annotation='Sets your current key selection or timeline key to linear',
                                     category=self.category, command=['KeyModifiers.setTangentsLinear()']))
        self.addCommand(self.tb_hkey(name='setTangentsStepped',
                                     annotation='Sets your current key selection or timeline key to linear',
                                     category=self.category, command=['KeyModifiers.setTangentsStepped()']))
        self.addCommand(self.tb_hkey(name='setTangentsAuto',
                                     annotation='Sets your current key selection or timeline key to auto',
                                     category=self.category, command=['KeyModifiers.setTangentsAuto()']))
        self.addCommand(self.tb_hkey(name='setTangentsSpline',
                                     annotation='Sets your current key selection or timeline key to spline',
                                     category=self.category, command=['KeyModifiers.setTangentsSpline()']))
        self.addCommand(self.tb_hkey(name='setTangentsFlat',
                                     annotation='Sets your current key selection or timeline key to flat',
                                     category=self.category, command=['KeyModifiers.setTangentsFlat()']))
        self.addCommand(self.tb_hkey(name='setTangentsEase',
                                     annotation='Sets your current key selection or timeline key to Ease',
                                     category=self.category, command=['KeyModifiers.setTangentsEase()']))
        self.addCommand(self.tb_hkey(name='flattenControl',
                                     annotation='Flatten a controls rotation so the y axis points straight up',
                                     category=self.category, command=['KeyModifiers.level()']))
        self.addCommand(self.tb_hkey(name='eulerFilterSelection',
                                     annotation='euler filter your current keyframe selection',
                                     category=self.category, command=['KeyModifiers.eulerFilterSelectedKeys()']))
        self.addCommand(self.tb_hkey(name='quickCopyKeys',
                                     annotation='copy selected keys to the current frame',
                                     category=self.category, command=['KeyModifiers.quickCopyKeys()']))
        self.addCommand(self.tb_hkey(name='quickCopyKeysConnect',
                                     annotation='copy-connect selected keys to the current frame',
                                     category=self.category, command=['KeyModifiers.quickCopyKeys(connect=True)']))
        self.addCommand(self.tb_hkey(name='clampKeysBelow',
                                     annotation=maya.stringTable['tbCommand.clampKeysBelow'],
                                     category=self.category, command=['KeyModifiers.clampCurve(low=True)']))
        self.addCommand(self.tb_hkey(name='clampKeysAbove',
                                     annotation=maya.stringTable['tbCommand.clampKeysAbove'],
                                     category=self.category, command=['KeyModifiers.clampCurve(low=False)']))
        self.addCommand(self.tb_hkey(name='shiftUp180',
                                     annotation='shift keys up 180 units',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.shiftKeys(180)']))
        self.addCommand(self.tb_hkey(name='shiftUp360',
                                     annotation='shift keys up 360 units',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.shiftKeys(360)']))
        self.addCommand(self.tb_hkey(name='shiftDown180',
                                     annotation='shift keys up 180 units',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.shiftKeys(-180)']))
        self.addCommand(self.tb_hkey(name='shiftDown360',
                                     annotation='shift keys up 360 units',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.shiftKeys(-360)']))

        self.addCommand(self.tb_hkey(name='nudgeKeysLeft',
                                     annotation='shift keys left 1 frame',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.nudgeKeys(offset=-1)']))
        self.addCommand(self.tb_hkey(name='nudgeKeysRight',
                                     annotation='shift keys up 360 units',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.nudgeKeys(offset=1)']))
        self.addCommand(self.tb_hkey(name='offsetKeysLeft',
                                     annotation='offset keys left 1 frame',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.offsetKeys(offset=-0.25)']))
        self.addCommand(self.tb_hkey(name='offsetKeysRight',
                                     annotation='offset keys right 1 frame',
                                     ctx='graphEditor',
                                     category=self.category, command=['KeyModifiers.offsetKeys(offset=1)']))

        self.addCommand(self.tb_hkey(name='autoTangent',
                                     annotation='Blank',
                                     category=self.category, command=['KeyModifiers.autoTangentKey()']))
        self.addCommand(self.tb_hkey(name='guessKeyValue',
                                     annotation='Blank',
                                     category=self.category, command=['KeyModifiers.plot_guess()']))
        self.addCommand(self.tb_hkey(name='selectAllAnimCurves',
                                     annotation='Blank',
                                     category=self.category, command=['KeyModifiers.select_all_curves()']))
        self.addCommand(self.tb_hkey(name='deleteAllUnconnectedAnimCurves',
                                     annotation='Blank',
                                     category=self.category, command=['KeyModifiers.delete_unconnected_curves()']))
        self.addCommand(self.tb_hkey(name='cleanupTimeEditorNodes',
                                     annotation='Blank',
                                     category=self.category, command=['KeyModifiers.cleanupTimeEditorNodes()']))

        self.addCommand(self.tb_hkey(name='setZeroKey',
                                     annotation='Sets the identity pose (zero key) for selected layer',
                                     category=self.category, command=['KeyModifiers.setZeroKey()']))

        return self.commandList

    def assignHotkeys(self):
        return


class KeyModifiers(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'KeyModifiers'
    hotkeyClass = hotkeys()
    funcs = Functions()

    def __new__(cls):
        if KeyModifiers.__instance is None:
            KeyModifiers.__instance = object.__new__(cls)

        KeyModifiers.__instance.val = cls.toolName
        return KeyModifiers.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    def initData(self):
        super(KeyModifiers, self).initData()
        self.baseDataFile = os.path.join(self.dataPath, self.toolName + 'BaseData.json')

    def loadData(self):
        super(KeyModifiers, self).loadData()
        self.rawJsonBaseData = json.load(open(self.baseDataFile))

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(KeyModifiers, self).optionUI()
        return self.optionWidget

    def graphEditorWidget(self, parentWidget):
        self.loadData()
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)

        autoTangentCollapsingWidget = CollapsibleBox(optionVar='tbGeAutotangentCollapse', toolTip='AutoTangent')
        autoTangentWidget = AutoTangentWidgetLayout()
        autoTangentCollapsingWidget.setContentLayout(autoTangentWidget)

        nudgeKeyCollapsingWidget = CollapsibleBox(optionVar='tbGeNudgeCollapse', toolTip='Nudge Keys')
        nudgeKeyWidget = NudgeKeyWidgetLayout()
        nudgeKeyCollapsingWidget.setContentLayout(nudgeKeyWidget)

        offsetKeyCollapsingWidget = CollapsibleBox(optionVar='tbGeOffsetCollapse', toolTip='Offset Keys')
        offsetKeyWidget = OffsetKeyWidgetLayout()
        offsetKeyCollapsingWidget.setContentLayout(offsetKeyWidget)

        flipKeyCollapsingWidget = CollapsibleBox(optionVar='tbGeFlipkeyCollapse', toolTip='Flip Keys')
        flipKeyWidget = FlipKeyWidgetLayout()
        flipKeyCollapsingWidget.setContentLayout(flipKeyWidget)

        matchTangentCollapsingWidget = CollapsibleBox(optionVar='tbGeMatchTangentCollapse', toolTip='Match Tangents')
        matchTangentWidget = MatchTangentWidgetLayout()
        matchTangentCollapsingWidget.setContentLayout(matchTangentWidget)

        layout.addWidget(autoTangentCollapsingWidget)
        layout.addWidget(matchTangentCollapsingWidget)
        layout.addWidget(flipKeyCollapsingWidget)
        layout.addWidget(nudgeKeyCollapsingWidget)
        layout.addWidget(offsetKeyCollapsingWidget)

        collapsedWidgets = [
            matchTangentCollapsingWidget,
            flipKeyCollapsingWidget,
            autoTangentCollapsingWidget,
            nudgeKeyCollapsingWidget,
            offsetKeyCollapsingWidget,
        ]
        for cBox in collapsedWidgets:
            cBox.show()
            cBox.playAnimationByState(force=True, state=cBox.getState())

        return widget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def filterChannels(self):
        self.funcs.filterChannels()

    def matchStartTangentsToEndTangents(self):
        self.matchTangents(True)

    def matchEndTangentsToStartTangents(self):
        self.matchTangents(False)

    def setZeroKey(self):
        """
        Zero keys the selection
        :return:
        """
        cmds.setKeyframe(id=True)

    def select_all_curves(self):
        cmds.select(self.funcs.get_non_referenced_animation_curves())

    def delete_unconnected_curves(self):
        cmds.delete(self.funcs.get_unconnected_animation_curves())

    def cleanupTimeEditorNodes(self):
        cmds.delete(cmds.ls(type='timeEditorAnimSource'))
        self.delete_unconnected_curves()

    def matchTangents(self, data):
        keyTimeIndex = {True: -1, False: 0}[data]
        range = self.funcs.getTimelineRange()
        referenceTime = range[data]
        editTime = range[not data]
        animcurves = cmds.keyframe(query=True, name=True)
        if not animcurves:
            return cmds.warning('no anim curves found to match tangents with')

        for curve in animcurves:
            inTangent = None
            outTangent = None
            keyTimes = cmds.keyframe(curve, query=True, selected=False, timeChange=True)
            if not len(keyTimes) > 1:
                continue
            if editTime not in keyTimes:
                editTime = keyTimes[{True: -1, False: 0}[not data]]
            if referenceTime not in keyTimes:
                inTangent, outTangent = cmds.keyTangent(curve, query=True, time=((keyTimes[keyTimeIndex]),),
                                                        outAngle=True, inAngle=True)
            else:
                inTangent, outTangent = cmds.keyTangent(curve, query=True, time=((referenceTime),), outAngle=True,
                                                        inAngle=True)
            if data:
                cmds.keyTangent(curve,
                                edit=True,
                                lock=True,
                                time=((editTime),),
                                inAngle=inTangent,
                                outAngle=inTangent)
            else:
                cmds.keyTangent(curve,
                                edit=True,
                                lock=True,
                                time=((editTime),),
                                inAngle=outTangent,
                                outAngle=outTangent)

    def setTangentsLinear(self):
        self.setTangentType('linear')

    def setTangentsStepped(self):
        self.setTangentType('step')

    def setTangentsSpline(self):
        self.setTangentType('spline')

    def setTangentsAuto(self):
        self.setTangentType('auto')

    def setTangentsFlat(self):
        self.setTangentType('flat')

    def setTangentsEase(self):
        self.setTangentType('autoease')

    def setTangentType(self, input):
        graphEditorState = self.funcs.getGraphEditorState()
        timeSlider = self.funcs.getPlayBackSlider()

        minTime, maxTime = self.funcs.getTimelineHighlightedRange()
        currentKeys = cmds.keyframe(query=True, selected=True)

        if currentKeys and graphEditorState:
            cmds.keyTangent(itt=input, ott=input)
        else:
            sel = cmds.ls(sl=True)
            channels = mel.eval('selectedChannelBoxPlugs')
            if channels:
                attributes = [at.split('.')[-1] for at in channels]
            else:
                attributes = self.funcs.getValidAttributes(sel)
            if self.funcs.isTimelineHighlighted():
                minTime, maxTime = self.funcs.getTimelineHighlightedRange()
                timeRange = (minTime, (maxTime))
            else:
                timeRange = (cmds.currentTime(query=True),)
            cmds.keyTangent(sel,
                            attribute=attributes,
                            edit=True,
                            inTangentType=input,
                            outTangentType=input,
                            time=timeRange)
            self.funcs.infoMessage(prefix="Tangent :: ", message=input)

    def shiftKeys(self, offset):
        cmds.keyframe(animation='keys', relative=True, valueChange=offset)

    def nudgeKeys(self, offset=0):
        cmds.keyframe(animation='keys', relative=True, timeChange=offset)

    def offsetKeys(self, offset=0):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for x in range(len(sel) - 1):
            cmds.keyframe(sel[x + 1:], relative=True, timeChange=offset)

    def quickCopyKeys(self, connect=False):
        cmds.copyKey()
        if connect:
            cmds.pasteKey(option='merge', time=(cmds.currentTime(query=True),), copies=1, connect=connect)
        else:
            cmds.pasteKey(option='merge', time=(cmds.currentTime(query=True),), copies=1)

    def eulerFilterSelectedKeys(self):
        self.objects = cmds.ls(selection=True)
        self.selected = False
        # get the min and max times from our keyframe selection
        if cmds.keyframe(query=True, selected=True):
            self.firstTime = min(min(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
            self.lastTime = min(max(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
            self.selected = True
        if self.selected:
            # copy keys to buffer
            cmds.selectKey(self.objects, replace=True, time=(self.firstTime, self.lastTime))
            cmds.bufferCurve(animation='keys', overwrite=True)
            # delete surrounding keys
            cmds.cutKey(self.objects, time=(-9999999, self.firstTime - 0.01))
            cmds.cutKey(self.objects, time=(self.lastTime + 0.01, 999999))
            # euler filter
            cmds.filterCurve()
            # copy keys
            cmds.copyKey(self.objects, time=(self.firstTime, self.lastTime))
            # swap buffer to original
            cmds.bufferCurve(animation='keys', swap=True)
            # paste keys back
            cmds.pasteKey(option='merge')
        else:
            cmds.filterCurve()

    @staticmethod
    def getMatrix(node, matrix="worldMatrix"):
        '''
        Gets the world matrix of an object based on name.
        '''
        # TODO - have this use a shared function from self.funcs
        # Selection list object and MObject for our matrix
        selection = om2.MSelectionList()
        matrixObject = om2.MObject()

        # Adding object
        selection.add(node)

        # New api is nice since it will just return an MObject instead of taking two arguments.
        MObjectA = selection.getDependNode(0)

        # Dependency node so we can get the worldMatrix attribute
        fnThisNode = om2.MFnDependencyNode(MObjectA)

        # Get it's world matrix plug
        worldMatrixAttr = fnThisNode.attribute(matrix)

        # Getting mPlug by plugging in our MObject and attribute
        matrixPlug = om2.MPlug(MObjectA, worldMatrixAttr)
        try:
            matrixPlug = matrixPlug.elementByLogicalIndex(0)
        except:
            pass

        # Get matrix plug as MObject so we can get it's data.
        matrixObject = matrixPlug.asMObject()

        # Finally get the data
        worldMatrixData = om2.MFnMatrixData(matrixObject)
        worldMatrix = worldMatrixData.matrix()

        return worldMatrix

    def shiftKeySelection(self, start=True):
        """
        Shift the current graph editor key selection so the first/last key aligns with the current time
        :param start:
        :return:
        """
        currentTime = cmds.currentTime(query=True)
        timeDelta = 1
        selectedKeyTimes = cmds.keyframe(query=True, selected=True, timeChange=True)
        if not selectedKeyTimes:
            return False
        keyTimes = sorted(list(set(selectedKeyTimes)))
        keyTimes = [keyTimes[0], keyTimes[-1]]
        cmds.keyframe(animation='keys', option='over', relative=True, timeChange=currentTime - keyTimes[not start])

    def flipKeyValues(self, first=False, last=False, *args):
        """
        Flip the key values around either the first value, last value or 0
        :return:
        """
        selectedCurves = cmds.keyframe(query=True, selected=True, name=True)
        if not selectedCurves:
            return
        for curve in selectedCurves:
            selectedKeyTimes = cmds.keyframe(curve, query=True, selected=True, timeChange=True)
            selectedKeyValues = cmds.keyframe(curve, query=True, selected=True, valueChange=True)
            # print (curve, selectedKeyTimes)
            pivotValue = 0
            if first:
                pivotValue = selectedKeyValues[0]
            elif last:
                pivotValue = selectedKeyValues[-1]
            for index, key in enumerate(selectedKeyTimes):
                cmds.scaleKey(curve, time=(key,), valueScale=-1, valuePivot=pivotValue)

    def level(self):
        sel = cmds.ls(selection=True)
        if sel:
            for se in sel:
                upAxis = cmds.upAxis(query=True, axis=True)
                worldAxis = {'y': [1, 0, 1],
                             'z': [1, 1, 0]}
                self.do_level(se, upAxis=upAxis, worldAxis=worldAxis[upAxis])

    def do_level(self, node, upAxis='y', worldAxis=[1.0, 0.0, 1.0]):
        def multiply(input1, input2):
            mult = om2.MVector([input1[0] * input2[0], input1[1] * input2[1], input1[2] * input2[2]])
            _out = mult
            return _out

        def constructMatrix(_matrix, x_vector, y_vector, z_vector):
            _matrix[0] = x_vector[0]
            _matrix[1] = x_vector[1]
            _matrix[2] = x_vector[2]
            _matrix[4] = y_vector[0]
            _matrix[5] = y_vector[1]
            _matrix[6] = y_vector[2]
            _matrix[8] = z_vector[0]
            _matrix[9] = z_vector[1]
            _matrix[10] = z_vector[2]

            return _matrix

        _matrix = self.getMatrix(node)
        _original_matrix = om2.MTransformationMatrix(_matrix)
        # cache the rotate pivots

        _rp = cmds.xform(node, query=True, rotatePivot=True)
        _lsp = cmds.xform(node, query=True, scalePivot=True)

        rotOrder = cmds.getAttr('%s.rotateOrder' % node)
        _flat = om2.MVector(worldAxis)
        x_vector = om2.MVector([_matrix[0], _matrix[1], _matrix[2]])
        y_vector = om2.MVector([_matrix[4], _matrix[5], _matrix[6]])
        z_vector = om2.MVector([_matrix[8], _matrix[9], _matrix[10]])

        _flatX = multiply(x_vector, _flat)
        _flatY = multiply(y_vector, _flat)
        _flatZ = multiply(z_vector, _flat)

        if upAxis == 'x':
            _crossX = _flatY.cross(_flatZ)
            _crossZ = _crossX.cross(_flatY)
            _crossY = _crossZ.cross(_crossX)

        elif upAxis == 'y':
            _crossY = _flatZ.cross(_flatX)
            _crossX = _crossY.cross(_flatZ)
            _crossZ = _crossX.cross(_crossY)

        elif upAxis == 'z':
            _crossZ = _flatY.cross(_flatX)
            _crossX = _crossZ.cross(_flatY)
            _crossY = _crossX.cross(_crossZ)

        _matrix = constructMatrix(_matrix, _crossX, _crossY, _crossZ)
        mTransformMtx = om2.MTransformationMatrix(_matrix)
        eulerRot = mTransformMtx.rotation()
        eulerRot.reorderIt(rotOrder)
        angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
        cmds.setAttr(node + '.rotate', *angles)

    def clampCurve(self, low=True):
        currentTime = cmds.currentTime(query=True)
        graphEditorCurves = self.funcs.get_graph_editor_curves()
        selectedCurves = self.funcs.get_selected_curves()
        insertTimes = dict()
        inFlatTimes = dict()
        outFlatTimes = dict()
        clippedTimes = dict()

        if not selectedCurves:
            selectedCurves = graphEditorCurves
        print('graphEditorCurves', graphEditorCurves)
        if not selectedCurves:
            return cmds.warning('No curves selected')

        for curve in selectedCurves:
            insertTimes[curve] = list()
            inFlatTimes[curve] = list()
            outFlatTimes[curve] = list()
            clippedTimes[curve] = list()

            currentVal = cmds.keyframe(curve, query=True, eval=True, time=(currentTime,))
            keyRange = cmds.keyframe(curve, query=True, timeChange=True)

            for idx in range(int(keyRange[-1] - keyRange[0]) + 1):
                t = idx + int(keyRange[0])
                prevVal = cmds.keyframe(curve, query=True, eval=True, time=(t - 1,))
                val = cmds.keyframe(curve, query=True, eval=True, time=(t,))
                nextVal = cmds.keyframe(curve, query=True, eval=True, time=(t + 1,))

                if low:
                    if prevVal < currentVal and nextVal >= currentVal:
                        insertTimes[curve].append(t)
                        outFlatTimes[curve].append(t)

                    if nextVal < currentVal and prevVal >= currentVal:
                        insertTimes[curve].append(t)
                        inFlatTimes[curve].append(t)
                else:
                    if prevVal > currentVal and nextVal <= currentVal:
                        insertTimes[curve].append(t)
                        outFlatTimes[curve].append(t)

                    if nextVal > currentVal and prevVal <= currentVal:
                        insertTimes[curve].append(t)
                        inFlatTimes[curve].append(t)

            for t in insertTimes[curve]:
                cmds.setKeyframe(curve, time=(t,), insert=True)

            keyRange = cmds.keyframe(curve, query=True, timeChange=True)
            keyValues = cmds.keyframe(curve, query=True, valueChange=True)

            for i, v in zip(keyRange, keyValues):
                if low:
                    if v > currentVal[0]:
                        clippedTimes[curve].append(i)
                else:
                    if v < currentVal[0]:
                        clippedTimes[curve].append(i)
            for t in clippedTimes[curve]:
                cmds.setKeyframe(curve, time=(t,), value=currentVal[0])
                cmds.keyTangent(curve,
                                edit=True,
                                inTangentType='flat',
                                outTangentType='flat',
                                time=(t,))
            for t in inFlatTimes[curve]:
                cmds.setKeyframe(curve, time=(t,), inTangentType='flat')
                cmds.keyTangent(curve,
                                edit=True,
                                inTangentType='flat',
                                time=(t,))
            for t in outFlatTimes[curve]:
                cmds.setKeyframe(curve, time=(t,), outTangentType='flat')
                cmds.keyTangent(curve,
                                edit=True,
                                outTangentType='flat',
                                time=(t,))

    def autoTangentKey(self, softness=None, *args):
        print('autoTangentKey', softness, args)
        self.autoTangent(softness or self.defaultSoftness(), False)

    def defaultSoftness(self):
        return get_option_var('tbAutoTangent', 0.7)

    def setDefaultSoftness(self, value):
        print('setDefaultSoftness', value)
        set_option_var('tbAutoTangent', value)

    def defaultOffset(self):
        return get_option_var('tbKeyOffset', 1.0)

    def setDefaultOffset(self, value):
        set_option_var('tbKeyOffset', value)

    def defaultNudgeOffset(self):
        return get_option_var('tbKeyNudgeOffset', 1.0)

    def setDefaultNudgeOffset(self, value):
        set_option_var('tbKeyNudgeOffset', value)

    def autoTangent(self, softness, bFlatten):

        curves = cmds.keyframe(q=True, name=True, sl=True)  # get all selected animCurve Nodes
        if not curves:
            return
        for crv in curves:
            allKeyIndexes = cmds.keyframe(crv, q=True, indexValue=True, sl=True)
            keyCount = cmds.keyframe(crv, q=True, keyframeCount=True)
            for keyIndex in allKeyIndexes:
                currentValue = cmds.keyframe(crv, index=(keyIndex,), q=True, valueChange=True)[0]
                currentTime = cmds.keyframe(crv, index=(keyIndex,), q=True, timeChange=True)[0]

                previousTime = currentTime
                previousValue = currentValue
                nextTime = currentTime
                nextValue = currentValue

                if keyIndex > 0:
                    previousValue = cmds.keyframe(crv, index=((keyIndex - 1),), q=True, valueChange=True)[0]
                    previousTime = cmds.keyframe(crv, index=((keyIndex - 1),), q=True, timeChange=True)[0]

                if keyIndex < keyCount - 1:
                    nextValue = cmds.keyframe(crv, index=((keyIndex + 1),), q=True, valueChange=True)[0]
                    nextTime = cmds.keyframe(crv, index=((keyIndex + 1),), q=True, timeChange=True)[0]

                if keyIndex == 0 and not bFlatten:
                    previousTime = currentTime - (nextTime - currentTime)
                    previousValue = currentValue - (nextValue - currentValue)
                elif keyIndex == (keyCount - 1) and not bFlatten:
                    nextTime = currentTime + (currentTime - previousTime)
                    nextValue = currentValue + (currentValue - previousValue)

                # value change
                valueDeltaIn = currentValue - previousValue
                valueDeltaOut = nextValue - currentValue
                # time change
                timeDeltaIn = currentTime - previousTime
                timeDeltaOut = nextTime - currentTime

                slopeIn = 0
                slopeOut = 0

                if timeDeltaIn != 0:
                    slopeIn = valueDeltaIn / timeDeltaIn

                if timeDeltaOut != 0:
                    slopeOut = valueDeltaOut / timeDeltaOut

                powIn = 0.5

                if slopeIn + slopeOut != 0:
                    powIn = 1.0 - (abs(slopeIn) / (abs(slopeIn) + abs(slopeOut)))

                powOut = 1.0 - powIn

                powIn = ((1.0 - softness) * powIn) + (softness * 0.5)
                powOut = ((1.0 - softness) * powOut) + (softness * 0.5)

                newSlope = (powIn * slopeIn) + (powOut * slopeOut)
                ang = math.atan(newSlope) * 180.0 / 3.14159
                print('ang', ang)
                cmds.keyTangent(crv, itt='spline', ott='spline', time=(currentTime,))
                cmds.keyTangent(crv, ia=ang, oa=ang, time=(currentTime,))

                if cmds.keyTangent(crv, q=True, wt=True)[0]:
                    inWeight = abs(timeDeltaIn) / 3.0
                    outWeight = abs(timeDeltaOut) / 3.0
                    cmds.keyTangent(crv, iw=inWeight, ow=outWeight, time=currentTime)

    def predict_bezier_point(self, startTime, endTime, startValue, endValue, inAngle, outAngle, alpha):
        # Convert tangent angles to radians
        inAngle = inAngle * (3.141592653589793 / 180.0)
        outAngle = outAngle * (3.141592653589793 / 180.0)

        # Calculate control points based on the tangent angles and distance
        in_tangent_length = ((startTime - endTime) ** 2 + (startValue - endValue) ** 2) ** 0.5
        out_tangent_length = ((startTime - endTime) ** 2 + (startValue - endValue) ** 2) ** 0.5

        in_tangent = [startTime + in_tangent_length * math.cos(inAngle),
                      startValue + in_tangent_length * math.sin(inAngle)]
        out_tangent = [endTime - out_tangent_length * math.cos(outAngle),
                       endValue - out_tangent_length * math.sin(outAngle)]
        time = self.bezierPlot(alpha, endTime, in_tangent, out_tangent, startTime)
        value = self.bezierPlot(alpha, endValue, in_tangent, out_tangent, startValue)
        return time, value

    def bezierPlot(self, alpha, endTime, in_tangent, out_tangent, startTime):
        return (1 - alpha) ** 3 * startTime + 3 * (1 - alpha) ** 2 * alpha * in_tangent[0] + 3 * (
                1 - alpha) * alpha ** 2 * \
            out_tangent[0] + alpha ** 3 * endTime

    def cubic_bezier(self, start, end, in_tangent_angle, out_tangent_angle, num_steps):
        # Convert tangent angles to radians
        in_tangent_angle = in_tangent_angle * (3.141592653589793 / 180.0)
        out_tangent_angle = out_tangent_angle * (3.141592653589793 / 180.0)

        # Calculate control points based on the tangent angles and distance
        in_tangent_length = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5
        out_tangent_length = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5

        in_tangent = [start[0] + in_tangent_length * math.cos(in_tangent_angle),
                      start[1] + in_tangent_length * math.sin(in_tangent_angle)]
        out_tangent = [end[0] - out_tangent_length * math.cos(out_tangent_angle),
                       end[1] - out_tangent_length * math.sin(out_tangent_angle)]
        # Calculate Bezier curve points
        points = []
        for t in range(num_steps + 1):
            t /= num_steps

            x = (1 - t) ** 3 * start[0] + 3 * (1 - t) ** 2 * t * in_tangent[0] + 3 * (1 - t) * t ** 2 * out_tangent[
                0] + t ** 3 * end[0]
            y = (1 - t) ** 3 * start[1] + 3 * (1 - t) ** 2 * t * in_tangent[1] + 3 * (1 - t) * t ** 2 * out_tangent[
                1] + t ** 3 * end[1]
            print('t', t, y)
            points.append([x, y])

        return points

    def cubic_bezier2(self, start, end, in_tangent_angle, out_tangent_angle, t):
        # Convert tangent angles to radians
        in_tangent_angle = in_tangent_angle * (3.141592653589793 / 180.0)
        out_tangent_angle = out_tangent_angle * (3.141592653589793 / 180.0)

        # Calculate control points based on the tangent angles and distance
        in_tangent_length = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5
        out_tangent_length = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5

        in_tangent = [start[0] + in_tangent_length * math.cos(in_tangent_angle),
                      start[1] + in_tangent_length * math.sin(in_tangent_angle)]
        out_tangent = [end[0] - out_tangent_length * math.cos(out_tangent_angle),
                       end[1] - out_tangent_length * math.sin(out_tangent_angle)]
        # Calculate Bezier curve points

        x = (1 - t) ** 3 * start[0] + 3 * (1 - t) ** 2 * t * in_tangent[0] + 3 * (1 - t) * t ** 2 * out_tangent[
            0] + t ** 3 * end[0]
        y = (1 - t) ** 3 * start[1] + 3 * (1 - t) ** 2 * t * in_tangent[1] + 3 * (1 - t) * t ** 2 * out_tangent[
            1] + t ** 3 * end[1]
        return x, y

    def plot_guess(self, *args):
        curves = cmds.keyframe(q=True, name=True, sl=True)  # get all selected animCurve Nodes
        if not curves:
            return
        for crv in curves:
            allKeyIndexes = cmds.keyframe(crv, q=True, indexValue=True, sl=True)
            keyCount = cmds.keyframe(crv, q=True, keyframeCount=True)
            for keyIndex in allKeyIndexes:
                currentValue = cmds.keyframe(crv, index=(keyIndex,), q=True, valueChange=True)[0]
                currentTime = cmds.keyframe(crv, index=(keyIndex,), q=True, timeChange=True)[0]

                previousTime = currentTime
                previousValue = currentValue
                nextTime = currentTime
                nextValue = currentValue

                inAngle = 0
                outAngle = 0

                if keyIndex > 0:
                    previousValue = cmds.keyframe(crv, index=((keyIndex - 1),), q=True, valueChange=True)[0]
                    previousTime = cmds.keyframe(crv, index=((keyIndex - 1),), q=True, timeChange=True)[0]
                    inAngle = cmds.keyTangent(crv, query=True, outAngle=True, index=((keyIndex - 1),))[0]
                if keyIndex < keyCount - 1:
                    nextValue = cmds.keyframe(crv, index=((keyIndex + 1),), q=True, valueChange=True)[0]
                    nextTime = cmds.keyframe(crv, index=((keyIndex + 1),), q=True, timeChange=True)[0]
                    outAngle = cmds.keyTangent(crv, query=True, inAngle=True, index=((keyIndex + 1),))[0]

                alpha = (currentTime - previousTime) / (nextTime - previousTime)

                time, value = self.cubic_bezier2([previousTime, previousValue], [nextTime, nextValue], inAngle,
                                                 outAngle, alpha)
                # values = cubic_bezier([previousTime,previousValue], [nextTime, nextValue], inAngle, outAngle, int(nextTime-previousTime + 1))
                cmds.keyframe(crv, index=((keyIndex),), edit=True, valueChange=value)
        self.autoTangentKey()


class KeyButtonWidgetLayout(QHBoxLayout):
    def __init__(self, toolTip=''):
        super(KeyButtonWidgetLayout, self).__init__()

        self.setSpacing(0)
        self.setContentsMargins(1, 0, 1, 0)


class AutoTangentWidgetLayout(KeyButtonWidgetLayout):
    def __init__(self, toolTip=''):
        super(AutoTangentWidgetLayout, self).__init__(toolTip=toolTip)

        self.autoTangentButton = GraphToolbarButton(icon='autoTangent.png',
                                                    toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                        'autoTangent', dict())
                                                    )
        self.softnessLabel = QLabel('Softness')
        self.spinBox = NudgeSpinBox(defaultValue=KeyModifiers().defaultSoftness(),
                                    controlStep=0.05,
                                    shiftStep=0.2,
                                    defaultStep=0.1)
        self.spinBox.setFixedWidth(self.spinBox.sizeHint().width() + 4 * dpiScale())
        self.spinBox.setMinimum(0.01)
        self.spinBox.setMaximum(10)

        self.addWidget(self.autoTangentButton)
        self.addWidget(self.softnessLabel)
        self.addWidget(self.spinBox)

        self.autoTangentButton.clicked.connect(self.theCommand)

        self.spinBox.valueChanged.connect(self.softnessChanged)
        self.setPopupMenu()

    def setPopupMenu(self):
        self.autoTangentButton.pop_up_window = AutoTangentPopup('name', self)
        self.autoTangentButton.pop_up_window.setSpinBox(self.spinBox)
        self.autoTangentButton.setContextMenuPolicy(Qt.CustomContextMenu)
        self.autoTangentButton.customContextMenuRequested.connect(self.autoTangentButton._showMenu)

    def theCommand(self):
        KeyModifiers().autoTangentKey(softness=self.spinBox.value())

    def softnessChanged(self):
        KeyModifiers().setDefaultSoftness(self.spinBox.value())
        KeyModifiers().autoTangentKey(softness=self.spinBox.value())


class AutoTangentPopup(ButtonPopup):
    def __init__(self, name, parent=None):
        super(AutoTangentPopup, self).__init__(parent)

        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()
        self.spinBox = None

    def create_widgets(self):
        pass

    def setSpinBox(self, spinBox):
        self.spinBox = spinBox

    def create_layout(self):
        tbAdjustmentBlendLabel = QLabel('AutoTangent')

        self.layout.addRow(tbAdjustmentBlendLabel)

        button = QPushButton('Set Default')
        button.clicked.connect(self.setDefault)
        self.layout.addRow(button)

    def setDefault(self):
        KeyModifiers().setDefaultSoftness(self.spinBox.value())
        self.hide()


class OffsetKeyWidgetLayout(KeyButtonWidgetLayout):
    def __init__(self, toolTip=''):
        super(OffsetKeyWidgetLayout, self).__init__(toolTip=toolTip)

        self.offsetLeftButton = GraphToolbarButton(icon='offsetKeyLeft.png',
                                                   toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                       'offsetKeyLeft', dict()))
        self.offsetRightButton = GraphToolbarButton(icon='offsetKeyRight.png',
                                                    toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                        'offsetKeyRight', dict()))

        self.offsetSpinBox = NudgeSpinBox(defaultValue=KeyModifiers().defaultNudgeOffset(),
                                          controlStep=0.25,
                                          shiftStep=2.0,
                                          defaultStep=1.0)
        self.offsetSpinBox.setFixedWidth(self.offsetSpinBox.sizeHint().width() * dpiScale())
        self.offsetSpinBox.setMinimum(0.0)

        self.addWidget(self.offsetLeftButton)
        self.addWidget(self.offsetSpinBox)
        self.addWidget(self.offsetRightButton)

        self.offsetLeftButton.clicked.connect(self.offsetKeysLeft)
        self.offsetRightButton.clicked.connect(self.offsetKeysRight)

    def offsetKeysLeft(self):
        KeyModifiers().offsetKeys(offset=-1 * self.offsetSpinBox.value())

    def offsetKeysRight(self):
        KeyModifiers().offsetKeys(offset=1 * self.offsetSpinBox.value())

    def offsetValueChanged(self):
        KeyModifiers().setDefaultOffset(self.spinBox.value())


class NudgeKeyWidgetLayout(KeyButtonWidgetLayout):
    def __init__(self, toolTip=''):
        super(NudgeKeyWidgetLayout, self).__init__(toolTip=toolTip)

        self.nudgeLeftButton = GraphToolbarButton(icon='nudgeKeyLeft.png',
                                                  toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                      'nudgeKeyLeft', dict()))

        self.nudgeRightButton = GraphToolbarButton(icon='nudgeKeyRight.png',
                                                   toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                       'nudgeKeyRight', dict()))

        self.nudgeSpinBox = NudgeSpinBox(defaultValue=KeyModifiers().defaultOffset(),
                                         controlStep=0.25,
                                         shiftStep=2.0,
                                         defaultStep=1.0)
        self.nudgeSpinBox.setFixedWidth(self.nudgeSpinBox.sizeHint().width() * dpiScale())
        self.nudgeSpinBox.setMinimum(0.0)

        self.addWidget(self.nudgeLeftButton)
        self.addWidget(self.nudgeSpinBox)
        self.addWidget(self.nudgeRightButton)

        self.nudgeLeftButton.clicked.connect(self.nudgeLeft)
        self.nudgeRightButton.clicked.connect(self.nudgeRight)

        # self.spinBox.valueChanged.connect(self.softnessChanged)

    def nudgeLeft(self):
        KeyModifiers().nudgeKeys(offset=-1 * self.nudgeSpinBox.value())

    def nudgeRight(self):
        KeyModifiers().nudgeKeys(offset=1 * self.nudgeSpinBox.value())

    def nudgeValueChanged(self):
        KeyModifiers().defaultNudgeOffset(self.nudgeSpinBox.value())


class MatchTangentWidgetLayout(KeyButtonWidgetLayout):
    def __init__(self, toolTip=''):
        super(MatchTangentWidgetLayout, self).__init__(toolTip=toolTip)

        matchTangentStartButton = GraphToolbarButton(icon='matchTangentStart.png',
                                                     toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                         'matchTangentStart', dict()),

                                                     width=18)
        matchTangentEndButton = GraphToolbarButton(icon='matchTangentEnd.png',
                                                   toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                       'matchTangentEnd', dict()),
                                                   width=18)

        plotButton = GraphToolbarButton(icon='plotKey.png',
                                        toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                            'matchTangentEnd', dict())
                                        )

        self.addWidget(matchTangentStartButton)
        self.addWidget(matchTangentEndButton)
        self.addWidget(plotButton)

        plotButton.clicked.connect(create_callback(KeyModifiers().plot_guess))
        matchTangentStartButton.clicked.connect(KeyModifiers().matchStartTangentsToEndTangents)
        matchTangentEndButton.clicked.connect(KeyModifiers().matchEndTangentsToStartTangents)


class FlipKeyWidgetLayout(KeyButtonWidgetLayout):
    def __init__(self, toolTip=''):
        super(FlipKeyWidgetLayout, self).__init__(toolTip=toolTip)

        self.flipFirstButton = GraphToolbarButton(icon='flipKeysStart.png',
                                                  toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                      'flipKeysStart', dict()))

        self.flipZeroButton = GraphToolbarButton(icon='flipKeys.png',
                                                 toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                     'flipKeys', dict()))

        self.flipLastButton = GraphToolbarButton(icon='flipKeysEnd.png',
                                                 toolTip=KeyModifiers().rawJsonBaseData['toolTips'].get(
                                                     'flipKeysEnd', dict()))

        self.flipFirstButton.clicked.connect(create_callback(KeyModifiers().flipKeyValues, first=True))
        self.flipZeroButton.clicked.connect(create_callback(KeyModifiers().flipKeyValues))
        self.flipLastButton.clicked.connect(create_callback(KeyModifiers().flipKeyValues, last=True))

        self.addWidget(self.flipFirstButton)
        self.addWidget(self.flipZeroButton)
        self.addWidget(self.flipLastButton)

        # self.offsetLeftButton.clicked.connect(create_callback(KeyModifiers().autoTangentKey))
        # self.spinBox.valueChanged.connect(self.softnessChanged)

    def softnessChanged(self):
        KeyModifiers().setDefaultSoftness(self.spinBox.value())


class NudgeSpinBox(QDoubleSpinBox):
    def __init__(self, defaultValue=1, controlStep=0.25, shiftStep=2, defaultStep=1.0, *args, **kwargs):
        super(NudgeSpinBox, self).__init__(*args, **kwargs)
        self.default_value = defaultValue
        self.setValue(self.default_value)
        self.controlStep = controlStep
        self.shiftStep = shiftStep
        self.defaultStep = defaultStep
        self.setSingleStep(defaultStep)

    def wheelEvent(self, event: QWheelEvent):
        step = self.singleStep()  # Default step
        modifiers = event.modifiers()

        if modifiers & Qt.AltModifier:
            self.setValue(self.default_value)
            return

        # Check modifiers and adjust step
        if modifiers & Qt.ShiftModifier:
            step = self.shiftStep
        elif modifiers & Qt.ControlModifier:
            step = self.controlStep

        # Adjust the spinbox value based on the event delta
        if event.angleDelta().y() > 0:
            self.setValue(self.value() + step)
        else:
            self.setValue(self.value() - step)

        # Accept the event so the base class wheel event is not processed
        event.accept()

    def mousePressEvent(self, event):
        print('mousePressEvent')
        if event.modifiers() & Qt.ControlModifier and event.button() == Qt.LeftButton:
            self.setValue(self.default_value)  # Reset value to 1
            event.accept()  # Accept the event
        else:
            # Call the base class implementation for regular behavior
            super(NudgeSpinBox, self).mousePressEvent(event)
