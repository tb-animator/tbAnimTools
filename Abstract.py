from __future__ import print_function
import abc
import re
import os
import maya.cmds as cmds
import maya.mel as mel
import json
import textwrap
import shutil
from functools import partial

# maya module imports

from tb_mainFunctions import Functions
from tb_mainUtility import *
from callback import create_callback
import tb_mainHelpStrings

from apps.tb_UI import *
import apps.tb_fileTools as ft

# compatible with Python 2 *and* 3:
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

class hotKeyAbstractFactory(ABC):
    # __metaclass__ = abc.ABCMeta
    category = 'tbtools'
    commandList = list()
    helpStrings = tb_mainHelpStrings

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
        return

    @abc.abstractmethod
    def assignHotkeys(self):
        return

    class tb_hkey(object):
        def __init__(self, name="",
                     annotation="",
                     category="tb_tools",
                     niceName=None,
                     ctx=str(),
                     language='python',
                     command=[""], help=str()):
            self.name = name
            if not niceName:
                niceName = name
            self.niceName = niceName
            self.annotation = annotation
            self.ctx = ctx
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
                helpLines = help.split('__')
                for helpLine in helpLines:
                    cmd += textwrap.fill(helpLine, 60)
                    cmd += "\n"
                cmd += "\n\n"
            cmd += '----------------------------------------------------"""'
            return cmd


