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
import pymel.core.datatypes as dt
from Abstract import *
import maya.api.OpenMaya as om2
from difflib import SequenceMatcher

str_spacePresets = 'spacePresets'
str_spaceDefaultValues = 'spaceDefaultValues'
str_spaceMirrorValues = 'spaceMirrorValues'
str_spaceLocalValues = 'spaceLocalValues'
str_spaceGlobalValues = 'spaceGlobalValues'
str_spaceControlKey = 'spaceControl'

IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Icons'))

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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('spaceSwitch'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbSpaceSwitchSelectedGlobal',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['SpaceSwitch.switchSelection(mode="{key}")'.format(
                                         key=str_spaceGlobalValues)]))
        self.addCommand(self.tb_hkey(name='tbSpaceSwitchSelectedLocal',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=[
                                         'SpaceSwitch.switchSelection(mode="{key}")'.format(key=str_spaceLocalValues)]))
        self.addCommand(self.tb_hkey(name='tbSpaceSwitchSelectedDefault',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=[
                                         'SpaceSwitch.switchSelection(mode="{key}")'.format(key=str_spaceLocalValues)]))

        self.addCommand(self.tb_hkey(name='tbSpaceBakeSelectedGlobal',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['SpaceSwitch.bakeSelection(mode="spaceGlobalValues")']))
        self.addCommand(self.tb_hkey(name='tbSpaceBakeSelectedLocal',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['SpaceSwitch.bakeSelection(mode="spaceLocalValues")']))
        self.addCommand(self.tb_hkey(name='tbSpaceBakeSelectedDefault',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['SpaceSwitch.bakeSelection(mode="spaceDefaultValues")']))

        self.addCommand(self.tb_hkey(name='selectAllSpaceSwitchControls',
                                     annotation='selects all space switch controls for selected rigs',
                                     category=self.category, command=['SpaceSwitch.selectAllSpaceSwitchControls()']))

        self.setCategory(self.helpStrings.category.get('markingMenus'))
        self.addCommand(self.tb_hkey(name='tbOpenSpaceSwitchMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.openMM()']))
        self.addCommand(self.tb_hkey(name='tbOpenSpaceSwitchPresetMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.openPresetMM()']))
        self.addCommand(self.tb_hkey(name='tbCloseSpaceSwitchMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.closeMM()']))

        self.setCategory(self.helpStrings.category.get('ui'))
        self.addCommand(self.tb_hkey(name='tbOpenSpaceSwitchDataEditor',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.openEditorWindow()']))

        return self.commandList

    def assignHotkeys(self):
        return


class SpaceData(object):
    def __init__(self):
        self.spaceControl = {}  #
        self.spaceGlobalValues = {}  #
        self.spaceLocalValues = {}  #
        self.spaceDefaultValues = {}  #
        self.spaceMirrorValues = {}  #
        self.spacePresets = dict()  # key is preset name, value is a dict of control:spaces

    def setControlSpaceAttribute(self, control, attribute):
        self.spaceControl[control + '.' + attribute] = control

    def captureCurrentState(self, switchAttrData, switchValueData, key=str_spaceGlobalValues):
        for switchAttr in switchAttrData.keys():
            self.__dict__[key][switchAttr] = switchValueData[switchAttr]

    def addControlsWithMatchingAttribute(self, namespace, controls, attribute):
        """
        Add a list of controls, if there is a user attribute that partially matches the input, use that.
        If no partial match - ignore it
        :param controls:
        :param attribute:
        :return:
        """
        for control in controls:
            attrs = cmds.listAttr(namespace + ':' + control)
            bestMatch = attribute
            if attribute not in attrs:
                matches = {at: SequenceMatcher(None, at, attribute).ratio() for at in attrs}
                bestMatch = max(matches, key=matches.get)
            self.setControlSpaceAttribute(control, bestMatch)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict[str_spaceControlKey] = self.spaceControl
        returnDict[str_spaceGlobalValues] = self.spaceGlobalValues
        returnDict[str_spaceLocalValues] = self.spaceLocalValues
        returnDict[str_spaceDefaultValues] = self.spaceDefaultValues
        returnDict[str_spaceMirrorValues] = self.spaceMirrorValues
        returnDict[str_spacePresets] = self.spacePresets
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))

        self.spaceControl = rawJsonData.get(str_spaceControlKey, dict())
        self.spaceGlobalValues = rawJsonData.get(str_spaceGlobalValues, dict())
        self.spaceLocalValues = rawJsonData.get(str_spaceLocalValues, dict())
        self.spaceDefaultValues = rawJsonData.get(str_spaceDefaultValues, dict())
        self.spaceMirrorValues = rawJsonData.get(str_spaceMirrorValues, dict())
        self.spacePresets = rawJsonData.get(str_spacePresets, dict())

    def removeItem(self, key):
        self.spaceControl.pop(key)
        self.spaceGlobalValues.pop(key)
        self.spaceLocalValues.pop(key)
        self.spaceDefaultValues.pop(key)
        self.spaceMirrorValues.pop(key)

        # TODO - remove from presets as well


