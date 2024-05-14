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

from Abstract import *
import maya
import time
from maya.api import OpenMaya

# maya.utils.loadStringResourcesForModule(__name__)
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

turnexpressionName = '_turnExpression'
attrName = 'DegreesPerMeter'
circleCentreAttr = 'CircleCentre'
offsetAttrName = 'OffsetPosition'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbOpenCircleWalkUI',
                                     annotation='',
                                     category=self.category,
                                     command=['LocomotionTools.circleToolBoxUI()']))

        return self.commandList

    def assignHotkeys(self):
        return


class LocomotionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'LocomotionTools'
    hotkeyClass = hotkeys()
    funcs = functions()
    start_time = 0
    last_time = 0
    circleToolbox = None

    def __new__(cls):
        if LocomotionTools.__instance is None:
            LocomotionTools.__instance = object.__new__(cls)

        LocomotionTools.__instance.val = cls.toolName
        return LocomotionTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(LocomotionTools, self).optionUI()

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def circleToolBoxUI(self):
        if self.circleToolbox:
            self.circleToolbox.show()
        self.circleToolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                                  title='tb Circle Walk', text=str(),
                                  lockState=False, showLockButton=False, showCloseButton=True, showInfo=True)
        toolboxWidget = QWidget()
        buttonLayout = QVBoxLayout()
        toolboxWidget.setLayout(buttonLayout)
        addSelectedButton = QPushButton('Add Selected controls')
        addSelectedRotationButton = QPushButton('Add Selected controls (rotate only)')
        selectCurveButton = QPushButton('Select Curve Main')
        resetCurveButton = QPushButton('Reset curve')
        bakeOutButton = QPushButton('- Bake Out -')
        buttonLayout.addWidget(addSelectedButton)
        buttonLayout.addWidget(addSelectedRotationButton)
        buttonLayout.addWidget(selectCurveButton)
        buttonLayout.addWidget(resetCurveButton)
        buttonLayout.addWidget(bakeOutButton)
        self.circleToolbox.mainLayout.addWidget(toolboxWidget)

        addSelectedButton.clicked.connect(lambda: self.addCircleToSelected(rotateOnly=False))
        addSelectedRotationButton.clicked.connect(lambda: self.addCircleToSelected(rotateOnly=True))
        selectCurveButton.clicked.connect(self.selectCurveMain)
        resetCurveButton.clicked.connect(self.resetCurve)
        bakeOutButton.clicked.connect(self.bakeOut)

        self.circleToolbox.show()
        self.circleToolbox.setFixedSize(self.circleToolbox.sizeHint())

    def bakeOut(self):
        curveMains = cmds.ls('*:Turn_Control')
        allTempControls = list()
        for curve in curveMains:
            childNodes = cmds.listRelatives(curve, children=True, allDescendents=True)
            childNodes = [c for c in childNodes if cmds.attributeQuery('animControl', node=c, exists=True)]
            for c in childNodes:
                tempControls = cmds.listConnections(c + '.' + 'animControl')
                if not tempControls:
                    continue
                allTempControls.append(tempControls[0])
        self.allTools.tools['BakeTools'].quickBake(allTempControls,
                                                   startTime=cmds.playbackOptions(query=True, min=True),
                                                   endTime=cmds.playbackOptions(query=True, max=True),
                                                   deleteConstraints=True)
        cmds.delete(curveMains)

    def selectCurveMain(self):
        curveMains = cmds.ls('*:Turn_Control')
        cmds.select(curveMains, replace=True)
    def resetCurve(self):
        curveMains = cmds.ls('*:Turn_Control')
        for c in curveMains:
            try:
                cmds.setAttr(c + '.' + attrName, 0)
            finally:
                pass
    def addCircleToSelected(self, rotateOnly=False):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return raiseError('No valid selection', title='Cannot bend loco')

        namespace = sel[0].split(':')[0]
        strippedControllers = [x.split(':')[-1] for x in sel]
        turnControllerName = self.createGlobalTurnController(namespace=namespace)
        currentTurnAmount = cmds.getAttr(turnControllerName + '.' + attrName)
        cmds.setAttr(turnControllerName + '.' + attrName, 0)
        rotateOnlyList = list()
        if rotateOnly:
            rotateOnlyList = strippedControllers
        controlData = self.createCircleAnimControllers(namespace=namespace, controls=strippedControllers,
                                                       rotateOnly=rotateOnlyList)
        controlDict = {x:0 for x in strippedControllers}
        self.addExpressionToNodes(globalControl=turnControllerName,
                                  controls=controlDict,
                                  controlData=controlData)

        cmds.setAttr(turnControllerName + '.' + attrName, currentTurnAmount)

    def createCircleAnimControllers(self, namespace=str(), controls=list(), rotateOnly=list()):
        controlData = dict()
        globalControl = self.createGlobalTurnController(namespace=namespace)
        for cnt in controls:
            thisControl = '{ns}:{ob}'.format(ns=namespace, ob=cnt)
            controlData[cnt] = self.createTempController(control='{ns}:{ob}'.format(ns=namespace, ob=cnt))
            tempController = controlData[cnt]['tempController']
            tempControllerParent = controlData[cnt]['tempParent']
            cmds.addAttr(tempController, ln='animControl', at='message')
            cmds.connectAttr(thisControl + '.message', tempController + '.animControl')
            cmds.addAttr(tempController, ln=circleCentreAttr, at='float')
            cmds.setAttr(tempController + '.' + circleCentreAttr, edit=True, channelBox=True)
            pm.parent(tempControllerParent, globalControl)
        allControls = [x['tempController'] for x in controlData.values()]
        self.allTools.tools['BakeTools'].quickBake(allControls,
                                                   startTime=cmds.playbackOptions(query=True, min=True),
                                                   endTime=cmds.playbackOptions(query=True, max=True),
                                                   deleteConstraints=True)

        for cnt in controls:
            if cnt in rotateOnly:
                cmds.parentConstraint(controlData[cnt]['tempController'], '{ns}:{ob}'.format(ns=namespace, ob=cnt),
                                      skipTranslate=('x', 'y', 'z'))
            else:
                cmds.parentConstraint(controlData[cnt]['tempController'], '{ns}:{ob}'.format(ns=namespace, ob=cnt))
        return controlData

    def createGlobalTurnController(self, namespace=str()):
        turnControllerName = '{ns}:Turn_Control'.format(ns=namespace)
        if not cmds.objExists(turnControllerName):
            turnControllerName = str(self.funcs.tempControl(name='{ns}:Turn'.format(ns=namespace), suffix='Control', scale=1.0, drawType='pin'))

        if not cmds.attributeQuery(attrName, node=turnControllerName, exists=True):
            cmds.addAttr(turnControllerName, ln=attrName, at='double')
            cmds.setAttr(turnControllerName + '.' + attrName, channelBox=True)
        return turnControllerName

    def createTempController(self, control=None):
        if not control:
            return None, None
        if not cmds.objExists(control):
            return None, None
        tempController = str(self.funcs.tempControl(name=control, suffix='Loco', scale=1.0))
        tempParent = str(self.funcs.tempNull(name=control, suffix='LocoGrp'))
        constraint = cmds.parentConstraint(control, tempController)
        cmds.parent(tempController, tempParent)
        forwardAxis = self.guessForwardAxis(control=tempController)
        return {'tempParent': tempParent,
                'tempController': tempController,
                'forwardAxis': forwardAxis,
                'constraint': constraint}

    def max_difference_axis(self, vec1, vec2):
        """
        Returns the axis name with the largest delta
        :param vec1:
        :param vec2:
        :return:
        """
        # Calculate absolute differences for each axis
        diff_x = abs(vec1[0] - vec2[0])
        diff_y = abs(vec1[1] - vec2[1])
        diff_z = abs(vec1[2] - vec2[2])

        # Find the maximum difference among the axes
        max_diff = max(diff_x, diff_y, diff_z)

        # Determine which axis has the maximum difference
        if max_diff == diff_x:
            return 'x'
        elif max_diff == diff_y:
            return 'y'
        else:
            return 'z'

    def guessForwardAxis(self, control=None, startFrame=cmds.playbackOptions(query=True, min=True),
                         endFrame=cmds.playbackOptions(query=True, max=True)):
        if not control:
            return None, None
        if not cmds.objExists(control):
            return None, None

        thisMob = self.funcs.getMObject(control)
        startTranslation = self.getTranslationAtFrame(startFrame, thisMob)
        endTranslation = self.getTranslationAtFrame(endFrame, thisMob)

        return self.max_difference_axis(startTranslation, endTranslation)

    def getTranslationAtFrame(self, endFrame, thisMob):
        currentMDG = OpenMaya.MDGContext(OpenMaya.MTime(endFrame, om2.MTime.uiUnit()))
        currentTransform = self.funcs.om_plug_worldMatrix_at_time('worldMatrix', thisMob, currentMDG)
        mfnTransform = om2.MTransformationMatrix(currentTransform)
        endTranslation = mfnTransform.translation(om2.MSpace.kWorld)
        return endTranslation

    def addExpressionToNodes(self,
                             globalControl=None,
                             controls=dict(),
                             controlData=dict()
                             ):
        """
        Adds an expression to offset the space group, using a multmatrix node to insert the offset, plugs in
        to the driven controls choice node
        :param namespace:
        :param controls:
        :param offsetData:
        :param axis:
        :param space:
        :return:
        """

        upAxis = cmds.upAxis(query=True, axis=True)

        for cnt, offset in controls.items():
            availableAxis = ['x', 'y', 'z']
            # remove the forward axis
            availableAxis = [x for x in availableAxis if x is not controlData[cnt]['forwardAxis']]
            availableAxis = [x for x in availableAxis if x is not upAxis]

            translateAxis = 'translate' + controlData[cnt]['forwardAxis'].upper()
            rotateAxis = 'rotate' + upAxis.upper()
            floorForwardAxis = 'translate' + controlData[cnt]['forwardAxis'].upper()
            floorSideAxis = 'translate' + availableAxis[0].upper()

            if not cmds.attributeQuery(offsetAttrName, node=controlData[cnt]['tempController'], exists=True):
                cmds.addAttr(controlData[cnt]['tempController'], ln=offsetAttrName, at='double')
                cmds.setAttr(controlData[cnt]['tempController'] + '.' + offsetAttrName, channelBox=True)
                cmds.setAttr(controlData[cnt]['tempController'] + '.' + offsetAttrName, offset)

            # print(globalControl, driverNode, offsetNode)

            circleExpression(turnControl=globalControl,
                             turnAttr=attrName,
                             circleCentreAttr=circleCentreAttr,
                             outputNode=controlData[cnt]['tempParent'],
                             driverAttr=translateAxis,
                             rotateAttr=rotateAxis,
                             floorForwardAttr=floorForwardAxis,
                             floorSideAttr=floorSideAxis,
                             offsetAttr=controlData[cnt]['tempController'] + '.' + offsetAttrName,
                             driverControl=controlData[cnt]['tempController']
                             )


