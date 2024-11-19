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

__author__ = 'tom.bailey'

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('layers'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='select_best_layer',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.select_best_layer'],
                                     command=['LayerEditor.selectBestLayer()']))
        self.addCommand(self.tb_hkey(name='toggleLayerWeight',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.toggleLayerWeight'],
                                     command=['LayerEditor.toggleLayerWeight()']))
        self.addCommand(self.tb_hkey(name='setLayerWeightZero',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.toggleLayerWeight'],
                                     command=['LayerEditor.setLayerWeightFromTimeline(value=0)']))
        self.addCommand(self.tb_hkey(name='setLayerWeightOne',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.toggleLayerWeight'],
                                     command=['LayerEditor.setLayerWeightFromTimeline(value=1)']))
        self.addCommand(self.tb_hkey(name='convertAdditiveLayerToOverride',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.makeAdditiveFromOverrideLayer'],
                                     command=['LayerEditor.makeAdditiveFromOverrideLayer()']))

        return self.commandList

    def assignHotkeys(self):
        return


class LayerEditor(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'LayerEditor'
    hotkeyClass = hotkeys()
    funcs = Functions()
    hasAppliedUI = False

    useCustomUIOption = 'tUseCustomLayerEditor'
    tbEmbedOutlinerInChannelBoxOption = 'tbEmbedOutlinerInChannelBox'
    autoFixEnumOption = 'tbAutoFixEnumOption'
    autoFixEnumOnCreateOption = 'tbAutoFixEnumOnCreateOption'
    buttonSize = 18 * dpiScale()

    selectBestLayerTimer = -1
    selectBestLayerRepeat = False

    def __new__(cls):
        if LayerEditor.__instance is None:
            LayerEditor.__instance = object.__new__(cls)

        LayerEditor.__instance.val = cls.toolName
        return LayerEditor.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        """
        Put this in the startup script, not on class initialize
        """

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(LayerEditor, self).optionUI()
        customLayerEditorWidget = optionVarBoolWidget('Use custom layer editor - disabling requires restart',
                                                      self.useCustomUIOption)
        customOutlinerEditorWidget = optionVarBoolWidget('Put outliner in channelbox UI - disabling requires restart',
                                                      self.tbEmbedOutlinerInChannelBoxOption)

        autoFixEnumOnCreateWidget = optionVarBoolWidget('Auto fix enum attributes in additive anim layer creation',
                                                        self.autoFixEnumOnCreateOption)
        autoFixEnumWidget = optionVarBoolWidget('Auto fix enum attributes in existing additive layers',
                                                self.autoFixEnumOption)

        formLayout = QFormLayout()
        formLayout.addRow(customLayerEditorWidget.labelText, customLayerEditorWidget.checkBox)
        formLayout.addRow(autoFixEnumOnCreateWidget.labelText, autoFixEnumOnCreateWidget.checkBox)
        formLayout.addRow(autoFixEnumWidget.labelText, autoFixEnumWidget.checkBox)
        formLayout.addRow(customOutlinerEditorWidget.labelText, customOutlinerEditorWidget.checkBox)

        customLayerEditorWidget.changedSignal.connect(self.modifyAnimLayerTabToggled)
        self.layout.addWidget(autoFixEnumOnCreateWidget)
        self.layout.addWidget(customLayerEditorWidget)
        self.layout.addWidget(customOutlinerEditorWidget)
        self.layout.addWidget(autoFixEnumWidget)
        self.layout.addLayout(formLayout)
        self.layout.addStretch()
        return self.optionWidget

    def animLayerTabUI(self):
        mergeLayersDownButton = self.customButton(icon='moveButtonDown.png',
                                                  toolTip='Fast Merge all Layers')
        additiveExtractButton = self.customButton(icon='Amplify.png',
                                                  toolTip='Additive Extract Selected Layer')
        counterAnimationButton = self.customButton(icon='arcLengthDim.png',
                                                   toolTip='Counter animation layer')
        mergeLayersDownButton.clicked.connect(self.fastMergeAllButtonCommmand)
        additiveExtractButton.clicked.connect(self.additiveExtractButtonCommmand)
        counterAnimationButton.clicked.connect(self.counterAnimationButtonCommmand)
        return [mergeLayersDownButton, additiveExtractButton, counterAnimationButton]

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def modifyAnimLayerTabToggled(self, *args):
        print('modifyAnimLayerTabToggled', args)
        from pluginLookup import ClassFinder
        print('ClassFinder', ClassFinder)
        ClassFinder().applyAnimLayerTabModification()
        print('DONE')

    def modifyAnimLayerTab(self):
        if self.hasAppliedUI:
            return
        if not get_option_var(self.useCustomUIOption, False):
            return
        self.styleSheet = getStyleSheet()
        buttonSize = 22 * dpiScale()

        self.animLayerTabName = 'AnimLayerTab'
        self.animLayerTab = wrapInstance(int(omUI.MQtUtil.findControl(self.animLayerTabName)), QWidget)
        self.animLayerTab.objectName()
        animLayerTab_children = self.animLayerTab.children()
        animLayerTabLayout = animLayerTab_children[0]  # our layout to drop widgets in
        animLayerLayout = animLayerTab_children[-1]
        animLayerLayout.show()
        animLayerLayout.setAttribute(Qt.WA_StyledBackground, True)
        animLayerLayout.setStyleSheet('background-color: red')
        animLayerLayout.objectName()

        animLayerTabWidgets = animLayerLayout.children()[1:]

        self.zeroKeyAnimLayerButton = animLayerTabWidgets[0]
        self.zeroWeightAnimLayerButton = animLayerTabWidgets[1]
        self.fullWeightAnimLayerButton = animLayerTabWidgets[2]
        self.moveLayerUpButton = animLayerTabWidgets[6]
        self.moveLayerDownButton = animLayerTabWidgets[5]
        self.emptyAnimLayerButton = animLayerTabWidgets[3]
        self.selectedAnimLayerButton = animLayerTabWidgets[4]
        self.weightLabel = animLayerTabWidgets[7]
        self.animLayerWeightField = animLayerTabWidgets[8]
        self.animLayerWeightSlider = animLayerTabWidgets[9]
        self.animLayerWeightButton = animLayerTabWidgets[10]

        # extra buttons
        """
        Pull these buttons from somewhere else, from all tools maybe?
        """

        # modify cursor style
        self.animLayerWeightSlider.setCursor(QCursor(Qt.SplitHCursor))

        self.animLayerTree = animLayerTabWidgets[-1]

        # make a new QVBoxLayout
        mainLayout = QVBoxLayout()
        # make it neat
        mainLayout.setContentsMargins(4, 0, 4, 2)

        # new widget to wrap around the old maya UI
        animLayerWidget = QWidget()

        animLayerWidget.setLayout(mainLayout)

        # widget to wrap the top buttons
        topButtonWidget = QWidget()

        topButtonLayout = QHBoxLayout()
        topButtonLeftLayout = QHBoxLayout()
        topButtonRightLayout = QHBoxLayout()
        topButtonLayout.addLayout(topButtonLeftLayout)
        topButtonLayout.addStretch()
        topButtonLayout.addLayout(topButtonRightLayout)
        topButtonLayout.setContentsMargins(0, 0, 0, 0)
        topButtonLayout.setSpacing(0)
        topButtonWidget.setLayout(topButtonLayout)

        topButtonLeftLayout.addWidget(self.zeroKeyAnimLayerButton)
        topButtonLeftLayout.addWidget(self.zeroWeightAnimLayerButton)
        topButtonLeftLayout.addWidget(self.fullWeightAnimLayerButton)

        # topButtonRightLayout.addWidget(self.additiveExtractButton)
        # topButtonRightLayout.addWidget(self.mergeLayersDownButton)
        topButtonRightLayout.addWidget(self.moveLayerUpButton)
        topButtonRightLayout.addWidget(self.moveLayerDownButton)
        topButtonRightLayout.addWidget(self.emptyAnimLayerButton)
        topButtonRightLayout.addWidget(self.selectedAnimLayerButton)
        weightSliderWidget = QWidget()
        weightSliderLayout = QHBoxLayout()
        weightSliderLayout.setContentsMargins(0, 0, 0, 0)
        weightSliderLayout.setSpacing(2 * dpiScale())
        weightSliderWidget.setLayout(weightSliderLayout)
        weightSliderLayout.addWidget(self.weightLabel)
        weightSliderLayout.addWidget(self.animLayerWeightField)
        self.animLayerWeightField.setFixedWidth(40 * dpiScale())
        weightSliderLayout.addWidget(self.animLayerWeightSlider)
        weightSliderLayout.addWidget(self.animLayerWeightButton)
        self.curveButton = QPushButton('C')
        self.curveButton.setToolTip('Select the layer weight curve')
        weightSliderLayout.addWidget(self.curveButton)

        mainLayout.addWidget(topButtonWidget)
        mainLayout.addWidget(self.animLayerTree)
        mainLayout.addWidget(weightSliderWidget)

        animLayerTabLayout.addWidget(animLayerWidget)

        topButtonWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        weightSliderWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        topButtonWidget.setFixedHeight(24 * dpiScale())
        weightSliderWidget.setFixedHeight(22 * dpiScale())

        # topButtonWidget.setStyleSheet(self.styleSheet)
        weightSliderWidget.setStyleSheet(self.styleSheet)
        self.weightLabel.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        self.zeroKeyAnimLayerButton.setFixedSize(buttonSize, buttonSize)
        self.zeroWeightAnimLayerButton.setFixedSize(buttonSize, buttonSize)
        self.fullWeightAnimLayerButton.setFixedSize(buttonSize, buttonSize)
        self.moveLayerUpButton.setFixedSize(buttonSize, buttonSize)
        self.moveLayerDownButton.setFixedSize(buttonSize, buttonSize)
        self.emptyAnimLayerButton.setFixedSize(buttonSize, buttonSize)
        self.selectedAnimLayerButton.setFixedSize(buttonSize, buttonSize)

        # self.zeroWeightAnimLayerButton.clicked.disconnect()
        # self.zeroWeightAnimLayerButton.clicked.connect(self.setLayerWeightZero)
        cmds.button(self.zeroWeightAnimLayerButton.objectName(),
                    edit=True,
                    command=self.setLayerWeightZero)
        # self.fullWeightAnimLayerButton.clicked.disconnect()
        # self.fullWeightAnimLayerButton.clicked.connect(self.setLayerWeightOne())
        cmds.button(self.fullWeightAnimLayerButton.objectName(),
                    edit=True,
                    command=self.setLayerWeightOne)

        self.animLayerWeightSlider.valueChanged.disconnect()
        self.animLayerWeightSlider.valueChanged.connect(self.weightSliderEditCommand)
        self.animLayerWeightSlider.sliderReleased.connect(self.weightSliderReleasedCommand)
        self.animLayerWeightButton.setIcon(QIcon(""))
        self.animLayerWeightButton.setText('K')
        self.curveButton.setFixedSize(self.buttonSize, self.buttonSize)
        self.animLayerWeightButton.setFixedSize(self.buttonSize, self.buttonSize)

        animLayerLayout.deleteLater()
        self.curveButton.setEnabled(False)
        self.addAnimLayerUpdateScriptJob()

        # connections
        self.curveButton.clicked.connect(self.curveButtonCommand)
        self.hasAppliedUI = True
        return topButtonLeftLayout, topButtonRightLayout

    def customButton(self, icon='', toolTip=''):
        button = QPushButton()
        button.setIcon(QIcon(":/{0}".format(icon)))
        button.setFixedSize(self.buttonSize, self.buttonSize)
        button.setFlat(True)
        button.setToolTip(toolTip)
        button.setStyleSheet("background-color: transparent;border: 0px")
        button.setStyleSheet(self.styleSheet)
        return button

    def addAnimLayerUpdateScriptJob(self):
        self.scriptJob = cmds.scriptJob(compressUndo=True,
                                        permanent=True,
                                        parent='DisplayLayerUITabLayout',
                                        event=('animLayerRefresh', self.animLayerRefresh))

    def animLayerRefresh(self):
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        if not layers:
            self.toggleWeightButtons(False)
            return
        baseLayer = cmds.animLayer(query=True, root=True)
        if baseLayer in layers: layers.remove(baseLayer)
        if layers:
            self.toggleWeightButtons(True)
        else:
            self.toggleWeightButtons(False)

    def toggleWeightButtons(self, state):
        self.curveButton.setEnabled(state)

    def additiveExtractButtonCommmand(self):
        mel.eval('additiveExtractSelection')

    def fastMergeAllButtonCommmand(self):
        mel.eval('quickMergeAllLayers')

    def counterAnimationButtonCommmand(self):
        mel.eval('counterAnimLayer')

    def curveButtonCommand(self):
        weightCurves = list()
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        if not layers:
            return cmds.warning('no layers selected')
        for layer in layers:
            if layer == cmds.animLayer(query=True, root=True):
                continue
            weightCurve = cmds.listConnections('{0}.weight'.format(layer))
            if not weightCurve:
                continue
            weightCurves.append(weightCurve[0])
        if not weightCurves:
            return cmds.warning('no weight curves found')
        cmds.select(clear=True)
        cmds.select(weightCurves, replace=True)

    def weightSliderReleasedCommand(self):
        print('weightSliderReleasedCommand')
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        value = cmds.floatSlider('AnimLayerTabWeightSlider', query=True, value=True)
        baseLayer = cmds.animLayer(query=True, root=True)
        if baseLayer in layers: layers.remove(baseLayer)

        if value >= 0.99 or value <= 0.01:
            self.setLayerWeightKeyFlat(layers)

    def weightSliderEditCommand(self):
        mods = cmds.getModifiers()
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        value = cmds.floatSlider('AnimLayerTabWeightSlider', query=True, value=True)
        baseLayer = cmds.animLayer(query=True, root=True)
        if baseLayer in layers: layers.remove(baseLayer)
        if not layers:
            return
        if cmds.undoInfo(query=True, stateWithoutFlush=True):
            cmds.undoInfo(stateWithoutFlush=False)
            # self.refreshHack()
            cmds.undoInfo(stateWithoutFlush=True)
        cmds.floatField('AnimLayerTabWeightField', edit=True, value=value)
        self.setLayerWeightNoRefresh(layers, value)

    def refreshHack(self):
        cmds.refresh(suspend=True)
        cmds.currentTime(cmds.currentTime(query=True))
        cmds.refresh(suspend=False)

    def toggleLayerWeight(self):
        layers = self.funcs.get_selected_layers()
        if not layers:
            return
        if layers[-1] == 'BaseAnimation':
            return
        currentWeight = int(cmds.getAttr('{0}.weight'.format(layers[-1])))
        cmds.setAttr('{0}.weight'.format(layers[-1]), int(currentWeight <= 0.5))
        cmds.setKeyframe('{0}.weight'.format(layers[-1]))
        cmds.keyTangent('{0}.weight'.format(layers[-1]), inTangentType='flat', outTangentType='flat')

    def setLayerWeightFromTimeline(self, value=1):
        layers = self.funcs.get_selected_layers()
        if not layers:
            return
        if layers[-1] == 'BaseAnimation':
            return
        timeRange = [cmds.currentTime(query=True)]
        if self.funcs.isTimelineHighlighted():
            timeRange = self.funcs.getTimelineHighlightedRange()
        for time in timeRange:
            cmds.setKeyframe('{0}.weight'.format(layers[-1]), time=time, value=value)
            cmds.keyTangent('{0}.weight'.format(layers[-1]), inTangentType='flat', outTangentType='flat')

    def setLayerWeightNoRefresh(self, layers, weight):
        for layer in layers:
            cmds.animLayer(layer, edit=True, weight=weight)

    def setLayerWeightKeyFlat(self, layers):
        for layer in layers:
            cmds.setKeyframe('{0}.weight'.format(layer))
            cmds.keyTangent('{0}.weight'.format(layer), inTangentType='flat', outTangentType='flat')

    def setLayerWeight(self, layers, weight):
        self.setLayerWeightNoRefresh(layers, weight)
        self.setLayerWeightKeyFlat(layers)

    def setLayerWeightZero(self, *args):
        baseLayer = cmds.animLayer(query=True, root=True)
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        if baseLayer in layers: layers.remove(baseLayer)
        if not layers:
            return
        self.refreshHack()
        self.setLayerWeight(layers, 0.0)

    def setLayerWeightOne(self, *args):
        baseLayer = cmds.animLayer(query=True, root=True)
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        if baseLayer in layers: layers.remove(baseLayer)
        if not layers:
            return
        self.refreshHack()
        self.setLayerWeight(layers, 1.0)

    def bookEndLayerWeight(self, layer, startTime, endTime, innerValue=1, outerValue=0):
        cmds.setKeyframe('{0}.weight'.format(layer), value=0.0, time=startTime - 1, inTangentType='flat',
                         outTangentType='flat')
        cmds.setKeyframe('{0}.weight'.format(layer), value=1.0, time=startTime, inTangentType='flat',
                         outTangentType='flat')
        cmds.setKeyframe('{0}.weight'.format(layer), value=1.0, time=endTime, inTangentType='flat',
                         outTangentType='flat')
        cmds.setKeyframe('{0}.weight'.format(layer), value=0.0, time=endTime + 1, inTangentType='flat',
                         outTangentType='flat')

    def selectBestLayer(self, sel=None):
        """
        Selects the top most preferred layer if an object is selected
        on repeat it will cycle down through available layers
        Changing selection will reset the repeat state
        If no object is selected, the topmost layer will be selected
        :param sel:
        :return:
        """
        resultLayer = None
        selectedLayer = None
        allLayers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, children=True)
        if not allLayers:
            return
        currentLayerSelection = [layer for layer in allLayers if cmds.animLayer(layer, query=True, selected=True)]
        if currentLayerSelection:
            if len(currentLayerSelection) > 1:
                selectedLayer = None
            else:
                selectedLayer = currentLayerSelection[-1]
        if sel is None:
            sel = cmds.ls(sl=True)
        if not sel:
            resultLayer = allLayers[-1]
        if not resultLayer:
            affectedLayers = cmds.animLayer(query=True, affectedLayers=True)
            if affectedLayers:
                index = 0
                if selectedLayer in affectedLayers:
                    if self.selectBestLayerRepeat or selectedLayer == affectedLayers[0]:
                        index = (affectedLayers.index(selectedLayer) + 1) % (len(affectedLayers))

                resultLayer = affectedLayers[index]
        cmds.treeView('AnimLayerTabanimLayerEditor', edit=True, clearSelection=True)
        cmds.animLayer(resultLayer, edit=True, preferred=True, selected=True)

        if not self.selectBestLayerRepeat:
            self.selectBestLayerRepeat = True
            cmds.scriptJob(runOnce=True, event=['SelectionChanged', partial(self.clearBestAnimSelection)])

    def clearBestAnimSelection(self):
        self.selectBestLayerRepeat = False

    def colourAnimLayers(self, *args):
        """
        Script job function to colour the anim layer tab based on ghosting colour
        :param args:
        :return:
        """

        def lerpFloat(a, b, alpha):
            return a * alpha + b * (1.0 - alpha)

        # TODO - hook this up to a script job when anim layer tab is rebuilt
        if not cmds.treeView('AnimLayerTabanimLayerEditor', query=True, exists=True):
            return
        layers = cmds.ls(type='animLayer')
        for layer in layers:
            colour = cmds.getAttr(layer + '.ghostColor') - 1
            col = cmds.colorIndex(colour, q=True)
            cmds.treeView('AnimLayerTabanimLayerEditor',
                        edit=True,
                        labelBackgroundColor=[layer,
                                              lerpFloat(col[0], 0.5, 0.5),
                                              lerpFloat(col[1], 0.5, 0.5),
                                              lerpFloat(col[2], 0.5, 0.5)])

    def makeAdditiveFromOverrideLayer(self):
        # get the attributes in the override layer
        selectedLayers = self.funcs.get_selected_layers()
        if not selectedLayers:
            return cmds.warning('No override layer selected')

        overrideLayer = None

        for layer in selectedLayers:
            if not cmds.animLayer(layer, query=True, override=True):
                continue
            overrideLayer = layer
        if not overrideLayer:
            return cmds.warning('No override layer selected')
        animCurves = cmds.animLayer(overrideLayer, query=True, animCurves=True)
        attributes = cmds.animLayer(overrideLayer, query=True, attribute=True)

        additiveLayer = self.allTools.tools['BakeTools'].createLayer(override=False, suffixStr=None, component=True)
        additiveLayer = cmds.rename(additiveLayer, overrideLayer + '_toAdditive')
        cmds.animLayer(additiveLayer, edit=True, moveLayerBefore=overrideLayer)
        cmds.animLayer(additiveLayer, edit=True, weight=0)
        cmds.animLayer(additiveLayer, edit=True, attribute=attributes)

        # get the time range from the animation layer
        startTime = 99999
        endTime = -99999
        for curve in animCurves:
            keyTimes = cmds.keyframe(curve, query=True, tc=True)
            startTime = min(keyTimes[0], startTime)
            endTime = max(keyTimes[-1], endTime)

        # deselect all layers
        for layer in selectedLayers:
            cmds.animLayer(layer, edit=True, selected=False)
            cmds.animLayer(layer, edit=True, preferred=False)

        # select the new layer
        cmds.animLayer(additiveLayer, edit=True, selected=True)
        cmds.animLayer(additiveLayer, edit=True, preferred=True)
        with self.funcs.suspendUpdate():
            for x in range(int(startTime), int(endTime)+1):
                cmds.currentTime(x - startTime)
                cmds.setKeyframe(attributes, breakdown=False, preserveCurveShape=False, hierarchy=False,
                                 controlPoints=False, shape=False)
        cmds.animLayer(additiveLayer, edit=True, weight=1)
        cmds.animLayer(overrideLayer, edit=True, mute=True)
        cmds.animLayer(additiveLayer, edit=True, moveLayerAfter=overrideLayer)
        # create the additive layer
        # move it below the override layer
        # add the attributes to the additive layer
        # set the weight to 0
        # get the frame range
        # key the attributes in the additive layer
        # set the weight to 1
        # mute the override layer
        pass
