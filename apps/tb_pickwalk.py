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
import maya.mel as mel
import pymel.core.datatypes as dt
import os
from functools import partial
import maya.OpenMayaUI as omUI
import getStyleSheet as getqss
import json
from Abstract import *
from tb_UI import *

ToolTip_ctrlClickSelect = 'ctrl + click to select'
ToolTip_ctrlClickSet = 'ctrl + click to set from selection'

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

walkDirections = ['up', 'down', 'left', 'right']
skipDirections = ['upSkip', 'downSkip', 'leftSkip', 'rightSkip']

btnWidth = 80


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_pickwalking')
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='tbPickwalkUp',
                                     annotation='pickwalk up, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkUp()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkDown',
                                     annotation='pickwalk down, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkDown()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkLeft',
                                     annotation='pickwalk left, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkLeft()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkRight',
                                     annotation='pickwalk right, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkRight()']))

        self.addCommand(self.tb_hkey(name='tbPickwalkUpAdd',
                                     annotation='pickwalk up add, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkUpAdd()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkDownAdd',
                                     annotation='pickwalk down add, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkDownAdd()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkLeftAdd',
                                     annotation='pickwalk left add, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkLeftAdd()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkRightAdd',
                                     annotation='pickwalk right add, defaults to message attrs, then standard maya function',
                                     category=self.category,
                                     command=['Pickwalk.walkRightAdd()']))

        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class Pickwalk(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Pickwalk'
    hotkeyClass = None
    funcs = None

    defaultToStandardAtDeadEndOption = 'defaultToStandardAtDeadEndOption'

    transformTranslateDict = dict()
    transformRotateDict = dict()

    walkDataLibrary = str()
    pickwalkData = dict()
    rigToWalkDataDict = dict()

    walkDirectionNames = {'up': 'pickUp',
                          'down': 'pickDown',
                          'left': 'pickLeft',
                          'right': 'pickRight',
                          }

    picwalkAttributeNames = {'up': [walkDirectionNames['up'],
                                    '_pickwalk_up',
                                    'cgTkPickWalkup',
                                    'zooWalkup'],
                             'down': [walkDirectionNames['down'],
                                      '_pickwalk_down',
                                      'cgTkPickWalkdown',
                                      'zooWalkdown'],
                             'left': [walkDirectionNames['left'],
                                      '_pickwalk_left',
                                      'cgTkPickWalkleft',
                                      'zookWalkleft'],
                             'right': [walkDirectionNames['right'],
                                       '_pickwalk_right',
                                       'cgTkPickWalkright',
                                       'zookWalkright'],
                             }
    melCommands = {'up': 'pickWalkUp',
                   'down': 'pickWalkDown',
                   'left': 'pickWalkLeft',
                   'right': 'pickWalkRight',
                   }

    walkHotkeyMap = {'up': 'tbPickwalkUp',
                     'down': 'tbPickwalkDown',
                     'left': 'tbPickwalkLeft',
                     'right': 'tbPickwalkRight',
                     }
    walkAddHotkeyMap = {'up': 'tbPickwalkUpAdd',
                        'down': 'tbPickwalkDownAdd',
                        'left': 'tbPickwalkLeftAdd',
                        'right': 'tbPickwalkRightAdd',
                        }
    WASDwalkHotkeyMap = {'w': 'tbPickwalkUp',
                         's': 'tbPickwalkDown',
                         'a': 'tbPickwalkLeft',
                         'd': 'tbPickwalkRight',
                         }

    def __new__(cls):
        if Pickwalk.__instance is None:
            Pickwalk.__instance = object.__new__(cls)

        Pickwalk.__instance.val = cls.toolName
        Pickwalk.__instance.loadWalkLibrary()
        Pickwalk.__instance.getAllPickwalkMaps()
        Pickwalk.__instance.initialiseWalkData()
        return Pickwalk.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(Pickwalk, self).optionUI()
        subWdiget = QWidget()
        subLayout = QVBoxLayout()
        self.layout.addWidget(subWdiget)
        subWdiget.setLayout(subLayout)
        openLibrary = QPushButton('Open Pickwalk library')
        openLibrary.clicked.connect(self.openLibrary)
        subLayout.addWidget(openLibrary)

        openCreator = QPushButton('Open Pickwalk creator')
        openCreator.clicked.connect(self.openCreator)
        subLayout.addWidget(openCreator)

        layout = QHBoxLayout()
        arrowLabel = QLabel('Arrow keys for pickwalking')
        assignArrowHotkeys = QPushButton('Assign arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(arrowLabel)
        subLayout.addLayout(layout)

        layout = QHBoxLayout()
        shiftArrowLabel = QLabel('Arrow Shift+Alt WASD for pickwalkingShift arrow keys for additive pickwalking')
        assignWASDHotkeys = QPushButton('Assign shiftAlt + WASD keys')
        assignWASDHotkeys.clicked.connect(self.assignWASDHotkeys)
        layout.addWidget(assignWASDHotkeys)
        layout.addWidget(shiftArrowLabel)
        subLayout.addLayout(layout)

        layout = QHBoxLayout()
        WASDLabel = QLabel('Shift arrow keys for additive pickwalking')
        assignArrowHotkeys = QPushButton('Assign shift + arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignShiftArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(WASDLabel)
        subLayout.addLayout(layout)

        layout = QHBoxLayout()
        revertArrowLabel = QLabel('Revert Arrow keys to default')
        revertArrowHotkeys = QPushButton('Revert')
        revertArrowHotkeys.clicked.connect(self.revertArrowHotkeys)
        layout.addWidget(revertArrowHotkeys)
        layout.addWidget(revertArrowLabel)
        subLayout.addLayout(layout)

        endOptionWidget = optionVarBoolWidget('Default to standard walk on empty custom map ', self.defaultToStandardAtDeadEndOption)
        self.layout.addWidget(endOptionWidget)
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def openLibrary(self):
        win = pickwalkRigAssignemtWindow()
        win.show()

    def openCreator(self):
        win = pickwalkMainWindow()
        win.show()

    def revertArrowHotkeys(self):
        pass

    def assignArrowHotkeys(self):
        for direction, command in self.walkHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        name=command + 'NameCommand')

    def assignShiftArrowHotkeys(self):
        for direction, command in self.walkHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=True,
                        name=command + 'NameCommand')

    def assignWASDHotkeys(self):
        for direction, command in self.WASDwalkHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=True,
                        altModifier=True,
                        name=command + 'NameCommand')

    def loadWalkLibrary(self):
        self.defaultPickwalkDir = pm.optionVar.get('pickwalkDir',
                                                   os.path.join(os.path.normpath(os.path.dirname(__file__)),
                                                                'pickwalkData'))
        if not os.path.isdir(self.defaultPickwalkDir):
            os.mkdir(self.defaultPickwalkDir)
        self.libraryFile = pm.optionVar.get('pickwalkLibrary', 'pickwalkLibraryData.json')
        #print 'library file',  self.libraryFile
        self.libraryFilePath = os.path.join(self.defaultPickwalkDir, self.libraryFile)

        if not os.path.isfile(self.libraryFilePath):
            self.walkDataLibrary = WalkDataLibrary()
            self.walkDataLibrary.save(self.libraryFilePath)
            pm.optionVar['pickwalkLibrary'] = self.libraryFile
        else:
            self.walkDataLibrary = WalkDataLibrary()
            self.walkDataLibrary.load(self.libraryFilePath)

        for key, values in self.walkDataLibrary.rigMapDict.items():
            for v in values:
                self.rigToWalkDataDict[v] = key
        return self.walkDataLibrary

    def getAllPickwalkMaps(self):
        self.jsonFiles = list()
        for filename in os.listdir(self.defaultPickwalkDir):
            if filename.endswith(".json"):
                if os.path.basename(filename) == self.libraryFile:
                    continue
                self.jsonFiles.append(os.path.join(self.defaultPickwalkDir, filename))
        for filename in self.jsonFiles:
            mapName = os.path.basename(filename).split('.')[0]
            if mapName not in self.walkDataLibrary.rigMapDict.keys():
                self.walkDataLibrary.rigMapDict[mapName] = list()

        statinfo = os.access(self.libraryFilePath, os.W_OK)
        if statinfo:
            self.walkDataLibrary.save(self.libraryFilePath)
        #print self.walkDataLibrary.__dict__

    def initialiseWalkData(self):
        """
        Load up all the pickwalk maps into a big dictionary
        :return:
        """
        for walkData in self.jsonFiles:
            #print 'initialiseWalkData, loading data', walkData
            mapName = os.path.basename(walkData).split('.')[0]
            jsonObjectInfo = json.load(open(walkData))

            pickwalkCreator = PickwalkCreator()
            pickwalkCreator.load(walkData)
            self.pickwalkData[mapName] = pickwalkCreator.walkData

    def walkStandard(self, direction):
        mel.eval(self.melCommands[direction])

    def pickWalkAttribute(self, node=None, attribute=None):
        # check if message attribute exists
        if not cmds.attributeQuery(attribute, node=node, exists=True):
            return
        # walk attribute exists, check it's type
        if cmds.getAttr(node + '.' + attribute, type=True) == u'string':
            # use string attribute method
            destination = cmds.getAttr(node + '.' + attribute)
            pNode = pm.PyNode(node)
            if cmds.objExists(pNode.namespace() + cmds.getAttr(node + '.' + attribute)):
                return pNode.namespace() + destination

        elif cmds.getAttr(node + '.' + attribute, type=True) == u'message':
            # list connection to message attribute
            conns = cmds.listConnections(node + '.' + attribute, source=True, destination=False)
            # if there are connections, check what kind of node it is
            if conns:
                return conns[0]

    def pickwalk(self, direction=str, add=False):
        sel = pm.ls(sl=True, type='transform')
        returnedControls = list()
        if not sel:
            self.walkStandard(direction)
            return
        walkObject = sel[-1]
        if direction not in self.walkDirectionNames.keys():
            return cmds.error('\nInvalid pick direction, only up, down, left, right are supported')

        refName = None
        refState = cmds.referenceQuery(str(walkObject), isNodeReferenced=True)
        if refState:
            # if it is referenced, check against pickwalk library entries
            refName = cmds.referenceQuery(str(walkObject), filename=True, shortName=True).split('.')[0]
        else:
            # might just be working in the rig file itself
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        if refName:
            #print 'query against pickwalk library'
            if refName in self.walkDataLibrary._fileToMapDict.keys():
                mapName = self.walkDataLibrary._fileToMapDict[refName]
                #print refName, 'uses map', self.walkDataLibrary._fileToMapDict[refName]
                result = self.pickwalkData[mapName].walk(namespace=walkObject.namespace(),
                                                         node=walkObject.stripNamespace(),
                                                         direction=direction)
                if result:
                    print 'data walk result', result
                    if cmds.objExists(walkObject.namespace() + result):
                        print 'final result', walkObject.namespace() + result
                        returnedControls.append(result)
                    else:
                        if pm.optionVar.get(self.defaultToStandardAtDeadEndOption, True):
                            self.walkStandard(direction)
                        return

                if add:
                    print 'adding'
                    returnedControls.append(sel)

                print 'final returnedControls', returnedControls
                if returnedControls:
                    cmds.select(returnedControls, replace=True)
                    return

            elif refName not in self.walkDataLibrary.ignoredRigs:
                #print 'not ignored, must be new, query user to add/assign/ignore it'
                prompt = PickwalkQueryWidget(title='New Rig Found', rigName=refName,
                                             text='This rig new, set up pickwalking on it?')
                prompt.AssignNewRigSignal.connect(self.assignNewRigExistingMap)
                prompt.IgnoreRigSignal.connect(self.assignIgnoreNewRig)
                prompt.CreateNewRigMapSignal.connect(self.assignNewRigNewMap)

                if prompt.exec_():
                    pass
                else:
                    pass

        # anything beyond here is using attribute based pickwalking
        userAttrs = cmds.listAttr(str(walkObject), userDefined=True)
        if not userAttrs:
            self.walkStandard(direction)
            return
        pickAttributes = [i for i in self.picwalkAttributeNames[direction] if i in userAttrs]
        if not pickAttributes:
            # didn't find any custom pickwalk attributes, use the regular walk
            self.walkStandard(direction)
            return

        found = False

        for walkAttribute in self.picwalkAttributeNames[direction]:
            if not found:
                if cmds.attributeQuery(walkAttribute, node=str(walkObject), exists=True):
                    returnObj = self.pickWalkAttribute(node=str(walkObject), attribute=walkAttribute)
                    if returnObj:
                        if isinstance(returnObj, list):
                            returnedControls.extend(returnObj)
                            found = True
                        else:
                            returnedControls.append(returnObj)
                            found = True

        if not returnedControls:
            self.walkStandard(direction)
            return
        if add:
            returnedControls.extend(sel)
        cmds.select(returnedControls, replace=True)

    def walkUp(self):
        self.pickwalk(direction='up')

    def walkDown(self):
        self.pickwalk(direction='down')

    def walkLeft(self):
        self.pickwalk(direction='left')

    def walkRight(self):
        self.pickwalk(direction='right')

    def walkUpAdd(self):
        self.pickwalk(direction='up', add=True)

    def walkDownAdd(self):
        self.pickwalk(direction='down', add=True)

    def walkLeftAdd(self):
        self.pickwalk(direction='left', add=True)

    def walkRightAdd(self):
        self.pickwalk(direction='right', add=True)

    def assignNewRigExistingMap(self, rigName):
        #print 'load a dialog to assign one of the existing maps'
        self.getAllPickwalkMaps()
        prompt = PickListDialog(title='Assign rig to existing map', text='Pick exising pickwalk map for rig',
                                itemList=self.walkDataLibrary.rigMapDict.keys(),
                                rigName=rigName)
        prompt.assignSignal.connect(self.assignRig)
        if prompt.exec_():
            pass
        else:
            pass

    def assignRig(self, rigMap, rigName):
        #print 'assign map to rig', rigMap, rigName
        self.walkDataLibrary.assignRig(rigMap, rigName)
        self.walkDataLibrary.save(self.libraryFilePath)

    def assignIgnoreNewRig(self):
        pass
        #print 'assignIgnoreNewRig'

    def assignNewRigNewMap(self, rigName):
        win = pickwalkMainWindow()
        newMap = win.saveAsLibrary()
        #print 'new map', newMap
        self.walkDataLibrary.assignRig(newMap, rigName)
        self.walkDataLibrary.save(self.libraryFilePath)
        win.show()


