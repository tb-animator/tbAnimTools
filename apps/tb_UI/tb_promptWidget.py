from . import *

class promptWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self, title=str(), text=str(), defaultInput=str(), buttonText=str()):
        super(promptWidget, self).__init__(parent=getMainWindow())
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(text)
        self.lineEdit = QLineEdit(defaultInput)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_]")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        self.confirmButton = QPushButton(buttonText)
        self.confirmButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.confirmButton)

        self.confirmButton.clicked.connect(self.confirm)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()

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

    def confirm(self, *args):
        self.saveSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(promptWidget, self).keyPressEvent(event)

class InfoPromptWidget(QWidget):
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
                 helpString=None,
                 image=str(),
                 imagePath=IconPath,
                 gif=bool,
                 info=False,
                 error=False,
                 parent=getMainWindow(),
                 show=True,
                 showButton=True):
        super(InfoPromptWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.info = info
        self.error = error
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())
        self.checkBox = checkBox
        self.combo = combo
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

        sel = pm.ls(sl=True)

        if image:
            self.imageLabel = QLabel(self)
            if gif:
                self.movie = QMovie(os.path.join(imagePath, image))

                self.imageLabel.setMovie(self.movie)
                self.movie.start()

            else:
                self.imagePixmap = QPixmap(os.path.join(imagePath, image))
                self.imageLabel.setPixmap(self.imagePixmap)

        self.titleText = QLabel(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit(default)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        self.checkBoxWD = QCheckBox()
        self.checkBoxWD.setText(self.checkBox)

        self.comboBox = QComboBox()
        for c in self.combo:
            self.comboBox.addItem(c)
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())

        # layout.addWidget(btnSetFolder)

        self.helpLabel = QLabel(self.helpString)
        self.helpLabel.setWordWrap(True)

        titleLayout.addWidget(self.titleText)

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)
        # layout.addWidget(self.text)
        # layout.addWidget(self.lineEdit)
        if len(self.combo):
            layout.addWidget(self.comboBox)
        if self.checkBox is not None:
            layout.addWidget(self.checkBoxWD)

        if self.helpString:
            mainLayout.addWidget(self.helpLabel)
        if image:
            mainLayout.addWidget(self.imageLabel)
        if showButton:
            self.saveButton = QPushButton(buttonText)
            self.saveButton.setStyleSheet(getqss.getStyleSheet())
            self.saveButton.clicked.connect(self.acceptedFunction)
            mainLayout.addWidget(self.saveButton)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        self.lineEdit.setFocus()
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
        # self.setFixedSize(400, 64)
        if show:
            self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        if self.info:
            lineColor = QColor(255, 160, 47, 128)
        elif self.error:
            lineColor = QColor(240, 68, 68, 128)
        else:
            lineColor = QColor(68, 240, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2 * dpiScale()))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8 * dpiScale(), 8 * dpiScale())
        qp.end()

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedComboSignal.emit(self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeyComboSignal.emit(self.key, self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeySubComboSignal.emit(self.key, self.lineEdit.text(), self.subKey)
        self.acceptedCBSignal.emit(self.lineEdit.text(), self.checkBoxWD.isChecked())
        self.close()

    def showRelative(self, screenPos=QPoint(0, 0), widgetSize=QPoint(0, 0)):

        screens = QApplication.screens()
        for s in screens:
            if s.availableGeometry().contains(QCursor.pos()):
                screen = s

        screenGeo = screen.availableGeometry()
        screenGeo.width()
        screenGeo.height()
        finalPos = QPoint(0, 0)

        if screenPos.y() + widgetSize.height() + self.height() > screenGeo.height():
            finalPos.setY(screenPos.y() - self.height())
        else:
            finalPos.setY(screenPos.y() + widgetSize.height())

        if screenPos.x() + widgetSize.width() + self.width() > screenGeo.width():
            finalPos.setX(screenPos.x() + widgetSize.width() - self.width())
        else:
            finalPos.setX(screenPos.x())

        self.move(finalPos)
        self.show(auto=False)

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(InfoPromptWidget, self).close()
        self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(InfoPromptWidget, self).keyPressEvent(event)

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

    def show(self, auto=True):
        if auto:
            position_x = (self.parent().pos().x() + (self.parent().width() - self.frameGeometry().width()) / 2)
            position_y = (self.parent().pos().y() + (self.parent().height() - self.frameGeometry().height()) / 2)

            self.move(position_x, position_y)
        super(InfoPromptWidget, self).show()


def raiseOk(errorMessage, title='Success'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              error=False,
                              # image='curves.png',
                              helpString=errorMessage)


def raiseError(errorMessage, title='Failed'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              error=True,
                              helpString=errorMessage)
    return False