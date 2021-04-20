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
        print 'loadedClasses hotkeys', self.classLookup.loadedClasses['hotkeys']
        self.allCommands = list()
        self.instantiateHotkeyClasses()
        self.getHotkeyCommandsFromLoadedClasses()
        self.allCommandNames = [command.name for command in self.allCommands]
        self.allCategories = list(set([command.category for command in self.allCommands]))
        print 'allCommands', self.allCommands
        print 'allCategories', self.allCategories
        self.getExistingCommands()
        self.updateCommands()
        self.removeBadCommands()

    def getHotkeyCommandsFromLoadedClasses(self):
        for cls in self.loadedHotkeyClasses:
            print 'loading hotkeys from class:: ', cls
            self.allCommands.extend(cls.createHotkeyCommands())

    def instantiateHotkeyClasses(self):
        if self.classLookup.loadedClasses['hotkeys']:
            self.loadedHotkeyClasses = [cls() for cls in self.classLookup.loadedClasses['hotkeys']]

    def assignHotkeysFromLoadedClasses(self):
        for cls in self.loadedHotkeyClasses:
            print 'assigning hotkeys from class:: ', cls
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
                              #edit=True,
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
        #print 'extra_commands', self.extra_commands
        needed_ignore_names = [item for item in self.existing_commands if item in self.existing_commands]
        #print needed_ignore_names
        return
        for items in self.extra_commands:
            if items in self.existing_commands:
                needed_ignore_names.append(items)

        pm.optionVar.pop('tb_extra_commands')
        for items in needed_ignore_names:
            pm.optionVar(stringValueAppend=('tb_extra_commands', items))

    def removeBadCommands(self):
        #print 'removeBadCommands...'
        #print 'existing_commands', self.existing_commands
        #print 'allCommandNames', self.allCommandNames
        #print 'extra_commands', self.extra_commands
        commands = [com for com in self.existing_commands if
                    com not in self.allCommandNames and com not in self.extra_commands]
        #print commands
        if commands:
            hotkey_cleanup(commands_to_delete=commands)


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