class SpaceSwitch(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'SpaceSwitch'
    hotkeyClass = hotkeys()
    funcs = functions()

    culledUserAttributes = ['blendParent', 'blendOrient', 'blendPoint']
    quickBakeSimOption = 'tbSpaceSwitchBakeUseSim'
    bakeTimelineModes = ['Full timeline', 'Visible Timeline', 'All Keys']
    bakeTimelineModeOption = 'tbSpaceBakeTimelineMode'
    bakeLayerModes = ['To Override', 'To Override - Extract anim', 'To Base']
    bakeToLayerModeOption = 'tbSpaceBakeToLayerMode'

    loadedSpaceData = dict()  # store loaded data per session to avoid accessing the disc all the time
    namespaceToCharDict = dict()
    spaceDataDict = dict()
    popupSwitchMode = False
    allSpaceAttributes = list()
    win = None

    subPath = None
    allCharacters = dict()

    def __new__(cls):
        if SpaceSwitch.__instance is None:
            SpaceSwitch.__instance = object.__new__(cls)
            SpaceSwitch.__instance.initData()
            SpaceSwitch.__instance.loadAllCharacters()

        SpaceSwitch.__instance.val = cls.toolName
        return SpaceSwitch.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    def initData(self):
        super(SpaceSwitch, self).initData()
        self.subPath = os.path.join(self.dataPath, self.toolName)
        if not os.path.exists(self.subPath):
            os.mkdir(self.subPath)

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(SpaceSwitch, self).optionUI()

        sub = subHeader('Baking Timeline Option')
        infoText1 = QLabel('<b>Full Timeline</b> - The uncropped timeline range will be used to bake')
        infoText2 = QLabel('<b>Visible Timeline</b> - The currently visible timeline range will be used')
        infoText3 = QLabel('<b>All Keys</b> - Force the time range to be the the full key range of your controls')

        self.bakeRangeModeWidget = comboBoxWidget(optionVar=self.bakeTimelineModeOption,
                                                  values=self.bakeTimelineModes,
                                                  defaultValue=pm.optionVar.get(self.bakeTimelineModeOption,
                                                                                self.bakeTimelineModes[0]),
                                                  label='Bake mode range')
        simOptionWidget = optionVarBoolWidget('Space switch bake uses Simulation ', self.quickBakeSimOption)
        infoText4 = QLabel('<b>Bake to layer</b> - A space bake will bake to a new override layer')
        self.bakeLayerModeWidget = comboBoxWidget(optionVar=self.bakeToLayerModeOption,
                                                  values=self.bakeLayerModes,
                                                  defaultValue=pm.optionVar.get(self.bakeToLayerModeOption,
                                                                                self.bakeLayerModes[0]),
                                                  label='Bake Layer Mode')
        self.layout.addWidget(sub)
        self.layout.addWidget(infoText1)
        self.layout.addWidget(infoText2)
        self.layout.addWidget(infoText3)
        self.layout.addWidget(self.bakeRangeModeWidget)
        self.layout.addWidget(simOptionWidget)
        self.layout.addWidget(infoText4)
        self.layout.addWidget(self.bakeLayerModeWidget)

        self.layout.addStretch()

        return self.optionWidget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='SpaceSwitch Data Editor', image='menuIconChannels.png',
                    command='tbOpenSpaceSwitchDataEditor', sourceType='mel',
                    parent=parentMenu)

    def openPresetMM(self):
        self.build_preset_MM()
        self.presetMarkingMenuWidget.show()

    def build_preset_MM(self, parentMenu=None):
        menuDict = {'NE': list(),
                    'NW': list(),
                    'SE': list(),
                    'SW': list()
                    }

        # TODO - change this so the event filter doesn't get rebuilt all the time
        self.presetMarkingMenuWidget = ViewportDialog(menuDict=menuDict, parentMenu=parentMenu)

        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)
        # make this better...?

        if sel:
            menuDict['NW'].append(
                ToolboxButton(label='switch to Local', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\local_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceLocalValues),
                              closeOnPress=True))
            menuDict['NW'].append(
                ToolboxButton(label='switch to Global', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\world_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceGlobalValues),
                              closeOnPress=True))
            menuDict['NW'].append(
                ToolboxButton(label='switch to Default', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\default_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceDefaultValues),
                              closeOnPress=True))

            menuDict['NE'].append(
                ToolboxButton(label='bake to Local', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\local_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceLocalValues),
                              closeOnPress=True))
            menuDict['NE'].append(
                ToolboxButton(label='bake to Global', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\world_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceGlobalValues),
                              closeOnPress=True))
            menuDict['NE'].append(
                ToolboxButton(label='bake to Default', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                              icon=IconPath + '\default_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceDefaultValues),
                              closeOnPress=True))

            menuDict['SW'].append(ToolboxButton(label='Select all Switch Controls',
                                                parent=self.presetMarkingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.presetMarkingMenuWidget,
                                                command=lambda: SpaceSwitch().selectAllSpaceSwitchControls(),
                                                closeOnPress=True))
            menuDict['SW'].append(ToolboxButton(label='Select all Global Controls',
                                                parent=self.presetMarkingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.presetMarkingMenuWidget,
                                                command=lambda: SpaceSwitch().selectAllGlobalSpaceControls(),
                                                closeOnPress=True))

            attrDict, enumNames, rigName, namespace = self.getSpaceDataForSelection()
            presets = self.loadedSpaceData[rigName].__dict__[str_spacePresets]
            if presets:
                menuDict['SE'].append(
                    ToolboDivider(label='Space Switch Presets', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget))
                for preset in presets.keys():
                    button = ToolboxButton(label='Switch', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                                           command=pm.Callback(self.switchFromPreset, preset, rigName, namespace),
                                           closeOnPress=True)
                    altButton = ToolboxButton(label='Bake', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget,
                                              command=pm.Callback(self.bakeFromPreset, preset, rigName, namespace),
                                              closeOnPress=True)
                    menuDict['SE'].append(ToolboxDoubleButton(preset,
                                                              self.presetMarkingMenuWidget,
                                                              cls=self.presetMarkingMenuWidget,
                                                              buttons=[button, altButton]))
                menuDict['SE'].append(
                    ToolboDivider(label='Space Switch', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget))


        menuDict['SW'].append(ToolboDivider(label='', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Open SpaceSwitch Editor',
                                            icon=IconPath + '\popupWindow.png',
                                            parent=self.presetMarkingMenuWidget,
                                            cls=self.presetMarkingMenuWidget,
                                            command=pm.Callback(SpaceSwitch().openEditorWindow),
                                            closeOnPress=True))
        menuDict['SW'].append(ToolboDivider(label='', parent=self.presetMarkingMenuWidget, cls=self.presetMarkingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Save selection as preset...',
                                            parent=self.presetMarkingMenuWidget,
                                            cls=self.presetMarkingMenuWidget,
                                            command=pm.Callback(SpaceSwitch().saveSelectionAsPreset),
                                            closeOnPress=True))

    def openMM(self):
        self.build_MM()
        self.markingMenuWidget.show()

    def build_MM(self, parentMenu=None):
        menuDict = {'NE': list(),
                    'NW': list(),
                    'SE': list(),
                    'SW': list()
                    }

        # TODO - change this so the event filter doesn't get rebuilt all the time
        self.markingMenuWidget = ViewportDialog(menuDict=menuDict, parentMenu=parentMenu)

        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)
        # make this better...?

        if sel:
            menuDict['NW'].append(
                ToolboxButton(label='switch to Local', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\local_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceLocalValues),
                              closeOnPress=True))
            menuDict['NW'].append(
                ToolboxButton(label='switch to Global', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\world_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceGlobalValues),
                              closeOnPress=True))
            menuDict['NW'].append(
                ToolboxButton(label='switch to Default', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\default_base.png',
                              command=lambda: self.switchTo(sel, mode=str_spaceDefaultValues),
                              closeOnPress=True))

            menuDict['NE'].append(
                ToolboxButton(label='bake to Local', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\local_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceLocalValues),
                              closeOnPress=True))
            menuDict['NE'].append(
                ToolboxButton(label='bake to Global', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\world_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceGlobalValues),
                              closeOnPress=True))
            menuDict['NE'].append(
                ToolboxButton(label='bake to Default', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\default_base.png',
                              command=lambda: self.bakeTo(sel, mode=str_spaceDefaultValues),
                              closeOnPress=True))

            menuDict['SW'].append(ToolboxButton(label='Select all Switch Controls',
                                                parent=self.markingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: SpaceSwitch().selectAllSpaceSwitchControls(),
                                                closeOnPress=True))
            menuDict['SW'].append(ToolboxButton(label='Select all Global Controls',
                                                parent=self.markingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: SpaceSwitch().selectAllGlobalSpaceControls(),
                                                closeOnPress=True))

            attrDict, enumNames, rigName, namespace = self.getSpaceDataForSelection()
            presets = self.loadedSpaceData[rigName].__dict__[str_spacePresets]
            if presets:
                menuDict['SE'].append(
                    ToolboDivider(label='Space Switch Presets', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
                for preset in presets.keys():
                    button = ToolboxButton(label='Switch', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                           command=pm.Callback(self.switchFromPreset, preset, rigName, namespace),
                                           closeOnPress=True)
                    altButton = ToolboxButton(label='Bake', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                              command=pm.Callback(self.bakeFromPreset, preset, rigName, namespace),
                                              closeOnPress=True)
                    menuDict['SE'].append(ToolboxDoubleButton(preset,
                                                              self.markingMenuWidget,
                                                              cls=self.markingMenuWidget,
                                                              buttons=[button, altButton]))
                menuDict['SE'].append(
                    ToolboDivider(label='Space Switch', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
            for space in enumNames:
                valueDict = {k: space for k in attrDict.keys()}
                button = ToolboxButton(label='Switch', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                       command=pm.Callback(self.switchFromData, attrDict, valueDict),
                                       closeOnPress=True)
                altButton = ToolboxButton(label='Bake', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                          command=pm.Callback(self.bakeFromData, attrDict, valueDict),
                                          closeOnPress=True)
                menuDict['SE'].append(ToolboxDoubleButton(space,
                                                          self.markingMenuWidget,
                                                          cls=self.markingMenuWidget,
                                                          buttons=[button, altButton]))

        menuDict['SW'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Open SpaceSwitch Editor',
                                            icon=IconPath + '\popupWindow.png',
                                            parent=self.markingMenuWidget,
                                            cls=self.markingMenuWidget,
                                            command=pm.Callback(SpaceSwitch().openEditorWindow),
                                            closeOnPress=True))
        menuDict['SW'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Save selection as preset...',
                                            parent=self.markingMenuWidget,
                                            cls=self.markingMenuWidget,
                                            command=pm.Callback(SpaceSwitch().saveSelectionAsPreset),
                                            closeOnPress=True))
        menuDict['SW'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Save current state as ...',
                                            parent=self.markingMenuWidget,
                                            cls=self.markingMenuWidget,
                                            closeOnPress=True,
                                            popupSubMenu=True,
                                            subMenuClass=SaveCurrentStateWidget))

    def togglePopupSwitchMode(self):
        self.popupSwitchMode = not self.popupSwitchMode

    def loadAllCharacters(self):
        """
        #TODO: make this happen on startup and save
        :return:
        """
        self.allCharacters = dict()
        self.allSpaceAttributes = list()
        for file_name in [f for f in os.listdir(self.subPath) if f.endswith('.json')]:
            refname = file_name.split('.')[0]
            spaceData = self.loadRigData(SpaceData(), refname)
            self.loadedSpaceData[refname] = spaceData

            allSpaceAttrs = list(set([x.split('.')[-1] for x in self.loadedSpaceData[refname].spaceControl.keys()]))
            if not allSpaceAttrs:
                continue
            for attr in allSpaceAttrs:
                if attr in self.allSpaceAttributes:
                    continue
                self.allSpaceAttributes.append(attr)

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

            if refname not in self.loadedSpaceData.keys():
                self.saveRigFileIfNew(refname, SpaceData().toJson())

            spaceData = self.loadRigData(SpaceData(), refname)
            self.loadedSpaceData[refname] = spaceData
        self.namespaceToCharDict = namespaceToCharDict

    def simplifySpaceKeys(self, spaceAttribute='space'):
        """
        reduce the space switch attribute keys to a minimum
        :param node:
        :param spaceAttribute:
        :return:
        """
        with self.funcs.keepSelection():
            # make a list so we can send multiple objects in one go
            if not isinstance(spaceAttribute, list):
                spaceAttribute = [spaceAttribute]

            for attr in spaceAttribute:
                spaceSwitchAttr = pm.Attribute(attr)

                cmds.select(clear=True)

                allSpaceAttrKeyTimes = sorted(list(set(pm.keyframe(spaceSwitchAttr, query=True))))
                duplicateSpaceKeyTimes = []
                spaceAttrValues = pm.keyframe(spaceSwitchAttr, query=True, valueChange=True)
                for index in range(0, len(spaceAttrValues) - 1):
                    if spaceAttrValues[index] != spaceAttrValues[index + 1]:
                        continue
                    duplicateSpaceKeyTimes.append(allSpaceAttrKeyTimes[index + 1])

                # remove the duplicate values
                for keyTime in duplicateSpaceKeyTimes:
                    pm.cutKey(spaceSwitchAttr, time=keyTime)

                # put this as an option
                pm.keyframe(spaceSwitchAttr, tickDrawSpecial=True)

                # set the tangents to stepped and flat
                pm.keyTangent(spaceSwitchAttr, outTangentType='step', inTangentType='linear')

    def getAllControlsInSpace(self, mode=str_spaceGlobalValues):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        allControls = list()
        for char in characters:
            for key in self.loadedSpaceData[self.namespaceToCharDict[char]].spaceControl.keys():
                control = char + ':' + key
                if not cmds.objExists(control):
                    continue
                node, attr = control.split('.')
                globalValue = self.loadedSpaceData[self.namespaceToCharDict[char]].spaceGlobalValues.get(key, None)
                if not globalValue:
                    continue
                if not cmds.attributeQuery(attr, node=node, attributeType=True) == 'enum':
                    if cmds.getAttr(control) == globalValue:
                        allControls.append(control)
                        continue
                enumValues = cmds.attributeQuery(attr, node=node, listEnum=True)
                enumList = enumValues[0].split(':')
                index = cmds.getAttr(control)
                value = enumList[index]
                if value == globalValue:
                    allControls.append(node)
                    continue
        return allControls

    def getAllSpaceSwitchControls(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        allControls = list()
        for char in characters:
            allControls.extend(
                [char + ':' + c.split('.')[0] for c in
                 self.loadedSpaceData[self.namespaceToCharDict[char]].spaceControl.keys()])
        return allControls

    def getAllSpaceSwitchAttributes(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        allControls = list()
        outDict = dict()
        for char in characters:
            outDict[char] = [c for c in self.loadedSpaceData[self.namespaceToCharDict[char]].spaceControl.keys()]
        return outDict, characters

    def selectAllSpaceSwitchControls(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        cmds.select(self.getAllSpaceSwitchControls(), replace=True)

    def selectAllGlobalSpaceControls(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        cmds.select(self.getAllControlsInSpace(), replace=True)

    def switchSelection(self, mode=str_spaceGlobalValues):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected to switch')
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)
        self.switchTo(sel, mode=mode)

    def bakeSelection(self, mode=str_spaceGlobalValues):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected to switch')
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)
        self.bakeTo(sel, mode=mode)

    def bakeTo(self, selection, mode=str_spaceGlobalValues):
        attributes, values = self.makeSwitchData(selection=selection, mode=mode)
        self.bakeFromData(attributes, values)
        cmds.select(selection, replace=True)

    def switchTo(self, selection, mode=str_spaceGlobalValues):
        attributes, values = self.makeSwitchData(selection=selection, mode=mode)
        self.switchFromData(attributes, values)
        cmds.select(selection, replace=True)

    def captureData(self, mode=str_spaceGlobalValues, presetName=None):
        selection = cmds.ls(sl=True)

        if not selection:
            return
        characters = self.funcs.splitSelectionToCharacters(selection)
        self.loadDataForCharacters(characters)

        for s in selection:
            if ':' in s:
                namespace, control = s.split(':', 1)
            else:
                namespace = ''
                control = s
            rigName = self.namespaceToCharDict[namespace]
            controlValues = list(self.loadedSpaceData[rigName].spaceControl.values())
            if control not in controlValues:
                continue
            controlIndex = controlValues.index(control)
            attribute = list(self.loadedSpaceData[rigName].spaceControl.keys())[controlIndex]
            attributeType = cmds.getAttr(namespace + ':' + attribute, type=True)
            node, attr = str(namespace + ':' + attribute).split('.', 1)
            if attributeType == 'enum':

                enumValues = cmds.attributeQuery(attr, node=node, listEnum=True)
                enumList = enumValues[0].split(':')
                index = cmds.getAttr(namespace + ':' + attribute)
                value = enumList[index]
            else:
                value = cmds.getAttr(namespace + ':' + attribute)

            if presetName is None:
                self.loadedSpaceData[rigName].__dict__[mode][control + '.' + attr] = value
            else:
                if not self.loadedSpaceData[rigName].spacePresets.get(presetName):
                    self.loadedSpaceData[rigName].spacePresets[presetName] = dict()

                self.loadedSpaceData[rigName].spacePresets[presetName][control + '.' + attr] = value
            SpaceSwitch().saveRigData(rigName, self.loadedSpaceData[rigName].toJson())

    def makeSwitchData(self, selection=list(), mode=str_spaceGlobalValues):
        switchAttrData = dict()
        switchValueData = dict()

        for s in selection:
            if ':' in s:
                namespace, control = s.split(':', 1)
            else:
                namespace = ''
                control = s

            rigName = self.namespaceToCharDict[namespace]

            attrKeys = list(self.loadedSpaceData[rigName].spaceControl.keys())
            controlValues = list(self.loadedSpaceData[rigName].spaceControl.values())
            if control not in controlValues:
                continue
            attribute = attrKeys[controlValues.index(control)]

            globalValue = self.loadedSpaceData[rigName].spaceGlobalValues.get(attribute, 0)
            localValue = self.loadedSpaceData[rigName].spaceLocalValues.get(attribute, 0)
            defaultValue = self.loadedSpaceData[rigName].spaceDefaultValues.get(attribute, 0)
            switchValueData[namespace + ':' + attribute] = {str_spaceGlobalValues: globalValue,
                                                            str_spaceLocalValues: localValue,
                                                            str_spaceDefaultValues: defaultValue}[mode]
            switchAttrData[namespace + ':' + attribute] = s
        return switchAttrData, switchValueData

    def getSwitchDataFromScene(self, selection=list()):
        switchAttrData = dict()
        switchValueData = dict()
        for s in selection:
            namespace, control = s.split(':', 1)
            rigName = self.namespaceToCharDict[namespace]
            controlValues = list(self.loadedSpaceData[rigName].spaceControl.values())
            if control not in controlValues:
                continue
            controlIndex = controlValues.index(control)
            attribute = list(self.loadedSpaceData[rigName].spaceControl.keys())[controlIndex]
            attributeType = cmds.getAttr(namespace + ':' + attribute, type=True)
            if attributeType == 'enum':
                node, attr = str(namespace + ':' + attribute).split('.', 1)
                enumValues = cmds.attributeQuery(attr, node=node, listEnum=True)
                enumList = enumValues[0].split(':')
                index = cmds.getAttr(namespace + ':' + attribute)
                value = enumList[index]
            else:
                value = cmds.getAttr(namespace + ':' + attribute)
            switchValueData[attr] = value
            switchAttrData[attr] = control
        return rigName, switchAttrData, switchValueData

    def getMatchRange(self, sel, timeline=False):
        """
        Returns a list of all key times for the input object list, if the timeline is highlighted
        :param sel: input object list
        :param timeline: Force visible timeline range
        :return:
        """
        if timeline:
            startTime, endTime = self.funcs.getTimelineRange()
        elif self.funcs.isTimelineHighlighted():
            startTime, endTime = self.funcs.getTimelineHighlightedRange()
        else:
            return [cmds.currentTime(query=True)]
        return [x for x in self.funcs.get_all_key_times_for_node(sel) if x <= endTime and x >= startTime]

    def bakeFromData(self, attributes, values):
        resultLayer = None
        timeRange = self.funcs.getTimelineRange()
        bakeOption = pm.optionVar.get(self.bakeToLayerModeOption, self.bakeLayerModes[0])
        initialTime = cmds.currentTime(query=True)
        preSel = cmds.ls(sl=True)
        selection = list(set(attributes.values()))
        if not selection:
            return
        if bakeOption != self.bakeLayerModes[-1]:
            resultLayer = self.createLayer()
            # collect all attributes and bake explicitly
            bakeAttributes = self.getAllAnimatedChannels(selection)
            bakeAttributes.extend(list(attributes.values()))

        self.bakeSpaceSwitch(selection=selection,
                             resultLayer=str(resultLayer),
                             spaceAttributes=attributes,
                             bakeAttributes=bakeAttributes,
                             values=values,
                             startTime=timeRange[0],
                             endTime=timeRange[-1],
                             bakeOption=bakeOption)
        cmds.select(preSel, replace=True)

    def bakeSpaceSwitch(self, selection=list(),
                        resultLayer=str(),
                        spaceAttributes=dict(),
                        bakeAttributes=dict(),
                        values=dict(),
                        startTime=0,
                        endTime=0,
                        bakeOption=str()):
        locators = dict()
        tempConstraints = dict()
        if not isinstance(selection, list):
            selection = [selection]
        for s in selection:
            loc = self.funcs.tempNull(name=s, suffix='space')
            locators[s] = str(loc)
            cmds.parentConstraint(s, str(loc))

        with self.funcs.suspendUpdate():
            cmds.bakeResults(list(locators.values()),
                             time=(startTime, endTime),
                             # simulation=pm.optionVar.get(self.quickBakeSimOption, False),
                             simulation=True,
                             sampleBy=1)

        for s in selection:
            tempConstraints[s] = str(
                self.funcs.safeParentConstraint(locators[s], s, orientOnly=False, maintainOffset=False))

        cmds.animLayer(resultLayer, edit=True, attribute=list(spaceAttributes.keys()))
        cmds.animLayer(resultLayer, edit=True, selected=True)
        cmds.animLayer(resultLayer, edit=True, preferred=True)

        for key, attr in spaceAttributes.items():
            spaceSwitchAttr = pm.Attribute(key)
            spaceValue = values[key]
            if not isinstance(values[key], int) and not isinstance(values[key], float):
                spaceEnums = dict((k.lower(), v) for k, v in spaceSwitchAttr.getEnums().items())
                spaceValue = spaceEnums[spaceValue.lower()]

            cmds.setKeyframe(key, time=(startTime, endTime), value=spaceValue)

        with self.funcs.suspendUpdate():
            cmds.bakeResults(bakeAttributes,
                             time=(startTime, endTime),
                             destinationLayer=resultLayer,
                             # simulation=pm.optionVar.get(self.quickBakeSimOption, False),
                             simulation=True,
                             sampleBy=1)

        cmds.delete(list(tempConstraints.values()))
        cmds.delete(list(locators.values()))

    def getAllAnimatedChannels(self, controls):
        allAttributes = list()
        for c in controls:
            attributes = cmds.listAttr(c, keyable=True, settable=True)
            allAttributes.extend([c + '.' + a for a in attributes])
        return allAttributes

    def getSpaceDataForSelection(self):
        sel = cmds.ls(sl=True)

        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        dataControls = dict()
        allAttrNames = list()
        dataValues = dict()
        valueSet = set()
        ordered_spaces = []
        all_spaces = list()
        finalSpaceList = list()
        unknownControls = list()
        for s in sel:
            node = pm.PyNode(s)
            if not ':' in s:
                namespace = ''
                control = s
            else:
                namespace, control = s.split(':', 1)
            rigName = self.namespaceToCharDict.get(namespace, None)

            if not rigName:
                unknownControls.append(s)
            else:
                allSpaceAttrs = list(set([x.split('.')[-1] for x in self.loadedSpaceData[rigName].spaceControl.keys()]))

                if rigName not in self.loadedSpaceData.keys():
                    unknownControls.append(s)
                    continue
                attrs = list(self.loadedSpaceData[rigName].spaceControl.keys())
                values = list(self.loadedSpaceData[rigName].spaceControl.values())
                if control in values:
                    attr = attrs[values.index(control)]
                    attrName = attr.split('.')[-1]
                    p_attr = pm.Attribute(s + '.' + attrName)
                    if not cmds.attributeQuery(attrName, node=s, attributeType=True) == 'enum':
                        continue

                    spaceValues = p_attr.getEnums()
                    all_spaces.append(spaceValues)

                    allAttrNames.append(attrName)
                    dataValues[namespace + ':' + attr] = spaceValues
                    dataControls[namespace + ':' + attr] = namespace + ':' + control
                else:
                    # control is part of the rig, but undefined
                    # look for space attribites in the existing data
                    for attrName in self.allSpaceAttributes:
                        if not cmds.attributeQuery(attrName, node=s, exists=True):
                            continue
                        if not cmds.attributeQuery(attrName, node=s, attributeType=True) == 'enum':
                            continue
                        p_attr = pm.Attribute(s + '.' + attrName)
                        spaceValues = p_attr.getEnums()
                        all_spaces.append(spaceValues)

                        allAttrNames.append(attrName)
                        dataValues[namespace + ':' + control + '.' + attrName] = spaceValues
                        dataControls[namespace + ':' + control + '.' + attrName] = namespace + ':' + control
                        self.loadedSpaceData[rigName].addControlsWithMatchingAttribute(namespace, [control], attrName)
                        # set the default values based on existing values
                        index = cmds.getAttr(namespace + ':' + control + '.' + attrName)
                        value = spaceValues[index]
                        self.loadedSpaceData[rigName].__dict__[str_spaceGlobalValues][control + '.' + attrName] = \
                            spaceValues.keys()[0]
                        self.loadedSpaceData[rigName].__dict__[str_spaceLocalValues][control + '.' + attrName] = \
                            spaceValues.keys()[-1]
                        self.loadedSpaceData[rigName].__dict__[str_spaceDefaultValues][control + '.' + attrName] = value
                        SpaceSwitch().saveRigData(rigName, self.loadedSpaceData[rigName].toJson())
                        SpaceSwitch().loadAllCharacters()

        allAttrNames = set(allAttrNames)
        for c in unknownControls:
            if not ':' in c:
                namespace = ''
                control = c
            else:
                namespace, control = s.split(':', 1)
            userAttrs = cmds.listAttr(c, userDefined=True, keyable=True)
            intersection = allAttrNames.intersection(set(userAttrs))
            if not intersection:
                continue
            attrName = list(intersection)[0]
            p_attr = pm.Attribute(control + '.' + attrName)
            spaceValues = p_attr.getEnums()
            all_spaces.append(spaceValues)
            dataValues[attr] = spaceValues
            dataControls[attr] = namespace + ':' + c

        for space in all_spaces:
            ordered_sub_space = []
            for index in range(len(space)):
                ordered_sub_space.append(space.key(index))
            ordered_spaces.append(ordered_sub_space)

        if ordered_spaces:
            finalSpaceList = list(
                sorted(set(ordered_spaces[0]).intersection(*ordered_spaces), key=ordered_spaces[0].index))
        return dataControls, finalSpaceList, rigName, namespace

    def createLayer(self):
        newAnimLayer = pm.animLayer('SpaceSwitch',
                                    override=True)
        newAnimLayer.rotationAccumulationMode.set(True)
        newAnimLayer.ghostColor.set(self.allTools.tools['BakeTools'].overrideLayerColour)
        self.allTools.tools['BakeTools'].deselect_layers()
        newAnimLayer.selected.set(True)
        newAnimLayer.preferred.set(True)
        newAnimLayer.scaleAccumulationMode.set(0)
        return newAnimLayer

    def switchFromPreset(self, preset, rigName, namespace):
        presetData = self.loadedSpaceData[rigName].spacePresets[preset]
        values = dict()
        attributes = dict()
        for key, value in presetData.items():
            control = namespace + ':' + key.split('.')[0]
            attributes[namespace + ':' + key] = control
            values[namespace + ':' + key] = value

        self.switchFromData(attributes, values)
    def bakeFromPreset(self, preset, rigName, namespace):
        presetData = self.loadedSpaceData[rigName].spacePresets[preset]
        values = dict()
        attributes = dict()
        for key, value in presetData.items():
            control = namespace + ':' + key.split('.')[0]
            control.split('.')[0]
            attributes[namespace + ':' + key] = control
            values[namespace + ':' + key] = value
        self.bakeFromData(attributes, values)

    def switchFromData(self, attributes, values):
        timeDict = dict()
        selection = list(attributes.values())
        attributeKeyList = list(attributes.keys())
        for s in selection:
            timeDict[s] = self.getMatchRange(s, timeline=False)

        combinedTimeList = sorted({x for v in list(timeDict.values()) for x in v})

        if len(combinedTimeList) > 1:
            with self.funcs.suspendUpdate():
                for t in combinedTimeList[::-1]:
                    cmds.currentTime(t)
                    for index, s in enumerate(selection):
                        if s not in timeDict.keys():
                            continue
                        attributeKey = attributeKeyList[index]
                        self.simpleSpaceSwitch(node=s,
                                               spaceValue=values[attributeKey],
                                               spaceAttribute=attributeKey)
                for control in selection:
                    cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')
        else:
            for index, s in enumerate(selection):
                attributeKey = attributeKeyList[index]
                self.simpleSpaceSwitch(node=s,
                                       spaceValue=values[attributeKey],
                                       spaceAttribute=attributeKey)
            for control in selection:
                cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')

    def simpleSpaceBake(self, node=str(), spaceValue=None, spaceAttribute='space'):
        """
        Single frame space switch - from marking menu, not from data
        :param node:
        :param space:
        :param spaceAttribute:
        :return:
        """
        if not cmds.objExists(node):
            return pm.warning(node + ' does not exist')
        if not isinstance(node, list):
            node = [node]
        resultLayer = None
        timeRange = self.funcs.getTimelineRange()
        bakeOption = pm.optionVar.get(self.bakeToLayerModeOption, self.bakeLayerModes[0])
        initialTime = cmds.currentTime(query=True)
        if bakeOption != self.bakeLayerModes[-1]:
            resultLayer = self.createLayer()
            # collect all attributes and bake explicitly
            bakeAttributes = self.getAllAnimatedChannels(node)
            bakeAttributes.append(node[0] + '.' + spaceAttribute)
        spaceAttributeDict = dict()
        spaceValueDict = dict()
        for n in node:
            spaceAttributeDict[n + '.' + spaceAttribute] = n
            spaceValueDict[n + '.' + spaceAttribute] = spaceValue

        self.bakeSpaceSwitch(selection=node,
                             resultLayer=str(resultLayer),
                             spaceAttributes=spaceAttributeDict,
                             bakeAttributes=bakeAttributes,
                             values=spaceValueDict,
                             startTime=timeRange[0],
                             endTime=timeRange[-1],
                             bakeOption=bakeOption)
        cmds.currentTime(initialTime)
        cmds.select(node, replace=True)

    def simpleSpaceSwitch(self, node=str(), spaceValue=None, spaceAttribute='space'):
        """
        Single frame space switch
        :param node:
        :param space:
        :param spaceAttribute:
        :return:
        """
        if not cmds.objExists(node):
            return pm.warning(node + ' does not exist')
        # if there is no control node specified, just use the main node

        spaceSwitchAttr = pm.Attribute(node + '.' + spaceAttribute)

        if not isinstance(spaceValue, int) and not isinstance(spaceValue, float):
            spaceEnums = dict((k.lower(), v) for k, v in list(spaceSwitchAttr.getEnums().items()))
            spaceValue = spaceEnums[spaceValue.lower()]

        rotation = cmds.xform(node, query=True, absolute=True, worldSpace=True, rotation=True)
        translation = cmds.xform(node, query=True, absolute=True, worldSpace=True, translation=True)

        cmds.setAttr(spaceAttribute, spaceValue)
        cmds.xform(node, absolute=True, worldSpace=True, translation=translation)
        cmds.xform(node, absolute=True, worldSpace=True, rotation=rotation)
        '''
        # store the matrix
        storedMtx = self.funcs.getMatrix(node)

        # swap the space value
        pm.setAttr(spaceSwitchAttr, spaceValue)

        # get the new matrix
        postMtx = self.funcs.getMatrix(node)
        # also the parent matrix
        parentMtx = self.funcs.getMatrix(node, matrix='parentMatrix')

        # get the new position and rotation
        pos, rot = self.funcs.getMatrixOffset(node, storedMtx, postMtx, parentMtx)

        # rotate is
        cmds.xform(node, relative=True, rotation=rot)

        postMtx = self.funcs.getMatrix(node)
        parentMtx = self.funcs.getMatrix(node, matrix='parentMatrix')
        pos, rot = self.funcs.getMatrixOffset(node, storedMtx, postMtx, parentMtx)
        # translate it
        cmds.xform(node, relative=True, translation=pos)
        '''
        if pm.keyframe(node, query=True) and pm.autoKeyframe(state=True, q=True):
            try:
                cmds.setKeyframe(node + '.translate')
            except:
                pass
            try:
                cmds.setKeyframe(node + '.rotate')
            except:
                pass
            cmds.setKeyframe(str(spaceSwitchAttr))
        self.simplifySpaceKeys(spaceAttribute=spaceSwitchAttr)
        self.deleteBlendAttributes(node)

    def deleteBlendAttributes(self, node):
        for attr in pm.listAttr(node, userDefined=True, keyable=True):
            if attr not in self.culledUserAttributes:
                continue
            # deleted constraints remove the connection to the blend point/parent/orient attributes
            # if there's no connection then it's safe to delete, probably
            if not pm.listConnections(node + '.' + attr, source=False, destination=True):
                pm.deleteAttr(node + '.' + attr)

    def findSpaceAttributes(self, sel):
        if not sel:
            return
        for s in sel:
            customAttrs = cmds.listAttr(s, userDefined=True)

    def storeCurrentState(self, sel, key=str_spaceLocalValues):
        if not sel:
            return
        attrDict, characters = self.getAllSpaceSwitchAttributes()
        if not attrDict.keys():
            return cmds.warning('no characters found')
        for character, attributes in attrDict.items():
            for attr in attributes:
                attrName = self.namespaceToCharDict[character] + ':' + attr
                attributeType = cmds.getAttr(attrName, type=True)
                if attributeType == 'enum':
                    node, attrStripped = str(attrName).split('.', 1)
                    enumValues = cmds.attributeQuery(attrStripped, node=node, listEnum=True)
                    enumList = enumValues[0].split(':')
                    index = cmds.getAttr(attrName)
                    value = enumList[index]
                else:
                    value = cmds.getAttr(attrName)
                self.loadedSpaceData[character].__dict__[key][attr] = value
            SpaceSwitch().saveRigData(character, self.loadedSpaceData[character].toJson())
        self.loadDataForCharacters(characters)

    def getSavePresetSignal(self, name=str()):
        self.captureData(presetName=name)

    def saveSelectionAsPreset(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return pm.warning('Unable to save preset with no selection')

        attrDict, characters = self.getAllSpaceSwitchAttributes()
        if not attrDict.keys():
            return cmds.warning('no characters found')
        # TODO - make this ui nice
        dialog = PresetSaveWidget(title='Save Space Preset',
                                  label='Enter Name',
                                  buttonText="Save",
                                  default=sel[-1].split(':')[-1])
        dialog.acceptedSignal.connect(self.getSavePresetSignal)

    def openEditorWindow(self):
        if not self.win:
            self.win = SpaceSwitchSetupUI()
        self.win.show()


class ToolboxWidget(ViewportDialog):
    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget), menuDict=dict()):
        super(ToolboxWidget, self).__init__(parent=parent)
        # TODO - make this part of the space switch class, add buttons to the base dialog class
        # TODO - move custom code here into maain class
        # TODO - fix double action
        self.app = QApplication.instance()
        self.keyPressHandler = markingMenuKeypressHandler(UI=self)
        self.app.installEventFilter(self.keyPressHandler)


class SubToolboxWidget(ViewportDialog):
    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                 parentMenu=None):
        super(SubToolboxWidget, self).__init__(parent=parent, parentMenu=parentMenu)

        if self.parentMenu:
            self.parentMenu.setEnabled(False)

        self.addButton(quad='NE', button=ToolboxButton(label='SubMENU NE', parent=self, cls=self,
                                                       command=None,
                                                       closeOnPress=True))

        self.addButton(quad='NW', button=ToolboxButton(label='SubMENU NW', parent=self, cls=self, command=None,
                                                       closeOnPress=True))

        self.addButton(quad='SE', button=ToolboxButton(label='SubMENU SE', parent=self, cls=self, command=None,
                                                       closeOnPress=True))

        self.addButton(quad='SW', button=ToolboxButton(label='SubMENU SW', parent=self, cls=self, command=None,
                                                       closeOnPress=True,
                                                       subMenuClass=SubToolboxWidget,
                                                       popupSubMenu=True
                                                       ))


class SaveCurrentStateWidget(ViewportDialog):
    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                 parentMenu=None):
        super(SaveCurrentStateWidget, self).__init__(parent=parent, parentMenu=parentMenu)

        if self.parentMenu:
            self.parentMenu.setEnabled(False)

        self.addButton(quad='SW', button=ToolboxButton(label='Store as Global', parent=self, cls=self,
                                                       command=lambda: SpaceSwitch().captureData(
                                                           mode=str_spaceGlobalValues, presetName=None),
                                                       closeOnPress=True))
        self.addButton(quad='SW', button=ToolboxButton(label='Store as local', parent=self, cls=self,
                                                       command=lambda: SpaceSwitch().captureData(
                                                           mode=str_spaceLocalValues, presetName=None),
                                                       closeOnPress=True))

        self.addButton(quad='SW', button=ToolboxButton(label='Store as Default', parent=self, cls=self,
                                                       command=lambda: SpaceSwitch().captureData(
                                                           mode=str_spaceDefaultValues, presetName=None),
                                                       closeOnPress=True))
        '''
        self.addButton(quad='SW', button=ToolboxButton(label='SubMENU SW', parent=self, cls=self, command=None,
                                                       closeOnPress=True,
                                                       subMenuClass=SubToolboxWidget,
                                                       popupSubMenu=True
                                                       ))
        '''


