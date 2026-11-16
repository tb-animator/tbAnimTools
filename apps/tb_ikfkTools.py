'''tbAnimation Tools is a toolset for animators

*******************************************************************************

*******************************************************************************
'''
IK_CONTROL = 'ikControl'
key_IKControl = 'IKControl'
key_TopIK = 'TopIKBone'
key_Shoulder = 'ShoulderControl'
key_Upper = 'UpperControl'
key_Mid = 'MidControl'
key_End = 'EndControl'
key_TopPvControl = 'tempTopPVControl'
key_MidPvControl = 'tempMidPvControl'
key_LengthControl = 'tempLengthControl'
key_IkTempControl = 'tempIkTempControl'

# pvControl, ikControl, elbowPvControl,lengthControl]
IK_FKElbowLock_tempControl_keyList = [key_TopPvControl, key_IkTempControl, key_MidPvControl, key_LengthControl]
IK_temp_over_FK_tempControl_keyList = [key_TopPvControl, key_IkTempControl]
IK_IKElbowLock_tempControl_keyList = [key_TopPvControl, key_LengthControl, key_IkTempControl]
IK_temp_over_FK_Control_keyList = [key_Upper, key_Mid, key_End]
IK_FKElbowLock_Control_keyList = [key_Shoulder, key_Upper, key_Mid, key_End]
IK_IKElbowLock_Control_keyList = [key_Shoulder, key_IKControl]
IK_IKElbowLock_assetKeyDict_keyList = [key_Shoulder, key_TopIK, key_IKControl]

"""
TODO -
account for pv being slightly offset from actual pv location, store the vector as well as the distance
if ik is totally extended on match it fails to place  the pole vector correctly


ZERO OUT ATTRIBUTES AND CONTROLS ON IK BAKE!!!!!!

Temporary ik controls ideas
Elbow locker (fk elbow becomes ik handle)
Knee locker
temp ik chain (fingers etc)



"""
import maya
maya.utils.loadStringResourcesForModule(__name__)

from . import *

import socket
import traceback
import pickle
import hashlib
import sys
from difflib import SequenceMatcher, get_close_matches, ndiff

if sys.version_info >= (2, 8):
    from urllib.request import *
    from urllib import request, parse, error
else:
    from urllib2 import *


from copy import deepcopy
from difflib import SequenceMatcher

# python 3 mapping
if sys.version_info[0] >= 3:
    unicode = str

__author__ = 'tom.bailey'

