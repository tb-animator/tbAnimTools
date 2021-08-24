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
import maya.api.OpenMaya as om2
from Abstract import *
from tb_UI import *
from copy import deepcopy
import pymel.core.datatypes as dt
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
__author__ = 'tom.bailey'
import abc

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('ikfk'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='tbOpenIkFkCreator',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.showUI()']))
        self.addCommand(self.tb_hkey(name='switch_selection_to_fk',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.matchFKToCurrentPose()']))
        self.addCommand(self.tb_hkey(name='switch_selection_to_ik',
                                     annotation='',
                                     category=self.category,
                                     command=['IkFkTools.matchIKToCurrentPose()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class IKFK(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'IkFkTools'
    hotkeyClass = hotkeys()
    funcs = functions()
    subfolder = 'ikfkData'

    loadedIkFkData = dict()  # store loaded data per session to avoid accessing the disc all the time

    def __new__(cls):
        if IKFK.__instance is None:
            IKFK.__instance = object.__new__(cls)
            IKFK.__instance.initData()
        IKFK.__instance.val = cls.toolName
        return IKFK.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def initData(self):
        super(IKFK, self).initData()
        self.ikfkDir = os.path.normpath(os.path.join(self.dataPath, self.subfolder))
        if not os.path.isdir(self.ikfkDir):
            os.mkdir(self.ikfkDir)

    def optionUI(self):
        return super(IKFK, self).optionUI()

    def showUI(self):
        self.win = IKFK_SetupUI()
        self.win.show()

        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.win.getCurrentRig()

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='IkFk Setup', command='tbOpenIkFkCreator', sourceType='mel', parent=parentMenu)

    def getCurrentRig(self, sel=None):
        refName = None
        mapName = None
        fname = None
        if sel is None:
            sel = cmds.ls(sl=True)
        namespace = str()
        if sel:
            refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)
            if refState:
                # if it is referenced, check against pickwalk library entries
                refName = cmds.referenceQuery(sel[0], filename=True, shortName=True).split('.')[0]
            else:
                # might just be working in the rig file itself
                refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
            if ':' in sel[0]:
                namespace = sel[0].split(':')[0]
        else:
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]

        return refName, namespace  # TODO - fix up data path etc

    def saveRigFileIfNew(self, refname):
        dataFile = os.path.join(self.ikfkDir, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            print ('need to save',)
            ikFkData = IkFkData()
            data = ikFkData.toJson()
            self.saveJsonFile(dataFile, json.loads(data))

    def getIkFkOffsets(self, namespace, data):
        print (namespace, data)
        # set to FK
        # get offsets between joints and fk controls
        ikControlAttr = self.getControl(namespace, data.ikAttr)
        cmds.setAttr(ikControlAttr, data.fkValue)
        for j, c in zip(data.jointKeys, data.fkKeys):
            control = self.getControl(namespace, data.__dict__[c])
            joint = self.getControl(namespace, data.__dict__[j])
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            # print controlMMatrix, jointMMatrix
            resultTFMatrix = om2.MTransformationMatrix(controlMMatrix * jointMMatrix.inverse())
            resultMatrix = controlMMatrix * jointMMatrix.inverse()
            print
            # print resultTFMatrix.translation(om2.MSpace.kWorld)
            data.fkControlOffsets[c] = [x for x in resultMatrix]
        cmds.setAttr(ikControlAttr, data.ikValue)

    def getControl(self, namespace, name):
        if namespace:
            return namespace + ':' + name
        return name

    def loadIkFkData(self, rigName):
        ikFkData = IkFkData()
        ikFkData.fromJson(os.path.join(IKFK().ikfkDir, rigName + '.json'))
        return ikFkData

    def splitSelectionToCharacters(self, sel):
        """
        Returns a dictionary for all characters found in the selection, namespace as key, controls as items
        :param sel:
        :return:
        """
        if not sel:
            return

        # split selection by character
        namespaces = [x.split(':')[0] for x in sel if ':' in x]

        characters = {k: list() for k in namespaces}
        for s in sel:
            splitString = s.split(':')
            if len(splitString) == 1:
                if ('') not in characters.keys():
                    characters[''] = list()
                characters[''].append(s)
                continue
            for ns in namespaces:
                if splitString[0] == ns:
                    characters[ns].append(s)
                    continue
        return characters

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        for key, value in characters.items():
            refname, namespace = self.getCurrentRig([value[0]])
            namespaceToCharDict[namespace] = refname
            if refname not in self.loadedIkFkData.keys():
                ikFkData = self.loadIkFkData(refname)
                self.loadedIkFkData[refname] = ikFkData
                print ('loading from disc')
        return namespaceToCharDict

    def getLimbsToMatchFromSelection(self, sel=None):
        if sel is None:
            sel = cmds.ls(sl=True)
        if not sel:
            return
        characters = self.splitSelectionToCharacters(sel)
        print ('chars', characters)
        namespaceToCharDict = self.loadDataForCharacters(characters)

        limbsToMatch = {c: list() for c in characters.keys()}

        # get the limbs selected
        for char, controls in characters.items():
            for s in controls:
                control = s.split(':')[-1]
                for key, limb in self.loadedIkFkData[namespaceToCharDict[char]].limbs.items():
                    if limb.controlInData(control):
                        limbsToMatch[char].append(key)

        return limbsToMatch, namespaceToCharDict

    def matchFKToCurrentPose(self):
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        for ns, limb in limbsToMatch.items():
            for l in limb:
                self.loadedIkFkData[namespaceToCharDict[ns]].limbs[l].matchToFK(ns)

    def matchIKToCurrentPose(self):
        limbsToMatch, namespaceToCharDict = self.getLimbsToMatchFromSelection()
        for ns, limb in limbsToMatch.items():
            for l in limb:
                self.loadedIkFkData[namespaceToCharDict[ns]].limbs[l].matchToIK(ns)


class IkFkData(object):
    def __init__(self):
        self.limbs = dict()

    def addLimb(self, name):
        self.limbs[name] = TwoBoneIKData()

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}
        returnDict['limbs'] = {k: v.toJson() for k, v in self.limbs.items()}
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))
        for limb, data in rawJsonData.get('limbs').items():
            self.addLimb(limb)
            for k, v in data.items():
                self.limbs[limb].__dict__[k] = v


class IkDataAbstract(ABC):
    def __init__(self):
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
        self.ikAttr = str()
        self.ikValue = float()
        self.fkValue = float()

        self.jointKeys = ['jointUp', 'jointMid', 'jointEnd']
        self.fkKeys = ['fkControlUp', 'fkControlMid', 'fkControlEnd']
        self.limbWidget = LimbWidget(self)

    def toJson(self):
        jsonData = '''{}'''
        classData = json.loads(jsonData)
        for k, v in self.__dict__.items():
            if k == 'limbWidget':
                continue
            classData[k] = v
        return classData

    def controlInData(self, control):
        return control in self.__dict__.values()

    @abc.abstractmethod
    def getIkFkOffsets(self, namespace):
        pass

    @abc.abstractmethod
    def matchToFK(self, namespace):
        pass

    @abc.abstractmethod
    def matchToIK(self, namespace):
        pass

    @abc.abstractmethod
    def preBake(self, namespace):
        pass

    @abc.abstractmethod
    def postBake(self, namespace):
        pass

    @abc.abstractmethod
    def getFkBakeTargets(self, namespace):
        pass

    @abc.abstractmethod
    def getIkBakeTargets(self, namespace):
        pass

    @abc.abstractmethod
    def mirrorControls(self, sideA, sideB):
        pass



class TwoBoneIKData(IkDataAbstract):
    def __init__(self):
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
        self.ikAttr = str()
        self.ikValue = float()
        self.fkValue = float()

        self.jointKeys = ['jointUp', 'jointMid', 'jointEnd']
        self.fkKeys = ['fkControlUp', 'fkControlMid', 'fkControlEnd']
        self.limbWidget = LimbWidget(self)

    def controlInData(self, control):
        return control in self.__dict__.values()

    def calculatePVPosition(self, namespace):
        startPos = cmds.xform(IKFK().getControl(namespace, self.jointUp), query=True, worldSpace=True, translation=True)
        midPos = cmds.xform(IKFK().getControl(namespace, self.jointMid), query=True, worldSpace=True, translation=True)
        endPos = cmds.xform(IKFK().getControl(namespace, self.jointEnd), query=True, worldSpace=True, translation=True)

        startMV = om2.MVector(startPos[0], startPos[1], startPos[2])
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        endMV = om2.MVector(endPos[0], endPos[1], endPos[2])

        start_endV = endMV - startMV

        start_midV = midMV - startMV
        dot = start_endV * start_midV
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
        midPos = cmds.xform(IKFK().getControl(namespace, self.jointMid), query=True, worldSpace=True, rotatePivot=True)
        pvPos = cmds.xform(IKFK().getControl(namespace, self.pvControl), query=True, worldSpace=True, rotatePivot=True)
        midMV = om2.MVector(midPos[0], midPos[1], midPos[2])
        pvMV = om2.MVector(pvPos[0], pvPos[1], pvPos[2])

        distance = (pvMV - midMV)
        return distance.length()

    def getIkFkOffsets(self, namespace):
        ikControlAttr = IKFK().getControl(namespace, self.ikAttr)
        currentState = cmds.getAttr(ikControlAttr)
        cmds.setAttr(ikControlAttr, self.fkValue)
        for j, c in zip(self.jointKeys, self.fkKeys):
            control = IKFK().getControl(namespace, self.__dict__[c])
            joint = IKFK().getControl(namespace, self.__dict__[j])
            controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
            jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
            # print controlMMatrix, jointMMatrix
            resultTFMatrix = om2.MTransformationMatrix(controlMMatrix * jointMMatrix.inverse())
            resultMatrix = controlMMatrix * jointMMatrix.inverse()
            # print resultTFMatrix.translation(om2.MSpace.kWorld)
            self.fkControlOffsets[c] = [x for x in resultMatrix]
        self.pvDistance = self.getPVDistance(namespace)
        cmds.setAttr(ikControlAttr, self.ikValue)
        # ik is just one control this time
        control = IKFK().getControl(namespace, self.ikControl)
        joint = IKFK().getControl(namespace, self.jointEnd)
        controlMMatrix = om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True))
        jointMMatrix = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, q=True))
        resultMatrix = controlMMatrix * jointMMatrix.inverse()
        self.ikControlOffset = [x for x in resultMatrix]

        cmds.setAttr(ikControlAttr, currentState)

    def matchToFK(self, namespace):
        print ('matchToFK', namespace)
        ikControlAttr = IKFK().getControl(namespace, self.ikAttr)
        for fk, j in zip(self.fkKeys, self.jointKeys):
            control = IKFK().getControl(namespace, self.__dict__.get(fk))
            joint = IKFK().getControl(namespace, self.__dict__.get(j))
            jointMtx = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, absolute=True, q=True))
            offsetMtx = om2.MMatrix(self.fkControlOffsets[fk])
            fkResultMtx = offsetMtx * jointMtx
            cmds.xform(control, matrix=fkResultMtx, ws=1)
        cmds.setAttr(ikControlAttr, self.fkValue)

    def matchToIK(self, namespace):
        print ('matchToIK', namespace)
        ikControlAttr = IKFK().getControl(namespace, self.ikAttr)
        ikControl = IKFK().getControl(namespace, self.ikControl)
        pvControl = IKFK().getControl(namespace, self.pvControl)
        joint = IKFK().getControl(namespace, self.jointEnd)
        jointMtx = om2.MMatrix(cmds.xform(joint, matrix=True, ws=1, absolute=True, q=True))
        pvRotatePivot = cmds.xform(pvControl, rotatePivot=True, ws=1, absolute=True, q=True)
        pvTranslation = cmds.xform(pvControl, translation=True, ws=1, absolute=True, q=True)
        pvTranslationMV = om2.MVector(pvTranslation[0], pvTranslation[1], pvTranslation[2])
        pvRotatePivotMV = om2.MVector(pvRotatePivot[0], pvRotatePivot[1], pvRotatePivot[2])
        offsetMtx = om2.MMatrix(self.ikControlOffset)
        ikResultMtx = offsetMtx * jointMtx

        pvPos = self.calculatePVPosition(namespace)
        cmds.xform(pvControl, translation=pvTranslationMV + (pvPos - pvRotatePivotMV), ws=1)
        cmds.xform(ikControl, matrix=ikResultMtx, ws=1)

        cmds.setAttr(ikControlAttr, self.ikValue)

    def preBake(self, namespace):
        pass

    def postBake(self, namespace):
        pass

    def getFkBakeTargets(self, namespace):
        fkControlUp = IKFK().getControl(namespace, self.fkControlUp)
        fkControlMid = IKFK().getControl(namespace, self.fkControlMid)
        fkControlEnd = IKFK().getControl(namespace, self.fkControlEnd)
        return [fkControlUp, fkControlMid, fkControlEnd]

    def getIkBakeTargets(self, namespace):
        ikControl = IKFK().getControl(namespace, self.ikControl)
        pvControl = IKFK().getControl(namespace, self.pvControl)
        return [ikControl, pvControl]

    def mirrorControls(self, sideA, sideB):
        if sideB in self.ikControl:
            old = sideB
            new = sideA
        else:
            old = sideA
            new = sideB

        self.jointUp = self.jointUp.replace(old, new)
        self.jointMid = self.jointMid.replace(old, new)
        self.jointEnd = self.jointEnd.replace(old, new)
        self.fkControlUp = self.fkControlUp.replace(old, new)
        self.fkControlMid = self.fkControlMid.replace(old, new)
        self.fkControlEnd = self.fkControlEnd.replace(old, new)
        self.ikControl = self.ikControl.replace(old, new)
        self.pvControl = self.pvControl.replace(old, new)
        self.ikAttr = self.ikAttr.replace(old, new)