class SpaceSwitchSetupUI(QMainWindow):
    def __init__(self):
        super(SpaceSwitchSetupUI, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))

        self.setObjectName('SpaceSwitch_SetupUI')

        self.controlWidgets = {}
        self.spaceData = SpaceData()
        self.rigName = str()
        self.namespace = str()
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbSpaceSwitch Setup Tool')

        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_widget.setLayout(self.main_layout)

        self.globalHeader = HeaderWidget('Global Value')
        self.localHeader = HeaderWidget('Local Value')
        self.defaultHeader = HeaderWidget('Default Value')
        self.mirrorHeader = HeaderWidget('Mirror Value')
        self.globalHeader.pressedSignal.connect(lambda: self.captureState(key=str_spaceGlobalValues))
        self.localHeader.pressedSignal.connect(lambda: self.captureState(key=str_spaceLocalValues))
        self.defaultHeader.pressedSignal.connect(lambda: self.captureState(key=str_spaceDefaultValues))
        self.mirrorHeader.pressedSignal.connect(lambda: self.captureState(key=str_spaceMirrorValues))

        self.controlsLayout = QVBoxLayout()
        self.controlsSubLayout = QGridLayout()
        self.controlsSubLayout.setSpacing(0)
        self.controlsSubLayout.addWidget(QLabel('Attribute'), 0, 0)
        self.controlsSubLayout.addWidget(QLabel('Control'), 0, 1)
        self.controlsSubLayout.addWidget(self.globalHeader, 0, 2)
        self.controlsSubLayout.addWidget(self.localHeader, 0, 3)
        self.controlsSubLayout.addWidget(self.defaultHeader, 0, 4)
        self.controlsSubLayout.addWidget(self.mirrorHeader, 0, 5)
        self.controlsSubLayout.setColumnStretch(0, 0)
        self.controlsSubLayout.setColumnStretch(1, 0)
        self.controlsSubLayout.setColumnStretch(2, 0)
        self.controlsSubLayout.setColumnStretch(3, 0)
        self.controlsSubLayout.setColumnStretch(4, 0)
        self.controlsSubLayout.setColumnStretch(5, 0)
        self.controlsSubLayout.setColumnStretch(7, 0)
        self.controlsSubLayout.setColumnStretch(7, 100)

        self.controlsSpacerLayout = QVBoxLayout()
        self.controlsSpacerLayout.addStretch()
        spacer = QSpacerItem(20, 200, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.controlsSpacerLayout.addItem(spacer)
        self.controlsLayout.addLayout(self.controlsSubLayout)
        self.controlsLayout.addLayout(self.controlsSpacerLayout)
        self.controlsLayout.setAlignment(Qt.AlignTop)
        self.controlsFrame = QFrame()
        self.controlsScrollArea = QScrollArea()
        self.controlsScrollArea.setWidget(self.controlsFrame)
        self.controlsScrollArea.setWidgetResizable(True)
        self.controlsFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.controlsFrame.setLayout(self.controlsLayout)

        menu = self.menuBar()
        edit_menu = menu.addMenu('&File')
        load_action = QAction('Load data for current rig', self)
        load_action.setShortcut('Ctrl+C')
        edit_menu.addAction(load_action)
        load_action.triggered.connect(self.getCurrentRig)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        edit_menu.addAction(save_action)
        save_action.triggered.connect(self.save)

        self.limbUpdateWidget = SpaceControlWidget()
        self.limbUpdateWidget.addNewSignal.connect(self.addNewControls)
        # cuurent rig label
        self.currentRigLabel = QLabel('Current Rig ::')
        self.currentRigNameLabel = QLabel('None')
        self.rigLayout = QVBoxLayout()
        self.rigLabelLayout = QHBoxLayout()
        self.rigLabelLayout.addWidget(self.currentRigLabel)
        self.rigLabelLayout.addWidget(self.currentRigNameLabel)
        self.rigLabelLayout.addWidget(self.limbUpdateWidget)

        self.main_layout.addLayout(self.rigLabelLayout)

        # self.controlsLayout.addWidget(SwitchableObjectWidget(self))
        self.main_layout.addWidget(self.controlsScrollArea)
        self.resize(1100, 200)
        # self.controlsLayout.addStretch()
        # self.controlsLayout.addWidget(SwitchableObjectWidget(self))
        self.setObjectName('SpaceSetupUI')
        self.selectionChangedCallback = -1
        self.createSelectionChangedScriptJob()

    def createSelectionChangedScriptJob(self):
        self.selectionChangedCallback = cmds.scriptJob(event=("SelectionChanged", pm.Callback(self.selectionChanged)))
        return self.selectionChangedCallback

    def selectionChanged(self, *args):
        controls = self.getPendingControls()

        for k, v in self.spaceData.spaceControl.items():
            if v in controls:
                self.controlWidgets[k].controlWidget.errorHighlight()
            else:
                self.controlWidgets[k].controlWidget.errorHighlightRemove()

    def errorHighlight(self, widget):
        borderHighlightQSS = "{background-color: red}"

        widget.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

    @Slot()
    def getSideChangedSignal(self, sideA, sideB):
        self.spaceData.sideA = sideA
        self.spaceData.sideB = sideB

    @Slot()
    def toggleEnabledState(self, state):
        self.main_widget.setEnabled(state)
        self.limbUpdateWidget.dialog.setEnabled(True)

    @Slot()
    def addNewControls(self):
        if not self.spaceData:
            self.getCurrentRig()
        if not self.spaceData:
            return cmds.error('No current rig loaded')
        self.pendingControls = None
        sel = cmds.ls(sl=True)

        if not sel:
            return cmds.warning('nothing selected')
        self.pendingControls = sel
        refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)

        if refState:
            self.namespace = cmds.referenceQuery(sel[0], namespace=True).rsplit(':')[-1]
            pendingControls = [str(x).split(self.namespace)[-1].split(':', 1)[-1] for x in self.pendingControls]
            self.pendingControls = pendingControls

        # get controls, look for partial space name? text input?
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            self.dialog = ChannelInputWidget(title='Please select space attribute in the channelBox',
                                             label='Enter Name', buttonText="Save")
            self.dialog.acceptedSignal.connect(self.addNewControlsWithAttribute)
        else:
            self.addNewControlsWithAttribute(channels[0].split('.')[-1])

    def getPendingControls(self):
        sel = cmds.ls(sl=True)

        if not sel:
            cmds.warning('nothing selected')
            return []
        pendingControls = sel
        refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)

        if refState:
            namespace = cmds.referenceQuery(sel[0], namespace=True).rsplit(':')[-1]
            if namespace:
                pendingControls = [str(x).split(namespace)[-1].split(':', 1)[-1] for x in pendingControls]
            else:
                pendingControls = [str(x) for x in pendingControls]
        return pendingControls

    def addNewControlsWithAttribute(self, attribute):
        self.spaceData.addControlsWithMatchingAttribute(self.namespace, self.pendingControls, attribute)
        self.refreshUI()

    def captureState(self, key=str_spaceGlobalValues):
        for attr in self.spaceData.spaceControl.keys():
            attrName = self.namespace + ':' + attr
            attributeType = cmds.getAttr(attrName, type=True)
            if attributeType == 'enum':
                node, attrStripped = str(attrName).split('.', 1)
                enumValues = cmds.attributeQuery(attrStripped, node=node, listEnum=True)
                enumList = enumValues[0].split(':')
                index = cmds.getAttr(attrName)
                value = enumList[index]
            else:
                value = cmds.getAttr(attrName)
            self.spaceData.__dict__[key][attr] = value
        self.refreshUI()

    def remove(self):
        pass
        self.spaceData.limbs.pop(self.currentLimb)
        self.rigIKFKListWidget.updateView(self.spaceData.limbs.keys())
        self.limbStackedWidget.setCurrentWidget(self.blankWidget)

    @Slot()
    def mirrorLimb(self, inputData):
        pass
        self.spaceData.limbs[inputData] = self.spaceData.limbs[self.currentLimb].__class__()
        for k, v in self.spaceData.limbs[self.currentLimb].__dict__.items():
            if k == 'limbWidget':
                continue
            self.spaceData.limbs[inputData].__dict__[k] = v

        self.spaceData.limbs[inputData].mirrorControls(self.limbUpdateWidget.sideA.text(),
                                                       self.limbUpdateWidget.sideB.text())
        self.rigIKFKListWidget.updateView(self.spaceData.limbs.keys())

    def getCurrentRig(self):
        self.rigName, self.namespace = SpaceSwitch().funcs.getCurrentRig()
        SpaceSwitch().saveRigFileIfNew(self.rigName, SpaceData().toJson())

        self.currentRigNameLabel.setText(self.rigName)

        self.spaceData = SpaceSwitch().loadRigData(SpaceData(), self.rigName)

    def enableAndRefreshUI(self):
        if self.rigName:
            self.enableUI()
            self.refreshUI()

    def save(self):
        SpaceSwitch().saveRigData(self.rigName, self.spaceData.toJson())

    def enableUI(self):
        self.limbUpdateWidget.setEnabled(True)

    def disableUI(self):
        self.limbUpdateWidget.setEnabled(False)

    def show(self):
        super(SpaceSwitchSetupUI, self).show()
        sel = cmds.ls(sl=True)
        if sel:
            self.getCurrentRig()
        if self.rigName:
            self.enableAndRefreshUI()
        else:
            self.disableUI()

    def refreshUI(self):

        for key, widget in self.controlWidgets.items():
            if key not in self.spaceData.spaceControl.keys():
                self.controlsSubLayout.removeWidget(widget)
                self.controlWidgets.pop(key)
                widget.close()
                widget.deleteLater()
        self.attrRows = dict()
        for spaceAttribute in list(self.spaceData.spaceControl.keys()):
            count = self.controlsSubLayout.rowCount()

            if spaceAttribute not in self.controlWidgets.keys():
                self.controlWidgets[spaceAttribute] = SwitchableObjectWidget(self, spaceAttribute)
                self.controlWidgets[spaceAttribute].blockSignals(True)
                self.controlWidgets[spaceAttribute].objectDeletedSignal.connect(self.deleteEntry)
                self.attrRows[spaceAttribute] = count + 1
                self.controlWidgets[spaceAttribute].blockSignals(False)

            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].spaceAttributeWidget, count + 1, 0)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].controlWidget, count + 1, 1)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].globalValuesWidgets.stackWidget,
                                             count + 1, 2)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].localValuesWidgets.stackWidget,
                                             count + 1, 3)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].defaultValuesWidgets.stackWidget,
                                             count + 1, 4)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].mirrorValuesWidgets.stackWidget,
                                             count + 1, 5)
            self.controlsSubLayout.addWidget(self.controlWidgets[spaceAttribute].deleteButton, count + 1, 6)
            self.controlWidgets[spaceAttribute].spaceAttributeWidget.lineEdit.setFixedWidth(300)
            self.controlsSubLayout.setColumnMinimumWidth(0, 300)

        self.controlsLayout.setAlignment(Qt.AlignTop)

    def deleteEntry(self, key):
        if key not in self.controlWidgets.keys():
            return
        widget = self.controlWidgets[key]
        self.spaceData.removeItem(key)
        self.controlWidgets[key].deleteLater()
        self.controlWidgets[key].spaceAttributeWidget.deleteLater()
        self.controlWidgets[key].controlWidget.deleteLater()
        self.controlWidgets[key].globalValuesWidgets.stackWidget.deleteLater()
        self.controlWidgets[key].localValuesWidgets.stackWidget.deleteLater()
        self.controlWidgets[key].defaultValuesWidgets.stackWidget.deleteLater()
        self.controlWidgets[key].mirrorValuesWidgets.stackWidget.deleteLater()
        self.controlWidgets[key].deleteButton.deleteLater()
        self.controlsLayout.removeWidget(widget)
        self.controlWidgets.pop(key)
        widget.close()
        widget.deleteLater()

    def closeEvent(self, event):
        cmds.scriptJob(kill=self.selectionChangedCallback)

        event.accept()

    """
    Test functions
    """


