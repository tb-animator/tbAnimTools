from . import *


class hotkeyLineEdit(QLineEdit):
    keyPressed = Signal(str)

    def keyPressEvent(self, event):
        keyname = ''
        key = event.key()
        modifiers = int(event.modifiers())
        if (modifiers and modifiers & MOD_MASK == modifiers and
                key > 0 and key != Qt.Key_Shift and key != Qt.Key_Alt and
                key != Qt.Key_Control and key != Qt.Key_Meta):

            keyname = QKeySequence(modifiers + key).toString()

            # print('event.text(): %r' % event.text())
            # print('event.key(): %d, %#x, %s' % (key, key, keyname))
        elif (key > 0 and key != Qt.Key_Shift and key != Qt.Key_Alt and
              key != Qt.Key_Control and key != Qt.Key_Meta):
            keyname = QKeySequence(key).toString()
            # print('event.text(): %r' % event.text())
        self.keyPressed.emit(keyname)


class ObjectSelectLineEdit(QWidget):
    pickedSignal = Signal(str)
    editedSignalKey = Signal(str, str)
    editedSignalKeyList = Signal(str, list)

    def __init__(self, key=str(), label=str(), hint=str(), labelWidth=65, lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False,
                 lineEditStretches=False,
                 isMultiple=False,
                 tooltip=str()):
        QWidget.__init__(self)
        self.isMultiple = isMultiple
        self.key = key
        self.stripNamespace = stripNamespace
        self.lineEditStretches = lineEditStretches
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.mainLayout)
        self.label = QLabel(label)
        # self.label.setFixedWidth(labelWidth)
        self.itemLabel = QLineEdit()
        self.itemLabel.setPlaceholderText(placeholderTest)
        if not self.lineEditStretches:
            self.itemLabel.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(hint)
        self.cle_action_pick.triggered.connect(self.pickObject)
        self.itemLabel.textChanged.connect(self.textEdited)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.itemLabel)

    def pickObject(self):
        # print ('pickObject')
        sel = pm.ls(sl=True)
        objectList = list()
        if not sel:
            return
        if self.isMultiple:
            if self.stripNamespace:
                objectList = [str(x).split(':', 1)[-1] for x in sel]
                s = ' '.join(objectList)
            else:
                objectList = [str(x) for x in sel]
                s = ' '.join(objectList)
        else:
            if self.stripNamespace:
                s = str(sel[0]).split(':', 1)[-1]
            else:
                s = str(sel[0])
        self.itemLabel.setText(s)
        self.pickedSignal.emit(s)
        self.editedSignalKeyList.emit(self.key, objectList)
        # self.editedSignalKey.emit(self.key, str(sel[0]))

    def setTextNoUpdate(self, text):
        self.blockSignals(True)
        self.itemLabel.setText(text)
        self.blockSignals(False)

    @Slot()
    def textEdited(self):
        self.editedSignalKey.emit(self.key, self.itemLabel.text())

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 1px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.itemLabel.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.itemLabel.setStyleSheet(getqss.getStyleSheet())


class ObjectSelectLineEditNoLabel(QLineEdit):
    pickedSignal = Signal(str)
    editedSignalKey = Signal(str, str)
    editedSignalKeyList = Signal(str, list)

    def __init__(self, key=str(), hint=str(), lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False,
                 lineEditStretches=True,
                 isMultiple=False,
                 tooltip=str()):
        QLineEdit.__init__(self)
        self.isMultiple = isMultiple
        self.key = key
        self.stripNamespace = stripNamespace
        self.lineEditStretches = lineEditStretches
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.mainLayout)

        # self.label.setFixedWidth(labelWidth)

        self.setPlaceholderText(placeholderTest)
        if not self.lineEditStretches:
            self.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(hint)
        self.cle_action_pick.triggered.connect(self.pickObject)
        self.textChanged.connect(self.textEdited)

    def pickObject(self):
        # print ('pickObject')
        sel = pm.ls(sl=True)
        objectList = list()
        if not sel:
            return
        if self.isMultiple:
            if self.stripNamespace:
                objectList = [str(x).split(':', 1)[-1] for x in sel]
                s = ' '.join(objectList)
            else:
                objectList = [str(x) for x in sel]
                s = ' '.join(objectList)
        else:
            if self.stripNamespace:
                s = str(sel[0]).split(':', 1)[-1]
            else:
                s = str(sel[0])
        self.setText(s)
        self.pickedSignal.emit(s)
        self.editedSignalKeyList.emit(self.key, objectList)
        # self.editedSignalKey.emit(self.key, str(sel[0]))

    def setTextNoUpdate(self, text):
        self.blockSignals(True)
        self.itemLabel.setText(text)
        self.blockSignals(False)

    @Slot()
    def textEdited(self):
        self.editedSignalKey.emit(self.key, self.text())

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 1px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.itemLabel.setStyleSheet(getqss.getStyleSheet())


