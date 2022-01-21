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

        self.addCommand(self.tb_hkey(name='tbOpenSpaceSwitchMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.openMM()']))
        self.addCommand(self.tb_hkey(name='tbCloseSpaceSwitchMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.closeMM()']))
        self.addCommand(self.tb_hkey(name='tbOpenSpaceSwitchDataEditor',
                                     annotation='useful comment',
                                     category=self.category, command=['SpaceSwitch.openEditorWindow()']))

        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class SpaceData(object):
    def __init__(self):
        self.spaceAttribute = {}  #
        self.spaceGlobalValues = {}  #
        self.spaceLocalValues = {}  #
        self.spaceDefaultValues = {}  #
        self.spacePresets = dict()  # key is preset name, value is a dict of control:spaces

    def setDefaultSpaceAttribute(self, attribute):
        self.spaceAttribute['default'] = attribute

    def setControlSpaceAttribute(self, control, attribute):
        self.spaceAttribute[control] = attribute

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
                matches = {at: SequenceMatcher(None, at, 'RIKLegSpace').ratio() for at in attrs}
                bestMatch = max(matches, key=matches.get)
            self.setControlSpaceAttribute(control, bestMatch)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict['spaceAttribute'] = self.spaceAttribute
        returnDict['spaceGlobalValues'] = self.spaceGlobalValues
        returnDict['spaceLocalValues'] = self.spaceLocalValues
        returnDict['spaceDefaultValues'] = self.spaceDefaultValues
        returnDict['spacePresets'] = dict()
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))

        self.spaceAttribute = rawJsonData.get('spaceAttribute', dict())
        self.spaceGlobalValues = rawJsonData.get('spaceGlobalValues', dict())
        self.spaceLocalValues = rawJsonData.get('spaceLocalValues', dict())
        self.spaceDefaultValues = rawJsonData.get('spaceDefaultValues', dict())
        self.spacePresets = rawJsonData.get('spacePresets', dict())

    def removeItem(self, key):
        self.spaceAttribute.pop(key)
        self.spaceGlobalValues.pop(key)
        self.spaceLocalValues.pop(key)
        self.spaceDefaultValues.pop(key)

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

    bakeTimelineModes = ['Full timeline', 'Visible Timeline', 'All Keys']
    bakeTimelineModeOption = 'tbSpaceBakeTimelineMode'
    bakeLayerModes = ['To Override', 'To Override - Extract anim', 'To Base']
    bakeToLayerModeOption = 'tbSpaceBakeToLayerMode'

    loadedSpaceData = dict()  # store loaded data per session to avoid accessing the disc all the time
    namespaceToCharDict = dict()
    spaceDataDict = dict()

    def __new__(cls):
        if SpaceSwitch.__instance is None:
            SpaceSwitch.__instance = object.__new__(cls)
            SpaceSwitch.__instance.initData()

        SpaceSwitch.__instance.val = cls.toolName
        return SpaceSwitch.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

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

        infoText4 = QLabel('<b>Bake to layer</b> - An Ik/Fk bake will bake to a new override layer')
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
        self.layout.addWidget(infoText4)
        self.layout.addWidget(self.bakeLayerModeWidget)

        self.layout.addStretch()

        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='SpaceSwitch Data Editor', image='menuIconChannels.png',
                    command='tbOpenSpaceSwitchDataEditor', sourceType='mel',
                    parent=parentMenu)

    def build_MM(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)

        cmds.menuItem(label='Space Switch (temp)',
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        userAttrs = cmds.listAttr(sel[0], userDefined=True)
        if not userAttrs:
            return

        cmds.menuItem(label='Switch to Global',
                      image='bakeAnimation.png',
                      command=pm.Callback(self.switchTo, selection=sel, mode='global'))
        cmds.menuItem(optionBox=True,
                      optionBoxIcon='bakeAnimation.png',
                      command=pm.Callback(self.bakeTo, selection=sel, mode='global'))

        cmds.menuItem(label='Switch to Local',
                      image='bakeAnimation.png',
                      command=pm.Callback(self.switchTo, selection=sel, mode='local'))
        cmds.menuItem(optionBox=True,
                      optionBoxIcon='bakeAnimation.png',
                      command=pm.Callback(self.bakeTo, selection=sel, mode='local'))

        cmds.menuItem(label='Switch to Default',
                      image='bakeAnimation.png',
                      command=pm.Callback(self.switchTo, selection=sel, mode='default'))
        cmds.menuItem(optionBox=True,
                      optionBoxIcon='bakeAnimation.png',
                      command=pm.Callback(self.bakeTo, selection=sel, mode='default'))

        for attr in userAttrs:
            if cmds.attributeQuery(attr, node=sel[0], attributeType=True) == 'enum':
                if not cmds.getAttr('{c}.{a}'.format(c=sel[0], a=attr), keyable=True):
                    continue
                spaceValues = cmds.attributeQuery(attr, node=sel[0], listEnum=True)[0].split(':')

                # quick bake to global/local (user defined space)

                cmds.menuItem(divider=True)
                for space in spaceValues:
                    cmds.menuItem(label=space,
                                  image='bakeAnimation.png',
                                  command=pm.Callback(self.simpleSpaceSwitch, node=sel[0], spaceValue=space,
                                                      spaceAttribute=attr))
                    cmds.menuItem(optionBox=True,
                                  optionBoxIcon='bakeAnimation.png',
                                  command=pm.Callback(self.bakeSpaceSwitch, node=sel[0], spaceValue=space,
                                                      spaceAttribute=attr))
        cmds.menuItem(divider=True)
        cmds.menuItem('store current states as local',
                      command=pm.Callback(self.storeCurrentState, sel, characters, key='local', attribute=attr))
        cmds.menuItem('store current states as global',
                      command=pm.Callback(self.storeCurrentState, sel, characters, key='global', attribute=attr))

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        for key, value in characters.items():
            refname, namespace = self.funcs.getCurrentRig([value[0]])
            if namespace.startswith(':'):
                namespace = namespace.split(':', 1)[-1]
            namespaceToCharDict[namespace] = refname
            if refname not in self.loadedSpaceData.keys():
                self.saveRigFileIfNew(refname, SpaceData().toJson())
                spaceData = self.loadRigData(SpaceData(), refname)
                self.loadedSpaceData[refname] = spaceData
        self.namespaceToCharDict = namespaceToCharDict

    def simplifySpaceKeys(self, node, spaceAttribute='space'):
        """
        reduce the space switch attribute keys to a minimum
        :param node:
        :param spaceAttribute:
        :return:
        """
        with self.funcs.keepSelection():
            # make a list so we can send multiple objects in one go
            if not isinstance(node, list):
                nodes = [node]

            for node in nodes:
                if not isinstance(node, pm.nodetypes.Transform):
                    node = pm.PyNode(node)
                cmds.select(clear=True)

                allSpaceAttrKeyTimes = sorted(list(set(pm.keyframe(spaceAttribute, query=True))))
                duplicateSpaceKeyTimes = []
                spaceAttrValues = pm.keyframe(spaceAttribute, query=True, valueChange=True)
                for index in range(0, len(spaceAttrValues) - 1):
                    if spaceAttrValues[index] != spaceAttrValues[index + 1]:
                        continue
                    duplicateSpaceKeyTimes.append(allSpaceAttrKeyTimes[index + 1])

                # remove the duplicate values
                for keyTime in duplicateSpaceKeyTimes:
                    pm.cutKey(spaceAttribute, time=keyTime)

                # put this as an option
                pm.keyframe(spaceAttribute, tickDrawSpecial=True)

                # set the tangents to stepped and flat
                pm.keyTangent(spaceAttribute, outTangentType='step', inTangentType='linear')

    def bakeTo(self, selection, mode='global'):
        attributes, values = self.makeSwitchData(selection=selection, mode=mode)
        self.bakeFromData(selection, attributes, values)

    def switchTo(self, selection, mode='global'):
        attributes, values = self.makeSwitchData(selection=selection, mode=mode)
        self.switchFromData(selection, attributes, values)

    def makeSwitchData(self, selection=list(), mode='global'):
        switchAttrData = dict()
        switchValueData = dict()
        for s in selection:
            namespace, control = s.split(':', 1)
            rigName = self.namespaceToCharDict[namespace]
            attribute = self.loadedSpaceData[rigName].spaceAttribute[control]
            globalValue = self.loadedSpaceData[rigName].spaceGlobalValues[control]
            localValue = self.loadedSpaceData[rigName].spaceLocalValues[control]
            defaultValue = self.loadedSpaceData[rigName].spaceDefaultValues[control]
            switchValueData[s] = {'global': globalValue,
                                  'local': localValue,
                                  'default': defaultValue}[mode]
            switchAttrData[s] = namespace + ':' + attribute
        return switchAttrData, switchValueData

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

    def bakeFromData(self, selection, attributes, values):
        resultLayer = None
        timeRange = self.funcs.getTimelineRange()
        bakeOption = pm.optionVar.get(self.bakeToLayerModeOption, self.bakeLayerModes[0])
        initialTime = cmds.currentTime(query=True)
        if bakeOption != self.bakeLayerModes[-1]:
            resultLayer = self.createLayer()
            # collect all attributes and bake explicitly
            bakeAttributes = self.getAllAnimatedChannels(selection)
            bakeAttributes.extend(attributes.values())

        self.bakeSpaceSwitch(selection=selection,
                             resultLayer=str(resultLayer),
                             spaceAttributes=attributes,
                             bakeAttributes=bakeAttributes,
                             values=values,
                             startTime=timeRange[0],
                             endTime=timeRange[-1],
                             bakeOption=bakeOption)

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
        for s in selection:
            loc = self.funcs.tempNull(name=s, suffix='space')
            locators[s] = str(loc)
            cmds.parentConstraint(s, str(loc))

        with self.funcs.suspendUpdate():
            cmds.bakeResults(locators.values(),
                             time=(startTime, endTime),
                             simulation=True,
                             sampleBy=1)

        for s in selection:
            tempConstraints[s] = str(
                self.funcs.safeParentConstraint(locators[s], s, orientOnly=False, maintainOffset=False))

        cmds.animLayer(resultLayer, edit=True, attribute=spaceAttributes.values)
        for key, attr in spaceAttributes.items():
            spaceSwitchAttr = pm.Attribute(attr)
            spaceValue = values[key]
            if not isinstance(values[key], int) and not isinstance(values[key], float):
                spaceEnums = dict((k.lower(), v) for k, v in spaceSwitchAttr.getEnums().iteritems())
                spaceValue = spaceEnums[spaceValue.lower()]
            cmds.setAttr(attr, spaceValue)

        with self.funcs.suspendUpdate():
            cmds.bakeResults(bakeAttributes,
                             time=(startTime, endTime),
                             destinationLayer=resultLayer,
                             simulation=True,
                             sampleBy=1)

        cmds.delete(tempConstraints.values())
        cmds.delete(locators.values())

    def getAllAnimatedChannels(self, controls):
        allAttributes = list()
        for c in controls:
            attributes = cmds.listAttr(c, keyable=True, settable=True)
            allAttributes.extend([c + '.' + a for a in attributes])
        return allAttributes

    def createLayer(self):
        newAnimLayer = pm.animLayer('SpaceSwitch',
                                    override=True)
        newAnimLayer.ghostColor.set(self.allTools.tools['BakeTools'].overrideLayerColour)
        self.allTools.tools['BakeTools'].deselect_layers()
        newAnimLayer.selected.set(True)
        newAnimLayer.preferred.set(True)
        newAnimLayer.scaleAccumulationMode.set(0)
        return newAnimLayer

    def switchFromData(self, selection, attributes, values):
        timeDict = dict()
        for s in selection:
            timeDict[s] = self.getMatchRange(s, timeline=False)

        combinedTimeList = sorted({x for v in timeDict.itervalues() for x in v})

        if len(combinedTimeList) > 1:
            with self.funcs.suspendUpdate():
                for t in combinedTimeList:
                    cmds.currentTime(t)
                    for s in selection:
                        if s not in timeDict.keys():
                            continue
                        self.simpleSpaceSwitch(node=s,
                                               spaceValue=values[s],
                                               spaceAttribute=attributes[s])
                for control in selection:
                    cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')
        else:
            self.simpleSpaceSwitch(node=s,
                                   spaceValue=values[s],
                                   spaceAttribute=attributes[s])
            for control in selection:
                cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')

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

        spaceSwitchAttr = pm.Attribute(spaceAttribute)
        if not isinstance(spaceValue, int) and not isinstance(spaceValue, float):
            spaceEnums = dict((k.lower(), v) for k, v in spaceSwitchAttr.getEnums().iteritems())
            spaceValue = spaceEnums[spaceValue.lower()]

        # might not work nicely with frozen transforms
        worldRotation = pm.xform(node, query=True, absolute=True, worldSpace=True, rotation=True)

        # get the world pivot
        prePivot = dt.Vector(pm.xform(node, query=True, worldSpace=True, rotatePivot=True))

        spaceSwitchAttr.set(spaceValue)
        resultRelativeTranslation = dt.Vector(
            pm.xform(node, query=True, relative=True, worldSpace=True, translation=True))
        postPivot = dt.Vector(pm.xform(node, query=True, worldSpace=True, rotatePivot=True))

        outTranslation = resultRelativeTranslation + (prePivot - postPivot)

        # reset the position
        # maya has a persistent bug where it sometimes ignores an xform command, so we perform it twice here
        pm.xform(node, absolute=True, worldSpace=True, translation=outTranslation)
        pm.xform(node, absolute=True, worldSpace=True, translation=outTranslation)
        # reset the orientation
        pm.xform(node, absolute=True, worldSpace=True, rotation=worldRotation)
        pm.xform(node, absolute=True, worldSpace=True, rotation=worldRotation)

        if pm.keyframe(node, query=True) and pm.autoKeyframe(state=True, q=True):
            try:
                cmds.setKeyframe(node + '.translate')
            except:
                pass
            try:
                cmds.setKeyframe(node + '.rotate')
            except:
                pass
            cmds.setKeyframe(spaceAttribute)
        self.simplifySpaceKeys(node, spaceAttribute=spaceAttribute)
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

    def storeCurrentState(self, sel, characters, key='local', attribute=str()):
        if not sel:
            return
        allRigs = dict()
        # get all selected rigs and collect their controls
        return
        for char in characters:
            for s in sel:
                control = s.split(':', 1)[-1]
                for key, limb in self.loadedSpaceData[self.namespaceToCharDict[char]].limbs.items():
                    if limb.controlInData(control):
                        if key in limbsToMatch[char]:
                            continue
                        limbsToMatch[char].append(key)

            rig, namespace = self.funcs.getCurrentRig([s])
            if rig not in allRigs.keys():
                allRigs[rig] = list()
            allRigs[rig].append(s)
        for rig in allRigs.keys():
            self.saveRigFileIfNew(rig, SpaceData().toJson())

    def openEditorWindow(self):
        win = SpaceSwitchSetupUI()
        win.show()


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

        self.controlsLayout = QVBoxLayout()
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
            self.dialog = ChannelInputWidget(title='Space attribute?', label='Enter Name', buttonText="Save")
            self.dialog.acceptedSignal.connect(self.addNewControlsWithAttribute)
        else:
            self.addNewControlsWithAttribute(channels[0].split('.')[-1])

    def addNewControlsWithAttribute(self, attribute):
        self.spaceData.addControlsWithMatchingAttribute(self.namespace, self.pendingControls, attribute)
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
            if k is 'limbWidget':
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
            self.enableUI()
        else:
            self.disableUI()

    def refreshUI(self):
        for key, widget in self.controlWidgets.items():
            if key not in self.spaceData.spaceAttribute.keys():
                self.controlsLayout.removeWidget(widget)
                self.controlWidgets.pop(key)
                widget.close()
                widget.deleteLater()

        for control in self.spaceData.spaceAttribute.keys():
            if control not in self.controlWidgets.keys():
                self.controlWidgets[control] = SwitchableObjectWidget(self, control)
                self.controlWidgets[control].objectDeletedSignal.connect(self.deleteEntry)

                self.controlsLayout.addWidget(self.controlWidgets[control])
        self.controlsLayout.setAlignment(Qt.AlignTop)

    def deleteEntry(self, key):
        if key not in self.controlWidgets.keys():
            return
        widget = self.controlWidgets[key]
        self.spaceData.removeItem(key)
        self.controlsLayout.removeWidget(widget)
        self.controlWidgets.pop(key)
        widget.close()
        widget.deleteLater()

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
        self.addButton = QPushButton('Add')
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
    editedSignal = Signal(dict)

    def __init__(self):
        super(SwitchValuesIntWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.localIntValueWidget = intFieldWidget(key='spaceGlobalValues',
                                                  optionVar=None, defaultValue=0, label='Global value', maximum=9999,
                                                  minimum=-9999,
                                                  step=1)
        self.globalIntValueWidget = intFieldWidget(key='spaceLocalValues',
                                                   optionVar=None, defaultValue=0, label='Local value', maximum=9999,
                                                   minimum=-9999,
                                                   step=1)
        self.defaultIntValueWidget = intFieldWidget(key='spaceDefaultValues',
                                                    optionVar=None, defaultValue=0, label='Default value', maximum=9999,
                                                    minimum=-9999,
                                                    step=1)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalIntValueWidget)
        self.mainLayout.addWidget(self.localIntValueWidget)
        self.mainLayout.addWidget(self.defaultIntValueWidget)


class SwitchValuesEnumWidget(QWidget):
    editedSignal = Signal(str, str)

    def __init__(self):
        super(SwitchValuesEnumWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.globalValueWidget = comboBoxWidget(key='spaceGlobalValues',
                                                optionVar=None, values=list(), defaultValue=str(),
                                                label='Global value')
        self.localValueWidget = comboBoxWidget(key='spaceLocalValues',
                                               optionVar=None, values=list(), defaultValue=str(),
                                               label='Local value')
        self.defaultValueWidget = comboBoxWidget(key='spaceDefaultValues',
                                                 optionVar=None, values=list(), defaultValue=str(),
                                                 label='Default value')
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalValueWidget)
        self.mainLayout.addWidget(self.localValueWidget)
        self.mainLayout.addWidget(self.defaultValueWidget)

        self.globalValueWidget.editedSignalKey.connect(self.edited)
        self.localValueWidget.editedSignalKey.connect(self.edited)
        self.defaultValueWidget.editedSignalKey.connect(self.edited)

    def updateEnums(self, enumList, globalVal, localVal, defaultVal):
        self.globalValueWidget.updateValues(enumList, globalVal)
        self.localValueWidget.updateValues(enumList, localVal)
        self.defaultValueWidget.updateValues(enumList, defaultVal)

    def edited(self, key, value):
        self.editedSignal.emit(key, value)


class SwitchValuesDoubleWidget(QWidget):
    editedSignal = Signal(dict)

    def __init__(self):
        super(SwitchValuesDoubleWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.localIntValueWidget = intFieldWidget(key='spaceGlobalValues',
                                                  optionVar=None, defaultValue=0, label='Global value', maximum=9999,
                                                  minimum=-9999,
                                                  step=0.1)
        self.globalIntValueWidget = intFieldWidget(key='spaceLocalValues',
                                                   optionVar=None, defaultValue=0, label='Local value', maximum=9999,
                                                   minimum=-9999,
                                                   step=0.1)
        self.defaultIntValueWidget = intFieldWidget(key='spaceDefaultValues',
                                                    optionVar=None, defaultValue=0, label='Default value', maximum=9999,
                                                    minimum=-9999,
                                                    step=0.1)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.globalIntValueWidget)
        self.mainLayout.addWidget(self.localIntValueWidget)
        self.mainLayout.addWidget(self.defaultIntValueWidget)


class SwitchableObjectWidget(QWidget):
    editedSignal = Signal(dict)
    objectDeletedSignal = Signal(str)

    def __init__(self, cls, control):
        super(SwitchableObjectWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.cls = cls
        self.key = control

        self.attributeTypeFunctions = {'enum': self.showEnum,
                                       'double': self.showDouble,
                                       'int': self.showInt
                                       }

        self.mainLayout = QHBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        self.controlWidget = ObjectSelectLineEdit(key='control',
                                                  label='Control',
                                                  stripNamespace=True)

        self.spaceAttributeWidget = ChannelSelectLineEdit(key='spaceAttribute',
                                                          text='Attribute',
                                                          tooltip='Pick attribute to control ik blend.',
                                                          placeholderTest='enter condition attribute',
                                                          stripNamespace=True)
        self.spaceAttributeWidget.lineEdit.setFixedWidth(200)
        self.deleteButton = QPushButton()
        self.deleteButton.setIcon((QIcon(':/deleteActive.png')))

        self.deleteButton.clicked.connect(lambda: self.objectDeletedSignal.emit(self.key))
        self.intValuesWidget = SwitchValuesIntWidget()
        self.doubleValuesWidget = SwitchValuesDoubleWidget()
        self.enumValuesWidget = SwitchValuesEnumWidget()
        self.intValuesWidget.editedSignal.connect(self.valuesEdited)
        self.doubleValuesWidget.editedSignal.connect(self.valuesEdited)
        self.enumValuesWidget.editedSignal.connect(self.valuesEdited)

        objSelectWidgets = [self.controlWidget,
                            ]
        for wd in objSelectWidgets:
            wd.editedSignalKey.connect(self.updateControlName)

        self.spaceAttributeWidget.editedSignalKey.connect(self.updateData)
        self.spaceAttributeWidget.editedSignalKey.connect(self.updateAttributeType)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.valuesLayout = QHBoxLayout()
        self.valuesLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.fkLayout = QVBoxLayout()
        self.ikLayout = QVBoxLayout()

        self.controlLayout.addWidget(self.controlWidget)

        self.mainLayout.addLayout(self.controlLayout)
        self.mainLayout.addLayout(self.valuesLayout)

        # add stuff to layouts
        self.controlLayout.addWidget(self.controlWidget)
        self.controlLayout.addWidget(self.spaceAttributeWidget)
        self.controlLayout.addWidget(self.intValuesWidget)
        self.controlLayout.addWidget(self.doubleValuesWidget)
        self.controlLayout.addWidget(self.enumValuesWidget)
        self.controlLayout.addWidget(self.deleteButton)
        self.controlLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # self.controlLayout.addStretch()
        # self.valuesLayout.addStretch()

        self.valuesWidgets = [
            self.intValuesWidget,
            self.doubleValuesWidget,
            self.enumValuesWidget,
        ]
        self.hideAllValueWidgets()
        widgets = [x for x in self.mainLayout.children() if x.__class__.__name__ == 'ObjectSelectLineEdit']

        self.refresh()

    def refresh(self):
        self.controlWidget.itemLabel.setText(self.key)
        self.spaceAttributeWidget.lineEdit.setText(self.cls.spaceData.spaceAttribute[self.key])

    def hideAllValueWidgets(self):
        for widget in self.valuesWidgets:
            widget.setVisible(False)

    def showEnum(self):
        self.hideAllValueWidgets()
        self.enumValuesWidget.setVisible(True)
        self.update()

    def showDouble(self):
        self.hideAllValueWidgets()
        self.doubleValuesWidget.setVisible(True)

    def showInt(self):
        self.hideAllValueWidgets()
        self.intValuesWidget.setVisible(True)

    def valuesEdited(self, key, value):
        self.cls.spaceData.__dict__[key][self.key] = value

    def updateControlName(self, key, value):
        for k in self.cls.spaceData.__dict__.keys():
            if self.key in self.cls.spaceData.__dict__[k].keys():
                self.cls.spaceData.__dict__[k][value] = self.cls.spaceData.__dict__[k].pop(self.key)

    def updateData(self, key, value):
        self.cls.spaceData.__dict__[key][self.key] = value

    def updateAttributeType(self, key, value):
        if value.startswith(self.key):
            value.strip(self.key)
        if '.' not in value:
            value = self.key + '.' + value
        if self.cls.namespace:
            attrName = self.cls.namespace + ':' + value
        else:
            attrName = self.key + '.' + value
        attributeType = cmds.getAttr(attrName, type=True)
        self.attributeTypeFunctions.get(attributeType, self.showDouble)()
        if attributeType == 'enum':
            node, attr = attrName.split('.', 1)
            enumValues = cmds.attributeQuery(attr, node=node, listEnum=True)
            enumList = enumValues[0].split(':')
            globalVal = self.cls.spaceData.spaceGlobalValues.get(self.key, enumList[0])
            localVal = self.cls.spaceData.spaceLocalValues.get(self.key, enumList[-1])
            defaultVal = self.cls.spaceData.spaceDefaultValues.get(self.key, enumList[0])
            self.enumValuesWidget.updateEnums(enumList,
                                              globalVal,
                                              localVal,
                                              defaultVal)
        self.updateData(key, value)

    def pickFK(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 3:
            return cmds.warning('Please select all three fk controls')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.fkUpper.itemLabel.setText(sel[0])
        self.fkMid.itemLabel.setText(sel[1])
        self.fkEnd.itemLabel.setText(sel[2])

    def pickIK(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 2:
            return cmds.warning('Please select the pole vector and ik controls')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.ikPV.itemLabel.setText(sel[0])
        self.ikEnd.itemLabel.setText(sel[1])

    def pickJoints(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 3:
            return cmds.warning('Please select all three joints')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.controlWidget.itemLabel.setText(sel[0])
        self.skeletonMid.itemLabel.setText(sel[1])
        self.skeletonEnd.itemLabel.setText(sel[2])


"""
limb setup - space might be on another control
space data - attribute is full object+attribute

space data setup - select all controls, guess by attribute type (enum) or name
space data names for int based space
popup hotkey for bake whole char to preset, list in popup
presets in sub menu - work on selection
add selected control + highlighted channel as control

"""