class SpaceControlWidget(QWidget):
    addNewSignal = Signal()
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)
    sideUpdateSignal = Signal(str, str)

    def __init__(self):
        super(SpaceControlWidget, self).__init__()
        self.setMaximumHeight(200)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setObjectName('LimbUpdateWidget')
        self.setLayout(self.mainLayout)
        self.addRemoveLayout = QHBoxLayout()
        self.addButton = QPushButton('Add Control')
        self.removeButton = QPushButton('Remove')
        self.mirrorLayout = QHBoxLayout()
        self.sideLabel = QLabel('Sides')
        self.sideA = QLineEdit('_L_')
        self.sideB = QLineEdit('_R_')
        self.mirrorButton = QPushButton('Mirror Limb')

        self.mainLayout.addWidget(self.addButton)
        '''
        self.mainLayout.addLayout(self.addRemoveLayout)
        self.addRemoveLayout.addWidget(self.addButton)
        self.addRemoveLayout.addWidget(self.removeButton)
        self.mainLayout.addWidget(self.mirrorButton)
        self.mirrorLayout.addWidget(self.sideLabel)
        self.mirrorLayout.addWidget(self.sideA)
        self.mirrorLayout.addWidget(self.sideB)
        self.mirrorLayout.addWidget(self.mirrorButton)

        self.mainLayout.addLayout(self.mirrorLayout)
        # self.mainLayout.addStretch()
        '''
        self.addButton.clicked.connect(self.addNew)
        self.mirrorButton.clicked.connect(self.mirror)
        self.sideA.textEdited.connect(self.sideUpdated)
        self.sideB.textEdited.connect(self.sideUpdated)

    def sideUpdated(self):
        self.sideUpdateSignal.emit(self.sideA.text(), self.sideB.text())

    def addNew(self):
        self.addNewSignal.emit()

    def enableMainWidget(self):
        self.enableMainWidgetSignal.emit(True)

    def getAddNewSignal(self, inputData, ikType):
        self.addNewSignal.emit(inputData, ikType)

    def mirror(self):
        sel = cmds.ls(sl=True)
        if not sel:
            defaultName = 'RENAME_ME'
        else:
            defaultName = sel[0].split(':', 1)[-1]
        self.dialog = TextInputWidget(title='Mirror limb data', label='Enter Name', buttonText="Save",
                                      default=defaultName,
                                      parent=self)

        self.enableMainWidgetSignal.emit(False)
        self.dialog.acceptedSignal.connect(self.getMirrorSignal)
        self.dialog.rejectedSignal.connect(self.enableMainWidget)

    def getMirrorSignal(self, inputData):
        self.mirrorSignal.emit(inputData)