class WalkDataLibrary(object):
    def __init__(self):
        self.rigMapDict = dict()
        self.ignoredRigs = list()
        self._fileToMapDict = dict()
        self._walkData = dict()

    def toJson(self):
        jsonData = '''{}'''
        self.jsonObjectInfo = json.loads(jsonData)
        self.jsonObjectInfo['rigMapDict'] = {key: value for key, value in self.rigMapDict.items()}
        self.jsonObjectInfo['ignoredRigs'] = self.ignoredRigs

    def assignRig(self, key, map):
        for key, values in self.rigMapDict.items():
            if map in values:
                values.remove(map)
        self.rigMapDict[key].append(map)

    def save(self, filePath):
        """
        :return:
        """
        self.name = filePath.split('/')[-1].split('.')[0]
        self.toJson()
        fileName = os.path.join(filePath)
        j = json.dumps(self.jsonObjectInfo, indent=4, separators=(',', ': '))
        f = open(fileName, 'w')
        print >> f, j
        f.close()
        self.createFileToRigMapping()

    def load(self, filepath):
        jsonObjectInfo = json.load(open(filepath))
        self.rigMapDict = jsonObjectInfo['rigMapDict']
        self.ignoredRigs = jsonObjectInfo['ignoredRigs']
        self.createFileToRigMapping()

    def createFileToRigMapping(self):
        for key, values in self.rigMapDict.items():
            for v in values:
                self._fileToMapDict[v] = key


class WalkData(object):
    """
    Stores all information about pickwalking
    """

    def __init__(self):
        self.name = None
        self._filePath = None
        self.objectDict = dict()
        self.destinations = dict()
        self.jsonObjectInfo = dict()
        self.categoryKeys = dict()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def toJson(self):
        jsonData = '''{}'''
        self.jsonObjectInfo = json.loads(jsonData)
        self.jsonObjectInfo['destinations'] = {key: value.toJson() for key, value in self.destinations.items()}
        self.jsonObjectInfo['objectDict'] = {key.split(':')[-1]: value.toJson() for key, value in
                                             self.objectDict.items()}
        self.jsonObjectInfo['categoryKeys'] = {key: value for key, value in self.categoryKeys.items()}

    def save(self, filePath):
        """

        :return:
        """
        #print filePath
        self._filePath = filePath
        self.name = filePath.split('/')[-1].split('.')[0]
        self.toJson()
        fileName = os.path.join(filePath)
        j = json.dumps(self.jsonObjectInfo, indent=4, separators=(',', ': '))
        f = open(fileName, 'w')
        print >> f, j
        f.close()

    def walk(self, namespace=str(), node=str(), direction=str()):
        #print 'walk', node, direction
        # do a check on walk for current object in any destination objects, set the appropriate index
        if node not in self.objectDict.keys():
            return None
        target = self.objectDict[node][direction]
        if target in self.destinations.keys():
            # destination is a conditional destination
            #print ('destination is a conditional destination')
            #print 'namespace', namespace
            #print self.destinations[target]
            #print self.destinations[target].__dict__
            conditionTest = False
            if self.destinations[target].conditionAttribute:
                #print self.destinations[target].conditionAttribute
                conditionTest = cmds.getAttr(namespace + self.destinations[target].conditionAttribute) >= self.destinations[target].conditionValue
                #print 'conditionTest', conditionTest
            if conditionTest:
                target = self.destinations[target].destinationAlt[self.destinations[target]._lastIndex]
            else:
                target = self.destinations[target].destination[self.destinations[target]._lastIndex]
            return target
            # check for condition attr/object?
            # conditions met, pick alt/destination, use last used index
            pass
        else:
            # destination is an object
            return target
        return None


