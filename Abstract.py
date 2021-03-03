import abc
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
# maya module imports
import maya.cmds as cmds
from apps.tb_functions import functions


class hotKeyAbstractFactory(object):
    __metaclass__ = abc.ABCMeta
    category = 'tbtools'
    commandList = list()

    def __init__(self, **kwargs):
        pass

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def setCategory(self, category):
        self.category = category

    def addCommand(self, command):
        self.commandList.append(command)

    @abc.abstractmethod
    def createHotkeyCommands(self):
        return cmds.warning(self, 'createHotkeyCommands', ' function not implemented')

    @abc.abstractmethod
    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')

    class tb_hkey(object):
        def __init__(self, name="", annotation="", category="tb_tools", language='python', command=[""]):
            self.name = name
            self.annotation = annotation
            self.category = category
            self.language = language
            self.command = self.collapse_command_list(command)
            self.hotkeyName = self.name + 'NameCommand'

        def collapse_command_list(self, command):
            lineCmds = list()
            for line in command:
                tool, functionCalled = line.split('.')
                lineCmds.append(('tbtoolCLS.tools["%s"].%s') % (tool, functionCalled))

            tryCmd = ['global tbtoolCLS',
                      'try:']
            exceptCmd = [
                'except:',
                '\tfrom pluginLookup import ClassFinder',
                '\ttbtoolCLS = ClassFinder()']
            cmd = ""
            for lines in tryCmd:
                cmd = cmd + lines + "\n"
            for lines in lineCmds:
                cmd = cmd + '\t' + lines + "\n"
            for lines in exceptCmd:
                cmd = cmd + lines + "\n"
            for lines in lineCmds:
                cmd = cmd + '\t' + lines + "\n"
            return cmd


class toolAbstractFactory(object):
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'baseTool'
    hotkeyClass = None
    funcs = None

    layout = None

    def __new__(cls):
        if toolAbstractFactory.__instance is None:
            toolAbstractFactory.__instance = object.__new__(cls)

        toolAbstractFactory.__instance.val = cls.toolName
        return toolAbstractFactory.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotKeyAbstractFactory()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    @abc.abstractmethod
    def optionUI(self):
        self.layout = QFormLayout()
        label = QLabel(self.toolName)
        self.layout.addWidget(label)
        return self.layout

    @abc.abstractmethod
    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')