class SwitchValuesIntWidget(QWidget):
    editedSignal = Signal(str, float)

    def __init__(self):
        super(SwitchValuesIntWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.localIntValueWidget = intFieldWidget(key=str_spaceGlobalValues,
                                                  optionVar=None, defaultValue=0, label='Global value', maximum=9999,
                                                  minimum=-9999,
                                                  step=1)
        self.globalIntValueWidget = intFieldWidget(key=str_spaceLocalValues,
                                                   optionVar=None, defaultValue=0, label='Local value', maximum=9999,
                                                   minimum=-9999,
                                                   step=1)
        self.defaultIntValueWidget = intFieldWidget(key=str_spaceDefaultValues,
                                                    optionVar=None, defaultValue=0, label='Default value', maximum=9999,
                                                    minimum=-9999,
                                                    step=1)
        self.mirrorIntValueWidget = intFieldWidget(key=str_spaceMirrorValues,
                                                   optionVar=None, defaultValue=0, label='Mirror value', maximum=9999,
                                                   minimum=-9999,
                                                   step=1)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalIntValueWidget)
        self.mainLayout.addWidget(self.localIntValueWidget)
        self.mainLayout.addWidget(self.defaultIntValueWidget)
        self.mainLayout.addWidget(self.mirrorIntValueWidget)

        self.localIntValueWidget.editedSignalKey.connect(self.edited)
        self.globalIntValueWidget.editedSignalKey.connect(self.edited)
        self.defaultIntValueWidget.editedSignalKey.connect(self.edited)

    def edited(self, key, value):
        self.editedSignal.emit(key, value)


