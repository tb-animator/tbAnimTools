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
import maya.cmds as cmds
from pluginLookup import ClassFinder
import re
import getStyleSheet as getqss
import maya.OpenMayaUI as omUI
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


class tbToolLoader(object):
    classLookup = ClassFinder()
    classLookup.startup()
    allCommands = list()  # all user commands generated this run by tbtools scripts
    allCommandNames = list()  # names of commands generated this run by tbtools scripts
    allCategories = list()  # categories found via tbtools scripts
    existing_commands = list()  # currently existing tbtools commands
    extra_commands = pm.optionVar.get('tb_extra_commands', '')
    loadedHotkeyClasses = list()

    def loadAllCommands(self):
        #print ('loadedClasses hotkeys', self.classLookup.loadedClasses['hotkeys'])
        self.allCommands = list()
        self.instantiateHotkeyClasses()
        self.getHotkeyCommandsFromLoadedClasses()
        self.allCommandNames = [command.name for command in self.allCommands]
        self.allCategories = list(set([command.category for command in self.allCommands]))
        #print ('allCommands', self.allCommands)
        #print ('allCategories', self.allCategories)
        self.getExistingCommands()
        self.updateCommands()
        self.removeBadCommands()

    def getHotkeyCommandsFromLoadedClasses(self):
        for cls in self.loadedHotkeyClasses:
            #print ('loading hotkeys from class:: ', cls)
            self.allCommands.extend(cls.createHotkeyCommands())

    def instantiateHotkeyClasses(self):
        if self.classLookup.loadedClasses['hotkeys']:
            self.loadedHotkeyClasses = [cls() for cls in self.classLookup.loadedClasses['hotkeys']]

    def assignHotkeysFromLoadedClasses(self):
        for cls in self.loadedHotkeyClasses:
            #print ('assigning hotkeys from class:: ', cls)
            cls.assignHotkeys()

    def getExistingCommands(self):
        """
        Get all user created runtime commands
        Compare those to the categories found by the hotkey lookup
        return all commands in categories created by tbtools scripts
        :return:
        """
        allUserCommands = pm.runTimeCommand(query=True, userCommandArray=True)

        if not allUserCommands:
            return
        self.existing_commands = [com for com in allUserCommands if
                                  pm.runTimeCommand(com, query=True, category=True) in self.allCategories]

    def updateCommands(self):
        for commands in self.allCommands:
            self.addCommand(commands)

    def addCommand(self, command):
        try:
            # in theory deleting the command and re adding it will keep everything in a nice order
            if pm.runTimeCommand(command.name, exists=True):
                pm.runTimeCommand(command.name, edit=True, delete=True)

            pm.runTimeCommand(command.name,
                              # edit=True,
                              annotation=command.annotation,
                              category=command.category,
                              commandLanguage=command.language,
                              command=command.command)
            cmds.nameCommand(command.name + 'NameCommand',
                             annotation=command.name + 'NameCommand',
                             command=command.name,
                             sourceType='mel')
        except Exception as e:
            cmds.warning(e, e.message)

    def removeUnneededIgnoreEntries(self):
        if not self.extra_commands:
            return
        if not self.existing_commands:
            return
        # print 'extra_commands', self.extra_commands
        needed_ignore_names = [item for item in self.existing_commands if item in self.existing_commands]
        # print needed_ignore_names
        return
        for items in self.extra_commands:
            if items in self.existing_commands:
                needed_ignore_names.append(items)

        pm.optionVar.pop('tb_extra_commands')
        for items in needed_ignore_names:
            pm.optionVar(stringValueAppend=('tb_extra_commands', items))

    def removeBadCommands(self):
        # print 'removeBadCommands...'
        # print 'existing_commands', self.existing_commands
        # print 'allCommandNames', self.allCommandNames
        # print 'extra_commands', self.extra_commands
        commands = [com for com in self.existing_commands if
                    com not in self.allCommandNames and com not in self.extra_commands]
        # print commands
        if commands:
            hotkey_cleanup(commands_to_delete=commands)

    def getCommandAssignment(self):
        count = cmds.assignCommand(query=True, numElements=True)
        allHotkeys = dict()
        allHotkeyCategories = dict()
        for index in range(1, count + 1):
            keyString = cmds.assignCommand(index, query=True, keyString=True)
            commandName = cmds.assignCommand(index, query=True, name=True)
            commandNameStripped = commandName.replace('NameCommand', '')
            if commandNameStripped not in self.allCommandNames:
                continue
            category = pm.runTimeCommand(commandNameStripped, query=True, category=True)
            if category not in allHotkeyCategories.keys():
                allHotkeyCategories[category] = list()

            if 0 < len(keyString) and keyString[0] != "NONE":
                allHotkeys[commandName] = {'key': None,
                                           'ctrl': "1" == keyString[2],
                                           'Alt': "1" == keyString[1],
                                           'Command': "1" == keyString[5],
                                           'Release': "1" == keyString[3],
                                           'KeyRepeat': "1" == keyString[4]
                                           }
            else:
                allHotkeys[commandName] = {'key': None,
                                           'ctrl': False,
                                           'Alt': False,
                                           'Command': False,
                                           'Release': False,
                                           'KeyRepeat': False
                                           }
            allHotkeyCategories[category].append(commandName)

        return allHotkeys, allHotkeyCategories