class WalkDirectionDict(object):
    """
    Dictionary of walk directions, entries will be walkDatinationInfo() or str()
    """

    def __init__(self, left=None,
                 right=None,
                 up=None,
                 down=None):
        self.left = left,
        self.right = right,
        self.up = up,
        self.down = down

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def toJson(self):
        return {key: str(value).split(':')[-1] for key, value in self.__dict__.items()}


class WalkDatinationInfo(object):
    """
    Stores a particular set of destinations/condition
    """

    def __init__(self, destination=list(),
                 destinationAlt=list(),
                 conditionAttribute=list(),
                 conditionValue=0.5
                 ):
        self.destination = self.stripList(destination)
        self.destinationAlt = self.stripList(destinationAlt)
        self.conditionAttribute = conditionAttribute
        self.conditionValue = conditionValue
        self._lastIndex = 0

    def stripList(self, input):
        if len(input):
            return [x.split(':')[-1] for x in input]
        else:
            return input

    def toJson(self):
        d = dict((key, value) for key, value in self.__dict__.items() if not key.startswith("__"))
        # print d
        return d


pwShapeWindow = None
pickwalkWorkspaceControlName = 'pwWorkspaceControl'


def getMainWindow():
    return wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget)


def workspaceScript(*args):
    parentWidget = pm.toQtObject(pm.setParent(q=True))
    parentLayout = filter(lambda c: isinstance(c, QLayout), parentWidget.children())

    global pwShapeWindow

    if 'controlShapeWindow' not in globals():
        pm.mel.evalDeferred(
            'if (`workspaceControl -exists "shapeWorkspaceControl"`) workspaceControl -e -close "shapeWorkspaceControl";')

    if pwShapeWindow:
        try:
            pwShapeWindow.close()
        except:
            pass

    pwShapeWindow = pickwalkMainWindow()
    pwShapeWindow.show()
    parentLayout[0].addWidget(pwShapeWindow)


def dockControl():
    channelBoxTab = pm.mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false)')
    if pm.workspaceControl(pickwalkWorkspaceControlName, exists=True):
        try:
            pm.deleteUI(pickwalkWorkspaceControlName)
        except:
            pass
    pm.workspaceControl(pickwalkWorkspaceControlName,
                        tabToControl=[channelBoxTab, -1],
                        uiScript='import tb_pickwalk as tbPW;reload(tbPW);tbPW.workspaceScript()',
                        loadImmediately=True,
                        initialWidth=100,
                        # minimumWidth=False,
                        widthProperty='free',
                        retain=False,
                        r=True,
                        label='tbPickWalk')


class standardPickButton(QPushButton):
    pressedSignal = Signal(str)
    direction = str()

    def __init__(self, label=str, direction=str, icon=str(), rotation=0, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.setText(label)
        self.direction = direction

        upRotate = QTransform().rotate(rotation)
        pixmap = QPixmap(':/{}'.format(icon)).transformed(upRotate)
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.clicked.connect(partial(self.pressedSignal.emit, self.direction))


class pickObjectWidget(QWidget):
    setActiveObjectSignal = Signal(str)
    modeChangedSignal = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(pickObjectWidget, self).__init__()
        self.mainLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        self.ObjLabel = QLabel('Object ::')
        self.ObjLabel.setFixedWidth(btnWidth)
        self.currentObjLabel = QLabel('None')
        self.centre = QPushButton('Pick Object')
        self.modeBtn = QPushButton('Walk')
        self.modeBtn.setCheckable(True)
        self.modeBtn.setStyleSheet("""
                                    QPushButton{background:#228B22 ;color: white;} 
                                    QPushButton::checked{background:#ffa500;color: black;}
                                """)
        self.mainLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(self.ObjLabel)
        self.infoLayout.addWidget(self.currentObjLabel)
        self.mainLayout.addWidget(self.centre)
        # self.mainLayout.addWidget(self.modeBtn)

        self.centre.clicked.connect(self.setActiveObject)
        self.modeBtn.clicked.connect(self.sendModeChangedSignal)
        self.changeState()

    def changeState(self):
        # if button is checked
        if self.modeBtn.isChecked():
            self.modeBtn.setText('Skip')
        else:
            self.modeBtn.setText('Walk')

    @Slot()
    def setActiveObject(self):
        sel = pm.ls(selection=True, type='transform')
        if not sel:
            pm.warning('No objects selected')
            self.setActiveObjectSignal.emit(str())
            self.activeObject = None
            self.currentObjLabel.setText("None")
            return
        self.setActiveObjectSignal.emit(str(sel[0]))
        self.activeObject = sel[0]
        self.currentObjLabel.setText(sel[0].stripNamespace())

    @Slot()
    def sendModeChangedSignal(self):
        self.modeChangedSignal.emit(self.modeBtn.isChecked())
        self.changeState()


class pickDirectionWidget(QFrame):
    setActiveObjectSignal = Signal()  # in case the main ui needs to keep track?
    directionPressedObjectSignal = Signal(str)  # in case the main ui needs to keep track?

    loopChanged = Signal(bool)
    reciprocateChanged = Signal(bool)
    endOnSelfChanged = Signal(bool)
    activeObject = None

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mode = False
        # self.setFrameStyle(QFrame.Panel | QFrame.Raised)\

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

        # self.setTitle("Pickwalk")
        self.setMaximumWidth(290)
        self.mainLayout = QVBoxLayout()
        self.leftLayout = QHBoxLayout()
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(4)
        self.mainLayout.setSpacing(4)

        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        self.objectWidget = pickObjectWidget()
        self.objectWidget.setStyleSheet(getqss.getStyleSheet())
        self.objectWidget.setStyleSheet("QFrame {"
                                        "border-width: 0;"
                                        "border-radius: 0;"
                                        "border-style: solid;"
                                        "border-color: #222222}"
                                        )
        self.objectWidget.setActiveObjectSignal.connect(self.setActiveObject)
        self.objectWidget.modeChangedSignal.connect(self.modeChanged)

        self.upBtn = standardPickButton(label='', direction='up', icon='timeend.png', rotation=90)
        self.downBtn = standardPickButton(label='', direction='down', icon='timeend.png', rotation=270)
        self.leftBtn = standardPickButton(label='', direction='left', icon='timeend.png', rotation=0)
        self.rightBtn = standardPickButton(label='', direction='right', icon='timeend.png', rotation=180)

        self.chainOptionWidget = pickChainWidget()
        self.chainOptionWidget.setStyleSheet("QFrame {"
                                             "border-width: 0;"
                                             "border-radius: 0;"
                                             "border-style: solid;"
                                             "border-color: #222222}"
                                             )
        self.chainOptionWidget.loopChanged.connect(self.sendloopChangedSignal)
        self.chainOptionWidget.reciprocateChanged.connect(self.sendreciprocateChangedSignal)
        self.chainOptionWidget.endOnSelfChanged.connect(self.sendEndOnSelfChangedSignal)

        self.gridLayout.addWidget(self.upBtn, 0, 2)

        self.gridLayout.addWidget(self.downBtn, 4, 2)
        self.gridLayout.addWidget(self.leftBtn, 2, 0)
        self.gridLayout.addWidget(self.rightBtn, 2, 4)

        self.mainLayout.addLayout(self.leftLayout)
        self.leftLayout.addWidget(self.objectWidget)
        self.leftLayout.addLayout(self.gridLayout)
        self.mainLayout.addWidget(self.chainOptionWidget)

        self.allButtons = [
            self.upBtn,
            self.downBtn,
            self.leftBtn,
            self.rightBtn,
            # self.upSkipBtn,
            # self.downSkipBtn,
            # self.leftSkipBtn,
            # self.rightSkipBtn,
        ]
        for btn in self.allButtons:
            btn.pressedSignal.connect(self.inputSignal_pickDirection)
            btn.setFixedWidth(32)

    @Slot()
    def modeChanged(self, data):
        self.mode = data

    @Slot()
    def setActiveObject(self):
        self.setActiveObjectSignal.emit()

    @Slot()
    def inputSignal_pickDirection(self, direction):
        direction = '{0}{1}'.format(direction, {True: 'Skip', False: ''}[self.mode])
        self.directionPressedObjectSignal.emit(direction)

    @Slot()
    def sendloopChangedSignal(self, data):
        self.loopChanged.emit(data)

    @Slot()
    def sendreciprocateChangedSignal(self, data):
        self.reciprocateChanged.emit(data)

    @Slot()
    def sendEndOnSelfChangedSignal(self, data):
        self.endOnSelfChanged.emit(data)


class pickChainWidget(QFrame):
    loopChanged = Signal(bool)
    reciprocateChanged = Signal(bool)
    endOnSelfChanged = Signal(bool)

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.loop = QCheckBox('loop')
        self.reciprocate = QCheckBox('reciprocate')
        self.endOnSelf = QCheckBox('end on self')
        # self.reciprocate.setChecked(True)

        self.mainLayout.addWidget(self.loop)
        self.mainLayout.addWidget(self.reciprocate)
        self.mainLayout.addWidget(self.endOnSelf)

        self.loop.clicked.connect(self.sendloopChangedSignal)
        self.reciprocate.clicked.connect(self.sendreciprocateChangedSignal)
        self.endOnSelf.clicked.connect(self.sendendOnSelfChangedSignal)

    @Slot()
    def sendloopChangedSignal(self):
        self.loopChanged.emit(self.loop.isChecked())

    @Slot()
    def sendreciprocateChangedSignal(self):
        self.reciprocateChanged.emit(self.reciprocate.isChecked())

    @Slot()
    def sendendOnSelfChangedSignal(self):
        self.endOnSelfChanged.emit(self.endOnSelf.isChecked())


class labelledLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)

    def __init__(self, text=str, hasButton=False, buttonLabel=str, obj=False):
        super(labelledLineEdit, self).__init__()
        self.obj = obj

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        self.button = standardPickButton(label=buttonLabel, direction='left', icon='timeend.png', rotation=0)
        self.button.setFixedWidth(80)
        if self.obj:
            self.button.clicked.connect(self.pickObject)
        else:
            self.button.clicked.connect(self.pickChannel)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        if hasButton:
            self.layout.addWidget(self.button)
        self.label.setFixedWidth(60)
        # elf.lineEdit.setFixedWidth(200)
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            pm.warning('no channel selected')
        self.lineEdit.setText(channels[0].split(':')[-1])

    def pickObject(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            pm.warning('no object selected')
        self.lineEdit.setText(sel[0].split(':')[-1] + '_in')


class labelledDoubleSpinBox(QWidget):
    editedSignal = Signal(float)

    def __init__(self, text=str, ):
        super(labelledDoubleSpinBox, self).__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel(text)
        self.spinBox = QDoubleSpinBox()
        self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        self.spinBox.setValue(0.5)
        self.spinBox.setSingleStep(0.1)

        self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinBox)
        self.layout.addStretch()
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    @Slot()
    def sendValueChangedSignal(self):
        self.editedSignal.emit(self.spinBox.value())