import abc

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
assetCommandName = 'tempIKControlCommand'
tempIkControlScaleOptionVar = 'tempIKControlScaleOption'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('ikfk'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='tbOpenIkFkCreator',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.showUI()']))

        self.addCommand(self.tb_hkey(name='tbToggleIkFk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.toggleSelectedLimbs()']))
        self.addCommand(self.tb_hkey(name='tbToggleIkFkTimeline',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.toggleSelectedLimbsForTimeline()']))
        self.addCommand(self.tb_hkey(name='tbSwitchToFk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.matchFKToCurrentPose()']))
        self.addCommand(self.tb_hkey(name='tbSwitchToIk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.matchIKToCurrentPose()']))
        self.addCommand(self.tb_hkey(name='tbSwitchToIkTip',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.matchIKToCurrentPose(toe=True)']))
        self.addCommand(self.tb_hkey(name='tbBakeToggleIkFk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.toggleBakeSelectedLimbs()']))
        self.addCommand(self.tb_hkey(name='tbBakeToFk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.bakeSelectedLimbsFk()']))
        self.addCommand(self.tb_hkey(name='tbBakeToIk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.bakeSelectedLimbsIk()']))
        self.addCommand(self.tb_hkey(name='tbBakeToIkAndFk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.bakeSelectedLimbsIkFk()']))

        self.addCommand(self.tb_hkey(name='tbTempIK_IK_FKElbowLockSelection',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.temporaryIK_FKElbowLockSelection()']))
        self.addCommand(self.tb_hkey(name='tbTempIK_IK_Selection',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.temporaryIKSelection()']))
        self.addCommand(self.tb_hkey(name='tbTempIK_IK_ElbowLockSelection',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.temporaryIK_IKElbowLockSelection(reset=False)']))
        self.addCommand(self.tb_hkey(name='tbTempIK_IK_ElbowLockSelection_reset',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.temporaryIK_IKElbowLockSelection(reset=True)']))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='right click menu for temp controls',
                                     category=self.category, command=['IkFkTools.assetRmbCommand()'],
                                     help='Do not assign to a hotkey'))
        return self.commandList

    def assignHotkeys(self):
        return


class IkFkTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'IkFkTools'
    hotkeyClass = hotkeys()
    funcs = Functions()
    subfolder = 'ikfkData'

    loadedIkFkData = dict()  # store loaded data per session to avoid accessing the disc all the time

    productID = 'tbIkFkTools'
    version = 1.18

    assetCommandName = 'tempIKControlCommand'

    bakeTimelineModes = ['Full timeline', 'Visible Timeline', 'All Keys']
    bakeTimelineModeOption = 'tbIkFkBakeTimelineMode'
    bakeLayerModes = ['To Override', 'To Override - Extract anim', 'To Base']
    bakeToLayerModeOption = 'tbIkFkBakeToLayerMode'

    helpPath = None
    assetName = 'TempIKControls'

    def __new__(cls):
        if IkFkTools.__instance is None:
            IkFkTools.__instance = object.__new__(cls)

        IkFkTools.__instance.val = cls.toolName
        IkFkTools.__instance.loadData()
        """
        validate = False
        opVar = IkFkTools.__instance.getHash(IkFkTools.__instance.productID, '')
        # currentLicense = get_option_var(opVar, None)
        machineName = IkFkTools.__instance.getHash(socket.gethostname(), '')
        licenseData = IkFkTools.__instance.loadLic()
        if not licenseData:
            validate = True
            cmds.warning('no current license file/data')
        elif len(licenseData) != 4:
            validate = True
            cmds.warning('incorrect license format')
        elif licenseData[3] != machineName:
            validate = True
            cmds.warning('incorrect machine name')
        elif IkFkTools.__instance.getHash(licenseData[0], licenseData[1]) != licenseData[2]:
            validate = True
            cmds.warning('bad license value')

        if validate:
            cmds.warning(IkFkTools.__instance.toolName, 'license not found')
            IkFkTools.__instance.licenseWindow = LicenseWin(parent=IkFkTools.__instance.funcs.getMainWindow(),
                                                            title=IkFkTools.__instance.toolName)
            IkFkTools.__instance.licenseWindow.show()
            IkFkTools.__instance.licenseWindow.ActivateSignal.connect(IkFkTools.__instance.activate)
            if IkFkTools.__instance.licenseWindow.exec_():
                pass
            else:
                return None
        """
        return IkFkTools.__instance


    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        # help folder creation
        baseHelp = os.path.normpath(os.path.join(self.rootDirectory, 'proApps', 'Help'))
        if not os.path.isdir(baseHelp):
            os.mkdir(baseHelp)
        self.helpPath = os.path.normpath(os.path.join(self.rootDirectory, 'proApps', 'Help', self.toolName))
        if not os.path.isdir(self.helpPath):
            os.mkdir(self.helpPath)

        self.assetRmbDict = {
            '_IK_Elbow_Lock': self.rmb__IK_Elbow_Lock,
            '_IK_temp_over_FK': self.rmb__IK_Elbow_Lock,
            '_IK_FK_Elbow_Lock': self.rmb__IK_Elbow_Lock
        }
        self.assetKeyDict = {
            '_IK_Elbow_Lock': [key_Shoulder, key_TopIK, key_IKControl],
            '_IK_temp_over_FK': [key_Upper, key_Mid, key_End],
            '_IK_FK_Elbow_Lock': [key_Shoulder, key_Upper, key_Mid, key_End]

        }
        self.assetTempControlKeyDict = {
            '_IK_Elbow_Lock': IK_IKElbowLock_tempControl_keyList,
            '_IK_temp_over_FK': IK_temp_over_FK_tempControl_keyList,
            '_IK_FK_Elbow_Lock': IK_FKElbowLock_tempControl_keyList
        }
        self.assetControlNameKeyDict = {
            '_IK_Elbow_Lock': IK_IKElbowLock_Control_keyList,
            '_IK_temp_over_FK': IK_temp_over_FK_Control_keyList,
            '_IK_FK_Elbow_Lock': IK_FKElbowLock_Control_keyList
        }

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def initData(self):
        super(IkFkTools, self).initData()
        self.ikfkDir = os.path.normpath(os.path.join(self.dataPath, self.subfolder))
        if not os.path.isdir(self.ikfkDir):
            os.mkdir(self.ikfkDir)

    def optionUI(self):
        super(IkFkTools, self).optionUI()
        versionLabel = QLabel('version :: %s' % self.version)
        versionLabel.setAlignment(Qt.AlignRight)
        sub = subHeader('Baking Timeline Option')
        infoText1 = QLabel('<b>Full Timeline</b> - The uncropped timeline range will be used to bake')
        infoText2 = QLabel('<b>Visible Timeline</b> - The currently visible timeline range will be used')
        infoText3 = QLabel('<b>All Keys</b> - Force the time range to be the the full key range of your controls')

        self.bakeRangeModeWidget = comboBoxWidget(optionVar=self.bakeTimelineModeOption,
                                                  values=self.bakeTimelineModes,
                                                  defaultValue=get_option_var(self.bakeTimelineModeOption,
                                                                                  self.bakeTimelineModes[0]),
                                                  label='Bake mode range')

        infoText4 = QLabel('<b>Bake to layer</b> - An Ik/Fk bake will bake to a new override layer')
        self.bakeLayerModeWidget = comboBoxWidget(optionVar=self.bakeToLayerModeOption,
                                                  values=self.bakeLayerModes,
                                                  defaultValue=get_option_var(self.bakeToLayerModeOption,
                                                                                  self.bakeLayerModes[0]),
                                                  label='Bake Layer Mode')
        self.layout.addWidget(versionLabel)
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
        self.win = IKFK_SetupUI()
        self.win.show()

        if not self.win.rigName:
            self.win.pleaseSelect = raiseInfo('Select a rig control to proceed')
            self.win.pleaseSelect.rejectedSignal.connect(self.pleaseSelectClosed)

    def pleaseSelectClosed(self, *args):
        self.win.pleaseSelect = None

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='IkFk Setup', image='out_ikHandle.png', command='tbOpenIkFkCreator', sourceType='mel',
                      parent=parentMenu)

    def qtMarkingMenu(self, inputNodes):
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection(inputNodes)
        # print (limbsToMatch, namespaceToCharDict)
        if not limbsToMatch.keys():
            return list()
        menuItems = list()
        menuItems.append(MarkingMenuItem(label='FK',
                                         command=lambda: self.matchFKToCurrentPose(),
                                         textColour=None,
                                         variable_data={},
                                         radial=True,
                                         font=boldFont(),
                                         radial_position=None,
                                         bold=False))
        menuItems.append(MarkingMenuItem(label='IK',
                                         command=lambda: self.matchIKToCurrentPose(),
                                         textColour=None,
                                         variable_data={},
                                         radial=True,
                                         font=boldFont(),
                                         radial_position=None,
                                         bold=False))
        return menuItems

    def getCurrentRig(self, sel=None):
        refName = None
        mapName = None
        refState = False
        fname = None
        if sel is None:
            sel = cmds.ls(sl=True)
        namespace = ''
        if not sel:
            return refName, refState, namespace
        if isinstance(sel, list):
            sel = sel[0]
        if not sel:
            return refName, refState, namespace
        refName, refState, namespace = self.funcs.getCurrentRigAndNamespace(sel)

        namespace = self.stripLeadingColon(namespace)

        # print ('here????', namespace)
        return refName, refState, namespace

    def saveRigFileIfNew(self, refname):
        if not refname:
            return
        dataFile = os.path.join(self.ikfkDir, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            ikFkData = IkFkData()
            data = ikFkData.toJson()
            self.saveJsonFile(dataFile, json.loads(data))

    def saveRigFile(self, refname):
        if not refname in self.loadedIkFkData.keys():
            self.saveRigFileIfNew(refname)
        dataFile = os.path.join(self.ikfkDir, refname + '.json')

        data = self.loadedIkFkData[refname].toJson()
        self.saveJsonFile(dataFile, json.loads(data))

    '''
    def getIkFkOffsets(self, namespace, data):
        ikControlAttr = self.getControl(namespace, data.ikAttr)
        cmds.setAttr(ikControlAttr, data.fkValue)
        for j, c in zip(data.jointKeys, data.fkKeys):
            control = self.getControl(namespace, data.__dict__[c])
            joint = self.getControl(namespace, data.__dict__[j])
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            resultMatrix = controlMMatrix * jointMMatrix.inverse()

            data.fkControlOffsets[c] = [x for x in resultMatrix]
        cmds.setAttr(ikControlAttr, data.ikValue)
    '''

    def getControl(self, namespace, name, optional=False):
        # print ('getControl',  namespace, name)
        c = name.split('.')[0]
        obj = namespace + ':' + c
        if not cmds.objExists(obj):
            if not optional:
                return raiseError('Control not found (%s)' % str(obj))
            return None
        if namespace:
            return namespace + ':' + name
        return name

    def getControlForAttr(self, namespace, name, optional=False):
        c, attr = name.split('.')
        obj = namespace + ':' + c
        if not cmds.objExists(obj):
            if not optional:
                return raiseError('Control not found (%s)' % str(obj))
        if namespace:
            name = namespace + ':' + name
        if not cmds.attributeQuery(attr, node=name, exists=True):
            if not optional:
                return raiseError('Attribute not found (%s)' % str(obj))
        return name

    def loadIkFkData(self, refName):
        IkFkTools().saveRigFileIfNew(refName)
        ikFkData = IkFkData()
        ikFkData.fromJson(os.path.join(IkFkTools().ikfkDir, refName + '.json'))
        return ikFkData

    def splitSelectionToCharacters(self, sel):
        """
        Returns a dictionary for all characters found in the selection, namespace as key, controls as items
        :param sel:
        :return:
        """
        if not sel:
            return

        characters = dict()
        for s in sel:
            refName, refstate, namespace = self.getCurrentRig(s)
            # print ('new refname', refName)
            # add the dictionary for a new character
            if not refName in characters:
                characters[refName] = dict()
            # add the namespace
            if namespace not in characters[refName].keys():
                characters[refName][namespace] = list()
            characters[refName][namespace].append(s)

        return characters

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        for refname, namespaces in characters.items():
            self.loadDataCharacter(refname)
            for namespace in namespaces:
                namespaceToCharDict[namespace] = refname
        return namespaceToCharDict

    def loadDataCharacter(self, refName):
        if refName not in self.loadedIkFkData.keys():
            ikFkData = self.loadIkFkData(refName)
            self.loadedIkFkData[refName] = ikFkData

    def getLimbsToMatchFromSelection(self, sel=None):
        if sel is None:
            sel = cmds.ls(sl=True)
        if not sel:
            return

        characters = self.splitSelectionToCharacters(sel)

        namespaceToCharDict = self.loadDataForCharacters(characters)
        limbsToMatch = {c: list() for c in characters.keys()}

        # get the limbs selected
        for char, namespaces in characters.items():
            # print ('char', char, namespaces)
            for ns, controls in namespaces.items():
                # print ('ns', ns, controls)
                for control in controls:
                    control = self.removeNamespace(control, ns)
                    # print ('control', control)
                    for key, limb in self.loadedIkFkData[char].limbs.items():
                        if limb.controlInData(control):
                            if key in limbsToMatch[char]:
                                continue
                            limbsToMatch[char].append([ns, key])

        return limbsToMatch, namespaceToCharDict

    def removeNamespace(self, control, ns):
        # print (control, ns)
        if ns != '':
            # print ('namespace not in control', control, ns)
            control = control.split(ns, 1)[-1]
            # print ('finalControl', control)
        control = self.stripLeadingColon(control)
        return control

    def matchFKToCurrentPose(self):
        endFkControls = list()
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        for refName, limbs in limbsToMatch.items():
            # print ('refName', refName, limbs)
            for ns, limb in limbs:
                self.loadedIkFkData[refName].limbs[limb].matchToFK(ns)
                self.loadedIkFkData[refName].limbs[limb].getBestControlByState(ns)

    def matchIKToCurrentPose(self, toe=False):
        ikControls = list()
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        # print ('limbsToMatch', limbsToMatch)
        # print ('namespaceToCharDict', namespaceToCharDict)
        for refName, limbs in limbsToMatch.items():
            # print ('refName', refName, limbs)
            for ns, limb in limbs:
                # print ('ns', ns, limb)
                self.loadedIkFkData[refName].limbs[limb].matchToIKMain(ns, toe=toe)
                self.loadedIkFkData[refName].limbs[limb].getBestControlByState(ns)

    def matchToCurrentPose(self, ik=False, timeline=False, toe=False):
        # get the limb dictionary from selection
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        timeDict = dict()
        ikValueDict = dict()
        allControls = list()
        allFilteredControls = list()
        # TODO - skip key times when fully weighted to ik if matching to fk
        for refName, limbs in limbsToMatch.items():
            # print ('refName', refName, limbs)
            for ns, limb in limbs:
                limbData = self.loadedIkFkData[refName].limbs[limb]
                if ik:
                    keys = limbData.fkKeys
                    filterKeys = limbData.ikKeys
                else:
                    keys = limbData.ikKeys
                    filterKeys = limbData.fkKeys

                controls = [self.getControl(ns, limbData.__dict__.get(key)) for key in keys]
                filterControls = [self.getControl(ns, limbData.__dict__.get(key)) for key in filterKeys]
                # get combined control key times for ik
                timeDict[ns + '_' + limb] = self.getMatchRange(controls, ikAttr=limbData.getIkAttr(ns),
                                                               timeline=timeline)
                ikValueDict[ns + '_' + limb] = limbData.getIkValuesForTimeList(ns, timeDict[ns + '_' + limb])
                allControls.extend(controls)
                allControls.extend(filterControls)
                allFilteredControls.extend(filterControls)

        combinedTimeList = sorted({x for v in list(timeDict.values()) for x in v})

        if len(combinedTimeList) > 1:
            with self.funcs.suspendUpdate():
                # iterate over key times, matching appropriately
                for t in combinedTimeList:
                    cmds.currentTime(t)
                    for refName, limbs in limbsToMatch.items():
                        limbData = self.loadedIkFkData[refName].limbs[limb]
                        for ns, limb in limbs:
                            if t not in timeDict.get(ns + '_' + limb, list()):
                                continue

                            timeIndex = timeDict.get(ns + '_' + limb, list()).index(t)
                            limbData.setIkValue(ns, ikValueDict[ns + '_' + limb][
                                timeIndex])
                            cmds.refresh()
                            if ik:
                                if toe:
                                    # matching to toe will offset using the heel lift control (optional)
                                    limbData.matchToIKMain(ns, toe=True)
                                else:
                                    limbData.matchToIKMain(ns)
                            else:
                                limbData.matchToFK(ns)
                for control in filterControls:
                    cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')
        else:
            for refName, limbs in limbsToMatch.items():
                for ns, limb in limbs:
                    limbData = self.loadedIkFkData[refName].limbs[limb]
                    if ik:
                        limbData.matchToIKMain(ns)
                    else:
                        limbData.matchToFK(ns)

    def getMatchRange(self, sel, ikAttr=str, timeline=False):
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

    def toggleSelectedLimbs(self, timeline=False):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        state = False
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection(sel=[sel[-1]])
        if not limbsToMatch:
            return cmds.warning('No limbs to match for selection', sel)
        for refName, limbs in limbsToMatch.items():
            for ns, limb in limbs:
                state = self.loadedIkFkData[refName].limbs[limb].getCurrentState(ns)
                self.loadedIkFkData[refName].limbs[limb].getBestControlByState(ns)
        if state:
            self.matchToCurrentPose(ik=False, timeline=timeline)
        else:
            self.matchToCurrentPose(ik=True, timeline=timeline)

    def toggleSelectedLimbsForTimeline(self):
        self.toggleSelectedLimbs(timeline=True)

    def bakeSelectedLimbsIk(self):
        self.bakeSelectedLimbsWrapper(ik=True, fk=False)

    def bakeSelectedLimbsFk(self):
        self.bakeSelectedLimbsWrapper(fk=True, ik=False)

    def bakeSelectedLimbsIkFk(self):
        self.bakeSelectedLimbsWrapper(ik=True, fk=True)

    def toggleBakeSelectedLimbs(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return

        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection(sel=[sel[-1]])
        for refName, limbs in limbsToMatch.items():
            # print ('refName', refName, limbs)
            for ns, limb in limbs:
                state = self.loadedIkFkData[refName].limbs[limb].getCurrentState(ns)
        if state:
            self.bakeSelectedLimbsWrapper(ik=False, fk=True)
        else:
            self.bakeSelectedLimbsWrapper(ik=True, fk=False)

    def bakeSelectedLimbsWrapper(self, ik=True, fk=True):
        cmds.undoInfo(openChunk=True)
        sel = cmds.ls(sl=True)
        if not sel:
            return
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        for key, limbs in limbsToMatch.items():
            if not limbs:
                return cmds.warning('No valid limbs found')

        duration = None
        self.funcs.suspendSkinning()

        try:
            duration = self.bakeSelectedLimbs(ik=ik, fk=fk, limbsToMatch=limbsToMatch,
                                              namespaceToCharDict=namespaceToCharDict)
        finally:
            self.funcs.resumeSkinning()
            cmds.cycleCheck(evaluation=True)
            cmds.refresh()
            cmds.currentTime(cmds.currentTime(query=True))
            cmds.undoInfo(closeChunk=True)

        if duration:
            durationStr = ("{t}s".format(t=duration))
            self.funcs.infoMessage(position="botRight",
                                   prefix=" - IkFk Bake time - ",
                                   message=durationStr,
                                   fadeInTime=10.0,
                                   fadeStayTime=60.0,
                                   fadeOutTime=10.0,
                                   fade=False)

    def bakeSelectedLimbs(self, ik=True, fk=True, limbsToMatch=dict(), namespaceToCharDict=dict()):
        """
        Bakes all selected limbs to either ik or fk
        :param ik:
        :return:
        """

        duration = cmds.timerX()
        resultLayer = None
        bakeOption = get_option_var(self.bakeToLayerModeOption, self.bakeLayerModes[0])
        initialTime = cmds.currentTime(query=True)

        timeRange = self.funcs.getTimelineRange()
        allTempNodesDict = dict()
        allTempNodesList = list()
        allTempConstraints = list()
        allAnimControls = list()
        allIkAttrs = list()
        allZeroAttrs = list()
        allZeroControls = list()

        cmds.currentTime(timeRange[0])
        for refName, limbs in limbsToMatch.items():
            for ns, limb in limbs:
                if ns not in allTempNodesDict.keys():
                    allTempNodesDict[ns] = dict()

        for refName, limbs in limbsToMatch.items():
            for ns, limb in limbs:
                tempNodes, constraints = self.loadedIkFkData[refName].limbs[limb].preBake(ns, ik, fk)
                allTempNodesDict[ns][limb] = tempNodes
                allTempNodesList.extend(tempNodes.values())
                allTempConstraints.extend(constraints)
                allIkAttrs.append(self.loadedIkFkData[refName].limbs[limb].getIkAttr(ns))
                allZeroAttrs.extend(self.loadedIkFkData[refName].limbs[limb].getZeroAttrs(ns))
                allZeroControls.extend(self.loadedIkFkData[refName].limbs[limb].getZeroControls(ns))
        self.bakeTempControls(allTempNodesList, timeRange[0],
                              timeRange[1])  # bake the temporary controls to the base layer
        cmds.delete(allTempConstraints)
        # controlPreConstraints =
        allPostTempConstraints = list()

        for refName, limbs in limbsToMatch.items():
            for ns, limb in limbs:
                limbData = self.loadedIkFkData[refName].limbs[limb]
                controls, constraints = limbData.postBake(ns, ik, fk, allTempNodesDict[ns][limb])
                allAnimControls.extend(controls)
                allPostTempConstraints.extend(constraints)

        if bakeOption != self.bakeLayerModes[-1]:
            resultLayer = self.createResultLayer(ik=ik)
            self.addAttrsToResultLayer(allIkAttrs, resultLayer)
            self.addAttrsToResultLayer(allZeroAttrs, resultLayer)
            self.addZeroControlsToResultLayer(allZeroControls, resultLayer)

        for refName, limbs in limbsToMatch.items():
            # print ('refName', refName, limbs)
            for ns, limb in limbs:
                # self.loadedIkFkData[refName].limbs[limb].muteIkAttr(ns, False)
                self.loadedIkFkData[refName].limbs[limb].setToIk(ns)

                ikAttr = self.loadedIkFkData[refName].limbs[limb].getIkAttr(ns)
                if ik:
                    ikValue = self.loadedIkFkData[refName].limbs[limb].ikValue
                    print('IK BAKE, IK VALUE', ikValue)
                else:
                    ikValue = self.loadedIkFkData[refName].limbs[limb].fkValue
                    print('FK BAKE, IK VALUE', ikValue)
                cmds.setKeyframe(ikAttr, value=ikValue, animLayer=resultLayer, time=(timeRange[0], timeRange[-1]))
                # self.loadedIkFkData[refName].limbs[limb].muteIkAttr(ns, True)

        # collect all attributes and bake explicitly
        bakeAttributes = self.getAllAnimatedChannels(allAnimControls)
        bakeAttributes.extend(self.getAllAnimatedChannels(allZeroControls))
        '''
        for a in bakeAttributes:
            print (a)
        '''
        bakeAttributes.extend(allIkAttrs)
        bakeAttributes.extend(allZeroAttrs)

        self.bakeAnimControls(allAnimControls, timeRange[0], timeRange[1], resultLayer, bakeOption)
        '''
        for ns, limb in limbsToMatch.items():
            for l in limb:
                self.loadedIkFkData[refName].limbs[limb].muteIkAttr(ns, False)
        '''
        for control in allAnimControls:
            try:
                cmds.filterCurve(control + '.rotateX', control + '.rotateY', control + '.rotateZ')
            except:
                continue

        cmds.delete(allPostTempConstraints)
        cmds.delete(allTempNodesList)

        cmds.currentTime(initialTime)
        cmds.refresh()
        durationEnd = cmds.timerX()

        return (durationEnd - duration)

    def getAllAnimatedChannels(self, controls):
        allAttributes = list()
        for c in controls:
            attributes = cmds.listAttr(c, keyable=True, settable=True)
            allAttributes.extend([c + '.' + a for a in attributes])
        return allAttributes

    def createLayer(self, override=False, suffixStr=None):
        # TODO - remove this later, or tie it into the override colours
        if suffixStr is None:
            suffixStr = {True: 'Override', False: 'Additive'}[override]

        # colour = {True: self.overrideLayerColour, False: self.additiveLayerColour}

        newAnimLayer = cmds.animLayer(suffixStr,
                                      override=override)
        cmds.setAttr(newAnimLayer + '.ghostColor', self.allTools.tools['BakeTools'].overrideLayerColour)
        self.allTools.tools['BakeTools'].deselect_layers()
        self.funcs.select_layer(newAnimLayer)

        cmds.setAttr(newAnimLayer + '.scaleAccumulationMode', 0)
        return newAnimLayer

    def createResultLayer(self, ik=False):
        suffix = {True: 'Ikbake', False: 'FkBake'}[ik]
        return str(self.createLayer(override=True, suffixStr=suffix))

    def addAttrsToResultLayer(self, attrs, resultLayer):
        cmds.animLayer(resultLayer, edit=True, attribute=attrs)

    def addZeroControlsToResultLayer(self, controls, resultLayer):
        with self.funcs.keepSelection():
            cmds.select(controls)
            cmds.animLayer(resultLayer,
                         edit=True,
                         addSelectedObjects=True)

    def bakeAnimControls(self, controls, startTime, endTime, resultLayer, bakeOption):
        """
                Bakes the collected temp controls from the preBake functions
                :param controls:
                :param startTime:
                :param endTime:
                :return:
                """
        duration = cmds.timerX()
        rootLayer = cmds.animLayer(q=True, root=True)
        if rootLayer is not None:
            cmds.animLayer(rootLayer, edit=True, lock=False)
        # with self.funcs.suspendUpdate():
        destinationLayer = {True: rootLayer, False: resultLayer}[bakeOption == self.bakeLayerModes[2]]
        removeBakedAnimFromLayer = bakeOption != self.bakeLayerModes[0]
        '''
        print ('[bakeOption == self.bakeLayerModes[2]]', bakeOption == self.bakeLayerModes[2])
        print ('destinationLayer', destinationLayer)
        print ('removeBakedAnimFromLayer', removeBakedAnimFromLayer)
        print ('bakeOnOverrideLayer', destinationLayer is not None)
        '''
        cmds.cycleCheck(evaluation=False)
        with self.funcs.suspendUpdate():
            try:
                keyRange = self.funcs.getBestTimelineRangeForBake()
                if destinationLayer is None:
                    cmds.bakeResults(controls,
                                     time=(keyRange[0], keyRange[-1]),
                                     simulation=True,
                                     sampleBy=1,
                                     oversamplingRate=1,
                                     disableImplicitControl=False,
                                     preserveOutsideKeys=False,
                                     sparseAnimCurveBake=False,
                                     removeBakedAttributeFromLayer=True,
                                     removeBakedAnimFromLayer=True,
                                     bakeOnOverrideLayer=False,
                                     minimizeRotation=False,
                                     controlPoints=False,
                                     shape=False)
                else:
                    cmds.bakeResults(controls,
                                     time=(keyRange[0], keyRange[-1]),
                                     destinationLayer=destinationLayer,
                                     simulation=True,
                                     sampleBy=1,
                                     oversamplingRate=1,
                                     disableImplicitControl=False,
                                     preserveOutsideKeys=False,
                                     sparseAnimCurveBake=False,
                                     removeBakedAttributeFromLayer=removeBakedAnimFromLayer,
                                     removeBakedAnimFromLayer=removeBakedAnimFromLayer,
                                     bakeOnOverrideLayer=True,
                                     minimizeRotation=False,
                                     controlPoints=False,
                                     shape=False)
            finally:
                cmds.cycleCheck(evaluation=True)
        duration -= cmds.timerX()
        # cmds.warning('bake pass 2 took {0} seconds'.format(str(-duration)))

    def bakeTempControls(self, controls, startTime, endTime):
        """
        Bakes the collected temp controls from the preBake functions
        :param controls:
        :param startTime:
        :param endTime:
        :return:
        """
        duration = cmds.timerX()
        # with self.funcs.suspendUpdate():
        cmds.cycleCheck(evaluation=False)
        keyRange = self.funcs.getBestTimelineRangeForBake()
        with self.funcs.suspendUpdate():
            cmds.bakeResults(controls,
                             time=(keyRange[0], keyRange[-1]),
                             simulation=True,
                             sampleBy=1,
                             oversamplingRate=1,
                             disableImplicitControl=True
                             )
            cmds.cycleCheck(evaluation=True)
        duration -= cmds.timerX()
        # cmds.warning('bake pass 1 took {0} seconds'.format(str(-duration)))

    def saveTempIkData(self, objectList, keyList, refName, assetTag):
        # save the lock data, if there's not an entry for the opposite side
        # add that as well using the mirror values from the character data
        CharacterTool = IkFkTools().allTools.tools['CharacterTool']
        MirrorTools = IkFkTools().allTools.tools['MirrorTools']
        CharacterTool.getAllCharacters()
        # self.currentNamespace
        self.loadDataCharacter(refName)

        keyList = self.assetKeyDict.get(assetTag, list())
        tempControlKeyList = self.assetTempControlKeyDict.get(assetTag, list())

        if not assetTag + 'Scales' in self.loadedIkFkData[refName].__dict__.keys():
            self.loadedIkFkData[refName][assetTag + 'Scales'] = dict()
        if not assetTag in self.loadedIkFkData[refName].__dict__.keys():
            self.loadedIkFkData[refName][assetTag] = dict()

        self.loadedIkFkData[refName][assetTag][objectList[-1]] = {key: value for key, value in
                                                                  zip(keyList, objectList)}

        self.loadedIkFkData[refName][assetTag + 'Scales'][objectList[-1]] = {key: [1, 1, 1] for key, c in
                                                                             zip(tempControlKeyList,
                                                                                 [1, 1, 1])}
        if refName in CharacterTool.allCharacters.keys():
            mirrorControls = [MirrorTools.getMirrorForControlFromCharacter(CharacterTool.allCharacters[refName], s) for
                              s in objectList]
            if all([cmds.objExists(self.currentNamespace + ':' + s) for s in mirrorControls]):
                self.loadedIkFkData[refName][assetTag][mirrorControls[-1]] = {key: value for key, value in
                                                                              zip(keyList, mirrorControls)}
                self.loadedIkFkData[refName][assetTag + 'Scales'][mirrorControls[-1]] = {key: [1, 1, 1] for key, c in
                                                                                         zip(
                                                                                             tempControlKeyList,
                                                                                             [1, 1, 1])}
        self.saveRigFile(refName)

    def temporaryIKSelection(self, debug=False):
        sel = cmds.ls(sl=True)
        if not len(sel) == 3:
            return raiseInfo('Please select the following 3 controls\n'
                             'FK Upper Arm\n'
                             'FK Elbow\n'
                             'FK Wrist', title='No selection')

        assetName = '_IK_temp_over_FK'
        assetTag = str(assetName)
        keyList = self.assetKeyDict.get(assetTag, list())
        baseParent = cmds.listRelatives(sel[0], parent=True)[0]
        base = sel[0]
        mid = sel[1]
        end = sel[2]
        allControls = [base, mid, end]
        ns = self.funcs.namespace(base)

        asset = str(end) + self.assetName

        if not cmds.objExists(asset):
            asset = self.createAsset(asset, imageName=None, assetTag=assetTag)
        else:
            asset = assetName
        # get the current rig and namespace
        refName, refstate, namespace = self.getCurrentRig(sel[0])
        self.loadDataCharacter(refName)
        ikData = self.loadedIkFkData[refName]
        strippedSelection = [self.removeNamespace(s, namespace) for s in sel]
        # check current controls to see if they are defined
        # print ('strippedSelection', strippedSelection)
        currentData, dataKey = ikData.findLockIKLimb(strippedSelection, assetTag + 'Scales')
        # print ('dataKey', dataKey)
        rootNode = self.funcs.tempNull(name=base, suffix='ikBase')

        controlScales = self.loadedIkFkData[refName].__dict__.get(assetTag + 'Scales', dict()).get(
            strippedSelection[-1], dict())
        # print ('controlScales', controlScales)
        # print ('tag', self.assetTempControlKeyDict[assetTag])
        pvControl = self.funcs.tempControl(name=mid,
                                           suffix='PV',
                                           # scale=get_option_var(optionVar, 1),
                                           drawType='cross')
        cmds.setAttr(pvControl + '.scale', *controlScales.get(self.assetTempControlKeyDict[assetTag][0], [1, 1, 1]), type='double3')
        ikControl = self.funcs.tempControl(name=end,
                                           suffix='IK',
                                           # scale=get_option_var(optionVar, 1),
                                           drawType='orb')
        cmds.setAttr(ikControl + '.scale', controlScales.get(self.assetTempControlKeyDict[assetTag][1], [1, 1, 1]), type='double3')

        self.funcs.getSetColour(mid, pvControl, brightnessOffset=0.05)
        self.funcs.getSetColour(end, ikControl, brightnessOffset=0.05)

        # self.funcs.boldControl(mid, pvControl, offset=1.0)
        # self.funcs.boldControl(end, ikControl, offset=1.0)

        cmds.delete(cmds.parentConstraint(base, rootNode))
        cmds.delete(cmds.parentConstraint(mid, pvControl))
        cmds.delete(cmds.parentConstraint(end, ikControl))

        joints = list()
        cmds.bakeResults(clear=True)
        for index, s in enumerate([base, mid, end]):
            aimConstraint = None
            joint = cmds.joint()
            constraint = cmds.pointConstraint(s, joint)[0]
            cmds.parent(joint, rootNode)
            joints.append(joint)
            cmds.setAttr(joint + '.drawStyle', 2)
            if joints[max(index - 1, 0)] != joint:
                cmds.parent(joint, joints[index - 1])
                if index < 2:
                    aimConstraint = cmds.aimConstraint(end, joint, aimVector=[1, 0, 0])[0]
                cmds.joint(joint, edit=True, spa=True, ch=True)
            else:
                cmds.parent(joint, rootNode)
            cmds.delete(constraint)
            if aimConstraint: cmds.delete(aimConstraint)

            cmds.setAttr(joint + '.jointOrient', *cmds.getAttr(joint + '.rotate'))
            cmds.setAttr(joint + '.rotate', 0, 0, 0, type='double3')
            cmds.setAttr(joint + '.rotate', 0, 0, 0, type='double3')
            cmds.joint(joint, edit=True, spa=True, ch=True)

        ikHandle, effector = cmds.ikHandle(sj=joints[0], ee=joints[-1], p=2, w=1.0)
        cmds.setAttr(ikHandle + '.snapEnable', 1)
        cmds.setAttr(ikHandle + '.stickiness', 1)
        pvPosition = self.calculatePVPosition(joints)
        cmds.setAttr(pvControl + '.translate', pvPosition[0], pvPosition[1], pvPosition[2])
        pvConstraint = cmds.poleVectorConstraint(pvControl, ikHandle)
        cmds.parent(ikHandle, ikControl)

        # cosntrain root to parent
        cmds.parentConstraint(baseParent, rootNode, maintainOffset=True)

        # constrain temp controls to anim controls
        constraints = list()
        constraints.append(cmds.parentConstraint(base, pvControl, maintainOffset=True)[0])
        constraints.append(cmds.parentConstraint(end, ikControl, maintainOffset=True)[0])

        # bake pass
        currentTime = cmds.currentTime(query=True)
        bakeTools = self.allTools.tools['BakeTools']
        filteredTargets = [pvControl, ikControl]
        bakeRange = self.funcs.getBakeRange([base, mid, end])

        cmds.cycleCheck(evaluation=False)
        bakeTools.quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                            deleteConstraints=True)
        cmds.cycleCheck(evaluation=True)
        cmds.currentTime(currentTime)
        for c in constraints:
            if cmds.objExists(c): cmds.delete(c)

        self.funcs.eulerFilterControl(filteredTargets)

        self.funcs.safeParentConstraint(joints[0], base,
                                        orientOnly=True,
                                        maintainOffset=True)

        self.funcs.safeParentConstraint(joints[1], mid,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(ikControl, end,
                                        orientOnly=False,
                                        maintainOffset=True)
        '''
        self.funcs.safeParentConstraint(joints[2], end,
                                        orientOnly=False,
                                        maintainOffset=False)
        '''

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[pvControl, ikControl])
        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[rootNode])

        if not debug:
            cmds.setAttr(rootNode + '.hiddenInOutliner', True)
        # tag the anim controls
        # print ('self.assetControlNameKeyDict[assetTag]', self.assetControlNameKeyDict[assetTag])
        # print ('self.assetTempControlKeyDict[assetTag]', self.assetTempControlKeyDict[assetTag])
        for obj, key in zip(allControls, self.assetControlNameKeyDict[assetTag]):
            # print ('key', key)
            self.funcs.tagControl(asset, obj, key.replace(" ", ""))
        # tag the temp controls
        tempControlList = [pvControl, ikControl]
        self.funcs.tagControlList(asset, tempControlList, prefix='',
                                  keyList=self.assetTempControlKeyDict[assetTag])

    def temporaryIK_FKElbowLockSelection(self, debug=False):
        assetName = '_IK_FK_Elbow_Lock'
        assetTag = str(assetName)
        keyList = self.assetKeyDict.get(assetTag, list())
        tempControlKeyList = self.assetTempControlKeyDict.get(assetTag, list())

        sel = cmds.ls(sl=True)
        if not len(sel) == 4:
            return raiseInfo('Please select the following 4 controls\n'
                             'FK Shoulder\n'
                             'FK Upper Arm\n'
                             'FK Elbow\n'
                             'FK Wrist', title='No selection')

        shoulder = sel[0]
        upper = sel[1]
        elbow = sel[2]
        wrist = sel[3]
        allControls = [shoulder, upper, elbow, wrist]
        shoulderParent = cmds.listRelatives(shoulder, parent=True)[0]

        # get the current rig and namespace
        refName, refstate, namespace = self.getCurrentRig(sel[0])
        self.loadDataCharacter(refName)

        assetName = namespace + str(wrist) + assetName
        if not cmds.objExists(assetName):
            asset = self.createAsset(assetName, imageName=None, assetTag=assetTag)
        else:
            asset = assetName

        rootNode = self.funcs.tempNull(name=shoulder, suffix='ikBase')
        pvControl = self.funcs.tempControl(name=upper,
                                           suffix='PV',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                           drawType='orb')
        ikControl = self.funcs.tempControl(name=wrist,
                                           suffix='IK',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1) * 0.5,
                                           drawType='orb')
        elbowPvControl = self.funcs.tempControl(name=elbow,
                                                suffix='PV',
                                                scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                                drawType='cross')
        lengthControl = self.funcs.tempControl(name=elbow,
                                               suffix='Length',
                                               scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                               drawType='pin')
        lengthParent = self.funcs.tempNull(name=elbow, suffix='Length_grp')
        cmds.parent(lengthControl, lengthParent)

        self.funcs.boldControl(upper, pvControl, offset=1.0)
        self.funcs.boldControl(wrist, ikControl, offset=1.0)
        self.funcs.boldControl(elbow, elbowPvControl, offset=1.0)
        self.funcs.boldControl(elbow, lengthControl, offset=1.0)

        self.funcs.getSetColour(upper, pvControl, brightnessOffset=0.05)
        self.funcs.getSetColour(wrist, ikControl, brightnessOffset=0.05)
        self.funcs.getSetColour(elbow, elbowPvControl, brightnessOffset=0.05)
        self.funcs.getSetColour(elbow, lengthControl, brightnessOffset=0.05)

        cmds.delete(cmds.parentConstraint(shoulder, rootNode))
        cmds.delete(cmds.parentConstraint(upper, pvControl))
        cmds.delete(cmds.parentConstraint(wrist, ikControl))

        lockedJoints = list()
        # lock joints
        cmds.bakeResults(clear=True)
        for index, s in enumerate([shoulder, upper, wrist]):
            aimConstraint = None
            # cmds.bakeResults(s)
            # print ('s', s)

            joint = cmds.joint(name=str(s) + '_locked')
            constraint = cmds.pointConstraint(s, joint)[0]
            cmds.parent(joint, rootNode)

            cmds.setAttr(joint + '.scale', 1, 1, 1, type='double3')
            lockedJoints.append(joint)

            if lockedJoints[max(index - 1, 0)] != joint:
                cmds.parent(joint, lockedJoints[index - 1], relative=True)
                if index < 2:
                    aimConstraint = cmds.aimConstraint(wrist, joint, aimVector=[1, 0, 0])[0]
                cmds.joint(joint, edit=True, spa=True, ch=True)
            else:
                cmds.parent(joint, rootNode, relative=True)
            cmds.delete(constraint)
            if aimConstraint: cmds.delete(aimConstraint)

            cmds.setAttr(joint + '.jointOrient', cmds.getAttr(joint + '.rotate'))
            cmds.setAttr(joint + '.rotate', 0, 0, 0, type='double3')
            cmds.setAttr(joint + '.rotate', 0, 0, 0, type='double3')
            cmds.joint(joint, edit=True, spa=True, ch=True)

        cmds.parent(lengthParent, lockedJoints[1])
        cmds.delete(cmds.parentConstraint(lockedJoints[1], lengthParent))

        # parent the length control to the locked joints

        cmds.delete(cmds.pointConstraint(lockedJoints[2], lengthParent))
        cmds.delete(cmds.pointConstraint(lockedJoints[1], lengthControl))

        cmds.parentConstraint(shoulderParent, rootNode, skipRotate=('x', 'y', 'z'), maintainOffset=True)
        twoBoneJoints = list()
        # 2 bone ik joints
        for index, s in enumerate([upper, elbow, wrist]):
            cmds.bakeResults(s)
            joint = cmds.joint()
            twoBoneJoints.append(joint)
            if twoBoneJoints[max(index - 1, 0)] != joint:
                cmds.parent(joint, twoBoneJoints[index - 1])
                cmds.joint(joint, edit=True, spa=True, ch=True)
            else:
                cmds.parent(joint, rootNode)

        pvPosition = self.calculateShoulderPvPosition(lockedJoints)
        locked_ikHandle, locked_effector = cmds.ikHandle(sj=lockedJoints[0], ee=lockedJoints[-1], p=2, w=1.0)
        cmds.setAttr(locked_ikHandle + '.snapEnable', 1)
        cmds.setAttr(locked_ikHandle + '.stickiness', 1)
        # shoulder pv position is less smart compared to elbow pv position
        cmds.setAttr(pvControl + '.translate', pvPosition[0], pvPosition[1], pvPosition[2])

        pvConstraint = cmds.poleVectorConstraint(pvControl, locked_ikHandle)
        cmds.parent(locked_ikHandle, ikControl)

        elbow_ikHandle, elbow_effector = cmds.ikHandle(sj=twoBoneJoints[0], ee=twoBoneJoints[-1], p=2, w=1.0)
        cmds.setAttr(elbow_ikHandle + '.snapEnable', 1)
        cmds.setAttr(elbow_ikHandle + '.stickiness', 1)
        pvPosition = self.calculatePVPosition(twoBoneJoints)
        cmds.setAttr(elbowPvControl + '.translate', pvPosition[0], pvPosition[1], pvPosition[2])

        pvConstraint = cmds.poleVectorConstraint(elbowPvControl, elbow_ikHandle)

        cmds.parent(elbow_ikHandle, lockedJoints[2])
        cmds.parent(twoBoneJoints[0], lockedJoints[1])
        constraints = list()

        constraints.append(cmds.parentConstraint(shoulder, pvControl, maintainOffset=True)[0])

        constraints.append(cmds.parentConstraint(elbow, elbowPvControl, maintainOffset=True)[0])
        constraints.append(cmds.parentConstraint(upper, lengthControl, maintainOffset=True)[0])
        constraints.append(cmds.parentConstraint(wrist, ikControl)[0])
        tempConstraint = cmds.parentConstraint(wrist, lengthParent, maintainOffset=True, skipRotate=('x', 'y', 'z'))[0]
        distanceNode = cmds.createNode('distanceBetween')
        cmds.connectAttr(upper + '.worldMatrix', distanceNode + '.inMatrix1')
        cmds.connectAttr(wrist + '.worldMatrix', distanceNode + '.inMatrix2')
        cmds.connectAttr(distanceNode + '.distance', lockedJoints[2].translateX)

        """
        Bake
        """

        bakeTools = self.allTools.tools['BakeTools']
        filteredTargets = [pvControl,
                           elbowPvControl,
                           lengthControl,
                           ikControl]
        bakeRange = self.funcs.getBakeRange([wrist, upper, elbow, elbow])
        cmds.cycleCheck(evaluation=False)
        bakeTools.quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                            deleteConstraints=True)
        cmds.cycleCheck(evaluation=True)

        self.funcs.eulerFilterControl(filteredTargets)

        cmds.delete(distanceNode)
        cmds.delete(tempConstraint)

        cmds.parent(lengthParent, lockedJoints[1])
        cmds.setAttr(lengthParent + '.rotate', 0, 0, 0, type='double3')
        # connect the length bone to the control
        reverseNode = cmds.createNode('multiplyDivide')
        cmds.setAttr(reverseNode + '.input1X', -1)
        cmds.connectAttr(lengthControl.translateX, reverseNode.input2X)
        cmds.connectAttr(reverseNode.outputX, lengthParent.translateX)
        cmds.connectAttr(reverseNode.outputX, lockedJoints[2].translateX, force=True)

        '''
        Constrain original controls up
        '''

        self.funcs.safeParentConstraint(lockedJoints[0], shoulder,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(twoBoneJoints[0], upper,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(twoBoneJoints[1], elbow,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(ikControl, wrist,
                                        orientOnly=True,
                                        maintainOffset=True)

        cmds.cutKey(lengthControl,
                    clear=True,
                    at=["ty", "tz", "rx", "ry", "rz"])
        cmds.setAttr(lengthParent + '.ty', 0)
        cmds.setAttr(lengthParent + '.tz', 0)
        cmds.setAttr(lengthParent + '.rx', 0)
        cmds.setAttr(lengthParent + '.ry', 0)
        cmds.setAttr(lengthParent + '.rz', 0)
        cmds.setAttr(lengthControl + '.ty', 0, lock=True)
        cmds.setAttr(lengthControl + '.tz', 0, lock=True)
        cmds.setAttr(lengthControl + '.rx', 0, lock=True)
        cmds.setAttr(lengthControl + '.ry', 0, lock=True)
        cmds.setAttr(lengthControl + '.rz', 0, lock=True)

        # TODO - make it 1d, or have wobbles
        '''
        self.funcs.safeParentConstraint(joints[2], elbow,
                                        orientOnly=False,
                                        maintainOffset=False)
        '''
        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[pvControl, ikControl, lengthControl, elbowPvControl])

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[rootNode])
        if not debug:
            cmds.setAttr(rootNode + '.hiddenInOutliner', True)
        # tag the anim controls
        for obj, key in zip(allControls, keyList):
            self.funcs.tagControl(asset, obj, key.replace(" ", ""))
        # tag the temp controls
        tempControlList = [pvControl, ikControl, elbowPvControl, lengthControl]
        self.funcs.tagControlList(asset, tempControlList, prefix='',
                                  keyList=self.assetTempControlKeyDict[assetTag])

    def temporaryIK_IKElbowLockSelection(self, reset=False, debug=False):
        assetName = '_IK_Elbow_Lock'
        assetTag = str(assetName)
        # keyList = [key_Shoulder, key_TopIK, key_IKControl]
        keyList = self.assetKeyDict.get(assetTag, list())
        tempControlKeyList = self.assetTempControlKeyDict.get(assetTag, list())
        sel = cmds.ls(sl=True)
        if not sel:
            return raiseInfo('Please select at least one control for the temporary Ik elbow lock to work',
                             title='No selection')

        self.currentNamespace = None
        CharacterTool = self.allTools.tools['CharacterTool']
        char = CharacterTool.getSelectedChar(sel[-1])

        # print ('sel', sel)

        refName, refState, namespace = self.getCurrentRig(sel[0])
        self.loadDataCharacter(refName)
        ikData = self.loadedIkFkData[refName]
        strippedSelection = [self.removeNamespace(s, namespace) for s in sel]
        # check current controls to see if they are defined
        currentData, dataKey = ikData.findLockIKLimb(strippedSelection, assetTag)

        if not currentData or reset:
            self.currentNamespace = namespace
            dialog = self.queryObjects(title='Locked IK limb setup',
                                       info='Please enter the following controls',
                                       assetTag=assetTag,
                                       refName=refName,
                                       )
            # dialog.acceptedSignal.connect(self.temporaryIK_IKElbowLockSelection)
            dialog.saveSignal.connect(self.saveTempIkData)
            if reset:
                return
        if not currentData:
            return

        if len(sel) == 1:
            shoulder = namespace + ':' + currentData[key_Shoulder]
            upper = namespace + ':' + currentData[key_TopIK]
            wrist = namespace + ':' + currentData[key_IKControl]
        elif len(sel) == 2:
            shoulder = sel[0]
            upper = namespace + ':' + currentData[key_TopIK]
            wrist = namespace + ':' + currentData[key_IKControl]

        allControls = [shoulder, upper, wrist]
        if not all([cmds.objExists(s) for s in allControls]):
            return cmds.warning('cannot find all controls {}'.format(allControls))

        shoulderParent = cmds.listRelatives(shoulder, parent=True)[0]

        assetName = namespace + str(wrist) + assetName
        if not cmds.objExists(assetName):
            asset = self.createAsset(assetName, imageName=None, assetTag=assetTag)
        else:
            asset = assetName

        rootNode = self.funcs.tempNull(name=shoulder, suffix='ikBase')
        controlScales = self.loadedIkFkData[refName].__dict__.get(assetTag + 'Scales', dict()).get(dataKey, dict())

        pvControl = self.funcs.tempControl(name=shoulder,
                                           suffix='PV',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                           drawType='orb')
        cmds.setAttr(pvControl + '.scale', controlScales.get(self.assetTempControlKeyDict[assetTag][0], [1, 1, 1]), type='double3')
        lengthControl = self.funcs.tempControl(name=shoulder,
                                               suffix='Length',
                                               scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                               drawType='cross')

        cmds.setAttr(lengthControl + '.scale', controlScales.get(self.assetTempControlKeyDict[assetTag][1], [1, 1, 1]), type='double3')
        ikControl = self.funcs.tempControl(name=wrist,
                                           suffix='IK',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                           drawType='orb')
        cmds.setAttr(ikControl + '.scale', controlScales.get(self.assetTempControlKeyDict[assetTag][2], [1, 1, 1]), type='double3')
        lengthParent = self.funcs.tempNull(name=shoulder, suffix='Length_grp')
        cmds.delete(cmds.parentConstraint(shoulder, rootNode))
        cmds.parentConstraint(shoulderParent, rootNode, maintainOffset=True)
        cmds.parent(lengthControl, lengthParent)
        cmds.delete(cmds.parentConstraint(wrist, ikControl))

        self.funcs.boldControl(wrist, ikControl, offset=1.0)
        self.funcs.boldControl(shoulder, lengthControl, offset=1.0)
        self.funcs.boldControl(shoulder, pvControl, offset=1.0)

        # control colours
        self.funcs.getSetColour(shoulder, pvControl, brightnessOffset=0.05)
        self.funcs.getSetColour(shoulder, lengthControl, brightnessOffset=0.05)
        self.funcs.getSetColour(wrist, ikControl, brightnessOffset=0.05)

        '''
        pvControl = self.funcs.tempControl(name=shoulder,
                                           suffix='PV',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1),
                                           drawType='orb')
        ikControl = self.funcs.tempControl(name=elbow,
                                           suffix='IK',
                                           scale=get_option_var(tempIkControlScaleOptionVar, 1) * 0.5,
                                           drawType='orb')
        cmds.delete(cmds.parentConstraint(upper, pvControl))
        cmds.delete(cmds.parentConstraint(wrist, ikControl))
        '''
        lockedJoints = list()
        # lock joints
        cmds.bakeResults(clear=True)
        for index, s in enumerate([shoulder, upper, wrist]):
            aimConstraint = None
            # cmds.bakeResults(s)
            # print ('s', s)

            joint = cmds.joint(name=str(s) + '_locked')
            constraint = cmds.pointConstraint(s, joint)[0]
            cmds.parent(joint, rootNode)

            cmds.setAttr(joint + '.scale', 1, 1, 1, type='double3')
            cmds.setAttr(joint + '.drawStyle', 2)
            lockedJoints.append(joint)
            if lockedJoints[max(index - 1, 0)] != joint:
                cmds.parent(joint, lockedJoints[index - 1], relative=True)
                if index < 2:
                    aimConstraint = cmds.aimConstraint(wrist, joint, aimVector=[1, 0, 0])
                cmds.joint(joint, edit=True, spa=True, ch=True)
            else:
                cmds.parent(joint, rootNode, relative=True)
            cmds.delete(constraint)
            if aimConstraint: cmds.delete(aimConstraint)
            cmds.setAttr(joint + '.jointOrient', cmds.getAttr(joint + '.rotate'))
            cmds.setAttr(joint + '.rotate', 0, 0, 0, type='double3')

        cmds.delete(cmds.parentConstraint(lockedJoints[1], lengthParent))
        cmds.parent(lengthParent, lockedJoints[1])

        # parent the length control to the locked joints
        cmds.delete(cmds.pointConstraint(lockedJoints[2], lengthParent))
        cmds.delete(cmds.pointConstraint(lockedJoints[1], lengthControl))

        pvPosition = self.calculateShoulderPvPosition(lockedJoints)
        locked_ikHandle, locked_effector = cmds.ikHandle(sj=lockedJoints[0], ee=lockedJoints[-1], p=2, w=1.0)
        cmds.setAttr(locked_ikHandle + '.visibility', 0)
        cmds.setAttr(locked_effector + '.visibility', 0)
        cmds.setAttr(locked_ikHandle + '.snapEnable', 1)
        cmds.setAttr(locked_ikHandle + '.stickiness', 1)

        cmds.setAttr(pvControl + '.translate', pvPosition[0], pvPosition[1], pvPosition[2])
        pvConstraint = cmds.poleVectorConstraint(pvControl, locked_ikHandle)

        cmds.parent(locked_ikHandle, ikControl)

        constraints = list()
        constraints.append(cmds.parentConstraint(upper, lengthControl, maintainOffset=True)[0])
        constraints.append(cmds.parentConstraint(shoulder, pvControl, maintainOffset=True, skipRotate=('x', 'y', 'z'))[0])
        constraints.append(
            cmds.parentConstraint(shoulder, pvControl, maintainOffset=False, skipTranslate=('x', 'y', 'z'))[0])
        constraints.append(cmds.parentConstraint(wrist, ikControl, maintainOffset=False)[0])

        tempConstraint = cmds.parentConstraint(wrist, lengthParent, maintainOffset=True, skipRotate=('x', 'y', 'z'))[0]
        distanceNode = cmds.createNode('distanceBetween')
        cmds.connectAttr(upper + '.worldMatrix', distanceNode + '.inMatrix1')
        cmds.connectAttr(ikControl + '.worldMatrix', distanceNode + '.inMatrix2')
        cmds.connectAttr(distanceNode + '.distance', lockedJoints[2].translateX)

        # 
        # Bake
        # 

        bakeTools = self.allTools.tools['BakeTools']
        filteredTargets = [lengthControl, pvControl, ikControl]
        bakeRange = self.funcs.getBakeRange([wrist, shoulder])

        cmds.cycleCheck(evaluation=False)
        bakeTools.quickBake(filteredTargets, startTime=bakeRange[0], endTime=bakeRange[-1],
                            deleteConstraints=True)
        cmds.cycleCheck(evaluation=True)
        for c in constraints:
            if cmds.objExists(c): cmds.delete(c)

        self.funcs.eulerFilterControl(filteredTargets)

        cmds.delete(distanceNode)
        cmds.delete(tempConstraint)
        # cmds.parent(lengthParent, lockedJoints[1])
        cmds.setAttr(lengthParent + '.rotate', 0, 0, 0, type='double3')
        # connect the length bone to the control
        reverseNode = cmds.createNode('multiplyDivide')
        cmds.setAttr(reverseNode + '.input1X', -1)
        cmds.connectAttr(lengthControl.translateX, reverseNode.input2X)
        cmds.connectAttr(reverseNode.outputX, lengthParent.translateX)
        cmds.connectAttr(reverseNode.outputX, lockedJoints[2].translateX, force=True)

        # 
        # Constrain original controls up
        #
        cmds.delete(cmds.orientConstraint(shoulder, pvControl))
        constraint = self.funcs.constrainAimToTarget(str(shoulder),
                                                     str(lockedJoints[1]),
                                                     rotationObject=str(pvControl),
                                                     maintainOffset=True)

        '''
        self.funcs.safeParentConstraint(lockedJoints[0], shoulder,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(twoBoneJoints[0], upper,
                                        orientOnly=True,
                                        maintainOffset=True)
        self.funcs.safeParentConstraint(twoBoneJoints[1], elbow,
                                        orientOnly=True,
                                        maintainOffset=True)
        '''
        self.funcs.safeParentConstraint(ikControl, wrist,
                                        orientOnly=False,
                                        maintainOffset=True)

        cmds.cutKey(lengthControl,
                    clear=True,
                    at=["ty", "tz", "rx", "ry", "rz"])
        cmds.setAttr(lengthParent + '.ty', 0)
        cmds.setAttr(lengthParent + '.tz', 0)
        cmds.setAttr(lengthParent + '.rx', 0)
        cmds.setAttr(lengthParent + '.ry', 0)
        cmds.setAttr(lengthParent + '.rz', 0)
        cmds.setAttr(lengthControl + '.ty', 0, lock=True)
        cmds.setAttr(lengthControl + '.tz', 0, lock=True)
        cmds.setAttr(lengthControl + '.rx', 0, lock=True)
        cmds.setAttr(lengthControl + '.ry', 0, lock=True)
        cmds.setAttr(lengthControl + '.rz', 0, lock=True)

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=False,
                       force=True,
                       addNode=[ikControl, pvControl, lengthControl])

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[lengthControl])

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=False,
                       force=True,
                       addNode=rootNode)

        if not debug:
            cmds.setAttr(rootNode + '.hiddenInOutliner', True)
        # tag the anim controls
        for obj, key in zip(allControls, keyList):
            self.funcs.tagControl(asset, obj, key.replace(" ", ""))
        # tag the temp controls
        tempControlList = [pvControl, lengthControl, ikControl]
        self.funcs.tagControlList(asset, tempControlList, prefix='',
                                  keyList=self.assetTempControlKeyDict[assetTag])

    def calculateShoulderPvPosition(self, joints):
        jointUp = str(joints[0])
        jointMid = str(joints[1])

        if not cmds.objExists(jointUp):
            return raiseError('Control not found for match  (%s)' % str(jointUp))
        if not cmds.objExists(jointMid):
            return raiseError('Control not found for match  (%s)' % str(jointMid))
        startPos = cmds.xform(jointUp, query=True, worldSpace=True,
                              rotatePivot=True)
        midPos = cmds.xform(jointMid, query=True, worldSpace=True,
                            rotatePivot=True)

        startMV = om2.MVector(startPos[0], startPos[1], startPos[2])
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])

        offset = midMV - startMV
        return midMV
        return startMV + (offset * 2)

    def calculatePVPosition(self, joints):
        jointUp = str(joints[0])
        jointMid = str(joints[1])
        jointEnd = str(joints[2])

        if not cmds.objExists(jointUp):
            return raiseError('Control not found for match  (%s)' % str(jointUp))
        if not cmds.objExists(jointMid):
            return raiseError('Control not found for match  (%s)' % str(jointMid))
        if not cmds.objExists(jointEnd):
            return raiseError('Control not found for match  (%s)' % str(jointEnd))
        startPos = cmds.xform(jointUp, query=True, worldSpace=True,
                              translation=True)
        midPos = cmds.xform(jointMid, query=True, worldSpace=True,
                            translation=True)
        endPos = cmds.xform(jointEnd, query=True, worldSpace=True,
                            translation=True)

        startMV = om2.MVector(startPos[0], startPos[1], startPos[2])
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        endMV = om2.MVector(endPos[0], endPos[1], endPos[2])

        start_endV = endMV - startMV

        start_midV = midMV - startMV
        # check if joints are totally in line
        alignCheck = start_endV.normal() * start_midV.normal()
        if alignCheck >= 0.998:
            # joints are almost totally aligned, pv position can wig out
            pvTransform = om2.MMatrix(cmds.xform(jointMid,
                                                 query=True,
                                                 worldSpace=True,
                                                 matrix=True))
            pvMTransformMtx = om2.MTransformationMatrix(pvTransform)
            return pvMTransformMtx.translation(om2.MSpace.kWorld)

        dot = start_endV * start_midV
        if float(start_endV.length()) <= 0:
            return raiseError('Start to end joint distance is zero, check your joint definitions')
        p = float(dot) / float(start_endV.length())
        jointVectorN = start_endV.normal()
        pV = jointVectorN * p
        length = (start_midV - pV).length()
        aV = (start_midV - pV).normalize()
        aV *= (length * 2)
        V = aV + midMV

        return V

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = cmds.ls(sl=True)
        asset = cmds.container(query=True, findContainer=sel[0])

        # check asset message attribute

        cmds.menuItem(label='Temp IK Tools', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        assetType = cmds.getAttr(asset + '.assetTag')
        rmbFunc = self.assetRmbDict.get(assetType, None)
        if rmbFunc:
            rmbFunc(asset)
        return

    def rmb__IK_Elbow_Lock(self, asset):
        cmds.menuItem(label='Bake temp controls to layer',
                      command=create_callback(self.bakeSelectedCommand, asset),
                      image='bakeAnimation.png'
                      )
        cmds.menuItem(label='Bake all temp controls to layer',
                      # command=create_callback(self.bakeAllCommand, asset, sel),
                      enable=False,
                      image='bakeAnimation.png'
                      )
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Delete temp controls',
                      command=create_callback(self.deleteSelectedControlsCommand, asset),
                      image='deletePreset.png'
                      )
        cmds.menuItem(label='Delete all temp controls',
                      # command=create_callback(self.deleteControlsCommand, asset, sel),
                      enable=False,
                      image='deleteActive.png'
                      )
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Save control sizes',
                      command=create_callback(self.saveControlSizes, asset),
                      image='save.png'
                      )

    def deleteSelectedControlsCommand(self, asset):
        cmds.delete(asset)

    def bakeSelectedCommand(self, asset):
        # print ('bakeSelectedCommand', asset)
        try:
            assetTag = cmds.getAttr(asset + '.assetTag')
            # print ('assetTag', assetTag)
            objectList = self.assetControlNameKeyDict.get(assetTag, None)
            # print ('objectList', objectList)
            if not objectList:
                return
            filteredTargets = [cmds.listConnections(asset + '.' + x.replace(' ', ''))[0] for x in objectList]
            # print ('filteredTargets', filteredTargets)
            bakeRange = self.funcs.getBakeRange([str(x) for x in filteredTargets])
            cmds.cycleCheck(evaluation=False)
            self.allTools.tools['BakeTools'].bake_to_override(sel=filteredTargets,
                                                              keyRange=[bakeRange[0], bakeRange[-1]],
                                                              layerPrefix='IK_',
                                                              deleteConstraints=True)
            cmds.delete(asset)
        finally:
            cmds.cycleCheck(evaluation=True)

    def queryObjects(self,
                     title='placeholder_title',
                     info='placeholder_info',
                     assetTag=str(),
                     refName=None,
                     selection=list()):
        objectList = self.assetKeyDict.get(assetTag, None)
        if not objectList:
            return cmds.error('Failing to get control list')
        dialog = MultiObjectInputWidget(title=title, info=info, buttonText='Save',
                                        refName=refName,
                                        assetTag=assetTag,
                                        checkBox=None, overlay=False, showCloseButton=True,
                                        lineEditPlaceholder=objectList,
                                        helpString=None,
                                        parentWidget=None)
        if selection:
            for i in range(len(selection)):
                if i <= len(objectList):
                    dialog.lineEdits[i].setText(selection[i])
        dialog.show()
        return dialog

    def saveControlSizes(self, asset):
        """
        Figure out how to organize this
        :param asset:
        :return:
        """
        # TODO - get the attribute lists, prefix them with something so I know it's a control?
        # Figure out how to get the correct dict key
        assetTag = cmds.getAttr(asset + '.assetTag')
        # dictkey = self.assetKeyDict.get(assetTag, None)

        keyList = self.assetKeyDict.get(assetTag, list())
        tempControlKeyList = self.assetTempControlKeyDict.get(assetTag, list())

        controls = [cmds.listConnections(asset + '.' + key.replace(" ", ""))[0] for key in keyList]
        tempControls = [cmds.listConnections(asset + '.' + key.replace(" ", ""))[0] for key in tempControlKeyList]

        CharacterTool = self.allTools.tools['CharacterTool']
        refName, namespace = CharacterTool.getSelectedChar(controls[-1])
        namespace = self.stripLeadingColon(namespace)
        controlKey = controls[-1].replace(namespace, '')
        controlKey = self.stripLeadingColon(controlKey)
        self.loadDataCharacter(refName)
        strippedControls = [self.removeNamespace(s, namespace) for s in controls]

        ikData = self.loadedIkFkData[refName]
        # print ('namespace', namespace)
        if not assetTag + 'Scales' in self.loadedIkFkData[refName].__dict__.keys():
            self.loadedIkFkData[refName][assetTag + 'Scales'] = dict()
        if not controls[-1] in self.loadedIkFkData[refName][assetTag + 'Scales'].keys():
            self.loadedIkFkData[refName][assetTag + 'Scales'][controlKey] = dict()
        for key, control in zip(tempControlKeyList, tempControls):
            self.loadedIkFkData[refName][assetTag + 'Scales'][controlKey][key] = cmds.getAttr(control + '.scale')[0]

        # self.loadedIkFkData[refName].lockIKlimbsSizes[objectList[-1]]= {key: cmds.getAttr(c + '.scale') for key, c in
        #                                                             zip(IK_IKElbowLock_tempControl_keyList, tempControls)}
        '''
        # convert to the mirror stuff
        self.loadedIkFkData[refName].lockIKlimbsSizes[objectList[-1] ]= {key: cmds.getAttr(c + '.scale') for key, c in
                                                                    zip(IK_IKElbowLock_tempControl_keyList, tempControls)}
        '''
        self.saveRigFile(refName)

    def stripLeadingColon(self, namespace):
        if namespace.startswith(':'):
            namespace = namespace[1:]
        return namespace

    """
    TODO
    get_all_key_times_for_node
    get each limbs unique key times (combined from members of that set)
    get master key time list and use that as a set for matching
    run through the set, matching each limb as needed
    
    work on the baking, on all key range or slider highlight etc
    """


