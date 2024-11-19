from . import *

btnWidth = 80


class ToolTipWidget(QWidget):
    def __init__(self, tooltipTitle='', tooltip=''):
        super(ToolTipWidget, self).__init__()
        self.helpWidget = None
        self.helpWidget = InfoPromptWidget(title=tooltipTitle,
                                           buttonText='Ok',
                                           imagePath='',
                                           error=False,
                                           image='',
                                           gif='',
                                           helpString=tooltip,
                                           showCloseButton=False,
                                           show=False,
                                           showButton=False)
        self.setToolTipClass(self.helpWidget)

    def setToolTipClass(self, cls):
        if cls:
            self.helpWidget = cls
            self.installEventFilter(self)

    def showRelativeToolTip(self):
        if not self.helpWidget:
            return

        self.helpWidget.showRelative(screenPos=self.mapToGlobal(QPoint(0, 0)), widgetSize=self.size())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            self.showRelativeToolTip()
            return True
        return super(ToolTipWidget, self).eventFilter(obj, event)

    def enterEvent(self, event):
        if self.helpWidget:
            self.helpWidget.hide()
        return super(ToolTipWidget, self).enterEvent(event)

    def leaveEvent(self, event):
        if self.helpWidget:
            self.helpWidget.hide()
        return super(ToolTipWidget, self).leaveEvent(event)


class MiniDestinationWidget(ToolTipWidget):
    updatedSignal = Signal(list)

    def __init__(self, label='BLANK', tooltipTitle='title', tooltip='exampleTooltip'):
        super(MiniDestinationWidget, self).__init__(tooltipTitle=tooltipTitle, tooltip=tooltip)
        # self.setFixedWidth(140)
        self.setMaximumWidth(160)
        self.setMaximumHeight(150)
        self.mainListItem = str()

        self.controlsFrame = QFrame()

        self.controlsFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.mainLayout.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.label = QLabel(label)
        self.pickButton = SimpleIconButton(text='', icon=":/targetTransfoPlus.png", toolTip='Set selected controls as destination')

        self.hLayout = QHBoxLayout()
        self.vLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.controlsFrame)
        self.controlsFrame.setLayout(self.vLayout)
        self.vLayout.addLayout(self.hLayout)
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.hLayout.addWidget(self.label)
        self.hLayout.addWidget(self.pickButton)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        self.listwidget = QListWidget()
        self.listwidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listwidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vLayout.addWidget(self.listwidget)
        self.pickButton.clicked.connect(self.pickButtonPressed)

        # self.helpWidget = InfoPromptWidget(title=toolTip.get('title', 'toolTipText'),
        #                                    buttonText='Ok',
        #                                    imagePath='',
        #                                    error=False,
        #                                    image='',
        #                                    gif=toolTip.get('gif', ''),
        #                                    helpString=toolTip.get('text', 'toolTipText'),
        #                                    showCloseButton=False,
        #                                    show=False,
        #                                    showButton=False)

        self.resizeList()

    def currentItems(self):
        return [self.listwidget.item(x).text() for x in range(self.listwidget.count())]

    def getData(self):
        return self.currentItems()

    def recieveMainDestinationClicked(self, item):
        self.mainListItem = item

    @Slot()
    def sendUpdateSignal(self):
        self.updatedSignal.emit(self.currentItems())

    def pickButtonPressed(self, override=None):
        if not override:
            sel = cmds.ls(selection=True, type='transform')
        else:
            sel = override
        self.listwidget.clear()
        if sel:
            items = [stripNamespace(s) for s in sel]
            self.listwidget.addItems(items)

        self.sendUpdateSignal()

    def addButtonPressed(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return
        items = [stripNamespace(s) for s in sel]
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

    def refreshUI(self, targets):
        self.listwidget.clear()
        self.listwidget.addItems(targets)
        self.resizeList()

    def resizeList(self):
        if self.listwidget.count():
            self.listwidget.setFixedHeight(
                self.listwidget.sizeHintForRow(0) * self.listwidget.count() + 2 * self.listwidget.frameWidth() * dpiScale())
        else:
            self.listwidget.setFixedHeight(22 * dpiScale())


class PickwalkLabelledLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)

    def __init__(self, text=str, hasButton=False, buttonLabel=str, obj=False):
        super(PickwalkLabelledLineEdit, self).__init__()
        self.obj = obj

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        self.button = StandardPickButton(label=buttonLabel, direction='left', icon='timeend.png', rotation=0)
        self.button.setFixedWidth(80 * dpiScale())
        if self.obj:
            self.button.clicked.connect(self.pickObject)
        else:
            self.button.clicked.connect(self.pickChannel)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        if hasButton:
            self.layout.addWidget(self.button)
        self.label.setFixedWidth(60 * dpiScale())
        # elf.lineEdit.setFixedWidth(200)
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())

    def pickChannel(self, *args):
        # print ('picking channel')
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            cmds.warning('no channel selected')
        self.lineEdit.setText(channels[0].split(':')[-1])
        self.sendtextChangedSignal()

    def pickObject(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning('no object selected')
        self.lineEdit.setText(sel[0].split(':')[-1] + '_in')


class PickwalkLabelledDoubleSpinBox(ToolTipWidget):
    editedSignal = Signal(float)

    def __init__(self, text=str, helpLine=None, labelWidth=60, tooltipTitle='', tooltip=''):
        super(PickwalkLabelledDoubleSpinBox, self).__init__(tooltipTitle=tooltipTitle, tooltip=tooltip)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.spinBox = QDoubleSpinBox()
        # self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        self.spinBox.setValue(0.5)
        self.spinBox.setSingleStep(0.1)
        self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinBox)

        self.label.setFixedWidth(labelWidth * dpiScale())
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        if helpLine:
            self.help = QLabel(helpLine)
            self.layout.addWidget(self.help)
            self.help.setStyleSheet("QFrame {"
                                    "border-width: 0;"
                                    "border-radius: 0;"
                                    "border-style: solid;"
                                    "border-color: #222222}"
                                    )
            self.layout.addStretch()

    @Slot()
    def sendValueChangedSignal(self):
        self.editedSignal.emit(self.spinBox.value())

    def setValue(self, value):
        self.blockSignals(True)
        self.spinBox.setValue(value)
        self.blockSignals(False)

    def getData(self):
        return self.spinBox.value()


class PickObjectLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)

    def __init__(self, text=str, tooltip=str(), placeholderTest=str()):
        super(PickObjectLineEdit, self).__init__()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(tooltip)
        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        self.label.setFixedWidth(60 * dpiScale())

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())

    def setText(self, value):
        self.blockSignals(True)
        self.lineEdit.setText(value)
        self.blockSignals(False)

    def pickChannel(self, *args):
        # print ('picking channel')
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            cmds.warning('no channel selected')
        self.lineEdit.setText(channels[0].split(':')[-1])


class PickChannelLineEdit(ToolTipWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)

    def __init__(self, text=str, tooltipTitle='title', tooltip='exampleTooltip', placeholderTest=str()):
        super(PickChannelLineEdit, self).__init__(tooltipTitle=tooltipTitle, tooltip=tooltip)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)

        self.cle_action_pick.triggered.connect(self.pickChannel)
        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        self.label.setFixedWidth(60 * dpiScale())

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())

    def setText(self, value):
        self.blockSignals(True)
        self.lineEdit.setText(value)
        self.blockSignals(False)

    def pickChannel(self):
        # print ('picking channel')
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            cmds.warning('no channel selected')
        self.lineEdit.setText(channels[0].split(':')[-1])
        self.sendtextChangedSignal()

    def getData(self):
        return self.lineEdit.text()