class ControlListWidget(QWidget):
    pressedSignal = Signal(list())
    newDestinationSignal = Signal(str, str, str)
    newConditionDestinationSignal = Signal(QStandardItem)

    def __init__(self, CLS=None, label='BLANK'):
        super(ControlListWidget, self).__init__()
        self.CLS = CLS
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(120)
        self.width = 300
        self.setLayout(self.layout)
        self.topLayout = QVBoxLayout()
        self.layout.addLayout(self.topLayout)
        self.label = QLabel(label)
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.addAction(QIcon(":/resources/search.ico"), QLineEdit.LeadingPosition)
        self.filterLineEdit.setPlaceholderText("Search...")
        self.categoryLabel = QLabel('Category ::')
        self.addCategoryBtn = QPushButton('+')
        self.removeCategoryBtn = QPushButton('-')

        self.categoryOption = QComboBox()
        self.categoryOption.setMinimumWidth(120)
        self.addCategoryBtn.clicked.connect(self.categoryAdded)
        self.removeCategoryBtn.clicked.connect(self.categoryRemoved)
        # self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        # self.spinBox.setValue(0.5)
        # self.spinBox.setSingleStep(0.1)

        # self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.topLayout.addWidget(self.label)
        self.topLayout.addWidget(self.filterLineEdit)
        # self.topLayout.addWidget(self.categoryLabel)
        # self.topLayout.addWidget(self.categoryOption)
        # self.topLayout.addWidget(self.addCategoryBtn)
        # self.topLayout.addWidget(self.removeCategoryBtn)
        # self.layout.addWidget(self.spinBox)
        # self.layout.addStretch()
        '''
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        '''
        self.treeView = QTreeView()
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setStyleSheet("QTreeView {"
                                    "alternate-background-color: #464848 ;"
                                    "background: #323232;}"
                                    )
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Control', 'up', 'down', 'left', 'right'])
        self.proxyModel.setSourceModel(self.model)
        self.treeView.setModel(self.proxyModel)
        self.treeView.clicked.connect(self.itemClicked)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)
        self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.header = self.treeView.header()
        self.header.setStretchLastSection(False)
        self.header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.header.setSectionResizeMode(4, QHeaderView.Stretch)

        # self.header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)

        # spacerItem = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.layout.addItem(spacerItem)

        self.toolTypeScrollArea = QScrollArea()
        self.toolTypeScrollArea.setWidget(self.treeView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.toolTypeScrollArea)
        # self.layout.addStretch(1)
        # self.toolTypeScrollArea.setFixedWidth(148)
        self.updateCategoryList()
        self.updateView()

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def updateCategoryList(self):
        self.categoryOption.clear()
        self.categoryOption.addItem('None')
        for c in self.CLS.walkData.categoryKeys.keys():
            self.categoryOption.addItem(c)
        self.categoryOption.currentIndexChanged.connect(self.categoryChanged)

    def categoryChanged(self, i):
        pass
        #print self.categoryOption.currentText() == 'None'

    def categoryAdded(self):
        prompt = promptWidget(title='Add new category', text='Name ::', defaultInput='New', buttonText='OK')
        prompt.saveSignal.connect(self.inputSignal)

    def inputSignal(self, input):
        if input not in self.CLS.walkData.categoryKeys.keys():
            self.CLS.walkData.categoryKeys[input] = list()
            self.updateCategoryList()

    def categoryRemoved(self):
        self.categoryOption.removeItem(self.categoryOption.currentIndex())

    def updateView(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Control', 'up', 'down', 'left', 'right'])
        # self.listwidget.addItems(self.CLS.walkData.objectDict.keys())
        for item in sorted(self.CLS.walkData.objectDict.keys()):
            data = self.CLS.walkData.objectDict[item]
            controlItem = QStandardItem(item)
            controlItem.setToolTip(ToolTip_ctrlClickSelect)
            upItem = QStandardItem(str(data.up))
            downItem = QStandardItem(str(data.down))
            leftItem = QStandardItem(str(data.left))
            rightItem = QStandardItem(str(data.right))
            upItem.setToolTip(ToolTip_ctrlClickSet)
            downItem.setToolTip(ToolTip_ctrlClickSet)
            leftItem.setToolTip(ToolTip_ctrlClickSet)
            rightItem.setToolTip(ToolTip_ctrlClickSet)

            controlItem.control = item
            upItem.direction = 'up'
            upItem.control = item
            downItem.direction = 'down'
            downItem.control = item
            leftItem.direction = 'left'
            leftItem.control = item
            rightItem.direction = 'right'
            rightItem.control = item

            self.model.appendRow([controlItem, upItem, downItem, leftItem, rightItem])

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        #print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        #print item
        #print item.text()
        if not hasattr(item, 'control'):
            return
        #print 'Control', item.control

        if modifiers == Qt.ShiftModifier:
            #print('Shift+Click')
            self.sendNewConditionDestinationSignal(item)

        elif modifiers == Qt.ControlModifier:
            #print('Control+Click')
            if hasattr(item, 'direction'):
                #print 'direction', item.direction
                sel = cmds.ls(sl=True, type='transform')
                if not sel:
                    return pm.warning('nothing selected')
                walkObject = sel[0].split(':')[-1]
                item.setText(walkObject)
                self.sendNewDestinationSignal(item.control, item.direction, walkObject)
            else:
                cmds.select(item.control, replace=True)

    @Slot()
    def sendNewConditionDestinationSignal(self, item):
        #print 'sendNewConditionDestinationSignal'
        self.newConditionDestinationSignal.emit(item)

    @Slot()
    def sendNewDestinationSignal(self, control, direction, item):
        #print 'sendNewDestinationSignal'
        self.newDestinationSignal.emit(control, direction, item)


class QTreeSingleViewWidget(QFrame):
    pressedSignal = Signal(str)

    def __init__(self, CLS=None, label='BLANK'):
        super(QTreeSingleViewWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.setMinimumWidth(120)
        # self.setMaximumWidth(200)
        # self.width = 300
        self.setLayout(self.layout)
        self.topLayout = QVBoxLayout()
        self.layout.addLayout(self.topLayout)
        self.label = QLabel(label)
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.addAction(QIcon(":/resources/search.ico"), QLineEdit.LeadingPosition)
        self.filterLineEdit.setPlaceholderText("Search...")
        # self.categoryLabel = QLabel('Category ::')
        # self.addCategoryBtn = QPushButton('+')
        # self.removeCategoryBtn = QPushButton('-')

        # self.categoryOption = QComboBox()
        # self.categoryOption.setMinimumWidth(120)
        # self.addCategoryBtn.clicked.connect(self.categoryAdded)
        # self.removeCategoryBtn.clicked.connect(self.categoryRemoved)
        # self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        # self.spinBox.setValue(0.5)
        # self.spinBox.setSingleStep(0.1)

        # self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.topLayout.addWidget(self.label)
        self.topLayout.addWidget(self.filterLineEdit)
        # self.topLayout.addWidget(self.categoryLabel)
        # self.topLayout.addWidget(self.categoryOption)
        # self.topLayout.addWidget(self.addCategoryBtn)
        # self.topLayout.addWidget(self.removeCategoryBtn)
        # self.layout.addWidget(self.spinBox)
        # self.layout.addStretch()
        '''
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        '''
        self.listView = QListView()

        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.model = QStandardItemModel()
        # self.model.setHorizontalHeaderLabels(['Destination'])
        self.proxyModel.setSourceModel(self.model)
        self.listView.setModel(self.proxyModel)
        self.listView.clicked.connect(self.itemClicked)
        self.model.itemChanged.connect(self.itemChanged)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)
        # self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.listView.setSelectionBehavior(QAbstractItemView.SelectItems)

        # self.header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # self.header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.listView.setSizeAdjustPolicy(QListWidget.AdjustToContents)

        # spacerItem = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.layout.addItem(spacerItem)

        self.toolTypeScrollArea = QScrollArea()
        self.toolTypeScrollArea.setWidget(self.listView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.toolTypeScrollArea)
        # self.layout.addStretch(1)
        # self.toolTypeScrollArea.setFixedWidth(148)
        # self.updateCategoryList()
        # self.updateView()

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def updateView(self, items):
        self.model.clear()
        self.listView.blockSignals(True)
        for i in items:
            item = QStandardItem(i)
            self.model.appendRow(item)
        self.listView.blockSignals(False)

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        #print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.pressedSignal.emit(item.text())

    def itemChanged(self, item):
        pass
        #print 'old value', item.destination
        #print 'new value', item.text()


class DestinationListWidget(QFrame):
    pressedSignal = Signal(str)
    applySignal = Signal(str)

    def __init__(self, CLS=None, label='BLANK'):
        super(DestinationListWidget, self).__init__()
        self.CLS = CLS
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(120)
        self.setMaximumWidth(200)
        # self.width = 300
        self.setLayout(self.layout)
        self.topLayout = QVBoxLayout()
        self.layout.addLayout(self.topLayout)
        self.label = QLabel(label)
        self.applyButton = QPushButton('Replace selection')
        self.applyButton.clicked.connect(self.applyToSelected)
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setClearButtonEnabled(True)
        self.filterLineEdit.addAction(QIcon(":/resources/search.ico"), QLineEdit.LeadingPosition)
        self.filterLineEdit.setPlaceholderText("Search...")
        # self.categoryLabel = QLabel('Category ::')
        # self.addCategoryBtn = QPushButton('+')
        # self.removeCategoryBtn = QPushButton('-')

        # self.categoryOption = QComboBox()
        # self.categoryOption.setMinimumWidth(120)
        # self.addCategoryBtn.clicked.connect(self.categoryAdded)
        # self.removeCategoryBtn.clicked.connect(self.categoryRemoved)
        # self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        # self.spinBox.setValue(0.5)
        # self.spinBox.setSingleStep(0.1)

        # self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.topLayout.addWidget(self.label)
        self.topLayout.addWidget(self.filterLineEdit)
        self.topLayout.addWidget(self.applyButton)
        # self.topLayout.addWidget(self.categoryLabel)
        # self.topLayout.addWidget(self.categoryOption)
        # self.topLayout.addWidget(self.addCategoryBtn)
        # self.topLayout.addWidget(self.removeCategoryBtn)
        # self.layout.addWidget(self.spinBox)
        # self.layout.addStretch()
        '''
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        '''
        self.treeView = QTreeView()
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setStyleSheet("QTreeView {"
                                    "alternate-background-color: #464848 ;"
                                    "background: #323232;}"
                                    )
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Destination'])
        self.proxyModel.setSourceModel(self.model)
        self.treeView.setModel(self.proxyModel)
        self.treeView.clicked.connect(self.itemClicked)
        self.model.itemChanged.connect(self.itemChanged)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)
        # self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.header = self.treeView.header()
        self.header.setStretchLastSection(True)
        # self.header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # self.header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.treeView.setSizeAdjustPolicy(QListWidget.AdjustToContents)

        # spacerItem = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.layout.addItem(spacerItem)

        self.toolTypeScrollArea = QScrollArea()
        self.toolTypeScrollArea.setWidget(self.treeView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.toolTypeScrollArea)
        # self.layout.addStretch(1)
        # self.toolTypeScrollArea.setFixedWidth(148)
        # self.updateCategoryList()
        # self.updateView()

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def updateView(self):
        #print 'updating tree view', self.CLS
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Destination'])
        self.treeView.blockSignals(True)
        for item in sorted(self.CLS.walkData.destinations.keys()):
            # data = self.CLS.walkData.objectDict[item]
            destinationItem = QStandardItem(item)
            # destinationItem.setToolTip(ToolTip_ctrlClickSelect)

            destinationItem.destination = item

            self.model.appendRow([destinationItem])
        self.treeView.blockSignals(False)

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        #print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        #print item
        #print item.text()
        self.pressedSignal.emit(item.text())

    def applyToSelected(self):
        index = self.treeView.selectedIndexes()[0]
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.applySignal.emit(item.text())

    def itemChanged(self, item):
        pass
        #print 'old value', item.destination
        #print 'new value', item.text()