class IKFK_SetupUI(QMainWindow):
    def __init__(self):
        super(IKFK_SetupUI, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setObjectName('IKFK_SetupUI')
        self.ikFkData = IkFkData()
        self.rigName = str()
        self.namespace = str()
        self.currentLimb = str()
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbIKFK Setup Tool')

        self.main_widget = QWidget()

        self.setCentralWidget(self.main_widget)

        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)

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
        # 2 bone ik widget
        self.limbStackedWidget = QStackedWidget()
        self.blankWidget = LimbWidget(self)
        self.limbStackedWidget.addWidget(self.blankWidget)
        self.limbStackedWidget.setCurrentWidget(self.blankWidget)
        # all existing ik widget
        self.existingIkLayout = QVBoxLayout()
        self.existingIkLayout.setAlignment(Qt.AlignTop)
        self.rigIKFKListWidget = QTreeSingleViewWidget(label='Existing IK Definitions')
        self.existingIkLayout.addWidget(self.rigIKFKListWidget)
        self.limbUpdateWidget = LimbUpdateWidget()
        self.existingIkLayout.addWidget(self.limbUpdateWidget)
        # cuurent rig label
        self.currentRigLabel = QLabel('Current Rig ::')
        self.currentRigNameLabel = QLabel('None')
        self.rigLayout = QVBoxLayout()
        self.rigLabelLayout = QHBoxLayout()
        self.rigLabelLayout.addWidget(self.currentRigLabel)
        self.rigLabelLayout.addWidget(self.currentRigNameLabel)
        # self.rigLayout.addStretch()

        self.main_layout.addLayout(self.rigLayout)

        self.rigLayout.addLayout(self.rigLabelLayout)
        self.rigLayout.addLayout(self.existingIkLayout)
        self.main_layout.addWidget(self.limbStackedWidget)

        self.rigIKFKListWidget.pressedSignal.connect(self.selectLimb)
        self.rigIKFKListWidget.itemChangedSignal.connect(self.renameLimb)
        self.limbUpdateWidget.addNewSignal.connect(self.addNewLimb)
        self.limbUpdateWidget.enableMainWidgetSignal.connect(self.toggleEnabledState)
        self.limbUpdateWidget.mirrorSignal.connect(self.mirrorLimb)
        self.limbUpdateWidget.removeButton.clicked.connect(self.remove)
        # self.limbUpdateWidget.mirrorButton.clicked.connect(self.mirrorLimb)
        self.limbUpdateWidget.updateButton.clicked.connect(self.updateCurrent)
        self.limbUpdateWidget.updateAllButton.clicked.connect(self.updateAll)

        self.resize(self.sizeHint())

    @Slot()
    def toggleEnabledState(self, state):
        print ('toggleEnabledState', state)
        self.main_widget.setEnabled(state)
        self.limbUpdateWidget.dialog.setEnabled(True)

    @Slot()
    def selectLimb(self, inputData):
        print ('selectLimb', inputData)
        self.currentLimb = inputData
        if not inputData:
            self.limbStackedWidget.setDisabled(True)
            return
        self.limbStackedWidget.setDisabled(False)
        print (self.limbStackedWidget.children())
        self.limbStackedWidget.addWidget(self.ikFkData.limbs[self.currentLimb].limbWidget)
        self.limbStackedWidget.setCurrentWidget(self.ikFkData.limbs[self.currentLimb].limbWidget)
        self.ikFkData.limbs[self.currentLimb].limbWidget.refresh()

    @Slot()
    def renameLimb(self, inputData):
        self.ikFkData.limbs[inputData] = self.ikFkData.limbs.pop(self.currentLimb)

    @Slot()
    def addNewLimb(self, inputData, ikType):
        print ('addNewLimb', inputData, ikType)
        if inputData not in self.ikFkData.limbs.keys():
            self.ikFkData.addLimb(inputData)
            self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())
            self.currentLimb = inputData
            self.limbStackedWidget.addWidget(self.ikFkData.limbs[self.currentLimb].limbWidget)

    def remove(self):
        print ('remove')

    @Slot()
    def mirrorLimb(self, inputData):
        self.ikFkData.limbs[inputData] = self.ikFkData.limbs[self.currentLimb].__class__()
        self.ikFkData.limbs[inputData].__dict__ = {k: v for k, v in
                                                   self.ikFkData.limbs[self.currentLimb].__dict__.items()}
        self.ikFkData.limbs[inputData].mirrorControls(self.limbUpdateWidget.sideA.text(),
                                                      self.limbUpdateWidget.sideB.text())
        self.limbStackedWidget.refresh(inputData, self.ikFkData.limbs[inputData])
        self.updateCurrent()

    def updateCurrent(self):
        print ('updateCurrent', self.currentLimb)
        self.ikFkData.limbs[self.currentLimb].getIkFkOffsets(self.namespace)

    def updateAll(self):
        print ('updateAll')

    def getCurrentRig(self):
        self.rigName, self.namespace = IKFK().getCurrentRig()
        IKFK().saveRigFileIfNew(self.rigName)

        self.currentRigNameLabel.setText(self.rigName)
        self.ikFkData = IkFkData()
        self.ikFkData.fromJson(os.path.join(IKFK().ikfkDir, self.rigName + '.json'))
        self.rigIKFKListWidget.updateView(self.ikFkData.limbs.keys())

    def save(self):
        dataFile = os.path.join(IKFK().ikfkDir, self.rigName + '.json')
        data = self.ikFkData.toJson()
        print ('save')
        print ('rig', self.rigName)
        print ('rig file', dataFile)
        print ('data', data)
        IKFK().saveJsonFile(dataFile, json.loads(data))


