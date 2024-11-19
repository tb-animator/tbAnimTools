from . import *

class UpdateWin(BaseDialog):
    ActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None,
                 title='tbAnimTools Update Found',
                 newVersion=str(),
                 oldVersion=str(),
                 updateText=str()):
        super(UpdateWin, self).__init__(parent=parent)
        self.setWindowTitle(title)

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.addButton("Update To Latest", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400 * dpiScale(), 180 * dpiScale())
        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 14px;");
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText(updateText)
        self.infoText.setWordWrap(True)

        self.currentVersionLabel = QLabel('Current Version')
        self.currentVersionInfoText = QLabel(oldVersion)
        self.latestVersionLabel = QLabel('Latest Version')
        self.latestVersionInfoText = QLabel(newVersion)

        # self.mainLayout.addWidget(self.titleText)
        # self.mainLayout.addWidget(self.infoText)
        self.gridLayout.addWidget(self.currentVersionLabel, 0, 0)
        self.gridLayout.addWidget(self.currentVersionInfoText, 0, 1)
        self.gridLayout.addWidget(self.latestVersionLabel, 1, 0)
        self.gridLayout.addWidget(self.latestVersionInfoText, 1, 1)
        self.mainLayout.addLayout(self.gridLayout)
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
        return super(UpdateWin, self).keyPressEvent(event)