class DestinationWidget(QWidget):
    updatedSignal = Signal(list)

    def __init__(self, label='BLANK'):
        super(DestinationWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel(label)
        self.pickButton = QPushButton('Pick')
        self.addDestinationBtn = QPushButton('+')
        self.removeDestinationBtn = QPushButton('-')
        self.addFromDestinationBtn = QPushButton('Pick Destinations')
        self.spinBox = QDoubleSpinBox()
        # self.label.setFixedWidth(60)
        # self.spinBox.setFixedWidth(200)
        # self.spinBox.setValue(0.5)
        # self.spinBox.setSingleStep(0.1)

        # self.spinBox.valueChanged.connect(self.sendValueChangedSignal)

        self.layout.addWidget(self.label)
        # self.layout.addWidget(self.spinBox)
        self.layout.addStretch()
        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )
        self.listwidget = QListWidget()
        self.layout.addWidget(self.listwidget)

        self.subLayout = QHBoxLayout()
        self.subLayout.addWidget(self.pickButton)
        self.subLayout.addWidget(self.addDestinationBtn)
        self.subLayout.addWidget(self.removeDestinationBtn)
        self.subLayout2 = QHBoxLayout()
        self.subLayout2.addWidget(self.addFromDestinationBtn)

        self.layout.addLayout(self.subLayout)
        self.layout.addLayout(self.subLayout2)
        self.pickButton.clicked.connect(self.pickButtonPressed)
        self.addDestinationBtn.clicked.connect(self.addButtonPressed)
        self.removeDestinationBtn.clicked.connect(self.removeButtonPressed)

    def currentItems(self):
        return [self.listwidget.item(x).text() for x in range(self.listwidget.count())]

    @Slot()
    def sendUpdateSignal(self):
        self.updatedSignal.emit(self.currentItems())

    def pickButtonPressed(self):
        sel = pm.ls(selection=True, type='transform')
        self.listwidget.clear()
        if sel:
            items = [s.stripNamespace() for s in sel]
            self.listwidget.addItems(items)
        self.sendUpdateSignal()

    def addButtonPressed(self):
        sel = pm.ls(selection=True, type='transform')
        if not sel:
            return
        items = [s.stripNamespace() for s in sel]
        currentItems = self.currentItems()
        resultItems = self.currentItems()
        #print 'before', currentItems
        self.listwidget.clear()
        for i in items:
            if i not in currentItems:
                resultItems.append(i)
        #print 'after', resultItems
        self.listwidget.addItems(resultItems)
        self.sendUpdateSignal()

    def removeButtonPressed(self):
        listItems = self.listwidget.selectedItems()
        if not listItems: return
        for item in listItems:
            self.listwidget.takeItem(self.listwidget.row(item))
        self.sendUpdateSignal()

    def refreshUI(self, targets):
        self.listwidget.clear()
        self.listwidget.addItems(targets)


