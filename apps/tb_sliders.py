import pymel.core as pm
import pymel.core.datatypes as dt
import maya.cmds as cmds
import maya.OpenMayaUI as omUI
import maya.api.OpenMaya as om2
from maya.api import OpenMayaAnim
from maya.api import OpenMaya

qtVersion = pm.about(qtVersion=True)
margin = 2
from random import randint
from Abstract import *

if qtVersion.split('.')[0] < 5:
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
import sys, os

scriptLocation = os.path.dirname(os.path.realpath(__file__))
IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Icons'))

baseIconFile = 'iceCream.png'
hoverIconFile = 'iceCreamInverse.png'
activeIconFile = 'iceCream.png'
inactiveIconFile = 'blank.png'
dotSmallIconFile = 'dotSmall.png'
barSmallIconFile = 'barSmall.png'

noTint = QColor(0, 0, 0)
hoverTint = QColor(0, 128, 0)
dragTint = QColor(0, 128, 0)


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_sliders')
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='inbetweenSliderPress', annotation='',
                                     category=self.category, command=['slideTools.inbetweenSlidePress()']))
        self.addCommand(self.tb_hkey(name='inbetweenSliderRelease', annotation='',
                                     category=self.category, command=['slideTools.inbetweenSlideRelease()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class slideTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'slideTools'
    hotkeyClass = hotkeys()
    funcs = functions()
    app = None
    slideUI = None

    keyPressHandler = None
    selectionChangedCallback = -1

    def __new__(cls):
        if slideTools.__instance is None:
            slideTools.__instance = object.__new__(cls)

        slideTools.__instance.val = cls.toolName
        slideTools.__instance.app = QApplication.instance()

        return slideTools.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(slideTools, self).optionUI()
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def pickInbetweenClass(self):
        # TODO - don't pick the slider class like this, pick it in init for UI
        selectedKeys = cmds.keyframe(query=True, selected=True)
        selectedObjects = cmds.ls(sl=True, type='transform')
        geState = getGraphEditorState()
        if not geState:
            return worldSpaceTween()
        else:
            if selectedKeys:
                return keyframeTween()
            elif selectedObjects:
                return worldSpaceTween()
        return tweenBase()

    def inbetweenSlidePress(self):
        try:
            self.slideUI.close()
            self.slideUI.deleteLater()
            self.app.removeEventFilter(self.keyPressHandler)
        except:
            self.app.removeEventFilter(self.keyPressHandler)

        self.tweenClass = self.pickInbetweenClass()

        self.slideUI = sliderWidget(self.funcs.getWidgetAtCursor(), tweemClass=self.tweenClass, funcs=self.funcs)
        self.slideUI.showUI()
        try:
            cmds.scriptJob(kill=self.selectionChangedCallback)
        except:
            pass
        self.selectionChangedCallback = self.slideUI.createSelectionChangedScriptJob()
        print 'hello it is me'
        self.keyPressHandler = keypressHandler(self.tweenClass, self.slideUI)
        self.app.installEventFilter(self.keyPressHandler)

    def inbetweenSlideRelease(self):
        try:
            self.slideUI.close()
            self.slideUI.deleteLater()
            self.app.removeEventFilter(self.keyPressHandler)
        except:
            self.app.removeEventFilter(self.keyPressHandler)


class keypressHandler(QObject):

    def __init__(self, tweenClass=None, UI=None):
        super(keypressHandler, self).__init__()
        self.tweenClass = tweenClass
        self.UI = UI

    def eventFilter(self, target, event):
        if event.type() == event.KeyRelease:
            if event.key() == Qt.Key_Control:
                self.UI.controlReleased()
                return True
            elif event.key() == Qt.Key_Shift:
                self.UI.shiftReleased()
                return True
        if event.type() == event.KeyPress:
            if event.key() == Qt.Key_Control:
                self.UI.controlPressed()
                return True
            elif event.key() == Qt.Key_Shift:
                self.UI.shiftPressed()
                return True
        return False
        return super(keypressHandler, self).eventFilter(target, event)


class attrData(object):
    """
    Dict contains attr names as key, value as value
    """
    attributes = dict()

    def __init__(self, attributes):
        self.attributes = dict.fromkeys(attributes, None)


def lerpMVector(vecA, vecB, alpha):
    return vecB * alpha + vecA * (1.0 - alpha)


def lerpFloat(a, b, alpha):
    return a * alpha + b * (1.0 - alpha)


class tweenBase(object):
    ## Get the current UI Unit
    uiUnit = OpenMaya.MTime.uiUnit()
    keyboardModifier = None
    labelText = 'base class'

    def __init__(self):
        self.keyState = pm.autoKeyframe(query=True, state=True)
        self.affectedObjects = list()
        self.alpha = 0

    def apply(self):
        pm.autoKeyframe(state=self.keyState)
        self.updateAlpha(self.alpha, disableAutoKey=False)

    @staticmethod
    def iterSelection():
        """
        generator style iterator over current Maya active selection
        :return: [MObject) an MObject for each item in the selection
        """
        sel = om2.MGlobal.getActiveSelectionList()
        for i in xrange(sel.length()):
            yield sel.getDependNode(i)

    def setAffectedObjects(self):
        """
        set the affected objects/keys
        :return:
        """

    def cacheValues(self):
        """
        Cache the initial values/plugs to keep the speed high
        :return:
        """
        self.get_modifier()

    def get_modifier(self):
        self.keyboardModifier = {0: None,
                                 1: 'shift',
                                 4: 'ctrl',
                                 5: 'ctrlShift',
                                 8: 'alt',
                                 9: 'shiftAlt',
                                 12: 'ctrlAlt',
                                 }[cmds.getModifiers()]

    def updateAlpha(self, alpha, disableAutoKey=True):
        """
        perform the update calculation here that affects the objects/keys
        :param alpha:
        :param disableAutoKey:
        :return:
        """
        pass
        # print self.keyboardModifier

    def om_plug_at_time(self, dep_node, plug, mdg):
        '''
        Getting the plug from openMaya.
        Then create a time mdgContext and evaluate it.
        This is the fastest with layer compatability... however i suspect there to be issues when doing complex simulations.

        :param dep_node: object string name i.e. "pSphere1"
        :param attr: the attribute to check i.e. "tx"
        :return: a list of values per frame.
        '''

        objMfn = OpenMaya.MFnDependencyNode(dep_node)
        ## Get the plug of the node. (networkedplug = False, as it no longer profides a speed improvement)
        value = objMfn.findPlug(plug, False).asDouble(mdg)

        return value

    def om_plug_worldMatrix_at_time(self, matrix, dep_node, mdg):
        '''
        Getting the plug from openMaya.
        Then create a time mdgContext and evaluate it.
        This is the fastest with layer compatability... however i suspect there to be issues when doing complex simulations.

        :param dep_node: object string name i.e. "pSphere1"
        :param attr: the attribute to check i.e. "tx"
        :return: a list of values per frame.
        '''

        objMfn = OpenMaya.MFnDependencyNode(dep_node)
        ## Get the plug of the node. (networkedplug = False, as it no longer profides a speed improvement)
        plug = objMfn.findPlug(matrix, False).elementByLogicalIndex(0)

        value = om2.MFnMatrixData(plug.asMObject(mdg)).matrix()

        return value


class worldSpaceTween(tweenBase):
    labelText = 'worldSpaceTween'
    ignoredAttributeNames = ['translateX',
                             'translateY',
                             'translateZ',
                             'rotateX',
                             'rotateY',
                             'rotateZ',
                             'scaleX',
                             'scaleY',
                             'scaleZ']
    ignoredAttributeTypes = ['bool', 'enum', 'message']

    def __init__(self):
        super(worldSpaceTween, self).__init__()
        self.keyState = pm.autoKeyframe(query=True, state=True)
        self.affectedObjects = list()
        self.alpha = 0
        self.currentTime = float()
        self.startkeyTimes = dict()
        self.startTransforms = dict()
        self.endKeyTimes = dict()
        self.endTransforms = dict()

        # store mfp dependency nodes
        self.mfnDepNodes = dict()

        # store matrix values here
        self.currentMTransformationMatrix = dict()
        self.currentParentInverseMTransformationMatrix = dict()
        self.prevMTransformationMatrix = dict()
        self.nextMTransformationMatrix = dict()

        # store the user attributes here
        self.currentAttrData = dict()
        self.prevAttrData = dict()
        self.nextAttrData = dict()

    def apply(self):
        super(worldSpaceTween, self).apply()

    @staticmethod
    def iterSelection():
        """
        generator style iterator over current Maya active selection
        :return: [MObject) an MObject for each item in the selection
        """
        sel = om2.MGlobal.getActiveSelectionList()
        for i in xrange(sel.length()):
            yield sel.getDependNode(i)

    def setAffectedObjects(self):
        sel = cmds.ls(sl=True)
        keys = cmds.keyframe(query=True, selected=True)

        if sel:
            self.affectedObjects = sel

    def cacheValues(self):
        # print 'affectedObjects', self.affectedObjects
        # just get one objects next and previous transforms
        thisTime = cmds.currentTime(query=True)

        for obj in self.affectedObjects:
            self.startkeyTimes[obj] = cmds.findKeyframe(obj, time=(thisTime, thisTime), which="previous")
            self.endKeyTimes[obj] = cmds.findKeyframe(obj, time=(thisTime, thisTime), which="next")
            allAttrs = cmds.listAttr(obj, keyable=True, scalar=True, settable=True, inUse=True)
            validAttrs = list()
            for attr in allAttrs:
                if attr in self.ignoredAttributeNames:
                    continue
                attrType = cmds.getAttr(obj + '.' + attr, type=True)
                if attrType in self.ignoredAttributeTypes:
                    continue
                if cmds.getAttr(obj + '.' + attr, lock=True):
                    continue
                if not cmds.getAttr(obj + '.' + attr, keyable=True):
                    continue
                validAttrs.append(attr)
            if len(validAttrs):
                self.currentAttrData[obj] = attrData(validAttrs)
                self.prevAttrData[obj] = attrData(validAttrs)
                self.nextAttrData[obj] = attrData(validAttrs)
        # print 'start times', self.startkeyTimes
        # print 'end times', self.endKeyTimes
        for eachMob in self.iterSelection():
            obj_dag_path = om2.MDagPath.getAPathTo(eachMob)
            objMfn = OpenMaya.MFnDependencyNode(eachMob)

            self.mfnDepNodes[str(obj_dag_path)] = objMfn
            # print objMfn
            currentMDG = OpenMaya.MDGContext(OpenMaya.MTime(thisTime, self.uiUnit))
            currentTransform = self.om_plug_worldMatrix_at_time('worldMatrix', eachMob, currentMDG)
            self.currentMTransformationMatrix[str(obj_dag_path)] = om2.MTransformationMatrix(currentTransform)
            currentParentInverseTransform = self.om_plug_worldMatrix_at_time('parentInverseMatrix', eachMob, currentMDG)
            self.currentParentInverseMTransformationMatrix[str(obj_dag_path)] = om2.MTransformationMatrix(
                currentParentInverseTransform)

            prevMDG = OpenMaya.MDGContext(OpenMaya.MTime(self.startkeyTimes[obj], self.uiUnit))
            previousTransform = self.om_plug_worldMatrix_at_time('worldMatrix', eachMob, prevMDG)
            self.prevMTransformationMatrix[str(obj_dag_path)] = om2.MTransformationMatrix(previousTransform)

            nextMDG = OpenMaya.MDGContext(OpenMaya.MTime(self.endKeyTimes[obj], self.uiUnit))
            nextTransform = self.om_plug_worldMatrix_at_time('worldMatrix', eachMob, nextMDG)
            self.nextMTransformationMatrix[str(obj_dag_path)] = om2.MTransformationMatrix(nextTransform)

    def updateAlpha(self, alpha, disableAutoKey=True):
        super(worldSpaceTween, self).updateAlpha(alpha, disableAutoKey=disableAutoKey)
        pm.autoKeyframe(state=not disableAutoKey)
        self.alpha = alpha

        for obj in self.affectedObjects:
            translation = self.prevMTransformationMatrix[obj].translation(om2.MSpace.kWorld)
            translation = self.nextMTransformationMatrix[obj].translation(om2.MSpace.kWorld)
            rotation = self.prevMTransformationMatrix[obj].rotation(asQuaternion=False)
            rotation = self.nextMTransformationMatrix[obj].rotation(asQuaternion=False)
            outAlpha = 0
            if self.alpha >= 0:
                # lerp to next
                currentTranslation = self.currentMTransformationMatrix[obj].translation(om2.MSpace.kWorld)
                targetTranslation = self.nextMTransformationMatrix[obj].translation(om2.MSpace.kWorld)

                currentRotation = self.currentMTransformationMatrix[obj].rotation(asQuaternion=True)
                targetRotation = self.nextMTransformationMatrix[obj].rotation(asQuaternion=True)
                outAlpha = alpha
            else:
                # lerp to prev
                currentTranslation = self.currentMTransformationMatrix[obj].translation(om2.MSpace.kWorld)
                targetTranslation = self.prevMTransformationMatrix[obj].translation(om2.MSpace.kWorld)

                currentRotation = self.currentMTransformationMatrix[obj].rotation(asQuaternion=True)
                targetRotation = self.prevMTransformationMatrix[obj].rotation(asQuaternion=True)
                outAlpha = alpha * -1

            lerpedWorldTranslation = lerpMVector(currentTranslation, targetTranslation, outAlpha)
            lerpedWorldRotation = om2.MQuaternion.slerp(currentRotation, targetRotation, outAlpha)

            lerpedWorldMatrix = om2.MTransformationMatrix()
            lerpedWorldMatrix.setTranslation(lerpedWorldTranslation, om2.MSpace.kWorld)
            lerpedWorldMatrix.setRotation(lerpedWorldRotation)
            resultMatrix = lerpedWorldMatrix.asMatrix() * self.currentParentInverseMTransformationMatrix[obj].asMatrix()
            transformMatrixObj = om2.MTransformationMatrix(resultMatrix)
            resultTranslate = transformMatrixObj.translation(om2.MSpace.kWorld)
            resultRotate = transformMatrixObj.rotation(asQuaternion=False)

            translateNames = ['tx', 'ty', 'tz']  # , 'rx','ry', 'rz', 'sx', 'sy', 'sz', ]
            translatePlugs = [self.mfnDepNodes[obj].findPlug(eachName, False) for eachName in translateNames]
            rotateNames = ['rotateX', 'rotateY', 'rotateZ']
            rotatePlugs = [self.mfnDepNodes[obj].findPlug(eachName, False) for eachName in rotateNames]

            if not self.keyboardModifier == 'shift':
                for index, plug in enumerate(translatePlugs):
                    if not plug.isLocked:
                        plug.setFloat(resultTranslate[index])
            if not self.keyboardModifier == 'ctrl':
                for index, plug in enumerate(rotatePlugs):
                    if not plug.isLocked:
                        plug.setFloat(resultRotate[index])


class keyframeTween(tweenBase):
    labelText = 'keyframeTween'

    def __init__(self):
        super(keyframeTween, self).__init__()
        self.keyState = pm.autoKeyframe(query=True, state=True)
        self.affectedObjects = list()
        self.alpha = 0
        self.currentTime = float()
        self.selectedKeyTimes = dict()
        self.selectedKeyIndexes = dict()
        self.selectedKeyValues = dict()
        self.curvePreviousValues = dict()
        self.curveNextValues = dict()

        import tb_functions as funcs
        reload(funcs)
        self.funcs = funcs.functions()

    def apply(self):
        super(keyframeTween, self).apply()
        self.cacheValues()

    def setAffectedObjects(self):
        self.affectedObjects = self.funcs.get_selected_curves()

    def cacheValues(self):
        # just get one objects next and previous transforms
        thisTime = cmds.currentTime(query=True)
        if not self.affectedObjects:
            return
        for curve in self.affectedObjects:
            self.selectedKeyTimes[curve] = self.funcs.get_key_times(curve)
            self.selectedKeyIndexes[curve] = self.funcs.get_selected_key_indexes(curve)
            self.selectedKeyValues[curve] = self.funcs.get_key_values(curve)
            curvePreviousValues = list()
            curveNextValues = list()
            for index, indexVal in enumerate(self.selectedKeyIndexes[curve]):
                previousValue = self.funcs.get_prev_key_values_from_index(curve, indexVal)
                nextValue = self.funcs.get_next_key_values_from_index(curve, indexVal)
                curvePreviousValues.append(previousValue[0])
                curveNextValues.append(nextValue[0])
            self.curvePreviousValues[curve] = curvePreviousValues
            self.curveNextValues[curve] = curveNextValues

    def updateAlpha(self, alpha, disableAutoKey=True):
        super(keyframeTween, self).updateAlpha(alpha, disableAutoKey=disableAutoKey)
        pm.autoKeyframe(state=not disableAutoKey)
        self.alpha = alpha
        if self.keyboardModifier == 'shift':
            # print 'just shift'
            for curve in self.affectedObjects:
                for index, indexVal in enumerate(self.selectedKeyIndexes[curve]):
                    if self.alpha >= 0:
                        # lerp to next
                        targetValue = self.curveNextValues[curve][-1]
                        outAlpha = alpha
                    else:
                        # lerp to prev
                        targetValue = self.curvePreviousValues[curve][0]
                        outAlpha = alpha * -1

                    lerpedValue = lerpFloat(targetValue, self.selectedKeyValues[curve][index], outAlpha)
                    cmds.keyframe(curve, edit=True, valueChange=lerpedValue, index=((indexVal),))
            return
        if self.keyboardModifier == 'ctrl':
            # print 'just control'
            for curve in self.affectedObjects:
                for index, indexVal in enumerate(self.selectedKeyIndexes[curve]):
                    if self.alpha >= 0:
                        # lerp to next
                        targetValueA = self.curveNextValues[curve][index]
                        targetValueB = self.curvePreviousValues[curve][index]
                        targetValue = (targetValueA + targetValueB) / 2.0
                        outAlpha = alpha
                    else:
                        # lerp to prev
                        targetValue = self.curvePreviousValues[curve][0]
                        outAlpha = alpha * -1

                    lerpedValue = lerpFloat(targetValue, self.selectedKeyValues[curve][index], outAlpha)
                    cmds.keyframe(curve, edit=True, valueChange=lerpedValue, index=((indexVal),))
            return
        for curve in self.affectedObjects:
            if self.alpha >= 0:
                # lerp to next
                targetValue = self.curveNextValues[curve][-1]
                baseValue = self.selectedKeyValues[curve][-1]
                outAlpha = alpha
            else:
                # lerp to prev
                targetValue = self.curvePreviousValues[curve][0]
                baseValue = self.selectedKeyValues[curve][0]
                outAlpha = alpha * -1
            lerpedValue = lerpFloat(targetValue - baseValue, 0, outAlpha)
            # print 'outAlpha', outAlpha, 'lerpedValue', lerpedValue
            for index, indexVal in enumerate(self.selectedKeyIndexes[curve]):
                # print self.selectedKeyValues[curve][index]
                outValue = self.selectedKeyValues[curve][index] + lerpedValue

                cmds.keyframe(curve, edit=True, valueChange=outValue, index=((indexVal),))


class DragButton(QLabel):
    label = str()
    xMin = 0
    xMax = 100
    restPoint = QPoint(0, 0)
    clickOffset = QPoint(0, 0)
    __mousePressPos = None
    __mouseMovePos = None
    restX = 0
    restY = 0
    halfWidth = 10
    uiParent = None
    percent = 50
    draggable = True
    masterDragger = None

    baseIcon = baseIconFile
    hoverIcon = hoverIconFile
    activeIcon = activeIconFile
    inactiveIcon = inactiveIconFile

    minButtonPos = 0
    maxButtonPos = 100

    def __init__(self, label, draggable=True,
                 percent=50,
                 xMin=0,
                 xMax=200,
                 parent=None,
                 uiParent=None,
                 masterDragger=None,
                 baseIcon=baseIconFile,
                 hoverIcon=hoverIconFile,
                 activeIcon=activeIconFile,
                 inactiveIcon=inactiveIconFile,
                 width=16,
                 height=16,
                 ):
        QLabel.__init__(self, parent)
        self.drawWidth = width
        self.drawHeight = height
        sp_retain = QSizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp_retain)
        self.uiParent = uiParent
        self.masterDragger = masterDragger
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFixedSize(20, 20)
        self.halfWidth = (0.5 * self.width())
        self.baseIcon = QPixmap(os.path.join(IconPath, baseIcon))
        self.hoverIcon = QPixmap(os.path.join(IconPath, hoverIcon))
        self.activeIcon = QPixmap(os.path.join(IconPath, activeIcon))
        self.inactiveIcon = QPixmap(os.path.join(IconPath, inactiveIcon))
        self.setPixmap(self.baseIcon)
        self.draggable = draggable
        self.percent = percent
        self.xMin = xMin
        self.xMax = xMax
        self.setNonHoverSS()
        if self.percent <= 0:
            self.restX = xMin
        elif self.percent >= 100:
            self.restX = xMax - self.width()
        else:
            self.restX = (0.5 * self.width()) + ((xMax - xMin - self.width()) / (100 / self.percent))

        self.minButtonPos = self.xMin
        self.maxButtonPos = self.xMax - self.width()

        self.restY = 7
        self.restPoint = QPoint(self.restX, self.restY)
        self.move(self.restPoint)
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(1)
        shadow.setBlurRadius(3)
        self.setGraphicsEffect(shadow)

        self.HoverlineColor = QColor(128, 255, 128, 128)
        self.NonHoverlineColor = QColor(128, 128, 128, 128)

        self.innerLineColour = self.NonHoverlineColor

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        fillColor = QColor(255, 165, 0, 180)
        lineColor = QColor(64, 64, 64, 128)

        qp.drawRoundedRect(QRect(0.5 * (self.width() - self.drawWidth -1),
                                 0.5 * (self.height() - self.drawHeight-1),
                                 self.drawWidth+2,
                                 self.drawHeight+2), 2, 2)
        sideEdge = (1.0 / self.rect().width()) * 10
        topEdge = (1.0 / self.rect().height()) * 10

        qp.setRenderHint(QPainter.Antialiasing)
        #qp.setCompositionMode(QPainter.CompositionMode_HardLight)
        orange = QColor(255, 160, 47, 64)
        darkOrange = QColor(215, 128, 26, 64)

        qp.setPen(QPen(QBrush(self.innerLineColour), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, orange)
        grad.setColorAt(1, darkOrange)
        qp.setBrush(QBrush(grad))

        qp.drawRoundedRect(
            QRect(0.5 * (self.width() - self.drawWidth), 0.5 * (self.height() - self.drawHeight), self.drawWidth,
                  self.drawHeight), 4, 4)

        qp.end()

    def updateAlpha(self):
        """
        sends the alpha value back to the ui parent class
        :return:
        """
        range = (self.xMax) - (self.xMin) - self.width()

        pos = self.pos().x() - (0.5 * self.width())
        alpha = -1 * (1.0 - (pos / (range * 0.5)))
        # print alpha
        if self.uiParent is not None:
            self.uiParent.updateAlpha(alpha)

    def setButtonPosition(self, position):
        self.move(position)
        self.updateAlpha()

    def setButtonToRestPosition(self):
        self.move(self.restPoint)

    def setNonHoverSS(self):
        self.setStyleSheet("""
      QWidget{
          background-color: rgba(50, 50, 50, 0);
          color : rgba(50, 50, 50, 255);

          font-weight: bold;
          border-radius: 6px;
      }
      """)
        # background-image: url('%s\iceCream.png');

    def setHoverSS(self):
        self.setStyleSheet("""
      QWidget{
          background-color: rgba(50, 50, 50, 0);
          color : rgba(50, 50, 50, 255);
          font-weight: bold;
          border-radius: 6px;
      }
      """)

    def setIconStateInactive(self):
        self.setPixmap(self.inactiveIcon)

    def setIconStateBase(self):
        self.setPixmap(self.baseIcon)

    def setIconStateHover(self):
        self.setPixmap(self.hoverIcon)

    def setIconStateInactive(self):
        self.setPixmap(self.inactiveIcon)

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if self.uiParent.isDragging:
            print 'mousePressEvent when already dragging'
            return super(DragButton, self).mousePressEvent(event)
        else:
            self.uiParent.startDrag(event.button())

        if event.button() == Qt.RightButton:
            print 'RIGHT BUTTON PRESS'

        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton or event.button() == Qt.MiddleButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()
            self.clickOffset = self.mapFromGlobal(event.globalPos())
            self.dragStart = self.mapFromGlobal(event.globalPos())

            self.updatePosition(event.globalPos())
            self.uiParent.hideAllAnchors()
            if self.masterDragger:
                self.masterDragger.setPositionFromSlider(self.pos() + QPoint(self.halfWidth, 0))
            # self.uiParent.hideAllAnchors()
        super(DragButton, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.RightButton:
            print 'RIGHT BUTTON MOVE'
        if not self.uiParent.dragButton:
            return super(DragButton, self).mouseMoveEvent(event)
        if event.buttons() == Qt.LeftButton or event.buttons() == Qt.RightButton or event.buttons() == Qt.MiddleButton:
            if not self.draggable:
                if self.masterDragger:
                    # dragging one of those dot controls
                    self.setIconStateInactive()
                    self.uiParent.hideAllAnchors()
                    self.masterDragger.setPositionFromSlider(self.pos() + QPoint(self.halfWidth, 0))
                    # TODO - make the drag snap to the other anchors
                    # print self.uiParent.anchorButtons
                    # TODO - maybe split the get new position/alpha and the move
            # adjust offset from clicked point to origin of widget
            else:
                self.updatePosition(event.globalPos())

        super(DragButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setIconStateBase()
        self.uiParent.endDrag()
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos
            if moved.manhattanLength() > 3:
                event.ignore()
                return

        super(DragButton, self).mouseReleaseEvent(event)

    def updatePosition(self, globalPos):
        if not self.__mousePressPos:
            self.__mousePressPos = globalPos
        if not self.__mouseMovePos:
            self.__mouseMovePos = globalPos
        currPos = self.mapToGlobal(self.pos())

        ScreenVal = self.mapToParent(globalPos).x() - self.clickOffset.x()

        diff = globalPos - self.__mouseMovePos
        diff.setY(0)
        newPos = self.mapFromGlobal(currPos + diff)

        if ScreenVal < self.mapToGlobal(QPoint(self.xMin, 0)).x():
            newPos.setX(self.minButtonPos)
        if ScreenVal >= self.mapToGlobal(QPoint(self.xMax - self.width(), 0)).x():
            # print 'here'
            newPos.setX(self.maxButtonPos)
        # if current mouse position out of slider range, diff = 0

        # print 'new pos', newPos, self.minButtonPos, self.maxButtonPos
        newPos.setX(int(max(newPos.x(), self.minButtonPos)))
        newPos.setX(int(min(newPos.x(), self.maxButtonPos)))
        self.move(newPos)
        self.updateAlpha()
        self.uiParent.setWidgetVisibilityDuringDrag()
        self.__mouseMovePos = globalPos

    def setPositionFromSlider(self, position):
        position.setY(self.restY)
        position.setX(position.x() - self.halfWidth)
        if position.x() <= self.minButtonPos:
            position.setX(self.minButtonPos)
        if position.x() >= self.maxButtonPos:
            position.setX(self.maxButtonPos)
        self.move(position)
        self.updateAlpha()
        self.uiParent.setWidgetVisibilityDuringDrag()

    def enterEvent(self, event):
        # self.setHoverSS()
        self.setHoverTint()
        return super(DragButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setNoTint()
        return super(DragButton, self).enterEvent(event)

    def setHoverTint(self):
        self.innerLineColour = self.HoverlineColor
        self.update()

    def setNoTint(self):
        self.innerLineColour = self.NonHoverlineColor
        self.update()

    def setTintEffect(self):
        if self.graphicsEffect() is None:
            self.effect = QGraphicsColorizeEffect(self)
            self.effect.setStrength(0.6)
            self.setGraphicsEffect(self.effect)


class sliderBar(QLabel):
    uiParent = None
    barWidth = 300

    def __init__(self, uiParent, width):
        QLabel.__init__(self)
        self.barWidth = width
        self.uiParent = uiParent
        self.setFixedSize(self.barWidth, 24)
        self.setAlignment(Qt.AlignCenter)
        # self.setStyleSheet("QLabel {background-color: rgba(128, 128, 128, 128);}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        fillColor = QColor(255, 165, 0, 180)
        lineColor = QColor(64, 64, 64, 64)
        alpha = 50
        sideEdge = (1.0 / self.rect().width()) * 10
        topEdge = (1.0 / self.rect().height()) * 10
        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        orange = QColor(255, 160, 47, 32)
        darkOrange = QColor(215, 128, 26, 32)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, orange)
        grad.setColorAt(1, darkOrange)
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(QRect(0, 2, 300, 20), 4, 4)

        qp.end()
        return
        # qp.setCompositionMode(qp.CompositionMode_Overlay)
        # qp.setCompositionMode(qp.CompositionMode_Darken)
        qp.setPen(QPen(QBrush(lineColor), 4))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, QColor(0, 0, 0, alpha))
        grad.setColorAt(topEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1 - topEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1, QColor(0, 0, 0, alpha))
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 4, 4)
        grad = QLinearGradient(0, 16, 400, 16)
        grad.setColorAt(0, QColor(0, 0, 0, alpha))
        grad.setColorAt(sideEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1 - sideEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1, QColor(0, 0, 0, alpha))

        qp.setBrush(QBrush(grad))
        # qp.setBrush(QBrush(self.currentFillColour))

        qp.drawRoundedRect(self.rect(), 4, 4)

    def mousePressEvent(self, event):
        if self.uiParent.isDragging:
            print 'mousePressEvent when already dragging'
        self.uiParent.hideAllAnchors()
        self.uiParent.startDrag(event.button())

        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mousePressPos.setX(self.__mousePressPos.x() + 8)
            self.__mouseMovePos = event.globalPos()

        self.uiParent.dragButton.setPositionFromSlider(self.mapFromGlobal(self.__mousePressPos))
        super(sliderBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.uiParent.hideAllAnchors()
        if event.buttons() == Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()
            self.__mousePressPos.setX(self.__mousePressPos.x() + 8)

        self.uiParent.dragButton.setPositionFromSlider(self.mapFromGlobal(self.__mousePressPos))

        super(sliderBar, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.uiParent.endDrag()
        super(sliderBar, self).mouseReleaseEvent(event)


class sliderWidget(QWidget):
    def __init__(self, parent, tweemClass=tweenBase,
                 objectTweenClass=None,
                 objectShiftTweenClass=None,
                 objectControlTweenClass=None,
                 keyTweenLMB=keyframeTween,
                 keyTweenMMB=keyframeTween,
                 keyTweenRMB=keyframeTween,
                 keyShiftTweenClass=None,
                 keyControlTweenClass=None,
                 funcs=None,
                 largeAnchors=[0, 100.0],
                 mediumAnchors=[25.0, 50, 75.0],
                 smallAnchors=[12.5, 37.5, 62.5, 87.5]
                 ):
        QWidget.__init__(self, parent)


        self.isDragging = False
        self.currentDragButton = None
        if tweemClass is None:
            self.tweenClass = tweenBase()
        else:
            self.tweenClass = tweemClass
        self.keyTweenClassDict = {
            Qt.LeftButton: keyTweenLMB,
            Qt.MiddleButton: keyTweenMMB,
            Qt.RightButton: keyTweenRMB,
        }
        self.objTweenClassDict = {
            Qt.LeftButton: worldSpaceTween,
            Qt.MiddleButton: worldSpaceTween,
            Qt.RightButton: worldSpaceTween,
        }
        self.currentTweenClassDict = None
        self.affectingKeys = True
        self.funcs = funcs
        self.barHorizontalOffset = 10
        self.setFocus()
        self.lastEvent = None
        self.dragButton = None
        self.anchorButtons = list()
        self.largeAnchorPositions = list()
        self.mediumAnchorPositions = list()
        self.smallAnchorPositions = list()
        self.tweenClass = None
        self.barWidth = 300
        self.largeAnchorPositions = largeAnchors
        self.mediumAnchorPositions = mediumAnchors
        self.smallAnchorPositions = smallAnchors
        self.setFixedSize(500, 64)
        self.mainLayout = QHBoxLayout(self)
        # self.setStyleSheet('QWidget{margin-left:-1px;}')
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        # self.mainLayout.setSpacing(0)
        self.horizontalBar = sliderBar(self, self.barWidth)
        self.dragButton = DragButton("BD",
                                     xMin=self.barHorizontalOffset,
                                     xMax=self.horizontalBar.width() + self.barHorizontalOffset,
                                     parent=self.horizontalBar,
                                     uiParent=self)

        self.setFocusPolicy(Qt.StrongFocus)

        self.dragButton.setFocusPolicy(Qt.StrongFocus)

        for p in self.largeAnchorPositions:
            anchorBtn = DragButton("BD",
                                   xMin=self.barHorizontalOffset,
                                   xMax=self.horizontalBar.width() + self.barHorizontalOffset,
                                   parent=self.horizontalBar,
                                   uiParent=self,
                                   draggable=False,
                                   percent=p,
                                   masterDragger=self.dragButton,
                                   baseIcon=barSmallIconFile,
                                   hoverIcon=barSmallIconFile,
                                   activeIcon=dotSmallIconFile,
                                   inactiveIcon=inactiveIconFile,
                                   width=12,
                                   height=12,
                                   )
            self.anchorButtons.append(anchorBtn)
        for p in self.mediumAnchorPositions:
            anchorBtn = DragButton("BD",
                                   xMax=self.horizontalBar.width(),
                                   parent=self.horizontalBar,
                                   uiParent=self,
                                   draggable=False,
                                   percent=p,
                                   masterDragger=self.dragButton,
                                   baseIcon=dotSmallIconFile,
                                   hoverIcon=dotSmallIconFile,
                                   activeIcon=dotSmallIconFile,
                                   inactiveIcon=inactiveIconFile,
                                   width=10,
                                   height=10,
                                   )
            self.anchorButtons.append(anchorBtn)
        for p in self.smallAnchorPositions:
            anchorBtn = DragButton("BD",
                                   xMax=self.horizontalBar.width(),
                                   parent=self.horizontalBar,
                                   uiParent=self,
                                   draggable=False,
                                   percent=p,
                                   masterDragger=self.dragButton,
                                   baseIcon=dotSmallIconFile,
                                   hoverIcon=dotSmallIconFile,
                                   activeIcon=dotSmallIconFile,
                                   inactiveIcon=inactiveIconFile,
                                   width=6,
                                   height=6,
                                   )
            self.anchorButtons.append(anchorBtn)
        self.mainLayout.addWidget(self.horizontalBar)
        self.horizontalBar.move(2,2)
        for btn in self.anchorButtons:
            self.mainLayout.addWidget(btn)
        self.mainLayout.addWidget(self.dragButton)

        self.labelLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.labelLayout)

        # self.label = QLabel('testy test test')
        # self.label.setFixedWidth(200)
        # self.label.setStyleSheet("color: black")
        # spacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.labelLayout.addWidget(self.label)
        # self.labelLayout.addItem(spacerItem)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setSS()

        self.fillColourBaseTop = QColor(255, 160, 47, 88)
        self.fillColourBaseBottom = QColor(215, 128, 26, 88)
        self.fillColourAltTop = QColor(255, 160, 200, 88)
        self.fillColourAltBottom = QColor(215, 128, 200, 88)
        self.currentFillColourTop = self.fillColourBaseTop
        self.currentFillColourBottom = self.fillColourBaseBottom

    def createSelectionChangedScriptJob(self):
        self.selectionChangedCallback = cmds.scriptJob(event=("SelectionChanged", pm.Callback(self.updateTweenClass)))
        return self.selectionChangedCallback

    def setWidgetVisibilityDuringDrag(self):
        pass

    def hideAllAnchors(self):
        for btn in self.anchorButtons:
            btn.setIconStateInactive()

    def showAllAnchors(self):
        for btn in self.anchorButtons:
            btn.setIconStateBase()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(64, 64, 64, 64)
        alpha = 50
        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        orange = QColor(255, 160, 47, 32)
        darkOrange = QColor(215, 128, 26, 32)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, orange)
        grad.setColorAt(1, darkOrange)
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(QRect(314, 8, 180, 20), 4, 4)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setFont(QFont('Helvetic', 10))
        textRect = QRect(318, 7, 500, 32)
        '''
        textRect.translate(0,1)
        qp.setPen(QColor(0,0,0,20))
        qp.drawText(textRect, Qt.AlignLeft, self.tweenClass.labelText)
        textRect.translate(0, -2)
        qp.setPen(QColor(0,0,0,255))
        qp.drawText(textRect, Qt.AlignLeft, self.tweenClass.labelText)
        textRect.translate(0, 1)
        '''
        qp.setPen(QColor(Qt.lightGray))
        qp.drawText(textRect, Qt.AlignLeft, self.tweenClass.labelText)
        qp.end()
        '''
        fillColor = QColor(255, 165, 0, 180)
        lineColor = QColor(64, 64, 64, 64)
        alpha = 50
        sideEdge = (1.0 / self.rect().width()) * 10
        topEdge = (1.0 / self.rect().height()) * 10
        qp.setCompositionMode(qp.CompositionMode_Clear)
        # qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        orange = QColor(255, 160, 47, 32)
        darkOrange = QColor(215, 128, 26, 32)

        qp.setPen(QPen(QBrush(lineColor), 0))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, self.currentFillColourTop)
        grad.setColorAt(1, self.currentFillColourBottom)
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 4, 4)

        # qp.setCompositionMode(qp.CompositionMode_Overlay)
        # qp.setCompositionMode(qp.CompositionMode_Darken)
        qp.setPen(QPen(QBrush(lineColor), 4))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, QColor(0, 0, 0, alpha))
        grad.setColorAt(topEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1 - topEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1, QColor(0, 0, 0, alpha))
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 4, 4)
        grad = QLinearGradient(0, 16, 400, 16)
        grad.setColorAt(0, QColor(0, 0, 0, alpha))
        grad.setColorAt(sideEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1 - sideEdge, QColor(255, 255, 255, alpha * 0.5))
        grad.setColorAt(1, QColor(0, 0, 0, alpha))

        qp.setBrush(QBrush(grad))
        # qp.setBrush(QBrush(self.currentFillColour))

        qp.drawRoundedRect(self.rect(), 4, 4)
        '''
        qp.end()

    def windowFlags(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint | Qt.Tool)

    def move_UI(self):
        ''' Moves the UI to the widget position '''
        pos = QCursor.pos()
        xOffset = 10  # border?
        self.move(pos.x() - (self.width() * 0.5) + 88, pos.y() - (self.height() * 0.5))

    def arrangeUI(self):
        self.horizontalBar.move(self.barHorizontalOffset, 6)

        self.dragButton.setButtonToRestPosition()
        for btn in self.anchorButtons:
            btn.setButtonToRestPosition()
        self.update()

    def setSS(self):
        self.setStyleSheet("""
      QWidget{
          background-color: rgba(55, 250, 55, 0);
      }
        QLabel{
          background-color: rgba(55, 250, 55, 0);
      }
      QLayout{
          background: rgba(128, 55, 55, 0);
      }
      QFrame{
          border-style: None;
          border-color: rgba(55, 55, 55, 128);
          border-width: 5px;
          border-radius: 5px;
          background-color: rgba(55, 55, 55, 0);
      }
      """)

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()
        # print self.__mousePressPos, self.mapFromParent(self.__mousePressPos)
        super(sliderWidget, self).mousePressEvent(event)

    def enterEvent(self, event):
        return super(sliderWidget, self).enterEvent(event)

    def leaveEvent(self, event):
        return super(sliderWidget, self).enterEvent(event)

    def begin(self):
        """
        Turn auto key off to stop keyframe spamming updates killing performance
        :return:
        """
        self.tweenClass.begin()

    def updateAlpha(self, alpha):
        # print 'sliderWidget updateAlpha', self.tweenClass
        self.tweenClass.updateAlpha(alpha)

    def show(self):
        super(sliderWidget, self).show()
        self.setEnabled(True)
        self.setFocus()

    def close(self):
        cmds.scriptJob(kill=self.selectionChangedCallback)
        super(sliderWidget, self).close()

    def showUI(self):
        self.updateTweenClass()
        self.move_UI()
        self.show()
        self.arrangeUI()
        # self.updateTweenClass()

    def startDrag(self, button):
        print 'starting new drag on button!!', button
        self.updateTweenClass()

        self.tweenClass = self.currentTweenClassDict[button]()
        self.tweenClass.setAffectedObjects()
        self.tweenClass.cacheValues()
        self.tweenClass.get_modifier()
        print 'affectedObjects', self.tweenClass.affectedObjects
        self.currentDragButton = button
        self.isDragging = True

    def endDrag(self):
        self.isDragging = False
        self.currentDragButton = None
        self.tweenClass.apply()
        self.showAllAnchors()
        self.updateTweenClass()

    def updateTweenClass(self):
        """
        query the selection to decide what is the most appropriate tween class to use
        :return:
        """
        print 'updating tween class'
        selectedKeys = cmds.keyframe(query=True, selected=True)
        selectedObjects = cmds.ls(sl=True, type='transform')
        geState = getGraphEditorState()
        if not geState:
            self.affectingKeys = False
            self.currentTweenClassDict = self.objTweenClassDict
        else:
            if selectedKeys:
                self.affectingKeys = True
                self.currentTweenClassDict = self.keyTweenClassDict
            elif selectedObjects:
                self.affectingKeys = False
                self.currentTweenClassDict = self.objTweenClassDict
        self.tweenClass = self.currentTweenClassDict[Qt.LeftButton]()
        # self.label.setText(self.tweenClass.labelText)
        self.arrangeUI()
        self.tweenClass.setAffectedObjects()
        self.tweenClass.cacheValues()
        print self.tweenClass, self.tweenClass.labelText
        self.update()

    def get_modifier(self):
        print 'cmds.getModifiers()', cmds.getModifiers()
        self.keyboardModifier = {0: None, 1: 'shift', 4: 'ctrl'}[cmds.getModifiers()]

    def shiftPressed(self):
        print 'UI shift pressed'
        if self.isDragging:
            return
        # self.horizontalBar.setStyleSheet("QLabel {background-color: rgba(255, 128, 128, 128);}")
        self.currentFillColourTop = self.fillColourAltTop
        self.currentFillColourBottom = self.fillColourAltBottom
        self.update()
        # self.dragButton.setPixmap(self.dragButton.inactiveIcon)

    def shiftReleased(self):
        print 'UI shift released'
        if self.isDragging:
            return
        # self.horizontalBar.setStyleSheet("QLabel {background-color: rgba(128, 128, 128, 128);}")
        self.currentFillColourTop = self.fillColourBaseTop
        self.currentFillColourBottom = self.fillColourBaseBottom
        self.update()
        # self.dragButton.setPixmap(self.dragButton.activeIcon)

    def controlPressed(self):
        print 'UI control pressed'

    def controlReleased(self):
        print 'UI control released'


# TODO - stop using this
def getGraphEditorState():
    """
    use this to determine if we should act on selected keys based on graph editor visibility
    :return:
    """
    GraphEdWindow = None
    state = False
    if cmds.animCurveEditor('graphEditor1GraphEd', query=True, exists=True):
        graphEdParent = cmds.animCurveEditor('graphEditor1GraphEd', query=True, panel=True)
        if not cmds.panel(graphEdParent, query=True, exists=True):
            return False
        if cmds.panel(graphEdParent, query=True, exists=True):
            GraphEdWindow = cmds.panel(graphEdParent, query=True, control=True).split('|')[0]

    if GraphEdWindow:
        state = cmds.workspaceControl(GraphEdWindow, query=True, collapse=True)
        return not state
    return False
