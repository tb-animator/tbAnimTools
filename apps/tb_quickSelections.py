'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.mel as mel
import os, stat
import pickle
import maya.OpenMayaUI as omUI
from Abstract import *

import getStyleSheet as getqss


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_selection')
        self.commandList = list()

        # quick selection set - select
        self.addCommand(self.tb_hkey(name='select_quick_select_set_objs',
                                     annotation='',
                                     category=self.category,
                                     command=['quickSelectionTools.qs_select()']))
        self.addCommand(self.tb_hkey(name='quick_select_load_window',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['quickSelectionTools.restore_qs_from_dir()']))
        self.addCommand(self.tb_hkey(name='save_quick_selects_to_file',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['quickSelectionTools.save_qs_to_file()']))
        self.addCommand(self.tb_hkey(name='create_quick_select_set',
                                     annotation='create a new quick selection set from current selection',
                                     category=self.category,
                                     command=['quickSelectionTools.saveQssDialig()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class quickSelectionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'quickSelectionTools'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if quickSelectionTools.__instance is None:
            quickSelectionTools.__instance = object.__new__(cls)

        quickSelectionTools.__instance.val = cls.toolName
        return quickSelectionTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.all_sets = self.get_sets()

        self.save_dir = pm.optionVar.get('tb_qs_folder', 'c://qss//')
        self.qss_files = list()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(quickSelectionTools, self).optionUI()
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def create_main_set(self):
        sel = cmds.ls(sl=True)
        if not cmds.objExists("QuickSelects"):
            cmds.select(clear=True)
            main_set = cmds.sets(name="QuickSelects")
            cmds.select(sel, replace=True)
            return main_set
        else:
            return "QuickSelects"

    @staticmethod
    def get_sets():
        all_sets = cmds.ls(sets=True)
        qs_sets = list()
        for a_set in all_sets:
            if cmds.sets(a_set, query=True, text=True) == 'gCharacterSet':
                qs_sets.append(a_set)
        return qs_sets

    def qs_select(self):
        sel = cmds.ls(sl=True)
        print sel
        if not sel:
            return

        for s in sel:
            if cmds.objectType(s) == 'objectSet':
                cmds.select(s, add=True)
                cmds.select(s, deselect=True, noExpand=True)
        all_sets = self.get_sets()
        if all_sets:
            for a_set in all_sets:
                print 'checking set', a_set
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

    @staticmethod
    def get_sets():
        all_sets = cmds.ls(sets=True)
        qs_sets = []
        for a_set in all_sets:
            if cmds.sets(a_set, query=True, text=True) == 'gCharacterSet':
                qs_sets.append(a_set)
        return qs_sets

    def check_set_membership(self, selection, sel_set):
        sel_set_members = cmds.sets(sel_set, query=True)
        print 'sel_set_members', sel_set_members
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

    def saveQssDialig(self):
        sel = cmds.ls(selection=True)
        if not sel:
            return pm.warning('Unable to save empty selection')
        dialog = saveQssWidget()
        dialog.saveSignal.connect(self.getSaveQssSignal)

    def getSaveQssSignal(self, input):
        print 'getSaveQssSignal', input
        if input:
            self.save_qs(input, cmds.ls(sl=True))

    def save_qs(self, qs_name, selection):
        print "saving ", qs_name, "with", selection
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
            qs = cmds.sets(name=qs_name, text="gCharacterSet")
            cmds.select(qs, replace=True)
            cmds.sets(qs, addElement=self.create_main_set())
            cmds.select(pre_sel, replace=True)
        self.create_main_set()

    # Horrible old ui TODO update this
    # get data loaded from a qss file but muck about with namespaces first
    def save_qs_from_file(self, qs_name, selection):
        def process_namespace():
            sel = pm.ls(selection=True)
            if sel:
                namespace_override = sel[0].namespace()
                print namespace_override
            else:
                print "no selection!"
            if namespace_override:
                print "namespace overridden", namespace_override
            else:
                print "no namespace on sel"
            for sel in selection:
                processed_list.append(namespace_override + sel.split(":")[-1])
            return processed_list

        def replace_namespace(namespace=""):
            for sel in selection:
                processed_list.append(namespace + sel.split(":")[-1])

        print self.namespace_mode
        print selection
        processed_list = []
        if self.namespace_mode == "sel":
            processed_list = process_namespace()
            msg = 'quick selects created for %s' % qs_name
        elif self.namespace_mode == "spec":
            processed_list = replace_namespace(namespace=pm.textField(self.ns_text, query=True, text=True))
            msg = 'no quick selects created for specified namespace %s' % qs_name
        else:
            processed_list = selection
            msg = 'quick selects created for %s' % qs_name
        print processed_list
        if processed_list:
            self.save_qs(qs_name, processed_list)
            self.funcs.infoMessage(position="botRight", prefix="info", message=msg, fadeStayTime=5, fadeOutTime=5.0)
        else:
            # process failed, make error
            self.funcs.infoMessage(position="botRight", prefix="Error", message=msg, fadeStayTime=5, fadeOutTime=5.0)

    def save_qs_to_file(self):
        print 'save_qs_to_file'
        all_sets = self.get_sets()
        if not all_sets:
            return
        result = cmds.promptDialog(
            title='Save quick select file',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if not result:
            return

        file_name = cmds.promptDialog(query=True, text=True)
        save_file = os.path.join(self.save_dir, file_name + ".qss")
        if not os.path.isdir(self.save_dir):
            print "making maya qss folder"
            os.mkdir(self.save_dir)
        else:
            os.chmod(self.save_dir, stat.S_IWRITE)
        out_data = []
        for qsets in all_sets:
            out_data.append(qss_data_obj(qs_name=str(qsets), qs_objects=self.get_set_contents(qsets)))
        pickle.dump(out_data, open(save_file, "wb"))

    def load_qss_file(self, qss_name):
        file_name = os.path.join(self.save_dir, qss_name)
        loaded_data = pickle.load(open(file_name, "rb"))
        for qs in loaded_data:
            self.save_qs_from_file(qs.qs_name, qs.qs_objects)

    # gets the list of qss files
    def restore_qs_from_dir(self):
        for qss_files in os.listdir(self.save_dir):
            if qss_files.endswith(".qss"):
                self.qss_files.append(qss_files)
        if qss_files:
            self.restoreWin()

    # mini ui with a button!
    def qss_widget(self, qss_name="", parent=""):
        rLayout = pm.rowLayout(numberOfColumns=2,
                               adjustableColumn=1,
                               columnWidth2=(180, 50),
                               columnAttach2=("left", "right"),
                               parent=parent)
        pm.text(label=str(qss_name), parent=rLayout)

        pm.button(label="load", parent=rLayout, command=lambda *args: self.load_qss_file(qss_name))

    def get_ns_mode(self):
        print self.namespace_mode

    def namespace_widget(self, parent=""):
        def fileMode(*args):
            self.namespace_mode = "file"

        def selMode(*args):
            self.namespace_mode = "sel"

        def specMode(*args):
            self.namespace_mode = "spec"

        fLayout = pm.frameLayout(parent=parent, label="please select namespace source")
        cLayout = pm.columnLayout()
        r_layout = pm.rowLayout(numberOfColumns=2,
                                columnWidth1=60,
                                adjustableColumn=2)
        pm.columnLayout(width=150)
        pm.text(label="namespace source")
        pm.text(label="")
        pm.setParent(r_layout)
        g_layout = pm.gridLayout(numberOfColumns=2, cellWidthHeight=(100, 20))
        self.rb_col = pm.radioCollection()

        rb_file = pm.radioButton(collection=self.rb_col,
                                 label='from file',
                                 onCommand=fileMode)
        rb_sel = pm.radioButton("fromSel",
                                collection=self.rb_col,
                                label='from selection',
                                onCommand=selMode)
        rb_spec = pm.radioButton("spec",
                                 collection=self.rb_col,
                                 label='specify',
                                 onCommand=specMode)
        pm.radioCollection(self.rb_col, edit=True, select=rb_file)
        self.ns_text = pm.textField()

    # ui for loading sets
    def restoreWin(self):
        if pm.window("qssLoader", exists=True):
            pm.deleteUI("qssLoader")
        qss_win = pm.window("qssLoader", width=300, height=400)
        layout = pm.columnLayout(adjustableColumn=True)
        pm.text(font="boldLabelFont", label="quick select files")

        scroll_layout = pm.scrollLayout(parent=layout,
                                        childResizable=True,
                                        height=200)

        sub_layout = pm.columnLayout(adjustableColumn=True, parent=scroll_layout)

        for items in self.qss_files:
            print items
            self.qss_widget(qss_name=items, parent=sub_layout)
        self.namespace_widget(parent=layout)
        pm.showWindow(qss_win)


'''    


# this will find quick selection sets, and if you currently have one object in a set selected
# it will select the whole set

class quick_selection(object):
    def __init__(self):
        self.all_sets = self.get_sets()
        self.selection = cmds.ls(selection=True)
        self.main_set = self.create_main_set()
        self.save_dir = pm.optionVar.get('tb_qs_folder', 'c://qss//')
        self.qss_files = []
        self.rb_col = None
        self.ns_text = None
        self.namespace_mode = ""

    def create_main_set(self):
        if not cmds.objExists("QuickSelects"):
            cmds.select(clear=True)
            main_set = cmds.sets(name="QuickSelects")
            cmds.select(self.selection, replace=True)
            return main_set
        else:
            return "QuickSelects"

    def create_qs_set(self):
        if self.selection:
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
                    self.save_qs(qs_name, self.selection)

        else:
            msg = "can't save a quick selection set with nothing selected!"
            message.error(position="botRight", prefix="Error", message=msg, fadeStayTime=3.0, fadeOutTime=4.0)

    def save_qs(self, qs_name, selection):
        print "saving ", qs_name, "with", selection
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
            qs = cmds.sets(name=qs_name, text="gCharacterSet")
            cmds.select(qs, replace=True)
            cmds.sets(qs, addElement=self.main_set)
            cmds.select(pre_sel, replace=True)
        self.create_main_set()

    # get data loaded from a qss file but muck about with namespaces first
    def save_qs_from_file(self, qs_name, selection):
        def process_namespace():
            sel = pm.ls(selection=True)
            if sel:
                namespace_override = sel[0].namespace()
                print namespace_override
            else:
                print "no selection!"
            if namespace_override:
                print "namespace overridden", namespace_override
            else:
                print "no namespace on sel"
            for sel in selection:
                processed_list.append(namespace_override + sel.split(":")[-1])
            return processed_list

        def replace_namespace(namespace=""):
            for sel in selection:
                processed_list.append(namespace + sel.split(":")[-1])

        print self.namespace_mode
        print selection
        processed_list = []
        if self.namespace_mode == "sel":
            processed_list = process_namespace()
            msg = 'quick selects created for %s' % qs_name
        elif self.namespace_mode == "spec":
            processed_list = replace_namespace(namespace=pm.textField(self.ns_text, query=True, text=True))
            msg = 'no quick selects created for specified namespace %s' % qs_name
        else:
            processed_list = selection
            msg = 'quick selects created for %s' % qs_name
        print processed_list
        if processed_list:
            self.save_qs(qs_name, processed_list)
            message.info(position="botRight", prefix="info", message=msg, fadeStayTime=5, fadeOutTime=5.0)
        else:
            # process failed, make error
            message.error(position="botRight", prefix="Error", message=msg, fadeStayTime=5, fadeOutTime=5.0)

    def save_qs_to_file(self):
        self.all_sets = self.get_sets()
        result = cmds.promptDialog(
            title='Save quick select file',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')
        if self.all_sets and result:
            file_name = cmds.promptDialog(query=True, text=True)
            save_file = os.path.join(self.save_dir, file_name + ".qss")
            if not os.path.isdir(self.save_dir):
                print "making maya qss folder"
                os.mkdir(self.save_dir)
            else:
                os.chmod(self.save_dir, stat.S_IWRITE)
            out_data = []
            for qsets in self.all_sets:
                out_data.append(qss_data_obj(qs_name=str(qsets), qs_objects=self.get_set_contents(qsets)))
            pickle.dump(out_data, open(save_file, "wb"))

    def load_qss_file(self, qss_name):
        file_name = os.path.join(self.save_dir, qss_name)
        loaded_data = pickle.load(open(file_name, "rb"))
        for qs in loaded_data:
            self.save_qs_from_file(qs.qs_name, qs.qs_objects)

    # gets the list of qss files
    def restore_qs_from_dir(self):
        for qss_files in os.listdir(self.save_dir):
            if qss_files.endswith(".qss"):
                self.qss_files.append(qss_files)
        if qss_files:
            self.restoreWin()

    # mini ui with a button!
    def qss_widget(self, qss_name="", parent=""):
        rLayout = pm.rowLayout(numberOfColumns=2,
                               adjustableColumn=1,
                               columnWidth2=(180, 50),
                               columnAttach2=("left", "right"),
                               parent=parent)
        pm.text(label=str(qss_name), parent=rLayout)

        pm.button(label="load", parent=rLayout, command=lambda *args: self.load_qss_file(qss_name))

    def get_ns_mode(self):
        print self.namespace_mode

    def namespace_widget(self, parent=""):
        def fileMode(*args):
            self.namespace_mode = "file"

        def selMode(*args):
            self.namespace_mode = "sel"

        def specMode(*args):
            self.namespace_mode = "spec"

        fLayout = pm.frameLayout(parent=parent, label="please select namespace source")
        cLayout = pm.columnLayout()
        r_layout = pm.rowLayout(numberOfColumns=2,
                                columnWidth1=60,
                                adjustableColumn=2)
        pm.columnLayout(width=150)
        pm.text(label="namespace source")
        pm.text(label="")
        pm.setParent(r_layout)
        g_layout = pm.gridLayout(numberOfColumns=2, cellWidthHeight=(100, 20))
        self.rb_col = pm.radioCollection()
        print self.rb_col
        rb_file = pm.radioButton(collection=self.rb_col,
                                 label='from file',
                                 onCommand=fileMode)
        rb_sel = pm.radioButton("fromSel",
                                collection=self.rb_col,
                                label='from selection',
                                onCommand=selMode)
        rb_spec = pm.radioButton("spec",
                                 collection=self.rb_col,
                                 label='specify',
                                 onCommand=specMode)
        pm.radioCollection(self.rb_col, edit=True, select=rb_file)
        self.ns_text = pm.textField()

    # ui for loading sets
    def restoreWin(self):
        if pm.window("qssLoader", exists=True):
            pm.deleteUI("qssLoader")
        qss_win = pm.window("qssLoader", width=300, height=400)
        layout = pm.columnLayout(adjustableColumn=True)
        pm.text(font="boldLabelFont", label="quick select files")

        scroll_layout = pm.scrollLayout(parent=layout,
                                        childResizable=True,
                                        height=200)

        sub_layout = pm.columnLayout(adjustableColumn=True, parent=scroll_layout)

        for items in self.qss_files:
            print items
            self.qss_widget(qss_name=items, parent=sub_layout)
        self.namespace_widget(parent=layout)
        pm.showWindow(qss_win)

    def qs_select(self):
        if self.selection:
            for s in self.selection:
                if cmds.objectType(s) == 'objectSet':
                    cmds.select(s, add=True)
                    cmds.select(s, deselect=True, noExpand=True)
            if self.all_sets:
                for a_set in self.all_sets:
                    qs_result = self.check_set_membership(self.selection, a_set)
                    if qs_result:
                        cmds.select(a_set, add=True)
            else:
                msg = 'no quick selects found for selection'
                message.error(position="botRight", prefix="Error", message=msg, fadeStayTime=3.0, fadeOutTime=4.0)

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

    @staticmethod
    def get_sets():
        all_sets = cmds.ls(sets=True)
        qs_sets = []
        for a_set in all_sets:
            if cmds.sets(a_set, query=True, text=True) == 'gCharacterSet':
                qs_sets.append(a_set)
        return qs_sets

    @staticmethod
    def check_set_membership(selection, sel_set):
        sel_set_members = cmds.sets(sel_set, query=True)
        if sel_set_members:
            if [i for i in selection if i in sel_set_members]:
                return sel_set
            else:
                return None
        else:
            msg = 'no quick selects found in scene'
            message.error(position="botRight", prefix="Error", message=msg, fadeStayTime=3.0, fadeOutTime=4.0)

'''


class qss_data_obj(object):
    def __init__(self, qs_name="", qs_objects=[]):
        self.qs_name = qs_name
        self.qs_objects = qs_objects


class saveQssWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self):
        super(saveQssWidget, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
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
        self.setWindowFlags(Qt.PopupFocusReason| Qt.Tool | Qt.FramelessWindowHint)
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
        return super(saveQssWidget, self).keyPressEvent(event)