class contextPickwalkWidget(QFrame):
    destinationAdded = Signal(dict)
    changed = Signal(str)

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setMaximumWidth(290)
        self.setMaximumHeight(320)
        # self.setTitle("Context pickwalks")
        self.mainLayout = QVBoxLayout()
        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        self.nameWidget = labelledLineEdit(text='Name', hasButton=True, buttonLabel='From Sel', obj=True)
        self.conditionAttrWidget = labelledLineEdit(text='Attribute', hasButton=True,
                                                    buttonLabel='From CB')
        self.conditionWidget = labelledDoubleSpinBox('Condition')
        self.destinationsWidget = DestinationWidget(label='Destinations')
        self.destinationsWidget.updatedSignal.connect(self.inputSignal_destinationsUpdated)
        self.altDestinationsWidget = DestinationWidget(label='Alt Destinations')
        self.altDestinationsWidget.updatedSignal.connect(self.inputSignal_altDestinationsUpdated)
        self.mainLayout.addWidget(self.nameWidget)
        self.mainLayout.addWidget(self.conditionAttrWidget)
        self.mainLayout.addWidget(self.conditionWidget)

        self.splitLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.splitLayout)
        self.splitLayout.addWidget(self.destinationsWidget)
        self.splitLayout.addWidget(self.altDestinationsWidget)

        self.newButton = QPushButton('Add New Conditional Destination')
        self.newButton.clicked.connect(self.outputSignal_newDestinationCreated)
        self.mainLayout.addWidget(self.newButton)
        # self.nameWidget.editedSignal.connect(self.inputSignal_nameChanged)
        self.conditionAttrWidget.editedSignal.connect(self.inputSignal_attributehanged)
        self.conditionWidget.editedSignal.connect(self.inputSignal_conditionhanged)

    def outputSignal_newDestinationCreated(self):
        #print 'outputSignal_newDestinationCreated'
        outData = dict()
        outData['destination'] = self.destinationsWidget.currentItems()
        outData['destinationAlt'] = self.altDestinationsWidget.currentItems()
        outData['conditionAttribute'] = self.conditionAttrWidget.lineEdit.text()
        outData['conditionValue'] = self.conditionWidget.spinBox.value()
        outData['name'] = self.nameWidget.lineEdit.text()
        self.destinationAdded.emit(outData)

    def populate(self, item, destinationData):
        #print destinationData
        self.destinationsWidget.refreshUI(destinationData.destination)
        self.altDestinationsWidget.refreshUI(destinationData.destinationAlt)
        self.conditionAttrWidget.lineEdit.setText(destinationData.conditionAttribute)
        self.conditionWidget.spinBox.setValue(destinationData.conditionValue)
        self.nameWidget.lineEdit.setText(item)

    def inputSignal_destinationsUpdated(self, items):
        print 'inputSignal_destinationsPicked,', items
        pass

    def inputSignal_altDestinationsUpdated(self, items):
        print 'inputSignal_altDestinationsPicked,', items

    def inputSignal_nameChanged(self, name):
        print 'inputSignal_nameChanged,', name

    def inputSignal_attributehanged(self, attribute):
        print 'inputSignal_namgeChanged,', attribute

    def inputSignal_conditionhanged(self, value):
        print 'inputSignal_conditionhanged,', value


class mirrorPickwalkWidget(QFrame):
    pressed = Signal(None)
    changed = Signal(str)
    fromInputOption = pm.optionVar.get('fromInputOption', '_L')
    toInputOption = pm.optionVar.get('toInputOption', '_R')
    mirrorPressed = Signal(str, str)

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.setMaximumWidth(290)
        self.mainLayout = QHBoxLayout()
        self.setStyleSheet(getqss.getStyleSheet())
        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.mainLayout)
        self.fromLabel = QLabel('Sides')

        self.fromLabel.setStyleSheet("QFrame {"
                                     "border-width: 0;"
                                     "border-radius: 0;"
                                     "border-style: solid;"
                                     "border-color: #222222}"
                                     )
        self.fromInput = QLineEdit(self.fromInputOption)
        self.toInput = QLineEdit(self.toInputOption)
        self.mirrorBtn = QPushButton('Mirror selection')
        self.mirrorBtn.clicked.connect(self.sendMirrorSignal)
        self.mainLayout.addWidget(self.fromLabel)
        self.mainLayout.addWidget(self.fromInput)
        self.mainLayout.addWidget(self.toInput)
        self.mainLayout.addWidget(self.mirrorBtn)

        self.fromLabel.setFixedWidth(48)
        # self.mainLayout.addStretch(1)

        # events
        self.fromInput.textChanged.connect(self.fromChanged)

        # line edit input mask
        #reg_ex = QRegExp("[a-z-A-Z0123456789_,]+")
        #fromInput_validator = QRegExpValidator(reg_ex, self.fromInput)
        #self.fromInput.setValidator(fromInput_validator)

    def sendMirrorSignal(self):
        self.mirrorPressed.emit(self.fromInput.text(), self.toInput.text())

    def fromChanged(self, lineEdit):
        print 'fromChanged', lineEdit

    def toChanged(self, lineEdit):
        print 'toChanged', lineEdit

    @Slot()
    def sendChangedSignal(self):
        self.changed.emit(self.currentColour, self.paletteIndex)

    @Slot()
    def sendPressedSignal(self):
        self.pressed.emit()

    def on_clicked(self, event):
        if event.button() == Qt.LeftButton:
            self.sendSelectedSignal()
            return
        elif event.button() == Qt.RightButton:
            color = QColorDialog.getColor()
            if color.isValid():
                self.setColor(color)
                self.sendChangedSignal()
            return
        return


class pickwalkRigAssignemtWindow(QMainWindow):

    def __init__(self):
        super(pickwalkRigAssignemtWindow, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
        # DATA
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.walkDataLibrary = WalkDataLibrary()
        self.defaultPickwalkDir = pm.optionVar.get('pickwalkDir',
                                                   os.path.join(os.path.normpath(os.path.dirname(__file__)),
                                                                'pickwalkData'))
        if not os.path.isdir(self.defaultPickwalkDir):
            os.mkdir(self.defaultPickwalkDir)
        self.libraryFile = pm.optionVar.get('pickwalkLibrary', 'pickwalkLibraryData.json')
        self.libraryFilePath = os.path.join(self.defaultPickwalkDir, self.libraryFile)

        if not os.path.isfile(self.libraryFilePath):
            self.createLibrary()
        else:
            self.walkDataLibrary.load(self.libraryFilePath)
        self.currentMap = None

        # Main Widgets
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbPickwwalkAssignment')

        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        self.main_layout = QHBoxLayout()
        self.left_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        main_widget.setLayout(self.main_layout)

        menu = self.menuBar()
        edit_menu = menu.addMenu('&File')

        self.addReferenceButton = QPushButton('Add Rig To Map')
        self.addReferenceButton.clicked.connect(self.addRigToMap)

        self.pickwalkMapTree = QTreeSingleViewWidget(label='Pickwalk Maps')
        self.referencedRigsTree = QTreeSingleViewWidget(label='Referenced Rigs')
        self.ignoredRigsTree = QTreeSingleViewWidget(label='Ignored Rigs')
        self.left_layout.addWidget(self.pickwalkMapTree)
        self.right_layout.addWidget(self.referencedRigsTree)
        self.right_layout.addWidget(self.addReferenceButton)
        self.right_layout.addWidget(self.ignoredRigsTree)

        self.pickwalkMapTree.pressedSignal.connect(self.mapClicked)

        self.getAllPickwalkMaps()
        self.updateUI()

    def mapClicked(self, item):
        self.currentMap = item
        self.updateReferencedRigView()

    def updateReferencedRigView(self):
        self.referencedRigsTree.updateView(self.walkDataLibrary.rigMapDict[self.currentMap])

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            cmds.workspace(q=True, directory=True),
                                            "Maya files (*.ma *.mb)")
        return fname[0] or None

    def addRigToMap(self):
        if not self.currentMap:
            return
        fname = self.browseToFile()
        if not fname:
            return None
        baseName = os.path.basename(fname)

        self.walkDataLibrary.assignRig(self.currentMap, baseName)

        self.walkDataLibrary.save(self.libraryFilePath)
        self.updateReferencedRigView()

    def updateUI(self):
        self.pickwalkMapTree.CLS = self.walkDataLibrary
        self.pickwalkMapTree.updateView(self.walkDataLibrary.rigMapDict.keys())
        self.ignoredRigsTree.updateView(self.walkDataLibrary.ignoredRigs)

    def createLibrary(self):
        #print 'createLibrary'
        self.walkDataLibrary.save(self.libraryFilePath)
        pm.optionVar['pickwalkLibrary'] = self.libraryFile

    def getAllPickwalkMaps(self):
        jsonFiles = list()
        for filename in os.listdir(self.defaultPickwalkDir):
            if filename.endswith(".json"):
                if os.path.basename(filename) == self.libraryFile:
                    continue
                jsonFiles.append(os.path.join(self.defaultPickwalkDir, filename))
        for filename in jsonFiles:
            mapName = os.path.basename(filename).split('.')[0]
            if mapName not in self.walkDataLibrary.rigMapDict.keys():
                self.walkDataLibrary.rigMapDict[mapName] = list()

        statinfo = os.access(self.libraryFilePath, os.W_OK)
        if statinfo:
            self.walkDataLibrary.save(self.libraryFilePath)
        #print self.walkDataLibrary.__dict__