class SwitchValuesEnumWidget(QWidget):
    editedSignal = Signal(str, str)

    def __init__(self):
        super(SwitchValuesEnumWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.globalValueWidget = comboBoxWidget(key=str_spaceGlobalValues,
                                                optionVar=None, values=list(), defaultValue=str(),
                                                label='Global value')
        self.localValueWidget = comboBoxWidget(key=str_spaceLocalValues,
                                               optionVar=None, values=list(), defaultValue=str(),
                                               label='Local value')
        self.defaultValueWidget = comboBoxWidget(key=str_spaceDefaultValues,
                                                 optionVar=None, values=list(), defaultValue=str(),
                                                 label='Default value')
        self.mirrorValueWidget = comboBoxWidget(key=str_spaceMirrorValues,
                                                optionVar=None, values=list(), defaultValue=str(),
                                                label='Mirror value')
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalValueWidget)
        self.mainLayout.addWidget(self.localValueWidget)
        self.mainLayout.addWidget(self.defaultValueWidget)
        self.mainLayout.addWidget(self.mirrorValueWidget)

        self.globalValueWidget.editedSignalKey.connect(self.edited)
        self.localValueWidget.editedSignalKey.connect(self.edited)
        self.defaultValueWidget.editedSignalKey.connect(self.edited)
        self.mirrorValueWidget.editedSignalKey.connect(self.edited)

    def updateEnums(self, enumList, globalVal, localVal, defaultVal):
        self.globalValueWidget.updateValues(enumList, globalVal)
        self.localValueWidget.updateValues(enumList, localVal)
        self.defaultValueWidget.updateValues(enumList, defaultVal)
        self.mirrorValueWidget.updateValues(enumList, defaultVal)

    def edited(self, key, value):
        self.editedSignal.emit(key, value)


