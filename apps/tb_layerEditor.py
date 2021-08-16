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
import maya.cmds as cmds

from Abstract import *
import maya.OpenMayaUI as omui

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
from getStyleSheet import *

__author__ = 'tom.bailey'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('layers'))
        self.commandList = list()
        '''
        self.addCommand(self.tb_hkey(name='toggle_isolate_selection',
                                     annotation='',
                                     category=self.category,
                                     command=['isolator.toggle_isolate()']))
        self.addCommand(self.tb_hkey(name='addToIsolation',
                                     annotation='',
                                     category=self.category,
                                     command=['isolator.addToIsolation()']))
        '''
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class LayerEditor(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'LayerEditor'
    hotkeyClass = hotkeys()
    funcs = functions()
    hasAppliedUI = False

    useCustomUIOption = 'tUseCustomLayerEditor'

    def __new__(cls):
        if LayerEditor.__instance is None:
            LayerEditor.__instance = object.__new__(cls)

        LayerEditor.__instance.val = cls.toolName
        return LayerEditor.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        if pm.optionVar.get(self.useCustomUIOption, False):
            self.modifyAnimLayerTab()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(LayerEditor, self).optionUI()
        customLayerEditorWidget = optionVarBoolWidget('Use custom layer editor', self.useCustomUIOption)
        customLayerEditorWidget.changedSignal.connect(self.modifyAnimLayerTab)
        self.layout.addWidget(customLayerEditorWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def modifyAnimLayerTab(self):
        if self.hasAppliedUI:
            return
        self.styleSheet = getStyleSheet()
        buttonSize = 22

        self.animLayerTabName = 'AnimLayerTab'
        self.animLayerTab = wrapInstance(int(omui.MQtUtil.findControl(self.animLayerTabName)), QWidget)
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
        topButtonLayout.setContentsMargins(0, 0, 0, 0)
        topButtonLayout.setSpacing(0)
        topButtonWidget.setLayout(topButtonLayout)

        topButtonLayout.addWidget(self.zeroKeyAnimLayerButton)
        topButtonLayout.addWidget(self.zeroWeightAnimLayerButton)
        topButtonLayout.addWidget(self.fullWeightAnimLayerButton)
        topButtonLayout.addStretch()
        topButtonLayout.addWidget(self.moveLayerUpButton)
        topButtonLayout.addWidget(self.moveLayerDownButton)
        topButtonLayout.addWidget(self.emptyAnimLayerButton)
        topButtonLayout.addWidget(self.selectedAnimLayerButton)
        weightSliderWidget = QWidget()
        weightSliderLayout = QHBoxLayout()
        weightSliderLayout.setContentsMargins(0, 0, 0, 0)
        weightSliderLayout.setSpacing(2)
        weightSliderWidget.setLayout(weightSliderLayout)
        weightSliderLayout.addWidget(self.weightLabel)
        weightSliderLayout.addWidget(self.animLayerWeightField)
        self.animLayerWeightField.setFixedWidth(40)
        weightSliderLayout.addWidget(self.animLayerWeightSlider)
        weightSliderLayout.addWidget(self.animLayerWeightButton)
        self.curveButton = QPushButton('C')
        weightSliderLayout.addWidget(self.curveButton)

        mainLayout.addWidget(topButtonWidget)
        mainLayout.addWidget(self.animLayerTree)
        mainLayout.addWidget(weightSliderWidget)

        animLayerTabLayout.addWidget(animLayerWidget)

        topButtonWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        weightSliderWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        topButtonWidget.setFixedHeight(22)
        weightSliderWidget.setFixedHeight(22)

        # topButtonWidget.setStyleSheet(self.styleSheet)
        weightSliderWidget.setStyleSheet(self.styleSheet)
        self.weightLabel.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        animLayerTabWidgets[0].setFixedSize(buttonSize, buttonSize)
        animLayerTabWidgets[1].setFixedSize(buttonSize, buttonSize)
        animLayerTabWidgets[2].setFixedSize(buttonSize, buttonSize)
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
        self.curveButton.setFixedSize(18, 18)
        self.curveButton.clicked.connect(self.curveButtonCommand)
        self.animLayerWeightButton.setFixedSize(18, 18)

        animLayerLayout.deleteLater()
        self.curveButton.setEnabled(False)
        self.addAnimLayerUpdateScriptJob()
        self.hasAppliedUI = True

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

    def curveButtonCommand(self):
        weightCurves = list()
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        if not layers:
            return cmds.warning('no layers selected')
        print ('weight curves for layers', layers)
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
        print ('weightSliderReleasedCommand')
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        value = cmds.floatSlider('AnimLayerTabWeightSlider', query=True, value=True)
        baseLayer = cmds.animLayer(query=True, root=True)
        if baseLayer in layers: layers.remove(baseLayer)

        if value >= 0.99 or value <= 0.01:
            print ('setLayerWeightKeyFlat')
            self.setLayerWeightKeyFlat(layers)

    def weightSliderEditCommand(self):
        mods = cmds.getModifiers()
        print ('mods', mods)
        layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True)
        value = cmds.floatSlider('AnimLayerTabWeightSlider', query=True, value=True)
        baseLayer = cmds.animLayer(query=True, root=True)
        if baseLayer in layers: layers.remove(baseLayer)
        if not layers:
            return
        if cmds.undoInfo(query=True, stateWithoutFlush=True):
            cmds.undoInfo(stateWithoutFlush=False)
            self.refreshHack()

        cmds.floatField('AnimLayerTabWeightField', edit=True, value=value)
        self.setLayerWeightNoRefresh(layers, value)

    def refreshHack(self):
        cmds.refresh(suspend=True)
        cmds.currentTime(cmds.currentTime(query=True))
        cmds.refresh(suspend=False)

    def setLayerWeightNoRefresh(self, layers, weight):
        for layer in layers:
            cmds.animLayer(layer, edit=True, weight=weight)

    def setLayerWeightKeyFlat(self, layers):
        for layer in layers:
            print ('setLayerWeightKeyFlat', layer)
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