class IkDataAbstract(ABC):
    def __init__(self, namespace):
        self.limbType = 'base'

        self.ikControl = str()
        self.ikAttr = str()
        self.ikValue = float()
        self.fkValue = float()
        self.jointKeys = list()
        self.ikZeroControl = list()
        self.ikZeroAttribute = list()

        self.lastFkControl = str()
        self.fkKeys = list()
        self.ikKeys = list()
        self.optionalKeys = list()
        self.limbWidget = None
        self.__modified = False

    def setUnModified(self):
        self.__dict__['__modified'] = False

    def __setattr__(self, name, value):
        # print(name, value)
        self.__dict__[name] = value
        if name != '__modified':
            if not self.__dict__.get('__modified', False):
                self.__dict__['__modified'] = True

    def toJson(self):
        jsonData = '''{}'''
        classData = json.loads(jsonData)
        for k, v in self.__dict__.items():
            if k.startswith('__'):
                continue
            if k == 'limbWidget':
                continue
            classData[k] = v
        return classData

    def splitAndInsertSide(self, namespace, control, sideA, sideB):
        attr = None
        original = str(control)
        if '.' in control:
            control, attr = control.split('.')
        opposite = IkFkTools().funcs.getOppositeControl('{ns}:{c}'.format(ns=namespace, c=control))
        if not opposite:
            opposite = original + '_FAILED'
        opposite = opposite.split(':')[-1]
        if attr:
            opposite = opposite + '.' + attr
        return opposite
        sp = control.rsplit(sideA, 1)
        if len(sp) == 1:
            return sp[0]
        return str(sideB).join([r for r in sp])

    def controlInData(self, control):
        return control in self.__dict__.values()

    @abc.abstractmethod
    def getIkFkOffsets(self, namespace):
        pass

    @abc.abstractmethod
    def matchToFK(self, namespace):
        pass

    @abc.abstractmethod
    def matchToIKMain(self, namespace):
        """
        Used as the main match - logic goes here to determine which extra matches to perform
        :param namespace:
        :return:
        """
        pass

    @abc.abstractmethod
    def matchToIK(self, namespace):
        pass

    def zeroExtraControls(self, namespace, skipped=list()):
        skippedControls = [IkFkTools().getControl(namespace, c) for c in skipped]
        for attr in self.ikZeroAttribute:
            control = IkFkTools().getControlForAttr(namespace, attr)
            self.zeroAttribute(control)
        for control in self.ikZeroControl:
            control = IkFkTools().getControl(namespace, control)
            if control in skippedControls:
                continue
            self.zeroControl(control)

    def zeroAttribute(self, node):
        cmds.setAttr(node, 0)

    def zeroControl(self, node):
        manips = IkFkTools().allTools.tools['Manipulators']
        manips.zero_channel(["tx", "ty", "tz", "rx", "ry", "rz"], 0, sel=[node])
        manips.zero_channel(["sx", "sy", "sz"], 1, sel=[node])

    def muteIkAttr(self, namespace, state):
        cmds.mute(self.getIkAttr(namespace), disable=not state)

    def getBestControlByState(self, namespace):
        ikState = cmds.getAttr(self.getIkAttr(namespace))
        sel = cmds.ls(sl=True)

        ikControls = [IkFkTools().getControl(namespace, self.__dict__[x]) for x in self.ikKeys]
        ikControls.extend(IkFkTools().getControl(namespace, self.__dict__[x]) for x in self.optionalKeys)
        ikControls.extend(IkFkTools().getControl(namespace, x) for x in self.ikZeroControl)
        fkControls = [IkFkTools().getControl(namespace, self.__dict__[x]) for x in self.fkKeys]
        removedControls = list()
        addedControls = list()

        if ikState == self.ikValue:
            matched = False
            for s in sel:
                if s in ikControls:
                    print('in ik', s)
                    matched = True
            if not matched:
                addedControls = self.getIkControl(namespace)
            for s in sel:
                if s in fkControls:
                    removedControls.append(s)
        else:
            matched = False
            for s in sel:
                if s in fkControls:
                    print('in fk', s)
                    matched = True
            if not matched:
                addedControls = self.getLastFkControl(namespace)
            for s in sel:
                if s in ikControls:
                    removedControls.append(s)

        cmds.select(removedControls, deselect=True)
        cmds.select(addedControls, add=True)

    def getLastFkControl(self, namespace):
        fkControl = IkFkTools().getControl(namespace, self.__dict__[self.lastFkControl])
        return fkControl

    def getIkControl(self, namespace):
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        return ikControl

    def setToIk(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        cmds.setAttr(ikControlAttr, self.ikValue)

    def setToFk(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        cmds.setAttr(ikControlAttr, self.fkValue)

    def getIkAttr(self, namespace):
        return IkFkTools().getControl(namespace, self.ikAttr)

    def getZeroAttrs(self, namespace):
        returnList = list()
        if not self.ikZeroAttribute:
            return returnList
        for attr in self.ikZeroAttribute:
            returnList.append(IkFkTools().getControl(namespace, attr))
        return returnList

    def getZeroControls(self, namespace):
        returnList = list()
        if not self.ikZeroControl:
            return returnList
        for attr in self.ikZeroControl:
            returnList.append(IkFkTools().getControl(namespace, attr))
        return returnList

    def setIkValue(self, namespace, value):
        cmds.setAttr(self.getIkAttr(namespace), value)

    def getIkValue(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        return cmds.getAttr(ikControlAttr)

    def getIkValuesForTimeList(self, namespace, timeList):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        return [cmds.getAttr(ikControlAttr, time=t) for t in timeList]

    @abc.abstractmethod
    def preBake(self, namespace, ik, fk):
        """

        :param namespace:
        :param ik: True for ik, false for fk
        :return:
        """
        constraints = list()
        tempNodes = dict()
        # hold the current limb data
        for j in self.jointKeys:
            joint = IkFkTools().getControl(namespace, self.__dict__.get(j))
            tempNode = cmds.createNode('transform', name=joint + '_preBake')
            constraint = cmds.parentConstraint(joint, tempNode)[0]
            tempNodes[j] = tempNode
            constraints.append(constraint)

        return tempNodes, constraints

    @abc.abstractmethod
    def postBake(self, namespace, ik, fk, tempNodesDict):
        """
        Perform the ik control match + constraint
        figure out pole vector position from input baked nodes
        :param namespace:
        :param ik:
        :return:
        """
        returnControls = list()
        returnConstraints = list()
        if ik:
            ikReturnControls, constraints = self.postBakeIK(namespace, tempNodesDict)
            returnControls.extend(ikReturnControls)
            returnConstraints.extend(constraints)
        if fk:
            fkReturnControls, constraints = self.postBakeFK(namespace, tempNodesDict)
            returnControls.extend(fkReturnControls)
            returnConstraints.extend(constraints)
        return returnControls, returnConstraints

    @abc.abstractmethod
    def postBakeIK(self, namespace, tempNodesDict):
        """
        Constrains the fk controls to the baked locators
        :param namespace:
        :param tempNodesDict:
        :return:
        """
        pass

    @abc.abstractmethod
    def postBakeFK(self, namespace, tempNodesDict):
        """
        Constrains the fk controls to the baked locators
        :param namespace:
        :param tempNodesDict:
        :return:
        """
        pass

    @abc.abstractmethod
    def getFkBakeTargets(self, namespace):
        pass

    @abc.abstractmethod
    def getIkBakeTargets(self, namespace):
        pass

    def mirrorAttribute(self, namespace, attribute):
        # mirror ik attribute
        # print ('mirrorAttribute', namespace, attribute)
        control = attribute.split('.')[0]
        attr = attribute.split('.')[-1]
        # print ('control,', control)
        # print ('attr,', attr)
        if not cmds.objExists(namespace + ':' + control):
            return cmds.warning(namespace + ':' + control + ' does not exist')

        if cmds.objExists(namespace + ':' + control + '.' + attr):
            # print ('attribute exists')
            return attribute
        userAttrs = cmds.listAttr(namespace + ':' + control, userDefined=True)
        matches = get_close_matches(attr, userAttrs, cutoff=0.5)
        # print ('matches', matches)
        if matches:
            return control + '.' + matches[0]
        return ''

    @abc.abstractmethod
    def mirrorControls(self, char, namespace):
        MirrorTools = IkFkTools().allTools.tools['MirrorTools']
        for key, value in self.__dict__.items():
            if not str(value):
                continue
            if key == 'limbType':
                continue
            if not isinstance(value, unicode) and not isinstance(value, str):
                continue
            self.__dict__[key] = MirrorTools.getMirrorForControlFromCharacter(char, value)

        for key, value in self.__dict__.items():
            if isinstance(value, list):

                if key == 'ikZeroControl':
                    self.__dict__[key] = [MirrorTools.getMirrorForControlFromCharacter(char, v) for v in value]
                    continue
                if key == 'ikZeroAttribute':
                    # print ('key', key, value)
                    self.__dict__[key] = [MirrorTools.getMirrorForControlFromCharacter(char, v) for v in value]
                    self.__dict__[key] = [self.mirrorAttribute(namespace, v) for v in self.__dict__[key]]

        # controls are now mirrored, mirror the attributes themselves
        self.ikAttr = self.mirrorAttribute(namespace, self.ikAttr)

    @abc.abstractmethod
    def getCurrentState(self, namespace):
        pass

    def constrain(self, target, control):
        skipT = IkFkTools().funcs.getAvailableTranslates(control)
        skipR = IkFkTools().funcs.getAvailableRotates(control)
        return cmds.parentConstraint(target, control,
                                     skipTranslate=[x.split('translate')[-1] for x in skipT],
                                     skipRotate=[x.split('rotate')[-1] for x in skipR],
                                     maintainOffset=True)[0]

    def validateMatch(self, namespace, ikObjectList, fkObjectList, ikControlAttr):
        translates = dict()
        rotates = dict()

        postTranslates = dict()
        postRotates = dict()

        cmds.setAttr(ikControlAttr, self.fkValue)
        self.matchToFK(namespace)
        # ik validation
        cmds.setAttr(ikControlAttr, self.ikValue)
        self.matchToIKMain(namespace)

        for obj in ikObjectList:
            translates[obj] = cmds.xform(obj, translation=True, ws=1, q=True)
            rotates[obj] = cmds.xform(obj, rotation=True, ws=1, q=True)
        self.matchToIKMain(namespace)
        for obj in ikObjectList:
            postTranslates[obj] = cmds.xform(obj, translation=True, ws=1, q=True)
            postRotates[obj] = cmds.xform(obj, rotation=True, ws=1, q=True)
        matchedOk = True
        for obj in ikObjectList:
            for x, y in zip(translates[obj], postTranslates[obj]):
                if not int(x) == int(y):
                    return False
            if matchedOk:
                for x, y in zip(rotates[obj], postRotates[obj]):
                    if not int(x) == int(y):
                        return False

        # fk validation
        cmds.setAttr(ikControlAttr, self.fkValue)
        self.matchToFK(namespace)
        for obj in fkObjectList:
            translates[obj] = cmds.xform(obj, translation=True, ws=1, q=True)
            rotates[obj] = cmds.xform(obj, rotation=True, ws=1, q=True)
        self.matchToFK(namespace)
        for obj in fkObjectList:
            postTranslates[obj] = cmds.xform(obj, translation=True, ws=1, q=True)
            postRotates[obj] = cmds.xform(obj, rotation=True, ws=1, q=True)
        matchedOk = True
        for obj in fkObjectList:
            for x, y in zip(translates[obj], postTranslates[obj]):
                if not int(x) == int(y):
                    return False
            if matchedOk:
                for x, y in zip(rotates[obj], postRotates[obj]):
                    if not int(x) == int(y):
                        return False

        return True


class TwoBoneIKData(IkDataAbstract):
    def __init__(self, namespace):
        super(TwoBoneIKData, self).__init__(namespace)
        self.limbType = 'arm'
        self.jointUp = str()
        self.jointMid = str()
        self.jointEnd = str()
        self.fkControlUp = str()
        self.fkControlMid = str()
        self.fkControlEnd = str()
        self.ikControl = str()
        self.pvControl = str()
        self.fkControlOffsets = dict()
        self.ikControlOffset = list()
        self.pvDistance = float()
        self.pvOffset = list()
        self.ikAttr = str()
        self.ikValue = float()
        self.fkValue = float()

        self.lastFkControl = 'fkControlEnd'
        self.jointKeys = ['jointUp', 'jointMid', 'jointEnd']
        self.fkKeys = ['fkControlUp', 'fkControlMid', 'fkControlEnd']
        self.ikKeys = ['pvControl', IK_CONTROL]
        self.optionalKeys = []
        self.limbWidget = LimbWidget(self, namespace)

    def enforceKeyOrder(self):
        self.jointKeys = ['jointUp', 'jointMid', 'jointEnd']
        self.fkKeys = ['fkControlUp', 'fkControlMid', 'fkControlEnd']
        self.ikKeys = ['pvControl', IK_CONTROL]

    def controlInData(self, control):
        for key, value in self.__dict__.items():
            # print ('controlInData', control, key, value)
            if isinstance(value, (str, unicode)):
                if control in value:
                    return True
        return control in self.__dict__.values()

    def calculatePVPosition(self, namespace):
        jointUp = IkFkTools().getControl(namespace, self.jointUp)
        jointMid = IkFkTools().getControl(namespace, self.jointMid)
        jointEnd = IkFkTools().getControl(namespace, self.jointEnd)
        if not cmds.objExists(jointUp):
            return raiseError('Control not found for match  (%s)' % str(jointUp))
        if not cmds.objExists(jointMid):
            return raiseError('Control not found for match  (%s)' % str(jointMid))
        if not cmds.objExists(jointEnd):
            return raiseError('Control not found for match  (%s)' % str(jointEnd))
        startPos = cmds.xform(jointUp, query=True, worldSpace=True,
                              translation=True)
        midPos = cmds.xform(jointMid, query=True, worldSpace=True,
                            translation=True)
        endPos = cmds.xform(jointEnd, query=True, worldSpace=True,
                            translation=True)

        startMV = om2.MVector(startPos[0], startPos[1], startPos[2])
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        endMV = om2.MVector(endPos[0], endPos[1], endPos[2])

        start_endV = endMV - startMV

        start_midV = midMV - startMV
        # check if joints are totally in line
        alignCheck = start_endV.normal() * start_midV.normal()
        if alignCheck >= 0.998:
            # joints are almost totally aligned, pv position can wig out
            upperJointMtx = om2.MMatrix(cmds.xform(jointUp,
                                                   query=True,
                                                   worldSpace=True,
                                                   matrix=True))
            pvTransform = om2.MMatrix(self.pvOffset) * upperJointMtx
            pvMTransformMtx = om2.MTransformationMatrix(pvTransform)
            return pvMTransformMtx.translation(om2.MSpace.kWorld)

        dot = start_endV * start_midV
        if float(start_endV.length()) <= 0:
            return raiseError('Start to end joint distance is zero, check your joint definitions')
        p = float(dot) / float(start_endV.length())
        jointVectorN = start_endV.normal()
        pV = jointVectorN * p

        aV = (start_midV - pV).normalize()
        aV *= self.pvDistance
        V = aV + midMV

        return V

    def getPVDistance(self, namespace):
        """
        Gets the pole vector distance for caching
        :return:
        """
        # TODO - check that the ik control is not further away than the end joint is from the root joint
        control = IkFkTools().getControl(namespace, self.ikControl)
        ikPos = cmds.xform(control, query=True, worldSpace=True,
                           rotatePivot=True)
        midPos = cmds.xform(IkFkTools().getControl(namespace, self.jointMid), query=True, worldSpace=True,
                            rotatePivot=True)
        pvPos = cmds.xform(IkFkTools().getControl(namespace, self.pvControl), query=True, worldSpace=True,
                           rotatePivot=True)
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        pvMV = om2.MVector(pvPos[0], pvPos[1], pvPos[2])

        distance = (pvMV - midMV)

        pvTransform = om2.MMatrix()
        pvMTransformMtx = om2.MTransformationMatrix(pvTransform)
        pvMTransformMtx.setTranslation(pvMV, om2.MSpace.kWorld)
        upperJointMtx = om2.MMatrix(
            cmds.xform(IkFkTools().getControl(namespace, self.jointUp), query=True, worldSpace=True,
                       matrix=True))
        pvOffset = pvMTransformMtx.asMatrix() * upperJointMtx.inverse()

        return distance.length(), [x for x in pvOffset]

    def getIkFkOffsets(self, namespace):
        keyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(edit=True, state=False)
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)

        node, attr = ikControlAttr.split('.')
        if not cmds.attributeQuery(attr, node=node, exists=True):
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))
        currentState = cmds.getAttr(ikControlAttr)
        cmds.setAttr(ikControlAttr, self.fkValue)

        fkControls = list()
        for j, c in zip(self.jointKeys, self.fkKeys):
            control = IkFkTools().getControl(namespace, self.__dict__[c])
            fkControls.append(control)
            joint = IkFkTools().getControl(namespace, self.__dict__[j])
            if not cmds.objExists(control):
                return raiseError('Control not found for (%s)' % control)
                # return cmds.error('Control not found for ', control)
            if not cmds.objExists(joint):
                return raiseError('Joint not found for (%s)' % joint)
                # return cmds.error('Joint not found for ', j)
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            resultMatrix = controlMMatrix * jointMMatrix.inverse()
            self.fkControlOffsets[c] = [x for x in resultMatrix]
        self.pvDistance, self.pvOffset = self.getPVDistance(namespace)
        cmds.setAttr(ikControlAttr, self.ikValue)

        # ik is just one control this time
        control = IkFkTools().getControl(namespace, self.ikControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        joint = IkFkTools().getControl(namespace, self.jointEnd)
        controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
        jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
        resultMatrix = controlMMatrix * jointMMatrix.inverse()
        self.ikControlOffset = [x for x in resultMatrix]

        ikControls = [control, pvControl]
        matchedOk = self.validateMatch(namespace, ikControls, fkControls, ikControlAttr)

        cmds.setAttr(ikControlAttr, currentState)
        cmds.autoKeyframe(edit=True, state=keyState)
        if not matchedOk:
            return raiseError(
                'Ik matching failing to keep pose, check your object data in the UI and make sure your limb is in a relaxed pose.')
        return True

    def matchToFK(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        if not ikControlAttr:
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))

        for fk, j in zip(self.fkKeys, self.jointKeys):
            control = IkFkTools().getControl(namespace, self.__dict__.get(fk))
            joint = IkFkTools().getControl(namespace, self.__dict__.get(j))
            if not cmds.objExists(control):
                return raiseError('Control not found (%s)' % control)
                # return cmds.error('Control not found for ', fk)
            if not cmds.objExists(joint):
                return raiseError('Joint not found (%s) ' % joint)
                # return cmds.error('Joint not found for ', j)
        for fk, j in zip(self.fkKeys, self.jointKeys):
            control = IkFkTools().getControl(namespace, self.__dict__.get(fk))
            joint = IkFkTools().getControl(namespace, self.__dict__.get(j))
            jointMtx = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, absolute=True, q=True))
            offsetMtx = om2.MMatrix(self.fkControlOffsets[fk])
            fkResultMtx = offsetMtx * jointMtx
            cmds.xform(control, matrix=fkResultMtx, ws=1)

        cmds.setAttr(ikControlAttr, self.fkValue)

    def matchToIKMain(self, namespace, toe=False):
        self.matchToIK(namespace)

    def matchToIK(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        if not ikControlAttr:
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))
        node, attr = ikControlAttr.split('.')
        if not cmds.attributeQuery(attr, node=node, exists=True):
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        ikTarget = IkFkTools().getControl(namespace, self.jointEnd)
        if not cmds.objExists(ikControl):
            return raiseError('Ik Control not found for match  (%s)' % str(ikControl))
            # return cmds.error('Ik Control not found for match  (%s)' % str(ikControl))
        if not cmds.objExists(pvControl):
            return raiseError('Ik Control not found for match  (%s)' % str(ikControl))
            # return cmds.error('Pole Vector not found for match  (%s)' % str(pvControl))
        if not cmds.objExists(ikTarget):
            return raiseError('Ik Control not found for match  (%s)' % str(ikControl))
            # return cmds.error('Ik target not found for match (%s)' % str(ikTarget))
        ikTargetMtx = om2.MMatrix(cmds.xform(ikTarget, matrix=True, ws=1, absolute=True, q=True))

        pvRotatePivot = cmds.xform(pvControl, rotatePivot=True, ws=1, absolute=True, q=True)
        pvTranslation = cmds.xform(pvControl, translation=True, ws=1, absolute=True, q=True)
        pvTranslationMV = om2.MVector(pvTranslation[0], pvTranslation[1], pvTranslation[2])
        pvRotatePivotMV = om2.MVector(pvRotatePivot[0], pvRotatePivot[1], pvRotatePivot[2])
        offsetMtx = om2.MMatrix(self.ikControlOffset)
        ikResultMtx = offsetMtx * ikTargetMtx

        pvPos = self.calculatePVPosition(namespace)
        cmds.xform(ikControl, matrix=ikResultMtx, ws=1)
        cmds.xform(pvControl, translation=pvTranslationMV + (pvPos - pvRotatePivotMV), ws=1)

        self.zeroExtraControls(namespace)

        cmds.setAttr(ikControlAttr, self.ikValue)

    def preBake(self, namespace, ik, fk):
        """
        before baking, pin transforms to the joints, with the offset so controls align to them
        :param namespace:
        :param ik:
        :return:
        """
        tempNodes, constraints = super(TwoBoneIKData, self).preBake(namespace, ik, fk)
        return tempNodes, constraints

    def postBake(self, namespace, ik, fk, tempNodesDict):
        """
        Perform the ik control match + constraint
        figure out pole vector position from input baked nodes
        :param namespace:
        :param ik:
        :return:
        """
        return super(TwoBoneIKData, self).postBake(namespace, ik, fk, tempNodesDict)

    def postBakeIK(self, namespace, tempNodesDict):
        keyState = cmds.autoKeyframe(query=True, state=True)

        try:
            cmds.autoKeyframe(state=False)
            self.matchToIKMain(namespace)
        finally:
            cmds.autoKeyframe(state=keyState)
        returnControls = list()
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        returnControls.append(ikControl)
        returnControls.append(pvControl)
        constraints = list()
        ikTopTarget = tempNodesDict['jointUp']
        ikTarget = tempNodesDict['jointEnd']

        constraints.append(self.constrain(ikTarget, ikControl))
        constraints.append(self.constrain(ikTopTarget, pvControl))
        # self.muteIkAttr(namespace, True)
        return returnControls, constraints

    def postBakeFK(self, namespace, tempNodesDict):
        """
        Constrains the fk controls to the baked locators
        :param namespace:
        :param tempNodesDict:
        :return:
        """
        keyState = cmds.autoKeyframe(query=True, state=True)
        try:
            cmds.autoKeyframe(state=False)
            self.matchToFK(namespace)
        finally:
            cmds.autoKeyframe(state=keyState)

        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)

        constraints = list()
        controls = list()
        for j, fk in zip(self.jointKeys, self.fkKeys):
            control = IkFkTools().getControl(namespace, self.__dict__.get(fk))
            joint = tempNodesDict.get(j)
            skipT = IkFkTools().funcs.getAvailableTranslates(control)
            skipR = IkFkTools().funcs.getAvailableRotates(control)
            constraints.append(cmds.parentConstraint(joint, control,
                                                     skipTranslate=[x.split('translate')[-1] for x in skipT],
                                                     skipRotate=[x.split('rotate')[-1] for x in skipR],
                                                     maintainOffset=True,
                                                     decompRotationToChild=True)[0])
            controls.append(control)
        cmds.setAttr(ikControlAttr, self.fkValue)
        # self.muteIkAttr(namespace, True)
        return controls, constraints

    def getFkBakeTargets(self, namespace):
        fkControlUp = IkFkTools().getControl(namespace, self.fkControlUp)
        fkControlMid = IkFkTools().getControl(namespace, self.fkControlMid)
        fkControlEnd = IkFkTools().getControl(namespace, self.fkControlEnd)
        return [fkControlUp, fkControlMid, fkControlEnd]

    def getIkBakeTargets(self, namespace):
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        return [ikControl, pvControl]

    def mirrorControls(self, char, namespace):
        super(TwoBoneIKData, self).mirrorControls(char, namespace)

    def getCurrentState(self, namespace):
        """
        Gets the current state of the limb
        :param namespace:
        :return: True if in IK
        """
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        return cmds.getAttr(ikControlAttr) == self.ikValue