def circleExpression(turnControl=str(),
                     turnAttr=str(),
                     driverAttr=str(),
                     rotateAttr=str(),
                     circleCentreAttr=str(),
                     floorForwardAttr=str(),
                     floorSideAttr=str(),
                     offsetAttr=str(),
                     driverControl=str(),
                     outputNode=str()):
    """
    Builds the actual expression used to bend the x/y axis into a circular motion
    :param namespace:
    :param turnControl:
    :param turnAttr:
    :param driverAttr:
    :param offsetAttr:
    :param driverControl:
    :param outputNode:
    :return:
    """
    if 'X' in driverAttr:
        circleLine1 = "float $circleX = $radius * cos($angle) - $radius;"
        circleLine2 = "float $circleZ = $radius * sin($angle);"
        progressString = "vector $rot_offset = rot( << 0, 0, $progress >>, << 0, 1, 0 >>, -$angle);"
        offsetString = "vector $offset = rot( <<0, 0, {offsetAttr} >>, << 0, 1, 0 >>, -$angle);".format(
            offsetAttr=offsetAttr)
        groupOffsetLine = "vector $group_offset = rot($circle, << 0, 1, 0 >>, -$angle);"
        outAngleLine = "{out}.{r} = rad_to_deg(-$angle);".format(out=outputNode, r=rotateAttr)
    else:
        circleLine1 = "float $circleX = $radius * sin($angle);"
        circleLine2 = "float $circleZ = ($radius * cos($angle))- $radius;"
        progressString = "vector $rot_offset = rot( <<$progress, 0, 0 >>, << 0, 1, 0 >>, $angle);"
        offsetString = "vector $offset = rot( <<{offsetAttr}, 0, 0 >>, << 0, 1, 0 >>, -$angle);".format(
            offsetAttr=offsetAttr)
        groupOffsetLine = "vector $group_offset = rot($circle, << 0, 1, 0 >>, $angle);"
        outAngleLine = "{out}.{r} = rad_to_deg($angle);".format(out=outputNode, r=rotateAttr)
    expString = [
        "float $progress = {driverControl}.{driverAttr};".format(driverControl=driverControl,
                                                                 driverAttr=driverAttr),
        "float $offset = {offsetAttr};".format(offsetAttr=offsetAttr),
        "float $turn = {control}.{attr};".format(control=turnControl, attr=turnAttr),
        "float $circumference = 0.0;",
        "float $angle = 0.0;",
        "float $radius = 0.0;",
        "if (abs($turn) > 0.0)",
        "{",
        "$circumference = 100.0 * (360.0 /$turn);",
        "$radius = 0.5 * ($circumference / 3.14159265359);",
        "$angle = 2.0 * 3.14159265359 * (($progress + $offset) / $circumference);",
        offsetString,
        circleLine1,
        circleLine2,
        "$circle = << $circleX, 0.0, $circleZ >>;",
        progressString,
        groupOffsetLine,
        "{out}.{t} = (-$rot_offset.x + $circle.x -$offset.x);".format(out=outputNode,
                                                                      t=floorSideAttr),
        "{out}.{t} = (-$rot_offset.z + $circle.z - $offset.z);".format(out=outputNode,
                                                                       t=floorForwardAttr),
        "{out}.{t} = $radius;".format(out=driverControl, t=circleCentreAttr),
        outAngleLine,
        "}",
        "else",
        "{",
        "{out}.{t} = 0.0;".format(out=outputNode, t=floorForwardAttr),
        "{out}.{t} = 0.0;".format(out=outputNode, t=floorSideAttr),
        "{out}.{r} = 0.0;".format(out=outputNode, r=rotateAttr),
        "{out}.{r} = 0.0;".format(out=driverControl, r=circleCentreAttr),
        "}"]
    cmds.expression(name=outputNode + turnexpressionName, s=str('\n').join(expString))


def removeExpressionFromNodes(namespace=str(),
                              globalControl=str(),
                              controls=list()):
    """
    Removes any turning expression applied to a certain space.
    Also cleans up any attributes that were added to controls
    :param namespace:
    :param driverData:
    :param space:
    :return:
    """
    control = '{ns}:{S}'.format(ns=namespace, S=globalControl)
    if cmds.attributeQuery(attrName, node=control, exists=True):
        cmds.deleteAttr(control + '.' + attrName)

    for control in controls:
        node = '{ns}:{ob}'.format(ns=namespace, ob=control)
        expression = cmds.listConnections(node + '.' + offsetAttrName, source=False, destination=True, plugs=False)
        cmds.delete(expression)