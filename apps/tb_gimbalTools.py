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
    return """background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 {colourA}, stop: 0.1 {colourB}, stop: 0.5 {colourC}, stop: 0.9 {colourD}, stop: 1 {colourE});""".format(
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
            # print  (func.__name__, 'evaluation time:: ', (t2 - t1))
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

        self.layout.addWidget(tempControlHeader)
        self.layout.addWidget(tempControlInfo)
        self.layout.addWidget(quickBakeKeyOptionWidget)
        self.layout.addWidget(quickBakeLayerOptionWidget)

        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        # ui = self.gimbalUI(parentCLS=self)
        # ui.showUI()

        if not GimbalUI_pyside.instance:
            GimbalUI_pyside.instance = GimbalUI_pyside(parentCLS=self,
                                                       title='%s  v%s' % (ann_toolTitle, self.version),
                                                       text='test')
        GimbalUI_pyside.instance.show()
        GimbalUI_pyside.instance.raise_()
        # GimbalUI_pyside.resize(GimbalUI_pyside.sizeHint())

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='Rotation Order Swap', image='tbGimbalUI.png', command='gimbalToolUI',
                      sourceType='mel',
                      parent=parentMenu)

    def build_MM(self):
        selection = cmds.ls(sl=True)
        positions = ["NW", "N", "NE", "SE", "S", "SW"]
        iconDict = {0: 'tbGimbalGreen.png',
                    30: 'tbGimbalOrange.png',
                    60: 'tbGimbalRed.png'}
        bakeClass = BakeOrderClass(self)

        quickBake = get_option_var(tbGimbalQuickBakeOptionVar, True)
        quickBakeNewLayer = get_option_var(tbGimbalQuickBakeNewLayerOptionVar, True)

        cmds.menuItem(label='{:^24s}'.format('- Swap rotation order -'),
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )

        if selection:
            if isinstance(selection, list):
                selection = selection[-1]

            tbGimbalToolCls = GimbalTool()
            defaultRotateOrder, defaultRotateOrderInt = bakeClass.get_original_rotation_order(selection)
            gimbalValues = tbGimbalToolCls.get_all_gimbal_values(selection)
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
                elif index == cmds.getAttr(selection + '.rotateOrder'):
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
                              command=create_callback(tbGimbalToolCls.quickBake, value, quickBakeNewLayer,
                                                      not quickBake)
                              )
        else:  # no selection
            cmds.menuItem(label='{:^24s}'.format('No object selected'),
                          enable=False,
                          )

        cmds.menuItem(label='Divider',
                      divider=True,
                      enable=False,
                      )

        cmds.menuItem(label='Bake Keys',
                      checkBox=quickBake,
                      enable=True,
                      command=create_callback(cmds.optionVar, intValue=(tbGimbalQuickBakeOptionVar, not quickBake))
                      )
        cmds.menuItem(label='Bake to new layer',
                      checkBox=quickBakeNewLayer,
                      command=create_callback(cmds.optionVar,
                                              intValue=(tbGimbalQuickBakeNewLayerOptionVar, not quickBakeNewLayer))
                      )
        cmds.menuItem(label='Open UI',
                      image='tbGimbalUI.png',
                      enable=True,
                      sourceType="mel",
                      command="gimbalToolUI")



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

    class gimbalUI(object):
        def __init__(self, parentCLS=None):
            if cmds.window('GimbalTools', query=True, exists=True):
                cmds.deleteUI('GimbalTools')
            self.window = cmds.window('GimbalTools', title='%s  v%s' % (ann_toolTitle, parentCLS.version), width=396,
                                      height=234)
            self.parentCLS = parentCLS
            self.node = None
            self.bakeClass = None
            self.queueWidgets = []
            self.collapsedHeight = 124
            self.fullHeight = 200
            self.bakeHeight = 22
            self.objectQueue = {}
            self.tempLocators = []
            self.tempConstraints = []
            self.allKeyInfo = []
            self.firstKeys = []
            self.lastKeys = []
            ''' Scriptjobs '''
            self.timeChangeScriptJob = None
            self.DragReleaseScriptJob = None
            self.cleanupScriptJob = cmds.scriptJob(uiDeleted=('GimbalTools', self.removeScriptJob))
            self.inputList = None
            self.fromEditor = None
            self.margin = 4

            ''' Option Vars '''
            self.keyModeOption = 'gimbalMode'
            self.keyMode = get_option_var(self.keyModeOption, 1)

            self.bakeSampleOption = 'gimbalSample'
            self.bakeSample = get_option_var(self.bakeSampleOption, 1)
            cmds.optionVar(intValue=(self.bakeSampleOption, self.bakeSample))

            self.toleranceOption = 'gimbalTolerance'
            self.tolerance = get_option_var(self.toleranceOption, 1)
            cmds.optionVar(floatValue=(self.toleranceOption, self.tolerance))

            self.quickLabel = 'Quick Mode'
            self.queueLabel = 'Queue Mode'
            self.quickModeOption = 'gimbalQueue'
            self.quickMode = get_option_var(self.quickModeOption, 0)
            cmds.optionVar(intValue=(self.quickModeOption, self.quickMode))
            self.processLabel = 'Process Queue'
            self.gimbalInfo = {}
            self.rotateOrderButtonWidth = 64
            self.mainLayout = cmds.formLayout()
            self.queueModeButtonLayout = cmds.rowLayout('modeButtonLayout',
                                                        numberOfColumns=1,
                                                        adjustableColumn=1)
            self.queueModeButton = cmds.button(width=2 * self.rotateOrderButtonWidth, label=self.quickLabel,
                                               annotation=ann_queueMode,
                                               command=self.toggleQueueMode)
            cmds.setParent(self.mainLayout)
            self.outliner = cmds.outlinerEditor(allowMultiSelection=False)
            self.subLayout = cmds.columnLayout('subLayout',
                                               columnAlign="center",
                                               columnAttach=("both", 0),
                                               adjustableColumn=True,
                                               parent=self.mainLayout)
            cmds.setParent(self.subLayout)

            cmds.setParent(self.subLayout)
            self.objectLabel = cmds.text(label='::', parent=self.subLayout)
            self.gimbalLabels = []
            self.gimbalButtons = []
            self.originalLabels = []
            self.defaultOrderLayout = cmds.rowLayout(numberOfColumns=6, columnWidth6=(self.rotateOrderButtonWidth,
                                                                                      self.rotateOrderButtonWidth,
                                                                                      self.rotateOrderButtonWidth,
                                                                                      self.rotateOrderButtonWidth,
                                                                                      self.rotateOrderButtonWidth,
                                                                                      self.rotateOrderButtonWidth
                                                                                      ))
            cmds.setParent(self.subLayout)
            self.currentGimbalLayout = cmds.rowLayout(numberOfColumns=6,
                                                      columnWidth6=(self.rotateOrderButtonWidth,
                                                                    self.rotateOrderButtonWidth,
                                                                    self.rotateOrderButtonWidth,
                                                                    self.rotateOrderButtonWidth,
                                                                    self.rotateOrderButtonWidth,
                                                                    self.rotateOrderButtonWidth
                                                                    )
                                                      )
            cmds.setParent(self.subLayout)
            self.orderButtonLayout = cmds.rowLayout(numberOfColumns=6,
                                                    columnWidth6=(self.rotateOrderButtonWidth,
                                                                  self.rotateOrderButtonWidth,
                                                                  self.rotateOrderButtonWidth,
                                                                  self.rotateOrderButtonWidth,
                                                                  self.rotateOrderButtonWidth,
                                                                  self.rotateOrderButtonWidth
                                                                  )
                                                    )
            cmds.setParent(self.subLayout)
            for index, order in enumerate(rotateOrderList):
                self.originalLabels.append(cmds.text(label='',
                                                     parent=self.defaultOrderLayout,
                                                     backgroundColor=green,
                                                     width=self.rotateOrderButtonWidth,
                                                     enableBackground=False,
                                                     font='boldLabelFont'))
            for index, order in enumerate(rotateOrderList):
                self.gimbalLabels.append(cmds.text(label='',
                                                   parent=self.currentGimbalLayout,
                                                   width=self.rotateOrderButtonWidth,
                                                   backgroundColor=orange,
                                                   font='boldLabelFont'))

            for index, order in enumerate(rotateOrderList):
                self.gimbalButtons.append(cmds.button(label=order,
                                                      width=self.rotateOrderButtonWidth,
                                                      parent=self.orderButtonLayout,
                                                      command=create_callback(self.orderButtonPressed, order)))

            cmds.setParent(self.subLayout)
            self.toleranceFeedbackLayout = cmds.rowLayout(numberOfColumns=1,
                                                          columnAlign=(1, 'center'),
                                                          adjustableColumn=1)

            cmds.setParent(self.subLayout)
            self.modeLayout = cmds.rowLayout(numberOfColumns=3,
                                             columnWidth3=(
                                                 2.35 * self.rotateOrderButtonWidth, self.rotateOrderButtonWidth,
                                                 2.35 * self.rotateOrderButtonWidth),
                                             adjustableColumn=2,
                                             columnAlign=(2, 'center'))
            self.denseButton = cmds.button(label=' Bake Keys <<',
                                           width=(2.35 * self.rotateOrderButtonWidth) - self.margin,
                                           annotation=ann_setBakeMode,
                                           parent=self.modeLayout,
                                           command=self.setToBakeMode)

            self.modeLabel = cmds.text(label='<< Key Mode >>', align='center')
            self.keysButton = cmds.button(label='>> Keep Keys',
                                          width=(2.35 * self.rotateOrderButtonWidth) - self.margin,
                                          parent=self.modeLayout,
                                          annotation=ann_setKeepKeysMode,
                                          # backgroundColor=green,
                                          # enableBackground=False,
                                          command=self.setToKeyMode)
            cmds.setParent(self.subLayout)

            self.makeBakeSampleUI()  # gives and error

            cmds.setParent(self.subLayout)
            self.queueLayout = cmds.columnLayout(adjustableColumn=1)
            cmds.text(label='- Object Queue -')
            cmds.setParent(self.subLayout)
            self.processButtonLayout = cmds.columnLayout(adjustableColumn=1)
            self.processButton = cmds.button(label=self.processLabel,
                                             height=36,
                                             parent=self.mainLayout,
                                             command=self.processQueue)
            self.attachUI()

            ''' Initialise some labels etc'''
            self.updateObjectLabel()
            self.updateQueueModeButton()
            self.initialiseOptionUI()

        def makeBakeSampleUI(self):
            cmds.setParent(self.subLayout)
            intFieldWidth = 20
            self.tolerancelayout = cmds.rowLayout(numberOfColumns=3, columnWidth3=(
                2 * self.rotateOrderButtonWidth, 2 * self.rotateOrderButtonWidth, 2 * self.rotateOrderButtonWidth),
                                                  adjustableColumn=2)
            cmds.text(label='Inbetween key reduction', annotation=ann_bakeTolerance)
            self.toleranceSlider = cmds.floatSlider(min=0.00, max=1.0, width=2 * self.rotateOrderButtonWidth,
                                                    annotation=ann_bakeTolerance,
                                                    value=self.tolerance,
                                                    step=0.01,
                                                    )
            self.keepKeysButton = cmds.button(label='Keep current', command=self.setKeepCurrent)
            cmds.setParent(self.subLayout)
            self.bakeSampleLayout = cmds.rowLayout('bakeSampleLayout', numberOfColumns=4,
                                                   columnWidth4=(
                                                       1.5 * self.rotateOrderButtonWidth,
                                                       2 * self.rotateOrderButtonWidth,
                                                       intFieldWidth,
                                                       1.5 * self.rotateOrderButtonWidth),
                                                   adjustableColumn=4)
            cmds.text(label='Bake Sample ', width=1.5 * self.rotateOrderButtonWidth,
                      annotation=ann_bakeSample)
            self.bakeSampleSlider = cmds.intSlider(min=1, max=10, value=self.bakeSample,

                                                   annotation=ann_bakeSample,
                                                   width=(2 * self.rotateOrderButtonWidth),
                                                   changeCommand=self.updateBakeSampleInt,
                                                   dragCommand=self.updateBakeSampleInt)
            self.bakeSampleIntField = cmds.intField(min=1, max=10, value=self.bakeSample,
                                                    step=1,
                                                    width=intFieldWidth,
                                                    changeCommand=self.updateBakeSampleSlider,
                                                    visibleChangeCommand=self.updateBakeSampleSlider)
            self.layerOptions = ['New Layer', 'Base Layer']
            self.layerOptionVar = 'gimbalLayerBakeMode'
            self.layerBakeMode = get_option_var(self.layerOptionVar, self.layerOptions[0])
            cmds.optionVar(stringValue=(self.layerOptionVar, self.layerBakeMode))
            self.layerMenu = cmds.optionMenu(label='To:',
                                             width=1.5 * self.rotateOrderButtonWidth,
                                             changeCommand=self.changeLayerMode)
            layerList = [cmds.menuItem(key, label=key, parent=self.layerMenu) for key in self.layerOptions]
            self.toleranceSliderDragged(cmds.floatSlider(self.toleranceSlider, query=True, value=True))
            cmds.floatSlider(self.toleranceSlider, edit=True,
                             value=self.tolerance,
                             dragCommand=self.toleranceSliderDragged)

            # set the initial state of the options ui elements
            self.addAnnotations()
            ''' end of ui build'''

        def addAnnotations(self):
            lines = []
            lines.append('Layer bake option::')
            lines.append('  New Layer:')
            lines.append('      Bake the results to a new override layer.')
            lines.append('  Base Layer:')
            lines.append('      Bakes result to the base layer.')
            lines.append('      If objects are in layers it will')
            lines.append('      revert to creating a new layer')
            cmds.optionMenu(self.layerMenu, edit=True, annotation='\n'.join(lines))

        def initialiseOptionUI(self):
            if self.keyMode:
                self.hideBakeSampleUI()
                self.showKeyReduceUI()
            else:
                self.showBakeSampleUI()
                self.hideKeyReduceUI()

        def changeLayerMode(self, *args):
            self.layerBakeMode = args[0]
            cmds.optionVar(stringValue=(self.layerOptionVar, self.layerBakeMode))

        class queueObjectWidget(object):
            def __init__(self, obj, order, parent):
                self.parent = parent
                self.obj = obj
                self.order = order
                cmds.setParent(self.parent.queueLayout)
                self.rowLayout = cmds.rowLayout(numberOfColumns=3, columnWidth3=(80, 80, 80))
                self.deleteButton = cmds.iconTextButton(style='iconOnly',
                                                        image='deleteActive.png',
                                                        width=self.parent.rotateOrderButtonWidth,
                                                        label='delete',
                                                        command=self.deletePressed)
                self.nameLabel = cmds.text(width=self.parent.rotateOrderButtonWidth, label=str(self.obj))
                self.orderLabel = cmds.text(width=self.parent.rotateOrderButtonWidth, label=str(self.order))

            def deletePressed(self, *args):
                self.parent.removeFromQueue(self.obj)

        def updateBakeSampleSlider(self, data):
            cmds.intSlider(self.bakeSampleSlider, edit=True, value=data)
            cmds.optionVar(intValue=(self.bakeSampleOption, data))

        def updateBakeSampleInt(self, data):
            cmds.intField(self.bakeSampleIntField, edit=True, value=data)
            self.bakeSample = data
            cmds.optionVar(intValue=(self.bakeSampleOption, data))

        def updateQueueModeButton(self, *args):
            if self.quickMode:
                cmds.columnLayout(self.queueLayout, edit=True, enable=False)
                cmds.button(self.processButton, edit=True, enable=False)
                bakeState = cmds.rowLayout(self.bakeSampleLayout, query=True, enable=True)
                # cmds.window(self.window, edit=True, height=self.collapsedHeight + (self.bakeHeight * bakeState))
                cmds.button(self.queueModeButton, edit=True, label=self.quickLabel)
                cmds.button(self.queueModeButton, edit=True, backgroundColor=green)
            else:
                cmds.columnLayout(self.queueLayout, edit=True, enable=True)
                cmds.button(self.queueModeButton, edit=True, backgroundColor=orange)
                cmds.button(self.processButton, edit=True, enable=True)
                cmds.button(self.queueModeButton, edit=True, label=self.queueLabel)
            for index, order in enumerate(rotateOrderList):
                cmds.button(self.gimbalButtons[index],
                            edit=True,
                            annotation={True: ann_quickSetOrder, False: ann_queueSetOrder}[self.quickMode])

        def processQueue(self, *args):
            self.removeMissingObjectsFromQueue()
            bakeOrderClass = BakeOrderClass(nodeList=list(self.objectQueue.keys()),
                                            orderList=list(self.objectQueue.values()),
                                            keepCurrentKeys=self.keyMode,
                                            bakeSample=self.bakeSample,
                                            tolerance=self.tolerance,
                                            bakeToNewLayer=self.layerBakeMode == self.layerOptions[
                                                0])
            bakeOrderClass.bakeOrder()

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

        def add_outliner_connection(self):
            self.inputList = cmds.bakeResultsionConnection(activeList=True)
            self.fromEditor = cmds.bakeResultsionConnection()
            cmds.editor(self.outliner, edit=True, mainListConnection=self.inputList)
            cmds.editor(self.outliner, edit=True, selectionConnection=self.fromEditor)
            cmds.bakeResultsionConnection(self.fromEditor, edit=True, addScript=self.selectFunc)

        def attachUI(self):
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.queueModeButtonLayout, 'top', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.queueModeButtonLayout, 'left', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.queueModeButtonLayout, 'right', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.subLayout, 'left', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.subLayout, 'right', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.subLayout, 'bottom', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.processButton, 'bottom', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.processButton, 'left', self.margin))
            cmds.formLayout(self.mainLayout, e=True, attachForm=(self.processButton, 'right', self.margin))
            cmds.formLayout(self.mainLayout, e=True,
                            attachControl=(self.subLayout, 'top', self.margin, self.queueModeButtonLayout))

        def showUI(self):
            self.window.show()
            self.add_outliner_connection()
            sel = cmds.ls(sl=True)
            if sel:
                self.node = cmds.ls(sl=True)[-1]
                self.update()
            self.timeChangeScriptJob = cmds.scriptJob(event=["timeChanged", self.update], protected=False)
            self.DragReleaseScriptJob = cmds.scriptJob(event=["DragRelease", self.update], protected=False)

        def getAllAnimCurves(self, input):
            historyNodes = cmds.listHistory(input, pruneDagObjects=True, leaf=False)
            animCurves = cmds.ls(historyNodes, type='animCurve')
            return animCurves

        def hasAnimCurves(self, input):
            animCurves = self.getAllAnimCurves(input)
            if animCurves:
                return True

        def orderButtonPressed(self, data, *args):
            if self.quickMode:
                if not self.node:
                    msg = 'No object selected to process'
                    error(position="botRight",
                          prefix="Error",
                          message=msg, fadeStayTime=3.0, fadeOutTime=4.0)
                    return cmds.warning('No object selected to process')
                if self.hasAnimCurves(self.node):
                    bakeOrderClass = BakeOrderClass(nodeList=[self.node],
                                                    orderList=[data],
                                                    keepCurrentKeys=self.keyMode,
                                                    bakeSample=self.bakeSample,
                                                    tolerance=self.tolerance,
                                                    bakeToNewLayer=self.layerBakeMode ==
                                                                   self.layerOptions[
                                                                       0])
                    bakeOrderClass.bakeOrder()
                else:
                    self.staticSwapOrder(self.node, data)
            else:
                for s in cmds.ls(sl=True, type='transform'):
                    self.objectQueue[s] = data
            self.updateQueueObjects()

        def updateQueueObjects(self):
            for widget in self.queueWidgets:
                cmds.deleteUI(widget.rowLayout)
            self.queueWidgets = []

            self.removeMissingObjectsFromQueue()

            if self.objectQueue:
                for key, value in self.objectQueue.items():
                    self.queueWidgets.append(self.queueObjectWidget(key, value, self))
            self.updateProcessButtonColour()

        def removeMissingObjectsFromQueue(self):
            if self.objectQueue:
                for key, value in self.objectQueue.items():
                    # remove non existant objects from the queue
                    if not cmds.objExists(key):
                        self.objectQueue.pop(key)

        def removeFromQueue(self, obj):
            self.objectQueue.pop(obj)
            self.updateQueueObjects()

        def updateObjectLabel(self):
            if self.node:
                annotation = '%s :: %s' % (ann_currentObj, self.node)
            else:
                annotation = '%s :: %s' % (ann_currentObj, ann_noObj)
            cmds.text(self.objectLabel, edit=True, label=annotation)

        def updateGimbalLabels(self, reset=False):
            if reset:
                for index, order in enumerate(rotateOrderList):
                    gimbalVal = self.gimbalInfo[index]
                    cmds.text(self.originalLabels[index],
                              edit=True,
                              label='',
                              annotation=ann_blank,
                              enableBackground=False)

                    cmds.text(self.gimbalLabels[index],
                              edit=True,
                              label='',
                              annotation=ann_blank,
                              enableBackground=True)
                    cmds.button(self.gimbalButtons[index],
                                edit=True,
                                backgroundColor=defaultGrey,
                                annotation=ann_blank)
                return
            rotateOrder = cmds.getAttr(self.node + '.rotateOrder', asString=True)
            defaultRotateOrder, defaultRotateOrderInt = self.get_original_rotation_order(self.node)
            for index, order in enumerate(rotateOrderList):
                gimbalVal = self.gimbalInfo[index]
                cmds.text(self.originalLabels[index],
                          edit=True,
                          label={True: 'Default', False: ''}[order == defaultRotateOrder],
                          annotation={True: ann_defaultRot, False: ann_blank}[order == defaultRotateOrder],
                          enableBackground=order == defaultRotateOrder)

                cmds.text(self.gimbalLabels[index],
                          edit=True,
                          label=str("{} %".format("%.2f" % gimbalVal)),
                          annotation={True: ann_currentRot, False: ann_currentGimbal}[order == rotateOrder],
                          enableBackground=order == rotateOrder)
                cmds.button(self.gimbalButtons[index],
                            edit=True,
                            backgroundColor=getGimbalColour(gimbalVal),
                            annotation={True: ann_quickSetOrder, False: ann_queueSetOrder}[self.quickMode])

        def updateGimbalInfo(self):
            if self.node:
                self.gimbalInfo = self.get_all_gimbal_values(self.node)

        def selectFunc(self, *args):
            self.node = args[0][-1]

            self.update()

        @decorator.undoToggle
        def update(self):
            '''

            :return:
            '''
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
            if self.DragReleaseScriptJob != -1:
                cmds.scriptJob(kill=self.DragReleaseScriptJob, force=True)

        def cleanUpLocators(self):
            if self.bakeClass:
                self.bakeClass.cleanUpLocators()

        def setTolerance(self, value):
            cmds.optionVar(floatValue=(self.toleranceOption, value))

        def swapRotateOrderFrame(self, order):
            cmds.xform(self.node, preserve=True, rotateOrder=order)
            self.update()

        def staticSwapOrder(self, node, order):
            self.swap_rotate_order(node, order)
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

        def setKeepCurrent(self, *args):
            cmds.floatSlider(self.toleranceSlider, edit=True, value=1)
            cmds.button(self.keepKeysButton, edit=True, backgroundColor=green, enableBackground=True)

        def toleranceSliderDragged(self, value):
            '''

            :param value:
            :return:
            '''
            self.tolerance = value
            if value >= large:
                cmds.button(self.keepKeysButton, edit=True, backgroundColor=green, enableBackground=True)
            else:
                cmds.button(self.keepKeysButton, edit=True, backgroundColor=defaultGrey, enableBackground=False)
            '''
            if value <= small:
                cmds.button(self.denseButton, edit=True, backgroundColor=green, enableBackground=True)
                self.showBakeSampleUI()
            else:
                cmds.button(self.denseButton, edit=True, backgroundColor=defaultGrey, enableBackground=False)
                self.hideBakeSampleUI()

            '''

            cmds.optionVar(floatValue=(self.toleranceOption, self.tolerance))

        def hideBakeSampleUI(self):
            cmds.button(self.denseButton, edit=True, backgroundColor=defaultGrey, enableBackground=True)
            cmds.intSlider(self.bakeSampleSlider, edit=True, enable=False)
            cmds.intField(self.bakeSampleIntField, edit=True, enable=False)
            # cmds.rowLayout(self.bakeSampleLayout, edit=True, enable=False)
            '''
            bakeState = cmds.rowLayout(self.bakeSampleLayout, query=True, enable=True)
            queueState = cmds.columnLayout(self.queueLayout, query=True, enable=True)
            if not queueState:
                cmds.window(self.window, edit=True, height=self.collapsedHeight + (self.bakeHeight * bakeState))
            else:
                cmds.window(self.window, edit=True, height=self.fullHeight)
            '''

        def showBakeSampleUI(self):
            cmds.button(self.denseButton, edit=True, backgroundColor=green, enableBackground=False)
            cmds.intSlider(self.bakeSampleSlider, edit=True, enable=True)
            cmds.intField(self.bakeSampleIntField, edit=True, enable=True)
            # cmds.rowLayout(self.bakeSampleLayout, edit=True, enable=True)

        def showKeyReduceUI(self):
            if self.tolerance >= large:
                cmds.button(self.keepKeysButton, edit=True, backgroundColor=green, enableBackground=False)
            cmds.button(self.keysButton, edit=True, backgroundColor=green, enableBackground=True)

            cmds.rowLayout(self.tolerancelayout, edit=True, enable=True)

        def hideKeyReduceUI(self):
            cmds.button(self.keepKeysButton, edit=True, backgroundColor=defaultGrey, enableBackground=False)
            cmds.button(self.keysButton, edit=True, backgroundColor=defaultGrey, enableBackground=False)
            cmds.rowLayout(self.tolerancelayout, edit=True, enable=False)

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

    def staticSwapOrder(self, node, order):
        self.swap_rotate_order(node, order)
        self.updateGimbalLabels()

    def swap_rotate_order(self, input, rotateOrder):
        if isinstance(rotateOrder, int):
            rotateOrder = self.get_rotate_order_list(input)[rotateOrder]
        self.get_original_rotation_order(input)
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
                self.swap_rotate_order(value, self.orderList[index])
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

            layerOkState = self.funcs.checkKeyableState(self.nodeList)
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
            self.originalOrders.append(self.get_original_rotation_order(value)[1])
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

        if self.layerBakeMode or self.getLayerInclusion(self.nodeList):
            self.newLayer = cmds.animLayer(override=True)
            self.newLayer = cmds.rename(self.newLayer, self.newLayerName)

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
                                 value=rotateOrderList.index(self.orderList[index]),
                                 animLayer=str(self.newLayer))
            else:
                cmds.pasteKey(node,
                              attribute=['rotateX', 'rotateY', 'rotateZ'],
                              option='replace',
                              time=(self.firstKeys[index], self.lastKeys[index]))
                cmds.setKeyframe(node,
                                 time=[self.firstKeys[index]],
                                 attribute='rotateOrder',
                                 value=rotateOrderList.index(self.orderList[index]))

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

    def getLayerInclusion(self, input):
        if not input:
            return False
        if not isinstance(input, list):
            input = [input]
        inLayer = False
        for obj in input:
            if cmds.listConnections(obj, type='animLayer'):
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

    def __init__(self, parentCLS=None, parent=getMainWindow(), title='title', text='test',
                 altText='alt text'):
        super(GimbalUI_pyside, self).__init__(parent=parent, title=title, text=text)
        self.infoText.setText('Current Object ::')
        self.parentCLS = parentCLS
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

        self.layerOptions = ['New', 'Base']
        self.layerOptionVar = 'tbGimbalLayerBakeMode'
        self.layerBakeMode = get_option_var(self.layerOptionVar, self.layerOptions[0])

        set_option_var(self.layerOptionVar, self.layerBakeMode)

        self.quickModeOption = 'tbGimbalQueue'
        self.quickMode = get_option_var(self.quickModeOption, 0)
        set_option_var(self.quickModeOption, self.quickMode)

        self.queueWidgets = []
        self.collapsedHeight = 124
        self.fullHeight = 200
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

        self.processLabel = 'Process Queue'
        self.gimbalInfo = {}
        self.rotateOrderButtonWidth = 64

        self.queueWidgets = dict()

        self.result = str()
        self.setFixedSize(300 * dpiScale(), 160 * dpiScale())
        self.layout.setSpacing(0)
        self.originalLabels = list()
        self.gimbalLabels = list()
        self.gimbalButtons = list()

        self.createWidgets()
        self.attachUI()

        self.setupUIConnections()
        self.updateQueueModeButton()
        self.setInitialState()

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
            gimbalSetButton.setFixedHeight(22*dpiScale())
            self.originalLabels.append(orderLabel)
            self.gimbalLabels.append(gimbalValueLabel)
            self.gimbalButtons.append(gimbalSetButton)

        self.bakeKeysButton = QPushButton()

        self.denseButton = QPushButton(' Bake Keys <<')
        self.modeLabel = QLabel('<< Key Mode >>')
        self.modeLabel.setAlignment(Qt.AlignCenter)
        self.keysButton = QPushButton('>> Keep Keys')

        self.toolOptionStack = QStackedWidget()

        self.keysWidget = QWidget()
        self.keysLayout = QHBoxLayout()
        self.keysLayout.setSpacing(0)
        self.keysLayout.setContentsMargins(2, 2, 2, 2)

        self.keysWidget.setLayout(self.keysLayout)

        self.bakeWidget = QWidget()
        self.bakeLayout = QHBoxLayout()
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
        self.keepKeysButton.clicked.connect(self.setKeepCurrent)

        # changeCommand=self.updateBakeSampleSlider,
        self.modeLayout = QHBoxLayout()
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

        self.queueModeButton = QPushButton('Mode')
        self.queueModeButton.setFixedHeight(24 * dpiScale())
        self.queueModeButton.clicked.connect(self.toggleQueueMode)

        self.queueFrame = QFrame()

        self.queueScrollArea = QScrollArea()
        self.queueScrollArea.setFixedHeight(116 * dpiScale())
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
        bakeOrderClass = BakeOrderClass(nodeList=self.objectQueue.keys(),
                                        orderList=self.objectQueue.values(),
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
            self.queueModeButton.setText(self.quickLabel)
            self.queueModeButton.setStyleSheet(defaultBackgroundSS)
            self.setFixedHeight(174 * dpiScale())
            self.queueScrollArea.setVisible(False)
            self.processButton.setVisible(False)
        else:
            self.queueModeButton.setText(self.queueLabel)
            self.queueModeButton.setStyleSheet(mainStyleSheet)
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
            if self.hasAnimCurves(self.node):
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
                print('orderButtonPressed', data)
                self.objectQueue[s] = data
        self.updateQueueObjects()

    def clearQueueWidgets(self):
        for widget in self.queueWidgets.keys():
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
        if self.parentCLS.updateDisabled:
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
        self.swap_rotate_order(node, order)
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
        if self.layerBakeMode == 'Base':
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
        self.layout.addLayout(self.objectLabelLayout)
        self.objectLabelLayout.addWidget(self.infoText)
        self.objectLabelLayout.addWidget(self.objectLabel)
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.toolOptionStack)
        self.layout.addLayout(self.modeLayout)

        self.modeLayout.addWidget(self.keyModeLabel)
        self.modeLayout.addWidget(self.keyModeCombo)
        self.modeLayout.addWidget(self.bakeModeLabel)
        self.modeLayout.addWidget(self.layerModeCombo)

        self.toolOptionStack.addWidget(self.keysWidget)
        self.toolOptionStack.addWidget(self.bakeWidget)
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

        self.layout.addWidget(self.queueModeButton)

        self.queueScrollArea.setVisible(False)
        self.processButton.setVisible(False)
        self.queueFrame.setLayout(self.queueLayout)
        self.layout.addWidget(self.queueScrollArea)
        self.layout.addWidget(self.processButton)


ss2 = """
QSlider::groove:horizontal {
border: 1px solid #bbb;
background: transparent;
height: 4;
border-radius: 4px;
}

QSlider::sub-page:horizontal {
background: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);

border: 1px solid #2d2d2d;
height: 4;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::add-page:horizontal {
background: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);
border: 1px solid #2d2d2d;
height: 4px;
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