class LegIKData(IkDataAbstract):
    def __init__(self, namespace):
        super(LegIKData, self).__init__(namespace)
        self.limbType = 'leg'
        self.jointThigh = str()
        self.jointKnee = str()
        self.jointAnkle = str()
        self.jointToe = str()
        self.fkControlThigh = str()
        self.fkControlKnee = str()
        self.fkControlAnkle = str()
        self.fkControlToe = str()
        self.ikControl = str()
        self.ikToeControl = str()
        self.ikHeelLiftControl = str()
        self.ikHeelLiftControlOffset = dict()

        self.pvControl = str()
        self.fkControlOffsets = dict()
        self.ikControlOffset = dict()
        self.pvOffset = dict()
        self.pvDistance = float()
        self.ikAttr = str()
        self.ikValue = float()
        self.fkValue = float()

        self.lastFkControl = 'fkControlAnkle'
        self.jointKeys = ['jointThigh', 'jointKnee', 'jointAnkle', 'jointToe']
        self.fkKeys = ['fkControlThigh', 'fkControlKnee', 'fkControlAnkle', 'fkControlToe']
        self.ikKeys = ['pvControl', IK_CONTROL, 'ikToeControl']
        self.optionalKeys = ['ikToeControl']
        self.limbWidget = LegWidget(self, namespace)

    def enforceKeyOrder(self):
        self.jointKeys = ['jointThigh', 'jointKnee', 'jointAnkle', 'jointToe']
        self.fkKeys = ['fkControlThigh', 'fkControlKnee', 'fkControlAnkle', 'fkControlToe']
        self.ikKeys = ['pvControl', 'ikControl', 'ikToeControl']

    def controlInData(self, control):
        if control in self.__dict__.values():
            return True
        if control in self.__dict__.get('ikZeroControl', list()):
            return True
        return False

    def calculatePVPosition(self, namespace):
        startPos = cmds.xform(IkFkTools().getControl(namespace, self.jointThigh), query=True, worldSpace=True,
                              translation=True)
        midPos = cmds.xform(IkFkTools().getControl(namespace, self.jointKnee), query=True, worldSpace=True,
                            translation=True)
        endPos = cmds.xform(IkFkTools().getControl(namespace, self.jointAnkle), query=True, worldSpace=True,
                            translation=True)

        startMV = om2.MVector(startPos[0], startPos[1], startPos[2])
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        endMV = om2.MVector(endPos[0], endPos[1], endPos[2])

        start_endV = endMV - startMV

        start_midV = midMV - startMV
        dot = start_endV * start_midV

        # check if joints are totally in line
        alignCheck = start_endV.normal() * start_midV.normal()
        if alignCheck >= 0.998:
            # joints are almost totally aligned, pv position can wig out
            upperJointMtx = om2.MMatrix(cmds.xform(IkFkTools().getControl(namespace, self.jointThigh),
                                                   query=True,
                                                   worldSpace=True,
                                                   matrix=True))

            pvTransform = om2.MMatrix(self.pvOffset) * upperJointMtx
            pvMTransformMtx = om2.MTransformationMatrix(pvTransform)
            return pvMTransformMtx.translation(om2.MSpace.kWorld)

        if float(start_endV.length()) <= 0:
            return raiseError('Start to end joint distance is zero, check your joint definitions')

        p = float(dot) / float(start_endV.length())
        jointVectorN = start_endV.normal()
        pV = jointVectorN * p

        aV = (start_midV - pV).normalize()
        aV *= self.pvDistance
        V = aV + midMV

        return V

    def getPVDistance(self, namespace):
        """
        Gets the pole vector distance for caching
        :return:
        """
        midPos = cmds.xform(IkFkTools().getControl(namespace, self.jointKnee), query=True, worldSpace=True,
                            rotatePivot=True)
        pvPos = cmds.xform(IkFkTools().getControl(namespace, self.pvControl), query=True, worldSpace=True,
                           rotatePivot=True)
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        pvMV = om2.MVector(pvPos[0], pvPos[1], pvPos[2])

        distance = (pvMV - midMV)

        pvTransform = om2.MMatrix()
        pvMTransformMtx = om2.MTransformationMatrix(pvTransform)
        pvMTransformMtx.setTranslation(pvMV, om2.MSpace.kWorld)
        upperJointMtx = om2.MMatrix(
            cmds.xform(IkFkTools().getControl(namespace, self.jointThigh), query=True, worldSpace=True,
                       matrix=True))
        pvOffset = pvMTransformMtx.asMatrix() * upperJointMtx.inverse()

        return distance.length(), [x for x in pvOffset]

    def getIkFkOffsets(self, namespace):
        keyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(edit=True, state=False)

        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        currentState = cmds.getAttr(ikControlAttr)
        cmds.setAttr(ikControlAttr, self.fkValue)

        for j, c in zip(self.jointKeys, self.fkKeys):
            control = IkFkTools().getControl(namespace, self.__dict__[c])
            joint = IkFkTools().getControl(namespace, self.__dict__[j])
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            resultMatrix = controlMMatrix * jointMMatrix.inverse()
            self.fkControlOffsets[c] = [x for x in resultMatrix]
        cmds.setAttr(ikControlAttr, self.ikValue)
        self.pvDistance, self.pvOffset = self.getPVDistance(namespace)

        for j, c in zip(self.jointKeys[2:], self.ikKeys[1:]):
            optional = c in self.optionalKeys
            control = IkFkTools().getControl(namespace, self.__dict__[c], optional=optional)
            joint = IkFkTools().getControl(namespace, self.__dict__[j], optional=optional)

            if not optional:
                if not control:
                    return raiseError('Ik control not found for match (%s)  (%s)' % (ik, str(control)))
                if not cmds.objExists(control):
                    return raiseError('Ik control not found for match (%s)  (%s)' % (ik, str(control)))
                if not joint:
                    return raiseError('Joint not found for match (%s)  (%s)' % (j, str(control)))
                if not cmds.objExists(joint):
                    return raiseError('Joint not found for match (%s)  (%s)' % (j, str(control)))
            else:
                if not joint:
                    continue
                if not control:
                    continue
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            resultMatrix = controlMMatrix * jointMMatrix.inverse()
            omMatrix = om2.MTransformationMatrix(resultMatrix)
            self.ikControlOffset[c] = [x for x in resultMatrix]
        cmds.setAttr(ikControlAttr, currentState)

        cmds.autoKeyframe(edit=True, state=keyState)

        heelLiftControl = IkFkTools().getControl(namespace, self.__dict__['ikHeelLiftControl'], optional=True)
        toeControl = IkFkTools().getControl(namespace, self.__dict__[self.ikKeys[2]], optional=True)
        # print ('toeControl', toeControl)
        if heelLiftControl and toeControl:
            # get the toe control relative to the toe joint
            # get the ik control relative to the toe joint
            # currently it's relative to the toe control

            # get the matrix between the toe control and the ik
            ikControl = IkFkTools().getControl(namespace, self.__dict__[IK_CONTROL])
            toeControl = IkFkTools().getControl(namespace, self.__dict__[self.ikKeys[2]])
            toeJoint = IkFkTools().getControl(namespace, self.__dict__[self.jointKeys[3]])
            ikControlMMatrix = om2.MMatrix(cmds.xform(ikControl, matrix=True, ws=1, q=True))

            toeJointMMatrix = om2.MMatrix(cmds.xform(toeJoint, matrix=True, ws=1, q=True))
            resultMatrix = ikControlMMatrix * toeJointMMatrix.inverse()

            self.ikHeelLiftControlOffset[IK_CONTROL] = [x for x in resultMatrix]

            # get the delta from the heel joint and the heel lift control
            heelLiftControlMMatrix = om2.MMatrix(cmds.xform(heelLiftControl, matrix=True, ws=1, q=True))
            heelJointMMatrix = om2.MMatrix(cmds.xform(toeControl, matrix=True, ws=1, q=True))
            resultMatrix = heelLiftControlMMatrix * heelJointMMatrix.inverse()

            self.ikHeelLiftControlOffset['ikHeelLiftControl'] = [x for x in resultMatrix]

        # TODO - add in toe/ik control / heel lift control offsets

        return True

    def matchToFK(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        for fk, j in zip(self.fkKeys, self.jointKeys):
            control = IkFkTools().getControl(namespace, self.__dict__.get(fk))
            joint = IkFkTools().getControl(namespace, self.__dict__.get(j))
            jointMtx = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, absolute=True, q=True))
            offsetMtx = om2.MMatrix(self.fkControlOffsets[fk])
            fkResultMtx = offsetMtx * jointMtx
            cmds.xform(control, matrix=fkResultMtx, ws=1)
        cmds.setAttr(ikControlAttr, self.fkValue)

    def matchToIKToe(self, namespace):
        heelControl = IkFkTools().getControl(namespace, self.__dict__['ikHeelLiftControl'], optional=True)
        toeControl = IkFkTools().getControl(namespace, self.__dict__[self.ikKeys[2]], optional=True)
        if not heelControl:
            return cmds.warning('Cannot do this match without a heelLiftControl control')
        if not toeControl:
            return cmds.warning('Cannot do this match without a toeControl control')

        ikControl = IkFkTools().getControl(namespace, self.__dict__.get(self.ikKeys[1], 'unknown'))
        toeControl = IkFkTools().getControl(namespace, self.__dict__.get(self.ikKeys[2], 'unknown'))
        toeJoint = IkFkTools().getControl(namespace, self.__dict__[self.jointKeys[3]])
        heelControl = IkFkTools().getControl(namespace, self.__dict__.get('ikHeelLiftControl', 'unknown'))
        toeJointMtx = om2.MMatrix(cmds.xform(toeJoint, matrix=True, ws=1, absolute=True, q=True))
        ikControlMtx = om2.MMatrix(cmds.xform(ikControl, matrix=True, ws=1, absolute=True, q=True))
        toeControlMtx = om2.MMatrix(cmds.xform(toeControl, matrix=True, ws=1, absolute=True, q=True))
        heelControlMtx = om2.MMatrix(cmds.xform(heelControl, matrix=True, ws=1, absolute=True, q=True))

        # initial ik toe position

        # ik to toe offset
        offsetMtx = om2.MMatrix(self.ikHeelLiftControlOffset[IK_CONTROL])
        ikResultMtx = offsetMtx * toeJointMtx
        self.zeroExtraControls(namespace, skipped=[self.__dict__.get('ikHeelLiftControl', 'unknown')])
        self.zeroControl(toeControl)

        cmds.xform(ikControl, matrix=ikResultMtx, ws=1)
        cmds.xform(heelControl, matrix=heelControlMtx, ws=1)

    def matchToIKMain(self, namespace, toe=False):
        self.matchToIK(namespace)
        if toe:
            self.matchToIKToe(namespace)

    def matchToIK(self, namespace):
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        if not ikControlAttr:
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))
        node, attr = ikControlAttr.split('.')
        if not cmds.attributeQuery(attr, node=node, exists=True):
            return raiseError('Ik Attribute not found (%s)' % str(ikControlAttr))

        pvControl = IkFkTools().getControl(namespace, self.pvControl)

        if not cmds.objExists(pvControl):
            return raiseError('Pole Vector not found for match  (%s)' % str(pvControl))
            # return cmds.error('Pole Vector not found for match  (%s)' % str(pvControl))

        pvRotatePivot = cmds.xform(pvControl, rotatePivot=True, ws=1, absolute=True, q=True)
        pvTranslation = cmds.xform(pvControl, translation=True, ws=1, absolute=True, q=True)
        pvTranslationMV = om2.MVector(pvTranslation[0], pvTranslation[1], pvTranslation[2])
        pvRotatePivotMV = om2.MVector(pvRotatePivot[0], pvRotatePivot[1], pvRotatePivot[2])

        pvPos = self.calculatePVPosition(namespace)

        mtxDict = dict()
        for ik, j in zip(self.ikKeys[1:], self.jointKeys[2:]):
            optional = ik in self.optionalKeys
            control = IkFkTools().getControl(namespace, self.__dict__.get(ik, 'unknown'), optional=optional)
            joint = IkFkTools().getControl(namespace, self.__dict__.get(j), optional=optional)
            if not optional:
                if not control:
                    return raiseError('Ik control not found for match (%s)  (%s)' % (ik, str(control)))
                if not cmds.objExists(control):
                    return raiseError('Ik control not found for match (%s)  (%s)' % (ik, str(control)))
                if not joint:
                    return raiseError('Joint not found for match (%s)  (%s)' % (j, str(control)))
                if not cmds.objExists(joint):
                    return raiseError('Joint not found for match (%s)  (%s)' % (j, str(control)))
            else:
                if not joint:
                    continue
                if not control:
                    continue

            jointMtx = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, absolute=True, q=True))
            offsetMtx = om2.MMatrix(self.ikControlOffset[ik])
            fkResultMtx = offsetMtx * jointMtx
            mtxDict[control] = fkResultMtx

        # zero the exta objects
        self.zeroExtraControls(namespace)

        for control, mtx in mtxDict.items():
            cmds.xform(control, matrix=mtx, ws=1)
        for control, mtx in mtxDict.items():
            cmds.xform(control, matrix=mtx, ws=1)

        cmds.xform(pvControl, translation=pvTranslationMV + (pvPos - pvRotatePivotMV), absolute=True, ws=1)

        cmds.setAttr(ikControlAttr, self.ikValue)

    def preBake(self, namespace, ik, fk):
        """
        before baking, pin transforms to the joints, with the offset so controls align to them
        :param namespace:
        :param ik:
        :return:
        """
        tempNodes, constraints = super(LegIKData, self).preBake(namespace, ik, fk)
        return tempNodes, constraints

    def postBake(self, namespace, ik, fk, tempNodesDict):
        """
        Perform the ik control match + constraint
        figure out pole vector position from input baked nodes
        :param namespace:
        :param ik:
        :return:
        """
        return super(LegIKData, self).postBake(namespace, ik, fk, tempNodesDict)

    def postBakeIK(self, namespace, tempNodesDict):
        keyState = cmds.autoKeyframe(query=True, state=True)

        try:
            cmds.autoKeyframe(state=False)
            self.matchToIKMain(namespace)
        finally:
            cmds.autoKeyframe(state=keyState)

        returnControls = list()
        constraints = list()
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        returnControls.append(ikControl)
        returnControls.append(pvControl)
        if self.ikToeControl:
            ikToeControl = IkFkTools().getControl(namespace, self.ikToeControl)
            ikToeTarget = tempNodesDict['jointToe']
            constraints.append(self.constrain(ikToeTarget, ikToeControl))
            returnControls.append(ikToeControl)

        ikTopTarget = tempNodesDict['jointThigh']
        ikTarget = tempNodesDict['jointAnkle']

        constraints.append(self.constrain(ikTarget, ikControl))
        constraints.append(self.constrain(ikTopTarget, pvControl))
        # self.muteIkAttr(namespace, True)
        # print ('postBakeIK constraints', constraints)
        return returnControls, constraints

    def postBakeFK(self, namespace, tempNodesDict):
        """
        Constrains the fk controls to the baked locators
        :param namespace:
        :param tempNodesDict:
        :return:
        """
        keyState = cmds.autoKeyframe(query=True, state=True)

        try:
            cmds.autoKeyframe(state=False)
            self.matchToFK(namespace)
        finally:
            cmds.autoKeyframe(state=keyState)

        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)

        constraints = list()
        controls = list()
        for j, fk in zip(self.jointKeys, self.fkKeys):
            control = IkFkTools().getControl(namespace, self.__dict__.get(fk))
            joint = tempNodesDict.get(j)
            skipT = IkFkTools().funcs.getAvailableTranslates(control)
            skipR = IkFkTools().funcs.getAvailableRotates(control)
            constraints.append(cmds.parentConstraint(joint, control,
                                                     skipTranslate=[x.split('translate')[-1] for x in skipT],
                                                     skipRotate=[x.split('rotate')[-1] for x in skipR],
                                                     maintainOffset=True)[0])
            controls.append(control)
        cmds.setAttr(ikControlAttr, self.fkValue)
        # print ('postBakeFK constraints', constraints)
        # self.muteIkAttr(namespace, True)
        return controls, constraints

    def getFkBakeTargets(self, namespace):
        fkControlThigh = IkFkTools().getControl(namespace, self.fkControlThigh)
        fkControlKnee = IkFkTools().getControl(namespace, self.fkControlKnee)
        fkControlAnkle = IkFkTools().getControl(namespace, self.fkControlAnkle)
        fkControlToe = IkFkTools().getControl(namespace, self.fkControlToe)
        return [fkControlThigh, fkControlKnee, fkControlAnkle, fkControlToe]

    def getIkBakeTargets(self, namespace):
        ikControl = IkFkTools().getControl(namespace, self.ikControl)
        ikToeControl = IkFkTools().getControl(namespace, self.ikToeControl)
        pvControl = IkFkTools().getControl(namespace, self.pvControl)
        return [ikControl, ikToeControl, pvControl]

    def mirrorControls(self, char, namespace):
        super(LegIKData, self).mirrorControls(char, namespace)

    def getCurrentState(self, namespace):
        """
        Gets the current state of the limb
        :param namespace:
        :return: True if in IK
        """
        ikControlAttr = IkFkTools().getControl(namespace, self.ikAttr)
        return cmds.getAttr(ikControlAttr) == self.ikValue


