'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance
import maya.cmds as cmds
import pymel.core as pm
from Abstract import *

viewFlags = ['controllers',
             'polymeshes',
             'nurbsCurves',
             'nurbsSurfaces',
             'cv',
             'hulls',
             'subdivSurfaces',
             'planes',
             'lights',
             'cameras',
             'imagePlane',
             'joints',
             'ikHandles',
             'deformers',
             'dynamics',
             'particleInstancers',
             'fluids',
             'hairSystems',
             'follicles',
             'nCloths',
             'nParticles',
             'nRigids',
             'dynamicConstraints',
             'locators',
             'dimensions',
             'pivots',
             'handles',
             'textures',
             'strokes',
             'motionTrails',
             'pluginShapes',
             'clipGhosts',
             'greasePencils',
             'pluginObjects']


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_view')
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='ViewMode_xray_joints', annotation='',
                                     category=self.category,
                                     command=['viewModeTool.toggleXrayJoints()']))
        self.addCommand(self.tb_hkey(name='ViewMode_xray',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.toggleXray()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_Joints',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewControls()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_Meshes',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewMeshes()']))
        self.addCommand(self.tb_hkey(name='ViewMode_Objects_All',
                                     annotation='',
                                     category=self.category,
                                     command=['viewModeTool.viewAll()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class viewModeTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'viewModeTool'
    hotkeyClass = None
    funcs = None
    viewData = dict()

    viewControlsCustomOption = 'viewControlsCustomOption'
    viewMeshesCustomOption = 'viewMeshesCustomOption'
    viewAllCustomOption = 'viewAllCustomOption'

    def __new__(cls):
        if viewModeTool.__instance is None:
            viewModeTool.__instance = object.__new__(cls)

        viewModeTool.__instance.val = cls.toolName
        return viewModeTool.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.loadData()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(viewModeTool, self).optionUI()
        subWdiget = QWidget()
        subLayout = QVBoxLayout()
        self.layout.addWidget(subWdiget)
        subWdiget.setLayout(subLayout)

        layout = QHBoxLayout()
        controlLabel = QLabel('Set custom Control View')
        setControlButton = QPushButton('Set')
        setControlButton.clicked.connect(self.setCustomControlView)
        removeControlButton = QPushButton('Remove')
        removeControlButton.clicked.connect(self.removeCustomControlView)
        layout.addWidget(setControlButton)
        layout.addWidget(removeControlButton)
        layout.addWidget(controlLabel)
        subLayout.addLayout(layout)

        layout = QHBoxLayout()
        modelLabel = QLabel('Set custom Model View')
        setModelButton = QPushButton('Set')
        setModelButton.clicked.connect(self.setCustomModelView)
        removeModelButton = QPushButton('Remove')
        removeModelButton.clicked.connect(self.removeCustomModelView)
        layout.addWidget(setModelButton)
        layout.addWidget(removeModelButton)
        layout.addWidget(modelLabel)
        subLayout.addLayout(layout)

        layout = QHBoxLayout()
        allLabel = QLabel('Set custom All View')
        setAllButton = QPushButton('Set')
        setAllButton.clicked.connect(self.setCustomAllView)
        removeAllButton = QPushButton('Remove')
        removeAllButton.clicked.connect(self.removeCustomAllView)
        layout.addWidget(setAllButton)
        layout.addWidget(removeAllButton)
        layout.addWidget(allLabel)
        subLayout.addLayout(layout)

        setControlButton.setFixedWidth(48)
        setModelButton.setFixedWidth(48)
        setAllButton.setFixedWidth(48)
        removeControlButton.setFixedWidth(72)
        removeModelButton.setFixedWidth(72)
        removeAllButton.setFixedWidth(72)

        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def getCurrentFlags(self):
        panel = self.funcs.getModelPanel()
        flagDict = dict()
        for flag in viewFlags:
            try:
                value = cmds.modelEditor(panel, query=True, **{flag: True})
                flagDict[flag] = value
            except:
                cmds.warning('bad flag', flag)
                continue
        return flagDict

    def setFlagsFromDict(self, flagDict):
        panel = self.funcs.getModelPanel()
        for flag in viewFlags:
            try:
                cmds.modelEditor(panel, edit=True, **{flag: flagDict[flag]})
            except:
                continue
    def setCustomControlView(self, *args):
        self.savePreset('controls')
        pm.optionVar(intValue=(self.viewControlsCustomOption, True))
        self.loadData()

    def setCustomModelView(self, *args):
        self.savePreset('models')
        pm.optionVar(intValue=(self.viewMeshesCustomOption, True))
        self.loadData()

    def setCustomAllView(self, *args):
        self.savePreset('everything')
        pm.optionVar(intValue=(self.viewAllCustomOption, True))
        self.loadData()

    def removeCustomControlView(self, *args):
        pm.optionVar(intValue=(self.viewControlsCustomOption, False))
        if 'controls' in self.viewData['viewData'].keys():
            self.viewData['viewData'].pop('controls')
        self.saveData()

    def removeCustomModelView(self, *args):
        pm.optionVar(intValue=(self.viewMeshesCustomOption, False))
        if 'models' in self.viewData['viewData'].keys():
            self.viewData['viewData'].pop('models')
        self.saveData()

    def removeCustomAllView(self, *args):
        pm.optionVar(intValue=(self.viewAllCustomOption, False))
        if 'everything' in self.viewData['viewData'].keys():
            self.viewData['viewData'].pop('everything')
        self.saveData()

    def savePreset(self, presetName):
        self.loadData()
        flags = self.getCurrentFlags()
        self.viewData['viewData'][presetName] = flags
        self.saveData()
        self.loadData()

    def viewNone(self, panel):
        cmds.modelEditor(panel, edit=True,
                         allObjects=False)

    def viewMode(self, key='everything', custom=False, default='everything'):
        panel = self.funcs.getModelPanel()
        # self.viewNone(panel)
        print 'is custom?', custom
        print self.viewData['viewData'].get(key, default)
        self.setFlagsFromDict({False: default, True: self.viewData['viewData'].get(key, default)}[bool(custom)])

    def viewControls(self):
        self.viewMode(key='controls', custom=pm.optionVar.get(self.viewControlsCustomOption, False), default=controls)

    def viewMeshes(self):
        print 'viewMeshesCustomOption', pm.optionVar.get(self.viewMeshesCustomOption, False)
        self.viewMode(key='models', custom=pm.optionVar.get(self.viewMeshesCustomOption, False), default=models)

    def viewAll(self):
        self.viewMode(key='everything', custom=pm.optionVar.get(self.viewAllCustomOption, False), default=everything)

    def toggleXrayJoints(self):
        panel = self.funcs.getModelPanel()
        cmds.modelEditor(panel, edit=True,
                         jointXray=not cmds.modelEditor(panel, query=True, jointXray=True))

    def toggleXray(self):
        panel = self.funcs.getModelPanel()
        cmds.modelEditor(panel, edit=True,
                         xray=not cmds.modelEditor(panel, query=True, xray=True))

    def loadData(self):
        super(viewModeTool, self).loadData()
        self.viewData = self.rawJsonData.get('viewData', dict())
        if 'viewData' not in self.viewData.keys():
            self.viewData['viewData'] = dict()

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['viewData'] = self.viewData


controls = {
    'controllers': True,
    'polymeshes': False,
    'nurbsCurves': True,
    'nurbsSurfaces': True,
    'cv': True,
    'hulls': True,
    'subdivSurfaces': True,
    'planes': True,
    'lights': True,
    'cameras': True,
    'imagePlane': True,
    'joints': True,
    'ikHandles': True,
    'deformers': True,
    'dynamics': True,
    'particleInstancers': True,
    'fluids': True,
    'hairSystems': True,
    'follicles': True,
    'nCloths': True,
    'nParticles': True,
    'nRigids': True,
    'dynamicConstraints': True,
    'locators': True,
    'dimensions': True,
    'pivots': True,
    'handles': True,
    'textures': True,
    'strokes': True,
    'motionTrails': True,
    'pluginShapes': True,
    'clipGhosts': True,
    'greasePencils': True,
    'pluginObjects': True,
}
everything = {
    'controllers': True,
    'polymeshes': True,
    'nurbsCurves': True,
    'nurbsSurfaces': True,
    'cv': True,
    'hulls': True,
    'subdivSurfaces': True,
    'planes': True,
    'lights': True,
    'cameras': True,
    'imagePlane': True,
    'joints': True,
    'ikHandles': True,
    'deformers': True,
    'dynamics': True,
    'particleInstancers': True,
    'fluids': True,
    'hairSystems': True,
    'follicles': True,
    'nCloths': True,
    'nParticles': True,
    'nRigids': True,
    'dynamicConstraints': True,
    'locators': True,
    'dimensions': True,
    'pivots': True,
    'handles': True,
    'textures': True,
    'strokes': True,
    'motionTrails': True,
    'pluginShapes': True,
    'clipGhosts': True,
    'greasePencils': True,
    'pluginObjects': True,
}
models = {
    'controllers': False,
    'nurbsCurves': False,
    'polymeshes': True,
    'nurbsSurfaces': False,
    'cv': False,
    'hulls': False,
    'subdivSurfaces': False,
    'planes': False,
    'lights': False,
    'cameras': False,
    'imagePlane': False,
    'joints': False,
    'ikHandles': False,
    'deformers': False,
    'dynamics': False,
    'particleInstancers': False,
    'fluids': False,
    'hairSystems': False,
    'follicles': False,
    'nCloths': False,
    'nParticles': True,
    'nRigids': False,
    'dynamicConstraints': False,
    'locators': False,
    'dimensions': False,
    'pivots': False,
    'handles': False,
    'textures': False,
    'strokes': False,
    'motionTrails': False,
    'pluginShapes': False,
    'clipGhosts': False,
    'greasePencils': True,
    'pluginObjects': True,
}
