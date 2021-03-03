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

import os


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