class IkFkData(object):
    ikTypes = {'arm': TwoBoneIKData,
               'leg': LegIKData}

    def __init__(self):
        self.limbs = dict()
        self.sideA = '_L_'
        self.sideB = '_R_'
        # TODO - get sides from character data instead
        self.lockIKlimbs = dict()

        self.lockFKlimbs = dict()
        self.FKlimbs = dict()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def setUnmodified(self):
        for limb in self.limbs.values():
            limb.setUnModified()

    def isModified(self):
        for limb in self.limbs.values():
            if limb.__dict__.get('__modified', False):
                return True
        return False

    def findLockIKLimb(self, sel, assetTag):
        # print ('assetTag', assetTag)
        for key, data in self.__dict__.get(assetTag, dict()).items():
            # print('key', key)
            for v in data.values():
                # print ('v', v)
                for s in sel:
                    if s == v:
                        return self.__dict__[assetTag][key], key
        return None, None

    def addLimb(self, name, ikType, namespace):
        self.limbs[name] = self.ikTypes.get(ikType.lower())(namespace)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict['limbs'] = {k: v.toJson() for k, v in self.limbs.items()}
        returnDict['data'] = {k: self.__dict__[k] for k in self.__dict__.keys() if k not in returnDict.keys()}
        return returnDict

    def fromJson(self, data, namespace=str()):
        rawJsonData = json.load(open(data))
        for limb, data in rawJsonData.get('limbs').items():
            self.addLimb(limb, data.get('limbType', 'arm'), namespace)
            for k, v in data.items():
                self.limbs[limb].__dict__[k] = v
            self.limbs[limb].enforceKeyOrder()
        data = rawJsonData.get('data', dict())
        for k, v in data.items():
            self.__dict__[k] = v


