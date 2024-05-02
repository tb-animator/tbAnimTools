from . import *

class hotKeyWidget(QWidget):
    label = None
    lineEdit = None
    assignSignal = Signal(str, str, bool, bool)

    def __init__(self, cls=None, command=str(), text=str(), tooltip=str(), placeholderTest=str()):
        super(hotKeyWidget, self).__init__()
        # print('self.command', command)
        self.command = command
        self.cls = cls
        niceCommandName = '{0}NameCommand'.format(command)
        existingData = self.cls.commandData.get(niceCommandName, {'key': str(),
                                                                  'ctrl': False,
                                                                  'alt': False,
                                                                  'Command': niceCommandName,
                                                                  'Release': False,
                                                                  'KeyRepeat': True
                                                                  })
        commandString = ''
        if existingData['key']:
            if existingData['ctrl']:
                commandString += 'Ctrl+'
            if existingData['alt']:
                commandString += 'Alt+'
            if existingData['key'].isupper():
                commandString += 'Shift+'
            commandString += existingData['key']
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel('Existing Hotkey')
        self.lineEdit = hotkeyLineEdit(commandString)
        self.lineEdit.keyPressed.connect(self.setLabelText)

        self.assignButton = QPushButton('Assign')
        self.toolButton = HotkeyToolButton(text='test',
                                           imgLabel=command,
                                           width=64,
                                           height=22,
                                           icon=":/pythonFamily.png",
                                           command=command)
        self.clipboardButton = QPushButton()
        self.clipboardButton.setIcon(QIcon(':/menuIconCopy.png'))
        self.clipboardButton.clicked.connect(self.copyText)
        pixmap = QPixmap(":/arrowDown.png")
        pixmap = pixmap.scaled(QSize(22, 22), Qt.KeepAspectRatio)

        icon = QIcon(pixmap)
        icon = QIcon(pixmap)
        self.cle_action_pick = self.lineEdit.addAction(icon, QLineEdit.TrailingPosition)
        # self.cle_action_clear = self.lineEdit.addAction(QIcon(":/hotkeyFieldClear.png"), QLineEdit.TrailingPosition)

        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.show_category_table_Popup)
        self._category_table_Popup = QMenu(self)
        self.recentAction = QAction('Recent Command List', self._category_table_Popup, checkable=True,
                                    checked=existingData['KeyRepeat'])
        self.onPressAction = QAction('On Press', self._category_table_Popup, checkable=True,
                                     checked=not existingData['Release'])
        self.onReleaseAction = QAction('On Release', self._category_table_Popup, checkable=True,
                                       checked=existingData['Release'])
        self._category_table_Popup.addAction(self.recentAction)
        self._category_table_Popup.addSeparator()
        self._category_table_Popup.addAction(self.onPressAction)
        self._category_table_Popup.addAction(self.onReleaseAction)

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.addAction(self.onPressAction)
        self.action_group.addAction(self.onReleaseAction)

        self.lineEdit.setPlaceholderText(placeholderTest)
        # self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        self.assignButton.clicked.connect(self.assinHotkey)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.assignButton)
        self.layout.addWidget(self.toolButton)
        self.layout.addWidget(self.clipboardButton)

        # self.label.setFixedWidth(60)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    def copyText(self):
        cmd = 'echo ' + self.command + '|clip'
        return subprocess.check_call(cmd, shell=True)

    @Slot()
    def setLabelText(self, text):
        self.lineEdit.setText(text)

    @Slot()
    def sendtextChangedSignal(self):
        # print ('sendtextChangedSignal', self.lineEdit.text())
        self.editedSignal.emit(self.command, self.lineEdit.text(), self.onPressAction.isChecked(),
                               self.recentAction.isChecked())

    @Slot()
    def assinHotkey(self):
        self.assignSignal.emit(self.command, self.lineEdit.text(), self.onPressAction.isChecked(),
                               self.recentAction.isChecked())

    @Slot()
    def show_category_table_Popup(self):
        '''
        Show Popup Menu on Category Table
        '''
        self._category_table_Popup.exec_(QCursor.pos())