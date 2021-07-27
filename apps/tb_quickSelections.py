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

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    #from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    #from pyside2uic import *
    from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.mel as mel
import os, stat
import pickle
import json
import maya.OpenMayaUI as omUI
from Abstract import *
from tb_UI import *
import getStyleSheet as getqss


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('selection'))
        self.commandList = list()

        # quick selection set - select
        self.addCommand(self.tb_hkey(name='select_quick_select_set_objs',
                                     annotation='',
                                     category=self.category,
                                     command=['QuickSelectionSets.qs_select()']))
        self.addCommand(self.tb_hkey(name='quick_select_load_window',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['QuickSelectionSets.openQssLoadWindow()']))
        self.addCommand(self.tb_hkey(name='save_quick_selects_to_file',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['QuickSelectionSets.save_qs_to_file()']))
        self.addCommand(self.tb_hkey(name='create_quick_select_set',
                                     annotation='create a new quick selection set from current selection',
                                     category=self.category,
                                     command=['QuickSelectionSets.saveQssDialog()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class QuickSelectionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    #__metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'QuickSelectionSets'
    hotkeyClass = hotkeys()
    funcs = functions()

    quickSelectFolderOption = 'tb_qs_folder'
    quickSelectFolder = 'qssFiles'
    quickSelectFolderDefault = None
    quickSelectSavePath = None

    quickSelectOnQssSuffix = 'quickSelectOnQssSuffix'

    namespace_mode = 0

    def __new__(cls):
        if QuickSelectionTools.__instance is None:
            QuickSelectionTools.__instance = object.__new__(cls)
            QuickSelectionTools.__instance.initData()

        QuickSelectionTools.__instance.val = cls.toolName
        return QuickSelectionTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.all_sets = self.get_sets()

        self.quickSelectSavePath = pm.optionVar.get(self.quickSelectFolderOption, self.quickSelectFolderDefault)

        self.qss_files = list()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(QuickSelectionTools, self).optionUI()
        self.initData()
        dirWidget = filePathWidget(self.quickSelectFolderOption, self.quickSelectFolderDefault)
        quickSelectOnQssWidget = optionVarBoolWidget('Quick select selection only on sets named _qss', self.quickSelectOnQssSuffix)
        self.layout.addWidget(dirWidget)
        self.layout.addWidget(quickSelectOnQssWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def initData(self):
        super(QuickSelectionTools, self).initData()
        self.quickSelectFolderDefault = os.path.join(self.dataPath, self.quickSelectFolder)
        if not os.path.isdir(self.quickSelectFolderDefault):
            os.mkdir(self.quickSelectFolderDefault)

    def create_main_set(self):
        sel = cmds.ls(sl=True)
        if not cmds.objExists("QuickSelects"):
            cmds.select(clear=True)
            main_set = cmds.sets(name="QuickSelects")
            cmds.select(sel, replace=True)
            return main_set
        else:
            return "QuickSelects"

    def get_sets(self):
        all_sets = cmds.ls(sets=True)
        qs_sets = list()

        if pm.optionVar.get(self.quickSelectOnQssSuffix, True):
            all_sets = [q for q in all_sets if q.endswith('_qss')]

        for qs_name in all_sets:
            if cmds.sets(qs_name, query=True, text=True) == 'gCharacterSet':
                qs_sets.append(qs_name)

        return qs_sets

    def qs_select(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return

        for s in sel:
            if cmds.objectType(s) == 'objectSet':
                cmds.select(s, add=True)
                cmds.select(s, deselect=True, noExpand=True)
        all_sets = self.get_sets()
        if all_sets:
            for a_set in all_sets:
                qs_result = self.check_set_membership(sel, a_set)
                if qs_result:
                    cmds.select(a_set, add=True)
        else:
            msg = 'no quick selects found for selection'
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=3.0,
                                   fadeOutTime=4.0)

    @staticmethod
    def existing_obj_in_list(sel):
        existing = []
        for ob in sel:
            if cmds.objExists(ob):
                existing.append(ob)
        return existing

    @staticmethod
    def get_set_contents(qss_set):
        return cmds.sets(qss_set, query=True)

    def check_set_membership(self, selection, sel_set):
        sel_set_members = cmds.sets(sel_set, query=True)
        if sel_set_members:
            if [i for i in selection if i in sel_set_members]:
                return sel_set
            else:
                return None
        else:
            msg = 'no quick selects found in scene'
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=3.0,
                                   fadeOutTime=4.0)

    def create_qs_set(self):

        sel = cmds.ls(sl=True)
        if not sel:
            return

        result = cmds.promptDialog(
            title='Quick selection name',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            qs_name = cmds.promptDialog(query=True, text=True)
            save = True
            if qs_name in self.all_sets:
                if not cmds.confirmDialog(
                        title='Overwrite existing set?',
                        message='Are you sure?',
                        button=['Yes', 'No'],
                        defaultButton='Yes',
                        cancelButton='No',
                        dismissString='No'):
                    save = False
            if save:
                self.save_qs(qs_name, sel)

        else:
            msg = "can't save a quick selection set with nothing selected!"
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=3.0,
                                   fadeOutTime=4.0)

    def saveQssDialog(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return pm.warning('Unable to save empty selection')

        dialog = TextInputWidget(title='Save Quick Selection Set', label='Enter Name', buttonText="Save",
                                 default=sel[-1].split(':')[-1])
        dialog.acceptedSignal.connect(self.getSaveQssSignal)

    def getSaveQssSignal(self, input):
        if input:
            self.save_qs(input, cmds.ls(sl=True))

    def save_qs(self, qs_name, selection):
        pre_sel = cmds.ls(selection=True)
        # make sure we have the main set

        # only select existing objects
        existing_obj = self.existing_obj_in_list(selection)
        if existing_obj:
            cmds.select(existing_obj, replace=True)

            if cmds.objExists(qs_name):
                if cmds.nodeType(qs_name) == 'objectSet':
                    cmds.delete(qs_name)
            self.create_main_set()
            if not qs_name.endswith('_qss'):
                qs_name += '_qss'
            qs = cmds.sets(name=qs_name, text="gCharacterSet")
            cmds.select(qs, replace=True)
            cmds.sets(qs, addElement=self.create_main_set())
            cmds.select(pre_sel, replace=True)
        self.create_main_set()

    def save_qs_from_file(self, qs_name, selection):
        def process_namespace():
            sel = pm.ls(selection=True)
            if sel:
                namespace_override = sel[0].namespace()
            else:
                return pm.warning('Nothing selected, cannot match namespace')
            for sel in selection:
                processed_list.append(namespace_override + sel.split(":")[-1])
            return processed_list

        def replace_namespace(namespace=""):
            for sel in selection:
                processed_list.append(namespace + sel.split(":")[-1])

        processed_list = []
        if self.namespace_mode == 1:
            processed_list = process_namespace()
            msg = 'quick selects created for %s' % qs_name
        else:
            processed_list = selection
            msg = 'quick selects created for %s' % qs_name
        if processed_list:
            self.save_qs(qs_name, processed_list)
            self.funcs.infoMessage(position="botRight", prefix="info", message=msg, fadeStayTime=10, fadeOutTime=10.0)
        else:
            # process failed, make error
            self.funcs.infoMessage(position="botRight", prefix="Error", message=msg, fadeStayTime=10, fadeOutTime=10.0)

    def save_qs_to_file(self):
        if not self.get_sets():
            return cmds.warning('no sets found to save')
        dialog = TextInputWidget(title='Save Quick Selection Sets To File', label='Enter FileName', buttonText="Save",
                                 default='default')
        dialog.acceptedSignal.connect(self.getSaveFileSignal)

    def getSaveFileSignal(self, fileName):
        if fileName:
            save_file = os.path.join(self.quickSelectSavePath, fileName + ".qss")
            jsonFile = os.path.join(self.quickSelectSavePath, fileName + ".json")
            if not os.path.isdir(self.quickSelectSavePath):
                os.mkdir(self.quickSelectSavePath)
            else:
                os.chmod(self.quickSelectSavePath, stat.S_IWRITE)
            out_data = []
            jsonData = '''{}'''
            setData = json.loads(jsonData)
            for qsets in self.get_sets():
                out_data.append(qss_data_obj(qs_name=str(qsets), qs_objects=self.get_set_contents(qsets)))
                setData[str(qsets)] = self.get_set_contents(qsets)
            #pickle.dump(out_data, open(save_file, "wb"))
            self.saveJsonFile(jsonFile, setData)


    def load_qss_file(self, qss_name):
        """
        using pickle for some reason - TODO switch to json
        :param qss_name:
        :return:
        """
        file_name = os.path.join(self.quickSelectSavePath, qss_name)
        loaded_data = pickle.load(open(file_name, "rb"))
        for qs in loaded_data:
            self.save_qs_from_file(qs.qs_name, qs.qs_objects)

    def restore_qs_from_dir(self):
        qss_files = list()
        for qss_files in os.listdir(self.quickSelectSavePath):
            if qss_files.endswith(".qss"):
                self.qss_files.append(qss_files)

    def openQssLoadWindow(self):
        win = LoadQuickSelectWindow()
        win.show()


class qss_data_obj(object):
    def __init__(self, qs_name="", qs_objects=[]):
        self.qs_name = qs_name
        self.qs_objects = qs_objects

    def toJson(self):
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)
        jsonObjectInfo['qs_name'] = self.qs_name
        jsonObjectInfo['qs_objects'] = self.qs_objects

class saveQssWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self):
        super(TextInputWidget, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())
        self.setStyleSheet(
            "QDialog { "
            "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0.1 #646464, stop: 1 #5d5d5d);"
            "}"
            "saveQssWidget {"
            "border-style: solid;"
            "border: 1px solid #1e1e1e;"
            "border-radius: 5;"
            "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);"

            "}"
        )
        self.setWindowOpacity(0.9)
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

        self.titleText = QLabel('Save Quick Selection Set')
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel('Enter Name')
        self.lineEdit = QLineEdit(sel[0].stripNamespace())
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        self.saveButton = QPushButton("Save")
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.saveQss)

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
        grad.setColorAt(0, "#4d4d4d")
        grad.setColorAt(0.1, "#646464")
        grad.setColorAt(1, "#5d5d5d")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def saveQss(self, *args):
        self.saveSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.saveQss()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(TextInputWidget, self).keyPressEvent(event)


class QssFileWidget(QWidget):
    loadSignal = Signal(str)

    def __init__(self, name=str, filename=str):
        super(QssFileWidget, self).__init__()
        self.name = name
        self.filename = filename
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.label = QLabel(self.name)
        self.loadButton = QPushButton('Load')
        self.loadButton.setFixedWidth(64)
        self.loadButton.clicked.connect(self.loadClicked)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.loadButton)

    def loadClicked(self):
        self.loadSignal.emit(self.filename)


