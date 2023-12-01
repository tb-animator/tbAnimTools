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

        return self.commandList

    def assignHotkeys(self):
        return None


class Utility(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Utility'
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
        if Utility.__instance is None:
            Utility.__instance = object.__new__(cls)
            Utility.__instance.initData()

        Utility.__instance.val = cls.toolName
        return Utility.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    def initData(self):
        super(Utility, self).initData()

    def optionUI(self):
        super(Utility, self).optionUI()
        self.initData()
        self.dirWidget = filePathWidget(self.mainDataOption, self.rootDirectory, requiresRestart=True)

        copyButton = QPushButton('Move (Copy) appData to new directory')
        copyButton.clicked.connect(self.copyAppData)

        resetButton = QPushButton('Reset appData location to default')
        resetButton.clicked.connect(self.revertAppData)

        useCustomScaleOption = optionVarBoolWidget('Use custom window scale',
                                                   'tbUseWindowsScale')
        uiScaleOption = intFieldWidget(optionVar='tbCustomDpiScale',
                                       defaultValue=1.0,
                                       label='Custom UI scale factor',
                                       minimum=0.1, maximum=2.0, step=0.01)
        useCustomFontScaleOption = optionVarBoolWidget('Use custom font scale',
                                                   'tbUseFontScale')
        uiScaleFontOption = intFieldWidget(optionVar='tbCustomFontScale',
                                       defaultValue=1.0,
                                       label='Custom Font scale factor',
                                       minimum=0.1, maximum=2.0, step=0.01)

        self.layout.addWidget(copyButton)
        self.layout.addWidget(resetButton)
        self.layout.addWidget(self.dirWidget)
        self.layout.addWidget(useCustomScaleOption)
        self.layout.addWidget(uiScaleOption)
        self.layout.addWidget(useCustomFontScaleOption)
        self.layout.addWidget(uiScaleFontOption)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None