class SwitchValuesDoubleWidget(QWidget):
    editedSignal = Signal(str, float)

    def __init__(self):
        super(SwitchValuesDoubleWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.localIntValueWidget = intFieldWidget(key=str_spaceGlobalValues,
                                                  optionVar=None, defaultValue=0, label='Global value', maximum=9999,
                                                  minimum=-9999,
                                                  step=0.1)
        self.globalIntValueWidget = intFieldWidget(key=str_spaceLocalValues,
                                                   optionVar=None, defaultValue=0, label='Local value', maximum=9999,
                                                   minimum=-9999,
                                                   step=0.1)
        self.defaultIntValueWidget = intFieldWidget(key=str_spaceDefaultValues,
                                                    optionVar=None, defaultValue=0, label='Default value', maximum=9999,
                                                    minimum=-9999,
                                                    step=0.1)
        self.mirrorIntValueWidget = intFieldWidget(key=str_spaceMirrorValues,
                                                   optionVar=None, defaultValue=0, label='Mirror value', maximum=9999,
                                                   minimum=-9999,
                                                   step=0.1)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalIntValueWidget)
        self.mainLayout.addWidget(self.localIntValueWidget)
        self.mainLayout.addWidget(self.defaultIntValueWidget)
        self.mainLayout.addWidget(self.mirrorIntValueWidget)

        self.localIntValueWidget.editedSignalKey.connect(self.edited)
        self.globalIntValueWidget.editedSignalKey.connect(self.edited)
        self.defaultIntValueWidget.editedSignalKey.connect(self.edited)

    def edited(self, key, value):
        self.editedSignal.emit(key, value)


