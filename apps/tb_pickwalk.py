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
from . import *
try:
    basestring  # Python 2
except NameError:
    basestring = str  # Python 3 and later

presetPrefix = 'pwref_'

defaultToStandardAtDeadEndOption = 'defaultToStandardAtDeadEndOption'
walkMultipleObjectsOption = 'walkMultipleObjectsOption'

saveOnUpdateOption = 'tbPickwalkSaveOnUpdate'
autoApplyOption = 'tbPickwalkAutoApply'
recordDemonstrationOption = 'tbPickwalkRecordDemonstration'
skipHiddenDestinationsOption = 'tbPickwalkSkipHiddenDestinations'

getStylesheet = getqss.getStyleSheet()

ToolTip_ctrlClickSelect = 'ctrl + click to select control in scene'
ToolTip_destinationPicker = 'ctrl + click to set from sceme selection' \
                            '\n\tMultiple objects will be added as a new contextual destination. \nshift + click to select currently highlighted destination'
ToolTip_DestinationCtrlClickSet = 'ctrl + click to load destination info'
ToolTip_QuickLeftRight = 'Quick add looping left/right pickwalk'
ToolTip_DownUp = 'Quick add down/up pickwalk, last control ends on self'
ToolTip_DownMulti = 'Quick add down from one object to many (e.g. Hand to Finger controls)\n First selection is the control, others are the destination'
ToolTip_UpMulti = 'Quick add up from many to one (e.g. Finger controls to hand)\n First control is the destination'
ToolTip_AddRigToMap = 'Select a map from the pickwalk map list to assign a rig file to it'


walkDirections = ['up', 'down', 'left', 'right']
skipDirections = ['upSkip', 'downSkip', 'leftSkip', 'rightSkip']

lockedIcon = 'nodeGrapherLocked.png'
unlockedIcon = 'nodeGrapherUnlocked.png'
btnWidth = 80  * dpiScale()


def getFileStamp(filePath):
    """
    Cheap fingerprint (modified time, size) used to tell if a file has changed on disk since it was last
    read, so the pickwalk maps can be cached in memory instead of being re-parsed on every lookup.
    Returns None if the file is missing.
    """
    try:
        stat = os.stat(filePath)
    except OSError:
        return None
    return stat.st_mtime, stat.st_size


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
        self.mirrorNames = dict()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def toJson(self, selectionFilter=list()):
        jsonData = '''{}'''
        self.jsonObjectInfo = json.loads(jsonData)
        self.jsonObjectInfo['destinations'] = {key: value.toJson() for key, value in self.destinations.items()}
        self.jsonObjectInfo['objectDict'] = {key.split(':')[-1]: value.toJson() for key, value in
                                             self.objectDict.items()}
        self.jsonObjectInfo['categoryKeys'] = {key: value for key, value in self.categoryKeys.items()}
        self.jsonObjectInfo['mirrorNames'] = {key: value for key, value in self.mirrorNames.items()}

        controlKeys = [x for x in self.jsonObjectInfo['objectDict'].keys()]
        if selectionFilter:
            strippedControls = [s.rsplit(':')[-1] for s in selectionFilter]
            for k in controlKeys:
                if k not in strippedControls:
                    self.jsonObjectInfo['objectDict'].pop(k)

    def save(self, filePath, selectionFilter=list()):
        """

        :return:
        """
        self._filePath = filePath
        self.setName(filePath)
        self.toJson(selectionFilter=selectionFilter)
        fileName = os.path.join(filePath)
        jsonString = json.dumps(self.jsonObjectInfo, indent=4, separators=(',', ': '))
        jsonFile = open(fileName, 'w')

        jsonFile.write(jsonString)
        jsonFile.close()

        # the file on disk no longer matches whatever is cached for it
        Pickwalk.invalidateMapCache(fileName)

    def setName(self, filePath):
        name = filePath.split('/')[-1].split('.')[0]
        name = name.split('\\')[-1]
        self.name = name

    def setLastUsedIndex(self, node):
        for key, value in self.destinations.items():
            if node in value.destination:
                self.destinations[key]._lastIndex = value.destination.index(node)
            elif node in value.destinationAlt:
                self.destinations[key]._lastIndex = value.destinationAlt.index(node)

    def walk(self, namespace=str(), node=str(), direction=str()):
        if not namespace.endswith(":"):
            namespace = namespace+':'
        # do a check on walk for current object in any destination objects, set the appropriate index
        if node not in self.objectDict.keys():
            return None
        destinationInfo = self.objectDict[node][direction]
        if not isinstance(destinationInfo, WalkDestinationInfo):
            # an unset direction is still a plain empty string until the map has been through a save
            return None
        self.setLastUsedIndex(node)
        return destinationInfo.resolve(namespace=namespace, walkObject=node)


