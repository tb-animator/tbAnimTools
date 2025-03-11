from . import *

class BaseDialog(QDialog):
    widgetClosed = Signal()
    oldPos = None

    def __init__(self, parent=None, title='', text='',
                 lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, showHelpButton=False,
                 *args, **kwargs):
        super(BaseDialog, self).__init__(parent=parent)
        self.stylesheet = getqss.getStyleSheet()
        self.setStyleSheet(self.stylesheet)
        self.lockState = lockState
        self.showHelpButton = showHelpButton
        self.showLockButton = showLockButton
        self.showCloseButton = showCloseButton
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setFixedSize(400 * dpiScale(), 120 * dpiScale())
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(margin, margin, margin, margin)
        self.layout = QVBoxLayout()
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.helpButton = HelpButton(toolTip='Help', width=14 * dpiScale(), height=14 * dpiScale())
        self.pinButton = LockButton('', None, lockState=self.lockState)
        self.pinButton.lockSignal.connect(self.togglePinState)
        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)
        self.titleText = QLabel(title)
        # self.titleText.setFont(QFont('Lucida Console', 12))
        # self.titleText.setStyleSheet("font-weight: lighter; font-size: 12px;")
        # self.titleText.setStyleSheet("background-color: rgba(255, 0, 0, 0);")
        # self.titleText.setStyleSheet("QLabel {"
        #                              "border-width: 0;"
        #                              "border-radius: 4;"
        #                              "border-style: solid;"
        #                              "border-color: #222222;"
        #                              "font-weight: bold; font-size: 12px;"
        #                              "}"
        #                              )

        self.titleText.setAlignment(Qt.AlignCenter)
        self.infoText = QLabel(text)
        if not showInfo: self.infoText.hide()

        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleText, alignment=Qt.AlignCenter)
        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.helpButton, alignment=Qt.AlignRight)
        self.titleLayout.addWidget(self.pinButton, alignment=Qt.AlignRight)
        self.titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

        self.mainLayout.addLayout(self.titleLayout)
        self.infoText.setStyleSheet(self.stylesheet)
        self.layout.addWidget(self.infoText)

        self.mainLayout.addLayout(self.layout)
        self.setLayout(self.mainLayout)

        self.pinButton.setVisible(self.showLockButton)
        self.helpButton.setVisible(self.showHelpButton)
        self.closeButton.setVisible(self.showCloseButton)

    def showEvent(self, event):
        super(BaseDialog, self).showEvent(event)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()


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
        qp.drawRoundedRect(self.rect(), 8 * dpiScale(), 8 * dpiScale())
        qp.end()

    def keyReleaseEvent(self, event):
        # print ('base dialog keyReleaseEvent')
        if event.key() == Qt.Key_Control:
            self.controlKeyPressed = False
        return False

    def keyPressEvent(self, event):
        # print ('base dialog keyPressEvent', event)
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Control:
            self.controlKeyPressed = True
        return super(BaseDialog, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.lockState and not modifiers == Qt.ControlModifier:
            return
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.lockState and not modifiers == Qt.ControlModifier:
            return
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            opacity = self.windowOpacity()
            opacity += event.delta() * 0.001
            opacity = min(max(opacity, 0.2), 1)
            self.setWindowOpacity(opacity)
        # cmds.warning(self.x(), event.delta() / 120.0 * 25)
        # self.setValue(self.value() + event.delta() / 120.0 * 25)
        # super(PySlider, self).wheelEvent(event)
        # self.wheelSignal.emit(self.value())

    def togglePinState(self, pinState):
        self.lockState = pinState
        self.closeButton.setVisible(True)

    def close(self):
        # print ('widget closed')
        self.widgetClosed.emit()
        super(BaseDialog, self).close()