class SwitchValuesComboWidget(QWidget):
    enumEditedSignal = Signal(str, str)
    doubleEditedSignal = Signal(str, float)

    def __init__(self, key=str_spaceGlobalValues):
        super(SwitchValuesComboWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.stackWidget = QStackedWidget(self)
        self.mainLayout.addWidget(self.stackWidget)
        self.enumWidget = comboBoxWidget(key=key,
                                         optionVar=None, values=list(), defaultValue=str(),
                                         label=str())
        self.intWidget = intFieldWidget(key=key,
                                        optionVar=None, defaultValue=0, label=str(), maximum=9999,
                                        minimum=-9999,
                                        step=0.1)
        self.floatWidget = intFieldWidget(key=key,
                                          optionVar=None, defaultValue=0, label=str(), maximum=9999,
                                          minimum=-9999,
                                          step=1)

        self.setLayout(self.mainLayout)
        self.stackWidget.addWidget(self.enumWidget)
        self.stackWidget.addWidget(self.intWidget)
        self.stackWidget.addWidget(self.floatWidget)
        # self.mainLayout.addWidget(self.enumWidget)
        # self.mainLayout.addWidget(self.intWidget)
        # self.mainLayout.addWidget(self.floatWidget)

        self.enumWidget.editedSignalKey.connect(self.edited)
        self.intWidget.editedSignalKey.connect(self.doubleEdited)
        self.floatWidget.editedSignalKey.connect(self.doubleEdited)

    def updateEnums(self, enumList, value):
        self.blockSignals(True)
        self.enumWidget.updateValues(enumList, value)
        self.blockSignals(False)

    def updateDoubles(self, value):
        self.blockSignals(True)
        self.floatWidget.updateValues(value)
        self.blockSignals(False)

    def updateInts(self, value):
        self.blockSignals(True)
        self.intWidget.updateValues(value)
        self.blockSignals(False)

    def edited(self, key, value):
        self.enumEditedSignal.emit(key, value)

    def doubleEdited(self, key, value):
        self.doubleEditedSignal.emit(key, value)

    def showEnum(self):
        self.stackWidget.setCurrentWidget(self.enumWidget)

    def showDouble(self):
        self.stackWidget.setCurrentWidget(self.floatWidget)

    def showInt(self):
        self.stackWidget.setCurrentWidget(self.intWidget)


class SwitchableObjectWidget(QWidget):
    editedSignal = Signal(dict)
    objectDeletedSignal = Signal(str)

    def __init__(self, cls, attributeName):
        super(SwitchableObjectWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.cls = cls
        self.key = attributeName

        self.attributeTypeFunctions = {'enum': self.showEnum,
                                       'double': self.showDouble,
                                       'int': self.showInt
                                       }

        self.mainLayout = QHBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.controlWidget = ObjectSelectLineEdit(key='control',
                                                  label=str(),
                                                  stripNamespace=True)
        # self.controlWidget.label.setFixedWidth(66)
        self.spaceAttributeWidget = ChannelSelectLineEdit(key=str_spaceControlKey,
                                                          text=str(),
                                                          tooltip='Pick attribute to control space switch.',
                                                          stripNamespace=True)
        self.spaceAttributeWidget.label.deleteLater()
        # self.spaceAttributeWidget.lineEdit.setFixedWidth(200)
        self.deleteButton = QPushButton()
        self.deleteButton.setFixedSize(18, 18)
        self.deleteButton.setIcon((QIcon(':/deleteActive.png')))

        self.deleteButton.clicked.connect(lambda: self.objectDeletedSignal.emit(self.key))
        self.globalValuesWidgets = SwitchValuesComboWidget(key=str_spaceGlobalValues)
        self.localValuesWidgets = SwitchValuesComboWidget(key=str_spaceLocalValues)
        self.defaultValuesWidgets = SwitchValuesComboWidget(key=str_spaceDefaultValues)
        self.mirrorValuesWidgets = SwitchValuesComboWidget(key=str_spaceMirrorValues)
        self.globalValuesWidgets.enumEditedSignal.connect(self.valuesEdited)
        self.globalValuesWidgets.doubleEditedSignal.connect(self.valuesEdited)
        self.localValuesWidgets.enumEditedSignal.connect(self.valuesEdited)
        self.localValuesWidgets.doubleEditedSignal.connect(self.valuesEdited)
        self.defaultValuesWidgets.enumEditedSignal.connect(self.valuesEdited)
        self.defaultValuesWidgets.doubleEditedSignal.connect(self.valuesEdited)
        self.mirrorValuesWidgets.enumEditedSignal.connect(self.valuesEdited)
        self.mirrorValuesWidgets.doubleEditedSignal.connect(self.valuesEdited)

        objSelectWidgets = [self.controlWidget,
                            ]
        for wd in objSelectWidgets:
            wd.editedSignalKey.connect(self.updateControlName)

        # self.spaceAttributeWidget.editedSignalKey.connect(self.updateData)
        self.spaceAttributeWidget.editedSignalKey.connect(self.updateAttributeType)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.valuesLayout = QHBoxLayout()
        self.valuesLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.fkLayout = QVBoxLayout()
        self.ikLayout = QVBoxLayout()

        # self.controlLayout.addWidget(self.controlWidget)

        self.mainLayout.addLayout(self.controlLayout)
        self.mainLayout.addLayout(self.valuesLayout)

        # add stuff to layouts
        self.controlLayout.addWidget(self.controlWidget)
        self.controlLayout.addWidget(self.spaceAttributeWidget)
        self.controlLayout.addWidget(self.globalValuesWidgets)
        self.controlLayout.addWidget(self.localValuesWidgets)
        self.controlLayout.addWidget(self.defaultValuesWidgets)
        self.controlLayout.addWidget(self.mirrorValuesWidgets)
        spacer = QSpacerItem(20, 20, QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.controlLayout.addItem(spacer)
        self.controlLayout.addStretch()
        self.controlLayout.addWidget(self.deleteButton)
        self.controlLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # self.controlLayout.addStretch()
        # self.valuesLayout.addStretch()

        self.valuesWidgets = [
            self.globalValuesWidgets,
            self.localValuesWidgets,
            self.defaultValuesWidgets,
            self.mirrorValuesWidgets,
        ]
        self.hideAllValueWidgets()
        widgets = [x for x in self.mainLayout.children() if x.__class__.__name__ == 'ObjectSelectLineEdit']

        self.refresh()

    def refresh(self):
        self.controlWidget.itemLabel.setText(self.cls.spaceData.spaceControl[self.key])
        self.spaceAttributeWidget.lineEdit.setText(self.key)

    def hideAllValueWidgets(self):
        pass
        for widget in self.valuesWidgets:
            widget.setVisible(False)

    def showEnum(self):
        self.hideAllValueWidgets()
        self.globalValuesWidgets.showEnum()
        self.localValuesWidgets.showEnum()
        self.defaultValuesWidgets.showEnum()
        self.mirrorValuesWidgets.showEnum()

        # self.defaultValuesWidgets.setVisible(True)
        self.update()

    def showDouble(self):
        self.hideAllValueWidgets()
        self.globalValuesWidgets.showDouble()
        self.localValuesWidgets.showDouble()
        self.defaultValuesWidgets.showDouble()
        self.mirrorValuesWidgets.showDouble()
        # self.localValuesWidgets.setVisible(True)
        self.update()

    def showInt(self):
        self.hideAllValueWidgets()
        self.globalValuesWidgets.showInt()
        self.localValuesWidgets.showInt()
        self.defaultValuesWidgets.showInt()
        self.mirrorValuesWidgets.showInt()
        # self.globalValuesWidgets.setVisible(True)
        self.update()

    def valuesEdited(self, key, value):
        self.cls.spaceData.__dict__[key][self.key] = value

    def updateControlName(self, key, value):
        self.cls.spaceData.spaceControl[self.key] = value
        '''
        for k in self.cls.spaceData.__dict__.keys():
            if self.key in self.cls.spaceData.__dict__[k].keys():
                self.cls.spaceData.__dict__[k][value] = self.cls.spaceData.__dict__[k].pop(self.key)
        '''

    def updateData(self, key, value):
        self.cls.spaceData.__dict__[key][self.key] = value

    def updateAttributeType(self, key, value):
        """
        Update the widgets containing the space values
        :param key:
        :param value:
        :return:
        """
        # swap out existing entry
        if self.key in self.cls.spaceData.spaceGlobalValues.keys():
            self.cls.spaceData.spaceGlobalValues[value] = self.cls.spaceData.spaceGlobalValues.pop(self.key)
        if self.key in self.cls.spaceData.spaceLocalValues.keys():
            self.cls.spaceData.spaceLocalValues[value] = self.cls.spaceData.spaceLocalValues.pop(self.key)
        if self.key in self.cls.spaceData.spaceDefaultValues.keys():
            self.cls.spaceData.spaceDefaultValues[value] = self.cls.spaceData.spaceDefaultValues.pop(self.key)
        if self.key in self.cls.spaceData.spaceControl.keys():
            self.cls.spaceData.spaceControl[value] = self.cls.spaceData.spaceControl.pop(self.key)

        if value.startswith(self.key):
            value.strip(self.key)
        if '.' not in value:
            value = self.key + '.' + value
        if self.cls.namespace:
            attrName = self.cls.namespace + ':' + value
        else:
            attrName = value

        obj, attr = attrName.split('.')

        if not cmds.objExists(obj):
            self.hideAllValueWidgets()
            return False
        if not cmds.attributeQuery(attr, node=obj, exists=True):
            self.hideAllValueWidgets()
            return False

        attributeType = cmds.getAttr(attrName, type=True)
        self.attributeTypeFunctions.get(attributeType, self.showDouble)()
        if attributeType == 'enum':
            node, attr = attrName.split('.', 1)
            enumValues = cmds.attributeQuery(attr, node=node, listEnum=True)
            enumList = enumValues[0].split(':')
            globalVal = self.cls.spaceData.spaceGlobalValues.get(self.key, enumList[0])
            localVal = self.cls.spaceData.spaceLocalValues.get(self.key, enumList[-1])
            defaultVal = self.cls.spaceData.spaceDefaultValues.get(self.key, enumList[0])
            mirrorVal = self.cls.spaceData.spaceDefaultValues.get(self.key, enumList[0])
            self.globalValuesWidgets.updateEnums(enumList,
                                                 globalVal)
            self.localValuesWidgets.updateEnums(enumList,
                                                localVal)
            self.defaultValuesWidgets.updateEnums(enumList,
                                                  defaultVal)
            self.mirrorValuesWidgets.updateEnums(enumList,
                                                 mirrorVal)
        if attributeType == 'int':
            globalVal = self.cls.spaceData.spaceGlobalValues.get(self.key, 0)
            localVal = self.cls.spaceData.spaceLocalValues.get(self.key, 0)
            defaultVal = self.cls.spaceData.spaceDefaultValues.get(self.key, 0)
            mirrorVal = self.cls.spaceData.spaceDefaultValues.get(self.key, 0)
            self.globalValuesWidgets.updateInts(globalVal)
            self.localValuesWidgets.updateInts(localVal)
            self.defaultValuesWidgets.updateInts(defaultVal)
            self.mirrorValuesWidgets.updateInts(mirrorVal)
        if attributeType == 'double':
            globalVal = self.cls.spaceData.spaceGlobalValues.get(self.key, 0)
            localVal = self.cls.spaceData.spaceLocalValues.get(self.key, 0)
            defaultVal = self.cls.spaceData.spaceDefaultValues.get(self.key, 0)
            mirrorVal = self.cls.spaceData.spaceDefaultValues.get(self.key, 0)
            self.globalValuesWidgets.updateDoubles(globalVal)
            self.localValuesWidgets.updateDoubles(localVal)
            self.defaultValuesWidgets.updateDoubles(defaultVal)
            self.mirrorValuesWidgets.updateDoubles(mirrorVal)
        return True


"""
limb setup - space might be on another control
space data - attribute is full object+attribute

space data setup - select all controls, guess by attribute type (enum) or name
space data names for int based space
popup hotkey for bake whole char to preset, list in popup
presets in sub menu - work on selection
add selected control + highlighted channel as control

"""


class HeaderWidget(QWidget):
    pressedSignal = Signal()

    def __init__(self, text):
        super(HeaderWidget, self).__init__()
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.label = QLabel(text)
        self.button = QPushButton()
        self.button.setFixedSize(22, 22)
        self.button.setIcon(QIcon(':\down_arrow.png'))
        self.button.setToolTip('Capture current states')
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.button)
        self.button.clicked.connect(self.sendPressedSignal)

    def sendPressedSignal(self):
        self.pressedSignal.emit()


class PresetSaveWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedCBSignal = Signal(str, bool, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title='Save Selection Set', label='Name', buttonText=str(), default=str(), combo=list(),
                 checkBox=None, overlay=False, showCloseButton=True, key=str(), subKey=str(),
                 helpString=None,
                 parentWidget=None,
                 qss=False,
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(PresetSaveWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())

        self.combo = combo
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        self.mirrorCheckbox = QCheckBox()
        self.mirrorCheckbox.setText('Mirror')
        self.qssCheckbox = QCheckBox()
        self.qssCheckbox.setChecked(qss)
        self.qssCheckbox.setText('Quick')

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)

        self.lineEdit = QLineEdit(default)
        self.lineEdit.setMinimumWidth(120)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        # self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        # self.lineEdit.setFocus()
        self.lineEdit.setFixedWidth(
            max(120, self.lineEdit.fontMetrics().boundingRect(self.lineEdit.text()).width() + 28))
        self.setStyleSheet(
            "PresetSave { "
            "border-radius: 8;"
            "}"
        )

        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.sizeHint())

        self.show()
        # self.setFixedSize(400, 64)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedCBSignal.emit(self.lineEdit.text(),
                                   self.qssCheckbox.isChecked(),
                                   self.mirrorCheckbox.isChecked())
        self.close()

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(PresetSaveWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        try:
            return super(PresetSaveWidget, self).keyPressEvent(event)
        except:
            return

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        if self.overlay:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def show(self):
        position_x = (self.parent().pos().x() + (self.parent().width() - self.frameGeometry().width()) / 2)
        position_y = (self.parent().pos().y() + (self.parent().height() - self.frameGeometry().height()) / 2)

        self.move(position_x, position_y)
        super(PresetSaveWidget, self).show()
