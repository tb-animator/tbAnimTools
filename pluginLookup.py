import importlib, inspect
import sys
import os
import copy
import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as om2a
import traceback
from Abstract import *

import zipfile


# paths

# baseDir = os.path.split(dir)[-1]
# toolBaseModule = 'animTools'
# toolsDir = os.path.join(dir, toolBaseModule)

class ClassFinder(object):
    """
    Used to look through sub folders to find classes of a type
    Singleton so can be called form anywhere
    """
    __instance = None
    name = 'hotKeyFinder'
    directory = None
    baseDirectory = None
    toolsBaseDirectory = 'apps'
    proToolsBaseDirectory = 'proApps'
    toolsDirectory = None
    proToolsDirectory = None

    loadedClasses = dict()
    allClasses = list()
    tools = dict()

    animLayerScriptJob = -1
    animLayerTabLeftLayout = None
    animLayerTabRightLayout = None

    def __new__(cls):
        if ClassFinder.__instance is None:
            ClassFinder.__instance = object.__new__(cls)

        ClassFinder.__instance.val = 'classFinder'
        return ClassFinder.__instance

    def __init__(self):
        pass

    def startup(self):
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.baseDirectory = os.path.split(self.directory)[-1]
        self.toolsBaseDirectory = 'apps'
        self.proToolsBaseDirectory = 'proApps'
        self.proToolsVerionDirectory = 'proApps'
        self.toolsDirectory = os.path.join(self.directory, self.toolsBaseDirectory)
        if sys.version_info >= (2, 8):
            self.proToolsDirectory = os.path.join(self.directory, self.proToolsBaseDirectory, 'Python3')
            self.proToolsVerionDirectory = 'proApps.Python3'
        else:
            self.proToolsDirectory = os.path.join(self.directory, self.proToolsBaseDirectory, 'Python2')
            self.proToolsVerionDirectory = 'proApps.Python2'

        self.loadPluginsByClass()
        self.applyAnimLayerTabModification()
        self.applyToolDeferredLoad()

    def loadPluginsByClass(self):
        self.allClasses = [cls for cls in
                           self.getAllModulesInFolder(self.toolsBaseDirectory, self.toolsDirectory)
                           if cls]
        self.allProClasses = [cls for cls in
                              self.getAllModulesInFolder(self.proToolsVerionDirectory, self.proToolsDirectory,
                                                         compiledOnly=True)
                              if cls]

        self.allClasses.extend(self.allProClasses)
        hotkeyClasses = [cls for cls in self.allClasses if cls.__base__ == hotKeyAbstractFactory]
        toolClasses = [cls for cls in self.allClasses if cls.__base__ == toolAbstractFactory]

        self.tools = dict()
        for cls in toolClasses:
            print (cls)
            tool = None
            try:
                tool = cls()
            except Exception:
                cmds.warning('Failing to load class ::', str(cls))
                cmds.warning(traceback.format_exc())
                continue
            if not tool:
                continue
            self.tools[cls.toolName] = cls()
            if not self.tools[cls.toolName]:
                continue
            self.tools[cls.toolName].allTools = self

        self.loadedClasses['hotkeys'] = hotkeyClasses
        self.loadAllDependentPlugins()

    def loadAllDependentPlugins(self):
        allPlugins = [x.dependentPlugins for x in self.tools.values()]
        allPlugins = [plugin for dependentPlugins in allPlugins for plugin in dependentPlugins if plugin]
        print ('loadAllDependentPlugins', allPlugins)

        if not allPlugins:
            return

        for plugin in allPlugins:
            try:
                cmds.evalDeferred(
                    'if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin))
                cmds.evalDeferred(
                    'if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin))
            except Exception:
                cmds.warning('Failing to load Plugin ::', str(plugin))

    def getAllModulesInFolder(self, baseDirectory, toolDirectory, compiledOnly=False):
        allFiles = list()
        for (dirpath, dirnames, filenames) in os.walk(toolDirectory):
            allFiles += [os.path.join(dirpath, file) for file in filenames]
        ignored = ['__init__', '__pycache__']
        for file in allFiles:
            if any(x in file for x in ignored):  # skip unneeded files
                continue

            if compiledOnly:
                if file.rsplit('.', 1)[-1] != 'pyc':
                    continue
            else:
                if file.rsplit('.', 1)[-1] != 'py':
                    continue

            file_name = os.path.basename(file.rsplit('.', 1)[0])
            subFolder = str(os.path.relpath(os.path.dirname(file), toolDirectory)).replace('\\', '.')

            # hacky check to see if the script is in the start folder
            if subFolder == '.':
                module_name = baseDirectory + '.' + file_name
            else:
                module_name = baseDirectory + '.' + subFolder + '.' + file_name

            for name, cls in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
                if cls.__module__ == module_name:
                    yield cls

    def collectQtMarkingMenuData(self, selection):
        menuDataDict = dict()
        if not selection:
            return None
        for tool, cls in self.tools.items():
            print (tool, cls)
            if not cls:
                continue
            menuDataDict[tool] = cls.qtMarkingMenu(selection)
        return menuDataDict

    def collectAnimLayerTabWidgets(self):
        widgets = list()
        for tool, cls in self.tools.items():
            if not cls:
                continue
            widgets.extend(cls.animLayerTabUI())
        return widgets

    def applyToolDeferredLoad(self):
        for tool, cls in self.tools.items():
            try:
                cls.deferredLoad()
            except Exception:
                cmds.warning('Deferred Load Failing for class ::', str(cls))
                cmds.warning(traceback.format_exc())

    def applyAnimLayerTabModification(self):
        try:
            animLayerLayouts = self.tools['LayerEditor'].modifyAnimLayerTab()
            if not animLayerLayouts:
                return
            widgets = self.collectAnimLayerTabWidgets()
            for widget in widgets:
                animLayerLayouts[-1].insertWidget(0, widget)
        except Exception:
            cmds.warning('Failing to modify animLayerTab ::', cmds.warning(traceback.format_exc()))

    def startupScriptJobs(self):
        if self.animLayerScriptJob is not -1:
            self.animLayerScriptJob = pm.scriptJob(event=('aninLayerRebuild', self.colourAnimLayers))

    def colourAnimLayers(self):
        print ('colourAnimLayers')

    def installFromZip(self, filename):
        print ('installFromZip', filename)
        self.directory = os.path.dirname(os.path.abspath(__file__))
        self.baseDirectory = os.path.split(self.directory)[-1]
        destinationPath = os.path.join(self.directory, self.proToolsBaseDirectory)
        destinationP2 = os.path.join(destinationPath, 'Python2')
        destinationP3 = os.path.join(destinationPath, 'Python3')
        if not os.path.isdir(destinationP2):
            os.mkdir(destinationP2)
        if not os.path.isdir(destinationP3):
            os.mkdir(destinationP3)
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            print ('destinationPath', destinationPath)
            zip_ref.extractall(destinationPath)
        self.loadPluginsByClass()

    def installFromZipUI(self):
        wd = PluginExtractor(self)
        wd.show()
        wd.installSignal.connect(self.installFromZip)
