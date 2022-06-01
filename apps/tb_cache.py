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

from Abstract import *

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
__author__ = 'tom.bailey'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='cacheSelectedCharacter',
                                     annotation='',
                                     category=self.category,
                                     command=['cacheTool.cacheSelectedCharacters()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class MeshData(object):
    def __init__(self):
        self.meshGroups = list()

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict['meshGroups'] = self.meshGroups
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))

        self.meshGroups = rawJsonData.get('meshGroups', list())


class CacheTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'cacheTool'
    hotkeyClass = hotkeys()
    funcs = functions()

    gpuCachExportOption = 'tbGpuCacheDir'
    gpuCachType_values = ['GPU', 'ALembic']
    gpuCachType_default = 'GPU'

    loadedMeshData = dict()
    namespaceToCharDict = dict()

    def __new__(cls):
        if CacheTool.__instance is None:
            CacheTool.__instance = object.__new__(cls)
            CacheTool.__instance.initData()

        CacheTool.__instance.val = cls.toolName
        CacheTool.__instance.loadPlugin(plugin='AbcExport')
        CacheTool.__instance.loadPlugin(plugin='gpuCache')
        return CacheTool.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(CacheTool, self).optionUI()

        dirWidget = filePathWidget(self.gpuCachExportOption, None)

        fileTypeWidget = radioGroupWidget(optionVarList=self.gpuCachType_values,
                                          optionVar=self.gpuCachType_default,
                                          defaultValue=self.gpuCachType_values[0], label='Output file type')

        self.layout.addWidget(dirWidget)
        self.layout.addWidget(fileTypeWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def loadPlugin(self, plugin='gpuCache'):

        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            try:
                cmds.loadPlugin(plugin, quiet=True)
                return True
            except:
                cmds.warning('failing to load %s plugin' % plugin)
                return False
        else:
            return False

    def getExportFolder(self):
        if not pm.optionVar.get(self.gpuCachExportOption, None):
            self.selectDirectory()

        return pm.optionVar.get(self.gpuCachExportOption, None)

    def selectDirectory(self, *args):
        dialog = QFileDialog(None, caption="Pick GPU Cache Folder")
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setWindowTitle("Pick GPU Cache Folder")
        dialog.setDirectory(self.dataPath)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_directory = dialog.getExistingDirectory()

        if selected_directory:
            pm.optionVar[self.gpuCachExportOption] = selected_directory

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        for key, value in characters.items():
            '''
            if not key:
                continue  # skip non referenced chars
            '''
            refname, namespace = self.funcs.getCurrentRig([value[0]])
            if namespace.startswith(':'):
                namespace = namespace.split(':', 1)[-1]
            namespaceToCharDict[namespace] = refname

            if refname not in self.loadedMeshData.keys():
                self.saveRigFileIfNew(refname, MeshData().toJson())

            spaceData = self.loadRigData(MeshData(), refname)
            self.loadedMeshData[refname] = spaceData
        self.namespaceToCharDict = namespaceToCharDict

    def defineMeshForCharacter(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        for s in sel:
            p = pm.PyNode(s)
            namespace = p.namespace()
            obj = p.stripNamespace()
            refname = self.namespaceToCharDict[namespace]

            if obj not in self.loadedMeshData[refname].meshGroups:
                self.loadedMeshData[refname].meshGroups.append(obj)
        self.saveRigData(refname, self.loadedMeshData[refname].toJson())

    def cacheSelectedCharacters(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        allMeshes = list()
        for ns in characters.keys():
            meshes = self.getSkinCLustersForNamespace(ns)
            allMeshes.extend(meshes)
        file = cmds.file(query=True, sceneName=True, shortName=True)
        file = file.split('.')[0]
        self.exportCache(meshes, name=file + '_' + ns)

    def getSkinCLustersForNamespace(self, ns):
        skinClusters = pm.ls(ns + ':*', type='skinCluster')
        meshes = [str(a) for b in [n.outputGeometry.connections() for n in skinClusters] for a in b if a]
        visibleMeshes = [m for m in meshes if self.isNodeVisible(m)]
        return visibleMeshes

    def exportCache(self, exportObjects, name='test'):
        startTime = cmds.playbackOptions(query=True, min=True)
        endTime = cmds.playbackOptions(query=True, max=True)
        outputFolder = self.getExportFolder()
        if not outputFolder:
            return cmds.warning('No output folder selected')
        cmds.gpuCache(exportObjects,
                      startTime=startTime,
                      endTime=endTime,
                      dataFormat='ogawa',
                      optimize=True,
                      optimizationThreshold=40000,
                      writeMaterials=False,
                      directory=outputFolder,
                      fileName=name,
                      saveMultipleFiles=False)

    def importCache(self, filename):
        cacheNode = pm.createNode('gpuCache')
        cacheNodeParent = cacheNode.getParent()
        cacheNodeParent.rename(str(os.path.basename(filename)).split('.')[0])
        cacheNode.cacheFileName.set(str(filename))

    def importCacheDialog(self):
        fileFilter = "gpu cache (*.abc)"
        importedFiles = cmds.fileDialog2(fileFilter=fileFilter,
                               fileMode=4,
                               dialogStyle=1,
                               startingDirectory=self.getExportFolder())
        if not importedFiles:
            return

        for f in importedFiles:
            self.importCache(f)

    def isNodeVisible(self, node):
        if not cmds.objExists(node):
            return False
        if not cmds.attributeQuery("visibility", node=node, exists=True):
            return False
        visible = cmds.getAttr(node + '.visibility')
        if not visible:
            return False
        parents = cmds.listRelatives(node, parent=True)
        if parents:
            visible = self.isNodeVisible(parents[0])
        return visible
