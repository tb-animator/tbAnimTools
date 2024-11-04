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

__author__ = 'tom.bailey'

_modifiedGraphEditor = 'ModifiedGraphEditor'

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbSetMoveKeyConstant',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyConstant()']))
        self.addCommand(self.tb_hkey(name='tbSetMoveKeyLinear',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyLinear()']))
        self.addCommand(self.tb_hkey(name='tbSetMoveKeyPower',
                                     annotation='',
                                     ctx='graphEditor',
                                     category=self.category,
                                     command=['GraphEditor.setMoveKeyPower()']))
        return self.commandList

    def assignHotkeys(self):
        return


class GraphEditor(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'GraphEditor'
    hotkeyClass = hotkeys()
    funcs = Functions()

    customUiLocationOption = 'tbCustomGEUILocation'
    customUiLocation = ['AboveButtons', 'BelowButtons', 'BeforeButtons', 'AfterButtons', 'MenuBar']
    graphEditorToolbarOption = 'tbGraphEditorToolbarOption'

    def __new__(cls):
        if GraphEditor.__instance is None:
            GraphEditor.__instance = object.__new__(cls)

        GraphEditor.__instance.val = cls.toolName
        return GraphEditor.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(GraphEditor, self).optionUI()
        useTumbleOptionWidget = optionVarBoolWidget('Use modified graph editor toolbar ', self.graphEditorToolbarOption)
        self.layout.addWidget(useTumbleOptionWidget)
        self.uiLocationWidget = comboBoxWidget(optionVar=self.customUiLocationOption,
                                               values=self.customUiLocation,
                                               defaultValue=get_option_var(self.customUiLocationOption,
                                                                             self.customUiLocation[0]),
                                               label='Custom UI location')
        self.layout.addWidget(self.uiLocationWidget)
        # connect the checkbox changed event to the function that handles removing/adding the camera scriptJobs
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def deferredLoad(self):
        self.deferredLoadJob = cmds.scriptJob(event=('graphEditorChanged', self.loadGraphEditorModifications),
                                              runOnce=True)

    def loadGraphEditorModifications(self, *args):
        ge = cmds.getPanel(scriptType="graphEditor")
        for g in ge:
            control = omUI.MQtUtil.findControl(g)
            if not control:
                continue
            pge = wrapInstance(int(control), QWidget)
            if get_option_var(self.graphEditorToolbarOption, False):
                self.modifyGraphEditorToolbar(pge)
            # self.createPopup(pge)

    def createPopup(self, graphEditor):
        if not hasattr(graphEditor, 'hasShiftPopup'):
            setattr(graphEditor, 'hasShiftPopup', False)
        if getattr(graphEditor, 'hasShiftPopup'):
            return
        name = 'graphEditor1GraphEdanimCurveEditorMenu'
        try:
            if cmds.popupMenu(name, query=True, exists=True):
                popup = cmds.popupMenu(name,
                                       ctrlModifier=False,
                                       shiftModifier=True,
                                       button=3,
                                       allowOptionBoxes=False,
                                       parent='graphEditor1GraphEd',
                                       markingMenu=True,
                                       postMenuCommandOnce=False,
                                       postMenuCommand=partial(self.graphEditorMenu, name))
                setattr(graphEditor, 'hasShiftPopup', True)
        except:
            pass


    def modifyGraphEditorToolbar(self, graphEditor):
        # check tween classes
        '''

        :return:
        '''
        '''
        for key, value in self.keyTweenDict.items():
            if not self.keyTweenMethods[key]:
                self.keyTweenMethods[key] = value()
            if not self.keyTweenMethods[key].instance:
                self.keyTweenMethods[key].instance = value()
        '''

        # print('modifyGraphEditorToolbar')
        if int(cmds.about(majorVersion=True)) >= 2025:
            self.modifyGraphEditorToolbar_2025(graphEditor)
            return

        if int(cmds.about(majorVersion=True)) >= 2024:
            self.modifyGraphEditorToolbar_2024(graphEditor)
            return
        if int(cmds.about(majorVersion=True)) >= 2023:
            if int(cmds.about(minorVersion=True)) >= 3:
                self.modifyGraphEditorToolbar_2024(graphEditor)
                return
        # maya 2024 actually has collapsing widgets in the graph editor, so got to change this
        graphEditor1 = wrapInstance(int(omUI.MQtUtil.findControl('graphEditor1')), QWidget)
        widgets = graphEditor1.children()[-1].children()[1].children()[-1].children()[-1].children()[1].children()
        graphEditorLayout = widgets[0]
        if graphEditorLayout.objectName() == _modifiedGraphEditor:
            return
        graphEditorLayout.setObjectName(_modifiedGraphEditor)
        sliderLayout = self.createSliderToolBar()
        tempWidget = GraphEditorWidget()

        graphEditorLayout.addWidget(tempWidget)

        layout = widgets[0]
        buttons = widgets[1:]

        index = 0
        buttonList = [[]]
        for x in widgets:
            if (type(x) == QFrame):
                index += 1
                buttonList.append(list())
            buttonList[-1].append(x)

        collapsedWidgets = list()
        for index, grp in enumerate(buttonList):
            optionVarName = grp[0].objectName() + '_collapseState'

            cBox = CollapsibleBox(optionVar=optionVarName)
            collapsedWidgets.append(cBox)
            cBox.setFixedHeight(24 * dpiScale())
            cBoxLayout = QHBoxLayout()
            cBoxLayout.setAlignment(Qt.AlignLeft)
            cBoxLayout.setContentsMargins(0, 0, 0, 0)
            cBoxLayout.setSpacing(0)

            for button in grp:
                if type(button) == QLayout:
                    continue
                if type(button) == QFrame:
                    button.deleteLater()
                    continue
                if type(button) == QButtonGroup:
                    continue
                if index == 0:
                    button.setFixedSize(24 * dpiScale(), 24 * dpiScale())
                cBoxLayout.addWidget(button)

            cBox.setContentLayout(cBoxLayout)

        defaultLocation = self.allTools.tools['GraphEditor'].customUiLocation[0]
        currentLocation = get_option_var(self.allTools.tools['GraphEditor'].customUiLocationOption,
                                           defaultLocation)

        if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[-1]:
            widgets = graphEditor1.children()
            self.graphEdiMenuBar = None
            for w in widgets:
                # print(str(w.__class__))
                if 'QMenuBar' in str(w.__class__):
                    self.graphEdiMenuBar = w
            if self.graphEdiMenuBar:
                self.sliderParentWidget = GraphEdToolbarWidget()
                self.sliderParentWidget.setLayout(sliderLayout)
                self.graphEdiMenuBar.setCornerWidget(self.sliderParentWidget)
            return

        # extra layout to hold the original maya buttons
        dupeLayout = QHBoxLayout()
        dupeLayout.setAlignment(Qt.AlignLeft)
        dupeLayout.setSpacing(0)
        dupeLayout.setContentsMargins(0, 0, 0, 0)
        # buttons = widgets[1:]
        for c in collapsedWidgets:
            dupeLayout.addWidget(c)

        # dupeLayout.addLayout(layout)
        blankLabel = QLabel('')
        blankLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        dupeLayout.addWidget(blankLabel)
        dupeLayout.addStretch(100)

        customLayout = QHBoxLayout()
        customLayout.setSpacing(0)
        customLayout.setContentsMargins(0, 0, 0, 0)
        customLayout.setAlignment(Qt.AlignCenter)

        # ['AboveButtons', 'BelowButtons', 'BeforeButtons', 'AfterButtons', 'MenuBar']
        if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[0]:
            tempLayout = QVBoxLayout()
            tempLayout.addLayout(dupeLayout)
            tempLayout.insertLayout(0, customLayout)
        elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[1]:
            tempLayout = QVBoxLayout()
            tempLayout.addLayout(dupeLayout)
            tempLayout.addLayout(customLayout)
        elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[2]:
            tempLayout = QHBoxLayout()
            tempLayout.addLayout(dupeLayout)
            tempLayout.insertLayout(0, customLayout)
        elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[3]:
            tempLayout = QHBoxLayout()
            tempLayout.addLayout(dupeLayout)
            tempLayout.addLayout(customLayout)
        # print ('added a slider')
        tempWidget.setLayout(tempLayout)
        w = QWidget()
        w.setLayout(sliderLayout)
        customLayout.addWidget(w)

        for widget in collapsedWidgets:
            widget.show()
            widget.playAnimationByState(force=True, state=widget.getState())
    def createSliderToolBar(self):
        self.sliderParentWidget = GraphEdToolbarWidget()
        sliderLayout = QHBoxLayout()
        sliderLayout.setAlignment(Qt.AlignLeft)
        # sliderLayout.addStretch()
        self.sliderParentWidget.setLayout(sliderLayout)

        sliderLayout.setContentsMargins(0, 0, 0, 0)
        sliderLayout.setSpacing(0)
        # sliderLayout.addWidget(graphEditKeyWidget)  # .setParent(phLayout)
        '''
        slider = PopupSlider(closeOnRelease=False, mode=fn_BREAKDOWN, icon=self.keyTweenIcons[fn_BREAKDOWN],
                             width=200, minValue=-50, maxValue=50, overshootMin=-100, overshootMax=100)

        widgets[0].addWidget(slider)  # .setParent(phLayout)
        '''
        # adjustmentBlendButton = GraphToolbarButton(icon='plotKey.png',
        #                                            toolTip='Look at me a tooltip')
        # adjustmentBlendButton.setPopupMenu(AdjustmentButtonPopup)
        keyframeWidget = self.allTools.tools['KeyModifiers'].graphEditorWidget(self.sliderParentWidget)
        sliderWidget = self.allTools.tools['SlideTools'].graphEditorWidget(self.sliderParentWidget)
        # adjustmentBlendButton.clicked.connect(self.plotKeyPressed)
        # sliderLayout.addWidget(adjustmentBlendButton)
        sliderLayout.addWidget(keyframeWidget)
        sliderLayout.addWidget(sliderWidget)
        self.loadData()
        # force the slider tools to load just in case

        sliderLayout.addStretch(100)
        return sliderLayout

    def modifyGraphEditorToolbar_2024(self, graphEditor):
        # check tween classes
        '''

        :return:
        '''
        '''
        for key, value in self.keyTweenDict.items():
            if not self.keyTweenMethods[key]:
                self.keyTweenMethods[key] = value()
            if not self.keyTweenMethods[key].instance:
                self.keyTweenMethods[key].instance = value()
        '''
        # maya 2024 actually has collapsing widgets in the graph editor, so got to change this
        graphEditor1 = wrapInstance(int(omUI.MQtUtil.findControl('graphEditor1')), QWidget)
        # I wish autodesk would name their UI layouts
        # print('this', graphEditor1.children()[-1].children()[1].children()[-1].children()[-1].children()[1])
        widgets = graphEditor1.children()[-1].children()[1].children()[-1].children()[-1].children()[1].children()
        graphEditorLayout = widgets[0]
        # print('widgets', widgets)

        # print('hex(id(widget))', hex(id(graphEditorLayout)))
        # print('graphEditorLayout', graphEditorLayout)
        # print('graphEditorLayout children', graphEditorLayout.children())
        # print('sliderParentWidget', self.sliderParentWidget)
        # print('object name', graphEditorLayout.objectName())

        # try:
        if not graphEditorLayout.objectName() == _modifiedGraphEditor:
            graphEditorLayout.setObjectName(_modifiedGraphEditor)
            parentWidget = graphEditor1.children()[-1].children()[1].children()[-1].children()[-1]
            # print('parentWidget', parentWidget)
            parentWidget = graphEditor1.children()[-1].children()[1].children()[-1]
            # print('parentWidget', parentWidget)
            parentWidget = graphEditor1.children()[-1].children()[1]
            # verticalLayout = QVBoxLayout()
            # verticalLayout.addWidget(parentWidget)
            parentLayout = parentWidget.parent()
            # graphEditor1.children()[-1].addLayout(verticalLayout)

            defaultLocation = self.allTools.tools['GraphEditor'].customUiLocation[0]
            currentLocation = get_option_var(self.allTools.tools['GraphEditor'].customUiLocationOption,
                                               defaultLocation)

            sliderLayout = self.createSliderToolBar()

            tempWidget = GraphEditorWidget()

            graphEditorLayout.addWidget(tempWidget)

            if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[-1]:
                widgets = graphEditor1.children()
                self.graphEdiMenuBar = None
                for w in widgets:
                    # print(str(w.__class__))
                    if 'QMenuBar' in str(w.__class__):
                        self.graphEdiMenuBar = w
                if self.graphEdiMenuBar:
                    self.sliderParentWidget = GraphEdToolbarWidget()
                    self.sliderParentWidget.setLayout(sliderLayout)
                    self.graphEdiMenuBar.setCornerWidget(self.sliderParentWidget)
                return

            # extra layout to hold the original maya buttons
            dupeLayout = QHBoxLayout()
            dupeLayout.setAlignment(Qt.AlignLeft)
            dupeLayout.setSpacing(0)
            dupeLayout.setContentsMargins(0, 0, 0, 0)
            buttons = widgets[1:]
            #dupeLayout.addWidget(widgets[1])
            for b in buttons:
                # print ('dupeLayout', dupeLayout, b)
                dupeLayout.addWidget(b)

            blankLabel = QLabel('')
            blankLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
            dupeLayout.addWidget(blankLabel)
            dupeLayout.addStretch(100)
            customLayout = QHBoxLayout()
            customLayout.setSpacing(0)
            customLayout.setContentsMargins(0, 0, 0, 0)
            customLayout.setAlignment(Qt.AlignCenter)

            # ['AboveButtons', 'BelowButtons', 'BeforeButtons', 'AfterButtons', 'MenuBar']
            if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[0]:
                tempLayout = QVBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.insertLayout(0, customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[1]:
                tempLayout = QVBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.addLayout(customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[2]:
                tempLayout = QHBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.insertLayout(0, customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[3]:
                tempLayout = QHBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.addLayout(customLayout)

            tempWidget.setLayout(tempLayout)
            w = QWidget()
            w.setLayout(sliderLayout)
            customLayout.addWidget(w)

            graphEditor1.__dict__['modified'] = True
            # print('graphEditor1', graphEditor1.__dict__['modified'])
        # except:
        #     return
    def modifyGraphEditorToolbar_2025(self, graphEditor):
        # check tween classes
        '''

        :return:
        '''
        '''
        for key, value in self.keyTweenDict.items():
            if not self.keyTweenMethods[key]:
                self.keyTweenMethods[key] = value()
            if not self.keyTweenMethods[key].instance:
                self.keyTweenMethods[key].instance = value()
        '''
        # maya 2024 actually has collapsing widgets in the graph editor, so got to change this
        graphEditor1 = wrapInstance(int(omUI.MQtUtil.findControl('graphEditor1')), QWidget)
        # I wish autodesk would name their UI layouts
        # print('this', graphEditor1.children()[-1].children()[1].children()[-1].children()[-1].children()[1])
        widgets = graphEditor1.children()[-1].children()[1].children()[-1].children()[-1].children()[1].children()
        graphEditorLayout = widgets[0]
        # print('widgets', widgets)

        # print('hex(id(widget))', hex(id(graphEditorLayout)))
        # print('graphEditorLayout', graphEditorLayout)
        # print('graphEditorLayout children', graphEditorLayout.children())
        # print('sliderParentWidget', self.sliderParentWidget)
        # print('object name', graphEditorLayout.objectName())

        # try:
        if not graphEditorLayout.objectName() == _modifiedGraphEditor:
            graphEditorLayout.setObjectName(_modifiedGraphEditor)
            parentWidget = graphEditor1.children()[-1].children()[1].children()[-1].children()[-1]
            # print('parentWidget', parentWidget)
            parentWidget = graphEditor1.children()[-1].children()[1].children()[-1]
            # print('parentWidget', parentWidget)
            parentWidget = graphEditor1.children()[-1].children()[1]
            # verticalLayout = QVBoxLayout()
            # verticalLayout.addWidget(parentWidget)
            parentLayout = parentWidget.parent()
            # graphEditor1.children()[-1].addLayout(verticalLayout)

            defaultLocation = self.allTools.tools['GraphEditor'].customUiLocation[0]
            currentLocation = get_option_var(self.allTools.tools['GraphEditor'].customUiLocationOption,
                                               defaultLocation)

            sliderLayout = self.createSliderToolBar()

            tempWidget = GraphEditorWidget()

            graphEditorLayout.addWidget(tempWidget)

            if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[-1]:
                widgets = graphEditor1.children()
                self.graphEdiMenuBar = None
                for w in widgets:
                    # print(str(w.__class__))
                    if 'QMenuBar' in str(w.__class__):
                        self.graphEdiMenuBar = w
                if self.graphEdiMenuBar:
                    self.sliderParentWidget = GraphEdToolbarWidget()
                    self.sliderParentWidget.setLayout(sliderLayout)
                    self.graphEdiMenuBar.setCornerWidget(self.sliderParentWidget)
                return

            # extra layout to hold the original maya buttons
            dupeLayout = QHBoxLayout()
            dupeLayout.setAlignment(Qt.AlignLeft)
            dupeLayout.setSpacing(0)
            dupeLayout.setContentsMargins(0, 0, 0, 0)
            buttons = widgets[2:]
            for b in buttons:
                # print ('dupeLayout', dupeLayout, b)
                dupeLayout.addWidget(b)
            blankLabel = QLabel('')
            blankLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
            dupeLayout.addWidget(blankLabel)
            dupeLayout.addStretch(100)
            customLayout = QHBoxLayout()
            customLayout.setSpacing(0)
            customLayout.setContentsMargins(0, 0, 0, 0)
            customLayout.setAlignment(Qt.AlignCenter)

            # ['AboveButtons', 'BelowButtons', 'BeforeButtons', 'AfterButtons', 'MenuBar']
            if currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[0]:
                tempLayout = QVBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.insertLayout(0, customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[1]:
                tempLayout = QVBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.addLayout(customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[2]:
                tempLayout = QHBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.insertLayout(0, customLayout)
            elif currentLocation == self.allTools.tools['GraphEditor'].customUiLocation[3]:
                tempLayout = QHBoxLayout()
                tempLayout.addLayout(dupeLayout)
                tempLayout.addLayout(customLayout)

            tempWidget.setLayout(tempLayout)
            w = QWidget()
            w.setLayout(sliderLayout)
            customLayout.addWidget(w)

            graphEditor1.__dict__['modified'] = True
            # print('graphEditor1', graphEditor1.__dict__['modified'])
        # except:
        #     return
    def resizeCornerWidget(self):
        graphEditor1 = wrapInstance(int(omUI.MQtUtil.findControl('graphEditor1')), QWidget)
        widgets = graphEditor1.children()
        for w in widgets:
            # print(str(w.__class__))
            if 'QMenuBar' in str(w.__class__):
                self.graphEdiMenuBar = w
        if self.graphEdiMenuBar:
            self.graphEdiMenuBar.adjustSize()

    def graphEditorMenu(self, menuName, *args):
        mode = self.getMoveKeyMode()
        cmds.popupMenu(menuName, edit=True, deleteAllItems=True)
        cmds.setParent(menuName, menu=True)
        cmds.menuItem('Key Move Mode', enable=False)
        cmds.menuItem(divider=True)

        constant = mode == 'constant'
        linear = mode == 'linear'
        power = mode == 'power'
        images = {True: 'checkboxOn.png', False: 'checkboxOff.png'}
        cmds.menuItem('Constant',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'constant'),
                      image=images[mode == 'constant'])
        cmds.menuItem('Linear',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'linear'),
                      image=images[mode == 'linear'])
        cmds.menuItem('Power',
                      parent=menuName,
                      command=partial(self.setMoveKeyMode, 'power'),
                      image=images[mode == 'power'])
        cmds.menuItem(parent=menuName,
                      divider=True)

    def getMoveKeyMode(self):
        mode = cmds.moveKeyCtx('moveKeyContext', query=True, moveFunction=True)
        return mode

    def setMoveKeyMode(self, mode, *args):
        cmds.moveKeyCtx('moveKeyContext', edit=True, moveFunction=mode)

    def setMoveKeyLinear(self):
        cmds.setToolTo('moveKeyContext')
        mel.eval("setToolTo $gMove;")
        self.setMoveKeyMode('linear')

    def setMoveKeyConstant(self):
        cmds.setToolTo('moveKeyContext')
        mel.eval("setToolTo $gMove;")
        self.setMoveKeyMode('constant')

    def setMoveKeyPower(self):
        mel.eval("setToolTo $gMove;")
        cmds.setToolTo('moveKeyContext')
        self.setMoveKeyMode('power')

class GraphEdToolbarWidget(QWidget):
    def __init__(self):
        super(GraphEdToolbarWidget, self).__init__()

    def resizeEvent(self, event):
        # print('GraphEdToolbarWidget resizeEvent')
        # Call the update method to repaint the QLabel when the parent UI is resized
        for wd in self.children():
            # print('resizeEvent', wd)
            wd.update()
        self.resize(self.sizeHint())

    def updateSize(self):
        self.resize(self.sizeHint())


class GraphEditorWidget(QWidget):
    pass
