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
defaultSides = {'left': '_l', 'right': '_r'}
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
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class CharacterTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'CharacterTool'
    hotkeyClass = hotkeys()
    funcs = functions()

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

    def initData(self):
        super(CharacterTool, self).initData()
        self.charTemplateDir = os.path.normpath(os.path.join(self.dataPath, self.charSubFolder))
        if not os.path.isdir(self.charTemplateDir):
            os.mkdir(self.charTemplateDir)

    def optionUI(self):
        return super(CharacterTool, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='Character Definition', image='out_character.png', command='characterDefinitionUI',
                    sourceType='mel',
                    parent=parentMenu)

    def getSelectedChar(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return None, None
        refname, namespace = self.funcs.getCurrentRig(sel)
        if not refname in self.allCharacters.keys():
            self.loadCharacter(refname)
        return refname, namespace

    def update(self):
        refname, namespace = self.getSelectedChar()
        if refname:
            self.currentRigLabel.setText(refname)
            if self.currentChar != refname:
                self.loadCharacter(refname)
            self.currentChar = refname
            self.currentNamespace = namespace
            self.currentCharData = self.allCharacters[refname]
            self.leftSideLineEdit.setText(self.currentCharData.get('sides', defaultSides)['left'])
            self.rightSideLineEdit.setText(self.currentCharData.get('sides', defaultSides)['right'])

    def loadCharacter(self, refname):
        if not refname:
            return
        print ('loadCharacter', refname, self.charTemplateDir)
        dataFile = os.path.join(self.charTemplateDir, refname + '.json')
        if not os.path.isfile(dataFile):
            self.saveJsonFile(dataFile, dict())
        self.allCharacters[refname] = json.load(open(dataFile))

    def getCharacterFromSelection(self):
        refname, namespace = self.getSelectedChar()
        if not refname in self.allCharacters.keys():
            self.loadCharacter(refname)

        return refname, self.allCharacters[refname]

    def getStrippedSelection(self):
        sel = pm.ls(sl=True)
        if not sel:
            return None

        return [x.stripNamespace() for x in sel]

    def setSide(self, side, value):
        sideDict = self.currentCharData.get('sides', defaultSides)
        sideDict[side] = value
        self.currentCharData['sides'] = sideDict

    def setAllControls(self):
        strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData['controls'] = sorted(strippedControls)

    def appendControls(self):
        strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        currentControls = self.currentCharData.get('controls', list())
        self.currentCharData['controls'] = sorted(list(set(currentControls + strippedControls)))

    def selectControls(self):
        controls = self.currentCharData.get('controls', list())
        if not controls:
            return cmds.warning('No controls')
        controls = [self.currentNamespace + ':' + x for x in controls]
        cmds.select(controls)

    def setAllMeshes(self):
        strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        self.currentCharData['meshes'] = sorted(strippedControls)

    def appendMeshes(self):
        strippedControls = self.getStrippedSelection()
        if not strippedControls:
            return cmds.warning('No selection')
        currentControls = self.currentCharData.get('meshes', list())
        self.currentCharData['meshes'] = sorted(list(set(currentControls + strippedControls)))

    def selectMeshes(self):
        meshes = self.currentCharData.get('meshes', list())
        if not meshes:
            return cmds.warning('No controls')
        meshes = [self.currentNamespace + ':' + x for x in meshes]
        cmds.select(meshes)

    def getAllMeshes(self, sel=None):
        refname, namespace = self.getSelectedChar(sel=sel)
        self.loadCharacter(refname)
        meshes = self.allCharacters[refname].get('meshes', list())
        meshes = [namespace + ':' + x for x in meshes]
        return meshes

    def getAllControls(self, sel=None):
        refname, namespace = self.getSelectedChar(sel=sel)
        self.loadCharacter(refname)
        controls = self.allCharacters[refname].get('controls', list())
        controls = [namespace + ':' + x for x in controls]
        return controls

    def saveCurrentCharacter(self):
        print ('saveCurrentCharacter')
        if not self.currentChar:
            return
        dataFile = os.path.join(self.charTemplateDir, self.currentChar + '.json')
        self.saveJsonFile(dataFile, self.currentCharData)

    @Slot()
    def removeScriptJob(self):
        cmds.scriptJob(kill=self.selectionChangedScriptJob)

    def getToolboxWidget(self, widget):
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
        toolBoxLayout.setContentsMargins(0, 0, 0, 0)
        toolBoxWidget.setLayout(toolBoxLayout)
        viewLayout = QHBoxLayout()

        currentLayout = QVBoxLayout()
        currentLayout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel('Current Char:')
        self.currentRigLabel = QLabel('None')
        currentLayout.addWidget(lbl)
        currentLayout.addWidget(self.currentRigLabel)

        controlsGroupbox = QGroupBox('Controls')
        controlsLayout = QHBoxLayout()
        controlsGroupbox.setLayout(controlsLayout)

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
                                          icon=":/selectObject.png",
                                          sourceType='py',
                                          command=self.selectControls)
        controlsLayout.addWidget(defineControlsButton)
        controlsLayout.addWidget(appendControlsButton)
        controlsLayout.addWidget(selectControlsButton)

        mirrorGroupbox = QGroupBox('Control Sides')
        mirrorLayout = QHBoxLayout()
        mirrorGroupbox.setLayout(mirrorLayout)

        leftLabel = QLabel('Left')
        rightLabel = QLabel('Right')
        self.leftSideLineEdit = QLineEdit('_l')
        self.leftSideLineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        self.leftSideLineEdit.textChanged.connect(self.sideUpdated)
        self.rightSideLineEdit = QLineEdit('_r')
        self.rightSideLineEdit.setFixedWidth((2 * buttonWidth) / 3.0)
        self.rightSideLineEdit.textChanged.connect(self.sideUpdated)

        meshGroupbox = QGroupBox('Meshes')
        meshLayout = QHBoxLayout()
        meshGroupbox.setLayout(meshLayout)
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

        mirrorLayout.addWidget(leftLabel)
        mirrorLayout.addWidget(self.leftSideLineEdit)
        mirrorLayout.addWidget(rightLabel)
        mirrorLayout.addWidget(self.rightSideLineEdit)

        saveLayout = QHBoxLayout()
        saveButton = ToolButton(text='Save',
                                icon=":/save.png", sourceType='py',
                                height=22,
                                width=64,
                                command=self.saveCurrentCharacter)
        saveLayout.addStretch()
        saveLayout.addWidget(saveButton)

        toolBoxLayout.addLayout(currentLayout)
        toolBoxLayout.addWidget(controlsGroupbox)
        toolBoxLayout.addWidget(meshGroupbox)
        toolBoxLayout.addWidget(mirrorGroupbox)
        toolBoxLayout.addLayout(saveLayout)

        return toolBoxWidget

    def sideUpdated(self):
        self.setSide('left', self.leftSideLineEdit.text())
        self.setSide('right', self.rightSideLineEdit.text())

    def toolBoxUI(self):
        # if not self.toolbox:
        self.toolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                                  title='tb Character Definition', text=str(),
                                  lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, )

        self.toolbox.mainLayout.addWidget(self.getToolboxWidget(self.toolbox))

        self.toolbox.show()
        self.toolbox.widgetClosed.connect(self.removeScriptJob)
        self.toolbox.setFixedSize(self.toolbox.sizeHint())
        self.toolbox.setFixedWidth(320)
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.update], protected=False)
        self.update()
