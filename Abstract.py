from __future__ import print_function
import abc
import re
import os
import pymel.core as pm
import maya.mel as mel
import json

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
# maya module imports
import maya.cmds as cmds
from apps.tb_functions import functions
import tb_helpStrings
from apps.tb_qtMarkingMenu import MarkingMenuItem
from apps.tb_UI import *

# compatible with Python 2 *and* 3:
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class hotKeyAbstractFactory(ABC):
    # __metaclass__ = abc.ABCMeta
    category = 'tbtools'
    commandList = list()
    helpStrings = tb_helpStrings

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
        def __init__(self, name="", annotation="", category="tb_tools", language='python', command=[""], help=[""]):
            self.name = name
            self.annotation = annotation
            self.category = category
            self.language = language
            self.command = self.collapse_command_list(command, help)
            self.hotkeyName = self.name + 'NameCommand'

        def collapse_command_list(self, command, help):
            lineCmds = list()
            for line in command:
                tool, functionCalled = line.split('.')
                lineCmds.append(('tbtoolCLS.tools["%s"].%s') % (tool, functionCalled))

            tryCmd = ['global tbtoolCLS',
                      'try:',
                      '\ttbtoolCLS = ClassFinder()'
                      ]
            exceptCmd = [
                'except:',
                '\tfrom pluginLookup import ClassFinder',
                '\ttbtoolCLS = ClassFinder()']
            cmd = ""
            for lines in tryCmd:
                cmd += lines + "\n"
            for lines in exceptCmd:
                cmd += lines + "\n"
            for lines in lineCmds:
                cmd += lines + "\n"
            cmd += "\n\n"
            cmd += '"""About ----------------------------------------------\n'
            if help:
                for lines in help:
                    cmd += lines + "\n"
            cmd += '----------------------------------------------------"""'
            return cmd


class toolAbstractFactory(ABC):
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'baseTool'

    hotkeyClass = None
    funcs = None

    layout = None
    classData = dict()
    rawJsonData = None

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
        toolUIName = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", self.toolName)
        self.optionWidget = optionWidget(label=toolUIName)
        self.layout = self.optionWidget.layout
        return self.optionWidget

    @abc.abstractmethod
    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    @abc.abstractmethod
    def drawMenuBar(self, parentMenu):
        return None

    def initData(self):
        self.dataPath = os.path.join(os.path.normpath(os.path.dirname(__file__)), 'appData')
        if not os.path.isdir(self.dataPath):
            os.mkdir(self.dataPath)
        self.dataFile = os.path.join(self.dataPath, self.toolName + '.json')

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)

    def saveData(self):
        self.initData()
        self.toJson()
        self.saveJsonFile(self.dataFile, self.classData)

    def saveJsonFile(self, filePath, data):
        fileName = os.path.join(filePath)
        jsonString = json.dumps(data, indent=4, separators=(',', ': '))
        jsonFile = open(fileName, 'w')

        jsonFile.write(jsonString)
        jsonFile.close()

    def loadData(self):
        self.initData()
        if not os.path.isfile(self.dataFile):
            self.saveData()
        self.rawJsonData = json.load(open(self.dataFile))

    def openMM(self):
        if cmds.popupMenu('tempMM', exists=True):
            cmds.deleteUI('tempMM')
        cmds.popupMenu('tempMM',
                       button=1,
                       ctl=False,
                       alt=False,
                       allowOptionBoxes=True,
                       parent=mel.eval("findPanelPopupParent"),
                       mm=True)
        self.build_MM()
        cmds.setParent('..', menu=True)

    def build_MM(self):
        pass

    def closeMM(self):
        if cmds.popupMenu('tempMM', exists=True):
            cmds.deleteUI('tempMM')

    def qtMarkingMenu(self, inputNodes):
        return list()