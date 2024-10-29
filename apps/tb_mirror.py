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
# maya.utils.loadStringResourcesForModule(__name__)

IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Icons'))

mirrorPlane = {'YZ': [-1, 1, 1],
               'XZ': [1, -1, 1],
               'XY': [1, 1, -1]}


def repeatable(function):
    '''A decorator that will make commands repeatable in maya'''

    def decoratorCode(*args, **kwargs):
        functionReturn = None
        argString = ''
        if args:
            for each in args:
                argString += str(each) + ', '

        if kwargs:
            for key, item in kwargs.items():
                argString += str(key) + '=' + str(item) + ', '

        commandToRepeat = 'python("global tbtoolCLS;tbtoolCLS.tools[\'MirrorTools\'].' + function.__name__ + '()")'

        functionReturn = function(*args, **kwargs)
        try:
            cmds.repeatLast(ac=commandToRepeat, acl=function.__name__)
        except:
            pass

        return functionReturn

    return decoratorCode


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        # all curve selector
        self.setCategory(self.helpStrings.category.get('mirror'))
        self.addCommand(self.tb_hkey(name='mirrorSelectedSwap',
                                     annotation='',
                                     category=self.category,
                                     help='Blank',
                                     command=['MirrorTools.mirrorSelection(option="swap")']))

        self.addCommand(self.tb_hkey(name='mirrorSelectedLeftToRight',
                                     annotation='',
                                     category=self.category,
                                     help='Blank',
                                     command=['MirrorTools.mirrorSelection(option="toRight")']))

        self.addCommand(self.tb_hkey(name='mirrorSelectedRightToLeft',
                                     annotation='',
                                     category=self.category,
                                     help='Blank',
                                     command=[
                                         'MirrorTools.mirrorSelection(option="toLeft")']))

        self.addCommand(self.tb_hkey(name='mirrorSelectedToOpposite',
                                     annotation='',
                                     category=self.category,
                                     help='Blank',
                                     command=[
                                         'MirrorTools.mirrorSelection(option="toOpposite")']))

        self.addCommand(self.tb_hkey(name='mirrorSelectedFromOpposite',
                                     annotation='',
                                     category=self.category,
                                     help='Blank',
                                     command=[
                                         'MirrorTools.mirrorSelection(option="fromOpposite")']))
        self.addCommand(self.tb_hkey(name='mirrorSelectedCycled',
                                     annotation='Blank',
                                     category=self.category, command=['MirrorTools.cycleMirror()']))
        self.setCategory(self.helpStrings.category.get('markingMenus'))
        self.addCommand(self.tb_hkey(name='mirrorMarkingMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['MirrorTools.openMM()']))

        return self.commandList

    def assignHotkeys(self):
        return


class MirrorData(object):
    def __init__(self):
        self.mirrorPlane = []  #
        self.controls = {}  #
        self.oppositeControls = {}  #

    def toJson(self):
        return json.dumps(self, default=lambda o: o.json_serialize(), sort_keys=True, indent=4, separators=(',', ': '))

    def json_serialize(self):
        returnDict = {}

        returnDict['mirrorPlane'] = self.mirrorPlane
        returnDict['controls'] = self.controls
        returnDict['oppositeControls'] = self.oppositeControls
        return returnDict

    def fromJson(self, data):
        rawJsonData = json.load(open(data))

        self.mirrorPlane = rawJsonData.get('mirrorPlane', list())
        self.controls = rawJsonData.get('controls', dict())
        self.oppositeControls = rawJsonData.get('oppositeControls', dict())


class MirrorTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'MirrorTools'
    subFolder = 'mirrorTables'
    hotkeyClass = hotkeys()
    funcs = Functions()
    lastSelected = None

    loadedMirrorTables = dict()

    def __new__(cls):
        if MirrorTools.__instance is None:
            MirrorTools.__instance = object.__new__(cls)

        MirrorTools.__instance.val = cls.toolName
        return MirrorTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        self.initData()

    def initData(self):
        super(MirrorTools, self).initData()
        self.mirrorDataDir = os.path.normpath(os.path.join(self.dataPath, self.subFolder))
        self.subPath = os.path.normpath(os.path.join(self.dataPath, self.subFolder))
        if not os.path.isdir(self.mirrorDataDir):
            os.mkdir(self.mirrorDataDir)

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(MirrorTools, self).optionUI()
        return None

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

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

            if refname not in self.loadedMirrorTables.keys():
                # print ('saving new mirror table file for %s' % refname)
                # print (MirrorData().toJson())
                self.saveRigFileIfNew(refname, MirrorData().toJson())
            mirrorData = self.loadMirrorData(refname)
            # print ('mirrorData', mirrorData)
            self.loadedMirrorTables[refname] = mirrorData
        self.namespaceToCharDict = namespaceToCharDict

    def loadMirrorData(self, refname):
        return self.loadRigData(MirrorData(), refname)

    def loadRigData(self, dataCLS, rigName):
        subPath = os.path.join(self.dataPath, self.subFolder)
        dataCLS.fromJson(os.path.join(subPath, rigName + '.json'))
        return dataCLS

    def saveRigFileIfNew(self, refname, jsonData):
        self.subPath = os.path.join(self.dataPath, self.subFolder)
        if not os.path.isdir(self.subPath):
            os.mkdir(self.subPath)
        dataFile = os.path.join(self.subPath, refname + '.json')
        if not os.path.isfile(os.path.join(dataFile)):
            self.saveJsonFile(dataFile, json.loads(jsonData))

    def saveRigData(self, refname, jsonData):
        """
        Pass in a json object
        :param dataCLS:
        :param rigName:
        :return:
        """
        dataFile = os.path.join(self.subPath, refname + '.json')
        self.saveJsonFile(dataFile, json.loads(jsonData))

    def openMM(self):
        self.build_MM()
        self.markingMenuWidget.show()

    def build_MM(self, parentMenu=None):
        menuDict = {'NE': list(),
                    'NW': list(),
                    'SE': list(),
                    'SW': list()
                    }

        self.markingMenuWidget = ViewportDialog(menuDict=menuDict, parentMenu=parentMenu, name='MirrorDialog')

        sel = cmds.ls(sl=True)
        if not sel:
            return

        if sel:
            menuDict['SE'].append(ToolboxButton(label='Mirror Pose',
                                                parent=self.markingMenuWidget,
                                                icon=IconPath + '\mirrorSwap.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: MirrorTools().mirrorSelection(option="swap"),
                                                closeOnPress=True))
            menuDict['SE'].append(ToolboxButton(label='Mirror Left To Right',
                                                parent=self.markingMenuWidget,
                                                icon=IconPath + '\mirrorLeftToRight.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: MirrorTools().mirrorSelection(option="toRight"),
                                                closeOnPress=True))
            menuDict['SE'].append(ToolboxButton(label='Mirror Right To Left',
                                                parent=self.markingMenuWidget,
                                                icon=IconPath + '\mirrorRightToLeft.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: MirrorTools().mirrorSelection(option="toLeft"),
                                                closeOnPress=True))
            menuDict['SE'].append(ToolboxButton(label='Mirror To Opposite',
                                                parent=self.markingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: MirrorTools().mirrorSelection(option="toOpposite"),
                                                closeOnPress=True))
            menuDict['SE'].append(ToolboxButton(label='Mirror From Opposite',
                                                parent=self.markingMenuWidget,
                                                icon=':selectObject.png',
                                                cls=self.markingMenuWidget,
                                                command=lambda: MirrorTools().mirrorSelection(option="fromOpposite"),
                                                closeOnPress=True))

    @staticmethod
    def _replace(name, old, new, count=1):
        """
        """
        return new.join(name.rsplit(old, count))

    @staticmethod
    def swapPrefix(objectName, old, new):
        """
        """
        outName = str(objectName)
        old = old.replace("*", "")
        new = new.replace("*", "")

        if ":" in objectName:
            outName = MirrorTools._replace(objectName, ":" + old, ":" + new, 1)
            if objectName != outName:
                return outName

        if "|" in objectName:
            outName = objectName.replace("|" + old, "|" + new)
        elif outName.startswith(old):
            outName = objectName.replace(old, new, 1)

        return outName

    @staticmethod
    def swapSuffix(objectName, old, new):
        """
        """
        outName = str(objectName)
        old = old.replace("*", "")
        new = new.replace("*", "")

        if "|" in objectName:
            outName = objectName.replace(old + "|", new + "|")

        if outName.endswith(old):
            outName = outName[:-len(old)] + new

        return outName

    @staticmethod
    def getMirrorControl(control, leftSide, rightSide):
        """
        """
        outName = None
        # Support for the prefix naming convention.
        if leftSide.endswith("*") or rightSide.endswith("*"):
            outName = MirrorTools.swapPrefix(control, leftSide, rightSide)

            if control == outName:
                outName = MirrorTools.swapPrefix(control, rightSide, leftSide)

            if outName != control:
                return outName

        # Support for the suffix naming convention.
        elif leftSide.startswith("*") or rightSide.startswith("*"):

            outName = MirrorTools.swapSuffix(control, leftSide, rightSide)

            if control == outName:
                outName = MirrorTools.swapSuffix(control, rightSide, leftSide)

            if outName != control:
                return outName

        # Support for all other naming conventions.
        else:
            outName = control.replace(leftSide, rightSide)

            if outName == control:
                outName = control.replace(rightSide, leftSide)

            if outName != control:
                return outName

        # Return None as the given name is probably a center control
        # and doesn't have an opposite side.
        return control

    def getMirrorForControlFromCharacter(self, character, control):
        left = character.getSide('left')
        right = character.getSide('right')
        mirroredControl = self.getMirrorControl(control, left, right)

        # print ('getMirrorForControlFromCharacter', character, control)
        # print ('left', left)
        # print ('right', right)
        # print ('mirroredControl', mirroredControl)

        return mirroredControl

    def getMirrorControlsForSelection(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No Selection')
        CharacterTool = self.allTools.tools['CharacterTool']
        mirrorSel = list()

        for s in sel:
            refname, namespace = CharacterTool.getSelectedChar(sel=s)
            if not refname:
                cmds.warning('No character for control %s' % s)
                continue
            character = CharacterTool.allCharacters[refname]
            mirrorSel.append(self.getMirrorForControlFromCharacter(character, s))
        return mirrorSel

    @staticmethod
    def getMirrorValue(attr, value, mirrorAxis):
        """
        :type attr: str
        :type value: float
        :type mirrorAxis: list[int]
        :rtype: float
        """
        if MirrorTools.isAttributeMirrored(attr, mirrorAxis):
            return value * -1
        return value

    @staticmethod
    def maxIndex(inputFloatList):
        """
        Finds the largest number in a list
        :type inputFloatList: list[float] or list[str]
        :rtype: int
        """

        last = 0
        output = 0
        for i in inputFloatList:
            absValue = abs(float(i))
            if absValue > last:
                last = absValue
                output = inputFloatList.index(i)
        return output

    @staticmethod
    def getWorldSpaceVectorAxis(control, vec):
        selList = om2.MSelectionList()
        controlNode = getDagNode(control)
        controlMatrix = controlNode.inclusiveMatrix()

        selList.add(control)
        dependNode = selList.getDependNode(0)
        mfn_dep = om2.MFnDependencyNode(dependNode)
        mfn_dep, controlDagPath = getMObjectAndDagPath(control)

        controlMMatrix = controlDagPath.inclusiveMatrix()
        controlMTransformMatrix = om2.MTransformationMatrix(controlMMatrix)
        controlTranslation = controlMTransformMatrix.translation(om2.MSpace.kWorld)

        rotateAxisMatrix = om.MEulerRotation(-math.radians(cmds.getAttr(control + '.rotateAxisX')),
                                             -math.radians(cmds.getAttr(control + '.rotateAxisY')),
                                             -math.radians(cmds.getAttr(control + '.rotateAxisZ')),
                                             cmds.getAttr(control + '.rotateOrder')).asMatrix()
        # print ('rotateAxisMatrix', rotateAxisMatrix)
        # om.MEulerRotation.kXYZ
        result_a = om.MVector(vec * controlMatrix) + om.MVector(controlTranslation[0], controlTranslation[1],
                                                                controlTranslation[2])
        result = om.MVector(vec * controlMatrix * rotateAxisMatrix)

        return result

    @staticmethod
    def isAttributeMirrored(attr, mirrorAxis):
        """
        :type attr: str
        :type mirrorAxis: list[int]
        :rtype: float
        """
        LRR = ["translateX", "rotateY", "rotateZ"]
        RLR = ["translateY", "rotateX", "rotateZ"]
        RRL = ["translateZ", "rotateX", "rotateY"]
        LLL = ["translateX", "translateY", "translateZ"]
        # print ('isAttributeMirrored', mirrorAxis)
        if mirrorAxis == [-1, 1, 1]:
            if attr in LRR:
                return True

        elif mirrorAxis == [1, -1, 1]:
            if attr in RLR:
                return True

        elif mirrorAxis == [1, 1, -1]:
            if attr in RRL:
                return True

        elif mirrorAxis == [-1, -1, -1]:
            if attr in LLL:
                return True
        return False

    @staticmethod
    def scaleVector(vec, plane):
        return om.MVector(vec[0] * plane[0],
                          vec[1] * plane[1],
                          vec[2] * plane[2])

    @staticmethod
    def roundVector(vec):
        return om.MVector(float("%.3f" % vec.x), float("%.3f" % vec.y), float("%.3f" % vec.z))

    @staticmethod
    def isAxisMirrored(srcObj, dstObj, axis, plane):
        """
        :type srcObj: str
        :type dstObj: str
        :type axis: list[int]
        :type mirrorPlane: list[int]
        :rtype: int
        """
        axisDict = {'x': om.MVector.xAxis,
                    'y': om.MVector.yAxis,
                    'z': om.MVector.zAxis,
                    }
        mp = mirrorPlane[plane]
        # TODO - replace this with the api version
        # get the current object up/forwrd/right axis
        srcAxisVec = MirrorTools.getWorldSpaceVectorAxis(srcObj, axisDict[axis])
        # round the vector to a sensible decimal
        srcAxisVec = MirrorTools.roundVector(srcAxisVec)
        # get the mirror object up/forwrd/right axis
        dstAxisVec = MirrorTools.getWorldSpaceVectorAxis(dstObj, axisDict[axis])
        # round the vector to a sensible decimal
        dstAxisVec = MirrorTools.roundVector(dstAxisVec)
        '''
        srcNode = cmds.createNode('transform', name='src_%s' % plane)
        cmds.xform(srcNode, translation=srcAxisVec)
        dstNode = cmds.createNode('transform', name='dst_%s' % plane)
        cmds.xform(dstNode, translation=dstAxisVec)
        '''
        # scale the current object axis vector around the mirror plane
        srcAxisVec = MirrorTools.scaleVector(srcAxisVec, mp)

        # print ('plane', plane, 'mp', mp)

        # dstAxisVec = MirrorTools.scaleVector(dstAxisVec, mp)
        # print ('srcAxisVec', srcAxisVec.x, srcAxisVec.y, srcAxisVec.z)
        # print ('dstAxisVec', dstAxisVec.x, dstAxisVec.y, dstAxisVec.z)

        v = (srcAxisVec - dstAxisVec)
        v = om.MVector(srcAxisVec[0] * dstAxisVec[0], srcAxisVec[1] * dstAxisVec[1], srcAxisVec[2] * dstAxisVec[2])
        # print ('l', math.sqrt((v.x * v.x) + (v.y * v.y) + (v.z * v.z)))
        # print ('v', v.x, v.y, v.z)
        # print ('length', v.length())

        d = sum(p * q for p, q in zip(srcAxisVec, dstAxisVec))
        # print ('d', d)
        if d >= 0.0001:
            return False
        return True

    @staticmethod
    def _calculateMirrorAxis(obj, plane):
        """
        :type obj: str
        :rtype: list[int]
        """
        # print ('obj,', obj, 'plane,', plane)
        if not cmds.objExists(obj):
            return cmds.warning('Object does not exist %s ' % obj)
        mirrorAxis = [1, 1, 1]

        xAxisVec = MirrorTools.getWorldSpaceVectorAxis(obj, om.MVector.xAxis)
        xAxisVec = MirrorTools.roundVector(xAxisVec)
        yAxisVec = MirrorTools.getWorldSpaceVectorAxis(obj, om.MVector.yAxis)
        yAxisVec = MirrorTools.roundVector(yAxisVec)
        zAxisVec = MirrorTools.getWorldSpaceVectorAxis(obj, om.MVector.zAxis)
        zAxisVec = MirrorTools.roundVector(zAxisVec)

        # print ('plane?', plane)
        if plane == 'YZ':  # [-1, 1, 1]:
            # print ('YZ', plane)
            i = MirrorTools.maxIndex([xAxisVec[0], yAxisVec[0], zAxisVec[0]])
            mirrorAxis[i] = -1

        if plane == 'XZ':  # [1, -1, 1]:
            # print ('XZ', plane)
            i = MirrorTools.maxIndex([xAxisVec[1], yAxisVec[1], zAxisVec[1]])
            mirrorAxis[i] = -1

        if plane == 'XY':  # [1, 1, -1]:
            # print ('XY', plane)
            i = MirrorTools.maxIndex([xAxisVec[2], yAxisVec[2], zAxisVec[2]])
            mirrorAxis[i] = -1

        return mirrorAxis

    def calculateMirrorAxis(self, srcObj, destinationObj, plane):
        """
        :type srcObj: str
        :rtype: list[int]
        """
        result = [1, 1, 1]

        # source is destination, or destination doesn't exist (mirror on self for better or worse)
        if destinationObj == srcObj or not cmds.objExists(destinationObj):
            result = MirrorTools._calculateMirrorAxis(srcObj, plane)
        else:
            for index, axis in enumerate(['x', 'y', 'z']):
                if MirrorTools.isAxisMirrored(srcObj, destinationObj, axis, plane):
                    result[index] = -1

        return result

    def calculateAllCharacter(self, refname=str(), character=str(), controls=list()):
        # print ('calculateAllCharacter')
        mirrorData = MirrorData()
        characters = self.funcs.splitSelectionToCharacters(controls)
        self.loadDataForCharacters(characters)

        self.initData()
        dataFile = os.path.join(self.mirrorDataDir, refname)

        allAttrs = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
        for control in controls:
            if not cmds.objectType(control, isAType='transform'):
                continue

            opposite = self.getMirrorForControlFromCharacter(character, control)
            # print ('opposite', opposite)
            if not maya.cmds.objExists(opposite):
                continue

            mirrorAxisRaw = character.getMirrorAxis()
            mirrorAxis = self.calculateMirrorAxis(control, opposite, mirrorAxisRaw)
            axisDict = dict()
            mirrorData.controls[self.funcs.stripNamespace(control)] = axisDict
            mirrorData.oppositeControls[self.funcs.stripNamespace(control)] = self.funcs.stripNamespace(opposite)

            for attr in allAttrs:
                axisDict[attr] = self.getMirrorValue(attr, 1, mirrorAxis)

        mirrorData.mirrorPlane = mirrorAxisRaw
        self.saveRigData(dataFile, mirrorData.toJson())

    def saveCurrentMirrorData(self, character):
        dataFile = os.path.join(self.mirrorDataDir, character)
        if character not in self.loadedMirrorTables.keys():
            return cmds.warning('character not in mirror table dictionary')
        self.saveRigData(dataFile, self.loadedMirrorTables[character].toJson())
        print('Saving current mirror', character)
        print('dataFile', dataFile)
        print(self.loadedMirrorTables[character].toJson())

    @staticmethod
    def matchSideName(control, sideName):
        """
        """
        if sideName:
            if sideName.endswith("*"):
                return MirrorTools.swapPrefix(control, sideName, "X") != control

            elif sideName.startswith("*"):
                return MirrorTools.swapSuffix(control, sideName, "X") != control

            else:
                return sideName in control

        return False

    def isMirror(self, control, character, option='swap'):
        CharacterTool = self.allTools.tools['CharacterTool']
        if option == 'swap':
            return True
        if option == 'toLeft':
            # check the object side
            return self.matchSideName(control, CharacterTool._side(character, 'right'))
        if option == 'toRight':
            return self.matchSideName(control, CharacterTool._side(character, 'left'))
        if option == 'toOpposite':
            # check the object against the selection?
            return control in cmds.ls(sl=True)
        if option == 'fromOpposite':
            # check the object against the selection?
            return control not in cmds.ls(sl=True)

    def splitControls(self, controls):
        """

        :param controls:
        :return:
        """
        characters = self.funcs.splitSelectionToCharacters(controls)
        self.loadDataForCharacters(characters)
        CharacterTool = self.allTools.tools['CharacterTool']

        controlPairs = list()
        matched = list()
        for c in controls:
            if c in matched:
                continue
            if ':' in c:
                namespace, control = c.split(':', 1)
            else:
                namespace = ''
                control = c
            rigName = self.namespaceToCharDict[namespace]
            CharacterTool.loadCharacterIfNotLoaded(rigName)
            opposite = self.getMirrorForControlFromCharacter(CharacterTool.allCharacters[rigName], c)
            matched.append(opposite)
            controlPairs.append([c, opposite, rigName])
        return controlPairs

    @repeatable
    def mirrorSelection(self, controls=list(), option='swap'):
        with self.funcs.undoChunk():
            if not controls:
                controls = cmds.ls(sl=True)
            if not controls:
                return cmds.warning('No selection')
            splitControls = self.splitControls(controls)
            # print (splitControls)
            # TODO - not safe if new character
            for src, dst, char in splitControls:
                self.mirrorControl(src, dst, char, option=option)

    def setIsMirror(self, fromControl, character, attr, value):
        strippedFrom = self.funcs.stripNamespace(fromControl)

        if not self.isMirror(strippedFrom, character, 'swap'):
            return
        attrEntry = self.loadedMirrorTables[character].controls.get(strippedFrom, None)
        if not attrEntry:
            return
        scalar = {True: -1, False: 1}[value]
        print(strippedFrom)
        print(self.loadedMirrorTables[character].controls[strippedFrom][attr])
        self.loadedMirrorTables[character].controls[strippedFrom][attr] = scalar
        print(self.loadedMirrorTables[character].controls[strippedFrom][attr])

    def getIsMirror(self, fromControl, character, attr):
        strippedFrom = self.funcs.stripNamespace(fromControl)

        if not self.isMirror(strippedFrom, character, 'swap'):
            return
        attrEntry = self.loadedMirrorTables[character].controls.get(strippedFrom, None)
        if not attrEntry:
            return cmds.warning('This character has no mirror table yet')
        if attr in attrEntry:
            return attrEntry.get(attr, 1)
        return False

    def mirrorControl(self, fromControl, toControl, character, option='swap', timeOffset=0):
        """
        Mirror a single control, specify the pair of controls
        :param fromControl:
        :param toControl:
        :param character:
        :param option:
        :param timeOffset: Offset the destination values in time (for cycles)
        :return:
        """
        valuesDict = dict()

        attrs = cmds.listAttr(fromControl, keyable=True, scalar=True, settable=True, inUse=True)
        toAttrs = cmds.listAttr(toControl, keyable=True, scalar=True, settable=True, inUse=True)
        strippedFrom = self.funcs.stripNamespace(fromControl)
        strippedTo = self.funcs.stripNamespace(toControl)
        valuesDict[fromControl] = dict()
        valuesDict[toControl] = dict()
        for index, a in enumerate(attrs):
            # print (a, cmds.getAttr(namespace + ':' + control + '.' + a))
            valuesDict[fromControl][a] = cmds.getAttr(fromControl + '.' + a)
        for index, a in enumerate(toAttrs):
            valuesDict[toControl][a] = cmds.getAttr(toControl + '.' + a)

        if self.isMirror(fromControl, character, option):

            attrEntry = self.loadedMirrorTables[character].controls.get(strippedFrom, None)
            if not attrEntry:
                # print ('skip')
                return
            for attr, value in valuesDict[toControl].items():
                if not cmds.attributeQuery(attr, node=toControl, exists=True):
                    continue
                if not cmds.attributeQuery(attr, node=toControl, keyable=True):
                    continue
                if not cmds.attributeQuery(attr, node=toControl, writable=True):
                    continue

                scalar = attrEntry.get(attr, 1)
                # print (toControl + '.' + attr, valuesDict[fromControl][attr] * scalar)
                try:
                    cmds.setAttr(toControl + '.' + attr,
                                 valuesDict[fromControl][attr] * scalar,
                                 clamp=True)
                except:
                    pass
        if self.isMirror(toControl, character, option):

            attrEntry = self.loadedMirrorTables[character].controls.get(strippedTo, None)
            if not attrEntry:
                # print ('skip')
                return
            for attr, value in valuesDict[fromControl].items():
                if not cmds.attributeQuery(attr, node=fromControl, exists=True):
                    continue
                if not cmds.attributeQuery(attr, node=fromControl, keyable=True):
                    continue
                if not cmds.attributeQuery(attr, node=fromControl, writable=True):
                    continue
                scalar = attrEntry.get(attr, 1)
                # print (fromControl + '.' + attr, valuesDict[toControl][attr] * scalar)
                try:
                    cmds.setAttr(fromControl + '.' + attr,
                                 valuesDict[toControl][attr] * scalar,
                                 clamp=True)
                except:
                    pass

    def mirrorControlOLD(self, controls=list(), option='swap'):
        """
        Mirror a static pose for selection/input
        :param controls:
        :return:
        """
        if not controls:
            controls = cmds.ls(sl=True)
        if not controls:
            return cmds.warning('No selection')
        characters = self.funcs.splitSelectionToCharacters(controls)
        self.loadDataForCharacters(characters)
        # print (self.loadedMirrorTables)
        valuesDict = dict()
        # TODO - add support for left to right, right to left, swap
        # TODO - checks for should the object mirror (is left side when only right to left == ignore)
        for c in controls:
            if ':' in c:
                namespace, control = c.split(':', 1)
            else:
                namespace = ''
                control = c
            # print (namespace, control)

            if namespace not in valuesDict.keys():
                valuesDict[namespace] = dict()
            attrs = cmds.listAttr(c, keyable=True, scalar=True, settable=True, inUse=True)
            valuesDict[namespace][control] = dict()
            for a in attrs:
                # print (a, cmds.getAttr(namespace + ':' + control + '.' + a))
                valuesDict[namespace][control][a] = cmds.getAttr(namespace + ':' + control + '.' + a)
        # print ('valuesDict', valuesDict)
        # print ('this', valuesDict[namespace]['CTRL_L__Hand']['armLength'])
        for c in controls:
            if ':' in c:
                namespace, control = c.split(':', 1)
            else:
                namespace = ''
                control = c
            rigName = self.namespaceToCharDict[namespace]
            opposite = self.loadedMirrorTables[rigName].oppositeControls.get(control)
            attrEntry = self.loadedMirrorTables[rigName].controls[control]
            # print ('control', control, opposite, attrEntry)

            for attr, value in valuesDict[namespace][control].items():
                if not cmds.attributeQuery(attr, node=namespace + ':' + opposite, exists=True):
                    continue
                scalar = attrEntry.get(attr, 1)
                # print ('attr', attr, 'scalar', scalar, valuesDict[namespace][control][attr])
                cmds.setAttr(namespace + ':' + opposite + '.' + attr,
                             valuesDict[namespace][control][attr] * scalar)


    def cycleMirror(self):
        """
        Used for flipping the control to the other side at the other phase of a walk cycle
        :return:
        """
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('No selection')
        refname, character = self.allTools.tools['CharacterTool'].getCharacterFromSelection()
        print('refname', refname)
        print('character', character)

        mirrorSel = dict()
        for s in sel:
            mirrorSel[s] = self.getMirrorForControlFromCharacter(character, s)
        selectedStart, selectedEnd = self.funcs.getTimelineHighlightedRange()
        selectedEnd = selectedEnd + 1

        # assume playback range is cycle range, objects in local space
        minTime = cmds.playbackOptions(query=True, min=True)
        maxTime = cmds.playbackOptions(query=True, max=True)

        selectedStart = int(selectedStart)
        selectedEnd = int(selectedEnd)
        originalTime = cmds.currentTime(query=True)
        times = range(selectedStart, selectedEnd)
        cmds.currentTime(times[0])
        # print('times', times)
        with self.funcs.suspendUpdate():
            cmds.undoInfo(openChunk=True)
            allMirrorTimes = dict()
            for t in times:
                mirrorTimes = self.getMirrorTime(t, minTime, maxTime)
                allMirrorTimes[t] = mirrorTimes

                for m in mirrorTimes:
                    print ('mirrorTimes', m)
                    cmds.currentTime(t)
                    cmds.currentTime(m, update=False)
                    self.mirrorSelection(controls=sel, option='toOpposite')
            cmds.currentTime(originalTime)
            cmds.undoInfo(closeChunk=True)
    def getMirrorTime(self, t, start, end):
        timeOffset = (end - start) * 0.5
        timeRange = end-start
        mirrorTime = (t-start+timeOffset) % timeRange
        outTime = [mirrorTime]
        if int(mirrorTime)==int(start):
            outTime.append(end)
        return outTime


def getMObject(node):
    selList = om2.MSelectionList()
    selList.add(node)
    return selList.getDependNode(0)


def getMObjectAndDagPath(node):
    selList = om2.MSelectionList()
    selList.add(node)
    return selList.getDependNode(0), selList.getDagPath(0)


def getDagNode(node):
    selList = om.MSelectionList()
    selList.add(node)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    return nodeDagPath


def getMatrixData(plug):
    MMatrix = om2.MFnMatrixData(plug.asMObject()).matrix()
    MTransformationMatrix = om2.MTransformationMatrix(MMatrix)
    return MMatrix, MTransformationMatrix


def iterSelection(selList):
    """
    generator style iterator over current Maya active selection
    :return: [MObject) an MObject for each item in the selection
    """
    for i in range(selList.length()):
        yield selList.getDependNode(i)