class ObjectSelectLineEditEnforced(ObjectSelectLineEdit):
    def __init__(self, key=str(), label=str(), hint=str(), labelWidth=65, lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False,
                 baseNamespace=str(),
                 lineEditStretches=False,
                 tooltip=str()):
        super(ObjectSelectLineEditEnforced, self).__init__(key=key, label=label, hint=hint, labelWidth=labelWidth,
                                                           lineEditWidth=lineEditWidth, placeholderTest=placeholderTest,
                                                           stripNamespace=stripNamespace,
                                                           lineEditStretches=lineEditStretches,
                                                           tooltip=tooltip)
        self.baseNamespace = baseNamespace
        self.itemLabel.textChanged.connect(self.validateText)

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.itemLabel.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.itemLabel.setStyleSheet(getqss.getStyleSheet())

    def validateText(self):
        if not cmds.objExists(self.baseNamespace + ':' + self.itemLabel.text()):
            self.errorHighlight()
        else:
            self.errorHighlightRemove()


class ChannelSelectLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), text=str, tooltip=str(), lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False):
        super(ChannelSelectLineEdit, self).__init__()
        self.stripNamespace = stripNamespace
        self.key = key
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignLeft)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.pickChannel)
        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        if text:
            self.mainLayout.addWidget(self.label)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.lineEdit)

        if text:
            self.label.setFixedWidth(60)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return pm.warning('no channel selected')
        refState = cmds.referenceQuery(channels[0].split('.')[0], isNodeReferenced=True)

        if refState:
            refNamespace = cmds.referenceQuery(channels[0].split('.')[0], namespace=True)
            if not self.stripNamespace:
                if refNamespace.startswith(':'):
                    refNamespace = refNamespace[1:]
                channel = channels[0]
                channel = channel.replace(refNamespace, '')
                if channel.startswith(':'):
                    channel = channel[1:]
                self.lineEdit.setText(channel)
            else:
                self.lineEdit.setText(channels[0].rsplit(':', 1)[-1])
        else:
            self.lineEdit.setText(channels[0])

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())
        self.editedSignalKey.emit(self.key, self.lineEdit.text())


class ChannelSelectLineEditEnforced(ChannelSelectLineEdit):
    def __init__(self, key=str(), text=str(), tooltip=str(), lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False, baseNamespace=str()):
        super(ChannelSelectLineEditEnforced, self).__init__(key=key,
                                                            text=text,
                                                            tooltip=tooltip,
                                                            lineEditWidth=lineEditWidth,
                                                            placeholderTest=placeholderTest,
                                                            stripNamespace=stripNamespace)

        self.baseNamespace = baseNamespace
        self.lineEdit.textChanged.connect(self.validateText)

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.lineEdit.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.lineEdit.setStyleSheet(getqss.getStyleSheet())

    def validateText(self):
        if not '.' in self.lineEdit.text():
            self.errorHighlight()
            return
        node, attr = str(self.baseNamespace + ':' + self.lineEdit.text()).split('.')
        if not cmds.objExists(node):
            self.errorHighlight()
            return
        if not cmds.attributeQuery(attr, node=node, exists=True):
            self.errorHighlight()
        else:
            self.errorHighlightRemove()
