from . import *

class LicenseWin(BaseDialog):
    ActivateSignal = Signal(str, str)
    OfflineActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title='Tool Name?', machineOnly=False,
                 infoText='Please enter your license key and email address used for this purchase'):
        super(LicenseWin, self).__init__(parent=parent)
        self.setWindowTitle("LicenseWin!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        if machineOnly:
            offlineButton = self.buttonBox.addButton("Offline Activate", QDialogButtonBox.ActionRole)
            offlineButton.clicked.connect(lambda: self.offlineActivate())
        self.buttonBox.addButton("Activate", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.activate)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(600, 300)
        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText(infoText)
        self.infoText.setWordWrap(True)

        self.titleText.setAlignment(Qt.AlignCenter)
        self.licenseKeyLabel = QLabel('License key::')
        self.licenseKeyLabel.setStyleSheet(getqss.getStyleSheet())
        self.licenseLineEdit = QLineEdit()
        self.emailLabel = QLabel('Email Address::')
        self.emailLabel.setStyleSheet(getqss.getStyleSheet())
        self.emailLineEdit = QLineEdit()

        # self.mainLayout.addWidget(self.titleText)
        # self.mainLayout.addWidget(self.infoText)
        self.gridLayout.addWidget(self.licenseKeyLabel, 0, 0)
        self.gridLayout.addWidget(self.licenseLineEdit, 0, 1)
        self.gridLayout.addWidget(self.emailLabel, 1, 0)
        self.gridLayout.addWidget(self.emailLineEdit, 1, 1)
        self.mainLayout.addLayout(self.gridLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None
        self.move(0,0)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            self.update()
            self.updateGeometry()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(LicenseWin, self).keyPressEvent(event)

    def activate(self):
        self.errorHighlightRemove(self.licenseLineEdit)
        self.errorHighlightRemove(self.emailLineEdit)
        if not len(self.licenseLineEdit.text()) == 35:
            return cmds.warning('Invalid length license key')
        if not '@' in self.emailLineEdit.text():
            return cmds.warning('Invalid email address')
        if not '.' in self.emailLineEdit.text():
            return cmds.warning('Invalid email address')
        self.ActivateSignal.emit(self.licenseLineEdit.text(), self.emailLineEdit.text())

    def offlineActivate(self):
        self.errorHighlightRemove(self.licenseLineEdit)
        self.errorHighlightRemove(self.emailLineEdit)
        if not len(self.licenseLineEdit.text()) == 35:
            self.errorHighlight(self.licenseLineEdit)
            return cmds.warning('Invalid length license key')
        if not '@' in self.emailLineEdit.text():
            self.errorHighlight(self.emailLineEdit)
            return cmds.warning('Invalid email address')
        if not '.' in self.emailLineEdit.text():
            self.errorHighlight(self.emailLineEdit)
            return cmds.warning('Invalid email address')
        self.OfflineActivateSignal.emit(self.licenseLineEdit.text(), self.emailLineEdit.text())

    def cancel(self):
        self.close()

    def errorHighlight(self, widget):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        widget.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

class OfflineActivateInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str, str, str)

    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title='Input activation code', label=str(), buttonText=str(), default=str(),
                 overlay=False, showCloseButton=True, licenseVal=str(), emailVal=str(),
                 productStr=str(),
                 helpString=None,
                 parentWidget=None,
                 lineEditPlaceholder=str(),
                 parent=getMainWindow()):
        super(OfflineActivateInputWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = licenseVal
        self.subKey = emailVal
        self.helpString = helpString
        self.overlay = overlay

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
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

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        productLineEditLayout = QHBoxLayout()

        self.productLineEdit = QLineEdit(productStr)
        self.productLineEdit.setReadOnly(True)
        self.productLineEdit.setFixedWidth(400)
        self.copyToCLipButton = QPushButton('Copy to clipboard')
        productLineEditLayout.addWidget(self.productLineEdit)
        productLineEditLayout.addWidget(self.copyToCLipButton)
        self.copyToCLipButton.clicked.connect(self.copyText)

        self.infoText = QLabel(
            'Copy the above text and email to to <b>tbanimtools@gmail.com</b> to get an offline activation code. <br>'
            'Make sure your email and license key are correct. <br><br>'
            'Once you get a response code, paste it into the box below')
        self.infoText.setWordWrap(True)
        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(productLineEditLayout)
        mainLayout.addWidget(self.infoText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)

        self.lineEdit = QLineEdit(default)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )

        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.productLineEdit.sizeHint().width() + 48, self.sizeHint().height())
        self.resize(self.sizeHint())
        self.setStyleSheet(getqss.getStyleSheet())
        # self.setFixedSize(400, 64)

    def copyText(self):
        cmd = 'echo ' + self.productLineEdit.text().strip() + '|clip'
        return subprocess.check_call(cmd, shell=True)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
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
        if not len(self.lineEdit.text()) == 8:
            return cmds.warning('Wrong length for activation code')
        self.acceptedSignal.emit(self.lineEdit.text(), self.key, self.subKey)

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(OfflineActivateInputWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(OfflineActivateInputWidget, self).keyPressEvent(event)

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
        super(OfflineActivateInputWidget, self).show()