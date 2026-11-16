from . import *

class TextInputDialog(BaseDialog):
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title=str, label=str, buttonText=str, default=str):
        super(TextInputDialog, self).__init__(parent=parent, title=title)
        self.setWindowTitle("TextInputDialog!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.addButton(buttonText, QDialogButtonBox.AcceptRole)
        # self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)

        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400 * dpiScale(), 180 * dpiScale())

        self.titleText.setAlignment(Qt.AlignCenter)
        self.lineEditLabel = QLabel('%s::' % label)
        self.lineEditLabel.setStyleSheet(getqss.getStyleSheet())
        self.lineEdit = QLineEdit(default)

        self.lineEditLayout = QHBoxLayout()
        self.lineEditLayout.addWidget(self.lineEditLabel)
        self.lineEditLayout.addWidget(self.lineEdit)
        self.mainLayout.addLayout(self.lineEditLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

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
        return super(TextInputDialog, self).keyPressEvent(event)


class TextOptionInputDialog(BaseDialog):
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title=str, label=str, buttonText=str, default=str, text='TextOptionInputDialog'):
        super(TextOptionInputDialog, self).__init__(parent=parent, title=title, text=text)
        self.setWindowTitle("TextInputDialog!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.selLayout = QHBoxLayout()
        self.footstepLayout = QHBoxLayout()
        self.layout.addLayout(self.selLayout)
        self.layout.addLayout(self.footstepLayout)

        self.AddSelectionLabel = QLabel('Add selection to sub path')
        self.AddSelectionCB = QCheckBox()
        self.AddSelectionCB.setChecked(True)
        self.UseFootstepsLabel = QLabel('Use footsteps (From first selection)')
        self.UseFootstepsCB = QCheckBox()
        self.UseFootstepsCB.setChecked(True)

        self.selLayout.addWidget(self.AddSelectionCB)
        self.selLayout.addWidget(self.AddSelectionLabel)
        self.selLayout.addStretch()
        self.footstepLayout.addWidget(self.UseFootstepsCB)
        self.footstepLayout.addWidget(self.UseFootstepsLabel)
        self.footstepLayout.addStretch()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.addButton(buttonText, QDialogButtonBox.AcceptRole)
        # self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)

        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400 * dpiScale(), 180 * dpiScale())

        self.titleText.setAlignment(Qt.AlignCenter)
        self.lineEditLabel = QLabel('%s::' % label)
        self.lineEditLabel.setStyleSheet(getqss.getStyleSheet())
        self.lineEdit = QLineEdit(default)

        self.lineEditLayout = QHBoxLayout()
        self.lineEditLayout.addWidget(self.lineEditLabel)
        self.lineEditLayout.addWidget(self.lineEdit)
        self.mainLayout.addLayout(self.lineEditLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

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
        return super(TextOptionInputDialog, self).keyPressEvent(event)

