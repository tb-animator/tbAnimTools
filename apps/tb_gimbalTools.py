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

tbGimbalQuickBakeNewLayerOptionVar = 'tbGimbalQuickBakeNewLayer'

tbGimbalQuickBakeOptionVar = 'tbGimbalQuickBake'
tbGimbalNewLayerBakeOptionVar = 'tbGimbalDefaultBakeToNewLayer'
tbGimbalJustFrameOptionVar = 'tbGimbalJustFrame'

from . import *

maya.utils.loadStringResourcesForModule(__name__)

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

## a dictionary of possible rotation order values
rotateOrderDict = {
    0: {'rotateOrder': om.MEulerRotation.kXYZ, 'middleAxis': 1},
    1: {'rotateOrder': om.MEulerRotation.kYZX, 'middleAxis': 2},
    2: {'rotateOrder': om.MEulerRotation.kZXY, 'middleAxis': 0},
    3: {'rotateOrder': om.MEulerRotation.kXZY, 'middleAxis': 2},
    4: {'rotateOrder': om.MEulerRotation.kYXZ, 'middleAxis': 0},
    5: {'rotateOrder': om.MEulerRotation.kZYX, 'middleAxis': 1}
}

rotateOrderList = ['xyz',
                   'yzx',
                   'zxy',
                   'xzy',
                   'yxz',
                   'zyx']

defaultRoAttribute = 'defaultRotateOrder'
greenRGB = [54, 161, 46]

greenBrightRGB = [52, 221, 39]
yellowRGB = [244, 232, 0]
orangeRGB = [242, 137, 0]
blueRGB = [65, 162, 215]
redRGB = [233, 66, 19]
green = [x / 255.0 for x in greenRGB]

greenBright = [x / 255.0 for x in greenBrightRGB]
yellow = [x / 255.0 for x in yellowRGB]
orange = [x / 255.0 for x in orangeRGB]
blue = [x / 255.0 for x in blueRGB]
red = [x / 255.0 for x in redRGB]
defaultGrey = [0.365, 0.365, 0.365]
large = 99.8
small = 0.001

orangeColour = [215, 128, 26]

currentBackgroundSS = """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #00BF01, stop: 0.1 #00A601, stop: 0.5 #008C01, stop: 0.9 #007301, stop: 1 #005901);"""
defaultBackgroundSS = """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #005901);"""
orangeBackgroundSS = """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e58d26, stop: 0.1 #d7801a, stop: 0.5 #d7801a, stop: 0.9 #c07217, stop: 1 #aa6514);"""
mainStyleSheet = getqss.getStyleSheet()


def tintedButton(colourA, colourB, colourC, colourD, colourE):
    return """font-weight: bold; font-size: 18px;background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 {colourA}, stop: 0.1 {colourB}, stop: 0.5 {colourC}, stop: 0.9 {colourD}, stop: 1 {colourE});""".format(
        colourA=colourA,
        colourB=colourB,
        colourC=colourC,
        colourD=colourD,
        colourE=colourE,
    )


class decorator(object):
    def __init__(self):
        pass

    @staticmethod
    def timer(func):
        '''
        Super awesome and cool for profiling a script - outputs the time taken by the function
        :param func:
        :return:
        '''

        def wrapper(*arg, **kw):
            t1 = time.time()
            res = func(*arg, **kw)
            t2 = time.time()
            return func.__name__, 'evaluation time:: ', (t2 - t1)

        return wrapper

    @staticmethod
    def timerVerbose(func):
        def wrapper(*arg, **kw):
            t1 = time.time()
            res = func(*arg, **kw)
            t2 = time.time()
            return func.__name__, 'evaluation time:: ', (t2 - t1), '\nResult::', res

        return wrapper

    @staticmethod
    def undoChunk(func):
        """
        Opens a new undo chunk for the current function. Means all maya commands passed in the function will only be
        part of one ctrl+z
        @param func:
        @return:
        """

        def pre(*args, **kwargs):
            cmds.undoInfo(openChunk=True)
            return_func = post(*args, **kwargs)
            return return_func

        def post(*args, **kwargs):
            return_func = func(*args, **kwargs)
            cmds.undoInfo(closeChunk=True)
            return return_func

        try:
            return pre

        except Exception as e:
            print(e)
            return None

    @staticmethod
    def undoToggle(func):
        """
        Turns the undo queue off during the function. Then back on afterwards. If the function fails it will restore the queue
        @param func: Function
        @return:
        """

        def pre(*args, **kwargs):
            cmds.undoInfo(stateWithoutFlush=False)
            return_func = post(*args, **kwargs)
            return return_func

        def post(*args, **kwargs):
            # We need to be careful with turning off the undo. the finally will always turn it on even with a fail
            try:
                return_func = func(*args, **kwargs)
            except Exception as e:
                return_func = None
                cmds.warning(e)

            finally:
                cmds.undoInfo(stateWithoutFlush=True)

            return return_func

        try:
            return pre

        except Exception as e:
            cmds.warning(e, e)
            return None


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('gimbal'))
        self.addCommand(self.tb_hkey(name='gimbalToolUI',
                                     annotation='Open the gimbal tool UI',
                                     category=self.category,
                                     command=['GimbalTool.showUI()']))
        for order in rotateOrderList:
            self.addCommand(self.tb_hkey(name='quickBakeToLayer%s' % str(order.upper()),
                                         annotation='One click bake to %s on a new layer' % order,
                                         category=self.category,
                                         command=['GimbalTool.quickBake("%s", True, False)' % order]))
        # TODO might be already present in main tools?
        self.addCommand(self.tb_hkey(name='tbSelectiveEulerFilter', annotation='euler filter the selected curves',
                                     category=self.category, command=['GimbalTool.eulerFilter()']))

        self.addCommand(self.tb_hkey(name='tbGimbalMarkingMenuPress',
                                     annotation='useful comment',
                                     category=self.category, command=['GimbalTool.openMM()']))
        self.addCommand(self.tb_hkey(name='tbGimbalMarkingMenuRelease',
                                     annotation='useful comment',
                                     category=self.category, command=['GimbalTool.closeMM()']))
        return self.commandList

    def assignHotkeys(self):
        return


class GimbalTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'GimbalTool'
    hotkeyClass = hotkeys()
    funcs = Functions()
    updateDisabled = False
    version = 2.04

    def __new__(cls):
        if GimbalTool.__instance is None:
            GimbalTool.__instance = object.__new__(cls)

        GimbalTool.__instance.val = cls.toolName
        GimbalTool.__instance.loadData()

        return GimbalTool.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(GimbalTool, self).optionUI()
        quickBake = get_option_var(tbGimbalQuickBakeOptionVar, True)
        quickBakeNewLayer = get_option_var(tbGimbalQuickBakeNewLayerOptionVar, True)

        tempControlHeader = subHeader('Quick Change options')
        tempControlInfo = infoLabel([
            'Choose if the quick swap from the marking menu bakes keys, or keeps current, and if the result should be on a new layer'])
        quickBakeKeyOptionWidget = optionVarBoolWidget('Quick swap bakes animation', tbGimbalQuickBakeOptionVar)
        quickBakeLayerOptionWidget = optionVarBoolWidget('Quick swap creates new layer',
                                                         tbGimbalQuickBakeNewLayerOptionVar)
        quickBakeKeyOptionWidget = optionVarBoolWidget('Marking menu main button bakes to new layer', tbGimbalNewLayerBakeOptionVar)

        self.layout.addWidget(tempControlHeader)
        self.layout.addWidget(tempControlInfo)
        self.layout.addWidget(quickBakeKeyOptionWidget)
        self.layout.addWidget(quickBakeKeyOptionWidget)
        self.layout.addWidget(quickBakeLayerOptionWidget)

        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        # ui = self.gimbalUI(parentCLS=self)
        # ui.showUI()

        if not GimbalUI_pyside.instance:
            GimbalUI_pyside.instance = GimbalUI_pyside(title='Rotate Order Switch',
                                                       text='test',
                                                       )
        GimbalUI_pyside.instance.show()
        GimbalUI_pyside.instance.raise_()
        # GimbalUI_pyside.resize(GimbalUI_pyside.sizeHint())

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='Rotation Order Swap', image='tbGimbalUI.png', command='gimbalToolUI',
                      sourceType='mel',
                      parent=parentMenu)

    def build_MM(self):
        selection = cmds.ls(sl=True, type='transform')
        positions = ["NW", "N", "NE", "SE", "S", "SW"]
        iconDict = {0: 'tbGimbalGreen.png',
                    30: 'tbGimbalOrange.png',
                    60: 'tbGimbalRed.png'}
        bakeClass = BakeOrderClass(self)

        defaultToBakeNewLayerOption = get_option_var(tbGimbalNewLayerBakeOptionVar, True)

        quickBake = get_option_var(tbGimbalQuickBakeOptionVar, True)
        quickBakeNewLayer = get_option_var(tbGimbalQuickBakeNewLayerOptionVar, True)

        cmds.menuItem(label='{:^24s}'.format('- Swap rotation order -'),
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        isFrame = get_option_var(tbGimbalJustFrameOptionVar, True)
        isBake = not isFrame and get_option_var(tbGimbalQuickBakeOptionVar, True)
        isKeys = not isFrame and not get_option_var(tbGimbalQuickBakeOptionVar, True)

        if selection:
            defaultRotateOrder, defaultRotateOrderInt = self.get_original_rotation_order(input=selection[-1])
            gimbalValues = self.get_all_gimbal_values(selection[-1])
            bestIndex = list(gimbalValues.values()).index(min(gimbalValues.values()))

            for index, value in enumerate(rotateOrderList):
                iconKey = 0
                for key in sorted(iconDict.keys()):
                    if gimbalValues[index] >= key:
                        iconKey = key
                valueActual = "%.2f" % gimbalValues[index]
                if gimbalValues[index] < 10.0:
                    valueActual = '0' + valueActual
                valueLabel = valueActual.rjust(7, ' ')
                label = str("{}{} {}".format(valueLabel, '%', value))
                if index == defaultRotateOrderInt:
                    label = label + ' - Default'
                elif index == cmds.getAttr(selection[-1] + '.rotateOrder'):
                    label = label + ' - Current'
                cmds.menuItem(label=label,
                              # radialPosition=positions[index],
                              divider=0,
                              image=iconDict[iconKey],
                              subMenu=0,
                              tearOff=0,
                              altModifier=0,
                              optionModifier=0,
                              commandModifier=0,
                              ctrlModifier=0,
                              shiftModifier=0,
                              optionBox=0,
                              enable=1,
                              data=0,
                              allowOptionBoxes=1,
                              postMenuCommandOnce=0,
                              enableCommandRepeat=1,
                              echoCommand=0,
                              italicized=0,
                              boldFont=index == int(bestIndex),
                              sourceType="python",
                              longDivider=1,
                              command=create_callback(self.orderMMButtonPressed,
                                                      value,
                                                      quickBake,
                                                      isFrame,
                                                      defaultToBakeNewLayerOption))
                cmds.menuItem(command=create_callback(self.orderMMButtonPressed,
                                                      value,
                                                      quickBake,
                                                      isFrame,
                                                      not defaultToBakeNewLayerOption),
                              optionBox=True,
                              optionBoxIcon='addClip.png',
                              )
        else:  # no selection
            cmds.menuItem(label='{:^24s}'.format('No object selected'),
                          enable=False,
                          )

        cmds.menuItem(label='Divider',
                      divider=True,
                      enable=False,
                      )

        # Create a radio menu item collection
        cmds.menuItem(label='Divider',
                      divider=True)
        cmds.menuItem(label='Mode', enable=False)
        radio_collection = cmds.radioMenuItemCollection()
        #

        cmds.menuItem(label='Bake Keys', radioButton=isBake,
                      command=create_callback(self.set_quick_bake_mode, True))
        cmds.menuItem(label='Just keys', radioButton=isKeys,
                      command=create_callback(self.set_quick_bake_mode, False))
        cmds.menuItem(label='Highlighted Frames', radioButton=isFrame,
                      command=create_callback(self.set_key_bake_mode, True))
        cmds.menuItem(label='Divider',
                      divider=True)
        # cmds.menuItem(label='Bake Keys',
        #               isRadioButton=True,
        #               checkBox=quickBake,
        #               enable=True,
        #
        #               command=create_callback(set_option_var, tbGimbalQuickBakeOptionVar, not quickBake)
        #               )
        # cmds.menuItem(label='Bake to new layer',
        #               checkBox=quickBakeNewLayer,
        #               command=create_callback(set_option_var, tbGimbalQuickBakeNewLayerOptionVar, not quickBakeNewLayer)
        #               )
        if selection:
            cmds.menuItem(label='Bake to lower layer value',
                          image='bakeAnimation.png',
                          command=create_callback(self.quickBakeToLowestGimbal)
                          )

        cmds.menuItem(label='Open UI',
                      image='tbGimbalUI.png',
                      enable=True,
                      sourceType="mel",
                      command="gimbalToolUI")

    def set_quick_bake_mode(self, mode, *args):
        set_option_var(tbGimbalQuickBakeOptionVar, mode)
        set_option_var(tbGimbalJustFrameOptionVar, False)

    def set_key_bake_mode(self, mode, *args):
        set_option_var(tbGimbalQuickBakeOptionVar, False)
        set_option_var(tbGimbalQuickBakeOptionVar, False)
        set_option_var(tbGimbalJustFrameOptionVar, mode)

    def get_rotate_order_list(self, input):
        rotateOrders = cmds.attributeQuery('rotateOrder', node=input, listEnum=True)
        rotateOrders = rotateOrders[0].split(':')
        return rotateOrders

    def staticSwapOrder(self, node, order):
        isHighlighted = self.funcs.isTimelineHighlighted()
        timeStart = int(cmds.currentTime(query=True))
        timeEnd = int(cmds.currentTime(query=True))
        if isHighlighted:
            timeStart, timeEnd = self.funcs.getTimelineHighlightedRange()
        timeStart = int(timeStart)
        timeEnd = int(timeEnd)
        preTime = cmds.currentTime(query=True)
        for i in range(timeEnd - timeStart, -1, -1):
            cmds.currentTime(i + timeStart)
            self.swap_rotate_order(node, order)
        cmds.currentTime(preTime)

    def swap_rotate_order(self, input, rotateOrder):
        if isinstance(rotateOrder, int):
            rotateOrder = self.get_rotate_order_list(input)[rotateOrder]
        if isinstance(input, list):
            input = input[-1]
        self.get_original_rotation_order(input=input)
        cmds.xform(input,
                   preserve=True,
                   rotateOrder=rotateOrder
                   )

    def orderMMButtonPressed(self, order=0, bake=True, keyOnly=False, newLayer=True, *args):
        sel = cmds.ls(sl=True, type='transform')

        if not sel:
            return error(position="botRight",
                         prefix="Error",
                         message='No objects selected', fadeStayTime=3.0, fadeOutTime=4.0)

        keyedObjects = [s for s in sel if self.hasAnimCurves(s)]
        nonKeyedObjects = [x for x in sel if x not in keyedObjects]
        if keyOnly:
            self.staticSwapOrder(sel, order)
        else:
            bakeOrderClass = BakeOrderClass(nodeList=keyedObjects,
                                            orderList=[order] * len(keyedObjects),
                                            keepCurrentKeys=not bake,
                                            bakeSample=1,
                                            tolerance=1 * 0.01,
                                            bakeToNewLayer=newLayer)
            bakeOrderClass.bakeOrder()
            if nonKeyedObjects:
                self.staticSwapOrder(nonKeyedObjects, order)

    def hasAnimCurves(self, inputData):
        animCurves = self.getAllAnimCurves(inputData)
        if animCurves:
            return True

    def quickBake(self, order, newLayer, keepKeys, *args):
        sel = cmds.ls(sl=True, type='transform')
        if order not in rotateOrderList:
            return error(position="botRight",
                         prefix="Error",
                         message='No objects selected', fadeStayTime=3.0, fadeOutTime=4.0)
        self.updateDisabled = True
        bakeClass = BakeOrderClass(nodeList=sel,
                                   orderList=[order] * len(sel),
                                   keepCurrentKeys=keepKeys,
                                   bakeSample=1,
                                   bakeToNewLayer=newLayer)
        bakeClass.bakeOrder()
        self.updateDisabled = False

    def quickBakeToLowestGimbal(self, sel):
        quickBake = get_option_var(tbGimbalQuickBakeOptionVar, True)
        quickBakeNewLayer = get_option_var(tbGimbalQuickBakeNewLayerOptionVar, True)
        if not sel:
            sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return
        orderList = list()  # synched list of orders with selection
        for s in sel:
            lowest = self.getLowestGimbalOrder(s)
            orderList.append(rotateOrderList[lowest])
        bakeClass = BakeOrderClass(nodeList=sel,
                                   orderList=orderList,
                                   keepCurrentKeys=quickBakeNewLayer,
                                   bakeSample=1,
                                   bakeToNewLayer=not quickBake)
        bakeClass.bakeOrder()

    def get_current_gimbal_amount(self, r):
        d = r * (180.0 / math.pi)
        return 100.0 * (abs(((d + 90.0) % 180.0) - 90.0) / 90.0)

    def getAllAnimCurves(self, inputData):
        historyNodes = cmds.listHistory(inputData, pruneDagObjects=True, leaf=False)
        animCurves = cmds.ls(historyNodes, type='animCurve')
        return animCurves

    def hasAnimCurves(self, inputData):
        animCurves = self.getAllAnimCurves(inputData)
        if animCurves:
            return True

    def get_all_gimbal_values(self, inputData):
        returnDict = {}
        node = om2.MSelectionList().add(str(inputData)).getDependNode(0)
        nodeRotation = om2.MFnTransform(node).rotation(asQuaternion=False)
        nodeRotationOrder = om2.MFnTransform(node).rotationOrder()
        for rotationOrder in rotateOrderDict.keys():
            newRotation = nodeRotation.reorder(rotationOrder)
            returnDict[rotationOrder] = self.get_current_gimbal_amount(
                newRotation[rotateOrderDict[rotationOrder]['middleAxis']])
        return returnDict

    def getLowestGimbalOrder(self, inputData):
        allValues = self.get_all_gimbal_values(inputData)
        lowest = min(allValues, key=allValues.get)
        return lowest

    def eulerFilter(self):
        EulerFilter().filter()

    def get_original_rotation_order(self, input=None):
        if not cmds.attributeQuery(defaultRoAttribute, node=input, exists=True):
            self.tag_original_rotation_order(input)
        stringValue = cmds.getAttr(input + '.' + defaultRoAttribute, asString=True)
        rotateOrders = self.get_rotate_order_list(input)
        intValue = rotateOrders.index(cmds.getAttr(input + '.' + defaultRoAttribute))
        return stringValue, intValue

    def tag_original_rotation_order(self, input):
        if not cmds.attributeQuery(defaultRoAttribute, node=input, exists=True):
            cmds.addAttr(input, ln=defaultRoAttribute, dt='string')
        currentRO = cmds.getAttr(input + '.rotateOrder', asString=True)
        cmds.setAttr(input + '.' + defaultRoAttribute, currentRO, type='string')


class BakeOrderClass(object):
    def __init__(self,
                 nodeList=[],
                 orderList=[],
                 bakeSample=1,
                 tolerance=1,
                 keepCurrentKeys=False,
                 bakeToNewLayer=False):

        self.funcs = GimbalTool.funcs
        self.tempLocators = []
        self.tempNulls = []
        self.tempConstraints = []
        self.allKeyInfo = []
        self.firstKeys = []
        self.lastKeys = []
        self.originalOrders = []

        self.nodeList = nodeList
        self.orderList = orderList
        self.bakeSample = bakeSample
        self.tolerance = tolerance
        self.layerBakeMode = bakeToNewLayer  # true means bake to a new layer
        self.keepCurrentKeys = keepCurrentKeys
        self.newLayer = None
        self.newLayerName = None
        self.staticNodes = []
        self.staticNodeOrders = []

    def get_rotate_order_list(self, input):
        rotateOrders = cmds.attributeQuery('rotateOrder', node=input, listEnum=True)
        rotateOrders = rotateOrders[0].split(':')
        return rotateOrders

    def staticSwapOrder(self, node, order):
        GimbalTool.swap_rotate_order(node, order)
        self.updateGimbalLabels()

    def swap_rotate_order(self, input, rotateOrder):
        if isinstance(rotateOrder, int):
            rotateOrder = self.get_rotate_order_list(input)[rotateOrder]
        GimbalTool.get_original_rotation_order(input=input)
        cmds.xform(input,
                   preserve=True,
                   rotateOrder=rotateOrder
                   )

    @decorator.timer
    def bakeOrder(self):
        for index, value in enumerate(self.nodeList):
            if not self.hasAnimCurves(value):
                self.staticNodes.append(self.nodeList[index])
                self.staticNodeOrders.append(self.orderList[index])
                GimbalTool.swap_rotate_order(value, self.orderList[index])
        for index, value in enumerate(self.nodeList):
            if value in self.staticNodes:
                self.nodeList.pop(index)
                self.orderList.pop(index)

        preSel = cmds.ls(sl=True)

        if self.layerBakeMode:
            for s in preSel:
                try:
                    cmds.setAttr(s + ".rotateOrder", lock=False)
                except Exception as e:
                    cmds.warning(e)

            layerOkState = self.funcs.checkKeyableState(list(self.nodeList))
            if not layerOkState:
                msg = 'Rotate orders on some objects are not keyable, aborting\nSee script window for information'
                error(position="botRight",
                      prefix="Error",
                      message=msg, fadeStayTime=3.0, fadeOutTime=4.0)
                cmds.select(preSel, replace=True)
                return

        startTime = cmds.timerX()
        self.cleanUpLocators()
        self.tempLocators = []
        self.tempConstraints = []
        self.allKeyInfo = []
        self.firstKeys = []
        self.lastKeys = []
        self.originalOrders = []


        if not isinstance(self.nodeList, list):
            self.nodeList = [self.nodeList]
        if not isinstance(self.orderList, list):
            self.orderList = [self.orderList]

        if not self.nodeList:
            return cmds.warning('No objects to bake, exiting')
        if not self.orderList:
            return cmds.warning('No rotation orders specified, exiting')

        for index, value in enumerate(self.nodeList):
            self.originalOrders.append(GimbalTool().get_original_rotation_order(value)[1])
            self.allKeyInfo.append(self.get_all_key_times(value))
            self.firstKeys.append(self.allKeyInfo[index][0])
            self.lastKeys.append(self.allKeyInfo[index][-1])

            tempLocName = str("{}_roBake".format(str(value)))
            if cmds.objExists(tempLocName):
                cmds.delete(tempLocName)
            tempObj = cmds.duplicate(value, parentOnly=True)[0]
            parentNode = cmds.listRelatives(value, parent=True)

            if cmds.listConnections(value + '.offsetParentMatrix'):
                offsetParentMatrixConnection = cmds.listConnections(value + '.offsetParentMatrix',
                                                                    source=True,
                                                                    plugs=True)
                # using offset parent matrix but not inheriting transform
                cmds.connectAttr(offsetParentMatrixConnection[0], tempObj + '.offsetParentMatrix')

            self.tempLocators.append(tempObj)
            cmds.setAttr(tempObj + '.rotateOrder', cmds.getAttr(value + '.rotateOrder'))
            constraint = cmds.parentConstraint(value, tempObj)
            self.tempConstraints.append(constraint)
            cmds.setAttr(tempObj + '.rotateOrder', rotateOrderList.index(self.orderList[index]))

        self.bakeStart = min(self.firstKeys)
        self.bakeEnd = max(self.lastKeys)

        if self.keepCurrentKeys:
            sampleRate = 1
        else:
            sampleRate = self.bakeSample

        self.newLayerName = self.nodeList[0].split(':')[-1] + '_' + self.orderList[0]
        self.newLayer = None

        selectedLayer = GimbalTool.funcs.get_selected_layers()
        if selectedLayer:
            if isinstance(selectedLayer, list):
                selectedLayer = selectedLayer[0]

        if self.layerBakeMode:
            self.newLayer = cmds.animLayer(override=True)
            self.newLayer = cmds.rename(self.newLayer, self.newLayerName)
        else:
            if self.getLayerInclusion(self.nodeList, layerToCheck=selectedLayer):
                self.newLayer = selectedLayer
            else:
                self.newLayer = None

        cmds.bakeResults(self.tempLocators,
                         time=(self.bakeStart, self.bakeEnd),
                         simulation=False,
                         attribute=('rotateX', 'rotateY', 'rotateZ'),
                         sampleBy=sampleRate,
                         # oversamplingRate=1,
                         disableImplicitControl=False,
                         preserveOutsideKeys=False,
                         sparseAnimCurveBake=False,
                         removeBakedAttributeFromLayer=False,
                         removeBakedAnimFromLayer=False,
                         bakeOnOverrideLayer=False,
                         minimizeRotation=False,
                         controlPoints=False,
                         shape=False)
        cmds.select(self.tempLocators)

        # filter the bake result
        self.filterNode(self.tempLocators)
        # remove constraints
        for x in self.tempConstraints:
            cmds.delete(x)
        self.tempConstraints = []

        if self.keepCurrentKeys:
            if self.tolerance >= small:
                # if we aren't just baking to specific key sample
                for index, value in enumerate(self.tempLocators):
                    self.trimStartKeys(value, self.bakeStart, self.firstKeys[index])
                    self.trimEndKeys(value, self.lastKeys[index], self.bakeEnd)
                    # self.filterNode(value)
                    for curve in self.getAllAnimCurves(value):
                        self.set_curve_tangents(curve)

                    if self.tolerance < large:
                        for x in range(0, len(self.allKeyInfo[index]) - 1):
                            self.simplifyRange(value, self.allKeyInfo[index][x], self.allKeyInfo[index][x + 1])
                            # self.filterNode(value)
                    else:
                        for x in range(0, len(self.allKeyInfo[index]) - 1):
                            self.trimKeyRange(value, self.allKeyInfo[index][x], self.allKeyInfo[index][x + 1])
                            # self.filterNode(value)

        for index, node in enumerate(self.nodeList):
            cmds.copyKey(self.tempLocators[index],
                         attribute=['rotateX', 'rotateY', 'rotateZ'],
                         time=(self.firstKeys[index], self.lastKeys[index]))
            if self.newLayer:
                attrs = ['rotateOrder', 'rotateX', 'rotateY', 'rotateZ']

                for at in attrs:
                    cmds.animLayer(str(self.newLayer), edit=True, attribute=node + '.' + at)

                cmds.pasteKey(node,
                              attribute=['rotateX', 'rotateY', 'rotateZ'],
                              animLayer=str(self.newLayer),
                              option='replace',
                              time=(self.firstKeys[index], self.lastKeys[index]))
                cmds.setKeyframe(node,
                                 time=[self.firstKeys[index]],
                                 attribute='rotateOrder',
                                 insert=True,
                                 value=self.originalOrders[index],
                                 animLayer='BaseAnimation')
                cmds.setKeyframe(node,
                                 time=[self.firstKeys[index]],
                                 attribute='rotateOrder',
                                 inTangentType='linear',
                                 outTangentType='stepnext',
                                 value=rotateOrderList.index(self.orderList[index]),
                                 animLayer=str(self.newLayer))
                startKey = self.firstKeys[index] + 1
                endKey = self.lastKeys[index]

                if endKey - startKey > 0:
                    cmds.cutKey(node, attribute='rotateOrder', time=(startKey, endKey))
            else:
                cmds.pasteKey(node,
                              attribute=['rotateX', 'rotateY', 'rotateZ'],
                              option='replace',
                              time=(self.firstKeys[index], self.lastKeys[index]))
                cmds.setKeyframe(node,
                                 time=[self.firstKeys[index], self.lastKeys[index]],
                                 attribute='rotateOrder',
                                 inTangentType='linear',
                                 outTangentType='stepnext',
                                 value=rotateOrderList.index(self.orderList[index]))
                startKey = self.firstKeys[index] + 1
                endKey = self.lastKeys[index] - 1

                if endKey - startKey > 0:
                    cmds.cutKey(node, attribute='rotateOrder', time=(startKey, endKey))

        self.cleanUpLocators()
        cmds.refresh()
        cmds.select(preSel, replace=True)
        cmds.currentTime(cmds.currentTime(query=True))
        if self.newLayer:
            self.selectNewAnimLayer()
        endTime = cmds.timerX() - startTime
        msg = 'Rotate order swapped in %s seconds' % endTime
        info(position="botRight",
             prefix="Bake Complete",
             message=msg, fadeStayTime=3.0, fadeOutTime=4.0)

    def set_curve_tangents(self, curve):
        for key in cmds.keyframe(curve, query=True, tc=True):
            inTangent = cmds.keyTangent(curve, query=True, time=(key, key), inAngle=True)
            outTangent = cmds.keyTangent(curve, query=True, time=(key, key), outAngle=True)
            cmds.keyTangent(curve, edit=True, time=(key, key), inAngle=inTangent[0])
            cmds.keyTangent(curve, edit=True, time=(key, key), outAngle=outTangent[0])

    def getLayerInclusion(self, input, layerToCheck=None):
        if not input:
            return False
        if not isinstance(input, list):
            input = [input]
        inLayer = False
        for obj in input:
            layerConnections = cmds.listConnections(obj, type='animLayer')
            if layerConnections:
                if layerToCheck:
                    if layerToCheck in layerConnections:
                        return True
                return True
        return False

    def getAllAnimCurves(self, input):
        historyNodes = cmds.listHistory(input, pruneDagObjects=True, leaf=False)
        animCurves = cmds.ls(historyNodes, type='animCurve')
        return animCurves

    def hasAnimCurves(self, input):
        animCurves = self.getAllAnimCurves(input)
        if animCurves:
            return True

    def get_all_key_times(self, input):
        historyNodes = cmds.listHistory(input, pruneDagObjects=True, leaf=False)
        animCurves = cmds.ls(historyNodes, type='animCurve')
        all_keys = cmds.keyframe(animCurves, query=True,
                                 timeChange=True)
        if all_keys:
            return sorted(list(set(all_keys)))

    def selectNewAnimLayer(self):
        for layer in cmds.ls(type='animLayer'):
            cmds.animLayer(layer, edit=True, selected=False)
        cmds.animLayer(str(self.newLayer), edit=True, selected=True)
        cmds.animLayer(str(self.newLayer), edit=True, preferred=True)

    def filterNode(self, node):
        cmds.filterCurve(node, filter='euler')

    def trimStartKeys(self, node, start, end):
        cmds.cutKey(node,
                    time=(start - 2, end - 1),
                    option="keys",
                    attribute=('rotate'),
                    clear=True)

    def trimEndKeys(self, node, start, end):
        cmds.cutKey(node,
                    time=(start + 1, end + 2),
                    attribute=('rotate'),
                    option="keys",
                    clear=True)

    def trimKeyRange(self, node, start, end):
        if end - start > 1:
            cmds.cutKey(node,
                        time=(start + 1, end - 1),
                        attribute=('rotate'),
                        option="keys",
                        clear=True)

    def simplifyRange(self, node, start, end):
        cmds.filterCurve(node,
                         filter='simplify',
                         startTime=start,
                         endTime=end,
                         timeTolerance=self.tolerance)

    def cleanUpLocators(self):
        if self.tempConstraints:
            for x in self.tempConstraints:
                if cmds.objExists(x):
                    cmds.delete(x)
        return
        if self.tempLocators:
            for x in self.tempLocators:
                if cmds.objExists(x):
                    cmds.delete(x)


class EulerFilter(object):
    def __init__(self):
        self.objects = cmds.ls(selection=True)
        self.selected = False
        # get the min and max times from our keyframe selection
        if cmds.keyframe(query=True, selected=True):
            self.firstTime = min(min(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
            self.lastTime = min(max(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
            self.selected = True

    def filter(self):
        for obj in self.objects:
            cmds.select(obj, replace=True)
            if cmds.keyframe(query=True, selected=True):
                self.firstTime = min(min(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
                self.lastTime = min(max(cmds.keyframe(query=True, selected=True, timeChange=True)), 99999999)
                self.selected = True
            if self.selected:
                cmds.selectKey(clear=True)
                # copy keys to buffer
                cmds.selectKey(obj, replace=True, time=(self.firstTime, self.lastTime))
                cmds.bufferCurve(animation='keys', overwrite=True)
                # delete surrounding keys
                cmds.cutKey(obj, clear=True, time=(-9999999, self.firstTime - 0.01))
                cmds.cutKey(obj, clear=True,
                            time=(self.lastTime + 0.01, 999999))
                # euler filter
                cmds.filterCurve()
                # copy keys
                cmds.selectKey(obj, replace=True, time=(self.firstTime, self.lastTime))

                cmds.copyKey(obj, time=(self.firstTime, self.lastTime), attribute=['rotateX', 'rotateY', 'rotateZ'])

                # swap buffer to original
                cmds.bufferCurve(animation='keys', overwrite=False, swap=True)

                cmds.bufferCurve(animation='keys', overwrite=False)
                # paste keys back
                cmds.pasteKey(obj, time=(self.firstTime,), attribute=['rotateX', 'rotateY', 'rotateZ'],
                              option='merge')
            else:
                cmds.filterCurve()
        cmds.select(self.objects, replace=True)


def getGimbalColour(input):
    r = lerp(greenBright[0], red[0], input * 0.01) * 255
    g = lerp(greenBright[1], red[1], input * 0.01) * 255
    b = lerp(greenBright[2], red[2], input * 0.01) * 255
    return [int(r), int(g), int(b)]


def getGimbalColourHex(input):
    r = lerp(greenBright[0], red[0], input * 0.01) * 255
    g = lerp(greenBright[1], red[1], input * 0.01) * 255
    b = lerp(greenBright[2], red[2], input * 0.01) * 255

    return '#%02x%02x%02x' % (r, g, b)


def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def lighten_color(colour, factor=0.1):
    return adjust_color_lightness(colour[0], colour[1], colour[2], 1 + factor)


def darken_color(colour, factor=0.1):
    return adjust_color_lightness(colour[0], colour[1], colour[2], 1 - factor)


def hex_to_rgb(hex):
    return [(hex[x:x + 2], 16) for x in [1, 3, 5]]


def rgb_to_hex(colour):
    return "#%02x%02x%02x" % (colour[0], colour[1], colour[2])


def lerp(a, b, t):
    return a * (1 - t) + b * t


ann_blank = ''
ann_defaultRot = 'This is the objects default rotation order value'
ann_currentRot = 'This is the objects current rotation order and gimbal percentage'
ann_currentGimbal = 'The current percentage of gimbal lock in this rotation order'
ann_worldspace = 'This rotation order is good for world space controls (if Y is your up axis'
ann_quickSetOrder = 'Process the current object to this rotation order'
ann_queueSetOrder = 'Add this object to the queue with this rotation order'
ann_setBakeMode = 'Bake the new rotation orders to a set key interval'
ann_setKeepKeysMode = 'Set the new rotation order keeping the current key times\nOptionally increase the fidelity of the inbetweens'
ann_bakeTolerance = 'Drag the slider to adjust how closely the re-order will match your original keys\nThe more to the left, the more accurate the inbetweens.\nFar right will retain only your current keys.\nHit the button to set the slider to maximum.'
ann_bakeSample = 'Drag the slider to adjust the bake sample frame step'
ann_queueMode = '-- Mode Selector --\n' \
                'Quick Mode:\n' \
                '   This will instantly process your currently\n' \
                '   selected object to the new rotation order\n' \
                '   when you select one of the axis order buttons\n' \
                '   below.\n' \
                'Queue Mode:\n' \
                '   When you choose an axis order, the currently\n' \
                '   selected objects(s) will be added to the queue.\n' \
                '   Keep adding objects until you are ready, then\n' \
                '   click "Process Queue" to perform your re-ordering'
ann_currentObj = 'Current Object'
ann_noObj = 'None - please select an object'
ann_toolTitle = 'tbGimbalTools'


class Message(object):
    def __init__(self):
        self.positions = ["topLeft",
                          "topCenter",
                          "topRight",
                          "midLeft",
                          "midCenter",
                          "midCenterTop",
                          "midCenterBot",
                          "midRight",
                          "botLeft",
                          "botCenter",
                          "botRight"]
        self.optionVar_name = "inViewMessageEnable"
        self.inView_opt = get_option_var("inViewMessageEnable")
        self.colours = {'green': 'style=\"color:#33CC33;\"',
                        'red': 'style=\"color:#FF0000;\"',
                        'yellow': 'style=\"color:#FFFF00;\"',
                        }

    # this disables the default maya inview messages (which are pointless after a while)
    def disable_messages(self):
        cmds.optionVar(intValue=(Message().optionVar_name, 0))
        pass

    def enable_messages(self):
        cmds.optionVar(intValue=(Message().optionVar_name, 1))
        pass


# yellow info prefix highlighting
class info(Message):
    def __init__(self, position="midCenter", prefix="", message="", fadeStayTime=2.0, fadeOutTime=4.0, fade=True):
        prefix = '<hl>%s</hl>' % prefix
        Message().enable_messages()
        cmds.inViewMessage(amg='%s :: %s' % (prefix, message),
                           pos=position,
                           # fadeStayTime=fadeStayTime,
                           fadeOutTime=fadeOutTime,
                           fade=fade)
        Message().disable_messages()


# prefix will be highlighted in red!
class error(Message):
    def __init__(self, position="midCenter", prefix="", message="", fadeStayTime=0.5, fadeOutTime=4.0, fade=True):
        prefix = '<span %s>%s</span>' % (Message().colours['red'], prefix)
        Message().enable_messages()
        cmds.inViewMessage(amg='%s :: %s' % (prefix, message),
                           pos=position,
                           fadeOutTime=fadeOutTime,
                           dragKill=True,
                           fade=fade)
        Message().disable_messages()


class queueObjectWidget(QWidget):
    def __init__(self, obj, order, parent):
        super(queueObjectWidget, self).__init__()
        self.setObjectName(obj)

        self.parent = parent
        self.obj = obj
        self.order = order
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.deleteButton = MiniButton(toolTip='Remove')
        self.deleteButton.clicked.connect(self.deletePressed)
        self.nameLabel = QLabel(str(self.obj))
        self.orderLabel = QLabel(self.order)
        self.layout.addWidget(self.nameLabel)
        self.layout.addWidget(self.orderLabel)
        self.layout.addWidget(self.deleteButton)
        self.setLayout(self.layout)

    def deletePressed(self, *args):
        self.parent.removeFromQueue(self.obj)

    def updateOrder(self, order):
        self.order = order
        self.orderLabel.setText(order)


class GimbalUI_pyside(BaseDialog):
    assignSignal = Signal(str, str, str, list)
    conditionSignal = Signal(str, str, str, list)
    instance = None

    timeChangeScriptJob = -1
    dragReleaseScriptJob = -1
    selectionChangedScriptJob = -1
    shiftKeyPressed = False

    def __init__(self, parent=getMainWindow(), title='title', text='test',
                 altText='alt text'):
        super(GimbalUI_pyside, self).__init__(parent=parent, title=title, text=text, showHelpButton=True)
        self.infoText.setText('Current Object ::')
        self.node = None
        self.bakeClass = None

        ''' Option Vars '''
        self.keyModeOption = 'tbGimbalKeyMode'
        self.keyModeOptions = ['Bake', 'Keep Keys']
        self.keyMode = get_option_var(self.keyModeOption, self.keyModeOptions[0])
        set_option_var(self.keyModeOption, self.keyMode)

        self.bakeSampleOption = 'tbGimbalSample'
        self.bakeSample = get_option_var(self.bakeSampleOption, 1)
        set_option_var(self.bakeSampleOption, self.bakeSample)

        self.toleranceOption = 'tbGimbalTolerance'
        self.tolerance = get_option_var(self.toleranceOption, 1)
        set_option_var(self.toleranceOption, self.tolerance)

        self.layerOptions = ['New', 'Current']
        self.layerOptionVar = 'tbGimbalLayerBakeMode'
        self.layerBakeMode = get_option_var(self.layerOptionVar, self.layerOptions[0])

        set_option_var(self.layerOptionVar, self.layerBakeMode)

        self.quickModeOption = 'tbGimbalQueue'
        self.quickMode = get_option_var(self.quickModeOption, 0)
        set_option_var(self.quickModeOption, self.quickMode)

        self.queueWidgets = []
        self.collapsedHeight = 124
        self.fullHeight = 200
        self.fullWidth = 300
        self.bakeHeight = 22
        self.objectQueue = {}
        self.tempLocators = []
        self.tempConstraints = []
        self.allKeyInfo = []
        self.firstKeys = []
        self.lastKeys = []
        ''' Scriptjobs '''
        # self.cleanupScriptJob = cmds.scriptJob(uiDeleted=('GimbalTools', self.removeScriptJob))
        self.inputList = None
        self.fromEditor = None
        self.margin = 4

        self.quickLabel = 'Quick Mode'
        self.queueLabel = 'Queue Mode'

        self.gimbalInfo = {}
        self.rotateOrderButtonWidth = 64

        self.queueWidgets = dict()

        self.result = str()
        self.setFixedSize(self.fullWidth * dpiScale(), 160 * dpiScale())
        self.layout.setSpacing(0)
        self.originalLabels = list()
        self.gimbalLabels = list()
        self.gimbalButtons = list()

        self.createWidgets()
        self.attachUI()

        self.setupUIConnections()
        self.updateQueueModeButton()
        self.setInitialState()

    # def keyReleaseEvent(self, event):
    #     print ('base dialog keyReleaseEvent')
    #     if event.key() == Qt.Key_Shift:
    #         self.shiftKeyPressed = False
    #     return super(GimbalUI_pyside, self).keyReleaseEvent(event)
    #
    #
    # def keyPressEvent(self, event):
    #     print ('base dialog keyPressEvent', event)
    #     if event.key() == Qt.Key_Shift:
    #         self.shiftKeyPressed = True
    #     return super(GimbalUI_pyside, self).keyPressEvent(event)

    def show(self):
        self.createScriptJob()
        sel = cmds.ls(sl=True)
        if sel:
            self.node = cmds.ls(sl=True)[-1]
            self.update()
        super(GimbalUI_pyside, self).show()

    def getAllAnimCurves(self, inputData):
        historyNodes = cmds.listHistory(inputData, pruneDagObjects=True, leaf=False)
        animCurves = cmds.ls(historyNodes, type='animCurve')
        return animCurves

    def hasAnimCurves(self, inputData):
        animCurves = self.getAllAnimCurves(inputData)
        if animCurves:
            return True

    def createScriptJob(self):
        self.removeScriptJob()
        self.timeChangeScriptJob = cmds.scriptJob(event=["timeChanged", self.update], protected=False)
        self.dragReleaseScriptJob = cmds.scriptJob(event=["DragRelease", self.update], protected=False)
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.update], protected=False)

    def close(self):
        self.removeScriptJob()
        super(GimbalUI_pyside, self).close()

    def createWidgets(self):
        self.setObjectName('tbGimbalToolLayout')

        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 18px;"
                                     "}"
                                     )

        self.objectLabel = QLabel()
        self.buttonLayout = QGridLayout()
        self.buttonLayout.setSpacing(0)
        self.objectLabelLayout = QHBoxLayout()
        self.objectLabelLayout.setSpacing(0)
        for index, order in enumerate(rotateOrderList):
            orderLabel = QLabel(order)
            orderLabel.setAlignment(Qt.AlignCenter)
            gimbalValueLabel = QLabel('%')
            gimbalValueLabel.setAlignment(Qt.AlignCenter)
            gimbalSetButton = QPushButton(order)
            gimbalSetButton.setFixedHeight(22 * dpiScale())
            gimbalSetButton.setStyleSheet("font-weight: bold; font-size: 18px;")
            self.originalLabels.append(orderLabel)
            self.gimbalLabels.append(gimbalValueLabel)
            self.gimbalButtons.append(gimbalSetButton)

        self.bakeKeysButton = QPushButton()

        self.denseButton = QPushButton(' Bake Keys <<')
        self.keysButton = QPushButton('>> Keep Keys')

        self.toolOptionStack = QStackedWidget()
        self.toolOptionStack.setFixedHeight(30 * dpiScale())
        self.keysWidget = QWidget()
        self.keysLayout = QHBoxLayout()
        self.keysLayout.setSpacing(0)
        self.keysLayout.setContentsMargins(2, 2, 2, 2)

        self.keysWidget.setLayout(self.keysLayout)

        self.bakeWidget = QWidget()
        self.bakeLayout = QHBoxLayout()
        self.bakeLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.bakeLayout.setContentsMargins(2, 2, 2, 2)
        self.bakeLayout.setSpacing(0)
        self.bakeWidget.setLayout(self.bakeLayout)

        self.bakeSampleLabel = QLabel('Bake Sample ')
        self.bakeSampleLabel.setToolTip(ann_bakeSample)
        self.bakeSample = 1

        self.bakeSampleSlider = QSlider(Qt.Horizontal)
        self.bakeSampleSlider.setMinimum(1)
        self.bakeSampleSlider.setMaximum(10)
        self.bakeSampleSlider.setValue(self.bakeSample)
        self.bakeSampleSlider.setToolTip(ann_bakeSample)
        self.bakeSampleSlider.valueChanged.connect(self.updateBakeSampleInt)
        # changeCommand=self.updateBakeSampleInt,
        # #dragCommand=self.updateBakeSampleInt)
        self.bakeSampleIntField = QSpinBox()
        self.bakeSampleIntField.setFixedWidth(40 * dpiScale())
        self.bakeSampleIntField.setMinimum(1)
        self.bakeSampleIntField.setMaximum(10)
        self.bakeSampleIntField.setValue(self.bakeSample)
        self.bakeSampleIntField.valueChanged.connect(self.updateBakeSampleSlider)

        self.toleranceLabel = QLabel('Reduce Keys <<')
        self.toleranceRightLabel = QLabel('>>')

        self.toleranceLabel.setToolTip(ann_bakeTolerance)
        self.keySample = 1
        self.toleranceSlider = QSlider(Qt.Horizontal)
        self.toleranceSlider.setMinimum(0)
        self.toleranceSlider.setMaximum(100)
        self.toleranceSlider.setSingleStep(1)
        self.toleranceSlider.setValue(self.bakeSample)
        self.toleranceSlider.setToolTip(ann_bakeSample)
        self.toleranceSlider.valueChanged.connect(self.toleranceSliderDragged)

        self.keepKeysButton = QPushButton('Keep current')
        self.keepKeysButton.setFixedSize(80 * dpiScale(), 22 * dpiScale())
        self.keepKeysButton.clicked.connect(self.setKeepCurrent)

        self.modeSwapLayout = QHBoxLayout()
        # changeCommand=self.updateBakeSampleSlider,
        self.modeLayout = QHBoxLayout()
        self.modeLayout.setContentsMargins(2, 2, 2, 2)
        self.modeLayout.setAlignment(Qt.AlignTop)
        self.keyModeLabel = QLabel('Key Mode')
        self.keyModeCombo = QComboBox()
        self.keyModeCombo.setFixedWidth(88 * dpiScale())
        self.keyModeCombo.addItem(self.keyModeOptions[0])
        self.keyModeCombo.addItem(self.keyModeOptions[1])

        self.bakeModeLabel = QLabel('Layer Mode')
        self.layerModeCombo = QComboBox()
        self.layerModeCombo.addItem(self.layerOptions[0])
        self.layerModeCombo.addItem(self.layerOptions[1])
        self.keyModeCombo.currentIndexChanged.connect(self.bakeModeChanged)
        self.layerModeCombo.currentIndexChanged.connect(self.layerModeChanged)

        self.queModeLabel = QLabel('Object Mode')
        self.queueModeButton = AnimatedCheckBox(text='Quick',
                                                offText='Multi',
                                                checked=self.quickMode,
                                                width=48 * dpiScale(),
                                                height=11 * dpiScale())
        self.queueModeButton.clicked.connect(self.toggleQueueMode)

        self.queueFrame = QFrame()

        self.queueScrollArea = QScrollArea()
        # self.queueScrollArea.setFixedHeight(116 * dpiScale())
        self.queueScrollArea.setWidget(self.queueFrame)
        self.queueScrollArea.setWidgetResizable(True)
        self.queueScrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.queueScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.processButton = QPushButton('Process Queue')
        self.processButton.setFixedHeight(24 * dpiScale())
        self.queueFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.queueLayout = QVBoxLayout()
        self.queueLayout.setSpacing(0)
        self.queueLayout.setAlignment(Qt.AlignTop)
        self.queueLayout.setContentsMargins(2, 2, 2, 2)

    def processQueue(self, *args):
        self.removeMissingObjectsFromQueue()
        self.bakeSample = self.bakeSampleSlider.value()
        bakeOrderClass = BakeOrderClass(nodeList=list(self.objectQueue.keys()),
                                        orderList=list(self.objectQueue.values()),
                                        keepCurrentKeys=self.keyMode == self.keyModeOptions[0],
                                        bakeSample=self.bakeSample,
                                        tolerance=self.tolerance * 0.01,
                                        bakeToNewLayer=self.layerBakeMode == self.layerOptions[0])
        bakeOrderClass.bakeOrder()
        self.clearQueueWidgets()

    def updateProcessButtonColour(self):
        if self.quickMode:
            cmds.button(self.processButton, edit=True, backgroundColor=defaultGrey)
        else:
            if self.objectQueue.keys():
                cmds.button(self.processButton, edit=True, backgroundColor=green)
            else:
                cmds.button(self.processButton, edit=True, backgroundColor=defaultGrey)

    def toggleQueueMode(self, *args):
        self.quickMode = not self.quickMode
        self.updateQueueModeButton()
        cmds.optionVar(intValue=(self.quickModeOption, self.quickMode))

    def updateQueueModeButton(self, *args):
        if self.quickMode:
            # self.queueModeButton.setText(self.quickLabel)
            # self.queueModeButton.setStyleSheet(defaultBackgroundSS)
            self.setFixedHeight(158.0 * dpiScale())
            # 172.0 * dpiScale()
            self.queueScrollArea.setVisible(False)
            self.processButton.setVisible(False)
        else:
            # self.queueModeButton.setText(self.queueLabel)
            # self.queueModeButton.setStyleSheet(mainStyleSheet)
            self.setFixedHeight(340 * dpiScale())
            self.queueScrollArea.setVisible(True)
            self.processButton.setVisible(True)

        for index, order in enumerate(rotateOrderList):
            self.gimbalButtons[index].setToolTip({True: ann_quickSetOrder, False: ann_queueSetOrder}[self.quickMode])

    def orderButtonPressed(self, data):
        if self.quickMode:
            if not self.node:
                msg = 'No object selected to process'
                error(position="botRight",
                      prefix="Error",
                      message=msg, fadeStayTime=3.0, fadeOutTime=4.0)
                return cmds.warning('No object selected to process')
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                # shift modifier will just swap this frame
                self.staticSwapOrder(self.node, data)
            elif self.hasAnimCurves(self.node):
                self.bakeSample = self.bakeSampleSlider.value()
                bakeOrderClass = BakeOrderClass(nodeList=[self.node],
                                                orderList=[data],
                                                keepCurrentKeys=self.keyMode != self.keyModeOptions[0],
                                                bakeSample=self.bakeSample,
                                                tolerance=self.tolerance * 0.01,
                                                bakeToNewLayer=self.layerBakeMode == self.layerOptions[
                                                    0])

                bakeOrderClass.bakeOrder()
            else:
                self.staticSwapOrder(self.node, data)
        else:
            for s in cmds.ls(sl=True, type='transform'):
                self.objectQueue[s] = data
        self.updateQueueObjects()

    def clearQueueWidgets(self):
        widgetsToRemove = list()
        for widget in self.queueWidgets.keys():
            widgetsToRemove.append(widget)
        for widget in widgetsToRemove:
            self.removeFromQueue(widget)

    def updateQueueObjects(self):
        if self.objectQueue:
            for key, value in self.objectQueue.items():
                if key in self.queueWidgets:
                    self.queueWidgets[key].updateOrder(value)
                else:
                    self.queueWidgets[key] = queueObjectWidget(key, value, self)
                    self.queueLayout.addWidget(self.queueWidgets[key])

    def removeMissingObjectsFromQueue(self):
        if self.objectQueue:
            for key, value in self.objectQueue.items():
                # remove non existant objects from the queue
                if not cmds.objExists(key):
                    self.objectQueue.pop(key)

    def removeFromQueue(self, obj):
        self.objectQueue.pop(obj)
        self.queueLayout.removeWidget(self.queueWidgets[obj])
        self.queueWidgets[obj].deleteLater()
        self.queueWidgets.pop(obj)

    def updateObjectLabel(self):
        if self.node is not None:
            self.objectLabel.setText(self.node)
        else:
            self.objectLabel.setText(ann_noObj)

    def updateGimbalLabels(self, reset=False):
        if reset:
            for index, order in enumerate(rotateOrderList):
                gimbalVal = self.gimbalInfo[index]
                self.originalLabels[index].setText('')
                self.gimbalLabels[index].setText('')
                self.gimbalLabels[index].setStyleSheet(mainStyleSheet)
                self.gimbalButtons[index].setStyleSheet(mainStyleSheet)
                self.gimbalButtons[index].setStyleSheet("font-weight: bold; font-size: 18px;")
            return
        rotateOrder = cmds.getAttr(self.node + '.rotateOrder', asString=True)
        defaultRotateOrder, defaultRotateOrderInt = self.get_original_rotation_order(self.node)
        for index, order in enumerate(rotateOrderList):
            gimbalVal = self.gimbalInfo[index]
            self.originalLabels[index].setText({True: 'Default', False: ''}[order == defaultRotateOrder])
            self.originalLabels[index].setStyleSheet(
                {True: defaultBackgroundSS, False: mainStyleSheet}[order == defaultRotateOrder])
            self.gimbalLabels[index].setText("{:d}%".format(math.trunc(gimbalVal)))
            if order == rotateOrder:
                self.gimbalLabels[index].setStyleSheet(defaultBackgroundSS)
            else:
                self.gimbalLabels[index].setStyleSheet(mainStyleSheet)

            colour = getGimbalColour(gimbalVal)
            colour2 = rgb_to_hex(darken_color(colour, factor=0.1))
            colour3 = rgb_to_hex(darken_color(colour, factor=0.2))
            colour4 = rgb_to_hex(darken_color(colour, factor=0.4))
            colour5 = rgb_to_hex(darken_color(colour, factor=0.8))
            colour = rgb_to_hex(colour)

            self.gimbalButtons[index].setStyleSheet(
                tintedButton(str(colour), str(colour2), str(colour3), str(colour3), str(colour5)))

            # {True: ann_quickSetOrder, False: ann_queueSetOrder}[self.quickMode]

    def updateGimbalInfo(self):
        if self.node is not None:
            self.gimbalInfo = self.get_all_gimbal_values(self.node)

    def update(self):
        '''

        :return:
        '''
        if GimbalTool().updateDisabled:
            return
        sel = cmds.ls(sl=True, type='transform')
        if sel:
            self.node = sel[-1]
        else:
            self.node = None
        if self.node:
            if not cmds.objExists(self.node):
                self.node = None
        self.updateObjectLabel()
        self.updateGimbalInfo()
        self.updateGimbalLabels(reset=self.node == None)

    def removeScriptJob(self):
        self.cleanUpLocators()
        if self.timeChangeScriptJob != -1:
            cmds.scriptJob(kill=self.timeChangeScriptJob, force=True)
            self.timeChangeScriptJob = -1
        if self.dragReleaseScriptJob != -1:
            cmds.scriptJob(kill=self.dragReleaseScriptJob, force=True)
            self.dragReleaseScriptJob = -1
        if self.selectionChangedScriptJob != -1:
            cmds.scriptJob(kill=self.selectionChangedScriptJob, force=True)
            self.selectionChangedScriptJob = -1

    def cleanUpLocators(self):
        if self.bakeClass:
            self.bakeClass.cleanUpLocators()

    def setTolerance(self, value):
        cmds.optionVar(floatValue=(self.toleranceOption, value))

    def swapRotateOrderFrame(self, order):
        cmds.xform(self.node, preserve=True, rotateOrder=order)
        self.update()

    def staticSwapOrder(self, node, order):
        isHighlighted = GimbalTool.funcs.isTimelineHighlighted()
        timeStart = int(cmds.currentTime(query=True))
        timeEnd = int(cmds.currentTime(query=True))
        if isHighlighted:
            timeStart, timeEnd = GimbalTool.funcs.getTimelineHighlightedRange()
        timeStart = int(timeStart)
        timeEnd = int(timeEnd)
        preTime = cmds.currentTime(query=True)
        for i in range(timeEnd - timeStart, -1, -1):
            cmds.currentTime(i + timeStart)
            self.swap_rotate_order(node, order)
        cmds.currentTime(preTime)
        self.updateGimbalLabels()

    def swap_rotate_order(self, input, rotateOrder):
        if isinstance(rotateOrder, int):
            rotateOrder = self.get_rotate_order_list(input)[rotateOrder]
        self.get_original_rotation_order(input)
        cmds.xform(input,
                   preserve=True,
                   rotateOrder=rotateOrder
                   )

    def get_rotate_order_list(self, input):
        rotateOrders = cmds.attributeQuery('rotateOrder', node=input, listEnum=True)
        rotateOrders = rotateOrders[0].split(':')
        return rotateOrders

    def get_original_rotation_order(self, input):
        if not cmds.attributeQuery(defaultRoAttribute, node=input, exists=True):
            self.tag_original_rotation_order(input)
        stringValue = cmds.getAttr(input + '.' + defaultRoAttribute, asString=True)
        rotateOrders = self.get_rotate_order_list(input)
        intValue = rotateOrders.index(cmds.getAttr(input + '.' + defaultRoAttribute))
        return stringValue, intValue

    def tag_original_rotation_order(self, input):
        if not cmds.attributeQuery(defaultRoAttribute, node=input, exists=True):
            cmds.addAttr(input, ln=defaultRoAttribute, dt='string')
        currentRO = cmds.getAttr(input + '.rotateOrder', asString=True)
        cmds.setAttr(input + '.' + defaultRoAttribute, currentRO, type='string')

    def setToBakeMode(self, *args):
        self.keyMode = False
        cmds.optionVar(intValue=(self.keyModeOption, self.keyMode))
        self.showBakeSampleUI()
        self.hideKeyReduceUI()

    def setToKeyMode(self, *args):
        self.keyMode = True
        cmds.optionVar(intValue=(self.keyModeOption, self.keyMode))
        self.hideBakeSampleUI()
        self.showKeyReduceUI()

    def get_current_gimbal_amount(self, rotationValue):
        # get the middle axis of our rotation order
        degree = rotationValue * (180 / math.pi)
        return 100 * (abs(((degree + 90) % 180) - 90) / 90)

    def get_all_gimbal_values(self, input):
        returnDict = {}
        node = om2.MSelectionList().add(str(input)).getDependNode(0)
        nodeRotation = om2.MFnTransform(node).rotation(asQuaternion=False)
        nodeRotationOrder = om2.MFnTransform(node).rotationOrder()
        for rotationOrder in rotateOrderDict.keys():
            newRotation = nodeRotation.reorder(rotationOrder)
            returnDict[rotationOrder] = self.get_current_gimbal_amount(
                newRotation[rotateOrderDict[rotationOrder]['middleAxis']])
        return returnDict

    def setKeepCurrent(self, *args):
        self.toleranceSlider.setValue(100)
        self.keepKeysButton.setStyleSheet(
            """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #00BF01, stop: 0.1 #00A601, stop: 0.5 #008C01, stop: 0.9 #007301, stop: 1 #005901);""")

    def toleranceSliderDragged(self, value):
        '''

        :param value:
        :return:
        '''
        self.tolerance = value
        if value >= large:
            self.keepKeysButton.setStyleSheet(
                """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #00BF01, stop: 0.1 #00A601, stop: 0.5 #008C01, stop: 0.9 #007301, stop: 1 #005901);""")

        else:
            self.setNotKeepCurrent()
        '''
        if value <= small:
            cmds.button(self.denseButton, edit=True, backgroundColor=green, enableBackground=True)
            self.showBakeSampleUI()
        else:
            cmds.button(self.denseButton, edit=True, backgroundColor=defaultGrey, enableBackground=False)
            self.hideBakeSampleUI()

        '''

    def setNotKeepCurrent(self):
        self.keepKeysButton.setStyleSheet(getqss.getStyleSheet())

    def setInitialState(self):
        if self.layerBakeMode == 'Current':
            self.layerModeCombo.setCurrentIndex(1)
        else:
            self.layerModeCombo.setCurrentIndex(0)
        self.keyModeCombo.setCurrentIndex(self.keyModeOptions.index(self.keyMode))
        self.bakeModeChanged(None)
        # self.quickMode
        # self.keyMode

    def bakeModeChanged(self, b):
        text = self.keyModeCombo.currentText()
        self.keyMode = text
        cmds.optionVar(stringValue=(self.keyModeOption, self.keyMode))
        if text == 'Bake':
            self.toolOptionStack.setCurrentIndex(1)
        else:
            self.toolOptionStack.setCurrentIndex(0)

    def layerModeChanged(self, b):
        self.layerBakeMode = self.layerModeCombo.currentText()
        cmds.optionVar(stringValue=(self.layerOptionVar, self.layerBakeMode))

    def updateBakeSampleSlider(self, data):
        self.bakeSampleSlider.blockSignals(True)
        self.bakeSampleSlider.setValue(data)
        self.bakeSampleSlider.blockSignals(False)

    def updateBakeSampleInt(self, data):
        self.bakeSampleIntField.blockSignals(True)
        self.bakeSampleIntField.setValue(data)
        self.bakeSampleIntField.blockSignals(False)
        self.bakeSample = data

    def setupUIConnections(self):
        self.keysButton.clicked.connect(self.setToKeyMode)
        self.denseButton.clicked.connect(self.setToBakeMode)
        self.processButton.clicked.connect(self.processQueue)

        for index, order in enumerate(rotateOrderList):
            self.gimbalButtons[index].clicked.connect(create_callback(self.orderButtonPressed, order))

    def attachUI(self):
        for index, order in enumerate(rotateOrderList):
            self.buttonLayout.addWidget(self.originalLabels[index], 0, index)
            self.buttonLayout.addWidget(self.gimbalLabels[index], 1, index)
            self.buttonLayout.addWidget(self.gimbalButtons[index], 2, index)

        self.layout.setContentsMargins(2 * dpiScale(),
                                       6 * dpiScale(),
                                       2 * dpiScale(),
                                       2 * dpiScale())
        self.layout.addLayout(self.objectLabelLayout)
        self.objectLabelLayout.addWidget(self.infoText)
        self.objectLabelLayout.addWidget(self.objectLabel)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addLayout(self.modeLayout)
        self.layout.addWidget(self.toolOptionStack)
        self.layout.setAlignment(Qt.AlignTop)

        self.layout.addLayout(self.modeSwapLayout)
        self.modeSwapLayout.addWidget(self.queModeLabel)
        self.modeSwapLayout.addWidget(self.queueModeButton)

        self.modeLayout.addWidget(self.keyModeLabel)
        self.modeLayout.addWidget(self.keyModeCombo)
        self.modeLayout.addWidget(self.bakeModeLabel)
        self.modeLayout.addWidget(self.layerModeCombo)

        self.toolOptionStack.addWidget(self.keysWidget)
        self.toolOptionStack.addWidget(self.bakeWidget)

        # self.toolOptionStack.setFixedHeight(100)
        # self.toolOptionStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolOptionStack.setCurrentIndex(1)

        self.bakeLayout.addWidget(self.bakeSampleLabel)
        self.bakeLayout.addWidget(self.bakeSampleSlider)
        self.bakeLayout.addWidget(self.bakeSampleIntField)

        self.keysLayout.addWidget(self.toleranceLabel)
        self.keysLayout.addWidget(self.toleranceSlider)
        self.keysLayout.addWidget(self.toleranceRightLabel)
        self.keysLayout.addWidget(self.keepKeysButton)

        self.bakeSampleSlider.setStyleSheet(getqss.getStyleSheet())
        self.bakeSampleSlider.setStyleSheet(ss2)
        self.toleranceSlider.setStyleSheet(getqss.getStyleSheet())
        self.toleranceSlider.setStyleSheet(ss2)

        self.queueScrollArea.setVisible(False)
        self.processButton.setVisible(False)
        self.queueFrame.setLayout(self.queueLayout)
        self.layout.addWidget(self.queueScrollArea)
        self.layout.addWidget(self.processButton)


ss2 = """
QSlider::groove:horizontal {
border: 2px solid #bbb;
background: transparent;
height: 12;
border-radius: 8px;
}

QSlider::sub-page:horizontal {
background: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);

border: 1px solid #2d2d2d;
height: 8;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::add-page:horizontal {
background: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);
border: 1px solid #2d2d2d;
height: 8px;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::handle:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
border: 2px solid #444;
width: 10px; 
height: 10px; 
line-height: 10px; 
margin-top: -5px; 
margin-bottom: -5px; 
border-radius: 5px; 

}

QSlider::handle:horizontal:hover {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
border: 2px solid #777;
}

QSlider::sub-page:horizontal:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:horizontal:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:horizontal:disabled {
background: #eee;
border: 1px solid #aaa;
border-radius: 4px;
"""

buttonSS = """
QPushButton {
color: #333;
border: 2px solid #555;
border-radius: 8px;
border-style: outset;
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #888
);
padding: 5px;
}

QPushButton:hover {
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #bbb
);
}
"""