class toolAbstractFactory(ABC):
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'baseTool'

    hotkeyClass = None
    funcs = None
    allTools = None

    layout = None
    classData = dict()
    rawJsonData = None
    assetCommandName = 'blankCommandName'
    assetTitleLabel = 'Empty'

    dependentPlugins = list()
    deferredLoadJob = None
    deferredLoadDone = False
    rootDirectory = os.path.dirname(__file__)

    bookendBakeOption = 'tbBookendBake'
    bookendBakeHighlightOption = 'tbBookendBakeHighlight'
    mainDataOption = 'tb_mainDataOption'

    def __new__(cls):
        if toolAbstractFactory.__instance is None:
            toolAbstractFactory.__instance = object.__new__(cls)

        toolAbstractFactory.__instance.val = cls.toolName
        return toolAbstractFactory.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotKeyAbstractFactory()
        self.funcs = Functions()
        self.dataPath = None
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

    def hotkeyUI(self):
        toolUIName = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", self.toolName)
        self.hotkeyWidget = optionWidget(label=toolUIName)
        self.layout = self.hotkeyWidget.layout
        return self.hotkeyWidget

    @abc.abstractmethod
    def showUI(self):
        return None

    @abc.abstractmethod
    def drawMenuBar(self, parentMenu):
        return None

    def initData(self):
        baseDataPath = get_option_var(self.mainDataOption, os.path.normpath(os.path.dirname(__file__)))
        self.dataPath = os.path.join(baseDataPath, 'appData')
        if not os.path.isdir(self.dataPath):
            os.makedirs(self.dataPath)
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

    def revertAppData(self):
        set_option_var('mainDataOption', os.path.normpath(os.path.dirname(__file__)))
        mel.eval('SavePreferences')
        raiseOk('appData location reverted to default/n'
                'RESTART MAYA NOW',
                title='RESTART MAYA NOW')

    def copyAppData(self):
        """
        Copy the appData folder to a nother location
        :return:
        """
        baseDataPath = get_option_var(self.mainDataOption, os.path.normpath(os.path.dirname(__file__)))
        dataPath = os.path.join(baseDataPath, 'appData')
        selected_directory = ft.selectDirectory(baseDataPath)
        if not selected_directory:
            return
        if selected_directory == self.dataPath:
            return cmds.warning('Cannot copy to that location')
        # get the subfolder appData
        result_directory = os.path.join(selected_directory, 'appData')
        # copy the whole existing folder structure to the new location
        try:
            shutil.copytree(dataPath, result_directory)
            # set the current data path to the new location
            self.dataPath = selected_directory
            # set the option variable and save preferences
            set_option_var(self.mainDataOption, selected_directory)
            mel.eval('SavePreferences')
        except:
            raiseError('Failed to copy appData folder to new location')
            return
        finally:
            raiseOk('Copied appData folder to new location RESTART MAYA NOW',
                    title='RESTART MAYA NOW')

    def loadData(self):
        self.initData()
        if not os.path.isfile(self.dataFile):
            self.saveData()
        self.rawJsonData = json.load(open(self.dataFile))

    def loadRigData(self, dataCLS, rigName):
        subPath = os.path.join(self.dataPath, self.toolName)
        dataCLS.fromJson(os.path.join(subPath, rigName + '.json'))
        return dataCLS

    def saveRigData(self, refname, jsonData):
        """
        Pass in a json object
        :param dataCLS:
        :param rigName:
        :return:
        """
        dataFile = os.path.join(self.subPath, refname + '.json')
        self.saveJsonFile(dataFile, json.loads(jsonData))

    def saveRigFileIfNew(self, refname, jsonData):
        self.subPath = os.path.join(self.dataPath, self.toolName)
        if not os.path.isdir(self.subPath):
            os.mkdir(self.subPath)
        dataFile = os.path.join(self.subPath, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            self.saveJsonFile(dataFile, json.loads(jsonData))

    def updatePreview(self, scale=1, optionVar=str(), drawType='orb'):
        if not cmds.objExists('temp_Preview'):
            self.drawPreview(optionVar=optionVar, drawType=drawType)

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)

    def drawPreview(self, optionVar=str(), drawType='orb'):
        self.funcs.tempControl(name='temp',
                               suffix='Preview',
                               scale=get_option_var(optionVar, 1),
                               drawType=drawType)

    def createAsset(self, name, imageName=None, transform=False, assetTag=str(), assetCommandName=str()):
        if transform:
            asset = cmds.container(name=name,
                                   includeHierarchyBelow=False,
                                   includeTransform=True,
                                   type='dagContainer',
                                   )
        else:
            asset = cmds.container(name=name,
                                   includeHierarchyBelow=False,
                                   includeTransform=True,
                                   )
        if imageName:
            cmds.setAttr(asset + '.iconName', imageName, type="string")
        if assetTag:
            cmds.addAttr(asset, ln='assetTag', dt='string')
            cmds.setAttr(asset + '.assetTag', assetTag, type="string")
        if not assetCommandName:
            cmds.setAttr(asset + '.rmbCommand', self.assetCommandName, type='string')
        else:
            cmds.setAttr(asset + '.rmbCommand', assetCommandName, type='string')

        return asset

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

    def animLayerTabUI(self):
        return list()

    def deferredLoad(self):
        pass

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = cmds.ls(sl=True)
        asset = cmds.container(query=True, findContainer=sel[0])

        cmds.menuItem(label=self.assetTitleLabel, enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Bake selected temp pivots to layer',
                      command=create_callback(self.bakeSelectedCommand, asset, sel))
        cmds.menuItem(label='Bake all temp pivots to layer', command=create_callback(self.bakeAllCommand, asset, sel))
        # cmds.menuItem(label='Bake out to layer', command=create_callback(self.bakeOutCommand, asset))
        cmds.menuItem(label='Delete all temp pivots', command=create_callback(self.deleteControlsCommand, asset, sel))
        cmds.menuItem(divider=True)

    def bakeSelectedCommand(self, asset, sel, *args):
        targets = [x for x in sel if cmds.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [cmds.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)
        self.allTools.tools['BakeTools'].quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                                                   deleteConstraints=True)
        cmds.delete(filteredTargets)

    def bakeAllCommand(self, asset, sel, *args):
        nodes = cmds.ls(cmds.container(asset, query=True, nodeList=True), transforms=True)
        targets = [x for x in nodes if cmds.attributeQuery(self.constraintTargetAttr, node=x, exists=True)]
        filteredTargets = [cmds.listConnections(x + '.' + self.constraintTargetAttr)[0] for x in targets]
        bakeRange = self.funcs.getBakeRange(filteredTargets)
        self.allTools.tools['BakeTools'].quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                                                   deleteConstraints=True)
        cmds.delete(asset)

    def deleteControlsCommand(self, asset, sel, *args):
        cmds.delete(asset)
