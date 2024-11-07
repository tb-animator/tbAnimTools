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
_flipButtonStyleSheet = """
                            QPushButton {   
                                color:gray;
                                border-width: 1px;
                                 border-radius: 4;
                                 border-style: solid;
                                 border-color: #222222;
                                 font-weight: bold; font-size: 16px;
                            }   
                            QPushButton:checked{
                                color:darkGray;
                                background-color:green;
                                border-width: 1px;
                                 border-radius: 4;
                                 border-style: solid;
                                 border-color: #222222;
                                 font-weight: bold; font-size: 16px;
                            }
                            QPushButton:hover{  
                            border-width: 1px;
                                 border-color: #ffaa00;
                            }  
                            """
characterAttribute = 'tbCharacter'
defaultSides = {'left': '_l_', 'right': '_r_'}
"""
TODO - add option for combining selections into one cache object, feature to reload multiple references from one cache
"""

from . import *


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
labelDict = {True: 'Flip', False: 'Keep'}


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
        self.feetControls = str()
        self.customAttributes = dict()
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
        self.feetControls = rawJsonData.get('feetControls', str())
        self.customAttributes = rawJsonData.get('customAttributes', dict())
        if isinstance(self.customAttributes, str):
            self.customAttributes = dict()
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
        returnDict['feetControls'] = self.feetControls
        returnDict['customAttributes'] = self.customAttributes
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

    def setFeetControls(self, value):
        self.feetControls = value

    def getFeetControl(self, namespace):
        feet = [namespace + ':' + f for f in self.feetControls]
        feet = [f for f in feet if cmds.objExists(f)]
        if feet:
            return feet
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
    funcs = Functions()
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
        self.funcs = Functions()
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
        cmds.menuItem(label='Character Definition', image='out_character.png', command='characterDefinitionUI',
                    sourceType='mel',
                    parent=parentMenu)

    def getCharacterByName(self, char, openUI=False):
        if char not in self.allCharacters.keys():
            print('Loading character {}'.format(char))
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

    def getSelectedChar(self, sel=None, referenceOnly=False):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return None, None
        if not isinstance(sel, list):
            sel = [sel]
        # print ('getSelectedChar', sel)
        refname, namespace = self.funcs.getCurrentRig(sel, referenceOnly=referenceOnly)
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
            self.globalControlLabel.setText(self.currentCharData.globalControl)
            self.driverControlLabel.setText(self.currentCharData.driverControl)
            self.exportControlLabel.setText(self.currentCharData.exportControl)
            feet = self.currentCharData.feetControls
            if not feet:
                feet = list()
            feetString = '  '.join(feet)
            self.feetControlLabel.setText(feetString)

            mirrorIndex = self.mirrorPlaneLabelOption.findText(self.currentCharData.getMirrorAxis())
            self.mirrorPlaneLabelOption.setCurrentIndex(mirrorIndex)
        sel = cmds.ls(sl=True)
        self.updateMirrorChannels(sel)

    def loadCharacter(self, refname, node=None):
        # print ('loadCharacter', refname, node)
        if not refname:
            return cmds.warning ('No name specified for loading character')
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
        if refname not in self.allCharacters.keys():
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
        if node.startswith(':'):
            node = node[1:]

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
        if not self.currentChar:
            return
        dataFile = os.path.join(self.charTemplateDir, self.currentChar + '.json')
        # print ('currentChar', self.currentChar)

        self.saveJsonFile(self.currentCharData.getJsonFile(), self.currentCharData.toJson())

        allControls = self.getAllControls()

        if allControls:
            self.tagTopNodeAsCharacter(self.currentChar, allControls[0])
        self.getAllCharacters()
        MirrorTools = self.allTools.tools['MirrorTools']
        MirrorTools.saveCurrentMirrorData(self.currentChar)
        self.loadCharacter(self.currentChar)

    def setGlobalControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setGlobalControl(strippedControls[0])
        self.update()

    def setDriverControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setDriverControl(strippedControls[0])
        self.update()

    def setExportControl(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setExportControl(strippedControls[0])
        self.update()

    def setFeetControls(self):
        controls, strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData.setExportControl(strippedControls[0])
        self.update()

    @Slot()
    def removeScriptJob(self):
        cmds.scriptJob(kill=self.selectionChangedScriptJob)

    @Slot()
    def temp(self, data, data2):
        print(data, data2)

    def updateMirrorChannels(self, sel):
        if sel:
            for x in self.mirrorChannelWidgets.values():
                x.setEnabled(True)
            self.currentControls = sel
            if len(sel) == 1:
                self.currentControlLabel.setText('Control :: ' + sel[0])
            else:
                self.currentControlLabel.setText('Controls :: ' + sel[0] + ' ...')

            MirrorTools = self.allTools.tools['MirrorTools']
            characters = self.funcs.splitSelectionToCharacters(sel)
            MirrorTools.loadDataForCharacters(characters)

            for x in ['translateX', 'translateY', 'translateZ']:
                isMirrored = MirrorTools.getIsMirror(sel[0], self.currentChar, x)
                button = self.mirrorChannelWidgets[x]
                button.setChecked(isMirrored == -1)
                button.setText(labelDict[isMirrored == -1])
            for x in ['rotateX', 'rotateY', 'rotateZ']:
                isMirrored = MirrorTools.getIsMirror(sel[0], self.currentChar, x)
                button = self.mirrorChannelWidgets[x]
                button.setChecked(isMirrored == -1)
                button.setText(labelDict[isMirrored == -1])
            for x in self.mirrorChannelWidgets.values():
                x.setEnabled(True)
                x.setStyleSheet(_flipButtonStyleSheet)
        else:
            self.currentControlLabel.setText('No control')
            for x in self.mirrorChannelWidgets.values():
                x.setEnabled(False)
                x.setStyleSheet(getqss.getStyleSheet())

    def mirrorChannelWidget(self):
        mirrorChannelLayout = QVBoxLayout()
        mirrorChannelMainLayout = QHBoxLayout()

        self.mirrorTranslateFormLayout = QFormLayout()
        self.mirrorRotateFormLayout = QFormLayout()
        self.mirrorChannelWidgets = dict()

        for x in ['translateX', 'translateY', 'translateZ']:
            label = QLabel(x)
            button = QPushButton()
            button.setFixedHeight(18 * dpiScale())
            button.setCheckable(True)
            button.attribute = str(x)
            self.mirrorTranslateFormLayout.addRow(label, button)
            self.mirrorChannelWidgets[x] = button
            button.clicked.connect(create_callback(self.updateMirroChannelForControl, button))
        for x in ['rotateX', 'rotateY', 'rotateZ']:
            label = QLabel(x)
            button = QPushButton()

            button.setCheckable(True)
            button.attribute = str(x)
            self.mirrorRotateFormLayout.addRow(label, button)
            self.mirrorChannelWidgets[x] = button
            button.clicked.connect(create_callback(self.updateMirroChannelForControl, button))

        mirrorChannelMainLayout.addLayout(self.mirrorTranslateFormLayout)
        mirrorChannelMainLayout.addLayout(self.mirrorRotateFormLayout)
        self.currentControlLabel = QLabel('No control')
        mirrorChannelLayout.addWidget(self.currentControlLabel)
        mirrorChannelLayout.addLayout(mirrorChannelMainLayout)

        for x in self.mirrorChannelWidgets.values():
            x.setStyleSheet(_flipButtonStyleSheet)
            x.setFixedHeight(18 * dpiScale())
            x.setFixedWidth(48 * dpiScale())
        return mirrorChannelLayout

    def updateMirroChannelForControl(self, button, *args):
        MirrorTools = self.allTools.tools['MirrorTools']
        characters = self.funcs.splitSelectionToCharacters(self.currentControls)
        MirrorTools.loadDataForCharacters(characters)
        for s in self.currentControls:
            MirrorTools.setIsMirror(s, self.currentChar, button.attribute, button.isChecked())
        button.setText(labelDict[button.isChecked()])
        MirrorTools.saveCurrentMirrorData(self.currentChar)

    def getToolboxWidget(self, widget, message=''):
        buttonWidth = 124
        buttonHeight = 18
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

        controlsGroupbox = CollapsingContainer('Controls')
        # controlsGroupbox.clicked.connect(self.temp)
        controlsVLayout = QVBoxLayout(controlsGroupbox.contentWidget)
        controlsLayout = QHBoxLayout()
        controlsLayout2 = QHBoxLayout()
        controlsFormLayout = QFormLayout()

        # controlsGroupbox.setSubLayout(controlsVLayout)
        controlsVLayout.addLayout(controlsLayout)
        controlsVLayout.addLayout(controlsLayout2)
        controlsVLayout.addLayout(controlsFormLayout)

        defineControlsButton = ToolButton(text='Set All Controls',
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

        defineGlobalButton = ToolButton(text='Set Global Control',
                                        imgLabel='Pick global control',
                                        width=buttonWidth,
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setGlobalControl)
        defineDriverButton = ToolButton(text='Set Mover Control',
                                        imgLabel='Pick driver control',
                                        width=buttonWidth,
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setDriverControl)
        defineExportButton = ToolButton(text='Set Export Control',
                                        imgLabel='Pick export control',
                                        width=buttonWidth,
                                        height=buttonHeight,
                                        icon=":/pickPivotComp.png",
                                        sourceType='py',
                                        command=self.setExportControl)
        defineFeetButton = ToolButton(text='Set Feet Controls',
                                      imgLabel='Pick feet controls',
                                      width=buttonWidth,
                                      height=buttonHeight,
                                      icon=":/pickPivotComp.png",
                                      sourceType='py',
                                      command=self.setFeetControls)
        self.globalControlLabel = QLabel('Global ??')
        self.driverControlLabel = QLabel('Driver ??')
        self.exportControlLabel = QLabel('Export ??')
        self.feetControlLabel = QLabel('Feet ??')
        controlsFormLayout.addRow(defineGlobalButton, self.globalControlLabel)
        controlsFormLayout.addRow(defineDriverButton, self.driverControlLabel)
        controlsFormLayout.addRow(defineExportButton, self.exportControlLabel)
        controlsFormLayout.addRow(defineFeetButton, self.feetControlLabel)

        mirrorGroupbox = CollapsingContainer('Control Sides / Mirror')
        mirrorMainLayout = QVBoxLayout(mirrorGroupbox.contentWidget)

        mirrorLayout = QHBoxLayout()
        mirrorLayout.setContentsMargins(0, 0, 0, 0)
        mirrorAxisLayout = QHBoxLayout()
        mirrorAxisLayout.setContentsMargins(0, 0, 0, 0)
        mirrorMainLayout.addLayout(mirrorLayout)
        mirrorMainLayout.addLayout(mirrorAxisLayout)
        mirrorTestLayout = QHBoxLayout()
        mirrorTestLayout.setContentsMargins(0, 0, 0, 0)

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
        mirrorMainLayout.addWidget(calculateSelectedMirror)
        mirrorMainLayout.addLayout(mirrorTestLayout)
        mirrorTestLayout.addWidget(testMirrorSwap)
        mirrorTestLayout.addWidget(testMirrorLtoR)
        mirrorTestLayout.addWidget(testMirrorRtoL)
        mirrorMainLayout.addLayout(self.mirrorChannelWidget())

        meshGroupbox = CollapsingContainer('Meshes')
        meshLayout = QHBoxLayout(meshGroupbox.contentWidget)
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
        toolBoxWidget.setStyleSheet(getqss.getStyleSheet())
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
        self.toolbox = CharacterWindow()
        self.toolboxWidget = self.getToolboxWidget(self.toolbox, message=message)
        self.toolbox.setCentralWidget(self.toolboxWidget)
        # self.toolbox.mainLayout.addWidget(self.toolboxWidget)

        self.toolbox.show()
        self.toolbox.widgetClosed.connect(self.removeScriptJob)
        # self.toolbox.setFixedSize(self.toolbox.sizeHint())
        # self.toolbox.setFixedWidth(320 * dpiScale())
        self.toolboxWidget.setEnabled(False)
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.update], protected=False)
        self.update()

    def getTempControlData(self, character, rigControl, controlName, attribute):
        self.currentChar = character
        self.loadCharacter(self.currentChar)
        self.currentNamespace = self.funcs.namespace(controlName)
        self.currentCharData = self.allCharacters[character]

        customData = self.currentCharData.customAttributes.get(self.funcs.stripNamespace(controlName), dict())

        if attribute not in customData.keys():
            return cmds.warning('No stored drawScale for %s' % controlName)
        value = customData[attribute]
        cmds.setAttr(controlName + '.' + attribute, value)

    def setTempControlData(self, character, controlName, attribute):
        self.currentChar = character
        self.loadCharacter(self.currentChar)
        self.currentNamespace = self.funcs.namespace(controlName)
        self.currentCharData = self.allCharacters[character]

        customData = self.currentCharData.customAttributes.get(controlName, dict())

        value = cmds.getAttr(controlName + '.' + attribute)
        customData[attribute] = value
        self.currentCharData.customAttributes[self.funcs.stripNamespace(controlName)] = customData
        self.saveCurrentCharacter()


class CharacterWindow(MayaQWidgetDockableMixin, QMainWindow):
    widgetClosed = Signal()

    def __init__(self, *args, **kwargs):
        super(CharacterWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('tb Character Definition')
        self.setAttribute(Qt.WA_DeleteOnClose, True)

    def closeEvent(self, event):
        super(CharacterWindow, self).closeEvent(event)
        self.widgetClosed.emit()


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


class mirrorChannelWidget(QWidget):
    def __init__(self):
        super(mirrorChannelWidget, self).__init__()
        self.formLayout = QFormLayout()
        self.setLayout(self.formLayout)

        self.translateBox = QLineEdit()


class flipButton(QPushButton):
    pressedSignal = Signal(bool)

    def __init__(self, value, state):
        super(flipButton, self).__init__()
        self.labels = {True: 'Flip', False: 'NoFlip'}
        self.colours = {True: 'Flip', False: 'NoFlip'}
        self.setCheckable(True)
        self.setChecked(state)
        self.value = value
        self.state = state

        self.clicked.connect(self.toggle)

    def toggle(self):
        self.state = not self.state
        self.setChecked()
        self.setText(self.labels[self.state])