def getMainWindow():
    return wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)

class SearchProxyModel(QSortFilterProxyModel):
    def setFilterRegExp(self, pattern):
        if isinstance(pattern, str):
            pattern = QRegExp(pattern, Qt.CaseInsensitive, QRegExp.FixedString)
        super(SearchProxyModel, self).setFilterRegExp(pattern)

    def _accept_index(self, idx):
        if idx.isValid():
            text = idx.data(Qt.DisplayRole)
            if self.filterRegExp().indexIn(text.lower()) >= 0:
                return True
            for row in range(idx.model().rowCount(idx)):
                if self._accept_index(idx.model().index(row, 0, idx)):
                    return True
        return False

    def filterAcceptsRow(self, sourceRow, sourceParent):
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self._accept_index(idx)

class mainHotkeyWindow(QMainWindow):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __instance = None
    appWin = getMainWindow()
    win = None

    def __init__(self, commandData=dict(), commandCategories=dict()):
        self.commandData = commandData
        self.commandCategories = commandCategories

        super(mainHotkeyWindow, self).__init__(self.appWin)

    def initColor(self):
        windowCss = '''
        QFrame {
            background-color: rgb(90,90,90);
            border: 1px solid rgb(90,70,30);
        }
        QFrame#SideBar {
            background-color: rgb(50,50,50);
            border: 1px solid rgb(255,255,255);
        QDialog::title {
            height: 24px;
            font-weight: bold;
            color: #000000;
            background: #ffffff;
         }
        }'''
        self.setStyleSheet(windowCss)

    def buildUI(self):
        self.win = QDialog(parent=self.appWin)
        self.win.setStyleSheet(getqss.getStyleSheet())
        self.win.setWindowTitle('tbAnimTools - commands')
        self.win.setMinimumWidth(700)
        # self.win.setMinimumHeight(300)
        self.mainLayout = QHBoxLayout()

        self.treeView = QTreeView()
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setStyleSheet("QTreeView {"
                                    "alternate-background-color: #464848 ;"
                                    "background: #404040;}"
                                    )

        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.addAction(QIcon(":/resources/search.ico"), QLineEdit.LeadingPosition)
        self.filterLineEdit.setPlaceholderText("Search...")

        self.proxyModel = SearchProxyModel()
        self.proxyModel.setDynamicSortFilter(True)


        self.model = QStandardItemModel()
        #self.model.setHorizontalHeaderLabels(['Destination'])
        self.proxyModel.setSourceModel(self.model)
        self.treeView.setModel(self.proxyModel)

        self.treeView.clicked.connect(self.itemClicked)
        self.model.itemChanged.connect(self.itemChanged)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)
        # self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.header = self.treeView.header()
        self.treeView.setHeaderHidden(True)
        self.header.setStretchLastSection(True)
        # self.header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # self.header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)

        self.toolTypeScrollArea = QScrollArea()
        self.toolWidget = QListWidget()
        self.toolTypeScrollArea.setWidget(self.treeView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        #self.toolTypeScrollArea.setFixedWidth(148)
        self.toolTypeScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.optionUIScrollArea = QScrollArea()
        self.optionUIScrollArea.setWidgetResizable(True)
        self.optionUIScrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.optionUIScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.toolLayout = QVBoxLayout()

        self.toolWidget.setLayout(self.toolLayout)

        self.leftLayout = QVBoxLayout()
        self.toolLabel = QLabel('Tools')
        self.leftLayout.addWidget(self.toolLabel)
        self.leftLayout.addWidget(self.filterLineEdit)
        self.leftLayout.addWidget(self.toolTypeScrollArea)

        self.win.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.leftLayout)

        self.update()
        self.resize(self.sizeHint())

    def displayToolOptions(self, index):
        pass
        self.toolOptionStack.setCurrentIndex(index)
        self.toolHotkeyStack.setCurrentIndex(index)

    def showUI(self):
        self.buildUI()
        self.win.show()
        self.initColor()
        self.populateTreeView()

    def filterRegExpChanged(self, value):
        self.proxyModel.setFilterRegExp(value.lower())
        if len(value) >= 1 and self.proxyModel.rowCount() > 0:
            self.treeView.expandAll()
        else:
            self.treeView.collapseAll()

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        # print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        # print item
        # print item.text(
        if modifiers == Qt.ControlModifier:
            self.pressedSignal.emit(item.text())
        else:
            self.selectedSignal.emit(item.text())

    def applyToSelected(self):
        index = self.treeView.selectedIndexes()[0]
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.applySignal.emit(item.text())

    def itemChanged(self, item):
        pass
        # print 'old value', item.destination
        # print 'new value', item.text()

    def populateTreeView(self):
        for index, cat in enumerate(self.commandCategories.keys()):
            categoryItem = QStandardItem(cat)
            categoryItem.setEditable(False)

            for command in self.commandCategories[cat]:
                hotkey = QStandardItem(command.replace('NameCommand', ''))
                hotkey.setEditable(False)

                categoryItem.appendRow(hotkey)
            self.model.appendRow(categoryItem)
            # span container columns
            self.treeView.setFirstColumnSpanned(index, self.treeView.rootIndex(), True)