class pickwalkMainWindow(QMainWindow):
    loop = False
    reciprocate = True
    endOnSelf = False

    activeObject = None

    def __init__(self):
        super(pickwalkMainWindow, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
        # DATA
        self.defaultDir = pm.optionVar.get('pickwalkDir',
                                           os.path.join(os.path.normpath(os.path.dirname(__file__)), 'pickwalkData'))
        if not os.path.isdir(self.defaultDir):
            os.mkdir(self.defaultDir)

        self.pickwalkCreator = PickwalkCreator()
        self.resize(848, self.height())
        # Main Widgets
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbPickwwalkSetup')

        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        self.main_layout = QHBoxLayout()
        self.left_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        main_widget.setLayout(self.main_layout)

        menu = self.menuBar()
        edit_menu = menu.addMenu('&File')

        add_action = QAction('Add new library', self)
        add_action.setShortcut('Ctrl+N')
        edit_menu.addAction(add_action)
        add_action.triggered.connect(self.newLibrary)

        load_action = QAction('Load (replace)', self)
        load_action.setShortcut('Ctrl+O')
        edit_menu.addAction(load_action)
        load_action.triggered.connect(self.loadLibrary)

        load_action = QAction('Load map for current rig', self)
        load_action.setShortcut('Ctrl+C')
        edit_menu.addAction(load_action)
        load_action.triggered.connect(self.loadLibraryForCurrent)

        merge_action = QAction('load (merge)', self)
        merge_action.setShortcut('Ctrl+M')
        edit_menu.addAction(merge_action)
        merge_action.triggered.connect(self.appendLibrary)

        mergeSelected_action = QAction('load to selected', self)
        edit_menu.addAction(mergeSelected_action)
        mergeSelected_action.triggered.connect(self.loadLibraryToSelection)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        edit_menu.addAction(save_action)
        save_action.triggered.connect(self.saveLibrary)

        saveAs_action = QAction('Save AS', self)
        saveAs_action.setShortcut('Ctrl+Shift+S')
        edit_menu.addAction(saveAs_action)
        saveAs_action.triggered.connect(self.saveAsLibrary)

        open_action = QAction('Open pickwalk data location', self)
        open_action.triggered.connect(self.openDataFolder)
        edit_menu.addAction(open_action)

        self.mainPickWidget = pickDirectionWidget()
        self.controlListWidget = ControlListWidget(CLS=self.pickwalkCreator, label='Controls ::')
        self.destinationListWidget = DestinationListWidget(CLS=self.pickwalkCreator, label='Destinations')
        self.mirrorWidget = mirrorPickwalkWidget()
        self.contextWidget = contextPickwalkWidget()

        self.right_layout.addWidget(self.mainPickWidget)
        self.right_layout.addWidget(self.mirrorWidget)
        self.right_layout.addWidget(self.contextWidget)
        self.right_layout.addStretch()
        # self.left_layout.addStretch(0)
        self.left_layout.addWidget(self.controlListWidget)
        self.left_layout.addWidget(self.destinationListWidget)

        # dummy = QVBoxLayout()
        # self.right_layout.addLayout(dummy)
        # self.left_layout.addStretch()
        # connect events
        self.controlListWidget.newDestinationSignal.connect(self.inputSignal_dirFromControlTreeView)
        self.controlListWidget.newConditionDestinationSignal.connect(self.inputSignal_conditionDirFromControlTreeView)
        self.destinationListWidget.applySignal.connect(self.inputSignal_applyDestinationToCurrent)
        self.destinationListWidget.pressedSignal.connect(self.inputSignal_displayConditionalDestination)
        self.mainPickWidget.setActiveObjectSignal.connect(self.inputSignal_activeObjectSet)
        self.mainPickWidget.directionPressedObjectSignal.connect(self.addPickwalk)
        self.mainPickWidget.loopChanged.connect(self.inputSignal_loopChanged)
        self.mainPickWidget.reciprocateChanged.connect(self.inputSignal_reciprocateChanged)
        self.mainPickWidget.endOnSelfChanged.connect(self.inputSignal_endOnSelfChanged)
        self.contextWidget.destinationAdded.connect(self.inputSignal_destinationAdded)
        self.mirrorWidget.mirrorPressed.connect(self.inputSignal_mirrorSelection)

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            self.defaultDir,
                                            "Pickwalk files (*.json)")
        return fname[0] or None

    def newLibrary(self):
        self.pickwalkCreator = PickwalkCreator()
        self.refreshUI()

    def loadLibraryForCurrent(self):
        # TODO - implement this to look at the main walk library and open the
        # TODO - correct map file
        #
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.load(fname)
        self.refreshUI()

    def loadLibrary(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.walkData = WalkData()
        self.pickwalkCreator.load(fname)
        self.refreshUI()

    def appendLibrary(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.load(fname)
        self.refreshUI()

    def loadLibraryToSelection(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.load(fname, controlFilter=cmds.ls(sl=True))
        self.refreshUI()

    def saveLibrary(self):
        if not self.pickwalkCreator.walkData._filePath:
            self.saveAsLibrary()
            return
        self.pickwalkCreator.walkData.save(self.pickwalkCreator.walkData._filePath)
        self.pickwalkCreator.load(self.pickwalkCreator.walkData._filePath)
        self.refreshUI()

    def saveAsLibrary(self):
        save_filename = QFileDialog.getSaveFileName(self,
                                                    "Save file as",
                                                    self.defaultDir,
                                                    "Pickwalk files (*.json)")
        if not save_filename:
            return
        if os.path.isfile(save_filename[0]):
            if self.overwriteQuery().exec_() != 1024:
                return
        self.pickwalkCreator.walkData.save(save_filename[0])
        return os.path.basename(save_filename[0])

    def overwriteQuery(self):
        msg = QMessageBox()
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Overwrite existing data?")
        msg.setWindowTitle("Existing file warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg

    def refreshUI(self):
        self.controlListWidget.CLS = self.pickwalkCreator
        self.destinationListWidget.CLS = self.pickwalkCreator

        self.updateTreeView()

    def keyPressEvent(self, event):
        #print("That's a press!")
        return super(pickwalkMainWindow, self).keyPressEvent(event)

    def inputSignal_applyDestinationToCurrent(self, item):
        #print 'inputSignal_applyDestinationToCurrent', item
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            self.pickwalkCreator.replaceDestination(original=s.split(':')[-1], new=item)

    def inputSignal_displayConditionalDestination(self, item):
        self.contextWidget.populate(item, self.pickwalkCreator.walkData.destinations[item])

    def inputSignal_conditionDirFromControlTreeView(self, item):
        #print 'inputSignal_conditionDirFromControlTreeView', item.control, item.direction
        index = self.destinationListWidget.treeView.selectedIndexes()[0]
        if not index:
            return
        destinationItem = self.destinationListWidget.model.itemFromIndex(
            self.destinationListWidget.proxyModel.mapToSource(index))
        # 'new destination item is,', item.text()
        self.pickwalkCreator.setControlDestination(item.control,
                                                   direction=item.direction,
                                                   destination=destinationItem.text())
        item.setText(destinationItem.text())

    def inputSignal_dirFromControlTreeView(self, control, direction, destination):
        #print 'inputSignal_newDestinationFromControlTreeView', control, direction, destination
        self.pickwalkCreator.setControlDestination(control,
                                                   direction=direction,
                                                   destination=destination)

    def inputSignal_activeObjectSet(self):
        sel = cmds.ls(sl=True)
        #print 'inputSignal_activeObjectSet', sel
        if not sel:
            return
        self.activeObject = sel[0]
        self.mainPickWidget.objectWidget.currentObjLabel.setText(self.activeObject)
        for control in sel:
            self.pickwalkCreator.addControl(control)
        self.updateTreeView()

    def updateTreeView(self):
        self.controlListWidget.updateView()
        self.destinationListWidget.updateView()

    def inputSignal_loopChanged(self, state):
        #print 'inputSignal_loopChanged', state
        self.loop = state

    def inputSignal_reciprocateChanged(self, state):
        #print 'inputSignal_reciprocate', state
        self.reciprocate = state

    def inputSignal_endOnSelfChanged(self, state):
        #print 'inputSignal_endOnSelfChanged', state
        self.endOnSelf = state

    def inputSignal_mirrorSelection(self, sideA, sideB):
        #print 'inputSignal_mirrorSelection', sideA, sideB
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return pm.warning('No selection')
        for s in sel:
            self.pickwalkCreator.mirror(s.split(':')[-1], [sideA, sideB])

    def inputSignal_destinationAdded(self, input):
        #print 'inputSignal_destinationAdded', input
        self.pickwalkCreator.addDestination(name=input.get('name', 'defaultName'),
                                            destination=input.get('destination', list()),
                                            destinationAlt=input.get('destinationAlt', list()),
                                            conditionAttribute=input.get('conditionAttribute', str()),
                                            conditionValue=input.get('conditionValue', 0.5))
        self.destinationListWidget.updateView()

    def addPickwalk(self, direction):
        sel = cmds.ls(selection=True, type='transform')
        #print direction, sel
        if not sel:
            return pm.warning('No selection')
        if len(sel) > 1:
            pm.warning('Adding chain style')
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction=direction,
                                                  loop=self.loop,
                                                  reciprocate=self.reciprocate,
                                                  endOnSelf=self.endOnSelf)
            self.updateTreeView()
            return

        if not self.activeObject:
            return pm.warning('Unable to add single destination with no active object')
        pm.warning('Adding single style')
        self.pickwalkCreator.setControlDestination(self.activeObject,
                                                   direction=direction,
                                                   destination=sel[0])
        self.updateTreeView()
        self.updateTreeView()
        return

    def openDataFolder(self):
        os.startfile(self.defaultDir)


class PickwalkCreator(object):
    destKey = '_dest'

    ''' Acceptable directions as keys, opposite direction as value'''
    directionsDict = {'up': 'down',
                      'down': 'up',
                      'left': 'right',
                      'right': 'left'}

    def __init__(self, namespace=str()):
        self.namespace = namespace

        self.walkData = WalkData()

    def addControl(self, control):
        control = control.split(':')[-1]
        if control not in self.walkData.objectDict.keys():
            self.walkData.objectDict[control] = WalkDirectionDict()

    def addDestination(self,
                       name=str(),
                       destination=list(),
                       destinationAlt=list(),
                       conditionAttribute=str(),
                       conditionValue=0.5):
        self.walkData.destinations[name] = WalkDatinationInfo(destination=destination,
                                                              destinationAlt=destinationAlt,
                                                              conditionAttribute=conditionAttribute,
                                                              conditionValue=conditionValue)

    def mirror(self, item, sideList=list()):
        """
        duplicates input and mirrors side info
        if any destinations are conditional, build those as well
        :param item:
        :return:
        """
        #print 'sides', sideList
        for key, walkDirection in self.walkData.objectDict.items():
            mirrorDir = dict()
            if key == item:
                #print 'need to mirror', key
                for dir, value in walkDirection.__dict__.items():
                    if not value:
                        #print dir, 'is empty'
                        mirrorDir[dir] = None
                        continue
                    if value in self.walkData.destinations.keys():
                        #print dir, 'is condition'
                        continue
                    else:
                        mirrorDir[dir] = value
                        for s in sideList:
                            if s in value:
                                mirrorDir[dir] = value.replace(s, sideList[not sideList.index(s)])
                #print 'mirrorDir', mirrorDir

    def replaceDestination(self, original=str, new=str):
        """
        replaces all occurrences of original with new
        :param original:
        :param new:
        :return:
        """
        for walkDirection in self.walkData.objectDict.values():
            for dir, value in walkDirection.__dict__.items():
                #print 'dir', dir, 'value', value, 'o', original, 'n', new
                if value == original:
                    walkDirection.__dict__[dir] = new

    def setControlDestination(self, control,
                              direction=str(),
                              destination=str()):
        # add control entry in case it is not already there
        self.addControl(control)
        if destination in self.walkData.destinations.keys():
            self.walkData.objectDict[control][direction] = destination
        else:
            # destination is probably one object, just set it as a string
            #print 'simple destination, object only'
            self.walkData.objectDict[control][direction] = destination

    def addPickwalkChain(self,
                         controls=list(),
                         direction=str(),
                         loop=False,
                         reciprocate=True,
                         endOnSelf=False):
        if not controls:
            return cmds.error('no nodes defined for walk')
        if not isinstance(controls, list):
            controls = [controls]
        controls = [c.split(':')[-1] for c in controls]
        reciprocalIndexes = [None] * len(controls)
        destinationIndexes = [None] * len(controls)
        # print destinationIndexes
        # get the corresponding walk indexes
        for index, value in enumerate(controls):
            # if this is the last index, pick to loop or not
            if index == (len(controls) - 1):
                if loop:
                    # print 'loop', index, (index + 1) % len(nodes)
                    destinationIndexes[index] = (index + 1) % len(controls)

                elif endOnSelf:
                    # not looping so set the node to end at this object
                    destinationIndexes[index] = index
            else:
                # print 'meh', index, index + 1
                destinationIndexes[index] = index + 1
            # get reciprocal indexes
            if index == 0:
                if loop:
                    reciprocalIndexes[index] = len(controls) - 1
            else:
                reciprocalIndexes[index] = index - 1

        infoNodes = [None] * len(controls)
        for index, value in enumerate(controls):
            infoNodes[index] = value

        for index, value in enumerate(controls):
            # get the next index and connect it up to this if reciprocating
            if destinationIndexes[index] is not None:
                self.setControlDestination(value,
                                           direction=direction,
                                           destination=infoNodes[destinationIndexes[index]])
        if reciprocate:
            for index, value in enumerate(reciprocalIndexes):
                if value is not None:
                    self.setControlDestination(controls[index],
                                               direction=self.directionsDict[direction],
                                               destination=infoNodes[value])

    def load(self, walkDataFile, controlFilter=list()):
        """
        Load the walk data file and rebuild the walk info
        :param walkDataFile:
        :return:
        """
        # TODO - move this entirely to the WalkData class?
        #print 'loading data', walkDataFile
        filter = False
        jsonObjectInfo = json.load(open(walkDataFile))

        if len(controlFilter):
            # strip namespace
            controlFilter = [c.split(':')[-1] for c in controlFilter]
            allDestinations = list()
            for key, value in jsonObjectInfo['objectDict'].items():
                if key not in controlFilter:
                    jsonObjectInfo['objectDict'].pop(key)
                allDestinations.append(value)
            for key, destination in jsonObjectInfo['destinations'].items():
                if key not in allDestinations:
                    jsonObjectInfo['destinations'].pop(key)
        #self.walkData.destinations = jsonObjectInfo['destinations']
        for key, destination in jsonObjectInfo['destinations'].items():
            self.addDestination(name=key,
                                destination=destination['destination'],
                                destinationAlt=destination['destinationAlt'],
                                conditionAttribute=destination['conditionAttribute'],
                                conditionValue=destination['conditionValue'])
        # self.walkData.destinations = dict()
        #print 'objectDict', jsonObjectInfo['objectDict'].keys()

        for key, value in jsonObjectInfo['objectDict'].items():
            self.addControl(key)
            #print key, value, type(value)
            for dKey, dValue in value.items():
                self.setControlDestination(key,
                                           direction=dKey,
                                           destination=dValue)

        self.walkData._filePath = walkDataFile
