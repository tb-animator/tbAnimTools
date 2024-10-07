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
from . import *
import sys

if sys.version_info >= (2, 8):
    from urllib.request import *
else:
    from urllib2 import *
import zipfile
from distutils.dir_util import copy_tree
__author__ = 'tom.bailey'

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbAnimToolsReinstall',
                                     annotation='Runs the installer again to force an update',
                                     category='Installation',
                                     command=['Utility.reinstall()']))
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
        if Utility.__instance is None:
            Utility.__instance = object.__new__(cls)
            Utility.__instance.initData()

        Utility.__instance.val = cls.toolName
        return Utility.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

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

    def reinstall(self, *args):
        base_dir = os.path.join(os.path.normpath(os.path.dirname(__file__)), os.pardir)
        zipLocation = 'https://github.com/tb-animator/tbAnimTools/archive/refs/heads/main.zip'
        filedata = urlopen(zipLocation)
        datatowrite = filedata.read()
        zipFile = os.path.join(base_dir, 'tbAnimToolsLatest.zip')
        with open(zipFile, 'wb') as f:
            f.write(datatowrite)

        destinationPath = os.path.normpath(os.path.join(base_dir, 'extract'))
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(destinationPath)
        destinationPathFinal = os.path.normpath(os.path.join(base_dir))

        copy_tree(os.path.join(destinationPath, 'tbAnimTools-main'), destinationPathFinal)

        message_state = cmds.optionVar(query="inViewMessageEnable")
        cmds.optionVar(intValue=("inViewMessageEnable", 1))
        cmds.inViewMessage(amg='tbAnimTools update complete',
                           pos='botRight',
                           dragKill=True,
                           fadeOutTime=10.0,
                           fade=False)
        cmds.optionVar(intValue=("inViewMessageEnable", message_state))