class BlankWidget(QWidget):
    def __init__(self):
        super(BlankWidget, self).__init__()

        self.mainLayout = QVBoxLayout()
        self.setObjectName('BlankWidget')
        self.setLayout(self.mainLayout)

        self.blankLabel = QLabel('Blank')
        self.mainLayout.addWidget(self.blankLabel)


class LimbUpdateWidget(QWidget):
    addNewSignal = Signal(str, str)
    mirrorSignal = Signal(str)

    enableMainWidgetSignal = Signal(bool)

    def __init__(self):
        super(LimbUpdateWidget, self).__init__()

        self.mainLayout = QVBoxLayout()
        self.setObjectName('LimbUpdateWidget')
        self.setLayout(self.mainLayout)
        self.addButton = QPushButton('Add')
        self.removeButton = QPushButton('Remove')
        self.mirrorButton = QPushButton('Mirror')
        self.updateButton = QPushButton('Cache Offsets')
        self.updateAllButton = QPushButton('Cache Offsets All')
        self.sidesLayout = QHBoxLayout()

        self.sideLabel = QLabel('Sides')
        self.sideA = QLineEdit('_L_')
        self.sideB = QLineEdit('_R_')

        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.removeButton)
        self.mainLayout.addWidget(self.mirrorButton)
        self.sidesLayout.addWidget(self.sideLabel)
        self.sidesLayout.addWidget(self.sideA)
        self.sidesLayout.addWidget(self.sideB)

        self.mainLayout.addLayout(self.sidesLayout)
        self.mainLayout.addWidget(self.updateButton)
        self.mainLayout.addWidget(self.updateAllButton)
        # self.mainLayout.addStretch()

        self.addButton.clicked.connect(self.addNew)
        self.mirrorButton.clicked.connect(self.mirror)

    def addNew(self):
        sel = cmds.ls(sl=True)
        if not sel:
            defaultName = 'RENAME_ME'
        else:
            defaultName = sel[0].split(':')[-1]
        self.dialog = TextInputWidget(title='Add new limb data', label='Enter Name', buttonText="Save",
                                      default=defaultName,
                                      combo=['Arm', 'Leg'],
                                      parent=self)
        self.enableMainWidgetSignal.emit(False)
        self.dialog.acceptedComboSignal.connect(self.getAddNewSignal)
        self.dialog.rejectedSignal.connect(self.enableMainWidget)

    def enableMainWidget(self):
        self.enableMainWidgetSignal.emit(True)

    def getAddNewSignal(self, inputData, ikType):
        self.addNewSignal.emit(inputData, ikType)

    def mirror(self):
        sel = cmds.ls(sl=True)
        if not sel:
            defaultName = 'RENAME_ME'
        else:
            defaultName = sel[0].split(':')[-1]
        self.dialog = TextInputWidget(title='Mirror limb data', label='Enter Name', buttonText="Save",
                                      default=defaultName,
                                      parent=self)

        self.enableMainWidgetSignal.emit(False)
        self.dialog.acceptedSignal.connect(self.getMirrorSignal)
        self.dialog.rejectedSignal.connect(self.enableMainWidget)

    def getMirrorSignal(self, inputData):
        self.mirrorSignal.emit(inputData)


