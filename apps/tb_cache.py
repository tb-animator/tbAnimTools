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
"""
TODO - add option for combining selections into one cache object, feature to reload multiple references from one cache
"""
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
                                     command=['CacheTool.cacheSelectedCharacters()']))
        self.addCommand(self.tb_hkey(name='cacheSelectedCharacterUnload',
                                     annotation='',
                                     category=self.category,
                                     command=['CacheTool.cacheSelectedCharacters(disableReferences=True)']))
        self.addCommand(self.tb_hkey(name='importCache',
                                     annotation='Open a file dialog to import cache files',
                                     category=self.category,
                                     command=['CacheTool.importCacheDialog()']))
        self.addCommand(self.tb_hkey(name='loadReferenceFromCache',
                                     annotation='',
                                     category=self.category,
                                     command=['CacheTool.loadReferenceFromCacheSelected()']))
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
    toolName = 'CacheTool'
    hotkeyClass = hotkeys()
    funcs = functions()

    gpuCachExportOption = 'tbGpuCacheDir'
    gpuCachImportTypeOption = 'tbGpuCacheType'
    gpuCacheType_values = ['GPU', 'ALembic']
    gpuCacheType_default = 'GPU'

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

        fileTypeWidget = radioGroupWidget(optionVarList=self.gpuCacheType_values,
                                          optionVar=self.gpuCachImportTypeOption,
                                          defaultValue=self.gpuCacheType_values[0], label='Import mode')

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

    def cacheSelectedCharacters(self, disableReferences=False):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        fileName = cmds.file(query=True, sceneName=True, shortName=True)
        fileName = fileName.split('.')[0]

        allMeshes = list()
        for ns in characters.keys():
            meshes = self.getSkinCLustersForNamespace(ns)
            allMeshes.extend(meshes)

            outputFile = self.exportCache(meshes, name=fileName + '_' + ns)
            refNode, fileReference = self.getReference(meshes[0])
            cacheNode = self.importCache(outputFile)
            if refNode:
                cmds.addAttr(str(cacheNode), ln='refNode', dt='string')
                cmds.setAttr(str(cacheNode) + '.refNode', refNode, type='string')
            if disableReferences:
                self.unloadReference(refNode)

    def unloadReference(self, refNnode):
        cmds.file(unloadReference=refNnode)

    def loadReferenceFromCache(self, cacheNode):
        if not cmds.attributeQuery('refNode', node=cacheNode, exists=True):
            return
        refNode = cmds.getAttr(cacheNode + '.refNode', asString=True)
        cmds.file(loadReferenceDepth="asPrefs", loadReference=refNode)
        cmds.delete(cacheNode)

    def loadReferenceFromCacheSelected(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            self.loadReferenceFromCache(s)

    def getSkinCLustersForNamespace(self, ns):
        skinClusters = pm.ls(ns + ':*', type='skinCluster')
        meshes = [str(a) for b in [n.outputGeometry.connections() for n in skinClusters] for a in b if a]
        visibleMeshes = [m for m in meshes if self.isNodeVisible(m)]
        return visibleMeshes

    def exportCache(self, exportObjects, name='test', abc=True):
        startTime = cmds.playbackOptions(query=True, min=True)
        endTime = cmds.playbackOptions(query=True, max=True)
        outputFolder = self.getExportFolder()
        if not outputFolder:
            return cmds.warning('No output folder selected')
        if abc:
            pm.select(exportObjects)
            objs = pm.ls(sl=True, long=True)
            objString = ['-root ' + str(o) for o in objs]
            objString = ' '.join(objString)
            filePath = os.path.join(outputFolder, name + '.abc')
            filePath = filePath.replace('\\', '/')

            cmdString = 'AbcExport -j "-frameRange {startTime} {endTime} -ro -worldSpace -dataFormat ogawa {objString} -file {fileName}"'.format(
                fileName=filePath,
                objString=objString,
                startTime=int(startTime),
                endTime=int(endTime),
            )
            print (cmdString)
            mel.eval(cmdString)
        else:
            cmds.gpuCache(exportObjects,
                          startTime=startTime,
                          endTime=endTime,
                          dataFormat='ogawa',
                          optimize=True,
                          optimizationThreshold=40000,
                          writeMaterials=True,
                          directory=outputFolder,
                          fileName=name,
                          saveMultipleFiles=False)
        return os.path.join(outputFolder, name + '.abc')

    def importCache(self, filename, pointCloud=False, alembic=False):
        mode = None
        if pointCloud:
            mode = self.gpuCacheType_values[0]
        if alembic:
            mode = self.gpuCacheType_values[1]
        if not mode:
            mode = pm.optionVar.get(self.gpuCachImportTypeOption, self.gpuCacheType_default)
            print ('mode', mode)
        if mode == self.gpuCacheType_values[0]:
            cacheNode = pm.createNode('gpuCache')
            cacheNodeParent = cacheNode.getParent()
            cacheNodeParent.rename(str(os.path.basename(filename)).split('.')[0])
            cacheNode.cacheFileName.set(str(filename))
        else:
            cacheNodeParent = self.funcs.tempControl(name=str(os.path.basename(filename)).split('.')[0],
                                                     suffix='Root',
                                                     drawType='flatRotator')
            alembicNode = cmds.AbcImport(filename, mode="import")
            cacheNodes = cmds.listConnections(alembicNode + '.outPolyMesh')
            pm.parent(cacheNodes, cacheNodeParent)
            pm.addAttr(cacheNodeParent, ln='alembic', at='message')
            pm.connectAttr(alembicNode + '.message', cacheNodeParent + '.alembic')
        return cacheNodeParent

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

    def getReference(self, obj):
        refState = cmds.referenceQuery(str(obj), isNodeReferenced=True)

        if refState:
            # if it is referenced, check against pickwalk library entries
            refNnode = cmds.referenceQuery(str(obj), referenceNode=True)
            return refNnode, cmds.referenceQuery(str(obj), filename=True)
        else:
            # might just be working in the rig file itself
            return None, None
