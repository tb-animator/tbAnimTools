__author__ = 'Tom'
import pymel.core as pm

import maya.OpenMayaUI as omUI
import pymel.core as pm

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance
import getStyleSheet as getqss
import os


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent=parent)
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Something happened, is that OK?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class BaseDialog(QDialog):
    def __init__(self, parent=None, title='title?', text='message?'
                 ):
        super(BaseDialog, self).__init__(parent=parent)
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setFixedSize(400, 120)
        self.mainLayout = QVBoxLayout()
        self.layout = QVBoxLayout()

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(text)
        self.text.setStyleSheet(getqss.getStyleSheet())

        self.mainLayout.addWidget(self.titleText)
        self.mainLayout.addLayout(self.layout)
        self.layout.addWidget(self.text)

        self.setLayout(self.mainLayout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(BaseDialog, self).keyPressEvent(event)


class AimAxisDialog(BaseDialog):
    assignSignal = Signal(str, str, str, bool, bool, float)

    def __init__(self, controlName=str, parent=None,
                 title='Assign default aim for control',
                 text='what  what?',
                 itemList=['x','y','z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=10.0):
        super(AimAxisDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedSize(450, 130)
        self.controlName = controlName
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.itemLayout = QHBoxLayout()
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(32)
        self.upComboBox.setFixedWidth(32)

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80)
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(0.1)
        self.itemLayout.addWidget(aimLabel)
        self.itemLayout.addWidget(self.aimComboBox)
        self.itemLayout.addWidget(upLabel)
        self.itemLayout.addWidget(self.upComboBox)
        self.itemLayout.addWidget(flipAimLabel)
        self.itemLayout.addWidget(self.flipAimCB)
        self.itemLayout.addWidget(flipUpLabel)
        self.itemLayout.addWidget(self.flipUpCB)
        self.itemLayout.addWidget(distanceLabel)
        self.itemLayout.addWidget(self.distanceSpinBox)

        self.layout.addLayout(self.itemLayout)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)

    def assignPressed(self):
        self.assignSignal.emit(self.controlName,
                               str(self.aimComboBox.currentText()),
                               str(self.upComboBox.currentText()),
                               str(self.flipAimCB.isChecked()),
                               str(self.flipUpCB.isChecked()),
                               self.distanceSpinBox.value()
                               )
        self.close()


class PickListDialog(BaseDialog):
    assignSignal = Signal(str, str)

    def __init__(self, rigName=str, parent=None, title='title!!!?', text='what  what?', itemList=list()):
        super(PickListDialog, self).__init__(parent=parent, title=title, text=text)
        self.rigName = rigName
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        self.itemComboBox = QComboBox()
        for item in itemList:
            self.itemComboBox.addItem(item)
        self.layout.addWidget(self.itemComboBox)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)

    def assignPressed(self):
        print 'assign pressed', str(self.itemComboBox.currentText())
        self.assignSignal.emit(str(self.itemComboBox.currentText()), str(self.rigName))
        self.close()


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
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
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
        self.setFixedSize(400, 120)
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

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
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


class promptWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self, title=str(), text=str(), defaultInput=str(), buttonText=str()):
        super(promptWidget, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
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
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def confirm(self, *args):
        self.saveSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        print("That's a press!")
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(promptWidget, self).keyPressEvent(event)


class optionVarWidget(QWidget):
    def __init__(self, label=str, optionVar=str):
        super(optionVarWidget, self).__init__()
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.labelText = QLabel(label)


class optionVarBoolWidget(optionVarWidget):
    changedSignal = Signal(bool)

    def __init__(self, label=str, optionVar=str):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.checkBox = QCheckBox()
        self.checkBox.setChecked(pm.optionVar.get(self.optionVar, False))
        pm.optionVar(intValue=(self.optionVar, pm.optionVar.get(self.optionVar, False)))
        self.checkBox.clicked.connect(self.checkBoxEdited)
        self.layout.addWidget(self.labelText)
        self.layout.addWidget(self.checkBox)

    def checkBoxEdited(self):
        pm.optionVar(intValue=(self.optionVar, self.checkBox.isChecked()))

    def sendChangedSignal(self):
        self.changedSignal.emit(self.checkBox.isChecked())


class filePathWidget(QWidget):
    layout = None
    path = None
    optionVar = None
    dirButton = None

    def __init__(self, optionVar, defaultValue):
        super(filePathWidget, self).__init__()
        self.optionVar = optionVar
        self.path = pm.optionVar.get(self.optionVar, defaultValue)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.pathLabel = QLabel('Path:')
        self.pathLineEdit = QLineEdit(self.path)
        self.dirButton = QPushButton("Set folder")
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.dirButton)
        self.dirButton.clicked.connect(self.selectDirectory)

    def selectDirectory(self, *args):
        dialog = QFileDialog(None, caption="Pick Folder")
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setDirectory(self.path)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_directory = dialog.getExistingDirectory()

        if selected_directory:
            pm.optionVar[self.optionVar] = selected_directory
            self.path = selected_directory
            self.pathLineEdit.setText(self.path)


class intFieldWidget(QWidget):
    layout = None
    optionVar = None
    optionValue = 0

    def __init__(self, optionVar=str(), defaultValue=int(), label=str()):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.addStretch()
        label = QLabel(label)

        self.spinBox = QSpinBox()
        self.spinBox.setProperty("value", self.optionValue)
        self.layout.addWidget(label)
        self.layout.addWidget(self.spinBox)
        self.spinBox.valueChanged.connect(self.interactivechange)

    def interactivechange(self, b):
        pm.optionVar[self.optionVar] = self.spinBox.value()


class radioGroupWidget(QWidget):
    layout = None
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionVar = str()
    optionValue = str()

    def __init__(self, optionVarList=list(), optionVar=str(), defaultValue=str(), label=str()):
        super(radioGroupWidget, self).__init__()
        self.optionVarList = optionVarList
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addStretch()
        label = QLabel(label)
        btnGrp = QButtonGroup()  # Letter group
        layout.addWidget(label)
        for option in self.optionVarList:
            btn = QRadioButton(option)
            btn.toggled.connect(lambda: self.extBtnState(btn))
            btnGrp.addButton(btn)
            layout.addWidget(btn)
            btn.setChecked(self.optionValue == option)

    def extBtnState(self, b):
        pm.optionVar[self.optionVar] = b.text()