class IKFK_SetupUI(QMainWindow):
    def __init__(self):
        super(IKFK_SetupUI, self).__init__(parent=getMainWindow())
        self.setObjectName('IKFK_SetupUI')
        self.ikFkData = IkFkData()
        self.rigName = str()
        self.namespace = str()
        self.currentLimb = str()
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbIKFK Setup Tool :: v%s' % IkFkTools.version)

        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        menu = self.menuBar()
        '''
        edit_menu = menu.addMenu('&File')
        load_action = QAction('Load data for current rig', self)
        load_action.setShortcut('Ctrl+C')
        edit_menu.addAction(load_action)
        load_action.triggered.connect(self.getCurrentRig)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        edit_menu.addAction(save_action)
        save_action.triggered.connect(self.save)
        '''
        # 2 bone ik widget
        self.limbStackedWidget = QStackedWidget()
        self.blankWidget = BlankWidget()
        self.limbStackedWidget.addWidget(self.blankWidget)
        self.limbStackedWidget.setCurrentWidget(self.blankWidget)
        # all existing ik widget
        self.existingIkLayout = QVBoxLayout()
        self.existingIkLayout.setAlignment(Qt.AlignTop)
        self.rigIKFKListWidget = QTreeSingleViewWidget(label='Existing IK Definitions')
        self.existingIkLayout.addWidget(self.rigIKFKListWidget)
        self.limbUpdateWidget = LimbUpdateWidget(self)
        self.existingIkLayout.addWidget(self.limbUpdateWidget)
        # cuurent rig label
        self.currentRigLabel = QLabel('Current Rig ::')
        self.currentRigNameLabel = QLabel('None')
        self.rigLayout = QVBoxLayout()
        self.rigLabelLayout = QHBoxLayout()
        self.rigLabelLayout.addWidget(self.currentRigLabel)
        self.rigLabelLayout.addWidget(self.currentRigNameLabel)
        # self.rigLayout.addStretch()

        # test buttons layout
        self.mainTestWidget = QWidget()
        self.testMainLayout = QHBoxLayout()
        self.mainTestWidget.setLayout(self.testMainLayout)
        self.testMainLayout.setContentsMargins(0, 0, 0, 0)
        self.testLayout = QVBoxLayout()
        self.testLayout.setContentsMargins(0, 0, 0, 0)
        self.testSubLayout = QHBoxLayout()
        self.testSubLayout.setContentsMargins(0, 0, 0, 0)
        self.testLayout.setSpacing(0)
        self.testSubLayout.setSpacing(0)
        self.testMainLayout.addLayout(self.testLayout)
        self.testLayout.addLayout(self.testSubLayout)
        self.testFkButton = QPushButton('Test set to FK')
        self.testIkButton = QPushButton('Test set to IK')
        self.cacheButton = QPushButton('Cache Limb Offsets')
        self.cacheHelpButton = HelpButton()
        self.cacheHelpButton.clicked.connect(self.showCacheHelp)
        self.cacheButton.clicked.connect(self.updateCurrent)
        self.testMainLayout.addWidget(self.cacheHelpButton)
        self.testSubLayout.addWidget(self.testFkButton)
        self.testSubLayout.addWidget(self.testIkButton)
        self.testLayout.addWidget(self.cacheButton)
        self.testFkButton.clicked.connect(self.testSetFk)
        self.testIkButton.clicked.connect(self.testSetIk)

        self.saveButton = SimpleIconButton(text='Save')
        self.saveButton.clicked.connect(self.save)
        self.existingIkLayout.addWidget(self.saveButton)
        self.main_layout.addLayout(self.rigLayout)

        self.rigLayout.addLayout(self.rigLabelLayout)
        self.rigLayout.addLayout(self.existingIkLayout)
        self.rightLayout = QVBoxLayout()
        self.rightLayout.addWidget(self.mainTestWidget)
        self.rightLayout.addWidget(self.limbStackedWidget)
        self.main_layout.addLayout(self.rightLayout)

        self.rigIKFKListWidget.pressedSignal.connect(self.selectLimb)
        self.rigIKFKListWidget.itemChangedSignal.connect(self.renameLimb)
        self.limbUpdateWidget.addNewSignal.connect(self.addNewLimb)
        self.limbUpdateWidget.enableMainWidgetSignal.connect(self.toggleEnabledState)
        self.limbUpdateWidget.mirrorSignal.connect(self.mirrorLimb)
        self.limbUpdateWidget.sideUpdateSignal.connect(self.getSideChangedSignal)
        self.limbUpdateWidget.removeButton.clicked.connect(self.remove)
        # self.limbUpdateWidget.mirrorButton.clicked.connect(self.mirrorLimb)
        self.limbUpdateWidget.updateButton.clicked.connect(self.updateCurrent)
        self.limbUpdateWidget.updateAllButton.clicked.connect(self.updateAll)

        self.resize(self.sizeHint())

        # check for selecction
        self.pleaseSelect = None
        self.getCurrentRig()
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.updateUI], protected=False)

    def updateUI(self):
        if not self.rigName:
            self.getCurrentRig()

    def setEnableUI(self, state):
        if state:
            if self.pleaseSelect:
                try:
                    self.pleaseSelect.close()
                    self.pleaseSelect.deleteLater()
                except:
                    pass
        self.limbStackedWidget.setEnabled(state)
        self.rigIKFKListWidget.setEnabled(state)
        self.mainTestWidget.setEnabled(state)
        self.limbUpdateWidget.setEnabled(state)
        self.saveButton.setEnabled(state)

    def showCacheHelp(self):
        helpWidget = InfoPromptWidget(title='Cache Offset Help',
                                      buttonText='Ok',
                                      imagePath=IkFkTools().helpPath,
                                      error=False,
                                      image=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpImage'],
                                      gif=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelpIsGif'],
                                      helpString=maya.stringTable['y_tb_IkFkTools.CacheOffsetHelp'])

    @Slot()
    def getSideChangedSignal(self, sideA, sideB):
        self.ikFkData.sideA = sideA
        self.ikFkData.sideB = sideB

    @Slot()
    def toggleEnabledState(self, state):
        self.main_widget.setEnabled(state)
        self.limbUpdateWidget.dialog.setEnabled(True)

    @Slot()
    def selectLimb(self, inputData):
        self.currentLimb = inputData
        if not inputData:
            self.limbStackedWidget.setDisabled(True)
            return
        self.limbStackedWidget.setDisabled(False)

        widget = self.ikFkData.limbs[self.currentLimb].limbWidget
        self.limbStackedWidget.addWidget(widget)
        self.limbStackedWidget.setCurrentWidget(widget)
        widget.refresh()

    @Slot()
    def renameLimb(self, inputData):
        self.ikFkData.limbs[inputData] = self.ikFkData.limbs.pop(self.currentLimb)

    @Slot()
    def addNewLimb(self, inputData, ikType):
        if inputData not in self.ikFkData.limbs.keys():
            self.ikFkData.addLimb(inputData, ikType.lower(), self.namespace)
            self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())
            self.currentLimb = inputData
            self.limbStackedWidget.addWidget(self.ikFkData.limbs[self.currentLimb].limbWidget)
            self.selectLimb(self.currentLimb)
            self.rigIKFKListWidget.selectItem(self.currentLimb)

    def remove(self):
        if not self.currentLimb:
            raiseError('No limb selected to remove')
        self.ikFkData.limbs.pop(self.currentLimb)
        self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())
        self.limbStackedWidget.setCurrentWidget(self.blankWidget)
        self.currentLimb = str()

    @Slot()
    def mirrorLimb(self, inputData):
        # TODO - probably move this to the main tool class
        CharacterTool = IkFkTools().allTools.tools['CharacterTool']
        MirrorTools = IkFkTools().allTools.tools['MirrorTools']
        CharacterTool.getAllCharacters()
        # self.currentNamespace
        char = CharacterTool.allCharacters[self.rigName]

        '''
        CharacterTool = IkFkTools().allTools.tools['CharacterTool']
        MirrorTools = IkFkTools().allTools.tools['MirrorTools']
        CharacterTool.getAllCharacters()
        # self.currentNamespace
        IkFkTools().loadDataCharacter(self.cls.rigName)
        char = CharacterTool.allCharacters[self.cls.rigName]
        defaultName = MirrorTools.getMirrorForControlFromCharacter(char, self.cls.currentLimb)
        '''
        self.ikFkData.limbs[inputData] = self.ikFkData.limbs[self.currentLimb].__class__(self.namespace)
        for k, v in self.ikFkData.limbs[self.currentLimb].__dict__.items():
            if k == 'limbWidget':
                continue
            self.ikFkData.limbs[inputData].__dict__[k] = v

        self.ikFkData.limbs[inputData].mirrorControls(char, self.namespace)
        self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())
        self.rigIKFKListWidget.selectItem(inputData)
        self.selectLimb(inputData)

    def updateCurrent(self, suppressSuccess=False):
        if self.currentLimb not in self.ikFkData.limbs.keys():
            return cmds.warning('Current limb not found in limb data')
        status = self.ikFkData.limbs[self.currentLimb].getIkFkOffsets(self.namespace)
        if status and not suppressSuccess:
            raiseOk('Updated current limb offsets %s' % self.currentLimb)

    def updateAll(self):
        status = False
        for key, limb in self.ikFkData.limbs.items():
            self.selectLimb(key)
            self.updateCurrent(suppressSuccess=True)
        if status:
            raiseOk('Updated all limb offsets')
        # self.rigIKFKListWidget.proxyModel.select(0, QItemSelectionModel.Select)
        self.rigIKFKListWidget.selectItem(key)
        # item = self.rigIKFKListWidget.model.itemFromIndex(self.proxyModel.mapToSource(index))

    def getCurrentRig(self):
        self.rigName, refState, self.namespace = IkFkTools().getCurrentRig()

        # print ('IK getCurrentRig', self.rigName, refState, self.namespace)
        if self.rigName:
            self.setEnableUI(True)
        else:
            self.setEnableUI(False)
            return
        CharacterTool = IkFkTools().allTools.tools['CharacterTool']
        CharacterTool.getAllCharacters()
        char = CharacterTool.getCharacterByName(self.rigName, openUI=True)
        IkFkTools().saveRigFileIfNew(self.rigName)

        self.currentRigNameLabel.setText(self.rigName)
        self.ikFkData = IkFkData()
        self.ikFkData.fromJson(os.path.join(IkFkTools().ikfkDir, self.rigName + '.json'), namespace=self.namespace)
        self.ikFkData.setUnmodified()
        self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())
        self.limbUpdateWidget.sideA.setText(self.ikFkData.__dict__.get('sideA', '_L_'))
        self.limbUpdateWidget.sideB.setText(self.ikFkData.__dict__.get('sideB', '_L_'))

    def save(self):
        dataFile = os.path.join(IkFkTools().ikfkDir, self.rigName + '.json')
        data = self.ikFkData.toJson()
        IkFkTools().saveJsonFile(dataFile, json.loads(data))
        if self.rigName in IkFkTools().loadedIkFkData.keys():
            IkFkTools().loadedIkFkData.pop(self.rigName)
        self.ikFkData.setUnmodified()

    """
    Test functions
    """

    def matchIkToLift(self):
        self.ikFkData.limbs[self.currentLimb].matchToIKToe(self.namespace)

    def testSetFk(self):
        keyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(edit=True, state=False)

        self.ikFkData.limbs[self.currentLimb].matchToFK(self.namespace)
        cmds.autoKeyframe(edit=True, state=keyState)

    def testSetIk(self):
        keyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(edit=True, state=False)

        self.ikFkData.limbs[self.currentLimb].matchToIKMain(self.namespace)
        cmds.autoKeyframe(edit=True, state=keyState)

    def closeEvent(self, event):
        msg = QMessageBox()
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Overwrite existing data?")
        msg.setWindowTitle("Existing file warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if self.ikFkData.isModified():
            quit_msg = "You have unsaved changes, are you sure want to close"
            reply = QMessageBox.question(self, 'Message',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Clean up the script job stuff prior to closing the dialog.
                # cmds.scriptJob(kill=self.SCRIPT_JOB_NUMBER, force=True)
                super(IKFK_SetupUI, self).closeEvent(event)

                cmds.scriptJob(kill=self.selectionChangedScriptJob)

                event.accept()
            else:
                event.ignore()


class BlankWidget(QWidget):
    def __init__(self):
        super(BlankWidget, self).__init__()

        self.mainLayout = QVBoxLayout()
        self.setObjectName('BlankWidget')
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(QLabel('Add a new entry using the "Add" button on the left'))
        self.mainLayout.addWidget(QLabel('or load the existing data from the menubar'))
        self.mainLayout.addStretch()


class LimbUpdateWidget(QWidget):
    addNewSignal = Signal(str, str)
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)
    sideUpdateSignal = Signal(str, str)

    def __init__(self, cls):
        super(LimbUpdateWidget, self).__init__()
        self.cls = cls
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
        self.updateButton = QPushButton('Cache Offsets')
        self.updateAllButton = QPushButton('Cache All Limb Offsets')

        self.mainLayout.addLayout(self.addRemoveLayout)
        self.addRemoveLayout.addWidget(self.addButton)
        self.addRemoveLayout.addWidget(self.removeButton)
        self.mainLayout.addWidget(self.mirrorButton)
        # self.mirrorLayout.addWidget(self.sideLabel)
        # self.mirrorLayout.addWidget(self.sideA)
        # self.mirrorLayout.addWidget(self.sideB)
        self.addRemoveLayout.addWidget(self.mirrorButton)

        self.mainLayout.addLayout(self.mirrorLayout)
        # self.mainLayout.addWidget(self.updateButton)
        self.mainLayout.addWidget(self.updateAllButton)

        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)
        self.mirrorButton.clicked.connect(self.mirror)
        self.sideA.textEdited.connect(self.sideUpdated)
        self.sideB.textEdited.connect(self.sideUpdated)
        self.addButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddNewHelp'])
        self.mirrorButton.setToolTip(maya.stringTable['y_tb_IkFkTools.MirrorLimb'])
        self.removeButton.setToolTip(maya.stringTable['y_tb_IkFkTools.RemoveLimb'])
        self.updateAllButton.setToolTip(maya.stringTable['y_tb_IkFkTools.CacheOffsetAll'])

    def sideUpdated(self):
        self.sideUpdateSignal.emit(self.sideA.text(), self.sideB.text())

    def addNew(self):
        sel = cmds.ls(sl=True)
        if not sel:
            defaultName = 'RENAME_ME'
        else:
            defaultName = sel[0].split(':', 1)[-1]
        self.dialog = TextInputWidget(title='Add new limb data', label='Enter Name', buttonText="Save",
                                      default=defaultName,
                                      helpString=maya.stringTable['y_tb_IkFkTools.AddNewHelp'],
                                      combo=['Arm', 'Leg'],
                                      parent=self.cls)
        self.dialog.comboBox.setFixedWidth(65 * dpiScale())
        self.dialog.resize(self.dialog.sizeHint().width() + 100, self.dialog.sizeHint().height())

        self.enableMainWidgetSignal.emit(False)
        self.dialog.acceptedComboSignal.connect(self.getAddNewSignal)
        self.dialog.rejectedSignal.connect(self.enableMainWidget)

    def enableMainWidget(self):
        self.enableMainWidgetSignal.emit(True)

    def getAddNewSignal(self, inputData, ikType):
        self.addNewSignal.emit(inputData, ikType)

    def mirror(self):
        if not self.cls.currentLimb:
            return raiseError(maya.stringTable['y_tb_IkFkTools.NoCurrentLimb'], title='Cannot mirror limb')
        CharacterTool = IkFkTools().allTools.tools['CharacterTool']
        MirrorTools = IkFkTools().allTools.tools['MirrorTools']
        CharacterTool.getAllCharacters()
        # self.currentNamespace
        IkFkTools().loadDataCharacter(self.cls.rigName)
        char = CharacterTool.getCharacterByName(self.cls.rigName, openUI=True)
        if not char:
            raiseError('No valid character for this rig', title='Mirror failed')
            CharacterTool.toolBoxUI()
            return
        defaultName = MirrorTools.getMirrorForControlFromCharacter(char, self.cls.currentLimb)
        # print ('default name', defaultName)
        if cmds.objExists(self.cls.namespace + ':' + defaultName):
            self.getMirrorSignal(defaultName)
            return
        self.dialog = TextInputWidget(title='Mirror limb data', label='Enter Name', buttonText="Save",
                                      default=defaultName,
                                      parent=self.cls)
        self.dialog.show()
        # self.dialog.resize(self.dialog.sizeHint().width() + 100, self.dialog.sizeHint().height())
        self.enableMainWidgetSignal.emit(False)
        self.dialog.acceptedSignal.connect(self.getMirrorSignal)
        self.dialog.rejectedSignal.connect(self.enableMainWidget)

    def getMirrorSignal(self, inputData):
        self.mirrorSignal.emit(inputData)


