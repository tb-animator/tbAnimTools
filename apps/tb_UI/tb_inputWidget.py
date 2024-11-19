from . import *

class TextInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedComboSignal = Signal(str, str)
    acceptedKeyComboSignal = Signal(str, str, str)
    acceptedKeySubComboSignal = Signal(str, str, str)
    acceptedCBSignal = Signal(str, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText=str(), default=str(), combo=list(),
                 checkBox=None, overlay=False, showCloseButton=True, key=str(), subKey=str(),
                 objectLineEdit=False,
                 helpString=None,
                 parentWidget=None,
                 lineEditPlaceholder=str(),
                 parent=getMainWindow()):
        super(TextInputWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())
        self.checkBox = checkBox
        self.combo = combo
        self.setWindowOpacity(1.0)
        #Qt.PopupFocusReason |
        self.setWindowFlags( Qt.Popup | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = cmds.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        self.checkBoxWD = QCheckBox()
        self.checkBoxWD.setText(self.checkBox)

        self.comboBox = QComboBox()
        for c in self.combo:
            self.comboBox.addItem(c)
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width() + (32 * dpiScale()))

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)

        if objectLineEdit:
            objLineEdit = ObjectSelectLineEdit(stripNamespace=True, placeholderTest=lineEditPlaceholder)
            self.lineEdit = objLineEdit.itemLabel
            layout.addWidget(objLineEdit)
        else:
            self.lineEdit = QLineEdit(default)
            self.lineEdit.setFocusPolicy(Qt.StrongFocus)
            reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
            input_validator = QRegExpValidator(reg_ex, self.lineEdit)
            self.lineEdit.setValidator(input_validator)

            layout.addWidget(self.lineEdit)
        if len(self.combo):
            layout.addWidget(self.comboBox)
        if self.checkBox is not None:
            layout.addWidget(self.checkBoxWD)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        # self.move(getScreenCenter() - self.rect().center())

        self.lineEdit.setFocus()
        self.lineEdit.setFixedWidth(self.lineEdit.fontMetrics().boundingRect(self.lineEdit.text()).width() + (16 * dpiScale()))
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        width = self.comboBox.minimumSizeHint().width()
        self.comboBox.view().setMinimumWidth(width)
        self.comboBox.setMinimumWidth(width)
        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.sizeHint())

        self.show()
        # self.setFixedSize(400, 64)

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

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedComboSignal.emit(self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeyComboSignal.emit(self.key, self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeySubComboSignal.emit(self.key, self.lineEdit.text(), self.subKey)
        self.acceptedCBSignal.emit(self.lineEdit.text(), self.checkBoxWD.isChecked())
        self.close()

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(TextInputWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(TextInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        if self.overlay:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def show(self):
        position_x = (self.parent().pos().x() + (self.parent().width() - self.frameGeometry().width()) / 2)
        position_y = (self.parent().pos().y() + (self.parent().height() - self.frameGeometry().height()) / 2)

        self.move(position_x, position_y)
        super(TextInputWidget, self).show()





class ChannelInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(ChannelInputWidget, self).__init__(parent=getMainWindow())
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300 * dpiScale(), 64 * dpiScale())
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = cmds.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will replace your current path.')
        self.lineEdit.setPlaceholderText(default)
        self.cle_action_pick.triggered.connect(self.pickChannel)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(getScreenCenter() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        self.pickChannel()

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

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return cmds.warning('no channel selected')
        self.lineEdit.setText(channels[0].rsplit('.', 1)[-1])

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(ChannelInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class IntInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(int)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(IntInputWidget, self).__init__(parent=getMainWindow())
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = cmds.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = intFieldWidget(optionVar=None,
                                       defaultValue=1,
                                       minimum=1, maximum=100, step=1)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(getScreenCenter() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        # self.setFixedSize(self.sizeHint())

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

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.spinBox.value())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(IntInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class ObjectInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedDataSignal = Signal(str, list)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept", data=None,
                 objectType='nurbsCurve'):
        super(ObjectInputWidget, self).__init__(parent=getMainWindow())
        self.setStyleSheet(getqss.getStyleSheet())
        self.data = data
        self.objectType = objectType
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300 * dpiScale(), 64 * dpiScale())
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = cmds.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will replace your current path.')
        self.lineEdit.setPlaceholderText(default)
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(getScreenCenter() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )

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

    def pickObject(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return

        if self.objectType == "nurbsCurve":
            shape = sel[0].getShape()
            if not shape:
                return
            if cmds.nodeType(shape) == "nurbsCurve":
                self.lineEdit.setText(str(sel[0]))
        elif self.objectType == "nurbsSurface":
            shape = sel[0].getShape()
            if not shape:
                return
            if cmds.nodeType(shape) == "nurbsSurface":
                self.lineEdit.setText(str(sel[0]))
        elif self.objectType == "transform":
            if not cmds.objectType(str(sel[0])) == 'transform':
                return
            self.lineEdit.setText(str(sel[0]))

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedDataSignal.emit(self.lineEdit.text(), self.data)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(ObjectInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None
