import importlib, inspect
import os
import copy
import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as om2a

from Abstract import *


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
        self.toolsDirectory = os.path.join(self.directory, self.toolsBaseDirectory)
        self.proToolsDirectory = os.path.join(self.directory, self.proToolsBaseDirectory)
        #print 'startup', self.toolsDirectory
        self.loadPluginsByClass()

    def loadPluginsByClass(self):
        #print '!! loadPluginsByClass !!'
        #print 'toolsBaseDirectory', self.toolsBaseDirectory, 'toolsDirectory', self.toolsDirectory
        #print 'toolsBaseDirectory', self.proToolsBaseDirectory, 'proToolsDirectory', self.proToolsDirectory
        self.allClasses = [cls for cls in
                           self.getAllModulesInFolder(self.toolsBaseDirectory, self.toolsDirectory)
                           if cls]
        self.allProClasses = [cls for cls in
                           self.getAllModulesInFolder(self.proToolsBaseDirectory, self.proToolsDirectory)
                           if cls]
        #print 'allProClasses', self.allProClasses
        self.allClasses.extend(self.allProClasses)
        hotkeyClasses = [cls for cls in self.allClasses if cls.__base__ == hotKeyAbstractFactory]
        toolClasses = [cls for cls in self.allClasses if cls.__base__ == toolAbstractFactory]
        #print 'toolClasses'
        '''
        for t in toolClasses:
            print '\t', t
        print '\n\n'
        '''
        self.tools = dict()
        for cls in toolClasses:
            print ('instancing tool', cls, cls.toolName)
            self.tools[cls.toolName] = cls()
        self.loadedClasses['hotkeys'] = hotkeyClasses

    def getAllModulesInFolder(self, baseDirectory, tooldDirectory):
        allFiles = list()
        for (dirpath, dirnames, filenames) in os.walk(tooldDirectory):
            allFiles += [os.path.join(dirpath, file) for file in filenames]

        for file in allFiles:
            if file not in ['__init__.py', '__pycache__']:  # skip unneeded files
                if file[-3:] != '.py':
                    continue

                file_name = os.path.basename(file.split('.')[0])
                subFolder = str(os.path.relpath(os.path.dirname(file), tooldDirectory)).replace('\\', '.')

                module_name = ('%s%s%s') % (baseDirectory, subFolder, file_name)
                # hacky check to see if the script is in the start folder
                if subFolder == '.':
                    module_name = baseDirectory + '.' + file_name
                else:
                    module_name = baseDirectory + '.' + subFolder + '.' + file_name
                for name, cls in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
                    if cls.__module__ == module_name:
                        yield cls

    def startupScriptJobs(self):
        if self.animLayerScriptJob is not -1:
            self.animLayerScriptJob = pm.scriptJob(event=('aninLayerRebuild', self.colourAnimLayers))

    def colourAnimLayers(self):
        print ('colourAnimLayers')