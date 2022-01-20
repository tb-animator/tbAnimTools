'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2020-Tom Bailey
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    send issues/ requests to brimblashman@gmail.com
    visit https://tbanimtools.blogspot.com/ for "stuff"


*******************************************************************************
'''
import pymel.core as pm
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaUI as omUI
import pymel.core as pm
from functools import partial

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance
import getStyleSheet as getqss
import os

IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Icons'))
baseIconFile = 'checkBox.png'


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
    oldPos = None

    def __init__(self, parent=None, title='', text='',
                 lockState=False, showLockButton=False, showCloseButton=True, showInfo=True,
                 *args, **kwargs):
        super(BaseDialog, self).__init__(parent=parent)
        self.stylesheet = getqss.getStyleSheet()
        self.setStyleSheet(self.stylesheet)
        self.lockState = lockState
        self.showLockButton = showLockButton
        self.showCloseButton = showCloseButton
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setFixedSize(400, 120)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.layout = QVBoxLayout()
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.pinButton = LockButton('', None, lockState=self.lockState)
        self.pinButton.lockSignal.connect(self.togglePinState)
        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)
        self.titleText = QLabel(title)
        self.titleText.setFont(QFont('Lucida Console', 12))
        self.titleText.setStyleSheet("font-weight: lighter; font-size: 12px;")
        self.titleText.setStyleSheet("background-color: rgba(255, 0, 0, 0);")
        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        self.titleText.setAlignment(Qt.AlignCenter)
        self.infoText = QLabel(text)
        if not showInfo: self.infoText.hide()

        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleText, alignment=Qt.AlignCenter)
        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.pinButton, alignment=Qt.AlignRight)
        self.titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

        self.mainLayout.addLayout(self.titleLayout)
        self.infoText.setStyleSheet(self.stylesheet)
        self.layout.addWidget(self.infoText)

        self.mainLayout.addLayout(self.layout)
        self.setLayout(self.mainLayout)

        self.pinButton.setVisible(self.showLockButton)
        self.closeButton.setVisible(self.showCloseButton)

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
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.controlKeyPressed = False
        return False

    def keyPressEvent(self, event):
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

    def togglePinState(self, pinState):
        self.lockState = pinState
        self.closeButton.setVisible(True)


class AimAxisWidget(QWidget):
    editedSignal = Signal(str, str, bool, bool, float, float)

    def __init__(self, itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100.0,
                 scale=1.0):
        super(AimAxisWidget, self).__init__()
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        self.distance = distance
        self.scale = scale
        self.itemLayout = QHBoxLayout()
        self.setLayout(self.itemLayout)
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
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

        self.scaleSpinBox = QDoubleSpinBox()
        scaleLabel = QLabel('Scale')
        self.scaleSpinBox.setFixedWidth(80)
        self.scaleSpinBox.setValue(scale)
        self.scaleSpinBox.setMinimum(0.01)
        self.scaleSpinBox.setSingleStep(0.1)

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80)
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(1)

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

        # draw scale
        self.itemLayout.addWidget(scaleLabel)
        self.itemLayout.addWidget(self.scaleSpinBox)

        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        self.scaleSpinBox.valueChanged.connect(self.widgetedited)

    def widgetedited(self, *args):
        self.editedSignal.emit(str(self.aimComboBox.currentText()),
                               str(self.upComboBox.currentText()),
                               self.flipAimCB.isChecked(),
                               self.flipUpCB.isChecked(),
                               self.distanceSpinBox.value(),
                               self.scaleSpinBox.value()
                               )


class AimAxisDialog(BaseDialog):
    assignSignal = Signal(str, str, str, bool, bool, float, float)
    editedSignal = Signal(str, str, str, bool, bool, float, float)
    closeSignal = Signal()

    def __init__(self, controlName=str, parent=None,
                 title='Assign default aim for control',
                 text='what  what?',
                 itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100,
                 scale=1.0):
        super(AimAxisDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedSize(580, 130)
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

        self.aimWidget = AimAxisWidget(itemList=itemList,
                                       aimAxis=aimAxis,
                                       upAxis=upAxis,
                                       flipAim=flipAim,
                                       flipUp=flipUp,
                                       distance=distance,
                                       scale=scale)
        '''
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
        '''
        self.layout.addWidget(self.aimWidget)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)
        '''
        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        '''
        self.aimWidget.editedSignal.connect(self.widgetedited)

    def assignPressed(self):
        self.assignSignal.emit(self.controlName,
                               str(self.aimWidget.aimComboBox.currentText()),
                               str(self.aimWidget.upComboBox.currentText()),
                               self.aimWidget.flipAimCB.isChecked(),
                               self.aimWidget.flipUpCB.isChecked(),
                               self.aimWidget.distanceSpinBox.value(),
                               self.aimWidget.scaleSpinBox.value()
                               )
        self.close()

    def close(self):
        self.closeSignal.emit()
        super(AimAxisDialog, self).close()

    def widgetedited(self, aim, up, flipAim, flipUp, distance, scale):
        self.editedSignal.emit(self.controlName,
                               aim,
                               up,
                               flipAim,
                               flipUp,
                               distance,
                               scale
                               )


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
        self.assignSignal.emit(str(self.itemComboBox.currentText()), str(self.rigName))
        self.close()


class PickObjectDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(PickObjectDialog, self).__init__(parent=parent, title=title, text=text)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)
        self.show()

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))
        self.assignSignal.emit(str(sel[0]))


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


class QTreeSingleViewWidget(QFrame):
    pressedSignal = Signal(str)
    itemChangedSignal = Signal(str)

    def __init__(self, CLS=None, label='BLANK'):
        super(QTreeSingleViewWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.setMinimumWidth(120)
        # self.setMaximumWidth(200)
        # self.width = 300
        self.setLayout(self.layout)
        self.topLayout = QVBoxLayout()
        self.layout.addLayout(self.topLayout)
        self.label = QLabel(label)
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.addAction(QIcon(":/resources/search.ico"), QLineEdit.LeadingPosition)
        self.filterLineEdit.setPlaceholderText("Search...")

        # self.topLayout.addWidget(self.label)
        self.topLayout.addWidget(self.filterLineEdit)

        self.listView = QListView()

        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.model = QStandardItemModel()

        self.proxyModel.setSourceModel(self.model)
        self.listView.setModel(self.proxyModel)
        self.listView.clicked.connect(self.itemClicked)
        self.model.itemChanged.connect(self.itemChanged)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)

        self.listView.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.listView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.toolTypeScrollArea = QScrollArea()
        self.toolTypeScrollArea.setWidget(self.listView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.toolTypeScrollArea)

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def appendItem(self, i):
        item = QStandardItem(i)
        self.model.appendRow(item)

    def removeItem(self, item):
        for item in self.model.findItems(item):
            self.model.removeRow(item.row())

    def updateView(self, items):
        self.model.clear()
        self.listView.blockSignals(True)
        for i in items:
            self.appendItem(i)
        self.listView.blockSignals(False)

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        # print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.pressedSignal.emit(item.text())

    def itemChanged(self, item):
        self.itemChangedSignal.emit(item.text())


class TextInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedComboSignal = Signal(str, str)
    acceptedCBSignal = Signal(str, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText=str(), default=str(), combo=list(), checkBox=None,
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(TextInputWidget, self).__init__(parent=parent)
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
        self.setFixedSize(400, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
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
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())
        for c in self.combo:
            self.comboBox.addItem(c)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        if len(self.combo):
            layout.addWidget(self.comboBox)
        if self.checkBox is not None:
            layout.addWidget(self.checkBoxWD)
        layout.addWidget(self.saveButton)

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
        width = self.comboBox.minimumSizeHint().width()
        self.comboBox.view().setMinimumWidth(width)
        self.comboBox.setMinimumWidth(width)
        self.resize(self.sizeHint())

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

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedComboSignal.emit(self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedCBSignal.emit(self.lineEdit.text(), self.checkBoxWD.isChecked())
        self.close()

    def close(self):
        self.rejectedSignal.emit()
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
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

class ChannelInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(ChannelInputWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

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
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
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

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return pm.warning('no channel selected')
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

class ObjectInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(ObjectInputWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

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
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
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

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        shape = sel[0].getShape()
        if not shape:
            return
        if pm.nodeType(shape) == "nurbsCurve":
            self.lineEdit.setText(str(sel[0]))

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
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


class promptWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self, title=str(), text=str(), defaultInput=str(), buttonText=str()):
        super(promptWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
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
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(promptWidget, self).keyPressEvent(event)


class subHeader(QLabel):
    """
    label with wordwrap
    """

    def __init__(self, label=str()):
        super(subHeader, self).__init__()
        self.setText(label)
        self.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


class infoLabel(QLabel):
    def __init__(self, textLines=list()):
        super(infoLabel, self).__init__()
        text = str()
        for line in textLines:
            text += line + '\n'
        self.setText(text)
        self.setWordWrap(True)


class optionWidget(QWidget):
    def __init__(self, label=str):
        super(optionWidget, self).__init__()
        self.labelText = label
        self.initUI()

    def initUI(self):
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.scrollWidget = QWidget()  # Widget that contains the collection of Vertical Box
        self.layout = QVBoxLayout()  # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        self.scrollWidget.setLayout(self.layout)

        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollWidget)

        self.mainLayout.addWidget(self.scroll)

        self.label = QLabel(self.labelText)
        self.label.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.label)
        self.setGeometry(600, 100, 1000, 900)
        self.setWindowTitle('Scroll Area Demonstration')


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
        self.layout.setContentsMargins(0,0,0,0)
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
        self.sendChangedSignal()

    def sendChangedSignal(self):
        self.changedSignal.emit(self.checkBox.isChecked())


class optionVarListWidget(optionVarWidget):
    """
    changing to use classdata instead of maya option vars
    """
    changedSignal = Signal(str, list)

    def __init__(self, label=str(), optionVar=str(), optionList=list(), classData=dict()):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.labelText.setAlignment(Qt.AlignTop)
        self.cbLayout = QGridLayout()
        optionVarValues = classData.get(optionVar, list())
        self.checkBoxes = list()
        numColumns = 2
        currentRow = 0
        count = 0
        for op in optionList:
            checkBox = QCheckBox()
            self.checkBoxes.append(checkBox)
            checkBox.setText(op)
            checkBox.setObjectName(optionVar + '_' + op)
            checkBox.setChecked(op in optionVarValues)
            self.cbLayout.addWidget(checkBox, count / 2, count % numColumns)
            checkBox.clicked.connect(self.checkBoxEdited)
            count += 1

        self.layout.addWidget(self.labelText)
        self.layout.addLayout(self.cbLayout)

    def checkBoxEdited(self, *args):
        activeValues = list()
        for cb in self.checkBoxes:
            if cb.isChecked():
                activeValues.append(cb.text())

        self.changedSignal.emit(self.optionVar, activeValues)


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


class ChannelSelectLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), text=str, tooltip=str(), placeholderTest=str(), stripNamespace=False):
        super(ChannelSelectLineEdit, self).__init__()
        self.stripNamespace = stripNamespace
        self.key = key
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.pickChannel)
        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.lineEdit)
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
            if self.stripNamespace:
                refNamespace = cmds.referenceQuery(channels[0].split('.')[0], namespace=True)
                self.lineEdit.setText(channels[0].strip(refNamespace))
            else:
                self.lineEdit.setText(channels[0].rsplit(':', 1)[-1])
        else:
            self.lineEdit.setText(channels[0])

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())
        self.editedSignalKey.emit(self.key, self.lineEdit.text())


class hotKeyWidget(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)

    def __init__(self, command=str(), text=str(), tooltip=str(), placeholderTest=str()):
        super(hotKeyWidget, self).__init__()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()

        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/arrowDown.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.show_category_table_Popup)
        self._category_table_Popup = QMenu(self)
        recentAction = QAction('Recent Command List', self._category_table_Popup, checkable=True, checked=True)
        onPressAction = QAction('On Press', self._category_table_Popup, checkable=True, checked=True)
        onReleaseAction = QAction('On Release', self._category_table_Popup, checkable=True, checked=True)
        self._category_table_Popup.addAction(recentAction)
        self._category_table_Popup.addSeparator()
        self._category_table_Popup.addAction(onPressAction)
        self._category_table_Popup.addAction(onReleaseAction)

        self.action_group = QActionGroup(self)
        self.action_group.addAction(onPressAction)
        self.action_group.addAction(onReleaseAction)
        self.action_group.setExclusive(True)

        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        self.label.setFixedWidth(60)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())

    @Slot()
    def show_category_table_Popup(self):
        '''
        Show Popup Menu on Category Table
        '''
        self._category_table_Popup.exec_(QCursor.pos())


class ObjectSelectLineEdit(QWidget):
    pickedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), label=str(), hint=str(), labelWidth=65, lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False):
        QWidget.__init__(self)
        self.key = key
        self.stripNamespace = stripNamespace
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.label = QLabel(label)
        # self.label.setFixedWidth(labelWidth)
        self.itemLabel = QLineEdit()
        self.itemLabel.setPlaceholderText(placeholderTest)
        self.itemLabel.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(hint)
        self.cle_action_pick.triggered.connect(self.pickObject)
        self.itemLabel.textChanged.connect(self.textEdited)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.itemLabel)

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        if self.stripNamespace:
            s = str(sel[0]).split(':', 1)[-1]
        else:
            s = str(sel[0])
        self.itemLabel.setText(s)
        self.pickedSignal.emit(s)
        # self.editedSignalKey.emit(self.key, str(sel[0]))

    def setTextNoUpdate(self, text):
        self.blockSignals(True)
        self.itemLabel.setText(text)
        self.blockSignals(False)

    @Slot()
    def textEdited(self):
        self.editedSignalKey.emit(self.key, self.itemLabel.text())


class comboBoxWidget(QWidget):
    mainLayout = None
    optionVar = None
    optionValue = 0

    changedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), optionVar=None, values=list(), defaultValue=int(), label=str()):
        QWidget.__init__(self)
        self.key = key
        self.values = values
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        if optionVar is not None:
            self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        label = QLabel(label)

        self.comboBox = QComboBox()
        if self.values:
            for c in self.values:
                self.comboBox.addItem(c)
            self.comboBox.setCurrentIndex(self.values.index(self.defaultValue))
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())

        self.mainLayout.addWidget(label)
        self.mainLayout.addWidget(self.comboBox)
        self.comboBox.currentIndexChanged.connect(self.interactivechange)
        self.mainLayout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            pm.optionVar[self.optionVar] = self.comboBox.currentText()
        self.changedSignal.emit(self.comboBox.currentText())
        self.editedSignalKey.emit(self.key, self.comboBox.currentText())

    def updateValues(self, valueList, default):
        self.comboBox.clear()
        self.values = valueList
        for c in self.values:
            self.comboBox.addItem(c)
        self.comboBox.setCurrentIndex(self.values.index(default))


class intFieldWidget(QWidget):
    layout = None
    optionVar = None
    optionValue = 0

    changedSignal = Signal(float)
    editedSignalKey = Signal(str, float)

    def __init__(self, key=str(), optionVar=None, defaultValue=int(), label=str(), minimum=0, maximum=1, step=0.1):
        QWidget.__init__(self)
        self.key = key

        self.optionVar = optionVar
        self.defaultValue = defaultValue
        if optionVar is not None:
            self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        label = QLabel(label)

        self.spinBox = QDoubleSpinBox()
        self.spinBox.setMaximum(maximum)
        self.spinBox.setMinimum(minimum)
        self.spinBox.setSingleStep(step)
        self.spinBox.setValue(defaultValue)
        if step == 1:
            self.spinBox.setDecimals(0)
        self.spinBox.setProperty("value", self.optionValue)
        self.layout.addWidget(label)
        self.layout.addWidget(self.spinBox)
        self.spinBox.valueChanged.connect(self.interactivechange)
        self.layout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            pm.optionVar[self.optionVar] = self.spinBox.value()
        self.changedSignal.emit(self.spinBox.value())
        self.editedSignalKey.emit(self.key, self.spinBox.value())


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


class radioGroupVertical(object):
    layout = None
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionVar = str()
    optionValue = str()

    def __init__(self, formLayout=QFormLayout, optionVarList=list(), optionVar=str(), defaultValue=str(), label=str(),
                 tooltips=list()):
        super(radioGroupVertical, self).__init__()
        self.tooltips = tooltips
        self.optionVarList = optionVarList
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)

        self.btnGrp = QButtonGroup()  # Letter group
        self.returnedWidgets = list()
        self.buttons = list()
        for index, option in enumerate(self.optionVarList):
            self.buttons.append(QRadioButton(option))
            self.btnGrp.addButton(self.buttons[index])
            self.returnedWidgets.append(['option', self.buttons[index]])
            self.buttons[index].setChecked(self.optionValue == option)
            self.buttons[index].toggled.connect(self.buttonChecked)
            try:
                self.buttons[index].setToolTip(self.tooltips[index])
            except:
                pass

    def buttonChecked(self, value):
        for button in self.buttons:
            if button.isChecked() == True:
                pm.optionVar[self.optionVar] = button.text()


class LicenseWin(BaseDialog):
    ActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title='Tool Name?'):
        super(LicenseWin, self).__init__(parent=parent)
        self.setWindowTitle("LicenseWin!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.addButton("Activate", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.activate)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400, 180)
        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 14px;");
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText('Please enter your license key and email address used for this purchase')
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
        self.ActivateSignal.emit(self.licenseLineEdit.text(), self.emailLineEdit.text())

    def cancel(self):
        self.close()


class PickObjectDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(PickObjectDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedWidth(200)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))


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

        self.setFixedSize(400, 180)

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

        self.setFixedSize(400, 180)

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

        self.setFixedSize(400, 180)
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


class MiniButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon=baseIconFile, toolTip='Close'):
        super(MiniButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(18, 18)

        pixmap = QPixmap(os.path.join(IconPath, icon))
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())


class LockButton(MiniButton):
    lockSignal = Signal(bool)

    def __init__(self, label, parent,
                 icon='pinned_small.png',
                 unlockIcon='pin.png',
                 lockState=False,
                 toolTip='Lock UI on screen, hold control+left mouse click to move'):
        super(LockButton, self).__init__(icon=icon, toolTip=toolTip)
        self.lockState = False

        self.lockIcon = QPixmap(os.path.join(IconPath, icon))
        self.unlockIcon = QPixmap(os.path.join(IconPath, unlockIcon))

        self.clicked.connect(self.toggleLock)
        self.setLockIcon()

    def setLockIcon(self):
        if self.lockState:
            self.setIcon(self.lockIcon)
        else:
            self.setIcon(self.unlockIcon)

    def toggleLock(self, *args):
        self.lockState = not self.lockState
        self.lockSignal.emit(self.lockState)
        self.setLockIcon()


class AnimLayerTabButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon='', toolTip=''):
        super(AnimLayerTabButton, self).__init__()
        self.setIcon(QIcon(":/{0}".format(icon)))
        self.setFixedSize(18, 18)
        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        self.pop_up_window.move(pop_up_pos)

        self.pop_up_window.show()


sliderStylesheet = """


QSlider::groove:horizontal {
border: 1px solid #bbb;
background: transparent;
height: 4;
border-radius: 4px;
}

QSlider::sub-page:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2:1, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #66e, stop: 1 #bbf);
border: 1px solid #2d2d2d;
height: 4;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::add-page:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);
border: 1px solid #2d2d2d;
height: 4px;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::handle:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
border: 2px solid #444;
width: 16px; 
height: 16px; 
line-height: 20px; 
margin-top: -8px; 
margin-bottom: -8px; 
border-radius: 8px; 
image: url(":greasePencilPreGhostOff.png");
}

QSlider::handle:horizontal:hover {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
border: 2px solid #777;
}

QSlider::sub-page:horizontal:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:horizontal:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:horizontal:disabled {
background: #eee;
border: 1px solid #aaa;
border-radius: 4px;
"""

buttonSS = """
QPushButton {
color: #333;
border: 2px solid #555;
border-radius: 6px;
border-style: outset;
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #888
);
padding: 5px;
}

QPushButton:hover {
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #bbb
);
}
"""


class testDialog(QDialog):
    AssignNewRigSignal = Signal(str)
    CreateNewRigMapSignal = Signal(str)
    IgnoreRigSignal = Signal(str)

    def __init__(self, parent=None, title='title?', rigName=str(), text='message?',
                 assignText='Assign existing map',
                 createText='Create new map',
                 ignoreText='Ignore',
                 cancelText='Cancel',
                 ):
        super(testDialog, self).__init__(parent=parent)
        self.rigName = rigName
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # self.layout = QVBoxLayout()
        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.layout)

        # self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        sliderLayout = QHBoxLayout()
        sliderLayout.setContentsMargins(0, 0, 0, 0)

        leftButton = QPushButton()
        rightButton = QPushButton()
        leftButton.setStyleSheet(buttonSS)
        leftButton.setFixedSize(12, 12)
        rightButton.setStyleSheet(buttonSS)
        rightButton.setFixedSize(12, 12)
        sliderLayout.setAlignment(Qt.AlignCenter)
        sliderLayout.setSpacing(0)
        self.slider_label = QLabel()
        self.slider_label.setFixedHeight(20)
        self.slider_label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksAbove)
        self.slider.setFixedHeight(24)
        self.slider.setFixedWidth(220)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(0.1)
        self.slider.setStyleSheet(sliderStylesheet)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.sliderReleased.connect(self.slider_released)

        self.slider_label.setText(str(self.slider.value()))

        sliderLayout.addWidget(leftButton)
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(rightButton)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addWidget(self.slider_label)
        self.setLayout(mainLayout)
        self.resize(self.sizeHint())

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
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def move_UI(self):
        ''' Moves the UI to the widget position '''
        pos = QCursor.pos()
        self.move(pos.x() - (self.width() * 0.5), pos.y() - (self.height() * 0.5))

    def slider_changed(self):
        self.slider_label.setText(str(self.slider.value()))

    def slider_released(self):
        cmds.warning('Value is %d' % self.slider.value())

    def button_clicked(self, obj):
        self.button.setText('Clicked')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(testDialog, self).keyPressEvent(event)

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


class ButtonPopup(QWidget):
    def __init__(self, name, parent=None):
        super(ButtonPopup, self).__init__(parent)

        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        pass
        self.radioGroup = radioGroupVertical(formLayout=self.layout,
                                             optionVarList=['test', 'test2', 'test3'],
                                             optionVar='testVar',
                                             defaultValue='test',
                                             label=str())

    def create_layout(self):
        for label, widget in self.radioGroup.returnedWidgets:
            self.layout.addRow("%s:" % label, widget)
        # layout.addRow("Size:", self.size_sb)
        # layout.addRow("Opacity:", self.opacity_sb)


class PluginExtractor(BaseDialog):
    installSignal = Signal(str)

    def __init__(self, parentCLS):
        super(PluginExtractor, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.parentCLS = parentCLS
        self.titleText.setText('tbAnimTools Plugin Extractor')
        self.titleText.setStyleSheet("font-weight: normal; font-size: 18px;")
        self.infoText.setText('Install plugins from the zip file')
        self.infoText.setAlignment(Qt.AlignCenter)

        self.btnCloseWIndow = QPushButton("Close")
        self.btnCloseWIndow.clicked.connect(partial(self.close))

        self.btnInstall = QPushButton("Install")
        self.btnInstall.clicked.connect(partial(self.install))
        self.btnInstall.setEnabled(False)

        self.filePathLayout = QHBoxLayout()
        self.pathLabel = QLabel('Install to ::')
        self.pathLineEdit = QLineEdit('')
        self.pathLineEdit.setPlaceholderText('zip file path')
        self.cle_action_pick = self.pathLineEdit.addAction(QIcon(":/folder-open.png"),
                                                           QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Select your downloaded zip file')
        self.cle_action_pick.triggered.connect(self.pickZipFile)
        self.pathLineEdit.textChanged.connect(self.pathEdited)

        self.layout.addLayout(self.filePathLayout)
        self.filePathLayout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.btnInstall)
        self.layout.addWidget(self.btnCloseWIndow)
        self.setFixedSize(self.sizeHint())

    def pathEdited(self, *args):
        self.btnInstall.setEnabled(os.path.isfile(self.pathLineEdit.text()))

    def install(self, *args):
        self.installSignal.emit(self.pathLineEdit.text())

    def pickZipFile(self, *args):
        filename, filter = QFileDialog.getOpenFileName(parent=self,
                                                       caption='Open file',
                                                       dir='.',
                                                       filter='Zip Files (*.zip)')
        if filename:
            self.pathLineEdit.setText(filename)