class LimbWidget(QWidget):
    editedSignal = Signal(dict)

    def __init__(self, cls):
        super(LimbWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.cls = cls
        self.key = None
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addStretch()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        self.ikAttrWidget = ChannelSelectLineEdit(key='ikAttr',
                                                  text='Attribute', tooltip='Pick attribute to control ik blend.',
                                                  placeholderTest='enter condition attribute')
        self.ikAttrWidget.lineEdit.setFixedWidth(200)
        self.ikValuesLayout = QHBoxLayout()
        self.ikValueWidget = intFieldWidget(key='ikValue',
                                            optionVar=None, defaultValue=0, label='IK value', minimum=-100, maximum=100,
                                            step=1)

        self.fkValueWidget = intFieldWidget(key='fkValue',
                                            optionVar=None, defaultValue=1, label='FK value', minimum=-100, maximum=100,
                                            step=1)

        # ik value widget (int/bool)
        self.pickFkButton = QPushButton('From Selection')
        self.pickFkButton.clicked.connect(self.pickFK)
        self.pickIKButton = QPushButton('From Selection')
        self.pickIKButton.clicked.connect(self.pickIK)
        self.pickJointsButton = QPushButton('From Selection')
        self.pickJointsButton.clicked.connect(self.pickJoints)

        self.skeletonUpper = ObjectSelectLineEdit(key='jointUp',
                                                  label='Upper Joint')
        self.skeletonMid = ObjectSelectLineEdit(key='jointMid',
                                                label='Mid Joint')
        self.skeletonEnd = ObjectSelectLineEdit(key='jointEnd',
                                                label='End Joint')

        self.fkUpper = ObjectSelectLineEdit(key='fkControlUp',
                                            label='Upper FK')
        self.fkMid = ObjectSelectLineEdit(key='fkControlMid',
                                          label='Mid FK')
        self.fkEnd = ObjectSelectLineEdit(key='fkControlEnd',
                                          label='End FK')

        self.ikPV = ObjectSelectLineEdit(key='pvControl',
                                         label='Pole Vector')
        self.ikEnd = ObjectSelectLineEdit(key='ikControl',
                                          label='IK Control')
        objSelectWidgets = [self.skeletonUpper,
                            self.skeletonMid,
                            self.skeletonEnd,
                            self.fkUpper,
                            self.fkMid,
                            self.fkEnd,
                            self.ikPV,
                            self.ikEnd]
        print (max([x.label.sizeHint().width() for x in objSelectWidgets]))
        self.skeletonUpper.editedSignalKey.connect(self.updateData)
        self.skeletonMid.editedSignalKey.connect(self.updateData)
        self.skeletonEnd.editedSignalKey.connect(self.updateData)
        self.fkUpper.editedSignalKey.connect(self.updateData)
        self.fkMid.editedSignalKey.connect(self.updateData)
        self.fkEnd.editedSignalKey.connect(self.updateData)
        self.ikPV.editedSignalKey.connect(self.updateData)
        self.ikEnd.editedSignalKey.connect(self.updateData)
        self.ikAttrWidget.editedSignalKey.connect(self.updateData)
        self.ikValueWidget.editedSignalKey.connect(self.updateData)
        self.fkValueWidget.editedSignalKey.connect(self.updateData)

        self.attrFrame = QFrame()
        self.attrFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.jointFrame = QFrame()
        self.jointFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.fkFrame = QFrame()
        self.fkFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.ikFrame = QFrame()
        self.ikFrame.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.attrLayout = QVBoxLayout()
        self.jointLayout = QVBoxLayout()
        self.fkLayout = QVBoxLayout()
        self.ikLayout = QVBoxLayout()

        self.mainLayout.addWidget(self.attrFrame)
        self.mainLayout.addWidget(self.jointFrame)
        self.mainLayout.addWidget(self.fkFrame)
        self.mainLayout.addWidget(self.ikFrame)
        self.attrFrame.setLayout(self.attrLayout)
        self.jointFrame.setLayout(self.jointLayout)
        self.fkFrame.setLayout(self.fkLayout)
        self.ikFrame.setLayout(self.ikLayout)

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

        self.ikLayout.addStretch()
        self.ikLayout.addWidget(self.ikPV)
        self.ikLayout.addWidget(self.ikEnd)
        self.ikLayout.addWidget(self.pickIKButton)

        widgets = [x for x in self.mainLayout.children() if x.__class__.__name__ == 'ObjectSelectLineEdit']
        print ('widgets', widgets)

    def refresh(self):
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

    def updateData(self, key, value):
        print ('updateData', key, value)
        self.__dict__[key] = value

    def pickFK(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 3:
            return cmds.warning('Please select all three fk controls')
        sel = [s.split('.')[-1] for s in sel]
        self.fkUpper.itemLabel.setText(sel[0])
        self.fkMid.itemLabel.setText(sel[1])
        self.fkEnd.itemLabel.setText(sel[2])

    def pickIK(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 2:
            return cmds.warning('Please select the pole vector and ik controls')
        sel = [s.split('.')[-1] for s in sel]
        self.ikPV.itemLabel.setText(sel[0])
        self.ikEnd.itemLabel.setText(sel[1])

    def pickJoints(self):
        sel = cmds.ls(sl=True)
        if not len(sel) == 3:
            return cmds.warning('Please select all three joints')
        sel = [s.split('.')[-1] for s in sel]
        self.skeletonUpper.itemLabel.setText(sel[0])
        self.skeletonMid.itemLabel.setText(sel[1])
        self.skeletonEnd.itemLabel.setText(sel[2])