# class for holding hotkey command info
class tb_hkey(object):
    def __init__(self, name="", annotation="", category="tb_tools", language='python', command=[""]):
        self.name = name
        self.annotation = annotation
        self.category = category
        self.language = language
        self.command = self.collapse_command_list(command)

    def collapse_command_list(self, command):
        cmd = ""
        for lines in command:
            cmd = cmd + lines + "\n"
        return cmd


def make_command_list():
    command_list = []

    # keyframing tools
    cat = 'tbtools_importExport'
    command_list.append(tb_hkey(name='mocapImporter', annotation='mocap import window',
                                category=cat, command=['import apps.rig.mocapLinker.mocapImporter as mi',
                                                       'reload(mi)',
                                                       'mWindow = mi.mocapWindow(mi.mayaMainWindow())',
                                                       'mWindow.show()']))
    cat = 'tbtools_keyframing'
    command_list.append(tb_hkey(name='flatten_control', annotation='flattens the control out',
                                category=cat, command=['import tb_flatten as tbf',
                                                       'reload(tbf)',
                                                       'tbf.level()']))
    command_list.append(tb_hkey(name='lazy_cycle_anim', annotation='lazy_cycle_maker',
                                category=cat, command=['import animCycle.tb_cycler as tbs',
                                                       'reload(tbs)',
                                                       'tbs.cycler().go()']))

    command_list.append(tb_hkey(name='smart_frame_curves', annotation='smart framing of keys, or focus on selection',
                                category=cat, command=['import tb_graphEditor as ge',
                                                       'reload(ge)',
                                                       'ge.graphEditor().smart_frame()']))
    command_list.append(
        tb_hkey(name='smart_open_graphEditor', annotation='smart framing of keys, and opens the graph editor',
                category=cat, command=['import tb_graphEditor as ge',
                                       'reload(ge)',
                                       'ge.graphEditor().open_graph_editor()']))

    # push and pull
    command_list.append(
        tb_hkey(name='tb_pull_left', annotation='scale values down, from left',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().push_and_pull(\"pull\", \"left\")']))
    command_list.append(
        tb_hkey(name='tb_pull_right', annotation='scale values down, from left',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().push_and_pull(\"pull\", \"right\")']))
    command_list.append(
        tb_hkey(name='tb_push_left', annotation='scale values down, from left',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().push_and_pull(\"push\", \"left\")']))
    command_list.append(
        tb_hkey(name='tb_push_right', annotation='scale values down, from right',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().push_and_pull(\"push\", \"right\")']))
    command_list.append(
        tb_hkey(name='tb_negate_left', annotation='flip values, from left',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().negate_keys(\"left\")']))
    command_list.append(
        tb_hkey(name='tb_negate_right', annotation='flip values, from right',
                category=cat, command=['import tb_keyMod as tbkm',
                                       'reload(tbkm)',
                                       'tbkm.keyTools().negate_keys(\"right\")']))

    return command_list


class hotkey_cleanup(object):
    def __init__(self, commands_to_delete=[]):
        self.command_list = commands_to_delete
        self.showUI()
        pass

    def remove_hotkey(self, command_name, layout_name):
        pm.runTimeCommand(command_name, edit=True, delete=True)
        pm.deleteUI(layout_name)

    def ignore_hotkey(self, command_name, layout_name):
        pm.optionVar(stringValueAppend=('tb_extra_commands', command_name))
        pm.rowLayout(layout_name, edit=True, bgc=(0.2, 0.6, 0.2))

    def command_widget(self, command_name="", parent=""):
        rLayout = pm.rowLayout(numberOfColumns=4, adjustableColumn=2, parent=parent)
        pm.text(label="command:", parent=rLayout)
        pm.text(label=str(command_name), parent=rLayout)

        pm.button(label="keep", parent=rLayout, command=lambda *args: self.ignore_hotkey(command_name, rLayout))
        pm.button(label="delete", parent=rLayout, command=lambda *args: self.remove_hotkey(command_name, rLayout))

    def showUI(self):
        window = pm.window(title="hotkey check!")
        layout = pm.columnLayout(adjustableColumn=True)
        pm.text(font="boldLabelFont", label="Uknown or outdated commands")
        pm.text(label="")

        pm.text(label="your own commands saved in tbtools categories")
        pm.text(label="will show up here. If you wish to keep them,")
        pm.text(label="press the 'keep' button and they won't appear")
        pm.text(label="in this window again.")
        pm.text(label="")
        pm.text(label="If you didn't make it and it's here it means it")
        pm.text(label="is an old or outdated hotkey and should be removed")
        pm.text(label="")

        for items in self.command_list:
            self.command_widget(command_name=items, parent=layout)

        # pm.button( label='Delete all', parent=layout)
        pm.button(label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        pm.setParent('..')
        pm.showWindow(window)
