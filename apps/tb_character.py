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
characterAttribute = 'tbCharacter'
defaultSides = {'left': '_l_', 'right': '_r_'}
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

        self.addCommand(self.tb_hkey(name='characterDefinitionUI',
                                     annotation='',
                                     category=self.category,
                                     command=['CharacterTool.toolBoxUI()']))

        return self.commandList

    def assignHotkeys(self):
        return None


mirrorAxis = ["YZ", "XY", "XZ"]
defaultLeft = '_L_'
defaultRight = '_R_'


class CharacterDefinition(object):
    def __init__(self, jsonFile, char):
        super(CharacterDefinition, self).__init__()
        self.leftSide = defaultLeft
        self.rightSide = defaultRight
        self.controls = list()
        self.mirrorAxis = str()
        self.meshes = list()
        self.globalControl = str()
        self.driverControl = str()
        self.exportControl = str()
        self.UUID = str()
        self.topNode = str()
        self.char = char
        self.fromJson(jsonFile)
        self.jsonFile = jsonFile

    def setUUID(self, node):
        topParent = CharacterTool().funcs.getTopParent(node)
        self.UUID = cmds.ls(str(topParent), uuid=True)

    def setTopNode(self, node):
        # print ('setTopNode', node)
        topParent = CharacterTool().funcs.getTopParent(node)
        self.topNode = str(topParent)

    def fromJson(self, data):
        rawJsonData = json.load(open(data))
        # print (rawJsonData)
        sides = rawJsonData.get('sides', dict())
        self.leftSide = sides.get('left', '_l')
        self.rightSide = sides.get('right', '_r')
        self.controls = rawJsonData.get('controls', list())
        self.mirrorAxis = rawJsonData.get('mirrorAxis', str())
        self.meshes = rawJsonData.get('meshes', list())
        self.globalControl = rawJsonData.get('globalControl', str())
        self.driverControl = rawJsonData.get('driverControl', str())
        self.exportControl = rawJsonData.get('exportControl', str())
        self.UUID = rawJsonData.get('UUID', str())
        self.topNode = rawJsonData.get('topNode', str())

    def toJson(self):
        return json.loads(
            json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': ')))

    def json_serialize(self):
        self.validate()
        returnDict = {}
        returnDict['sides'] = {'left': self.leftSide, 'right': self.rightSide}
        returnDict['controls'] = self.controls
        returnDict['meshes'] = self.meshes
        returnDict['mirrorAxis'] = self.mirrorAxis
        returnDict['globalControl'] = self.globalControl
        returnDict['driverControl'] = self.driverControl
        returnDict['exportControl'] = self.exportControl
        returnDict['UUID'] = self.UUID
        returnDict['topNode'] = self.topNode
        # print ('returnDict', returnDict)
        return returnDict

    def getJsonFile(self):
        if not self.jsonFile:
            self.jsonFile = os.path.join(CharacterTool.charTemplateDir, self.char + '.json')
        return self.jsonFile

    def validate(self):
        """
        Put a bunch of data validation in here
        :return:
        """
        topNode = None
        if not self.topNode:
            try:
                topNode = CharacterTool().funcs.getTopParent(self.controls[0])

            except:
                topNode = None
        if topNode:
            self.topNode = topNode.rsplit(':')[-1]

    def getSide(self, sideName='left'):
        if sideName == 'left':
            return self.leftSide
        return self.rightSide

    def setSide(self, sideName='left', value='_l'):
        if sideName == 'left':
            self.leftSide = value
        else:
            self.rightSide = value

    def setMirrorAxis(self, axis):
        self.mirrorAxis = axis

    def getMirrorAxis(self):
        if not self.mirrorAxis:
            self.mirrorAxis = "YZ"
        return self.mirrorAxis

    def setControls(self, values):
        self.controls = values

    def appendControls(self, values):
        self.controls = list(set(self.controls + values))

    def getControls(self, namespace):
        controls = [namespace + ':' + x for x in self.controls]
        controls = [c for c in controls if cmds.objExists(c)]
        # controls = [c for c in controls if cmds.objectType(c, isAType='transform')]
        return controls

    def selectControls(self, namespace):
        cmds.select(self.getControls(namespace))

    def setGlobalControl(self, value):
        self.globalControl = value

    def getGlobalControl(self, namespace):
        control = namespace + ':' + self.globalControl
        if cmds.objExists(control):
            return control
        return None

    def setDriverControl(self, value):
        self.driverControl = value

    def getDriverControl(self, namespace):
        control = namespace + ':' + self.driverControl
        if cmds.objExists(control):
            return control
        return None

    def setExportControl(self, value):
        self.exportControl = value

    def getExportControl(self, namespace):
        control = namespace + ':' + self.exportControl
        if cmds.objExists(control):
            return control
        return None

    def getMeshes(self, namespace):
        meshes = [namespace + ':' + x for x in self.meshes]
        meshes = [c for c in meshes if cmds.objExists(c)]
        return meshes

    def setMeshes(self, values):
        # print ('setMeshes')
        # print (values)
        self.meshes = [str(x) for x in values]

    def appendMeshes(self, values):
        self.meshes = list(set(self.meshes + values))

    def selectMeshes(self, namespace):
        cmds.select(self.getMeshes(namespace))