class LimbWidget(QWidget):
    editedSignal = Signal(dict)

    def __init__(self, cls, namespace):
        super(LimbWidget, self).__init__(parent=getMainWindow())
        self.cls = cls
        self.namespace = namespace
        self.key = None
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.ikAttrWidget = ChannelSelectLineEditEnforced(key='ikAttr',
                                                          text='Attribute',
                                                          tooltip='Pick attribute to control ik blend.',
                                                          placeholderTest='enter condition attribute',
                                                          stripNamespace=False,
                                                          baseNamespace=self.namespace)
        self.ikAttrWidget.lineEdit.setFixedWidth(200 * dpiScale())
        self.ikValuesLayout = QHBoxLayout()
        self.ikValueWidget = intFieldWidget(key='ikValue',
                                            optionVar=None, defaultValue=0, label='IK value', minimum=-100, maximum=100,
                                            step=1)

        self.fkValueWidget = intFieldWidget(key='fkValue',
                                            optionVar=None, defaultValue=1, label='FK value', minimum=-100, maximum=100,
                                            step=1)

        # ik value widget (int/bool)
        self.ikControlLabel = QLabel('IK Controls')
        self.fkControlLabel = QLabel('FK Controls')
        self.resultJointsLabel = QLabel('Result Joints')
        self.pickFkButton = QPushButton('Add From Selection')
        self.pickFkButton.clicked.connect(self.pickFK)

        self.pickIKButton = QPushButton('Add From Selection')
        self.pickIKButton.clicked.connect(self.pickIK)
        self.pickJointsButton = QPushButton('Add From Selection')
        self.pickJointsButton.clicked.connect(self.pickJoints)

        self.pickFkButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelection'])
        self.pickIKButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelectionIK'])
        self.pickJointsButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelection'])

        self.skeletonUpper = ObjectSelectLineEditEnforced(key='jointUp',
                                                          label='Arm Joint',
                                                          hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointUp'],
                                                          stripNamespace=True,
                                                          baseNamespace=self.namespace)

        self.skeletonMid = ObjectSelectLineEditEnforced(key='jointMid',
                                                        label='Elbow Joint',
                                                        hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointMid'],
                                                        stripNamespace=True,
                                                        baseNamespace=self.namespace)
        self.skeletonEnd = ObjectSelectLineEditEnforced(key='jointEnd',
                                                        label='Wrist Joint',
                                                        hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointEnd'],
                                                        stripNamespace=True,
                                                        baseNamespace=self.namespace)

        self.fkUpper = ObjectSelectLineEditEnforced(key='fkControlUp',
                                                    label='FK Arm',
                                                    hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkUp'],
                                                    stripNamespace=True,
                                                    baseNamespace=self.namespace)
        self.fkMid = ObjectSelectLineEditEnforced(key='fkControlMid',
                                                  label='FK Elbow',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkMid'],
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)
        self.fkEnd = ObjectSelectLineEditEnforced(key='fkControlEnd',
                                                  label='FK Wrist',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkEnd'],
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)

        self.ikPV = ObjectSelectLineEditEnforced(key='pvControl',
                                                 label='Pole Vector',
                                                 hint=maya.stringTable['y_tb_IkFkTools.AddSinglePoleVector'],
                                                 stripNamespace=True,
                                                 baseNamespace=self.namespace
                                                 )
        self.ikEnd = ObjectSelectLineEditEnforced(key='ikControl',
                                                  label='IK Hand Control',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleIkControl'],
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)

        self.zeroControlListWidget = ZeroControlWidget(key='ikZeroControl', namespace=self.namespace)
        self.zeroAttributeListWidget = ZeroControlWidget(key='ikZeroAttribute', namespace=self.namespace, channels=True)

        self.objSelectWidgets = [self.skeletonUpper,
                                 self.skeletonMid,
                                 self.skeletonEnd,
                                 self.fkUpper,
                                 self.fkMid,
                                 self.fkEnd,
                                 self.ikPV,
                                 self.ikEnd,
                                 self.zeroControlListWidget,
                                 self.zeroAttributeListWidget,
                                 self.ikAttrWidget,
                                 self.ikValueWidget,
                                 self.fkValueWidget,
                                 self.zeroControlListWidget,
                                 self.zeroAttributeListWidget,
                                 ]
        for wd in self.objSelectWidgets:
            wd.editedSignalKey.connect(self.updateData)

        self.attrFrame = QGroupBox('Ik Attributes')
        # self.attrFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.jointFrame = QGroupBox('Result Joints')
        # self.jointFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.fkFrame = QGroupBox('Fk Controls')
        # self.fkFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.ikFrame = QGroupBox('Ik Controls')
        self.ikZeroControlsFrame = QGroupBox('IK Zeroed Controls')
        self.ikZeroAttrFrame = QGroupBox('IK Zeroed Attributes')
        # self.ikFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.attrLayout = QVBoxLayout()
        self.jointLayout = QVBoxLayout()
        self.fkLayout = QVBoxLayout()
        self.ikLayout = QVBoxLayout()
        self.ikZeroLayout = QVBoxLayout()
        self.ikZeroAttrLayout = QVBoxLayout()
        self.attrLayout.setContentsMargins(2, 14, 2, 2)
        self.jointLayout.setContentsMargins(2, 14, 2, 2)
        self.fkLayout.setContentsMargins(2, 14, 2, 2)
        self.ikLayout.setContentsMargins(2, 14, 2, 2)
        self.ikZeroLayout.setContentsMargins(2, 14, 2, 2)
        self.ikZeroAttrLayout.setContentsMargins(2, 14, 2, 2)

        self.attrLayout.setSpacing(0)
        self.jointLayout.setSpacing(0)
        self.fkLayout.setSpacing(0)
        self.ikLayout.setSpacing(0)
        self.ikZeroLayout.setSpacing(0)
        self.ikZeroAttrLayout.setSpacing(0)

        self.mainLayout.addWidget(self.attrFrame)
        self.mainLayout.addWidget(self.jointFrame)
        self.mainLayout.addWidget(self.fkFrame)
        self.mainLayout.addWidget(self.ikFrame)
        self.mainLayout.addWidget(self.ikZeroControlsFrame)
        self.mainLayout.addWidget(self.ikZeroAttrFrame)

        self.attrFrame.setLayout(self.attrLayout)
        self.jointFrame.setLayout(self.jointLayout)
        self.fkFrame.setLayout(self.fkLayout)
        self.ikFrame.setLayout(self.ikLayout)
        self.ikZeroControlsFrame.setLayout(self.ikZeroLayout)
        self.ikZeroAttrFrame.setLayout(self.ikZeroAttrLayout)

        self.attrLayout.addWidget(self.ikAttrWidget)
        self.attrLayout.addLayout(self.ikValuesLayout)
        self.ikValuesLayout.addWidget(self.ikValueWidget)
        self.ikValuesLayout.addWidget(self.fkValueWidget)
        self.attrLayout.addStretch()
        self.fkLayout.addWidget(self.fkUpper)
        self.fkLayout.addWidget(self.fkMid)
        self.fkLayout.addWidget(self.fkEnd)
        self.fkLayout.addWidget(self.pickFkButton)

        self.jointLayout.addWidget(self.skeletonUpper)
        self.jointLayout.addWidget(self.skeletonMid)
        self.jointLayout.addWidget(self.skeletonEnd)
        self.jointLayout.addWidget(self.pickJointsButton)

        self.ikZeroLayout.addWidget(self.zeroControlListWidget)
        self.ikZeroAttrLayout.addWidget(self.zeroAttributeListWidget)

        self.ikLayout.addStretch()
        self.ikLayout.addWidget(self.ikPV)
        self.ikLayout.addWidget(self.ikEnd)
        self.ikLayout.addWidget(self.pickIKButton)

        widgets = [x for x in self.mainLayout.children() if x.__class__.__name__ == 'ObjectSelectLineEdit']
        self.setStyleSheet(getqss.getStyleSheet())

    def refresh(self):
        [wd.blockSignals(True) for wd in self.objSelectWidgets]
        self.skeletonUpper.itemLabel.setText(self.cls.jointUp)
        self.skeletonMid.itemLabel.setText(self.cls.jointMid)
        self.skeletonEnd.itemLabel.setText(self.cls.jointEnd)
        self.fkUpper.itemLabel.setText(self.cls.fkControlUp)
        self.fkMid.itemLabel.setText(self.cls.fkControlMid)
        self.fkEnd.itemLabel.setText(self.cls.fkControlEnd)
        self.ikPV.itemLabel.setText(self.cls.pvControl)
        self.ikEnd.itemLabel.setText(self.cls.ikControl)
        self.ikAttrWidget.lineEdit.setText(self.cls.ikAttr)
        self.ikValueWidget.spinBox.setValue(self.cls.ikValue)
        self.fkValueWidget.spinBox.setValue(self.cls.fkValue)

        self.zeroControlListWidget.setItems(self.cls.ikZeroControl)
        self.zeroAttributeListWidget.setItems(self.cls.ikZeroAttribute)

        self.skeletonUpper.validateText()
        self.skeletonMid.validateText()
        self.skeletonEnd.validateText()
        self.fkUpper.validateText()
        self.fkMid.validateText()
        self.fkEnd.validateText()
        self.ikPV.validateText()
        self.ikEnd.validateText()
        self.ikAttrWidget.validateText()
        [wd.blockSignals(False) for wd in self.objSelectWidgets]

    def updateData(self, key, value):
        self.cls.__setattr__(key, value)

    def pickFK(self):
        sel = cmds.ls(sl=True, type='transform')
        # print (sel)
        if not sel:
            return cmds.warning('No selection')
        sel = IkFkTools().funcs.sortByParents(sel)
        # print (sel)
        if not len(sel) == 3:
            return cmds.warning('Please select all three fk controls')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.fkUpper.itemLabel.setText(sel[0])
        self.fkMid.itemLabel.setText(sel[1])
        self.fkEnd.itemLabel.setText(sel[2])

    def pickIK(self):
        sel = cmds.ls(sl=True, type='transform')
        if not len(sel) == 2:
            return cmds.warning('Please select the pole vector and ik controls')
        sel = [s.split(':', 1)[-1] for s in sel]
        pvIndex = 0
        controlIndex = 1
        pvNames = maya.stringTable['y_tb_IkFkTools.PoleVectorNames'].split('___')
        for s in sel:
            for name in pvNames:
                if name.lower() in s.lower():
                    pvIndex = sel.index(s)
                    controlIndex = not pvIndex
        self.ikPV.itemLabel.setText(sel[pvIndex])
        self.ikEnd.itemLabel.setText(sel[controlIndex])

    def pickJoints(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        sel = [str(x) for x in IkFkTools().funcs.sortByParents(sel)]
        curves = cmds.keyframe(sel, query=True, attribute=('tx', 'ty', 'tz', 'rx', 'ry', 'rz'))
        if curves:
            cmds.warning('Selected joints are keyed, are you sure they are the ik result joints or bind joints?')
        if not all(cmds.nodeType(c) == 'joint' for c in sel):
            cmds.warning(
                'Not all objects in the selection are joints, are you sure they are the result joints or bind joints?')
        if not len(sel) == 3:
            return cmds.warning('Please select all three joints')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.skeletonUpper.itemLabel.setText(sel[0])
        self.skeletonMid.itemLabel.setText(sel[1])
        self.skeletonEnd.itemLabel.setText(sel[2])


class LegWidget(QWidget):
    editedSignal = Signal(dict)

    def __init__(self, cls, namespace):
        super(LegWidget, self).__init__(parent=getMainWindow())
        self.cls = cls
        self.namespace = namespace
        self.key = None
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.ikAttrWidget = ChannelSelectLineEditEnforced(key='ikAttr',
                                                          text='Attribute',
                                                          tooltip=maya.stringTable['y_tb_IkFkTools.PickIkAttr'],
                                                          placeholderTest='enter condition attribute',
                                                          baseNamespace=self.namespace)
        self.ikAttrWidget.lineEdit.setFixedWidth(200 * dpiScale())
        self.ikValuesLayout = QHBoxLayout()
        self.ikValueWidget = intFieldWidget(key='ikValue',
                                            optionVar=None, defaultValue=0, label='IK value', minimum=-100, maximum=100,
                                            step=1)

        self.fkValueWidget = intFieldWidget(key='fkValue',
                                            optionVar=None, defaultValue=1, label='FK value', minimum=-100, maximum=100,
                                            step=1)

        # ik value widget (int/bool)
        self.pickFkButton = QPushButton('Add From Selection')
        self.pickFkButton.clicked.connect(self.pickFK)
        self.pickIKButton = QPushButton('Add From Selection')
        self.pickIKButton.clicked.connect(self.pickIK)
        self.pickJointsButton = QPushButton('Add From Selection')
        self.pickJointsButton.clicked.connect(self.pickJoints)

        self.pickFkButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelection'])
        self.pickIKButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelectionIK'])
        self.pickJointsButton.setToolTip(maya.stringTable['y_tb_IkFkTools.AddSelection'])

        self.skeletonThigh = ObjectSelectLineEditEnforced(key='jointThigh',
                                                          label='Thigh Joint',
                                                          hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointThigh'],
                                                          stripNamespace=True,
                                                          baseNamespace=self.namespace)
        self.skeletonKnee = ObjectSelectLineEditEnforced(key='jointKnee',
                                                         label='Knee Joint',
                                                         hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointKnee'],
                                                         stripNamespace=True,
                                                         baseNamespace=self.namespace)
        self.skeletonAnkle = ObjectSelectLineEditEnforced(key='jointAnkle',
                                                          label='Ankle Joint',
                                                          hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointAnkle'],
                                                          stripNamespace=True,
                                                          baseNamespace=self.namespace)
        self.skeletonToe = ObjectSelectLineEditEnforced(key='jointToe',
                                                        label='Toe Joint',
                                                        hint=maya.stringTable['y_tb_IkFkTools.AddSingleJointToe'],
                                                        stripNamespace=True,
                                                        baseNamespace=self.namespace)

        self.fkThigh = ObjectSelectLineEditEnforced(key='fkControlThigh',
                                                    label='Thigh FK',
                                                    hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkThigh'],
                                                    stripNamespace=True,
                                                    baseNamespace=self.namespace)
        self.fkKnee = ObjectSelectLineEditEnforced(key='fkControlKnee',
                                                   label='FK Knee',
                                                   hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkKnee'],
                                                   stripNamespace=True,
                                                   baseNamespace=self.namespace)
        self.fkAnkle = ObjectSelectLineEditEnforced(key='fkControlAnkle',
                                                    label='FK Ankle',
                                                    hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkAnkle'],
                                                    stripNamespace=True,
                                                    baseNamespace=self.namespace)
        self.fkToe = ObjectSelectLineEditEnforced(key='fkControlToe',
                                                  label='FK Toe',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleFkToe'],
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)

        self.ikPV = ObjectSelectLineEditEnforced(key='pvControl',
                                                 label='Pole Vector',
                                                 hint=maya.stringTable['y_tb_IkFkTools.AddSingleKneePoleVector'],
                                                 stripNamespace=True,
                                                 baseNamespace=self.namespace)
        self.ikEnd = ObjectSelectLineEditEnforced(key='ikControl',
                                                  label='IK Control',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleIkFootControl'],
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)
        self.ikToe = ObjectSelectLineEditEnforced(key='ikToeControl',
                                                  label='IK Toe Control',
                                                  hint=maya.stringTable['y_tb_IkFkTools.AddSingleIkToeControl'],
                                                  placeholderTest='optional control',
                                                  stripNamespace=True,
                                                  baseNamespace=self.namespace)

        self.ikHeelLift = ObjectSelectLineEditEnforced(key='ikHeelLiftControl',
                                                       label='IK Heel Lift Control',
                                                       hint=maya.stringTable['y_tb_IkFkTools.AddSingleIkToeControl'],
                                                       placeholderTest='optional control',
                                                       stripNamespace=True,
                                                       baseNamespace=self.namespace)

        self.zeroControlListWidget = ZeroControlWidget(key='ikZeroControl', namespace=self.namespace)
        self.zeroAttributeListWidget = ZeroControlWidget(key='ikZeroAttribute', namespace=self.namespace, channels=True)

        self.widgetsToSendUpdateSignal = [self.skeletonThigh,
                                          self.skeletonKnee,
                                          self.skeletonAnkle,
                                          self.skeletonToe,
                                          self.fkThigh,
                                          self.fkKnee,
                                          self.fkAnkle,
                                          self.fkToe,
                                          self.ikPV,
                                          self.ikEnd,
                                          self.ikToe,
                                          self.ikValueWidget,
                                          self.fkValueWidget,
                                          self.ikAttrWidget,
                                          self.zeroControlListWidget,
                                          self.zeroAttributeListWidget,
                                          self.ikHeelLift
                                          ]
        for x in self.widgetsToSendUpdateSignal:
            x.editedSignalKey.connect(self.updateData)
        # print (max([x.label.sizeHint().width() for x in widgetsToSendUpdateSignal]))

        self.attrFrame = QGroupBox('Ik Attributes')
        # self.attrFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.jointFrame = QGroupBox('Result Joints')
        # self.jointFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.fkFrame = QGroupBox('Fk Controls')
        # self.fkFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.ikFrame = QGroupBox('Ik Controls')
        # self.ikFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.ikZeroControlsFrame = QGroupBox('IK Zeroed Controls')
        self.ikZeroAttrFrame = QGroupBox('IK Zeroed Attributes')

        self.attrLayout = QVBoxLayout()
        self.jointLayout = QVBoxLayout()
        self.fkLayout = QVBoxLayout()
        self.ikLayout = QVBoxLayout()
        self.ikZeroLayout = QVBoxLayout()
        self.ikZeroAttrLayout = QVBoxLayout()

        self.attrLayout.setContentsMargins(2, 14, 2, 2)
        self.jointLayout.setContentsMargins(2, 14, 2, 2)
        self.fkLayout.setContentsMargins(2, 14, 2, 2)
        self.ikLayout.setContentsMargins(2, 14, 2, 2)
        self.ikZeroLayout.setContentsMargins(2, 14, 2, 2)
        self.ikZeroAttrLayout.setContentsMargins(2, 14, 2, 2)

        self.attrLayout.setSpacing(0)
        self.jointLayout.setSpacing(0)
        self.fkLayout.setSpacing(0)
        self.ikLayout.setSpacing(0)
        self.ikZeroLayout.setSpacing(0)
        self.ikZeroAttrLayout.setSpacing(0)

        self.mainLayout.addWidget(self.attrFrame)
        self.mainLayout.addWidget(self.jointFrame)
        self.mainLayout.addWidget(self.fkFrame)
        self.mainLayout.addWidget(self.ikFrame)
        self.mainLayout.addWidget(self.ikZeroControlsFrame)
        self.mainLayout.addWidget(self.ikZeroAttrFrame)

        self.attrFrame.setLayout(self.attrLayout)
        self.jointFrame.setLayout(self.jointLayout)
        self.fkFrame.setLayout(self.fkLayout)
        self.ikFrame.setLayout(self.ikLayout)
        self.ikZeroControlsFrame.setLayout(self.ikZeroLayout)
        self.ikZeroAttrFrame.setLayout(self.ikZeroAttrLayout)

        self.attrLayout.addWidget(self.ikAttrWidget)
        self.attrLayout.addLayout(self.ikValuesLayout)
        self.ikValuesLayout.addWidget(self.ikValueWidget)
        self.ikValuesLayout.addWidget(self.fkValueWidget)
        self.attrLayout.addStretch()
        self.fkLayout.addWidget(self.fkThigh)
        self.fkLayout.addWidget(self.fkKnee)
        self.fkLayout.addWidget(self.fkAnkle)
        self.fkLayout.addWidget(self.fkToe)
        self.fkLayout.addWidget(self.pickFkButton)

        self.jointLayout.addWidget(self.skeletonThigh)
        self.jointLayout.addWidget(self.skeletonKnee)
        self.jointLayout.addWidget(self.skeletonAnkle)
        self.jointLayout.addWidget(self.skeletonToe)
        self.jointLayout.addWidget(self.pickJointsButton)

        self.ikLayout.addStretch()
        self.ikLayout.addWidget(self.ikPV)
        self.ikLayout.addWidget(self.ikEnd)
        self.ikLayout.addWidget(self.ikToe)
        self.ikLayout.addWidget(self.ikHeelLift)
        self.ikLayout.addWidget(self.pickIKButton)

        self.ikZeroLayout.addWidget(self.zeroControlListWidget)
        self.ikZeroAttrLayout.addWidget(self.zeroAttributeListWidget)

        widgets = [x for x in self.mainLayout.children() if x.__class__.__name__ == 'ObjectSelectLineEdit']
        # print ('widgets', widgets)

    def refresh(self):
        [wd.blockSignals(True) for wd in self.widgetsToSendUpdateSignal]
        self.skeletonThigh.itemLabel.setText(self.cls.jointThigh)
        self.skeletonKnee.itemLabel.setText(self.cls.jointKnee)
        self.skeletonAnkle.itemLabel.setText(self.cls.jointAnkle)
        self.skeletonToe.itemLabel.setText(self.cls.jointToe)
        self.fkThigh.itemLabel.setText(self.cls.fkControlThigh)
        self.fkKnee.itemLabel.setText(self.cls.fkControlKnee)
        self.fkAnkle.itemLabel.setText(self.cls.fkControlAnkle)
        self.fkToe.itemLabel.setText(self.cls.fkControlToe)
        self.ikPV.itemLabel.setText(self.cls.pvControl)
        self.ikEnd.itemLabel.setText(self.cls.ikControl)
        self.ikToe.itemLabel.setText(self.cls.ikToeControl)
        self.ikHeelLift.itemLabel.setText(self.cls.ikHeelLiftControl)
        self.ikAttrWidget.lineEdit.setText(self.cls.ikAttr)
        self.ikValueWidget.spinBox.setValue(self.cls.ikValue)
        self.fkValueWidget.spinBox.setValue(self.cls.fkValue)

        self.zeroControlListWidget.setItems(self.cls.ikZeroControl)
        self.zeroAttributeListWidget.setItems(self.cls.ikZeroAttribute)

        self.skeletonThigh.validateText()
        self.skeletonKnee.validateText()
        self.skeletonAnkle.validateText()
        self.skeletonToe.validateText()
        self.fkThigh.validateText()
        self.fkKnee.validateText()
        self.fkAnkle.validateText()
        self.fkToe.validateText()
        self.ikPV.validateText()
        self.ikEnd.validateText()
        self.ikToe.validateText()
        self.ikAttrWidget.validateText()
        [wd.blockSignals(False) for wd in self.widgetsToSendUpdateSignal]

    def updateData(self, key, value):
        self.cls.__dict__[key] = value

    def pickFK(self):
        sel = cmds.ls(sl=True, type='transform')
        # print (sel)
        if not sel:
            return cmds.warning('No selection')
        sel = IkFkTools().funcs.sortByParents(sel)
        # print (sel)
        if not len(sel) == 4:
            return cmds.warning('Please select all four fk controls')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.fkThigh.itemLabel.setText(sel[0])
        self.fkKnee.itemLabel.setText(sel[1])
        self.fkAnkle.itemLabel.setText(sel[2])
        self.fkToe.itemLabel.setText(sel[3])

    def pickIK(self):
        sel = cmds.ls(sl=True, type='transform')
        if not len(sel) >= 2:
            return cmds.warning('Please select the pole vector, ik controls, and optional toe control')
        sel = [s.split(':', 1)[-1] for s in sel]
        pvIndex = 0
        controlIndex = 1
        pvNames = maya.stringTable['y_tb_IkFkTools.PoleVectorNames']
        for s in sel:
            for name in pvNames:
                if name.lower() in s.lower():
                    pvIndex = sel.index(s)
                    controlIndex = not pvIndex
        self.ikPV.itemLabel.setText(sel[pvIndex])
        self.ikEnd.itemLabel.setText(sel[controlIndex])

        if len(sel) == 3:
            self.ikToe.itemLabel.setText(sel[2])

    def pickJoints(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        sel = IkFkTools().funcs.sortByParents(sel)
        curves = cmds.keyframe(sel, query=True, attribute=('tx', 'ty', 'tz', 'rx', 'ry', 'rz'))
        if curves:
            cmds.warning('Selected joints are keyed, are you sure they are the ik result joints or bind joints?')
        if not all(cmds.nodeType(c) == 'joint' for c in sel):
            cmds.warning(
                'Not all objects in the selection are joints, are you sure they are the result joints or bind joints?')
        if not len(sel) == 4:
            return cmds.warning('Please select all three joints')
        sel = [s.split(':', 1)[-1] for s in sel]
        self.skeletonThigh.itemLabel.setText(sel[0])
        self.skeletonKnee.itemLabel.setText(sel[1])
        self.skeletonAnkle.itemLabel.setText(sel[2])
        self.skeletonToe.itemLabel.setText(sel[3])


def raiseInfo(errorMessage, title='No current rig'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              info=True,
                              error=False,
                              # image='curves.png',
                              helpString=errorMessage)
    cmds.warning(errorMessage)
    return prompt


def raiseOk(errorMessage):
    prompt = InfoPromptWidget(title='Success',
                              buttonText='Ok',
                              error=False,
                              # image='curves.png',
                              helpString=errorMessage)
    cmds.warning(errorMessage)
    return prompt


def raiseError(errorMessage, title='Matching Failed'):
    prompt = InfoPromptWidget(title=title,
                              buttonText='Ok',
                              error=True,
                              helpString=errorMessage)
    cmds.error(errorMessage)
    return prompt


class MultiObjectInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal()
    saveSignal = Signal(list, list, str, str)

    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title=str(), info=str(), buttonText=str(),
                 checkBox=None, overlay=False, showCloseButton=True,
                 helpString=None,
                 refName=None,
                 assetTag=None,
                 parentWidget=None,
                 lineEditPlaceholder=list(),
                 parent=getMainWindow()):
        super(MultiObjectInputWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.refName = refName
        self.assetTag = assetTag
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())
        self.checkBox = checkBox

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
        layout = QVBoxLayout()
        lineEditLayout = QVBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = cmds.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(info)

        self.checkBoxWD = QCheckBox()
        self.checkBoxWD.setText(self.checkBox)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)

        self.lineEdits = list()
        self.lineEditPlaceholder = lineEditPlaceholder
        for l in lineEditPlaceholder:
            objLineEdit = ObjectSelectLineEdit(stripNamespace=True, placeholderTest=l)
            # objLineEdit.setFixedWidth(128)
            self.lineEdits.append(objLineEdit.itemLabel)
            lineEditLayout.addWidget(objLineEdit)

        layout.addLayout(lineEditLayout)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        # self.move(getScreenCenter() - self.rect().center())

        self.lineEdits[0].setFocus()

        # self.lineEdit.setFixedWidth(self.lineEdit.fontMetrics().boundingRect(self.lineEdit.text()).width() + 16)

        self.setStyleSheet(
            "MultiObjectInputWidget { "
            "border-radius: 8;"
            "}"
        )

        self.closeButton.setVisible(self.showCloseButton)

        self.show()
        self.resize(self.sizeHint().width() + 36, self.sizeHint().height())
        # self.setFixedSize(400, 64)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(QPainter.CompositionMode_Clear)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
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
        self.saveSignal.emit([lineEdit.text() for lineEdit in self.lineEdits],
                             self.lineEditPlaceholder,
                             self.refName,
                             self.assetTag)
        self.acceptedSignal.emit()
        self.close()

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(MultiObjectInputWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(MultiObjectInputWidget, self).keyPressEvent(event)

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
        super(MultiObjectInputWidget, self).show()


class ZeroControlWidget(QWidget):
    editedSignalKey = Signal(str, list)

    def __init__(self, namespace=str(), key=str(), channels=False):
        super(ZeroControlWidget, self).__init__()
        self.key = key
        self.baseNamespace = namespace
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)

        self.listWidget = ZeroControlList()
        self.addButton = QPushButton("Add selected")
        self.removeButton = QPushButton("Remove selected")

        self.mainLayout.addWidget(self.listWidget)
        self.mainLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.addButton)
        self.buttonLayout.addWidget(self.removeButton)
        self.channels = channels

        self.addButton.clicked.connect(self.addPressed)
        self.removeButton.clicked.connect(self.removePressed)

    def addPressed(self):
        if self.channels:
            sel = self.pickChannels()
        else:
            sel = self.pickObject()
        if not sel:
            return
        self.listWidget.updateItems(sel)
        self.editedSignalKey.emit(self.key, self.listWidget.allItems())

    def pickObject(self):
        # print ('pickObject')
        sel = cmds.ls(sl=True)
        if not sel:
            return list()
        sel = [str(s).split(':', 1)[-1] for s in sel]
        return sel

    def pickChannels(self):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return cmds.warning('no channel selected')
        channels = [self.parseChannel(c) for c in channels]
        return channels

    def parseChannel(self, channel):
        refState = cmds.referenceQuery(channel.split('.')[0], isNodeReferenced=True)

        if refState:
            refNamespace = cmds.referenceQuery(channel.split('.')[0], namespace=True)

            if refNamespace.startswith(':'):
                refNamespace = refNamespace[1:]

            channel = channel.replace(refNamespace, '')
            if channel.startswith(':'):
                channel = channel[1:]
            return channel
        else:
            return channel

    def removePressed(self):

        listItems = self.listWidget.selectedItems()
        if not listItems: return
        for item in listItems:
            self.listWidget.takeItem(self.listWidget.row(item))
        self.editedSignalKey.emit(self.key, self.listWidget.allItems())

    def setItems(self, items):
        if not items:
            return
        self.listWidget.updateItems(items)


class ZeroControlList(QListWidget):
    editedSignalKey = Signal(str, list)

    def __init__(self):
        super(ZeroControlList, self).__init__()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def updateItems(self, items):
        for item in items:
            if item not in self.allItems():
                self.addItem(item)

    def allItems(self):
        return [str(self.item(i).text()) for i in range(self.count())]