class NamespaceWidget(QWidget):
    namespaceChangedSignal = Signal(int)
    namespaceModes = ['From File', 'From Selection']

    namespaceModesOptionVar = 'tb_QssNamespaceMode'

    def __init__(self):
        super(NamespaceWidget, self).__init__()
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.label = QLabel('Namespace source ::')
        self.namespaceModeOption = QComboBox()
        for namespaceMode in self.namespaceModes:
            self.namespaceModeOption.addItem(namespaceMode)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.namespaceModeOption)
        self.namespaceModeOption.setCurrentIndex(pm.optionVar.get(self.namespaceModesOptionVar, 0))
        self.namespaceModeOption.currentIndexChanged.connect(self.namespaceIndexChanged)
        self.namespaceIndexChanged()

    def namespaceIndexChanged(self):
        pm.optionVar(intValue=(self.namespaceModesOptionVar, self.namespaceModeOption.currentIndex()))
        self.namespaceChangedSignal.emit(self.namespaceModeOption.currentIndex())


class LoadQuickSelectWindow(QMainWindow):
    def __init__(self):
        super(LoadQuickSelectWindow, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
        # DATA
        self.setMinimumWidth(300)
        # self.setMinimumHeight(400)
        self.QuickSelectionTools = QuickSelectionTools()

        # Main Widgets
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('Quick Select Set Loader')

        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        self.main_layout = QVBoxLayout()
        self.left_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        main_widget.setLayout(self.main_layout)

        menu = self.menuBar()
        edit_menu = menu.addMenu('&File')
        self.qssScrollArea = QScrollArea()
        self.qssScrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.qssScrollArea.setWidgetResizable(True)
        self.qssListWidget = QWidget()
        self.qssLayout = QVBoxLayout(self.qssListWidget)
        self.qssListWidget.setLayout(self.qssLayout)
        self.qssScrollArea.setWidget(self.qssListWidget)
        self.main_layout.addWidget(self.qssScrollArea)
        self.addReferenceButton = QPushButton('Add Rig To Map')

        self.namespaceWidget = NamespaceWidget()
        self.namespaceWidget.namespaceChangedSignal.connect(self.namespaceModeChanged)
        self.main_layout.addWidget(self.namespaceWidget)

        self.updateUI()

    def namespaceModeChanged(self, i):
        self.QuickSelectionTools.namespace_mode = i

    def loadQss(self, name):
        self.QuickSelectionTools.namespace_mode = self.namespaceWidget.namespaceModeOption.currentIndex()
        self.QuickSelectionTools.load_qss_file(name)

    def updateUI(self):
        self.QuickSelectionTools.restore_qs_from_dir()
        for item in self.QuickSelectionTools.qss_files:
            widget = QssFileWidget(name=item.split('.')[0], filename=item)
            widget.loadSignal.connect(self.loadQss)
            self.qssLayout.addWidget(widget)
        self.qssLayout.addStretch()