class CharacterDataLibrary(object):
    def __init__(self):
        self.UUID_map = dict()
        self.knownTopNodeList = list()
        self.ignoredRigs = list()
        self._fileToMapDict = dict()
        self._walkData = dict()

    def toJson(self):
        jsonData = '''{}'''
        self.jsonObjectInfo = json.loads(jsonData)
        self.jsonObjectInfo['UUID_map'] = {key: value for key, value in self.UUID_map.items()}
        self.jsonObjectInfo['ignoredRigs'] = self.ignoredRigs
        self.jsonObjectInfo['knownTopNodeList'] = self.knownTopNodeList

    def assignRig(self, mapName, rigName):
        if mapName not in self.UUID_map.keys():
            self.UUID_map[mapName] = list()
        for key, values in self.UUID_map.items():
            if rigName in values:
                values.remove(rigName)
        if rigName in self.ignoredRigs:
            self.ignoredRigs.remove(rigName)

        self.UUID_map[mapName].append(rigName)

    def ignoreRig(self, rigName):
        for key, values in self.UUID_map.items():
            if rigName in values:
                values.remove(rigName)
        if rigName not in self.ignoredRigs:
            self.ignoredRigs.append(rigName)

    def save(self, filePath):
        """
        :return:
        """
        self.name = filePath.split('/')[-1].split('.')[0]
        self.toJson()

        fileName = os.path.join(filePath)
        jsonString = json.dumps(self.jsonObjectInfo, indent=4, separators=(',', ': '))
        jsonFile = open(fileName, 'w')
        # print ('jsonString',jsonString)
        jsonFile.write(jsonString)
        jsonFile.close()

        self.createFileToRigMapping()

    def load(self, filepath):
        # print('load', filepath)
        jsonObjectInfo = json.load(open(filepath))
        self.UUID_map = jsonObjectInfo.get('UUID_map', dict())
        self.knownTopNodeList = jsonObjectInfo.get('knownTopNodeList', list())
        self.ignoredRigs = jsonObjectInfo.get('ignoredRigs', list())
        self.createFileToRigMapping()

    def createFileToRigMapping(self):
        for key, values in self.UUID_map.items():
            for v in values:
                self._fileToMapDict[v] = key


class CharacterTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'CharacterTool'
    hotkeyClass = hotkeys()
    funcs = functions()
    libraryName = 'characterLibraryData'
    charSubFolder = 'charTemplates'
    charTemplateDir = None
    selectionChangedScriptJob = -1
    currentChar = None
    currentNamespace = None
    currentCharData = dict()

    # rig names / rig data
    allCharacters = dict()

    def __new__(cls):
        if CharacterTool.__instance is None:
            CharacterTool.__instance = object.__new__(cls)
            CharacterTool.__instance.initData()

        CharacterTool.__instance.val = cls.toolName
        return CharacterTool.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.loadCharacterLibrary()

    def initData(self):
        super(CharacterTool, self).initData()
        self.charTemplateDir = os.path.normpath(os.path.join(self.dataPath, self.charSubFolder))
        if not os.path.isdir(self.charTemplateDir):
            os.mkdir(self.charTemplateDir)
        self.getAllCharacters()

    def optionUI(self):
        super(CharacterTool, self).optionUI()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='Character Definition', image='out_character.png', command='characterDefinitionUI',
                    sourceType='mel',
                    parent=parentMenu)

    def getCharacterByName(self, char, openUI=False):
        # print ('getCharacterByName', char)
        print(char not in self.allCharacters.keys())
        if char not in self.allCharacters.keys():
            self.loadCharacterIfNotLoaded(char, node=None)
            if openUI:
                self.toolBoxUI(
                    message='This rig appears to be new, whatever you were doing just now probably needs something to be set up here')
        return self.allCharacters.get(char, None)

    def getCharFromTopNode(self, node):
        topNode = self.funcs.getTopParent(str(node))
        if topNode is None:
            # print ('exit')
            return None
        # print ('characterAttribute', characterAttribute, topNode)
        if not cmds.attributeQuery(characterAttribute, node=topNode, exists=True):
            return self.queryCharacter(topNode)
        return cmds.getAttr(topNode + '.' + characterAttribute)

    def createNewCharacter(self, node):
        if not node:
            return cmds.warning('Failing to create a new character for node {}'.format(node))
        if isinstance(node, list): node = node[0]
        # print ('createNewCharacter', node)
        refname, namespace = self.funcs.getCurrentRig(node)
        if not refname:
            return cmds.warning('Failing to create a new character for node {}'.format(node))
        self.tagTopNodeAsCharacter(refname, node)
        self.tempCharacter = refname
        self.loadCharacterIfNotLoaded(refname, node=node)

    def tagTopNodeAsCharacter(self, character, node):
        """
        Used to tag the top node of an imported character as an existing character
        :param node:
        :return:
        """
        print('tagTopNodeAsCharacter', node, character)
        topNode = self.funcs.getTopParent(node)
        if not cmds.attributeQuery(characterAttribute, node=str(topNode), exists=True):
            cmds.addAttr(str(topNode), ln=characterAttribute, dt='string')
        cmds.setAttr(str(topNode) + '.' + characterAttribute, character, type='string')
        self.tempCharacter = character

    def queryCharacter(self, node):
        """
        Raise a popup and return an existing character definition
        Used to tag top nodes on imported rigs
        :return:
        """
        if node.rsplit(':')[-1] not in self.characterLibrary.knownTopNodeList:
            return cmds.warning('Probably not a rig?')
        self.tempCharacter = -1
        rigList = self.allCharacters.keys()
        title = 'Assign new/imported rig to character'
        text = 'Looks like this rig has been imported.\n' \
               'Choose from the drop down list the character definition it belongs to'
        prompt = AssignCharacterDialog(title=title, text=text,
                                       itemList=rigList,
                                       rigName=node)
        prompt.assignSignal.connect(self.tagTopNodeAsCharacter)
        prompt.newSignal.connect(self.createNewCharacter)
        if prompt.exec_():
            return 'boop'
        else:
            return self.tempCharacter

    def getSelectedChar(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return None, None
        if not isinstance(sel, list):
            sel = [sel]
        # print ('getSelectedChar', sel)
        refname, namespace = self.funcs.getCurrentRig(sel)
        # print ('refname', refname)
        # print ('namespace', namespace)
        # print ('sel', sel)

        if not refname:
            refname = self.getCharFromTopNode(sel[0])

            if not refname:
                return None, None
        if refname not in self.allCharacters.keys():
            # print ('loading character for %s' % refname)
            self.createNewCharacter(sel)
            # self.loadCharacter(refname)
        return refname, namespace

    def update(self):
        refname, namespace = self.getSelectedChar()
        # print (refname, namespace)
        # print ('self.currentNamespace', self.currentNamespace)
        if namespace:
            self.currentNamespace = namespace
            # print ('update', self.currentNamespace)
        if refname:
            # open up the ui for editing
            self.toolboxWidget.setEnabled(True)
            self.currentRigLabel.setText(refname)
            if self.currentChar != refname:
                self.loadCharacter(refname)
            self.currentChar = refname
            self.currentNamespace = namespace
            self.currentCharData = self.allCharacters[refname]
            # print ('refname', refname)

            leftSide = self.currentCharData.getSide('left')
            rightSide = self.currentCharData.getSide('right')

            self.leftSideLineEdit.setText(leftSide)
            self.rightSideLineEdit.setText(rightSide)

            mirrorIndex = self.mirrorPlaneLabelOption.findText(self.currentCharData.getMirrorAxis())
            self.mirrorPlaneLabelOption.setCurrentIndex(mirrorIndex)

    def loadCharacter(self, refname, node=None):
        # print ('loadCharacter', refname, node)
        if not refname:
            return

        dataFile = os.path.join(self.charTemplateDir, refname + '.json')
        isNew = False
        if not os.path.isfile(dataFile):
            isNew = True
            self.saveJsonFile(dataFile, dict())
        # TODO - maybe make a class for this?
        self.allCharacters[refname] = CharacterDefinition(dataFile, refname)
        if isNew:
            if node is None:
                sel = cmds.ls(sl=True)
            else:
                sel = node
                # print ('sel = node', sel)

            if not sel:
                return cmds.warning('No selection when creating new character entry')
            if isinstance(sel, list):
                sel = str(sel[0])
            # print ('sel', sel)
            self.allCharacters[refname].setUUID(sel)
            self.allCharacters[refname].setTopNode(sel)
            self.saveJsonFile(dataFile, self.allCharacters[refname].toJson())

        # self.allCharacters[refname] = json.load(open(dataFile))

    def getCharacterFromUUID(self, UUID):
        # print ('getCharacterFromUUID', UUID)
        # print (self.characterLibrary.UUID_map)
        return self.characterLibrary.UUID_map.get(UUID, None)

    def getCharacterFromSelection(self):
        refname, namespace = self.getSelectedChar()
        self.loadCharacterIfNotLoaded(refname)

        return refname, self.allCharacters[refname]

    def loadCharacterIfNotLoaded(self, refname, node=None):
        if not refname in self.allCharacters.keys():
            self.loadCharacter(refname, node=node)

    def getAllCharacters(self):
        self.loadCharacterLibrary()
        self.jsonFiles = list()
        for filename in os.listdir(self.charTemplateDir):
            if filename.endswith(".json"):
                if os.path.basename(filename) == self.libraryFile:
                    continue
                self.jsonFiles.append(os.path.join(self.charTemplateDir, filename))
        for filename in self.jsonFiles:
            mapName = os.path.basename(filename).split('.')[0]
            self.loadCharacterIfNotLoaded(mapName)
            char = self.allCharacters[mapName]
            # TODO - this part can be removed
            if char.UUID:
                UUID = char.UUID[0]

                if UUID not in self.characterLibrary.UUID_map.keys():
                    self.characterLibrary.UUID_map[UUID] = mapName
        # take all the known top nodes and add them if not already in the library
        for char in self.allCharacters.values():
            if not char.topNode:
                continue
            if char.topNode not in self.characterLibrary.knownTopNodeList:
                self.characterLibrary.knownTopNodeList.append(char.topNode)

        statinfo = os.access(self.libraryFilePath, os.W_OK)
        if statinfo:
            self.saveCharacterLibraryMap()
        # print self.walkDataLibrary.__dict__

    def saveCharacterLibraryMap(self):
        self.characterLibrary.save(self.libraryFilePath)

    def loadCharacterLibrary(self):
        self.libraryFile = self.libraryName + '.json'
        self.libraryFilePath = os.path.join(self.charTemplateDir, self.libraryFile)

        if not os.path.isfile(self.libraryFilePath):
            self.characterLibrary = CharacterDataLibrary()
            self.saveCharacterLibraryMap()
        else:
            self.characterLibrary = CharacterDataLibrary()
            self.characterLibrary.load(self.libraryFilePath)

        '''
        for key, values in self.walkDataLibrary.rigMapDict.items():
            for v in values:
                self.rigToWalkDataDict[v] = key
        '''
        return self.characterLibrary

    def getStrippedSelection(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return None

        return sel, [str(self.stripNamespace(x)) for x in sel]

    def stripNamespace(self, node):
        refState = cmds.referenceQuery(str(node), isNodeReferenced=True)
        if not refState:
            # TODO - figure out if this is robust
            # print ('currentNamespace', self.currentNamespace)
            if self.currentNamespace:
                # print (self.currentNamespace, node.split(self.currentNamespace, 1)[-1])
                return node.split(self.currentNamespace, 1)[-1]
            else:
                return str(node)
        namespace = cmds.referenceQuery(str(node), namespace=True)
        if namespace[0] == ':':
            namespace = namespace[1:]

        name, node = node.rsplit(namespace)

        return node

    def setAxis(self, value):
        self.currentCharData.setMirrorAxis(value)

    def setSide(self, side, value):
        self.currentCharData.setSide(side, value)

    def _side(self, character, sideName):
        self.loadCharacterIfNotLoaded(character)
        return self.allCharacters[character].getSide(sideName)

    def setAllControls(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setControls(sorted(strippedControls))
        self.currentCharData.setUUID(controls)

    def appendControls(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.appendControls(sorted(strippedControls))

    def getAllControls(self):
        return self.currentCharData.getControls(self.currentNamespace)

    def selectControls(self):
        cmds.select(self.getAllControls())

    def setAllMeshes(self):
        meshes, strippedMeshes = self.getStrippedSelection()
        if not strippedMeshes:
            return cmds.warning('No selection')
        self.currentCharData.setMeshes(sorted(strippedMeshes))

    def appendMeshes(self):
        meshes, strippedMeshes = self.getStrippedSelection()
        if not strippedMeshes:
            return cmds.warning('No selection')
        self.currentCharData.appendMeshes(sorted(strippedMeshes))

    def selectMeshes(self):
        self.currentCharData.selectMeshes(self.currentNamespace)

    def getAllMeshes(self, sel=None):
        refname, namespace = self.getSelectedChar(sel=sel)
        self.loadCharacter(refname)
        return self.allCharacters[refname].getMeshes(namespace)

    def getAllControls(self, sel=None):
        # print ('currentChar', self.currentChar)
        # print ('currentNamespace', self.currentNamespace)
        if sel:
            refname, namespace = self.getSelectedChar(sel=sel)
            self.loadCharacter(refname)

        return self.allCharacters[self.currentChar].getControls(self.currentNamespace)

    def saveCurrentCharacter(self):
        # print ('saveCurrentCharacter')
        if not self.currentChar:
            return
        dataFile = os.path.join(self.charTemplateDir, self.currentChar + '.json')
        # print ('currentChar', self.currentChar)
        self.saveJsonFile(self.currentCharData.getJsonFile(), self.currentCharData.toJson())
        # print ('UUID', self.currentCharData.UUID)
        allControls = self.getAllControls()
        print('saveCurrentCharacter', allControls)
        if allControls:
            self.tagTopNodeAsCharacter(self.currentChar, allControls[0])
        self.getAllCharacters()

    def setGlobalControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setGlobalControl(strippedControls[0])

    def setDriverControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setDriverControl(strippedControls[0])

    def setExportControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setExportControl(strippedControls[0])

    @Slot()
    def removeScriptJob(self):
        cmds.scriptJob(kill=self.selectionChangedScriptJob)

    @Slot()
    def temp(self, data, data2):
        print(data, data2)

    def getToolboxWidget(self, widget, message=''):
        buttonWidth = 124
        buttonHeight = 28
        '''
        cmds.setParent()
        if cmds.menu(TOOLBOX_MENU, exists=True):
            cmds.deleteUI(TOOLBOX_MENU)
        menuBar = cmds.menu(TOOLBOX_MENU, label=TOOLBOX_MENU, tearOff=True)
        '''

        toolBoxWidget = QWidget()
        toolBoxWidget.setContentsMargins(0, 0, 0, 0)
        toolBoxLayout = QVBoxLayout()
        if message:
            messageLabel = QLabel(message)
            messageLabel.setWordWrap(True)
            messageLabel.setStyleSheet("""QLabel{   
            font-weight: bold;
            }
            """)
            toolBoxLayout.addWidget(messageLabel)
        toolBoxLayout.setContentsMargins(0, 0, 0, 0)
        toolBoxWidget.setLayout(toolBoxLayout)
        viewLayout = QHBoxLayout()

        currentLayout = QVBoxLayout()
        currentLayout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel('Current Char:')
        self.currentRigLabel = QLabel('None')
        currentLayout.addWidget(lbl)
        currentLayout.addWidget(self.currentRigLabel)

        controlsGroupbox = myGroupBox('Controls')
        # controlsGroupbox.clicked.connect(self.temp)
        controlsVLayout = QVBoxLayout()
        controlsLayout = QHBoxLayout()
        controlsLayout2 = QHBoxLayout()
        controlsGroupbox.setSubLayout(controlsVLayout)
        controlsVLayout.addLayout(controlsLayout)
        controlsVLayout.addLayout(controlsLayout2)

        defineControlsButton = ToolButton(text='Set Controls',
                                          imgLabel='Tips',
                                          width=buttonWidth,
                                          height=buttonHeight,
                                          icon=":/character.svg",
                                          sourceType='py',
                                          command=self.setAllControls)
        appendControlsButton = ToolButton(text='Append Controls',
                                          imgLabel='Tips',
                                          width=buttonWidth,
                                          height=buttonHeight,
                                          icon=":/character.svg",
                                          sourceType='py',
                                          command=self.appendControls)
        selectControlsButton = ToolButton(text='',
                                          imgLabel='Tips',
                                          width=32,
                                          height=buttonHeight,
                                          icon=":selectObject.png",
                                          sourceType='py',
                                          command=self.selectControls)
        controlsLayout.addWidget(defineControlsButton)
        controlsLayout.addWidget(appendControlsButton)
        controlsLayout.addWidget(selectControlsButton)

        defineGlobalButton = ToolButton(text='Global',
                                        imgLabel='Pick global control',
                                        width=0.33 * (buttonWidth * 2 + 32),
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setGlobalControl)
        defineDriverButton = ToolButton(text='Driver',
                                        imgLabel='Pick driver control',
                                        width=0.33 * (buttonWidth * 2 + 32),
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setDriverControl)
        defineExportButton = ToolButton(text='Export',
                                        imgLabel='Pick export control',
                                        width=0.33 * (buttonWidth * 2 + 32),
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setExportControl)

        controlsLayout2.addWidget(defineGlobalButton)
        controlsLayout2.addWidget(defineDriverButton)
        controlsLayout2.addWidget(defineExportButton)

        mirrorGroupbox = myGroupBox('Control Sides')
        mirrorMainLayout = QVBoxLayout()

        mirrorLayout = QHBoxLayout()
        mirrorLayout.setContentsMargins(0, 0, 0, 0)
        mirrorAxisLayout = QHBoxLayout()
        mirrorAxisLayout.setContentsMargins(0, 0, 0, 0)
        mirrorMainLayout.addLayout(mirrorLayout)
        mirrorMainLayout.addLayout(mirrorAxisLayout)
        mirrorTestLayout = QHBoxLayout()
        mirrorTestLayout.setContentsMargins(0, 0, 0, 0)
        mirrorGroupbox.setSubLayout(mirrorMainLayout)

        leftLabel = QLabel('Left')
        rightLabel = QLabel('Right')
        self.leftSideLineEdit = QLineEdit('??')
        self.leftSideLineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        self.leftSideLineEdit.textChanged.connect(self.sideUpdated)
        self.rightSideLineEdit = QLineEdit('??')
        self.rightSideLineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        self.rightSideLineEdit.textChanged.connect(self.sideUpdated)

        mirrorPlaneLabel = QLabel('Mirror Plane')
        self.mirrorPlaneLabelOption = QComboBox()
        for a in mirrorAxis:
            self.mirrorPlaneLabelOption.addItem(a)
        self.mirrorPlaneLabelOption.currentIndexChanged.connect(self.mirrorAxisChanged)

        calculateAllMirror = QPushButton('Calculate All mirror values')
        calculateAllMirror.clicked.connect(self._calculateMirrorAxis)
        testMirrorSwap = QPushButton('Test Swap')
        testMirrorSwap.clicked.connect(self._testSwap)
        testMirrorLtoR = QPushButton('Test Left To Right')
        testMirrorLtoR.clicked.connect(self._testLeftToRight)
        testMirrorRtoL = QPushButton('Test Right To Left')
        testMirrorRtoL.clicked.connect(self._testRightToLeft)
        calculateSelectedMirror = QPushButton('Calculate Selected mirror values')

        mirrorLayout.addWidget(leftLabel)
        mirrorLayout.addWidget(self.leftSideLineEdit)
        mirrorLayout.addWidget(rightLabel)
        mirrorLayout.addWidget(self.rightSideLineEdit)

        mirrorAxisLayout.addWidget(mirrorPlaneLabel)
        mirrorAxisLayout.addWidget(self.mirrorPlaneLabelOption)

        mirrorMainLayout.addWidget(calculateAllMirror)
        mirrorMainLayout.addLayout(mirrorTestLayout)
        mirrorTestLayout.addWidget(testMirrorSwap)
        mirrorTestLayout.addWidget(testMirrorLtoR)
        mirrorTestLayout.addWidget(testMirrorRtoL)

        meshGroupbox = myGroupBox('Meshes')
        meshLayout = QHBoxLayout()
        meshGroupbox.setSubLayout(meshLayout)
        defineMeshesButton = ToolButton(text='Set Meshes',
                                        imgLabel='Tips',
                                        width=buttonWidth,
                                        height=buttonHeight,
                                        icon=":/out_polySphere.png",
                                        sourceType='py',
                                        command=self.setAllMeshes)
        appendMeshesButton = ToolButton(text='Append Meshes',
                                        imgLabel='Tips',
                                        width=buttonWidth,
                                        height=buttonHeight,
                                        icon=":/out_polySphere.png",
                                        sourceType='py',
                                        command=self.appendMeshes)
        selectMeshesButton = ToolButton(text='',
                                        imgLabel='Tips',
                                        width=32,
                                        height=buttonHeight,
                                        icon=":/selectObject.png",
                                        sourceType='py',
                                        command=self.selectMeshes)
        meshLayout.addWidget(defineMeshesButton)
        meshLayout.addWidget(appendMeshesButton)
        meshLayout.addWidget(selectMeshesButton)

        spaceSwitchroupbox = QGroupBox('SpaceSwitch')
        # add in  aUI to choose the space switch attribute names?
        spaceLayout = QHBoxLayout()
        spaceSwitchroupbox.setLayout(spaceLayout)
        tmpSpaceButton = ToolButton(text='Space!',
                                    imgLabel='Tips',
                                    width=buttonWidth,
                                    height=buttonHeight,
                                    icon=":/out_polySphere.png",
                                    sourceType='py',
                                    command=self.setAllMeshes)
        spaceLayout.addWidget(tmpSpaceButton)

        saveLayout = QHBoxLayout()
        saveButton = ToolButton(text='Save',
                                icon=":/save.png", sourceType='py',
                                height=26,
                                width=80,
                                command=self.saveCurrentCharacter)
        saveLayout.addStretch()
        saveLayout.addWidget(saveButton)

        toolBoxLayout.addLayout(currentLayout)
        toolBoxLayout.addWidget(controlsGroupbox)
        toolBoxLayout.addWidget(meshGroupbox)
        toolBoxLayout.addWidget(mirrorGroupbox)
        toolBoxLayout.addStretch()
        # TODO - add this back
        # toolBoxLayout.addWidget(spaceSwitchroupbox)
        toolBoxLayout.addLayout(saveLayout)

        return toolBoxWidget

    def _calculateMirrorAxis(self):
        refname, namespace = self.getSelectedChar()
        MirrorTools = self.allTools.tools['MirrorTools']
        # print MirrorTools
        controls = self.getAllControls()
        MirrorTools = self.allTools.tools['MirrorTools']
        # print (refname, namespace)
        # print (controls)
        MirrorTools.calculateAllCharacter(refname=refname, character=self.currentCharData, controls=controls)
        pass

    def _testSwap(self):
        mel.eval('mirrorSelectedSwap')

    def _testLeftToRight(self):
        mel.eval('mirrorSelectedLeftToRight')

    def _testRightToLeft(self):
        mel.eval('mirrorSelectedRightToLeft')

    def sideUpdated(self):
        self.setSide('left', self.leftSideLineEdit.text())
        self.setSide('right', self.rightSideLineEdit.text())

    def mirrorAxisChanged(self):
        self.setAxis(self.mirrorPlaneLabelOption.currentText())

    def toolBoxUI(self, message=''):
        # if not self.toolbox:
        self.toolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                                  title='tb Character Definition', text=str(),
                                  lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, )
        self.toolboxWidget = self.getToolboxWidget(self.toolbox, message=message)
        self.toolbox.mainLayout.addWidget(self.toolboxWidget)

        self.toolbox.show()
        self.toolbox.widgetClosed.connect(self.removeScriptJob)
        self.toolbox.setFixedSize(self.toolbox.sizeHint())
        self.toolbox.setFixedWidth(320 * dpiScale())
        self.toolboxWidget.setEnabled(False)
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.update], protected=False)
        self.update()


class myGroupBox(QGroupBox):
    """
    Extension of QGoupBox, add functions for collapsing
    """
    clicked = Signal(str, object)
    isCollapsed = False
    widget = None
    titleDict = {}

    def __init__(self, title):
        super(myGroupBox, self).__init__()
        self.title = title
        self.titleDict = {True: '%s  ...' % self.title, False: self.title}
        self.setTitle(self.title)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12 * dpiScale(), 0, 0)
        layout.setSpacing(0)
        self.widget = QWidget()
        self.setLayout(layout)
        layout.addWidget(self.widget)

    def toggleCollapse(self):
        self.setTitle(self.titleDict[not self.isCollapsed])
        self.widget.setVisible(self.isCollapsed)
        self.isCollapsed = not self.isCollapsed

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if not child:
            child = self
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self.toggleCollapse()
        self.clicked.emit(self.title, child)

    def setSubLayout(self, layout):
        self.widget.setLayout(layout)


class AssignCharacterDialog(BaseDialog):
    newSignal = Signal(str)
    assignSignal = Signal(str, str)

    def __init__(self, rigName=str, parent=None, title='title!!!?', text='what  what?', itemList=list()):
        super(AssignCharacterDialog, self).__init__(parent=parent, title=title, text=text)
        self.rigName = rigName
        buttonLayout = QHBoxLayout()
        self.newButton = QPushButton('Create New')
        self.newButton.clicked.connect(self.newPressed)
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        self.itemComboBox = QComboBox()
        for item in itemList:
            self.itemComboBox.addItem(item)
        self.layout.addWidget(self.itemComboBox)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.newButton)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)

    def newPressed(self):
        self.newSignal.emit(str(self.rigName))
        self.close()

    def assignPressed(self):
        self.assignSignal.emit(str(self.itemComboBox.currentText()), str(self.rigName))
        self.close()