class StandardPickButton(QPushButton):
    pressedSignal = Signal(str)
    direction = str()

    def __init__(self, label=str, direction=str, icon=str(), fixedWidth=False, width=64, rotation=0, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setText(label)
        self.direction = direction
        if fixedWidth:
            self.setFixedWidth(width * dpiScale())
        upRotate = QTransform().rotate(rotation)
        pixmap = QPixmap(':/{}'.format(icon)).transformed(upRotate)
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.clicked.connect(partial(self.pressedSignal.emit, self.direction))


class PickwalkDestinationWidget(QFrame):
    pressedSignal = Signal(str, str)
    conditionPressedSignal = Signal(str, str)
    direction = str()
    walkInfoSignal = Signal(str, dict)
    destinationDoubleClickSignal = Signal(str)

    def __init__(self, mainWindow, loop=False, endOnSelf=False, label=str, direction=str, icon=str(), fixedWidth=False,
                 rotation=0,
                 *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainWindow = mainWindow
        self.direction = direction
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 4, 0, 4)
        self.setLayout(self.mainLayout)
        self.label = QLabel(label)
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        self.label.setFixedWidth(64 * dpiScale())
        self.label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.mainLayout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.lineEdit = QLineEdit()

        self.attrLayout = QVBoxLayout()

        # new stuff
        self.destinationsWidget = MiniDestinationWidget(label='Destinations', tooltipTitle='Walk destination',
                                                        tooltip='Pick your destination control(s) for the current control\n'
                                                                'Use the button above to use your selection')

        self.altDestinationsWidget = MiniDestinationWidget(label='Alt Destinations',
                                                           tooltipTitle='Walk destination (conditional)',
                                                           tooltip='Pick your destination control(s) for the current control, if the selected attribute is greater than the value specified, the walk will choose a control from this list')
        self.conditionAttrWidget = PickChannelLineEdit(text='Attribute',
                                                       tooltipTitle='Conditional attribute',
                                                       tooltip='Pick attribute to control pickwalk. If the selected attribute is greater than the value specified, the alternate destination will be walked to.',
                                                       placeholderTest='enter condition attribute')
        self.conditionValueWidget = PickwalkLabelledDoubleSpinBox(text='Value',
                                                                  tooltipTitle='Conditional attribute threshold',
                                                                  tooltip='If the selected attribute is greater than the value specified here, the alternate destination will be walked to.',
                                                                  helpLine='')

        self.button = StandardPickButton(label='from sel', direction=direction, icon=icon,
                                         rotation=rotation, width=32, fixedWidth=False)

        self.destinationsWidget.listwidget.itemDoubleClicked.connect(self.setActiveObjectFromDestination)
        self.altDestinationsWidget.listwidget.itemDoubleClicked.connect(self.setActiveObjectFromDestination)


        self.contextButton = QPushButton('< from destination list')
        self.mainLayout.addWidget(self.label)
        # self.mainLayout.addWidget(self.lineEdit)
        self.mainLayout.addWidget(self.destinationsWidget)
        self.attrLayout.addWidget(self.conditionAttrWidget)
        self.attrLayout.addWidget(self.conditionValueWidget)
        spacer = QSpacerItem(60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.attrLayout.addItem(spacer)
        self.mainLayout.addLayout(self.attrLayout)
        self.mainLayout.addWidget(self.altDestinationsWidget)
        self.mainLayout.addWidget(self.contextButton)

        self.contextButton.clicked.connect(partial(self.conditionPressedSignal.emit,
                                                   self.lineEdit.text(),
                                                   self.direction,
                                                   ))
        self.label.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        self.button.clicked.connect(self.pickControl)
        self.conditionAttrWidget.editedSignal.connect(self.pickAttribute)
        self.contextButton.clicked.connect(self.pickDestination)
        self.conditionValueWidget.editedSignal.connect(self.sendData)
        self.destinationsWidget.updatedSignal.connect(self.sendData)
        self.altDestinationsWidget.updatedSignal.connect(self.sendData)

    def setActiveObjectFromDestination(self, item):
        self.destinationDoubleClickSignal.emit(item.text())

    def pickControl(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            lbl = ''
        if len(sel) > 1:
            cmds.warning('need to make this support auto creation of contexts')
            lbl = ''
        else:
            lbl = stripNamespace(sel[0])
        self.lineEdit.setText(lbl)
        self.sendData()

    def pickAttribute(self, attr):
        # print ('pickAttribute', attr)
        if attr:
            self.setSimple(False)
        else:
            self.setSimple(True)
        self.sendData()

    def pickDestination(self):
        self.lineEdit.setText(self.mainWindow.currentDestination)

    def sendPickedSignal(self):
        self.pressedSignal.emit(self.lineEdit.text(), self.direction)

    def setValues(self, data):
        # print('data', data)

        if data.destination:
            self.destinationsWidget.refreshUI(data.destination)
        if data.destinationAlt:
            self.altDestinationsWidget.refreshUI(data.destinationAlt)
        else:
            self.altDestinationsWidget.refreshUI(list())
        if data.conditionAttribute:
            self.conditionAttrWidget.setText(data.conditionAttribute)
            self.setSimple(False)
        else:
            self.setSimple(True)
            self.conditionAttrWidget.setText('')
        if data.conditionValue:
            self.conditionValueWidget.setValue(data.conditionValue)

    def setSimple(self, state):
        self.altDestinationsWidget.setHidden(state)
        self.conditionValueWidget.setHidden(state)

    def sendData(self, *args):
        outDict = {'destination': self.destinationsWidget.getData(),
                   'destinationAlt': self.altDestinationsWidget.getData(),
                   'conditionAttribute': self.conditionAttrWidget.getData(),
                   'conditionValue': self.conditionValueWidget.getData(),
                   }
        # print ("sending data")
        # print (outDict)
        self.walkInfoSignal.emit(self.direction, outDict)


class PickObjectWidget(QWidget):
    setActiveObjectSignal = Signal()
    modeChangedSignal = Signal(bool)
    lockChangedSignal = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(PickObjectWidget, self).__init__(parent=getMainWindow())
        self.mainLayout = QHBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.pickBtn = ToolTipPushButton('Pick Current', tooltipTitle='Set current control', tooltip='Set the currently edited control from your scene selection.')
        self.pickBtn.setFixedHeight(dpiScale() * 22)
        self.pickBtn.setStyleSheet('background-color:green;')
        self.pickBtn.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #52bf90, stop: 0.1 #49ab81, stop: 0.5 #419873, stop: 0.9 #398564, stop: 1 #317256);color: 	#3b2f2f;font-weight: bold; font-size: 14px;')

        self.ObjLabel = Header('Current Control ::')

        self.currentObjLabel = Header('None')
        self.mainLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(self.ObjLabel)
        self.infoLayout.addWidget(self.currentObjLabel)
        # self.mainLayout.addWidget(self.centre)
        self.mainLayout.addWidget(self.pickBtn)
        # self.mainLayout.addWidget(self.modeBtn)

        self.pickBtn.clicked.connect(self.pickButtonPress)

    @Slot()
    def pickButtonPress(self):
        self.setActiveObjectSignal.emit()

    @Slot()
    def sendModeChangedSignal(self):
        # self.modeChangedSignal.emit(self.modeBtn.isChecked())
        self.modeChangedSignal.emit(True)
        self.changeState()


class PickwalkQueryWidget(QDialog):
    AssignNewRigSignal = Signal(str)
    CreateNewRigMapSignal = Signal(str)
    IgnoreRigSignal = Signal(str)

    def __init__(self, parent=None, title='title?', rigName=str(), text='message?',
                 assignText='Assign existing map',
                 createText='Create new map',
                 ignoreText='Ignore',
                 cancelText='Cancel',
                 ):
        super(PickwalkQueryWidget, self).__init__(parent=parent)
        self.rigName = rigName
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Ignore | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # self.layout = QVBoxLayout()
        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.layout)

        # self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(400 * dpiScale(), 120 * dpiScale())
        mainLayout = QVBoxLayout()
        layout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(text)
        self.text.setStyleSheet(getqss.getStyleSheet())

        self.assignExistingButton = QPushButton(assignText)
        self.assignExistingButton.setStyleSheet(getqss.getStyleSheet())

        self.createButton = QPushButton(createText)
        self.createButton.setStyleSheet(getqss.getStyleSheet())

        self.ignoreButton = QPushButton(ignoreText)
        self.ignoreButton.setStyleSheet(getqss.getStyleSheet())

        self.cancelButton = QPushButton(cancelText)
        self.cancelButton.setStyleSheet(getqss.getStyleSheet())

        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignExistingButton)
        buttonLayout.addWidget(self.createButton)
        buttonLayout.addWidget(self.ignoreButton)
        buttonLayout.addWidget(self.cancelButton)

        self.assignExistingButton.clicked.connect(self.assignNewRig)
        self.createButton.clicked.connect(self.createNewRigMap)
        self.ignoreButton.clicked.connect(self.ignoreRigMap)
        self.cancelButton.clicked.connect(self.close)

        self.setLayout(mainLayout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(QPainter.CompositionMode_Clear)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2 * dpiScale()))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16 * dpiScale(), 16 * dpiScale())
        qp.end()

    def assignNewRig(self, *args):
        self.AssignNewRigSignal.emit(self.rigName)
        self.close()

    def createNewRigMap(self, *args):
        self.CreateNewRigMapSignal.emit(self.rigName)
        self.close()

    def ignoreRigMap(self, *args):
        self.IgnoreRigSignal.emit(self.rigName)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(PickwalkQueryWidget, self).keyPressEvent(event)