class PickwalkCreator(object):
    destKey = '_dest'

    ''' Acceptable directions as keys, opposite direction as value for mirroring'''
    directionsDict = {'up': 'up',
                      'down': 'down',
                      'left': 'right',
                      'right': 'left'}
    reciprocalDirectionsDict = {'up': 'down',
                                'down': 'up',
                                'left': 'right',
                                'right': 'left'}

    def __init__(self, namespace=str()):
        self.namespace = namespace

        self.walkData = WalkData()
        self._processedMirrorDestinations = list()  # used when mirroring to prevent looping of recursive function?

    def validForMirror(self, input, sideList):
        for s in sideList:
            if s in input:
                return True
        return False

    def getMirrorName(self, input, sideList):
        for s in sideList:
            if s in input:
                return input.replace(s, sideList[not sideList.index(s)])
        return input

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
        self.walkData.destinations[name] = WalkDestinationInfo(destination=destination,
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
        # for key, walkDirection in self.walkData.objectDict.items():

        for key in [x for x in self.walkData.objectDict.keys()]:
            mirrorDir = dict()
            if key == item:
                if not self.validForMirror(key, sideList):
                    continue
                for dir, value in self.walkData.objectDict[key].__dict__.items():
                    found = False
                    if not value:
                        mirrorDir[dir] = None
                        continue

                    # add the mirror key to the destination list, mirror it
                    mirrorDir[dir] = self.mirrorWalkDestination(destinationInfo=value, sideList=sideList)

                mirrorKey = self.getMirrorName(key, sideList)

                for dKey, dValue in mirrorDir.items():
                    if isinstance(dValue, str):
                        self.setControlDestination(mirrorKey,
                                                   direction=dKey,
                                                   destination=dValue)
                    elif isinstance(dValue, dict):
                        self.setControlDestination(mirrorKey,
                                                   direction=dKey,
                                                   destination=dValue['destination'],
                                                   destinationAlt=dValue['destinationAlt'],
                                                   conditionAttribute=dValue['conditionAttribute'],
                                                   conditionValue=dValue['conditionValue'])
                pass

    def mirrorWalkDestination(self, destinationInfo=str(), sideList=list(), processed=list()):
        """
        Mirror all the entries in the destination, the the entries are also destinations,
        recursively edit them, hopefully don't get into a loop....
        :param destinationInfo:
        :param sideList:
        :param processed:
        :return:
        """
        outData = dict()
        outData['destination'] = list()
        outData['destinationAlt'] = list()
        outData['conditionAttribute'] = None
        outData['conditionValue'] = None

        if destinationInfo.conditionValue:
            outData['conditionValue'] = destinationInfo.conditionValue
        if destinationInfo.conditionAttribute:
            outData['conditionAttribute'] = self.getMirrorName(
                destinationInfo.conditionAttribute,
                sideList)
        if destinationInfo.destination:
            outData['destination'] = [self.getMirrorName(x, sideList) for x in
                                      destinationInfo.destination]

        if destinationInfo.destinationAlt:
            outData['destinationAlt'] = [self.getMirrorName(x, sideList) for x in
                                         destinationInfo.destinationAlt]
        return outData

    def replaceDestination(self, original=str, new=str):
        """
        replaces all occurrences of original with new
        :param original:
        :param new:
        :return:
        """
        for walkDirection in self.walkData.objectDict.values():
            for dir, value in walkDirection.__dict__.items():
                if value == original:
                    walkDirection.__dict__[dir] = new

    def setControlDestination(self, control,
                              direction=str(),
                              destination=str(),
                              destinationAlt=str(),
                              conditionAttribute=str(),
                              conditionValue=0.5):
        '''

        '''
        # add control entry in case it is not already there
        # TODO add logic here to strip out bad data

        control = str(control).split(':')[-1]
        self.addControl(control)
        if destination:
            if not isinstance(destination, list):
                destination = [destination]
        if destinationAlt:
            if not isinstance(destinationAlt, list):
                destinationAlt = [destinationAlt]
        destinationInfo = WalkDestinationInfo(destination=destination,
                                              destinationAlt=destinationAlt,
                                              conditionAttribute=conditionAttribute,
                                              conditionValue=conditionValue)

        self.walkData.objectDict[control][direction] = destinationInfo

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

        firstControl = controls[0]
        lastControl = controls[-1]
        opposite = self.reciprocalDirectionsDict[direction]
        firstContolInTarget = self.walkData.objectDict.get(firstControl,
                                                           WalkDirectionDict()).__dict__.get(opposite, None)
        lastControlOutTarget = self.walkData.objectDict.get(lastControl,
                                                            WalkDirectionDict()).__dict__.get(direction, None)


        fwdControls = [c for c in controls]
        bwdControls = [c for c in controls]
        fwdControls.append(fwdControls.pop(0))
        bwdControls.insert(0, bwdControls.pop(-1))
        '''

        '''
        if not loop:
            fwdControls.pop(-1)
            fwdControls.append(None)
            bwdControls.pop(0)
            bwdControls.insert(0, None)

        if endOnSelf:
            fwdControls.pop(-1)
            fwdControls.append(controls[-1])

        '''
        if lastControlOutTarget:
            fwdControls.pop(-1)
            fwdControls.append(None)

        if firstContolInTarget:
            bwdControls.pop(0)
            bwdControls.insert(0, None)
        '''
        for control, fwdTarget, bwdTarget in zip(controls, fwdControls, bwdControls):

            if fwdTarget is not None:
                self.setControlDestination(control,
                                           direction=direction,
                                           destination=fwdTarget)
            if not reciprocate:
                continue
            if bwdTarget is None:
                continue
            self.setControlDestination(control,
                                       direction=opposite,
                                       destination=bwdTarget)

    def getNodeInfoFromRig(self, control):
        """
        Used to grab info from existing message/string attributes on a rig and dump them
        into the walk data
        :param control:
        :return:
        """
        controlName = control.split(':')[-1]
        self.addControl(controlName)
        userAttrs = cmds.listAttr(control, userDefined=True)
        if not userAttrs:
            return
        userAttrs = set(userAttrs)
        for direction, values in Pickwalk().pickwalkAttributeNames.items():
            matching = set(values) & userAttrs
            for m in matching:
                attrType = cmds.getAttr(control + '.' + m, type=True)
                destination = None
                if attrType == 'message':
                    destination = cmds.listConnections(control + '.' + m, source=True, destination=False)
                elif attrType == 'string':
                    destination = cmds.getAttr(control + '.' + m)
                if destination:
                    if isinstance(destination, list):
                        if len(destination) > 1:
                            self.addDestination(
                                name=controlName + '_in',
                                destination=[d.split(':')[-1] for d in destination])
                            continue
                        else:
                            destination = destination[0]
                    self.walkData.objectDict[controlName][direction] = destination.split(':')[-1]

    """ multi object modes etc, called from popups and ui """

    def quickUpFromMulti(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No objects selected')
        if len(sel) > 1:
            # cmds.warning('inputSignal_quickUpFromMulti')
            control = sel[0].split(':')[-1]
            targets = [s.split(':')[-1] for s in sel[1:]]
            for s in targets:
                self.setControlDestination(s,
                                           direction='up',
                                           destination=control)

    def quickDownToMulti(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No objects selected')
        if len(sel) > 1:
            control = sel[0].split(':')[-1]
            targets = [s.split(':')[-1] for s in sel[1:]]
            name = control + '_' + targets[0] + '_mult'
            self.addDestination(name=name,
                                destination=targets,
                                destinationAlt=list(),
                                conditionAttribute=str(),
                                conditionValue=0.5)
            self.setControlDestination(control,
                                       direction='down',
                                       destination=name)
            return

    def quickLeftRight(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No objects selected')
        if len(sel) > 1:
            self.addPickwalkChain(controls=sel,
                                  direction='left',
                                  loop=True,
                                  reciprocate=True,
                                  endOnSelf=False)
            return

    def quickUpDown(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No objects selected')
        if len(sel) > 1:
            self.addPickwalkChain(controls=sel,
                                  direction='down',
                                  loop=False,
                                  reciprocate=True,
                                  endOnSelf=True)
            return

    def load(self, walkDataFile, controlFilter=list()):
        """
        Load the walk data file and rebuild the walk info
        :param walkDataFile:
        :return:
        """
        # TODO - move this entirely to the WalkData class?

        filter = False
        try:
            jsonObjectInfo = json.load(open(walkDataFile))
        except ValueError:  # includes simplejson.decoder.JSONDecodeError
            jsonData = '''{}'''
            jsonObjectInfo = json.loads(jsonData)

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
        # self.walkData.destinations = jsonObjectInfo['destinations']
        for key, destination in jsonObjectInfo['destinations'].items():
            self.addDestination(name=key,
                                destination=destination['destination'],
                                destinationAlt=destination['destinationAlt'],
                                conditionAttribute=destination['conditionAttribute'],
                                conditionValue=destination['conditionValue'])


        for key, value in jsonObjectInfo['objectDict'].items():
            self.addControl(key)

            for dKey, dValue in value.items():
                if isinstance(dValue, basestring):
                    self.setControlDestination(key,
                                               direction=dKey,
                                               destination=dValue)
                else:
                    self.setControlDestination(key,
                                               direction=dKey,
                                               destination=dValue['destination'],
                                               destinationAlt=dValue['destinationAlt'],
                                               conditionAttribute=dValue['conditionAttribute'],
                                               conditionValue=dValue['conditionValue'])

        mirrorNames = jsonObjectInfo.get('mirrorNames', dict())

        # replace the names in the walkdata for ones in the character (if existing)
        self.walkData.mirrorNames['left'] = mirrorNames.get('left', '_L')
        self.walkData.mirrorNames['right'] = mirrorNames.get('right', '_R')
        self.walkData._filePath = walkDataFile
        self.walkData.setName(walkDataFile)

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('pickwalk'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbAssignExistingPickwalkCondition',
                                     annotation='Open the conditional pickwalk creator UI',
                                     category=self.category,
                                     help='Open the conditional pickwalk creator UI',
                                     command=['Pickwalk.openAssignExistingConditionUI()']))

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

        self.addCommand(self.tb_hkey(name='tbPickwalkUpCreate',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('up', condition=False)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkDownCreate',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('down', condition=False)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkLeftCreate',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('left', condition=False)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkRightCreate',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('right', condition=False)"]))

        self.addCommand(self.tb_hkey(name='tbPickwalkUpCreateCondition',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('up', condition=True)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkDownCreateCondition',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('down', condition=True)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkLeftCreateCondition',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('left', condition=True)"]))
        self.addCommand(self.tb_hkey(name='tbPickwalkRightCreateCondition',
                                     annotation='Create a new pickwalk, raise the ui if needed',
                                     category=self.category,
                                     command=["Pickwalk.walkCreate('right', condition=True)"]))

        self.setCategory(self.helpStrings.category.get('markingMenus'))
        self.addCommand(self.tb_hkey(name='tbPickwalkMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['Pickwalk.openMM()']))
        self.addCommand(self.tb_hkey(name='tbPickwalkMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['Pickwalk.closeMM()']))

        self.setCategory(self.helpStrings.category.get('ui'))
        self.addCommand(self.tb_hkey(name='tbOpenPickwalkCreator',
                                     annotation='OpenPickwalkCreator',
                                     category=self.category,
                                     command=['Pickwalk.openCreator()'],
                                     help=self.helpStrings.OpenPickwalkCreator))
        self.addCommand(self.tb_hkey(name='tbOpenPickwalkLibrary',
                                     annotation='OpenPickwalkLibrary',
                                     category=self.category,
                                     command=['Pickwalk.openLibrary()'],
                                     help=self.helpStrings.OpenPickwalkLibrary))
        self.addCommand(self.tb_hkey(name='tbOpenPickwalkConditionUI',
                                     annotation='Open the conditional pickwalk creator UI',
                                     category=self.category,
                                     help='Open the conditional pickwalk creator UI',
                                     command=['Pickwalk.openPickwalkConditionUI()']))

        return self.commandList

    def assignHotkeys(self):
        return


class Pickwalk(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Pickwalk'
    libraryName = 'pickwalkLibraryData'
    subfolder = 'pickwalkData'
    dataPath = None
    defaultPickwalkDir = None
    hotkeyClass = None
    funcs = None
    win = None
    assignmentWin = None
    saveOnUpdateOption = saveOnUpdateOption
    autoApplyOption = autoApplyOption
    recordDemonstrationOption = recordDemonstrationOption
    skipHiddenDestinationsOption = skipHiddenDestinationsOption
    defaultToStandardAtDeadEndOption = defaultToStandardAtDeadEndOption
    walkMultipleObjectsOption = walkMultipleObjectsOption

    # record by demonstration - tag a walk in one rig state, flip the rig, tag it again, and the two
    # get folded into a single conditional entry instead of the second one overwriting the first
    _walkStateSnapshots = dict()  # (mapName, namespace, control, direction): state at the time of tagging
    # a walk that dead ended on a hidden destination, so picking a replacement knows what was already
    # there and can keep it as the other branch instead of overwriting it
    _pendingDeadEnds = dict()  # (mapName, namespace, control, direction): the destination that was hidden
    walkStateSnapshotLifetime = 1800  # seconds, a snapshot older than this is too stale to trust
    conditionTraceMaxDepth = 12
    conditionTraceMaxNodes = 200

    transformTranslateDict = dict()
    transformRotateDict = dict()

    walkDataLibrary = str()
    pickwalkData = dict()
    rigToWalkDataDict = dict()

    jsonFiles = list()
    libraryFile = None
    libraryFilePath = None
    # cache state - file stamps of everything that has been read off disk, so nothing gets re-parsed needlessly
    _mapStamps = dict()  # mapName: file stamp of the walk data that is currently in pickwalkData
    _libraryStamp = None  # file stamp of the library map currently held in walkDataLibrary
    _pickwalkDirStamp = None  # file stamp of the pickwalk directory, changes when maps are added/removed
    _creatorStamp = None  # file stamp of the map currently loaded into the shared pickwalkCreator
    _initialised = False

    fingerNames = [['thumb', 'Thumb', 'Thumb', 'Thumb'],
                   ['index', 'Index', 'IndexFinger', 'Index'],
                   ['middle', 'Middle', 'MiddleFinger', 'Mid'],
                   ['ring', 'Ring', 'RingFinger', 'Ring'],
                   ['pinky', 'Pinky', 'PinkyFinger', 'Pinkie']]

    walkDirectionNames = {'up': 'pickUp',
                          'down': 'pickDown',
                          'left': 'pickLeft',
                          'right': 'pickRight',
                          }

    pickwalkAttributeNames = {'up': [walkDirectionNames['up'],
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
                                       'zooWalkleft'],
                              'right': [walkDirectionNames['right'],
                                        '_pickwalk_right',
                                        'cgTkPickWalkright',
                                        'zooWalkright'],
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

    walkCreateHotkeyMap = {'up': 'tbPickwalkUpCreate',
                           'down': 'tbPickwalkDownCreate',
                           'left': 'tbPickwalkLeftCreate',
                           'right': 'tbPickwalkRighCreate',
                           }
    walkCreateConditionHotkeyMap = {'up': 'tbPickwalkUpCreateCondition',
                                    'down': 'tbPickwalkDownCreateCondition',
                                    'left': 'tbPickwalkLeftCreateCondition',
                                    'right': 'tbPickwalkRightCreateCondition',
                                    }
    WASDwalkHotkeyMap = {'w': 'tbPickwalkUp',
                         's': 'tbPickwalkDown',
                         'a': 'tbPickwalkLeft',
                         'd': 'tbPickwalkRight',
                         }
    walkIncrementMap = {'up': -1,
                        'down': 1,
                        'left': 0,
                        'right': 0,
                        }

    pickwalkCreator = PickwalkCreator()

    def __new__(cls):
        """
        Pickwalk() is called all over the place (including from inside the walk itself), so the disk work
        only happens the first time. Use refreshWalkData()/forceReloadData() to pick up changes after that.
        """
        if Pickwalk.__instance is None:
            Pickwalk.__instance = object.__new__(cls)

            Pickwalk.__instance.val = cls.toolName
            Pickwalk.__instance.newConditionPopup = None
            Pickwalk.__instance.existingConditionPopup = None
            Pickwalk.__instance.mirrorPopup = None
            Pickwalk.__instance.funcs = Functions()
            Pickwalk.__instance.initData()
            Pickwalk.__instance.refreshWalkData()
        return Pickwalk.__instance

    def __init__(self):
        if Pickwalk._initialised:
            return
        Pickwalk._initialised = True
        self.hotkeyClass = hotkeys()
        set_option_var(self.saveOnUpdateOption, get_option_var(self.saveOnUpdateOption, True))
        set_option_var(self.autoApplyOption, get_option_var(self.autoApplyOption, True))
        set_option_var(self.recordDemonstrationOption, get_option_var(self.recordDemonstrationOption, True))
        set_option_var(self.skipHiddenDestinationsOption,
                       get_option_var(self.skipHiddenDestinationsOption, True))

    def initData(self):
        super(Pickwalk, self).initData()
        self.defaultPickwalkDir = os.path.normpath(os.path.join(self.dataPath, self.subfolder))
        if not os.path.isdir(self.defaultPickwalkDir):
            os.mkdir(self.defaultPickwalkDir)

        self.loadWalkLibrary()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(Pickwalk, self).optionUI()
        # self.widget.setGeometry(600, 100, 1000, 900)
        openLibrary = QPushButton('Open Pickwalk library')
        openLibrary.clicked.connect(self.openLibrary)
        self.layout.addWidget(openLibrary)

        openCreator = QPushButton('Open Pickwalk creator')
        openCreator.clicked.connect(self.openCreator)
        self.layout.addWidget(openCreator)

        endOptionWidget = optionVarBoolWidget('Default to standard walk on empty custom map ',
                                              self.defaultToStandardAtDeadEndOption)
        walkMultipleOptionWidget = optionVarBoolWidget('Walk multiple objects at once ',
                                                       self.walkMultipleObjectsOption)
        recordDemonstrationWidget = optionVarBoolWidget('Offer contextual walks when a walk is re-tagged '
                                                        'in a different rig state ',
                                                        self.recordDemonstrationOption)
        skipHiddenWidget = optionVarBoolWidget('Ask for a new destination when the target is hidden ',
                                               self.skipHiddenDestinationsOption)
        self.layout.addWidget(endOptionWidget)
        self.layout.addWidget(walkMultipleOptionWidget)
        self.layout.addWidget(recordDemonstrationWidget)
        self.layout.addWidget(skipHiddenWidget)

        layout = QHBoxLayout()
        arrowLabel = QLabel('Arrow keys for pickwalking')
        assignArrowHotkeys = QPushButton('Assign arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(arrowLabel)
        self.layout.addLayout(layout)

        layout = QHBoxLayout()
        shiftArrowLabel = QLabel('Shift+Alt WASD for pickwalking')
        assignWASDHotkeys = QPushButton('Assign ShiftAlt + WASD keys')
        assignWASDHotkeys.clicked.connect(self.assignWASDHotkeys)
        layout.addWidget(assignWASDHotkeys)
        layout.addWidget(shiftArrowLabel)
        self.layout.addLayout(layout)

        layout = QHBoxLayout()
        WASDLabel = QLabel('Shift arrow keys for additive pickwalking')
        assignArrowHotkeys = QPushButton('Assign shift + arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignShiftArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(WASDLabel)
        self.layout.addLayout(layout)

        layout = QHBoxLayout()
        ctrlArrowLabel = QLabel('Ctrl arrow keys for pickwalk creation')
        assignArrowHotkeys = QPushButton('Assign ctrl + arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignCtrlArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(ctrlArrowLabel)
        self.layout.addLayout(layout)

        layout = QHBoxLayout()
        ctrlShiftrrowLabel = QLabel('Ctrl shift arrow keys for conditional pickwalk creation')
        assignArrowHotkeys = QPushButton('Assign ctrl + shift + arrow keys')
        assignArrowHotkeys.clicked.connect(self.assignCtrlShiftArrowHotkeys)
        layout.addWidget(assignArrowHotkeys)
        layout.addWidget(ctrlShiftrrowLabel)
        self.layout.addLayout(layout)

        layout = QHBoxLayout()
        revertArrowLabel = QLabel('Revert Arrow keys to default')
        revertArrowHotkeys = QPushButton('Revert')
        revertArrowHotkeys.clicked.connect(self.revertArrowHotkeys)
        layout.addWidget(revertArrowHotkeys)
        layout.addWidget(revertArrowLabel)
        self.layout.addLayout(layout)

        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='Pickwalk Creator', image='walk.png', command='tbOpenPickwalkCreator', sourceType='mel',
                    parent=parentMenu)
        cmds.menuItem(label='Pickwalk Library', image='QR_settings.png', command='tbOpenPickwalkLibrary',
                    sourceType='mel', parent=parentMenu)

    def build_MM(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            cmds.menuItem(label='tbPickwalk - Select part of the rig',
                          divider=0,
                          boldFont=True,
                          enable=False,
                          radialPosition='N'
                          )
            return

        cmds.menuItem(label='tbPickwalk UI',
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='tbPickwalk',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Open Creator UI',
                      command=self.openCreator,
                      )
        cmds.menuItem(label='Open Library UI',
                      command=self.openLibrary,
                      )

        cmds.menuItem(label='Left',
                      command=create_callback(self.walkCreate, 'left', condition=False),
                      radialPosition='W'
                      )
        cmds.menuItem(label='Right',
                      command=create_callback(self.walkCreate, 'right', condition=False),
                      radialPosition='E'
                      )
        cmds.menuItem(label='Up',
                      command=create_callback(self.walkCreate, 'up', condition=False),
                      radialPosition='N'
                      )
        cmds.menuItem(label='Down',
                      command=create_callback(self.walkCreate, 'down', condition=False),
                      radialPosition='S'
                      )
        cmds.menuItem(label='Add Down To Many',
                      command=self.quickDownToMulti,
                      radialPosition='SE'
                      )
        cmds.menuItem(label='Add Up From Many',
                      command=self.quickUpFromMulti,
                      radialPosition='NE'
                      )

        cmds.menuItem(label='Add New Condition',
                      command=self.openPickwalkConditionUI,
                      )
        # cmds.menuItem(label='Add Existing Condition',
        #               command=self.openAssignExistingConditionUI,
        #               annotation='test'
        #               )
        cmds.menuItem(label='Mirror selected controls',
                      command=self.openMirrorSelectedUI,
                      annotation='test'
                      )

    def openLibrary(self, *args):
        self.assignmentWin = pickwalkRigAssignemtWindow()
        self.assignmentWin.show()

    def openCreator(self, *args):
        try:
            self.win.show()
        except:
            self.win = pickwalkMainWindow()
            self.win.show()

    def revertArrowHotkeys(self):
        pass

    def assignArrowHotkeys(self):
        for direction, command in self.walkHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        name=command + 'NameCommand')

    def assignShiftArrowHotkeys(self):
        for direction, command in self.walkAddHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=True,
                        name=command + 'NameCommand')

    def assignCtrlArrowHotkeys(self):
        for direction, command in self.walkCreateHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=False,
                        ctrlModifier=True,
                        name=command + 'NameCommand')

    def assignCtrlShiftArrowHotkeys(self):
        for direction, command in self.walkCreateConditionHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=True,
                        ctrlModifier=True,
                        name=command + 'NameCommand')

    def assignWASDHotkeys(self):
        for direction, command in self.walkHotkeyMap.items():
            cmds.hotkey(keyShortcut=direction,
                        shiftModifier=True,
                        altModifier=True,
                        name=command + 'NameCommand')

    @classmethod
    def invalidateMapCache(cls, filePath):
        """
        Flag a walk data file as changed so the next data refresh re-reads it. Called from WalkData.save()
        so every save site invalidates without having to remember to.
        """
        mapName = os.path.basename(filePath).split('.')[0]
        cls._mapStamps.pop(mapName, None)
        cls._pickwalkDirStamp = None

    def refreshWalkData(self, force=False):
        """
        Bring the cached maps up to date with what is on disk. Unchanged files are left alone.
        """
        self.getAllPickwalkMaps(force=force)
        self.initialiseWalkData(force=force)

    def loadWalkLibrary(self, force=False):
        self.libraryFile = self.libraryName + '.json'
        self.libraryFilePath = os.path.join(self.defaultPickwalkDir, self.libraryFile)

        if not os.path.isfile(self.libraryFilePath):
            self.walkDataLibrary = WalkDataLibrary()
            self.savePickwalkLibraryMap()
        else:
            libraryStamp = getFileStamp(self.libraryFilePath)
            if force or Pickwalk._libraryStamp != libraryStamp or not isinstance(self.walkDataLibrary,
                                                                                 WalkDataLibrary):
                self.walkDataLibrary = WalkDataLibrary()
                self.walkDataLibrary.load(self.libraryFilePath)
                Pickwalk._libraryStamp = libraryStamp

        for key, values in self.walkDataLibrary.rigMapDict.items():
            for v in values:
                self.rigToWalkDataDict[v] = key
        return self.walkDataLibrary

    def getAllPickwalkMaps(self, force=False):
        """
        Collect the walk data files on disk. The directory is only re-listed when its contents have changed,
        and the library map is only written back out when a new map file was actually picked up.
        """
        dirStamp = getFileStamp(self.defaultPickwalkDir)
        if not force and self.jsonFiles and dirStamp is not None and dirStamp == Pickwalk._pickwalkDirStamp:
            return

        self.jsonFiles = list()
        for filename in os.listdir(self.defaultPickwalkDir):
            if filename.endswith(".json"):
                if os.path.basename(filename) == self.libraryFile:
                    continue
                self.jsonFiles.append(os.path.join(self.defaultPickwalkDir, filename))

        newMaps = False
        for filename in self.jsonFiles:
            mapName = os.path.basename(filename).split('.')[0]
            if mapName not in self.walkDataLibrary.rigMapDict.keys():
                self.walkDataLibrary.rigMapDict[mapName] = list()
                newMaps = True

        Pickwalk._pickwalkDirStamp = dirStamp

        if newMaps:
            statinfo = os.access(self.libraryFilePath, os.W_OK)
            if statinfo:
                self.savePickwalkLibraryMap()

    def initialiseWalkData(self, force=False):
        """
        Load up all the pickwalk maps into a big dictionary.
        Only maps that are new, or whose file has changed on disk since it was last read, get parsed again.
        :return:
        """
        currentMaps = set()
        for walkData in self.jsonFiles:
            mapName = os.path.basename(walkData).split('.')[0]
            currentMaps.add(mapName)

            mapStamp = getFileStamp(walkData)
            if not force and mapName in self.pickwalkData.keys() and Pickwalk._mapStamps.get(mapName) == mapStamp:
                continue

            pickwalkCreator = PickwalkCreator()
            pickwalkCreator.load(walkData)

            self.pickwalkData[mapName] = pickwalkCreator.walkData
            Pickwalk._mapStamps[mapName] = mapStamp

        # drop maps whose files have gone away
        for mapName in [m for m in self.pickwalkData.keys() if m not in currentMaps]:
            self.pickwalkData.pop(mapName)
            Pickwalk._mapStamps.pop(mapName, None)

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

            if cmds.objExists(self.funcs.namespace(node) + cmds.getAttr(node + '.' + attribute)):
                return self.funcs.namespace(node) + destination

        elif cmds.getAttr(node + '.' + attribute, type=True) == u'message':
            # list connection to message attribute
            conns = cmds.listConnections(node + '.' + attribute, source=True, destination=False)
            # if there are connections, check what kind of node it is
            if conns:
                return conns[0]

    def findSequenceMain(self, control):
        controlList = []
        controlList = self.findSequenceRecursive(control, [control])
        return controlList

    def findSequenceRecursive(self, control, substringList):
        length = len(control)
        if length == 0:
            return substringList

        else:
            m = re.search(r'\d+$', control)
            # if the string ends in digits m will be a Match object, or None otherwise.
            if m is not None:
                dat = m.group()
                next = (str(int(dat) + 1).zfill(len(str(dat))))

                nextControl = control[:len(control) - len(str(dat))] + next
                if cmds.objExists(nextControl):
                    substringList.append(nextControl)
                    self.findSequenceRecursive(nextControl, substringList)
            return substringList

    def createDestination(self, controlA, controlB, direction):
        self.loadLibraryForCurrent()
        self.pickwalkCreator.addPickwalkChain(
            controls=[controlA, controlB],
            direction=direction,
            loop=False,
            reciprocate=True,
            endOnSelf=False)
        self.saveLibrary()
        self.forceReloadData()

    def getNamespace(self, node):
        """
        Namespace of a node with a trailing colon, or an empty string, so it can always be prefixed onto
        a stripped control name.
        """
        namespace = self.funcs.namespace(str(node))
        if namespace and not namespace.endswith(':'):
            namespace += ':'
        return namespace

    def isPickable(self, node):
        """
        Is this control actually available to the animator right now - visible, and not hidden by a parent,
        a display layer or a draw override. Used to tell an inactive IK/FK branch from an active one.
        """
        if not cmds.objExists(node):
            return False
        current = node
        depth = 0
        while current and depth <= self.conditionTraceMaxDepth:
            if not cmds.getAttr(current + '.visibility'):
                return False
            if cmds.attributeQuery('lodVisibility', node=current, exists=True):
                if not cmds.getAttr(current + '.lodVisibility'):
                    return False
            # a display layer drives overrideEnabled/overrideVisibility through drawOverride, so reading
            # the override attributes covers display layers as well as manual draw overrides
            if cmds.attributeQuery('overrideEnabled', node=current, exists=True):
                if cmds.getAttr(current + '.overrideEnabled'):
                    if not cmds.getAttr(current + '.overrideVisibility'):
                        return False
                    # 1 is template, 2 is reference - both are on screen but cannot be selected
                    if cmds.getAttr(current + '.overrideDisplayType') in (1, 2):
                        return False
            parents = cmds.listRelatives(current, parent=True, fullPath=True)
            current = parents[0] if parents else None
            depth += 1
        return True

    def isValidWalkDestination(self, node):
        """
        A destination is only any use if the animator can actually select it. Rigs hide the inactive half
        of an IK/FK setup, so a destination that exists but is hidden is a dead end, and the walk should
        offer to pick an alternative rather than selecting something invisible.
        """
        if not cmds.objExists(node):
            return False
        if not get_option_var(self.skipHiddenDestinationsOption, True):
            return True
        return self.isPickable(node)

    def isCandidateConditionPlug(self, plug):
        """
        A plug an animator could actually flip - a numeric custom attribute that shows up in the channel box.
        """
        node = plug.split('.')[0]
        attr = plug.split('.')[-1].split('[')[0]
        if not cmds.objExists(node):
            return False
        if not cmds.attributeQuery(attr, node=node, exists=True):
            return False
        if attr not in (cmds.listAttr(node, userDefined=True) or list()):
            return False
        if cmds.getAttr(plug, lock=True):
            return False
        if not cmds.getAttr(plug, keyable=True) and not cmds.getAttr(plug, channelBox=True):
            return False
        try:
            value = cmds.getAttr(plug)
        except (RuntimeError, ValueError):
            return False
        return isinstance(value, (int, float, bool))

    def getVisibilityGatePlugs(self, node):
        """
        Every plug that can hide this control - its own visibility, its shapes, and its ancestors.
        """
        plugs = list()
        current = node
        depth = 0
        while current and depth <= self.conditionTraceMaxDepth:
            for attr in ('visibility', 'lodVisibility', 'overrideVisibility'):
                if cmds.attributeQuery(attr, node=current, exists=True):
                    plugs.append(current + '.' + attr)
            for shape in cmds.listRelatives(current, shapes=True, fullPath=True) or list():
                plugs.append(shape + '.visibility')
            parents = cmds.listRelatives(current, parent=True, fullPath=True)
            current = parents[0] if parents else None
            depth += 1
        return plugs

    def collectUpstreamCandidates(self, sourcePlug, candidates, visited, depth):
        if depth > self.conditionTraceMaxDepth or len(visited) > self.conditionTraceMaxNodes:
            return
        if sourcePlug in visited:
            return
        visited.add(sourcePlug)
        if self.isCandidateConditionPlug(sourcePlug):
            candidates.add(sourcePlug)
            return
        # not something an animator drives, keep walking back through whatever utility nodes the rig uses
        sourceNode = sourcePlug.split('.')[0]
        for nextPlug in cmds.listConnections(sourceNode, source=True, destination=False, plugs=True) or list():
            self.collectUpstreamCandidates(nextPlug, candidates, visited, depth + 1)

    def getConditionCandidatePlugs(self, node):
        """
        The plugs that gate whether a control is available, found by walking back from its visibility
        through the rig's utility nodes. Uses connections rather than attribute names, so it does not
        care what the rig calls its IK/FK switch.
        """
        candidates = set()
        if not cmds.objExists(node):
            return candidates
        visited = set()
        for plug in self.getVisibilityGatePlugs(node):
            for sourcePlug in cmds.listConnections(plug, source=True, destination=False, plugs=True) or list():
                self.collectUpstreamCandidates(sourcePlug, candidates, visited, 0)
        return candidates

    def getUserAttributePlugs(self, node):
        """
        Channel box attributes on a node - some rigs put the switch on the control being walked from
        rather than on a separate settings node.
        """
        plugs = set()
        if not cmds.objExists(node):
            return plugs
        attrs = set(cmds.listAttr(node, userDefined=True, keyable=True, scalar=True) or list())
        attrs.update(cmds.listAttr(node, userDefined=True, channelBox=True, scalar=True) or list())
        for attr in attrs:
            plug = node + '.' + attr
            if not cmds.getAttr(plug, lock=True):
                plugs.add(plug)
        return plugs

    @staticmethod
    def plugExists(plug):
        node = plug.split('.')[0]
        attr = plug.split('.')[-1].split('[')[0]
        return cmds.objExists(node) and cmds.attributeQuery(attr, node=node, exists=True)

    def getCharacterSides(self, mapName):
        CharacterTool = self.allTools.tools['CharacterTool']
        CharacterTool.loadCharacterIfNotLoaded(mapName)
        character = CharacterTool.allCharacters.get(mapName)
        if not character:
            return None, None
        return character.getSide('left'), character.getSide('right')

    def getMirroredName(self, name, mapName):
        """
        Mirror a name using the character definition's side naming. MirrorTools understands the prefix
        (L_*), suffix (*_L) and plain substring conventions, where PickwalkCreator.getMirrorName only
        handles the plain one - so this works on rigs where the naive swap silently does nothing.
        """
        left, right = self.getCharacterSides(mapName)
        if not left or not right:
            return None
        MirrorTools = self.allTools.tools['MirrorTools']
        mirrored = MirrorTools.getMirrorControl(name, left, right)
        if not mirrored or mirrored == name:
            return None
        return mirrored

    def getMirroredControl(self, control, mapName, namespace):
        """
        Mirror name for a control, or None when it has no other side or the mirror is not in the scene.
        """
        mirrored = self.getMirroredName(control, mapName)
        if not mirrored or not cmds.objExists(namespace + mirrored):
            return None
        return mirrored

    def getMirroredPlug(self, plug, mapName, namespace):
        """
        Mirror a condition attribute. The switch usually sits on a sided settings node, but some rigs keep
        one settings node with sided attributes, and some drive both sides from a single switch.
        """
        node, attr = plug.split('.', 1)

        mirrorNode = self.getMirroredControl(node, mapName, namespace)
        if mirrorNode and self.plugExists(namespace + mirrorNode + '.' + attr):
            return mirrorNode + '.' + attr

        mirrorAttr = self.getMirroredName(attr, mapName)
        if mirrorAttr and self.plugExists(namespace + node + '.' + mirrorAttr):
            return node + '.' + mirrorAttr

        # one switch driving both sides
        return plug

    def mirrorDemonstratedCondition(self, control, direction, plug, destination, destinationAlt,
                                    newDestination, threshold, namespace):
        """
        Write the same conditional entry for the other side of the character. Bails rather than guessing
        if any control involved has no mirror in the scene, so a centre control never gets a bogus entry.
        Returns True when the mirrored entry was written.
        """
        mapName = self.pickwalkCreator.walkData.name
        if not mapName:
            return False

        mirrorControl = self.getMirroredControl(control, mapName, namespace)
        if not mirrorControl:
            return False

        mirrorDestination = [self.getMirroredControl(d, mapName, namespace) for d in destination]
        mirrorDestinationAlt = [self.getMirroredControl(d, mapName, namespace) for d in destinationAlt]
        if None in mirrorDestination or None in mirrorDestinationAlt:
            return False

        self.pickwalkCreator.setControlDestination(mirrorControl,
                                                   direction=direction,
                                                   destination=mirrorDestination,
                                                   destinationAlt=mirrorDestinationAlt,
                                                   conditionAttribute=self.getMirroredPlug(plug, mapName,
                                                                                           namespace),
                                                   conditionValue=threshold)

        mirrorNewDestination = self.getMirroredControl(newDestination, mapName, namespace)
        if mirrorNewDestination:
            self.pickwalkCreator.setControlDestination(
                mirrorNewDestination,
                direction=self.pickwalkCreator.reciprocalDirectionsDict[direction],
                destination=mirrorControl)
        return True

    def getPlugName(self, plug):
        """
        node.attribute with any dag path and namespace stripped, so a condition attribute is stored the
        same way control names are and can have a namespace prefixed back on at walk time.
        """
        node, attr = plug.split('.', 1)
        return node.split('|')[-1].split(':')[-1] + '.' + attr

    def getWalkStateKey(self, control, direction, namespace):
        mapName = self.pickwalkCreator.walkData.name
        if not mapName:
            return None
        return (mapName, namespace, control, direction)

    def snapshotWalkState(self, control, destination, direction, namespace):
        """
        Remember the rig state at the moment a walk was tagged, so a later tag on the same control can
        tell whether anything about the rig actually changed in between.
        """
        key = self.getWalkStateKey(control, direction, namespace)
        if not key:
            return
        candidates = self.getConditionCandidatePlugs(namespace + destination)
        candidates.update(self.getUserAttributePlugs(namespace + control))

        values = dict()
        for plug in candidates:
            try:
                values[self.getPlugName(plug)] = cmds.getAttr(plug)
            except (RuntimeError, ValueError):
                continue

        Pickwalk._walkStateSnapshots[key] = {'destination': destination,
                                             'values': values,
                                             'frame': cmds.currentTime(query=True),
                                             'time': time.time()}

    def getDemonstratedCondition(self, control, newDestination, direction, namespace):
        """
        Decide whether a second tag on the same control is the animator demonstrating the other half of a
        switch, or just fixing a mistake. Everything here is a reason to say no - the default is that this
        is a correction, and it takes a stack of corroborating evidence to conclude otherwise.
        Returns (plug, oldDestination, oldValue, newValue) or None.
        """
        key = self.getWalkStateKey(control, direction, namespace)
        if not key:
            return None
        snapshot = Pickwalk._walkStateSnapshots.get(key)
        if not snapshot:
            return None
        if time.time() - snapshot['time'] > self.walkStateSnapshotLifetime:
            Pickwalk._walkStateSnapshots.pop(key, None)
            return None

        oldDestination = snapshot['destination']
        if oldDestination == newDestination:
            return None
        # a value that only moved because the timeline moved says nothing about intent
        if cmds.currentTime(query=True) != snapshot['frame']:
            return None
        # the old target has to have gone away and the new one has to be available. If both are pickable
        # they live in the same context, so this is a correction rather than a condition
        if self.isPickable(namespace + oldDestination):
            return None
        if not self.isPickable(namespace + newDestination):
            return None

        changed = list()
        for plug, oldValue in snapshot['values'].items():
            fullPlug = namespace + plug
            if not cmds.objExists(fullPlug.split('.')[0]):
                continue
            try:
                newValue = cmds.getAttr(fullPlug)
            except (RuntimeError, ValueError):
                continue
            if newValue != oldValue:
                changed.append((plug, oldValue, newValue))

        # nothing changed is a straight correction, several changes is too ambiguous to guess from
        if len(changed) != 1:
            return None

        plug, oldValue, newValue = changed[0]
        return plug, oldDestination, oldValue, newValue

    def promptForDemonstratedCondition(self, control, direction, plug, oldDestination, newDestination,
                                       oldValue, newValue, namespace=str()):
        mirrorControl = self.getMirroredControl(control, self.pickwalkCreator.walkData.name, namespace)
        mirrorText = '\n\nThis will also be mirrored to {}.'.format(mirrorControl) if mirrorControl else str()

        msg = QMessageBox(getMainWindow())
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle('Contextual pickwalk')
        msg.setText('{control} already walks {direction} to {old}.'.format(control=control,
                                                                          direction=direction,
                                                                          old=oldDestination))
        msg.setInformativeText('{plug} changed from {a} to {b} since then, and {old} is no longer '
                               'selectable.\n\nReplace the existing destination, or make this walk '
                               'contextual?{mirror}'.format(plug=plug, a=oldValue, b=newValue,
                                                            old=oldDestination, mirror=mirrorText))
        replaceButton = msg.addButton('Replace', QMessageBox.RejectRole)
        contextualButton = msg.addButton('Make Contextual', QMessageBox.AcceptRole)
        msg.setDefaultButton(replaceButton)
        msg.exec_()
        return msg.clickedButton() == contextualButton

    def applyDemonstratedCondition(self, control, direction, plug, oldDestination, newDestination,
                                   oldValue, newValue, namespace=str()):
        threshold = (float(oldValue) + float(newValue)) / 2.0
        # walk() returns destinationAlt when the attribute reads >= the threshold
        if float(newValue) > float(oldValue):
            destination, destinationAlt = [oldDestination], [newDestination]
        else:
            destination, destinationAlt = [newDestination], [oldDestination]

        self.pickwalkCreator.setControlDestination(control,
                                                   direction=direction,
                                                   destination=destination,
                                                   destinationAlt=destinationAlt,
                                                   conditionAttribute=plug,
                                                   conditionValue=threshold)
        # walking back the other way is unambiguous, the control you came from is always the answer
        self.pickwalkCreator.setControlDestination(newDestination,
                                                   direction=self.pickwalkCreator.reciprocalDirectionsDict[
                                                       direction],
                                                   destination=control)

        if not self.mirrorDemonstratedCondition(control, direction, plug, destination, destinationAlt,
                                                newDestination, threshold, namespace):
            # no character data, or nothing on this control has another side - fall back to the plain
            # name swap, which is all the creator's own mirror can do
            self.pickwalkCreator.mirror(control,
                                        [self.pickwalkCreator.walkData.mirrorNames.get('left', '_L'),
                                         self.pickwalkCreator.walkData.mirrorNames.get('right', '_R')])

    def handleDemonstratedWalk(self, control, destination, direction):
        """
        Called for the two object 'walk from A to B' gesture. Returns True when the tag has been turned
        into a contextual entry and the caller has nothing left to do.
        """
        if not get_option_var(self.recordDemonstrationOption, True):
            return False

        namespace = self.getNamespace(control)
        control = self.funcs.stripNamespace(str(control))
        destination = self.funcs.stripNamespace(str(destination))

        result = self.getDemonstratedCondition(control, destination, direction, namespace)
        if result:
            plug, oldDestination, oldValue, newValue = result
            if self.promptForDemonstratedCondition(control, direction, plug, oldDestination, destination,
                                                   oldValue, newValue, namespace=namespace):
                self.applyDemonstratedCondition(control, direction, plug, oldDestination, destination,
                                                oldValue, newValue, namespace=namespace)
                # the pair has been captured, a third tag should behave like a plain replace
                Pickwalk._walkStateSnapshots.pop(self.getWalkStateKey(control, direction, namespace), None)
                return True

        self.snapshotWalkState(control, destination, direction, namespace)
        return False

    def walkCreate(self, direction=str(), condition=False, *args):
        sel = cmds.ls(sl=True, type='transform')
        returnedControls = list()
        if not sel:
            return
        if direction not in self.walkDirectionNames.keys():
            return cmds.error('\nInvalid pick direction, only up, down, left, right are supported')

        self.loadLibraryForCurrent()

        if not condition and len(sel) == 2:
            if self.handleDemonstratedWalk(sel[0], sel[1], direction):
                self.saveLibrary()
                self.forceReloadData()
                return

        if not condition:
            # standard single object destination
            if len(sel) == 1:
                controlList = self.findSequenceMain(sel[0])
                if len(controlList) == 1:
                    self.pickwalkCreator.setControlDestination(sel[0],
                                                               direction=direction,
                                                               destination=sel[0])
                else:
                    self.pickwalkCreator.addPickwalkChain(
                        controls=controlList,
                        direction=direction,
                        loop=False,
                        reciprocate=True,
                        endOnSelf=False)
            elif len(sel) == 2:
                # 2 objects - create single direction pickwalk
                '''
                self.pickwalkCreator.setControlDestination(sel[0],
                                                           direction=direction,
                                                           destination=sel[1])
                '''
                if direction == 'down':
                    # if left or right, create the reverse
                    self.pickwalkCreator.addPickwalkChain(
                        controls=sel,
                        direction=direction,
                        loop=False,
                        reciprocate=True,
                        endOnSelf=False)
                elif direction == 'left' or direction == 'right':
                    self.pickwalkCreator.addPickwalkChain(
                        controls=sel,
                        direction=direction,
                        loop=True,
                        reciprocate=True,
                        endOnSelf=False)
                else:
                    self.pickwalkCreator.addPickwalkChain(
                        controls=sel,
                        direction=direction,
                        loop=False,
                        reciprocate=False,
                        endOnSelf=False)

            elif len(sel) > 2:
                # add all objects in a chain
                self.pickwalkCreator.addPickwalkChain(
                    controls=sel,
                    direction=direction,
                    loop=direction == 'left' or direction == 'right',
                    reciprocate=True,
                    endOnSelf=False)
            if direction != 'left' and direction != 'right':
                for s in sel:
                    self.pickwalkCreator.mirror(s.split(':')[-1],
                                                [self.pickwalkCreator.walkData.mirrorNames.get('left', '_L'),
                                                 self.pickwalkCreator.walkData.mirrorNames.get('right', '_R')])
        else:
            if len(sel) == 1 or len(sel) == 2:
                dlg = PickwalkNewConditionPopup()
                dlg.show()
                return
            else:
                if direction == 'down':
                    self.pickwalkCreator.quickDownToMulti()
                elif direction == 'up':
                    self.pickwalkCreator.quickUpFromMulti()

        self.saveLibrary()
        self.forceReloadData()
        return

    def recursiveLookup(self, control, attribute, source=True, destination=False):
        if cmds.attributeQuery(attribute, node=str(control), exists=True):
            targetConnections = cmds.listConnections(control + '.' + attribute, source=source, destination=destination)
            if targetConnections:
                return self.recursiveLookup(targetConnections[0], attribute, source=source, destination=destination)
        return control

    def checkDownstreamTempControls(self, control, found_controls=None):
        """
        This is used to look for temp controls, and walk to those if they exist
        """
        if found_controls is None:
            found_controls = []
        walkObject = None
        messageConnections = cmds.listConnections(control + '.message', source=False, destination=True, plugs=True)

        if not messageConnections:
            return control
        for conn in messageConnections:
            if not cmds.attributeQuery('constraintTarget', node=str(conn.split('.')[0]), exists=True):
                continue
            walkObject = self.recursiveLookDown(str(conn.split('.')[0]), 'constraintTarget', source=False, destination=True)

            if not walkObject:
                continue
            elif walkObject not in found_controls:
                found_controls.append(walkObject)
                return self.checkDownstreamTempControls(walkObject, found_controls=found_controls)
            else:
                continue
        return control

    def recursiveLookDown(self, control, attribute, source=True, destination=False):
        if cmds.attributeQuery(attribute, node=str(control), exists=True):

            targetConnections = cmds.listConnections(control + '.' + attribute, source=source, destination=destination,
                                                     plugs=True)

            if targetConnections:
                return self.recursiveLookup(targetConnections[0], attribute, source=source, destination=destination)
            else:
                return control
        return control

    def pickwalk(self, direction=str, add=False):

        sel = cmds.ls(sl=True, type='transform')
        returnedControls = list()
        finalControls = list()
        if not sel:
            self.walkStandard(direction)
            return

        if not get_option_var(self.walkMultipleObjectsOption, False):
            if not add:
                sel = [sel[-1]]

        for walkObject in sel:

            if cmds.attributeQuery('constraintTarget', node=str(walkObject), exists=True):
                walkObject = self.recursiveLookup(str(walkObject), 'constraintTarget')

            if direction not in self.walkDirectionNames.keys():
                return cmds.error('\nInvalid pick direction, only up, down, left, right are supported')

            refName, refState = self.funcs.getRefName(walkObject)

            if not refName:
                # if the object is not referenced, check the top node
                refName = self.funcs.getRefNameFromTopParent(walkObject)
                if refName == -1:
                    return

            if refName not in self.walkDataLibrary._fileToMapDict.keys():
                # check if the current file is actually defined as a rig
                if not refState:
                    # not referenced, check against UUID
                    refName = self.funcs.getRefNameFromTopParent(walkObject)

                    if not refName:
                        self.walkStandard(direction)
                        return

            if refName:
                returnedControls = self.dataDrivenWalk(direction, refName, walkObject)

                if returnedControls == False:
                    # means a standard walk has been performed
                    return

            if not returnedControls:
                # anything beyond here is using attribute based pickwalking
                userAttrs = cmds.listAttr(str(walkObject), userDefined=True)
                if not userAttrs:
                    self.walkStandard(direction)
                    return
                pickAttributes = [i for i in self.pickwalkAttributeNames[direction] if i in userAttrs]
                if not pickAttributes:
                    # didn't find any custom pickwalk attributes, use the regular walk
                    self.walkStandard(direction)
                    return

                found = False

                for walkAttribute in self.pickwalkAttributeNames[direction]:
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

            # returnedControls = [str(self.checkDownstreamTempControls(returnedControls[0]))]
            finalControls.append(str(self.checkDownstreamTempControls(returnedControls[0])))

        if add:
            finalControls = [str(s) for s in sel] + finalControls

        cmds.select(finalControls, replace=True)
        mel.eval("updateCameraPivot")

    def queryNewRig(self, refName, force=False):
        if force:
            self.queryWalkOnNewRig(refName)
            return
        if refName in self.walkDataLibrary._fileToMapDict.keys():
            return
        if refName in self.walkDataLibrary.ignoredRigs:
            return
        self.queryWalkOnNewRig(refName)

    @staticmethod
    def pad_integers(input_string):
        matches = re.findall(r'\d+', input_string)
        padded_integers = ['{:0{width}d}'.format(int(match), width=len(match)) for match in matches]
        return padded_integers

    @staticmethod
    def increment_padded_integer(input_string, offset):
        matches = re.findall(r'\d+', input_string)
        padded_integers = ['{:0{width}d}'.format(int(match), width=len(match)) for match in matches]
        incremented_integers = ['{:0{width}d}'.format(int(padded) + offset, width=len(padded)) for padded in
                                padded_integers]
        return incremented_integers[0]

    def findIncrementalControl(self, cnt, namespace=str(), offset=1):
        intParts = self.pad_integers(cnt)
        if not intParts:
            return None

        if not intParts:
            return None

        nameParts = cnt.split(intParts[-1])

        intParts[-1] = self.increment_padded_integer(intParts[-1], offset)
        outStr = nameParts[0] + str(intParts[-1]) + nameParts[-1]

        return outStr

    def dataDrivenWalk(self, direction, refName, walkObject):
        returnedControls = list()
        walkObjectStripped = self.funcs.stripNamespace(walkObject)
        walkObjectNS = self.funcs.namespace(walkObject)
        if not walkObjectNS.endswith(":"):
            walkObjectNS = walkObjectNS + ":"
        userAttrs = cmds.listAttr(str(walkObject), userDefined=True)
        vaildObject = False
        if refName in self.walkDataLibrary._fileToMapDict.keys():
            mapName = self.walkDataLibrary._fileToMapDict[refName]

            CharacterTool = self.allTools.tools['CharacterTool']
            MirrorTools = self.allTools.tools['MirrorTools']
            # only hits disk the first time this character is seen, the rest of the tool treats
            # CharacterTool.allCharacters as a cache too
            CharacterTool.loadCharacterIfNotLoaded(mapName, node=str(walkObject))

            result = self.pickwalkData[mapName].walk(namespace=walkObjectNS,
                                                     node=walkObjectStripped,
                                                     direction=direction)

            vaildObject = self.isValidWalkDestination(walkObjectNS + str(result))

            # a destination that is there but hidden is worth remembering - if the animator ends up
            # picking a replacement, both can be kept and chosen by rig state instead of one overwriting
            # the other
            hiddenDestination = None
            if not vaildObject and result and cmds.objExists(walkObjectNS + str(result)):
                hiddenDestination = str(result)

            if not vaildObject:
                if direction == 'up' or direction == 'down':
                    result = self.findIncrementalControl(walkObjectStripped,
                                                         namespace=walkObjectNS,
                                                         offset=self.walkIncrementMap[direction])

                    vaildObject = self.isValidWalkDestination(walkObjectNS + str(result))

                    if vaildObject:
                        mirrorStart = MirrorTools.getMirrorForControlFromCharacter(CharacterTool.allCharacters[mapName],
                                                                                   walkObject)
                        # walkObjectNS already carries its trailing colon
                        mirrorEnd = MirrorTools.getMirrorForControlFromCharacter(CharacterTool.allCharacters[mapName],
                                                                                 walkObjectNS + str(result))

                        validMirror = cmds.objExists(str(mirrorEnd)) and cmds.objExists(str(mirrorStart))
                        if validMirror:
                            self.createDestination(mirrorStart, mirrorEnd, direction)
                        self.createDestination(walkObject, walkObjectNS + result, direction)
                        return [walkObjectNS + result]
                else:
                    # check for fingers
                    offset = 1
                    if direction == 'left': offset = -1
                    result = self.getMatchingFinger(walkObject, offset)
                    vaildObject = self.isValidWalkDestination(result)
                    if vaildObject:
                        self.createDestination(walkObject, result, direction)
                        return [result]

                    # no finger, check for mirror
                    result = MirrorTools.getMirrorForControlFromCharacter(CharacterTool.allCharacters[mapName],
                                                                          walkObject)
                    # getMirrorControl hands back the control it was given when there is no other side, so
                    # without this a centre control gets tagged as walking to itself and nothing below here
                    # ever runs
                    vaildObject = str(result) != str(walkObject) and self.isValidWalkDestination(str(result))
                    if vaildObject:
                        self.createDestination(walkObject, result, direction)
                        return [result]

            if not vaildObject:
                existingEntry = self.findPreExistingEntries(walkObjectStripped, walkObjectNS, direction)

                if existingEntry:
                    if not isinstance(existingEntry, WalkDestinationInfo):
                        # a plain destination, already resolved against this scene
                        self.createDestination(walkObject, existingEntry, direction)
                        return [existingEntry]

                    # a complete entry from another map, copy it onto this rig's map and keep it
                    self.loadLibraryForCurrent()
                    self.pickwalkCreator.setControlDestination(walkObjectStripped,
                                                               direction=direction,
                                                               destination=existingEntry.destination,
                                                               destinationAlt=existingEntry.destinationAlt,
                                                               conditionAttribute=existingEntry.conditionAttribute,
                                                               conditionValue=existingEntry.conditionValue)
                    self.saveLibrary()
                    self.forceReloadData()

                    # resolve through walk() rather than taking destination blind, so a conditional entry
                    # picks the branch that matches the rig's current state
                    result = self.pickwalkData[mapName].walk(namespace=walkObjectNS,
                                                             node=walkObjectStripped,
                                                             direction=direction)
                    if result and self.isValidWalkDestination(walkObjectNS + str(result)):
                        return [walkObjectNS + str(result)]
                    # the copied entry points somewhere the animator cannot select, so still ask
                    if result and cmds.objExists(walkObjectNS + str(result)):
                        hiddenDestination = str(result)
                    self.pickNewDestination(direction, walkObjectNS, walkObjectStripped,
                                            hiddenDestination=hiddenDestination)
                    return False
                else:
                    self.pickNewDestination(direction, walkObjectNS, walkObjectStripped,
                                            hiddenDestination=hiddenDestination)
                return False

            # validity was already established above, so this only needs the cheap existence check
            if cmds.objExists(walkObjectNS + str(result)):
                returnedControls.append(walkObjectNS + result)
            else:
                self.pickNewDestination(direction, walkObjectNS, walkObjectStripped)
                if get_option_var(self.defaultToStandardAtDeadEndOption, True):
                    self.walkStandard(direction)
                    return
                return False
            return returnedControls
        elif refName not in self.walkDataLibrary.ignoredRigs:
            self.queryWalkOnNewRig(refName)
            return False
        elif userAttrs:
            pickAttributes = [i for i in self.pickwalkAttributeNames[direction] if i in userAttrs]
            if pickAttributes:
                # exit and return to standard pickwalk ( bit of repeated code but whatever for now )
                return returnedControls
        return returnedControls

    def findPreExistingEntries(self, walkObjectStripped, namespace, direction):
        """
        This rig's map has no destination, so look for a control of the same name in the other maps -
        reference presets first, then the user's own maps - and reuse the first entry that fits this scene.
        Returns a WalkDestinationInfo to copy, or a resolved destination name, or None.
        """
        node = str(walkObjectStripped)
        mapList = self.walkDataLibrary.rigMapDict.keys()
        refList = [m for m in mapList if m.startswith(presetPrefix)]
        customList = [m for m in mapList if m not in refList]

        for mapName in refList + customList:
            if mapName not in self.pickwalkData.keys():
                continue
            if node not in self.pickwalkData[mapName].objectDict.keys():
                continue
            result = self.pickwalkData[mapName].objectDict[node][direction]

            if isinstance(result, WalkDestinationInfo):
                if not result.matchesScene(namespace=namespace, walkObject=node):
                    continue
                # an entry is only worth copying over if what it resolves to right now can be selected,
                # otherwise it gets written to this rig's map and immediately leads to a dead end
                resolved = result.resolve(namespace=namespace, walkObject=node)
                if resolved and self.isValidWalkDestination(namespace + resolved):
                    return result
            elif isinstance(result, basestring) and result:
                # namespace already carries its trailing colon. A hidden destination is no better here
                # than it would be on this rig's own map, so skip it and keep looking
                if self.isValidWalkDestination(namespace + result):
                    return namespace + result
        return None

    def getMatchingFinger(self, walkObject, offset=1):
        shortName = walkObject.rsplit(':')[-1]

        for index, l in enumerate(self.fingerNames):
            for i, f in enumerate(l):
                if f in shortName:
                    currentFinger = self.fingerNames[index][i]
                    nextFinger = self.fingerNames[(index + offset) % len(self.fingerNames)][i]
                    result = walkObject.replace(currentFinger, nextFinger)
                    if cmds.objExists(result):
                        return result
        return str()

    def getDeadEndKey(self, control, direction, namespace):
        mapName = self.pickwalkCreator.walkData.name
        if not mapName:
            return None
        return (mapName, namespace, control, direction)

    def deriveConditionFromHiddenDestination(self, hiddenDestination, namespace):
        """
        Only one rig state has been seen, so the far end of the switch attribute's own range stands in
        for the other state. Returns (plug, threshold, currentValue) or None when it cannot be worked out.
        """
        candidates = self.getConditionCandidatePlugs(namespace + hiddenDestination)
        if len(candidates) != 1:
            # no switch found, or too many to pick between
            return None
        plug = list(candidates)[0]

        node = plug.split('.')[0]
        attr = plug.split('.')[-1].split('[')[0]
        try:
            value = float(cmds.getAttr(plug))
        except (RuntimeError, ValueError, TypeError):
            return None

        attrType = cmds.getAttr(plug, type=True)
        minimum = maximum = None
        if attrType == 'bool':
            minimum, maximum = 0.0, 1.0
        elif attrType == 'enum':
            enums = cmds.attributeQuery(attr, node=node, listEnum=True)
            if enums:
                minimum, maximum = 0.0, float(len(enums[0].split(':')) - 1)
        else:
            if cmds.attributeQuery(attr, node=node, minExists=True):
                minimum = float(cmds.attributeQuery(attr, node=node, minimum=True)[0])
            if cmds.attributeQuery(attr, node=node, maxExists=True):
                maximum = float(cmds.attributeQuery(attr, node=node, maximum=True)[0])

        if minimum is None or maximum is None or minimum == maximum:
            # an unbounded attribute gives nothing to measure the other state against
            return None

        far = minimum if abs(value - maximum) < abs(value - minimum) else maximum
        return self.getPlugName(plug), (value + far) / 2.0, value

    def promptForDeadEndCondition(self, control, direction, hiddenDestination, newDestination, plug):
        msg = QMessageBox(getMainWindow())
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle('Contextual pickwalk')
        msg.setText('{control} already walks {direction} to {old}, which is hidden right '
                    'now.'.format(control=control, direction=direction, old=hiddenDestination))
        if plug:
            msg.setInformativeText('{plug} looks like what hides it, so both destinations can be kept and '
                                   'picked by the rig state.\n\nKeep both, or replace {old} with '
                                   '{new}?'.format(plug=plug, old=hiddenDestination, new=newDestination))
            keepButton = msg.addButton('Keep Both', QMessageBox.AcceptRole)
        else:
            msg.setInformativeText('No switch attribute could be worked out for it, so keeping both would '
                                   'need a condition set up by hand.\n\nReplace {old} with {new}, or leave '
                                   'it alone?'.format(old=hiddenDestination, new=newDestination))
            keepButton = None
            msg.addButton('Leave Alone', QMessageBox.RejectRole)
        replaceButton = msg.addButton('Replace', QMessageBox.DestructiveRole)
        msg.setDefaultButton(keepButton if keepButton else replaceButton)
        msg.exec_()

        if keepButton is not None and msg.clickedButton() == keepButton:
            return 'keep'
        if msg.clickedButton() == replaceButton:
            return 'replace'
        return 'cancel'

    def pickNewDestination(self, direction, namespace, walkObject, hiddenDestination=None):
        if hiddenDestination:
            key = self.getDeadEndKey(walkObject, direction, namespace)
            if key:
                Pickwalk._pendingDeadEnds[key] = hiddenDestination
        prompt = PickWalkObjectDialog(direction, namespace, walkObject, parent=getMainWindow(),
                                      title='No destination found',
                                      text=str("Pick new control for {control} {dir}").format(control=walkObject,
                                                                                              dir=direction))
        prompt.assignSignal.connect(self.assignNewDestinationFromWalk)
        prompt.conditionSignal.connect(self.assignNewConditionFromWalk)
        prompt.existingConditionSignal.connect(self.assigmExistingConditionFromWalk)
        prompt.show()

    def quickDownToMulti(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')

        self.loadLibraryForCurrent()
        self.pickwalkCreator.quickDownToMulti()
        self.saveLibrary()
        self.forceReloadData()

    def quickUpFromMulti(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        self.loadLibraryForCurrent()
        self.pickwalkCreator.quickUpFromMulti()
        self.saveLibrary()
        self.forceReloadData()

    def quickLeftRight(self, *args):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('Nothing selected')
        self.loadLibraryForCurrent()
        if len(sel) > 1:
            # cmds.warning('inputSignal_quickLeftRight')
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction='left',
                                                  loop=True,
                                                  reciprocate=True,
                                                  endOnSelf=False)
            # self.updateTreeView()
            self.saveLibrary()
            self.forceReloadData()
            return

    def quickDownUp(self, *args):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('Nothing selected')
        self.loadLibraryForCurrent()
        if len(sel) > 1:
            # cmds.warning('inputSignal_quickUpDown')
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction='down',
                                                  loop=False,
                                                  reciprocate=True,
                                                  endOnSelf=True)
            # self.updateTreeView()
            self.saveLibrary()
            self.forceReloadData()
            return

    def openMirrorSelectedUI(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        self.loadLibraryForCurrent()
        self.assigmMirroredWalk()

    def openAssignExistingConditionUI(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        namespace, control = sel[0].rsplit(':', 1)
        self.assigmExistingConditionFromWalk(str(), namespace, control, str())

    def openPickwalkConditionUI(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        namespace, control = sel[0].rsplit(':', 1)
        self.assignNewConditionFromWalk(str(), namespace, control, str())

    def assigmMirroredWalk(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        self.loadLibraryForCurrent()
        if self.mirrorPopup is not None:
            self.mirrorPopup.close()
            self.mirrorPopup.deleteLater()

        self.mirrorPopup = MirrorPickwalkPopup()
        self.mirrorPopup.show()

    def assigmExistingConditionFromWalk(self, direction, namespace, walkObject, destination):
        cmds.select(namespace + ':' + walkObject, replace=True)
        self.loadLibraryForCurrent()
        if self.existingConditionPopup is not None:
            self.existingConditionPopup.close()
            self.existingConditionPopup.deleteLater()

        self.existingConditionPopup = PickwalkExistingConditionPopup(control=walkObject, destination=destination)
        self.existingConditionPopup.show()

    def assignNewConditionFromWalk(self, direction, namespace, walkObject, destination):
        cmds.select(namespace + ':' + walkObject, replace=True)
        self.loadLibraryForCurrent()
        if self.newConditionPopup is not None:
            self.newConditionPopup.close()
            self.newConditionPopup.deleteLater()

        self.newConditionPopup = PickwalkNewConditionPopup(control=walkObject, destination=destination)
        self.newConditionPopup.show()

    def assignNewDestinationFromWalk(self, direction, namespace, walkObject, destination):
        if namespace and not namespace.endswith(':'):
            namespace += ':'
        cmds.select(namespace + walkObject, replace=True)
        self.loadLibraryForCurrent()

        newDestination = self.funcs.stripNamespace(str(destination[0]))
        key = self.getDeadEndKey(walkObject, direction, namespace)
        hiddenDestination = Pickwalk._pendingDeadEnds.pop(key, None) if key else None

        if hiddenDestination and hiddenDestination != newDestination:
            # this walk already had a destination and it was only skipped because it is hidden, so
            # overwriting it would throw away work. Keep both and let the rig state choose
            derived = self.deriveConditionFromHiddenDestination(hiddenDestination, namespace)
            plug = derived[0] if derived else None
            answer = self.promptForDeadEndCondition(walkObject, direction, hiddenDestination,
                                                    newDestination, plug)
            if answer == 'cancel':
                return
            if answer == 'keep':
                plug, threshold, value = derived
                self.applyDeadEndCondition(walkObject, direction, plug, hiddenDestination,
                                           newDestination, threshold, value, namespace)
                self.saveLibrary()
                self.forceReloadData()
                return

        # TODO - make this work with the incoming list
        self.pickwalkCreator.setControlDestination(walkObject,
                                                   direction=direction,
                                                   destination=newDestination)
        self.saveLibrary()
        self.forceReloadData()

    def applyDeadEndCondition(self, control, direction, plug, hiddenDestination, newDestination,
                              threshold, value, namespace):
        # walk() returns destinationAlt when the attribute reads >= the threshold, and the destination
        # the animator just picked is the one they can see in the rig's current state
        if value >= threshold:
            destination, destinationAlt = [hiddenDestination], [newDestination]
        else:
            destination, destinationAlt = [newDestination], [hiddenDestination]

        self.pickwalkCreator.setControlDestination(control,
                                                   direction=direction,
                                                   destination=destination,
                                                   destinationAlt=destinationAlt,
                                                   conditionAttribute=plug,
                                                   conditionValue=threshold)
        # walking back the other way is unambiguous, the control you came from is always the answer
        self.pickwalkCreator.setControlDestination(newDestination,
                                                   direction=self.pickwalkCreator.reciprocalDirectionsDict[
                                                       direction],
                                                   destination=control)

        if not self.mirrorDemonstratedCondition(control, direction, plug, destination, destinationAlt,
                                                newDestination, threshold, namespace):
            self.pickwalkCreator.mirror(control,
                                        [self.pickwalkCreator.walkData.mirrorNames.get('left', '_L'),
                                         self.pickwalkCreator.walkData.mirrorNames.get('right', '_R')])

    def forceReloadData(self, force=False):
        self.loadLibraryForCurrent()
        self.loadWalkLibrary(force=force)
        self.refreshWalkData(force=force)
        if self.win:
            self.win.pickwalkCreator = self.pickwalkCreator
            self.win.refreshUI()

    def queryWalkOnNewRig(self, refName):
        prompt = PickwalkQueryWidget(title='New Rig Found', rigName=refName,
                                     text='This rig new, set up pickwalking on it?')
        prompt.AssignNewRigSignal.connect(self.assignNewRigExistingMap)
        prompt.IgnoreRigSignal.connect(self.assignIgnoreNewRig)
        prompt.CreateNewRigMapSignal.connect(self.assignNewRigNewMap)
        if prompt.exec_():
            pass
        else:
            pass

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

    def walkUpCreate(self):
        self.walkCreate(direction='up')

    def walkDownCreate(self):
        self.walkCreate(direction='down')

    def walkLeftCreate(self):
        self.walkCreate(direction='left')

    def walkRightCreate(self):
        self.walkCreate(direction='right')

    def assignNewRigExistingMap(self, rigName):
        prompt = PickListDialog(title='Assign rig to existing map', text='Pick exising pickwalk map for rig',
                                itemList=self.walkDataLibrary.rigMapDict.keys(),
                                rigName=rigName)
        prompt.assignSignal.connect(self.assignRig)
        if prompt.exec_():
            pass
        else:
            pass

    def assignRig(self, rigMap, rigName):
        self.walkDataLibrary.assignRig(rigMap, rigName)
        self.savePickwalkLibraryMap()
        self.getAllPickwalkMaps(force=True)

    def savePickwalkLibraryMap(self):
        self.walkDataLibrary.save(self.libraryFilePath)
        # we just wrote it from the in memory library, so there is nothing to read back
        Pickwalk._libraryStamp = getFileStamp(self.libraryFilePath)

    def assignIgnoreNewRig(self, rigName):
        self.walkDataLibrary.ignoreRig(rigName)
        self.savePickwalkLibraryMap()
        self.getAllPickwalkMaps(force=True)

    def assignNewRigNewMap(self, rigName):
        if not self.win:
            self.win = pickwalkMainWindow()
        newMap = self.win.saveAsLibrary(defaultName=rigName)
        if not newMap:
            return
        self.walkDataLibrary.assignRig(newMap.split('.')[0], rigName)
        self.savePickwalkLibraryMap()
        self.refreshWalkData(force=True)
        self.win.show()
        self.win.loadLibraryForCurrent()

    """
    Functions moved from mainwindow to here
    """

    def getReferenceName(self, sel):
        refName = None
        if sel:
            refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)
            if refState:
                # if it is referenced, check against pickwalk library entries
                refName = cmds.referenceQuery(sel[0], filename=True, shortName=True).split('.')[0]
            else:
                # might just be working in the rig file itself
                refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        else:
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        return refName

    def getCurrentRig(self):
        refName = None
        mapName = None
        fname = None
        namespace = ''
        sel = cmds.ls(sl=True)

        if not sel:
            return None, None, None
        if ':' in sel[0]:
            namespace = sel[0].split(':')[0]
        refName, refState = self.funcs.getRefName(sel[0])
        if not refName:
            refName = self.funcs.getRefNameFromTopParent(sel[0])
            if refName == -1:
                return None, None, None

        if refName in Pickwalk().walkDataLibrary._fileToMapDict.keys():
            mapName = Pickwalk().walkDataLibrary._fileToMapDict[refName]
            fname = os.path.join(Pickwalk().defaultPickwalkDir, mapName + '.json')
            if not os.path.isfile(fname):
                return None, mapName, namespace
        return fname, mapName, namespace

    def loadLibraryForCurrent(self):
        fname, mapName, namespace = self.getCurrentRig()
        if mapName and not fname:
            cmds.warning('Pickwalk library is referencing a missing file')
            self.queryNewRig(mapName, force=True)
            return None, mapName

        if not fname:
            sel = cmds.ls(sl=True)
            if not sel:
                return None, None
            refName = self.getReferenceName(sel)
            self.queryNewRig(refName)
            return None, None

        self.loadCreatorFile(fname)
        self.setMirrorValuesFromCharacter(fname, mapName)
        return fname, mapName, namespace

    def loadCreatorFile(self, fname, force=False):
        """
        Load a walk data file into the shared pickwalkCreator, skipping the read when the creator already
        holds that exact file contents.
        """
        fileStamp = getFileStamp(fname)
        if not force and Pickwalk._creatorStamp is not None and Pickwalk._creatorStamp == fileStamp:
            currentPath = self.pickwalkCreator.walkData._filePath
            if currentPath and os.path.normpath(currentPath) == os.path.normpath(fname):
                return
        self.pickwalkCreator.load(fname)
        Pickwalk._creatorStamp = fileStamp

    def setMirrorValuesFromCharacter(self, fname, mapName):
        CharacterTool = Pickwalk().allTools.tools['CharacterTool']
        CharacterTool.loadCharacterIfNotLoaded(mapName)
        char = CharacterTool.allCharacters[mapName]
        self.pickwalkCreator.walkData.mirrorNames['left'] = char.leftSide
        self.pickwalkCreator.walkData.mirrorNames['right'] = char.rightSide

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(QWidget(), 'Open file',
                                            cmds.workspace(q=True, directory=True),
                                            "Pickwalk files (*.json)")
        return fname[0] or None

    def saveLibrary(self):
        if not self.pickwalkCreator.walkData._filePath:
            self.saveAsLibrary()
            return
        filePath = self.pickwalkCreator.walkData._filePath
        self.pickwalkCreator.walkData.save(filePath)
        # the creator holds exactly what was just written, no need to read it back in
        Pickwalk._creatorStamp = getFileStamp(filePath)
        self.loadWalkLibrary()
        self.getAllPickwalkMaps()

    def saveAsLibrary(self, defaultName=str(), selectionFilter=list(), base=False):
        self.defaultPickwalkDir = os.path.normpath(os.path.join(self.dataPath, self.subfolder))
        if not os.path.isdir(self.defaultPickwalkDir):
            os.mkdir(self.defaultPickwalkDir)
        save_filename = QFileDialog.getSaveFileName(QWidget(),
                                                    "Save file as",
                                                    self.defaultPickwalkDir + '/' + defaultName,
                                                    "Pickwalk files (*.json)")
        if not save_filename:
            return
        if base:
            dirname = os.path.dirname(save_filename[0])
            basename = presetPrefix + os.path.basename(save_filename[0])
            save_filename = [os.path.join(dirname, basename)]

        if os.path.isfile(save_filename[0]) and not base:
            if self.overwriteQuery().exec_() != 1024:
                return
        self.pickwalkCreator.walkData.save(save_filename[0], selectionFilter=selectionFilter)
        Pickwalk._creatorStamp = None
        self.loadWalkLibrary()

        return os.path.basename(save_filename[0])

    def getCurrentLibraryName(self):
        return self.pickwalkCreator.walkData.name

    def overwriteQuery(self):
        msg = QMessageBox()
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Overwrite existing data?")
        msg.setWindowTitle("Existing file warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg


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

    def assignRig(self, mapName, rigName):
        if mapName not in self.rigMapDict.keys():
            self.rigMapDict[mapName] = list()
        for key, values in self.rigMapDict.items():
            if rigName in values:
                values.remove(rigName)
        if rigName in self.ignoredRigs:
            self.ignoredRigs.remove(rigName)

        self.rigMapDict[mapName].append(rigName)

    def ignoreRig(self, rigName):
        for key, values in self.rigMapDict.items():
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
        jsonFile.write(jsonString)
        jsonFile.close()

        # this may not be the library Pickwalk is holding (the assignment window keeps its own), so mark
        # it as needing a re-read. Pickwalk.savePickwalkLibraryMap re-stamps it when it saved its own copy.
        Pickwalk._libraryStamp = None

        self.createFileToRigMapping(filePath)

    def load(self, filepath):
        jsonObjectInfo = json.load(open(filepath))
        self.rigMapDict = jsonObjectInfo['rigMapDict']
        self.ignoredRigs = jsonObjectInfo['ignoredRigs']
        self.createFileToRigMapping(filepath)

    def createFileToRigMapping(self, filepath):
        dirName = os.path.dirname(filepath)
        for key, values in self.rigMapDict.items():
            mapFile = os.path.join(dirName, key + '.json')
            if not os.path.isfile(mapFile):
                cmds.warning('Missing pickwalk file for {}, Auto creating a new file'.format(key))
                walkData = WalkData()
                walkData.save(mapFile)
            for v in values:
                self._fileToMapDict[v] = key


class WalkDirectionDict(object):
    """
    Dictionary of walk directions, entries will be walkDatinationInfo() or str()
    """

    def __init__(self, left=str(),
                 right=str(),
                 up=str(),
                 down=str()):
        self.left = left
        self.right = right
        self.up = up
        self.down = down

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def toJson(self):
        for key, value in self.__dict__.items():
            if isinstance(value, str):
                value = WalkDestinationInfo(destination=[value])
            elif value == u'(None,)':
                value = WalkDestinationInfo()
            self.__dict__[key] = value
        return {key: value.toJson() for key, value in self.__dict__.items()}


class WalkDestinationInfo(object):
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
        return d

    def getConditionNode(self, namespace=str(), walkObject=str()):
        """
        The node holding the condition attribute. Stored as node.attribute, the form walk() expects;
        older maps kept just the attribute name, which lived on the control being walked from.
        """
        if '.' in self.conditionAttribute:
            return namespace + self.conditionAttribute.split('.')[0]
        return namespace + walkObject

    def pickDestination(self, destinations):
        # the two branches can hold different numbers of destinations, so the shared index is only
        # meaningful up to the length of whichever list is being used
        if not destinations:
            return None
        return destinations[min(self._lastIndex, len(destinations) - 1)]

    def resolve(self, namespace=str(), walkObject=str()):
        """
        Where this entry points given the rig's current state. Shared by walk() and the cross map lookup
        so the condition is only ever evaluated one way.
        """
        if not self.destination:
            return None
        if not self.conditionAttribute:
            return self.pickDestination(self.destination)

        conditionNode = self.getConditionNode(namespace=namespace, walkObject=walkObject)
        attr = self.conditionAttribute.split('.')[-1]
        if not cmds.objExists(conditionNode):
            return self.pickDestination(self.destination)
        if not cmds.attributeQuery(attr, node=conditionNode, exists=True):
            return self.pickDestination(self.destination)

        if cmds.getAttr(conditionNode + '.' + attr) >= self.conditionValue:
            return self.pickDestination(self.destinationAlt or self.destination)
        return self.pickDestination(self.destination)

    def matchesScene(self, namespace=str(), walkObject=str()):
        # TODO - make this more lenient
        if not self.destination:
            return False

        for d in self.destination:
            if not cmds.objExists(namespace + d):
                return False
        for d in self.destinationAlt:
            if not cmds.objExists(namespace + d):
                return False
        if self.conditionAttribute:
            conditionNode = self.getConditionNode(namespace=namespace, walkObject=walkObject)
            if not cmds.objExists(conditionNode):
                return False
            if not cmds.attributeQuery(self.conditionAttribute.split('.')[-1], node=conditionNode,
                                       exists=True):
                return False
        return True


pwShapeWindow = None
pickwalkWorkspaceControlName = 'pwWorkspaceControl'



def workspaceScript(*args):
    parentWidget = toQtObject(cmds.setParent(q=True))
    parentLayout = filter(lambda c: isinstance(c, QLayout), parentWidget.children())

    global pwShapeWindow

    if 'controlShapeWindow' not in globals():
        mel.evalDeferred(
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
    channelBoxTab = mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false)')
    if cmds.workspaceControl(pickwalkWorkspaceControlName, exists=True):
        try:
            cmds.deleteUI(pickwalkWorkspaceControlName)
        except:
            pass
    cmds.workspaceControl(pickwalkWorkspaceControlName,
                        tabToControl=[channelBoxTab, -1],
                        uiScript='import tb_pickwalk as tbPW;reload(tbPW);tbPW.workspaceScript()',
                        loadImmediately=True,
                        initialWidth=100,
                        # minimumWidth=False,
                        widthProperty='free',
                        retain=False,
                        r=True,
                        label='tbPickWalk')


class ChainPickButton(QWidget):
    pressedSignal = Signal(bool, bool)
    direction = str()

    def __init__(self, mainWindow, loop=False, endOnSelf=False, label=str, direction=str, icon=str(), fixedWidth=False,
                 width=32,
                 noOption=False,
                 rotation=0,
                 *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.mainWindow = mainWindow
        self.loop = loop
        self.direction = direction
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.button = StandardPickButton(label=label, direction=direction, icon=icon, fixedWidth=fixedWidth,
                                         width=width,
                                         rotation=rotation)

        self.loopCB = LoopCBWidget(loop=loop, label='loop')
        self.endOnSelfCB = LoopCBWidget(loop=endOnSelf, label='end on self')
        self.mainLayout.addWidget(self.button)
        if not noOption:
            self.mainLayout.addWidget(self.loopCB)
            self.mainLayout.addWidget(self.endOnSelfCB)
        else:
            self.mainLayout.addStretch()
        self.button.clicked.connect(partial(self.pressedSignal.emit,
                                            self.loopCB.checkbox.isChecked(),
                                            self.endOnSelfCB.checkbox.isChecked(),
                                            ))


class lockButton(QPushButton):
    pressedSignal = Signal(bool)

    def __init__(self, icon=str(), icon2=str(), *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.lockedIcon = QIcon(QPixmap(':/{}'.format(icon)))
        self.unlockedIcon = QIcon(QPixmap(':/{}'.format(icon2)))
        self.setText('Pick')
        self.setFixedWidth(64 * dpiScale())
        # self.setCheckable(True)
        # self.setIconType()
        self.clicked.connect(self.toggle)

    def setIconType(self):
        self.setIcon(self.lockedIcon if self.isChecked() else self.unlockedIcon)

    def toggle(self):
        self.setIconType()
        self.pressedSignal.emit(self.isChecked())


class PickDirectionWidget(QFrame):
    setActiveObjectSignal = Signal()  # in case the main ui needs to keep track?
    setNewActiveObjectSignal = Signal(str)  # in case the main ui needs to keep track?
    upDownSignal = Signal()  # in case the main ui needs to keep track?
    leftRightSignal = Signal()  # in case the main ui needs to keep track?
    downMultiSignal = Signal()  # in case the main ui needs to keep track?
    upMultiSignal = Signal()  # in case the main ui needs to keep track?
    setLockStateSignal = Signal(bool)
    directionPressedObjectSignal = Signal(str)  # in case the main ui needs to keep track?
    applyButtonPressedSignal = Signal(str, str, str, str, str)
    walkUpdateSignal = Signal(str, dict)
    loopChanged = Signal(bool)
    reciprocateChanged = Signal(bool)
    endOnSelfChanged = Signal(bool)
    activeObject = None

    def __init__(self, mainWindow, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mainWindow = mainWindow
        self.mode = False
        self.lockState = False
        # self.setFrameStyle(QFrame.Panel | QFrame.Raised)\

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

        # self.setTitle("Pickwalk")

        self.mainLayout = QVBoxLayout()

        self.mainLayout.setSpacing(4)
        self.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(0)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel('Basic Pickwalk Setup')
        self.title.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.subtitle = QLabel('Quick Add Multiple Pickwalks')
        self.subtitle.setStyleSheet("QLabel {"
                                    "border-width: 0;"
                                    "border-radius: 4;"
                                    "border-style: solid;"
                                    "border-color: #222222;"
                                    "font-weight: bold; font-size: 12px;}"
                                    )
        self.editOnSaveCB = optionVarBoolWidget('Auto Apply', autoApplyOption)
        self.editOnSaveCB.changedSignal.connect(self.toggleAutoApply)
        self.editOnSaveCB.layout.setAlignment(Qt.AlignRight)
        self.editOnSaveCB.labelText.setStyleSheet("QLabel {"
                                                  "border-width: 0;"
                                                  "border-radius: 4;"
                                                  "border-style: solid;"
                                                  "border-color: #222222;}"
                                                  )
        # self.topLayout.addWidget(self.title)
        # self.topLayout.addWidget(self.editOnSaveCB)
        self.mainLayout.addLayout(self.topLayout)

        self.objectWidget = PickObjectWidget(self.mainWindow)
        self.objectWidget.setStyleSheet(getStylesheet)
        self.objectWidget.setStyleSheet("QFrame {"
                                        "border-width: 0;"
                                        "border-radius: 0;"
                                        "border-style: solid;"
                                        "border-color: #222222}"
                                        )
        self.objectWidget.setActiveObjectSignal.connect(self.setActiveObject)
        self.objectWidget.modeChangedSignal.connect(self.modeChanged)
        self.objectWidget.lockChangedSignal.connect(self.lockChanged)

        '''
        syncOn.png

        '''
        self.quickLeftRight = ChainPickButton(self.mainWindow, label='Quick Left/Right', direction='Left/Right',
                                              icon='syncOn.png',
                                              fixedWidth=True,
                                              width=150,
                                              rotation=0, loop=True)

        self.quickLeftRight.setToolTip(ToolTip_QuickLeftRight)
        self.quickUpDown = ChainPickButton(self.mainWindow, label='Quick Down/Up', direction='Left/Right',
                                           icon='syncOn.png',
                                           fixedWidth=True,
                                           width=150,
                                           rotation=90, loop=False)
        self.quickUpDown.setToolTip(ToolTip_DownUp)
        self.quickDownMulti = ChainPickButton(self.mainWindow, label='Quick Down To Many', direction='DownMult',
                                              icon='camera.png',
                                              fixedWidth=True,
                                              noOption=True,
                                              width=150,
                                              rotation=180, loop=False)
        self.quickDownMulti.setToolTip(ToolTip_DownMulti)
        self.quickUpMulti = ChainPickButton(self.mainWindow, label='Quick Up From Many', direction='Left/Right',
                                            icon='camera.png',
                                            fixedWidth=True,
                                            noOption=True,
                                            width=150,
                                            rotation=180, loop=False)
        self.quickUpMulti.setToolTip(ToolTip_UpMulti)
        self.upDestinationWidget = PickwalkDestinationWidget(self.mainWindow, label='UP', direction='up', icon='timeend.png', rotation=90)
        self.downDestinationWidget = PickwalkDestinationWidget(self.mainWindow, label='DOWN', direction='down', icon='timeend.png',
                                                               rotation=270)
        self.leftDestinationWidget = PickwalkDestinationWidget(self.mainWindow, label='LEFT', direction='left', icon='timeend.png',
                                                               rotation=0)
        self.rightDestinationWidget = PickwalkDestinationWidget(self.mainWindow, label='RIGHT', direction='right', icon='timeend.png',
                                                                rotation=180)

        self.applyButton = QPushButton('Apply')
        self.applyButton.clicked.connect(self.applyData)

        self.quickLeftRight.pressedSignal.connect(self.inputSignal_quickLeftRight)
        self.quickUpDown.pressedSignal.connect(self.inputSignal_quickUpDown)
        self.quickDownMulti.pressedSignal.connect(self.inputSignal_quickDownMulti)
        self.quickUpMulti.pressedSignal.connect(self.inputSignal_quickUpMulti)

        self.mainLayout.addWidget(self.objectWidget)
        # self.dirHLayout.addWidget(self.chainOptionWidget)
        self.mainLayout.addWidget(self.upDestinationWidget)
        self.mainLayout.addWidget(self.downDestinationWidget)
        self.mainLayout.addWidget(self.leftDestinationWidget)
        self.mainLayout.addWidget(self.rightDestinationWidget)
        #self.mainLayout.addWidget(self.applyButton)
        self.mainLayout.addWidget(self.subtitle)

        self.mainLayout.addWidget(self.quickLeftRight)
        self.mainLayout.addWidget(self.quickUpDown)
        self.mainLayout.addWidget(self.quickDownMulti)
        self.mainLayout.addWidget(self.quickUpMulti)

        self.allButtons = [
            self.upDestinationWidget,
            self.downDestinationWidget,
            self.leftDestinationWidget,
            self.rightDestinationWidget,
            # self.upSkipBtn,
            # self.downSkipBtn,
            # self.leftSkipBtn,
            # self.rightSkipBtn,
        ]

        for btn in self.allButtons:
            btn.setSimple(True)
            btn.pressedSignal.connect(self.autoApplyData)
            btn.walkInfoSignal.connect(self.getWalkUpdate)
            btn.destinationDoubleClickSignal.connect(self.setNewActiveObject)

        self.toggleAutoApply()

    def setNewActiveObject(self, item):
        self.setNewActiveObjectSignal.emit(item)

    def getWalkUpdate(self, direction, data):
        self.walkUpdateSignal.emit(direction,
                                   data)


    def toggleAutoApply(self):
        if get_option_var(autoApplyOption, True):
            self.applyButton.setDisabled(True)
        else:
            self.applyButton.setEnabled(True)

    def autoApplyData(self, *args):
        if get_option_var(autoApplyOption, True):
            self.applyData()

    def applyData(self):
        self.mainWindow.currentDestination = self.objectWidget.currentObjLabel.text()
        self.mainWindow.currentTargetUp = self.upDestinationWidget.lineEdit.text()
        self.mainWindow.currentTargetDown = self.downDestinationWidget.lineEdit.text()
        self.mainWindow.currentTargetLeft = self.leftDestinationWidget.lineEdit.text()
        self.mainWindow.currentTargetRight = self.rightDestinationWidget.lineEdit.text()

        self.applyButtonPressedSignal.emit(self.objectWidget.currentObjLabel.text(),
                                           self.upDestinationWidget.lineEdit.text(),
                                           self.downDestinationWidget.lineEdit.text(),
                                           self.leftDestinationWidget.lineEdit.text(),
                                           self.rightDestinationWidget.lineEdit.text()
                                           )

    def displayCurrentData(self, data, activeObject):
        if not activeObject:
            self.clear()
            return
        self.objectWidget.currentObjLabel.setText(activeObject)
        walkData = data.objectDict.get(activeObject, str())
        if walkData:
            if walkData.up:
                self.upDestinationWidget.setValues(walkData.up)
            if walkData.down:
                self.downDestinationWidget.setValues(walkData.down)
            if walkData.left:
                self.leftDestinationWidget.setValues(walkData.left)
            if walkData.right:
                self.rightDestinationWidget.setValues(walkData.right)
        else:
            self.clear(obj=False)

    def setWidgetText(self, widget, value):
        if isinstance(value, tuple):
            value = str()
        '''
        if str(value).lower() == 'none':
            value = str()
        '''
        widget.setValues(value)

    def clear(self, obj=True):
        if obj: self.objectWidget.currentObjLabel.setText('None')
        self.upDestinationWidget.lineEdit.setText('')
        self.downDestinationWidget.lineEdit.setText('')
        self.leftDestinationWidget.lineEdit.setText('')
        self.rightDestinationWidget.lineEdit.setText('')

    @Slot()
    def lockChanged(self, data):
        self.lockState = data
        self.setLockStateSignal.emit(data)

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
    def inputSignal_quickLeftRight(self, *args):
        self.leftRightSignal.emit()

    @Slot()
    def inputSignal_quickUpDown(self, *args):
        self.upDownSignal.emit()

    @Slot()
    def inputSignal_quickDownMulti(self, *args):
        self.downMultiSignal.emit()

    @Slot()
    def inputSignal_quickUpMulti(self, *args):
        self.upMultiSignal.emit()

    @Slot()
    def sendloopChangedSignal(self, data):
        self.loopChanged.emit(data)

    @Slot()
    def sendreciprocateChangedSignal(self, data):
        self.reciprocateChanged.emit(data)

    @Slot()
    def sendEndOnSelfChangedSignal(self, data):
        self.endOnSelfChanged.emit(data)

    def setWidgetsEnabled(self, state):
        self.upDestinationWidget.setEnabled(state)
        self.downDestinationWidget.setEnabled(state)
        self.leftDestinationWidget.setEnabled(state)
        self.rightDestinationWidget.setEnabled(state)

class pickContextDirectionWidget(QFrame):
    setActiveObjectSignal = Signal()  # in case the main ui needs to keep track?
    upDownSignal = Signal()  # in case the main ui needs to keep track?
    leftRightSignal = Signal()  # in case the main ui needs to keep track?
    setLockStateSignal = Signal(bool)
    directionPressedObjectSignal = Signal(str, str, str)  # in case the main ui needs to keep track?

    activeObject = None

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mode = False
        self.lockState = False
        self.activeObject = ''
        self.activeDestination = ''
        # self.setFrameStyle(QFrame.Panel | QFrame.Raised)\

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

        # self.setTitle("Pickwalk")

        self.mainLayout = QVBoxLayout()
        self.midLayout = QHBoxLayout()
        self.dirHLayout = QHBoxLayout()
        self.dirMidLayout = QVBoxLayout()

        self.leftLayout = QVBoxLayout()
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(4)
        self.mainLayout.setSpacing(4)

        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.title = QLabel('Context Pickwalk Assignment')
        self.title.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.mainLayout.addWidget(self.title)

        self.upBtn = StandardPickButton(label='', direction='up', fixedWidth=True, icon='timeend.png', rotation=90)
        self.downBtn = StandardPickButton(label='', direction='down', fixedWidth=True, icon='timeend.png', rotation=270)
        self.leftBtn = StandardPickButton(label='', direction='left', fixedWidth=True, icon='timeend.png', rotation=0)
        self.rightBtn = StandardPickButton(label='', direction='right', fixedWidth=True, icon='timeend.png',
                                           rotation=180)

        self.ObjLabel = QLabel('Current Control ::')
        self.ObjLabel.setFixedWidth(btnWidth)
        self.currentObjLabel = QLabel('None')

        self.destLabel = QLabel('Destination ::')
        self.destLabel.setFixedWidth(btnWidth)
        self.currentDestLabel = QLabel('None')
        self.objLayout = QHBoxLayout()
        self.destLayout = QHBoxLayout()

        self.stylesheetFix(self.ObjLabel)
        self.stylesheetFix(self.currentObjLabel)
        self.stylesheetFix(self.destLabel)
        self.stylesheetFix(self.currentDestLabel)

        self.mainLayout.addLayout(self.objLayout)
        self.mainLayout.addLayout(self.destLayout)
        self.objLayout.addWidget(self.ObjLabel)
        self.objLayout.addWidget(self.currentObjLabel)
        self.destLayout.addWidget(self.destLabel)
        self.destLayout.addWidget(self.currentDestLabel)
        self.mainLayout.addLayout(self.leftLayout)
        self.leftLayout.addLayout(self.dirHLayout)

        self.dirHLayout.addWidget(self.leftBtn)
        self.dirMidLayout.addWidget(self.upBtn)
        self.dirMidLayout.addWidget(self.downBtn)
        self.dirHLayout.addLayout(self.dirMidLayout)
        self.dirHLayout.addWidget(self.rightBtn)

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
            btn.setFixedWidth(32 * dpiScale())

    def stylesheetFix(self, widget):
        widget.setStyleSheet("QLabel {"
                             "border-width: 0;"
                             "border-radius: 4;"
                             "border-style: solid;"
                             "border-color: #222222}"
                             )

    @Slot()
    def lockChanged(self, data):
        self.lockState = data
        self.setLockStateSignal.emit(data)

    @Slot()
    def modeChanged(self, data):
        self.mode = data

    def setActiveObject(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            # cmds.warning('No objects selected')
            self.currentObjLabel.setText("None")
            return
        if len(sel) > 1:
            return
        else:
            lbl = funcs.stripNamespace(sel[0])
            self.activeObject = lbl
            self.currentObjLabel.setText(lbl)

    def setActiveDestination(self, data):
        self.activeDestination = data
        self.currentDestLabel.setText(data)

    @Slot()
    def inputSignal_pickDirection(self, direction):
        direction = '{0}{1}'.format(direction, {True: 'Skip', False: ''}[self.mode])
        if not self.activeObject:
            return cmds.warning('No current object')
        if not self.activeDestination:
            return cmds.warning('No current object')
        self.directionPressedObjectSignal.emit(direction, self.activeObject, self.activeDestination)

    @Slot()
    def inputSignal_quickLeftRight(self):
        self.leftRightSignal.emit()

    @Slot()
    def inputSignal_quickUpDown(self):
        self.upDownSignal.emit()

    @Slot()
    def sendloopChangedSignal(self, data):
        self.loopChanged.emit(data)

    @Slot()
    def sendreciprocateChangedSignal(self, data):
        self.reciprocateChanged.emit(data)

    @Slot()
    def sendEndOnSelfChangedSignal(self, data):
        self.endOnSelfChanged.emit(data)


class LoopCBWidget(QFrame):
    loopChanged = Signal(bool)

    def __init__(self, loop=False, label=str, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.checkbox = QCheckBox(label)
        self.checkbox.setChecked(loop)
        self.mainLayout.addWidget(self.checkbox)

        self.checkbox.clicked.connect(self.sendloopChangedSignal)
        self.setStyleSheet("QFrame {"
                           "border-width: 0;"
                           "border-radius: 0;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

    @Slot()
    def sendloopChangedSignal(self):
        self.loopChanged.emit(self.checkbox.isChecked())


class pickChainWidget(QFrame):
    loopChanged = Signal(bool)
    reciprocateChanged = Signal(bool)
    endOnSelfChanged = Signal(bool)

    def __init__(self, *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.loop = QCheckBox('loop')
        self.reciprocate = QCheckBox('reciprocate')
        self.endOnSelf = QCheckBox('end on self')
        # self.reciprocate.setChecked(True)
        self.reciprocate.setChecked(True)

        self.mainLayout.addWidget(self.loop)
        self.mainLayout.addWidget(self.reciprocate)
        self.mainLayout.addWidget(self.endOnSelf)

        self.loop.clicked.connect(self.sendloopChangedSignal)
        self.reciprocate.clicked.connect(self.sendreciprocateChangedSignal)
        self.endOnSelf.clicked.connect(self.sendendOnSelfChangedSignal)

        self.sendreciprocateChangedSignal()
        self.setStyleSheet("QFrame {"
                           "border-width: 0;"
                           "border-radius: 0;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

    @Slot()
    def sendloopChangedSignal(self):
        self.loopChanged.emit(self.loop.isChecked())

    @Slot()
    def sendreciprocateChangedSignal(self):
        self.reciprocateChanged.emit(self.reciprocate.isChecked())

    @Slot()
    def sendendOnSelfChangedSignal(self):
        self.endOnSelfChanged.emit(self.endOnSelf.isChecked())







class ControlListWidget(QWidget):
    pressedSignal = Signal(list())
    newDestinationSignal = Signal(str, str, list)
    newConditionDestinationSignal = Signal(QStandardItem)
    getFromRigSignal = Signal()

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
        self.horizontalLayout = QVBoxLayout()

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
        self.getFromRigButton = QPushButton('Get from object attributes')
        self.getFromRigButton.clicked.connect(self.getFromRig)
        self.topLayout.addWidget(self.label)
        self.topLayout.addLayout(self.horizontalLayout)
        self.topLayout.addWidget(self.filterLineEdit)
        self.horizontalLayout.addWidget(self.filterLineEdit)

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
        self.layout.addWidget(self.getFromRigButton)
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
            upItem.setToolTip(ToolTip_destinationPicker)
            downItem.setToolTip(ToolTip_destinationPicker)
            leftItem.setToolTip(ToolTip_destinationPicker)
            rightItem.setToolTip(ToolTip_destinationPicker)

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

    def getFromRig(self):
        self.getFromRigSignal.emit()

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        if not hasattr(item, 'control'):
            return

        if modifiers == Qt.ShiftModifier:
            self.sendNewConditionDestinationSignal(item)

        elif modifiers == Qt.ControlModifier:
            if hasattr(item, 'direction'):
                sel = cmds.ls(sl=True, type='transform')
                if not sel:
                    return cmds.warning('nothing selected')
                walkObject = sel[0].split(':')[-1] + '_in'
                item.setText(walkObject)
                self.sendNewDestinationSignal(item.control, item.direction, sel)
            else:
                cmds.select(item.control, replace=True)

    @Slot()
    def sendNewConditionDestinationSignal(self, item):
        self.newConditionDestinationSignal.emit(item)

    @Slot()
    def sendNewDestinationSignal(self, control, direction, item):
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

    def appendItem(self, i):
        item = QStandardItem(i)
        self.model.appendRow(item)

    def removeItem(self, item):
        for item in self.model.findItems(item):
            self.model.removeRow(item.row())

    def updateView(self, items):
        self.model.clear()
        self.listView.blockSignals(True)
        for i in items:
            self.appendItem(i)
        self.listView.blockSignals(False)

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.pressedSignal.emit(item.text())

    def itemChanged(self, item):
        pass


class DestinationListWidget(QFrame):
    pressedSignal = Signal(str)
    selectedSignal = Signal(str)
    applySignal = Signal(str)

    def __init__(self, CLS=None, label='BLANK'):
        super(DestinationListWidget, self).__init__()
        self.CLS = CLS
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(120)
        self.setMaximumWidth(200)
        # self.width = 300
        self.setLayout(self.mainLayout)
        self.topLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.topLayout)
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
        self.mainLayout.addWidget(self.toolTypeScrollArea)
        self.mainLayout.addWidget(self.applyButton)

        # self.layout.addStretch(1)
        # self.toolTypeScrollArea.setFixedWidth(148)
        # self.updateCategoryList()
        # self.updateView()

    @Slot()
    def sendValueChangedSignal(self):
        self.pressedSignal.emit(list())

    def updateView(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Destination'])
        self.treeView.blockSignals(True)
        for item in sorted(self.CLS.walkData.destinations.keys()):
            # data = self.CLS.walkData.objectDict[item]
            destinationItem = QStandardItem(item)
            destinationItem.setToolTip(ToolTip_DestinationCtrlClickSet)

            destinationItem.destination = item

            self.model.appendRow([destinationItem])
        self.treeView.blockSignals(False)

    def filterRegExpChanged(self, value):
        regExp = QRegExp(value)
        self.proxyModel.setFilterRegExp(regExp)

    def itemClicked(self, index):
        modifiers = QApplication.keyboardModifiers()
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        if modifiers == Qt.ControlModifier:
            self.pressedSignal.emit(item.text())
        else:
            self.selectedSignal.emit(item.text())

    def applyToSelected(self):
        index = self.treeView.selectedIndexes()[0]
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.applySignal.emit(item.text())

    def itemChanged(self, item):
        pass


class tempPickWidget(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.lineEdit = QLineEdit()
        self.layout.addWidget(self.lineEdit)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"),
                                                       QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip('Placeholder')
        self.cle_action_pick.triggered.connect(self.chooseControl)

    def chooseControl(self):
        pass


class DestinationWidget(QWidget):
    updatedSignal = Signal(list)

    def __init__(self, label='BLANK'):
        super(DestinationWidget, self).__init__()
        self.mainListItem = str()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel(label)
        self.pickButton = QPushButton('Pick')
        self.addDestinationBtn = QPushButton('+')
        self.removeDestinationBtn = QPushButton('-')
        self.addFromDestinationBtn = QPushButton('From Destinations')
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
        self.addFromDestinationBtn.clicked.connect(self.addFromDestinationPressed)

    def currentItems(self):
        return [self.listwidget.item(x).text() for x in range(self.listwidget.count())]

    def recieveMainDestinationClicked(self, item):
        self.mainListItem = item

    @Slot()
    def sendUpdateSignal(self):
        self.updatedSignal.emit(self.currentItems())

    def pickButtonPressed(self):
        sel = cmds.ls(selection=True, type='transform')
        self.listwidget.clear()
        if sel:
            items = [s.stripNamespace() for s in sel]
            self.listwidget.addItems(items)
        self.sendUpdateSignal()

    def addButtonPressed(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return
        items = [s.stripNamespace() for s in sel]
        currentItems = self.currentItems()
        resultItems = self.currentItems()
        self.listwidget.clear()
        for i in items:
            if i not in currentItems:
                resultItems.append(i)
        self.listwidget.addItems(resultItems)
        self.sendUpdateSignal()

    def addFromDestinationPressed(self):
        currentItems = self.currentItems()
        resultItems = self.currentItems()

        self.listwidget.clear()
        resultItems.append(self.mainListItem)

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
        self.setMaximumWidth(420)
        self.setMaximumHeight(320)
        # self.setTitle("Context pickwalks")
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.title = QLabel('Context pickwalk Creation')
        self.title.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.nameWidget = PickwalkLabelledLineEdit(text='Name', hasButton=True, buttonLabel='From Sel', obj=True)
        self.conditionAttrWidget = PickwalkLabelledLineEdit(text='Attribute', hasButton=True,
                                                            buttonLabel='From CB')
        self.conditionWidget = PickwalkLabelledDoubleSpinBox('Condition')
        self.destinationsWidget = DestinationWidget(label='Destinations')
        self.destinationsWidget.updatedSignal.connect(self.inputSignal_destinationsUpdated)
        self.altDestinationsWidget = DestinationWidget(label='Alt Destinations')
        self.altDestinationsWidget.updatedSignal.connect(self.inputSignal_altDestinationsUpdated)

        self.mainLayout.addWidget(self.title)

        self.mainLayout.addWidget(self.nameWidget)
        self.mainLayout.addWidget(self.conditionAttrWidget)
        self.mainLayout.addWidget(self.conditionWidget)

        self.splitLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.splitLayout)
        self.splitLayout.addWidget(self.destinationsWidget)
        self.splitLayout.addWidget(self.altDestinationsWidget)

        self.newButton = QPushButton('Add/Update Conditional Destination')
        self.newButton.clicked.connect(self.outputSignal_newDestinationCreated)
        self.mainLayout.addWidget(self.newButton)
        # self.nameWidget.editedSignal.connect(self.inputSignal_nameChanged)
        self.conditionAttrWidget.editedSignal.connect(self.inputSignal_attributehanged)
        self.conditionWidget.editedSignal.connect(self.inputSignal_conditionhanged)

    def outputSignal_newDestinationCreated(self):
        outData = dict()
        outData['destination'] = self.destinationsWidget.currentItems()
        outData['destinationAlt'] = self.altDestinationsWidget.currentItems()
        outData['conditionAttribute'] = self.conditionAttrWidget.lineEdit.text()
        outData['conditionValue'] = self.conditionWidget.spinBox.value()
        outData['name'] = self.nameWidget.lineEdit.text()
        self.destinationAdded.emit(outData)

    def populate(self, item, destinationData):
        self.destinationsWidget.refreshUI(destinationData.destination)
        self.altDestinationsWidget.refreshUI(destinationData.destinationAlt)
        self.conditionAttrWidget.lineEdit.setText(destinationData.conditionAttribute)
        self.conditionWidget.spinBox.setValue(destinationData.conditionValue)
        self.nameWidget.lineEdit.setText(item)

    def inputSignal_destinationsUpdated(self, items):
        pass

    def inputSignal_altDestinationsUpdated(self, items):
        pass

    def inputSignal_nameChanged(self, name):
        pass

    def inputSignal_attributehanged(self, attribute):
        pass

    def inputSignal_conditionhanged(self, value):
        pass


class PickwalkExistingConditionPopup(BaseDialog):
    destinationAdded = Signal(dict)
    changed = Signal(str)

    def __init__(self, control=None, destination=None, *args, **kwargs):
        super(PickwalkExistingConditionPopup, self).__init__(
            parent=getMainWindow(),
            title='Assign Pickwalk')
        self.borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}" \
                                  "QListWidget {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.pickwalk = Pickwalk()
        self.pickwalkWindow = pickwalkMainWindow()
        self.pickwalk.loadLibraryForCurrent()
        self.pickwalkCreator = self.pickwalk.pickwalkCreator

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.mainLayout)

        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        self.destinationListWidget = DestinationListWidget(CLS=self.pickwalkCreator, label='Destinations')
        self.destinationListWidget.applyButton.setText('Replace current selection')
        self.destinationListWidget.setMaximumWidth(400)
        self.destinationListWidget.applySignal.connect(self.inputSignal_applyDestinationToCurrent)
        self.upBtn = StandardPickButton(label='Up',
                                        direction='up',
                                        icon='timeend.png',
                                        rotation=90,
                                        fixedWidth=False,
                                        width=48)
        self.downBtn = StandardPickButton(label='Down',
                                          direction='down',
                                          icon='timeend.png',
                                          rotation=270,
                                          fixedWidth=False,
                                          width=48)
        self.leftBtn = StandardPickButton(label='Left',
                                          direction='left',
                                          icon='timeend.png',
                                          rotation=0,
                                          fixedWidth=False,
                                          width=48)
        self.rightBtn = StandardPickButton(label='Right',
                                           direction='right',
                                           icon='timeend.png',
                                           rotation=180,
                                           fixedWidth=False,
                                           width=48)

        applyLabel = QLabel('Assign Existing conditional destination')
        applyLabel.setAlignment(Qt.AlignCenter)
        applyLabel.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.mainLayout.addWidget(applyLabel)
        self.mainLayout.addWidget(self.destinationListWidget)
        self.directionLayout = QHBoxLayout()
        self.directionLayout.addWidget(self.upBtn)
        self.directionLayout.addWidget(self.downBtn)
        self.directionLayout.addWidget(self.leftBtn)
        self.directionLayout.addWidget(self.rightBtn)
        self.mainLayout.addLayout(self.directionLayout)

        self.upBtn.pressedSignal.connect(self.addWalk)
        self.downBtn.pressedSignal.connect(self.addWalk)
        self.leftBtn.pressedSignal.connect(self.addWalk)
        self.rightBtn.pressedSignal.connect(self.addWalk)

        self.setFixedSize(self.sizeHint().width(), 320 * dpiScale())

        self.setStyleSheet(getqss.getStyleSheet())
        self.populate()

    def pickControl(self, control=None, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('no object selected')
        controlString = sel[0].split(':')[-1]
        if len(sel) > 1:
            controlString += '...'
        self.controlWidget.lineEdit.setText(controlString)
        self.controls = [s.split(':')[-1] for s in sel]

    def inputSignal_applyDestinationToCurrent(self, item):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            self.pickwalkWindow.pickwalkCreator.replaceDestination(original=s.split(':')[-1], new=item)
        self.pickwalkWindow.saveOnUpdate()

    def populate(self):
        self.destinationListWidget.updateView()

    def inputSignal_destinationsUpdated(self, items):
        self.setOKHighlight(self.destinationsWidget.listwidget)

    def inputSignal_altDestinationsUpdated(self, items):
        self.setOKHighlight(self.altDestinationsWidget.listwidget)

    def inputSignal_nameChanged(self, name):
        pass

    def inputSignal_attributehanged(self, attribute):
        pass

    def inputSignal_conditionhanged(self, value):
        pass

    def setErrorHighlight(self, widget):
        widget.setStyleSheet(self.borderHighlightQSS)

    def setOKHighlight(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

    def addWalk(self, direction=str()):
        index = self.destinationListWidget.treeView.selectedIndexes()[0]
        if not index:
            return
        destinationItem = self.destinationListWidget.model.itemFromIndex(
            self.destinationListWidget.proxyModel.mapToSource(index))
        # 'new destination item is,', item.text()
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('no object selected')
        for s in sel:
            self.pickwalkWindow.pickwalkCreator.setControlDestination(s,
                                                                      direction=direction,
                                                                      destination=destinationItem.text())
        self.pickwalkWindow.saveLibrary()
        self.pickwalk.forceReloadData()


class MirrorPickwalkPopup(BaseDialog):
    mirrorSignal = Signal(list, str, str)

    def __init__(self, *args, **kwargs):
        super(MirrorPickwalkPopup, self).__init__(
            parent=getMainWindow(),
            title='Mirror Selected Pickwalk',
            showInfo=False, )
        # TODO - move these functions out of the window and into Pickwalk()
        self.borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}" \
                                  "QListWidget {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.pickwalk = Pickwalk()
        if not self.pickwalk.win:
            self.pickwalk.win = pickwalkMainWindow()
        self.pickwalkWindow = self.pickwalk.win
        self.pickwalkWindow.loadLibraryForCurrent()
        self.pickwalkCreator = self.pickwalkWindow.pickwalkCreator

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.mainLayout)

        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        self.mirrorwidget = mirrorPickwalkWidget(CLS=self.pickwalkCreator)
        self.mirrorwidget.sideChangedSignal.connect(self.pickwalkWindow.saveOnUpdate)
        self.mirrorwidget.title.hide()
        self.mainLayout.addWidget(self.mirrorwidget)

        self.setFixedSize(self.sizeHint())

        self.setStyleSheet(getqss.getStyleSheet())

        self.mirrorwidget.mirrorPressed.connect(self.mirrorWalk)

    def setErrorHighlight(self, widget):
        widget.setStyleSheet(self.borderHighlightQSS)

    def setOKHighlight(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

    def mirrorWalk(self, fromText=str(), toText=str()):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('no object selected')
        for s in sel:
            self.pickwalkCreator.mirror(s.split(':')[-1], [fromText, toText])
        self.pickwalkWindow.saveLibrary()
        self.pickwalkWindow.loadLibraryForCurrent()
        self.close()


class PickwalkNewConditionPopup(BaseDialog):
    destinationAdded = Signal(dict)
    changed = Signal(str)

    def __init__(self, control=None, destination=None, *args, **kwargs):
        super(PickwalkNewConditionPopup, self).__init__(parent=getMainWindow(),
                                                        title='Context pickwalk Creation')
        # TODO - move these functions out of the window and into Pickwalk()
        self.borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}" \
                                  "QListWidget {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.control = control
        self.destination = destination
        self.pickwalk = Pickwalk()
        self.pickwalkWindow = pickwalkMainWindow()
        self.pickwalk.loadLibraryForCurrent()
        self.creator = self.pickwalk.pickwalkCreator

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.mainLayout)

        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        'Condition Name'
        self.controlWidget = PickObjectLineEdit(text='Control', tooltip='Pick the control to walk from.',
                                                placeholderTest='pick control')
        self.controlWidget.cle_action_pick.triggered.connect(self.pickControl)

        '''
        self.nameWidget = LineEdit(text='Name', tooltip='Pick name from selected object.',
                                   placeholderTest='enter condition name')
        self.nameWidget.cle_action_pick.triggered.connect(self.pickObject)
        '''
        self.conditionAttrWidget = PickObjectLineEdit(text='Attribute', tooltip='Pick attribute to control pickwalk.',
                                                      placeholderTest='enter condition attribute')
        self.conditionAttrWidget.cle_action_pick.triggered.connect(self.pickAttribute)

        self.conditionWidget = PickwalkLabelledDoubleSpinBox(text='Value',
                                                             helpLine='value > this, use alt destination')
        self.destinationsWidget = MiniDestinationWidget(label='Destinations')
        self.destinationsWidget.updatedSignal.connect(self.inputSignal_destinationsUpdated)
        self.altDestinationsWidget = MiniDestinationWidget(label='Alt Destinations')
        self.altDestinationsWidget.updatedSignal.connect(self.inputSignal_altDestinationsUpdated)

        self.mainLayout.addWidget(self.controlWidget)
        # self.mainLayout.addWidget(self.nameWidget)
        self.mainLayout.addWidget(self.conditionAttrWidget)
        self.mainLayout.addWidget(self.conditionWidget)

        self.splitLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.splitLayout)
        self.splitLayout.addWidget(self.destinationsWidget)
        self.splitLayout.addWidget(self.altDestinationsWidget)

        self.upBtn = StandardPickButton(label='Up',
                                        direction='up',
                                        icon='timeend.png',
                                        rotation=90,
                                        fixedWidth=False,
                                        width=48)
        self.downBtn = StandardPickButton(label='Down',
                                          direction='down',
                                          icon='timeend.png',
                                          rotation=270,
                                          fixedWidth=False,
                                          width=48)
        self.leftBtn = StandardPickButton(label='Left',
                                          direction='left',
                                          icon='timeend.png',
                                          rotation=0,
                                          fixedWidth=False,
                                          width=48)
        self.rightBtn = StandardPickButton(label='Right',
                                           direction='right',
                                           icon='timeend.png',
                                           rotation=180,
                                           fixedWidth=False,
                                           width=48)

        applyLabel = QLabel('Walk Direction')
        applyLabel.setAlignment(Qt.AlignCenter)
        applyLabel.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.mainLayout.addWidget(applyLabel)
        self.directionLayout = QHBoxLayout()
        self.directionLayout.addWidget(self.upBtn)
        self.directionLayout.addWidget(self.downBtn)
        self.directionLayout.addWidget(self.leftBtn)
        self.directionLayout.addWidget(self.rightBtn)
        self.mainLayout.addLayout(self.directionLayout)
        self.conditionWidget.editedSignal.connect(self.inputSignal_conditionhanged)

        self.upBtn.pressedSignal.connect(self.addWalk)
        self.downBtn.pressedSignal.connect(self.addWalk)
        self.leftBtn.pressedSignal.connect(self.addWalk)
        self.rightBtn.pressedSignal.connect(self.addWalk)

        self.setFixedSize(self.sizeHint())
        self.pickControl(self.control)
        if self.destination:
            if not isinstance(self.destination, list):
                self.destination = [self.destination]
            self.destinationsWidget.pickButtonPressed(self.destination)
        self.setStyleSheet(getqss.getStyleSheet())

    def pickControl(self, control=None, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('no object selected')
        controlString = sel[0].split(':')[-1]
        if len(sel) > 1:
            controlString += '...'
        self.controlWidget.lineEdit.setText(controlString)
        self.controls = [s.split(':')[-1] for s in sel]

    def pickObject(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning('no object selected')
        self.nameWidget.lineEdit.setText(sel[0].split(':')[-1] + '_in')

    def pickAttribute(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return cmds.warning('no channel selected')
        self.conditionAttrWidget.lineEdit.setText(channels[0].split(':')[-1])
        self.setOKHighlight(self.conditionAttrWidget.lineEdit)

    def outputSignal_newDestinationCreated(self):
        pass
        # self.destinationAdded.emit(outData)

    def populate(self, item, destinationData):
        self.destinationsWidget.refreshUI(destinationData.destination)
        self.altDestinationsWidget.refreshUI(destinationData.destinationAlt)
        self.conditionAttrWidget.lineEdit.setText(destinationData.conditionAttribute)
        self.conditionWidget.spinBox.setValue(destinationData.conditionValue)
        self.nameWidget.lineEdit.setText(item)

    def inputSignal_destinationsUpdated(self, items):
        self.setOKHighlight(self.destinationsWidget.listwidget)

    def inputSignal_altDestinationsUpdated(self, items):
        self.setOKHighlight(self.altDestinationsWidget.listwidget)

    def inputSignal_nameChanged(self, name):
        pass

    def inputSignal_attributehanged(self, attribute):
        pass

    def inputSignal_conditionhanged(self, value):
        pass

    def setErrorHighlight(self, widget):
        widget.setStyleSheet(self.borderHighlightQSS)

    def setOKHighlight(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

    def addWalk(self, direction=str()):
        self.pickwalkWindow.loadLibraryForCurrent()
        outData = dict()
        if not self.conditionAttrWidget.lineEdit.text():
            self.setErrorHighlight(self.conditionAttrWidget.lineEdit)
            return cmds.warning('No valid attribute')
        if not self.destinationsWidget.currentItems():
            self.setErrorHighlight(self.destinationsWidget.listwidget)
            return cmds.warning('No destinations')
        if not self.altDestinationsWidget.currentItems():
            self.setErrorHighlight(self.altDestinationsWidget.listwidget)
            return cmds.warning('No alt destinations')

        outData['destination'] = self.destinationsWidget.currentItems()
        outData['destinationAlt'] = self.altDestinationsWidget.currentItems()
        outData['conditionAttribute'] = self.conditionAttrWidget.lineEdit.text()
        outData['conditionValue'] = self.conditionWidget.spinBox.value()
        outData['name'] = self.controlWidget.lineEdit.text() + '__' + direction

        for control in self.controls:
            self.creator.setControlDestination(control,
                                               direction=direction,
                                               destination=outData['destination'],
                                               destinationAlt=outData['destinationAlt'],
                                               conditionAttribute=outData['conditionAttribute'],
                                               conditionValue=outData['conditionValue'])

            self.creator.mirror(control,
                                [self.creator.walkData.mirrorNames.get('left', '_L'),
                                 self.creator.walkData.mirrorNames.get('right', '_R')])

        self.creator.walkData.save(self.creator.walkData._filePath)
        # self.pickwalkWindow.saveLibrary()
        # self.pickwalk.loadWalkLibrary()
        self.pickwalk.refreshWalkData()
        self.pickwalkWindow.loadLibraryForCurrent()


class mirrorPickwalkWidget(QFrame):
    pressed = Signal(None)
    changed = Signal(str)

    mirrorPressed = Signal(str, str)
    sideChangedSignal = Signal()

    def __init__(self, CLS=None, label='Mirror Selected Controls', *args, **kwargs):
        QFrame.__init__(self, *args, **kwargs)
        self.CLS = CLS

        self.fromInputOption = self.CLS.walkData.mirrorNames.get('left', '_L')
        self.toInputOption = self.CLS.walkData.mirrorNames.get('right', '_R')

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)

        self.layout = QHBoxLayout()
        # self.setStyleSheet(getqss.getStyleSheet())
        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.title = QLabel(label)
        self.title.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.mainLayout.addWidget(self.title)
        self.mainLayout.addLayout(self.layout)

        self.fromLabel = QLabel('Sides')

        self.fromLabel.setStyleSheet("QFrame {"
                                     "border-width: 0;"
                                     "border-radius: 0;"
                                     "border-style: solid;"
                                     "border-color: #222222}"
                                     )

        self.fromInput = QLineEdit(self.fromInputOption)
        self.fromInput.setReadOnly(True)
        self.toInput = QLineEdit(self.toInputOption)
        self.toInput.setReadOnly(True)
        self.mirrorBtn = QPushButton('Mirror selection')
        self.mirrorBtn.clicked.connect(self.sendMirrorSignal)
        # self.layout.addWidget(self.fromLabel)
        # self.layout.addWidget(self.fromInput)
        # self.layout.addWidget(self.toInput)
        self.layout.addWidget(self.mirrorBtn)

        self.fromLabel.setFixedWidth(48 * dpiScale())
        # self.mainLayout.addStretch(1)

        # events
        self.fromInput.textChanged.connect(self.fromChanged)
        self.toInput.textChanged.connect(self.toChanged)

        self.updateMirrorLabels()

        self.fromInput.setStyleSheet("QLineEdit[readOnly=\"true\"] {"
                                     "background-color: #323232;"
                                     "}");
        self.toInput.setStyleSheet("QLineEdit[readOnly=\"true\"] {"
                                   "background-color: #323232;"
                                   "}");
        # line edit input mask
        # reg_ex = QRegExp("[a-z-A-Z0123456789_,]+")
        # fromInput_validator = QRegExpValidator(reg_ex, self.fromInput)
        # self.fromInput.setValidator(fromInput_validator)

    def updateMirrorLabels(self):
        self.fromInputOption = Pickwalk().pickwalkCreator.walkData.mirrorNames.get('left', '_L')
        self.toInputOption = Pickwalk().pickwalkCreator.walkData.mirrorNames.get('right', '_R')
        self.fromInput.setText(self.fromInputOption)
        self.toInput.setText(self.toInputOption)

    def sendMirrorSignal(self):
        self.mirrorPressed.emit(self.fromInput.text(), self.toInput.text())

    def fromChanged(self, *args):
        # TODO update this to edit the character data, not the walk data
        self.CLS.walkData.mirrorNames['left'] = self.fromInput.text()
        self.sideChangedSignal.emit()

    def toChanged(self, *args):
        # TODO update this to edit the character data, not the walk data
        self.CLS.walkData.mirrorNames['right'] = self.toInput.text()
        self.sideChangedSignal.emit()

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
        super(pickwalkRigAssignemtWindow, self).__init__(parent=getMainWindow())
        # DATA
        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.walkDataLibrary = WalkDataLibrary()

        self.defaultPickwalkDir = Pickwalk().defaultPickwalkDir
        if not os.path.isdir(self.defaultPickwalkDir):
            os.mkdir(self.defaultPickwalkDir)
        self.libraryFile = get_option_var('pickwalkLibrary', 'pickwalkLibraryData.json')
        self.libraryFilePath = os.path.join(self.defaultPickwalkDir, self.libraryFile)

        if not os.path.isfile(self.libraryFilePath):
            self.createLibrary()
        else:
            self.walkDataLibrary.load(self.libraryFilePath)
        self.currentMap = None
        self.currentIgnoredRig = None
        self.currentRig = None

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

        self.addReferenceButton = QPushButton('Add Rig File To Map')
        self.addReferenceButton.setToolTip(ToolTip_AddRigToMap)
        self.addReferenceButton.clicked.connect(self.addRigToMap)

        self.addSelectedRigButton = QPushButton('Add Selected Rig To Map')
        self.addSelectedRigButton.setToolTip(ToolTip_AddRigToMap)
        self.addSelectedRigButton.clicked.connect(self.addSelectedRigToMap)

        self.removeeferenceButton = QPushButton('Remove Rig From Map')
        self.removeeferenceButton.clicked.connect(self.removeRigFromMap)
        self.assignIgnoredRigButton = QPushButton('Assign Ignored Rig to Map')
        self.assignIgnoredRigButton.clicked.connect(self.addRigToFromIgnoreListMap)

        self.pickwalkMapTree = QTreeSingleViewWidget(label='Pickwalk Maps')
        self.referencedRigsTree = QTreeSingleViewWidget(label='Referenced Rigs')
        self.ignoredRigsTree = QTreeSingleViewWidget(label='Ignored Rigs')
        self.left_layout.addWidget(self.pickwalkMapTree)
        self.right_layout.addWidget(self.referencedRigsTree)
        self.right_layout.addWidget(self.addSelectedRigButton)
        self.right_layout.addWidget(self.addReferenceButton)
        self.right_layout.addWidget(self.removeeferenceButton)
        self.right_layout.addWidget(self.ignoredRigsTree)
        self.right_layout.addWidget(self.assignIgnoredRigButton)

        self.pickwalkMapTree.pressedSignal.connect(self.mapClicked)
        self.referencedRigsTree.pressedSignal.connect(self.referenceClicked)
        self.ignoredRigsTree.pressedSignal.connect(self.ignoredClicked)

        self.getAllPickwalkMaps()
        self.updateUI()

    def referenceClicked(self, item):
        self.currentRig = item

    def ignoredClicked(self, item):
        self.currentIgnoredRig = item

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

    def addRigToFromIgnoreListMap(self):
        if not self.currentMap:
            return
        if not self.currentIgnoredRig:
            return
        self.walkDataLibrary.assignRig(self.currentMap, self.currentIgnoredRig)

        self.walkDataLibrary.save(self.libraryFilePath)
        Pickwalk().loadWalkLibrary()
        self.referencedRigsTree.appendItem(self.currentIgnoredRig)
        self.ignoredRigsTree.removeItem(self.currentIgnoredRig)

    def removeRigFromMap(self):
        if not self.currentMap:
            return
        if not self.currentRig:
            return
        self.walkDataLibrary.ignoreRig(self.currentRig)
        self.referencedRigsTree.removeItem(self.currentRig)
        self.ignoredRigsTree.appendItem(self.currentRig)
        self.walkDataLibrary.save(self.libraryFilePath)

    def addSelectedRigToMap(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.wanring('No selection')
        baseName, namespace = Pickwalk().funcs.getCurrentRig([sel[0]])

        self.walkDataLibrary.assignRig(self.currentMap, baseName)

        self.walkDataLibrary.save(self.libraryFilePath)
        Pickwalk().loadWalkLibrary()
        self.ignoredRigsTree.removeItem(baseName.split('.')[0])
        self.pickwalkMapTree.appendItem(baseName.split('.')[0])

    def addRigToMap(self):
        if not self.currentMap:
            return
        fname = self.browseToFile()
        if not fname:
            return None
        baseName = os.path.basename(fname)

        self.walkDataLibrary.assignRig(self.currentMap, baseName.split('.')[0])

        self.walkDataLibrary.save(self.libraryFilePath)
        Pickwalk().loadWalkLibrary()
        self.ignoredRigsTree.removeItem(baseName.split('.')[0])
        self.pickwalkMapTree.appendItem(baseName.split('.')[0])

    def updateUI(self):
        self.pickwalkMapTree.CLS = self.walkDataLibrary
        self.pickwalkMapTree.updateView(self.walkDataLibrary.rigMapDict.keys())
        self.ignoredRigsTree.updateView(self.walkDataLibrary.ignoredRigs)

    def createLibrary(self):
        self.walkDataLibrary.save(self.libraryFilePath)
        set_option_var('pickwalkLibrary', self.libraryFile)

    def getAllPickwalkMaps(self):
        jsonFiles = list()
        for filename in os.listdir(self.defaultPickwalkDir):
            if filename.endswith(".json"):
                if os.path.basename(filename) == self.libraryFile:
                    continue
                jsonFiles.append(os.path.join(self.defaultPickwalkDir, filename))
        newMaps = False
        for filename in jsonFiles:
            mapName = os.path.basename(filename).split('.')[0]
            if mapName not in self.walkDataLibrary.rigMapDict.keys():
                self.walkDataLibrary.rigMapDict[mapName] = list()
                newMaps = True

        if newMaps:
            statinfo = os.access(self.libraryFilePath, os.W_OK)
            if statinfo:
                self.walkDataLibrary.save(self.libraryFilePath)



class pickwalkMainWindow(QMainWindow):
    loop = False
    reciprocate = True
    endOnSelf = False

    activeObject = None
    title = 'tbPickwwalkSetup'
    selectionChangedScriptJob = -1

    def __init__(self):
        super(pickwalkMainWindow, self).__init__(parent=getMainWindow())
        # DATA
        self.overlay = None
        self.overlayFlag = False
        self.currentTemplate = None
        self.pickwalkCreator = PickwalkCreator()
        #self.resize(948, self.height())
        # Main Widgets
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('tbPickwwalkSetup')
        self.titleLabel = Header('No current template')
        self.editOnSaveCB = optionVarBoolWidget('Save On Edit', saveOnUpdateOption)
        self.editOnSaveCB.layout.setAlignment(Qt.AlignRight)
        # self.editOnSaveCB.changedSignal.connect(self.toggleSaveOnEdit)
        self.lockState = False

        self.hiddenLayout = QHBoxLayout()

        self.currentControl = None
        self.currentDestination = None
        self.currentTargetUp = None
        self.currentTargetDown = None
        self.currentTargetLeft = None
        self.currentTargetRight = None

        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        self.superLayout = QVBoxLayout()
        self.superLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.main_layout = QHBoxLayout()
        self.left_layout = QHBoxLayout()
        self.left_layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.superLayout.addLayout(self.titleLayout)
        self.titleLayout.addWidget(self.titleLabel)
        spacer = QSpacerItem(60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.titleLayout.addItem(spacer)
        self.titleLayout.addWidget(self.editOnSaveCB)
        self.superLayout.addLayout(self.main_layout)
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        main_widget.setLayout(self.superLayout)

        menu = self.menuBar()
        file_menu = menu.addMenu('&File')
        # option_menu = menu.addMenu('&Options')
        edit_menu = menu.addMenu('&Edit')
        view_menu = menu.addMenu('&View')

        '''
        add_action = QAction('Add new library', self)
        add_action.setShortcut('Ctrl+N')
        file_menu.addAction(add_action)
        add_action.triggered.connect(self.newLibrary)
        '''

        load_action = QAction('Load map for current rig', self)
        load_action.setShortcut('Ctrl+C')
        load_action.triggered.connect(self.loadLibraryForCurrent)

        merge_action = QAction('Load (merge with current)', self)
        merge_action.setShortcut('Ctrl+M')
        merge_action.triggered.connect(self.appendLibrary)

        saveSelectedAsBase_action = QAction('Save Selection as shared base', self)
        saveSelectedAsBase_action.triggered.connect(self.saveSelectionAsBase)

        mergeSelected_action = QAction('Load (replace selected controls)', self)
        mergeSelected_action.triggered.connect(self.loadLibraryToSelection)

        open_action = QAction('Open pickwalk file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.loadLibrary)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.saveLibrary)

        saveAs_action = QAction('Save AS', self)
        saveAs_action.setShortcut('Ctrl+Shift+S')
        saveAs_action.triggered.connect(self.saveAsLibrary)

        assign_action = QAction('Assign to selected rig', self)
        assign_action.triggered.connect(self.assignToSelectedRig)

        open_action = QAction('Open pickwalk data location', self)
        open_action.triggered.connect(self.openDataFolder)

        edit_menu.addAction(assign_action)
        edit_menu.addAction(saveSelectedAsBase_action)
        edit_menu.addAction(open_action)

        file_menu.addAction(load_action)
        file_menu.addAction(open_action)
        file_menu.addAction(merge_action)
        file_menu.addAction(mergeSelected_action)
        divider = QAction('-', self)
        divider.setEnabled(False)
        file_menu.addAction(divider)
        file_menu.addAction(save_action)
        file_menu.addAction(saveAs_action)

        # self.saveOnEdit_action = QAction('Save On Edit', self)
        # self.saveOnEdit_action.setCheckable(True)
        # self.saveOnEdit_action.triggered.connect(self.toggleSaveOnEdit)
        # option_menu.addAction(self.saveOnEdit_action)

        '''
        nodeGrapherModeSimple.svg
        nodeGrapherModeConnected.svg
        nodeGrapherModeAll.svg
        '''
        simple_action = QAction('Simple mode', self)
        simple_action.triggered.connect(self.setSimpleMode)
        simple_action.setShortcut('Ctrl+1')
        simple_action.setIcon(QIcon(QPixmap(':/{}'.format('nodeGrapherModeSimple.svg'))))
        view_menu.addAction(simple_action)

        medium_action = QAction('Context mode', self)
        medium_action.triggered.connect(self.setMediumMode)
        medium_action.setShortcut('Ctrl+2')
        medium_action.setIcon(QIcon(QPixmap(':/{}'.format('nodeGrapherModeConnected.svg'))))
        view_menu.addAction(medium_action)

        full_action = QAction('Full mode', self)
        full_action.triggered.connect(self.setDetailMode)
        full_action.setShortcut('Ctrl+3')
        full_action.setIcon(QIcon(QPixmap(':/{}'.format('nodeGrapherModeAll.svg'))))
        view_menu.addAction(full_action)

        self.mainPickWidget = PickDirectionWidget(self)
        # self.contextPickWidget = pickContextDirectionWidget()
        self.controlListWidget = ControlListWidget(CLS=self.pickwalkCreator, label='Controls ::')
        self.destinationListWidget = DestinationListWidget(CLS=self.pickwalkCreator, label='Destinations')
        self.mirrorWidget = mirrorPickwalkWidget(CLS=self.pickwalkCreator)
        self.mirrorWidget.sideChangedSignal.connect(self.saveOnUpdate)
        self.contextWidget = contextPickwalkWidget()

        self.right_layout.addWidget(self.mainPickWidget)
        # self.right_layout.addWidget(self.contextPickWidget)
        self.right_layout.addWidget(self.contextWidget)
        self.right_layout.addWidget(self.mirrorWidget)
        # self.right_layout.addStretch()
        # self.left_layout.addStretch(0)
        self.main_layout.addWidget(self.destinationListWidget)
        self.main_layout.addWidget(self.controlListWidget)

        # dummy = QVBoxLayout()
        # self.right_layout.addLayout(dummy)
        # self.left_layout.addStretch()
        # connect events
        self.controlListWidget.newDestinationSignal.connect(self.inputSignal_dirFromControlTreeView)
        self.controlListWidget.newConditionDestinationSignal.connect(
            self.inputSignal_conditionDirFromControlTreeView)
        self.controlListWidget.getFromRigSignal.connect(self.inputSignal_getFromRig)
        self.destinationListWidget.applySignal.connect(self.inputSignal_applyDestinationToCurrent)
        self.destinationListWidget.selectedSignal.connect(self.inputSignal_selectConditionalDestination)
        self.destinationListWidget.pressedSignal.connect(self.inputSignal_displayConditionalDestination)
        self.destinationListWidget.pressedSignal.connect(
            self.contextWidget.destinationsWidget.recieveMainDestinationClicked)
        self.destinationListWidget.pressedSignal.connect(
            self.contextWidget.altDestinationsWidget.recieveMainDestinationClicked)
        # self.contextPickWidget.directionPressedObjectSignal.connect(self.inputSignal_setConditionalDestination)
        self.mainPickWidget.setActiveObjectSignal.connect(self.inputSignal_activeObjectSet)
        self.mainPickWidget.setNewActiveObjectSignal.connect(self.inputSignal_activeObjectSetFromDestination)
        self.mainPickWidget.applyButtonPressedSignal.connect(self.inputSignal_applyPickwalk)

        #self.mainPickWidget.upDownSignal.connect(self.inputSignal_quickUpDown)
        #self.mainPickWidget.leftRightSignal.connect(self.inputSignal_quickLeftRight)
        #self.mainPickWidget.downMultiSignal.connect(self.inputSignal_quickDownToMulti)
        #self.mainPickWidget.upMultiSignal.connect(self.inputSignal_quickUpFromMulti)
        self.mainPickWidget.walkUpdateSignal.connect(self.getWalkUpdate)

        self.mainPickWidget.setLockStateSignal.connect(self.setLockState)
        self.mainPickWidget.directionPressedObjectSignal.connect(self.addPickwalk)
        self.mainPickWidget.loopChanged.connect(self.inputSignal_loopChanged)
        self.mainPickWidget.reciprocateChanged.connect(self.inputSignal_reciprocateChanged)
        self.mainPickWidget.endOnSelfChanged.connect(self.inputSignal_endOnSelfChanged)
        self.contextWidget.destinationAdded.connect(self.inputSignal_destinationAdded)
        self.mirrorWidget.mirrorPressed.connect(self.inputSignal_mirrorSelection)

        # self.SCRIPT_JOB_NUMBER = cmds.scriptJob(event=['SelectionChanged', self.onSelectionChange], protected=True)

        self.setSimpleMode()
        self.mainPickWidget.setWidgetsEnabled(False)
        # self.loadLibraryForCurrent()

    def resizeEvent(self, event):
        if self.overlay:
            self.overlay.move(0, 0)
            self.overlay.resize(self.width(), self.height())

    def showOverlay(self):
        if not self.overlay:
            self.overlay = TranslucentWidget(self, text='Select a rig control')
        self.overlay.move(0, 0)
        self.overlay.resize(self.width(), self.height())
        self.overlay.SIGNALS.CLOSE.connect(self.hideOverlay)
        self.overlayFlag = True
        self.overlay.show()

    def hideOverlay(self):
        if self.overlay:
            self.overlay.close()
            self.overlayFlag = False


    def show(self):
        super(pickwalkMainWindow, self).show()
        self.selectionChangedScriptJob = cmds.scriptJob(event=["SelectionChanged", self.selectionChanged], protected=False)
        self.disableUI()
        self.loadLibraryForCurrent()
        self.setSimpleMode()

    def getWalkUpdate(self, direction, data):
        self.pickwalkCreator.setControlDestination(self.activeObject,
                                                   direction=direction,
                                                   destination=data['destination'],
                                                   destinationAlt=data['destinationAlt'],
                                                   conditionAttribute=data['conditionAttribute'],
                                                   conditionValue=data['conditionValue'])
        self.pickwalkCreator.mirror(self.activeObject,
                            [self.pickwalkCreator.walkData.mirrorNames.get('left', '_L'),
                             self.pickwalkCreator.walkData.mirrorNames.get('right', '_R')])
        self.saveLibrary()

    def selectionChanged(self):
        if not self.currentTemplate:
            self.loadLibraryForCurrent()

    def disableUI(self):
        #self.setEnabled(False)
        self.showOverlay()
        self.overlay.resize(self.size())

    def enabableUI(self):
        self.hideOverlay()
        self.setEnabled(True)

    @Slot()
    def removeScriptJob(self):
        cmds.scriptJob(kill=self.selectionChangedScriptJob)

    def closeEvent(self, event):
        msg = QMessageBox()
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Overwrite existing data?")
        msg.setWindowTitle("Existing file warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        quit_msg = "You may have unsaved changes, are you sure want to close"
        reply = QMessageBox.question(self, 'Message',
                                     quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up the script job stuff prior to closing the dialog.
            # cmds.scriptJob(kill=self.SCRIPT_JOB_NUMBER, force=True)
            super(pickwalkMainWindow, self).closeEvent(event)
            self.removeScriptJob()
            event.accept()
        else:
            event.ignore()

    def onSelectionChange(self):
        if not self.lockState:
            self.mainPickWidget.displayCurrentData(self.pickwalkCreator.walkData)


    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            Pickwalk().defaultPickwalkDir,
                                            "Pickwalk files (*.json)")
        return fname[0] or None

    def newLibrary(self):
        self.pickwalkCreator = PickwalkCreator()
        self.refreshUI()
        self.setWindowTitle('tbPickwwalkSetup :: untitled')
        self.titleLabel.setText('Current Template :: untitled')

    def getCurrentRig(self):
        refName = None
        mapName = None
        fname = None
        sel = cmds.ls(sl=True)
        if not sel:
            return None
        refName, refState = Pickwalk().funcs.getRefName(sel[0])
        if not refName:
            # if the object is not referenced, check the top node
            topParent = Pickwalk().funcs.getTopParent(str(sel[0]))
            # get the UUID
            UUID = cmds.ls(str(topParent), uuid=True)[0]
            # see if the UUID is in the character definitions
            CharacterTool = Pickwalk().allTools.tools['CharacterTool']

            refName = CharacterTool.getCharacterFromUUID(UUID)

        if refName in Pickwalk().walkDataLibrary._fileToMapDict.keys():
            mapName = Pickwalk().walkDataLibrary._fileToMapDict[refName]
            fname = os.path.join(Pickwalk().defaultPickwalkDir, mapName + '.json')
        return fname

    def getReferenceName(self, sel):
        refName = None
        if sel:
            refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)
            if refState:
                # if it is referenced, check against pickwalk library entries
                refName = cmds.referenceQuery(sel[0], filename=True, shortName=True).split('.')[0]
            else:
                # might just be working in the rig file itself
                refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        else:
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        return refName

    def loadLibraryForCurrent(self):
        fname, mapName, namespace = Pickwalk().loadLibraryForCurrent()
        if not fname:
            fname, mapName, namespace = Pickwalk().getCurrentRig()

        if not fname:
            self.setTitleLabel('NONE')
            self.currentTemplate = None
        else:
            self.currentTemplate = mapName
            self.pickwalkCreator = Pickwalk().pickwalkCreator
            self.pickwalkCreator.namespace = namespace
            CharacterTool = Pickwalk().allTools.tools['CharacterTool']
            CharacterTool.loadCharacterIfNotLoaded(mapName)
            self.pickwalkCreator.walkData.mirrorNames['left'] = CharacterTool.allCharacters[mapName].leftSide
            self.pickwalkCreator.walkData.mirrorNames['right'] = CharacterTool.allCharacters[mapName].rightSide

            self.setTitleLabel(fname)

        self.refreshUI()

    def setTitleLabel(self, fname):
        if isinstance(fname, list):
            fname = fname[0]
        lbl = os.path.normpath(fname).split('\\')[-1]
        self.titleLabel.setText('Current Template :: ' + lbl)

    def loadLibrary(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.walkData = WalkData()
        self.pickwalkCreator.load(fname)
        Pickwalk._creatorStamp = getFileStamp(fname)
        self.refreshUI()
        # self.setWindowTitle('tbPickwwalkSetup :: %s' % fname)
        self.setTitleLabel(fname)

    def appendLibrary(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.load(fname)
        # the creator now holds more than the file it points at, force a proper reload next time
        Pickwalk._creatorStamp = None
        self.refreshUI()

    def saveSelectionAsBase(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Cannot save selection when nothing is selected')
        defaultName = self.pickwalkCreator.walkData.name
        save_filename = Pickwalk().saveAsLibrary(defaultName=defaultName, selectionFilter=sel, base=True)
        return

    def loadLibraryToSelection(self):
        fname = self.browseToFile()
        if not fname:
            return None
        self.pickwalkCreator.load(fname, controlFilter=cmds.ls(sl=True))
        # only a filtered subset of the file was loaded, force a proper reload next time
        Pickwalk._creatorStamp = None
        self.refreshUI()

    def saveLibrary(self):
        if not self.pickwalkCreator.walkData._filePath:
            self.saveAsLibrary()
        else:
            self.pickwalkCreator.walkData.save(self.pickwalkCreator.walkData._filePath)
            if self.pickwalkCreator is Pickwalk().pickwalkCreator:
                # the shared creator holds exactly what was just written, no need to read it back in
                Pickwalk._creatorStamp = getFileStamp(self.pickwalkCreator.walkData._filePath)
        Pickwalk().refreshWalkData()
        self.refreshUI()

    def saveAsLibrary(self, defaultName=str()):
        save_filename = Pickwalk().saveAsLibrary(defaultName=defaultName)
        self.setWindowTitle('tbPickwwalkSetup :: %s' % save_filename)
        return os.path.basename(save_filename)

    def assignToSelectedRig(self):
        pickwalk = Pickwalk()
        if not self.pickwalkCreator.walkData.name:
            return cmds.warning('No current map')
        sel = cmds.ls(sl=True)

        fname = self.getReferenceName(sel)

        if not fname:
            fname = self.browseToFile()
        if not fname:
            return None
        baseName = os.path.basename(fname)

        pickwalk.walkDataLibrary.assignRig(self.pickwalkCreator.walkData.name, baseName.split('.')[0])
        pickwalk.savePickwalkLibraryMap()
        pickwalk.loadWalkLibrary()
        pickwalk.forceReloadData()

    def overwriteQuery(self):
        msg = QMessageBox()
        msg.setStyleSheet(getqss.getStyleSheet())
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Overwrite existing data?")
        msg.setWindowTitle("Existing file warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg

    def refreshUI(self):
        if not self.currentTemplate:
            self.disableUI()
            return
        self.controlListWidget.CLS = Pickwalk().pickwalkCreator
        self.destinationListWidget.CLS = Pickwalk().pickwalkCreator
        self.mainPickWidget.displayCurrentData(Pickwalk().pickwalkCreator.walkData, self.activeObject)
        self.updateTreeView()
        self.mirrorWidget.updateMirrorLabels()
        self.enabableUI()

    def keyPressEvent(self, event):
        return super(pickwalkMainWindow, self).keyPressEvent(event)

    def inputSignal_applyDestinationToCurrent(self, item):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        for s in sel:
            self.pickwalkCreator.replaceDestination(original=s.split(':')[-1], new=item)
        self.saveOnUpdate()

    def inputSignal_selectConditionalDestination(self, item):
        self.currentDestination = item

    def inputSignal_displayConditionalDestination(self, item):
        self.contextWidget.populate(item, self.pickwalkCreator.walkData.destinations[item])

    def inputSignal_conditionDirFromControlTreeView(self, item):
        index = self.destinationListWidget.treeView.selectedIndexes()[0]
        if not index:
            return
        destinationItem = self.destinationListWidget.model.itemFromIndex(
            self.destinationListWidget.proxyModel.mapToSource(index))
        self.pickwalkCreator.setControlDestination(item.control,
                                                   direction=item.direction,
                                                   destination=destinationItem.text())
        item.setText(destinationItem.text())
        self.saveOnUpdate()

    def inputSignal_dirFromControlTreeView(self, control, direction, destination):
        if len(destination) > 1:
            # multiple objects, quick set up destination
            outData = dict()
            outData['destination'] = [x.split(':')[-1] for x in destination]
            outData['destinationAlt'] = list()
            outData['conditionAttribute'] = str()
            outData['conditionValue'] = 0.5
            outData['name'] = destination[0].split(':')[-1] + '_in'
            self.contextWidget.destinationAdded.emit(outData)
        else:
            # single object, add as direct target
            self.pickwalkCreator.setControlDestination(control,
                                                       direction=direction,
                                                       destination=destination[0].split(':')[-1])
        self.saveOnUpdate()

    def setLockState(self, bool):
        self.lockState = bool

    def inputSignal_quickUpFromMulti(self):
        sel = cmds.ls(selection=True, type='transform')
        if len(sel) > 1:
            control = sel[0].split(':')[-1]
            targets = [s.split(':')[-1] for s in sel[1:]]
            for s in targets:
                self.pickwalkCreator.setControlDestination(s,
                                                           direction='up',
                                                           destination=control)
            self.updateTreeView()
            self.saveOnUpdate()
            return

    def inputSignal_quickDownToMulti(self):
        sel = cmds.ls(selection=True, type='transform')
        if len(sel) > 1:
            control = sel[0].split(':')[-1]
            targets = [s.split(':')[-1] for s in sel[1:]]
            name = control + '_' + targets[0] + '_mult'
            self.pickwalkCreator.addDestination(name=name,
                                                destination=targets,
                                                destinationAlt=list(),
                                                conditionAttribute=str(),
                                                conditionValue=0.5)
            self.pickwalkCreator.setControlDestination(control,
                                                       direction='down',
                                                       destination=name)
            self.updateTreeView()
            self.saveOnUpdate()
            return

    def inputSignal_quickLeftRight(self):
        sel = cmds.ls(selection=True, type='transform')
        if len(sel) > 1:
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction='left',
                                                  loop=True,
                                                  reciprocate=True,
                                                  endOnSelf=False)
            self.updateTreeView()
            self.saveOnUpdate()
            return

    def inputSignal_quickUpDown(self):
        sel = cmds.ls(selection=True, type='transform')
        if len(sel) > 1:
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction='down',
                                                  loop=False,
                                                  reciprocate=True,
                                                  endOnSelf=True)
            self.updateTreeView()
            self.saveOnUpdate()
            return

    @Slot()
    def inputSignal_setConditionalDestination(self, direction, control, destination):
        self.pickwalkCreator.setControlDestination(control,
                                                   direction=direction,
                                                   destination=destination)
        self.updateTreeView()
        self.saveOnUpdate()
        return

    @Slot()
    def inputSignal_applyPickwalk(self, control, up, down, left, right):
        self.pickwalkCreator.setControlDestination(control,
                                                   direction='up',
                                                   destination=up)
        self.pickwalkCreator.setControlDestination(control,
                                                   direction='down',
                                                   destination=down)
        self.pickwalkCreator.setControlDestination(control,
                                                   direction='left',
                                                   destination=left)
        self.pickwalkCreator.setControlDestination(control,
                                                   direction='right',
                                                   destination=right)
        self.updateTreeView()
        self.saveOnUpdate()

    def saveOnUpdate(self):
        if get_option_var(saveOnUpdateOption, True):
            self.saveLibrary()

    def inputSignal_activeObjectSetFromDestination(self, item):
        self.activeObject = item
        cmds.select(self.pickwalkCreator.namespace + ':' + item)
        self.inputSignal_activeObjectSet()

    def inputSignal_activeObjectSet(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.activeObject = sel[0].split(':')[-1]
        self.mainPickWidget.objectWidget.currentObjLabel.setText(self.activeObject)
        self.mainPickWidget.displayCurrentData(self.pickwalkCreator.walkData, self.activeObject)

        for control in sel:
            self.pickwalkCreator.addControl(control)
        self.updateTreeView()

    def updateTreeView(self):
        if self.activeObject:
            self.mainPickWidget.setWidgetsEnabled(True)
            self.controlListWidget.updateView()
            self.destinationListWidget.updateView()

    def inputSignal_loopChanged(self, state):
        self.loop = state

    def inputSignal_reciprocateChanged(self, state):
        self.reciprocate = state

    def inputSignal_endOnSelfChanged(self, state):
        self.endOnSelf = state

    def inputSignal_mirrorSelection(self, sideA, sideB):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        for s in sel:
            self.pickwalkCreator.mirror(s.split(':')[-1], [sideA, sideB])
        self.updateTreeView()
        self.saveOnUpdate()

    def inputSignal_destinationAdded(self, input):
        self.pickwalkCreator.addDestination(name=input.get('name', 'defaultName'),
                                            destination=input.get('destination', list()),
                                            destinationAlt=input.get('destinationAlt', list()),
                                            conditionAttribute=input.get('conditionAttribute', str()),
                                            conditionValue=input.get('conditionValue', 0.5))
        self.destinationListWidget.updateView()
        self.saveOnUpdate()

    def inputSignal_getFromRig(self):
        for s in cmds.ls(sl=True):
            self.pickwalkCreator.getNodeInfoFromRig(s)
        self.refreshUI()

    def addPickwalk(self, direction):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            return cmds.warning('No selection')
        if self.lockState:
            if not self.activeObject:
                return cmds.warning('Unable to add single destination with no active object')
            # there is an active (locked object)
            if len(sel) > 1:
                # multiple objects, quick set up destination
                self.pickwalkCreator.addDestination(name=sel[0].split(':')[-1] + '_in',
                                                    destination=[x.split(':')[-1] for x in sel],
                                                    destinationAlt=list(),
                                                    conditionAttribute=str(),
                                                    conditionValue=0.5)
                self.pickwalkCreator.setControlDestination(self.activeObject,
                                                           direction=direction,
                                                           destination=sel[0].split(':')[-1] + '_in')
            else:
                # single object, add as direct target
                self.pickwalkCreator.setControlDestination(self.activeObject,
                                                           direction=direction,
                                                           destination=sel[0].split(':')[-1])

            self.inputSignal_dirFromControlTreeView(self.activeObject, direction, sel)
            self.updateTreeView()
            return

        if len(sel) > 1:
            # cmds.warning('Adding chain style')
            self.pickwalkCreator.addPickwalkChain(controls=sel,
                                                  direction=direction,
                                                  loop=self.loop,
                                                  reciprocate=self.reciprocate,
                                                  endOnSelf=self.endOnSelf)
            self.updateTreeView()
            return

        if not self.activeObject:
            return cmds.warning('Unable to add single destination with no active object')
        # cmds.warning('Adding single style')
        self.pickwalkCreator.setControlDestination(self.activeObject,
                                                   direction=direction,
                                                   destination=sel[0])
        self.updateTreeView()
        self.updateTreeView()
        self.saveOnUpdate()
        return

    def toggleSaveOnEdit(self):
        set_option_var(saveOnUpdateOption, self.editOnSaveCB.isChecked.isChecked())

    def openDataFolder(self):
        os.startfile(Pickwalk().defaultPickwalkDir)

    def setSimpleMode(self):
        self.mainPickWidget.setVisible(True)
        self.controlListWidget.setVisible(False)
        self.destinationListWidget.setVisible(False)
        self.mirrorWidget.setVisible(True)
        self.contextWidget.setVisible(False)

        self.mainPickWidget.upDestinationWidget.contextButton.hide()
        self.mainPickWidget.downDestinationWidget.contextButton.hide()
        self.mainPickWidget.leftDestinationWidget.contextButton.hide()
        self.mainPickWidget.rightDestinationWidget.contextButton.hide()

        self.update()
        self.resize(self.width() * 0.5, self.height() * 0.5)
        self.adjustSize()

    def setMediumMode(self):
        # self.mainPickWidget.setVisible(False)
        # self.contextPickWidget.setVisible(True)
        self.destinationListWidget.setVisible(True)
        self.destinationListWidget.applyButton.setVisible(False)
        self.controlListWidget.setVisible(False)
        self.mirrorWidget.setVisible(True)
        self.contextWidget.setVisible(True)

        self.mainPickWidget.upDestinationWidget.contextButton.show()
        self.mainPickWidget.downDestinationWidget.contextButton.show()
        self.mainPickWidget.leftDestinationWidget.contextButton.show()
        self.mainPickWidget.rightDestinationWidget.contextButton.show()

        self.update()
        self.resize(self.width() * 0.5, self.height() * 0.5)
        self.adjustSize()

    def setDetailMode(self):
        self.mainPickWidget.setVisible(True)
        # self.contextPickWidget.setVisible(True)
        self.controlListWidget.setVisible(True)
        self.destinationListWidget.setVisible(True)
        self.destinationListWidget.applyButton.setVisible(True)
        self.mirrorWidget.setVisible(True)
        self.contextWidget.setVisible(True)

        self.mainPickWidget.upDestinationWidget.contextButton.show()
        self.mainPickWidget.downDestinationWidget.contextButton.show()
        self.mainPickWidget.leftDestinationWidget.contextButton.show()
        self.mainPickWidget.rightDestinationWidget.contextButton.show()

        self.update()
        self.resize(self.width() * 0.5, self.height() * 0.5)
        self.adjustSize()


class PickWalkObjectDialog(BaseDialog):
    assignSignal = Signal(str, str, str, list)
    conditionSignal = Signal(str, str, str, list)
    existingConditionSignal = Signal(str, str, str, list)

    def __init__(self, direction, namespace, walkObject, parent=None, title='title', text='test', altText='alt text'):
        super(PickWalkObjectDialog, self).__init__(parent=parent, title=title, text=text)
        self.direction = direction
        self.namespace = namespace
        self.walkObject = walkObject
        self.result = str()

        self.buttonBox = QDialogButtonBox()
        conditionButton = self.buttonBox.addButton("Add Condition", QDialogButtonBox.ActionRole)
        existingConditionButton = self.buttonBox.addButton("Use Existing Condition", QDialogButtonBox.ActionRole)
        self.buttonBox.addButton("Add Basic", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.setContentsMargins(0, 0, 0, 0)

        conditionButton.clicked.connect(lambda: self.makeCondition())
        existingConditionButton.clicked.connect(lambda: self.useCondition())
        self.infoLabel = QLabel(altText)
        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        # self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)

    def useCondition(self):
        self.existingConditionSignal.emit(self.direction, self.namespace, self.walkObject, self.result)
        self.close()

    def makeCondition(self):
        self.conditionSignal.emit(self.direction, self.namespace, self.walkObject, self.result)
        self.close()

    def pickObject(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))
        self.result = sel

    def accept(self):
        self.assignSignal.emit(self.direction, self.namespace, self.walkObject, self.result)
        super(PickWalkObjectDialog, self).accept()


class PickwalkControlWidget(QWidget):
    destinationAdded = Signal(dict)
    changed = Signal(str)

    def __init__(self, control=None, destination=None, *args, **kwargs):
        super(PickwalkControlWidget, self).__init__()
        # TODO - move these functions out of the window and into Pickwalk()
        self.borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}" \
                                  "QListWidget {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.control = control
        self.destination = destination
        self.pickwalk = Pickwalk()
        self.pickwalkWindow = pickwalkMainWindow()
        self.pickwalk.loadLibraryForCurrent()
        self.creator = self.pickwalk.pickwalkCreator

        self.setStyleSheet("QFrame {"
                           "border-width: 2;"
                           "border-radius: 4;"
                           "border-style: solid;"
                           "border-color: #222222}"
                           )
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.mainLayout)

        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        'Condition Name'
        self.controlWidget = PickObjectLineEdit(text='Control', tooltip='Pick the control to walk from.',
                                                placeholderTest='pick control')
        self.controlWidget.cle_action_pick.triggered.connect(self.pickControl)

        '''
        self.nameWidget = LineEdit(text='Name', tooltip='Pick name from selected object.',
                                   placeholderTest='enter condition name')
        self.nameWidget.cle_action_pick.triggered.connect(self.pickObject)
        '''
        self.conditionAttrWidget = PickObjectLineEdit(text='Attribute', tooltip='Pick attribute to control pickwalk.',
                                                      placeholderTest='enter condition attribute')
        self.conditionAttrWidget.cle_action_pick.triggered.connect(self.pickAttribute)

        self.conditionWidget = PickwalkLabelledDoubleSpinBox(text='Value',
                                                             helpLine='value > this, use alt destination')
        self.destinationsWidget = MiniDestinationWidget(label='Destinations')
        self.destinationsWidget.updatedSignal.connect(self.inputSignal_destinationsUpdated)
        self.altDestinationsWidget = MiniDestinationWidget(label='Alt Destinations')
        self.altDestinationsWidget.updatedSignal.connect(self.inputSignal_altDestinationsUpdated)

        self.mainLayout.addWidget(self.controlWidget)
        # self.mainLayout.addWidget(self.nameWidget)
        self.mainLayout.addWidget(self.conditionAttrWidget)
        self.mainLayout.addWidget(self.conditionWidget)

        self.splitLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.splitLayout)
        self.splitLayout.addWidget(self.destinationsWidget)
        self.splitLayout.addWidget(self.altDestinationsWidget)

        self.upBtn = StandardPickButton(label='Up',
                                        direction='up',
                                        icon='timeend.png',
                                        rotation=90,
                                        fixedWidth=False,
                                        width=48)
        self.downBtn = StandardPickButton(label='Down',
                                          direction='down',
                                          icon='timeend.png',
                                          rotation=270,
                                          fixedWidth=False,
                                          width=48)
        self.leftBtn = StandardPickButton(label='Left',
                                          direction='left',
                                          icon='timeend.png',
                                          rotation=0,
                                          fixedWidth=False,
                                          width=48)
        self.rightBtn = StandardPickButton(label='Right',
                                           direction='right',
                                           icon='timeend.png',
                                           rotation=180,
                                           fixedWidth=False,
                                           width=48)

        applyLabel = QLabel('Walk Direction')
        applyLabel.setAlignment(Qt.AlignCenter)
        applyLabel.setStyleSheet("QLabel {"
                                 "border-width: 0;"
                                 "border-radius: 4;"
                                 "border-style: solid;"
                                 "border-color: #222222;"
                                 "font-weight: bold; font-size: 12px;}"
                                 )
        self.mainLayout.addWidget(applyLabel)
        self.directionLayout = QHBoxLayout()
        self.directionLayout.addWidget(self.upBtn)
        self.directionLayout.addWidget(self.downBtn)
        self.directionLayout.addWidget(self.leftBtn)
        self.directionLayout.addWidget(self.rightBtn)
        self.mainLayout.addLayout(self.directionLayout)
        self.conditionWidget.editedSignal.connect(self.inputSignal_conditionhanged)

        self.upBtn.pressedSignal.connect(self.addWalk)
        self.downBtn.pressedSignal.connect(self.addWalk)
        self.leftBtn.pressedSignal.connect(self.addWalk)
        self.rightBtn.pressedSignal.connect(self.addWalk)


        self.pickControl(self.control)
        if self.destination:
            if not isinstance(self.destination, list):
                self.destination = [self.destination]
            self.destinationsWidget.pickButtonPressed(self.destination)
        self.setStyleSheet(getqss.getStyleSheet())

    def pickControl(self, control=None, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('no object selected')
        controlString = sel[0].split(':')[-1]
        if len(sel) > 1:
            controlString += '...'
        self.controlWidget.lineEdit.setText(controlString)
        self.controls = [s.split(':')[-1] for s in sel]

    def pickObject(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning('no object selected')
        self.nameWidget.lineEdit.setText(sel[0].split(':')[-1] + '_in')

    def pickAttribute(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return cmds.warning('no channel selected')
        self.conditionAttrWidget.lineEdit.setText(channels[0].split(':')[-1])
        self.setOKHighlight(self.conditionAttrWidget.lineEdit)

    def outputSignal_newDestinationCreated(self):
        pass

    def populate(self, item, destinationData):
        self.destinationsWidget.refreshUI(destinationData.destination)
        self.altDestinationsWidget.refreshUI(destinationData.destinationAlt)
        self.conditionAttrWidget.lineEdit.setText(destinationData.conditionAttribute)
        self.conditionWidget.spinBox.setValue(destinationData.conditionValue)
        self.nameWidget.lineEdit.setText(item)

    def inputSignal_destinationsUpdated(self, items):
        self.setOKHighlight(self.destinationsWidget.listwidget)

    def inputSignal_altDestinationsUpdated(self, items):
        self.setOKHighlight(self.altDestinationsWidget.listwidget)

    def inputSignal_nameChanged(self, name):
        pass

    def inputSignal_attributehanged(self, attribute):
        pass

    def inputSignal_conditionhanged(self, value):
        pass

    def setErrorHighlight(self, widget):
        widget.setStyleSheet(self.borderHighlightQSS)

    def setOKHighlight(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())

    def addWalk(self, direction=str()):
        self.pickwalkWindow.loadLibraryForCurrent()
        outData = dict()
        if not self.conditionAttrWidget.lineEdit.text():
            self.setErrorHighlight(self.conditionAttrWidget.lineEdit)
            return cmds.warning('No valid attribute')
        if not self.destinationsWidget.currentItems():
            self.setErrorHighlight(self.destinationsWidget.listwidget)
            return cmds.warning('No destinations')
        if not self.altDestinationsWidget.currentItems():
            self.setErrorHighlight(self.altDestinationsWidget.listwidget)
            return cmds.warning('No alt destinations')

        outData['destination'] = self.destinationsWidget.currentItems()
        outData['destinationAlt'] = self.altDestinationsWidget.currentItems()
        outData['conditionAttribute'] = self.conditionAttrWidget.lineEdit.text()
        outData['conditionValue'] = self.conditionWidget.spinBox.value()
        outData['name'] = self.controlWidget.lineEdit.text() + '__' + direction

        for control in self.controls:
            self.creator.setControlDestination(control,
                                               direction=direction,
                                               destination=outData['destination'],
                                               destinationAlt=outData['destinationAlt'],
                                               conditionAttribute=outData['conditionAttribute'],
                                               conditionValue=outData['conditionValue'])

            self.creator.mirror(control,
                                [self.creator.walkData.mirrorNames.get('left', '_L'),
                                 self.creator.walkData.mirrorNames.get('right', '_R')])

        self.creator.walkData.save(self.creator.walkData._filePath)
        # self.pickwalkWindow.saveLibrary()
        # self.pickwalk.loadWalkLibrary()
        self.pickwalk.refreshWalkData()
        self.pickwalkWindow.loadLibraryForCurrent()