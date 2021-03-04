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

    slideUI = None

    def __new__(cls):
        if slideTools.__instance is None:
            slideTools.__instance = object.__new__(cls)

        slideTools.__instance.val = cls.toolName
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
        except:
            pass

        self.slideUI = sliderWidget(self.funcs.getWidgetAtCursor(), tweemClass=self.pickInbetweenClass(), funcs=self.funcs)
        self.slideUI.showUI()

    def inbetweenSlideRelease(self):
        try:
            self.slideUI.close()
            self.slideUI.deleteLater()
        except:
            pass


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

    def get_modifier(self):
        self.keyboardModifier = {0: None, 1: 'shift', 4: 'ctrl'}[cmds.getModifiers()]

    def updateAlpha(self, alpha, disableAutoKey=True):
        """
        perform the update calculation here that affects the objects/keys
        :param alpha:
        :param disableAutoKey:
        :return:
        """
        self.get_modifier()

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
        #print 'start times', self.startkeyTimes
        #print 'end times', self.endKeyTimes
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
                    plug.setFloat(resultTranslate[index])
            if not self.keyboardModifier == 'ctrl':
                for index, plug in enumerate(rotatePlugs):
                    plug.setFloat(resultRotate[index])



class keyframeTween(tweenBase):
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
        for curve in self.affectedObjects:
            for index, indexVal in enumerate(self.selectedKeyIndexes[curve]):
                if self.alpha >= 0:
                    # lerp to next
                    targetValue = self.curveNextValues[curve][index]
                    outAlpha = alpha
                else:
                    # lerp to prev
                    targetValue = self.curvePreviousValues[curve][index]
                    outAlpha = alpha * -1

                lerpedValue = lerpFloat(targetValue, self.selectedKeyValues[curve][index], outAlpha)
                cmds.keyframe(curve, edit=True, valueChange=lerpedValue, index=((indexVal),))

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
                 inactiveIcon=inactiveIconFile
                 ):
        QLabel.__init__(self, parent)

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
            self.restX = xMin + margin
        elif self.percent >= 100:
            self.restX = xMax - margin - self.width()
        else:
            self.restX = ((xMax - xMin - self.width()) / (100 / self.percent)) + margin

        self.minButtonPos = self.xMin + margin
        self.maxButtonPos = self.xMax - self.width() + margin

        self.restY = 3 * margin
        self.restPoint = QPoint(self.restX, self.restY)
        self.move(self.restPoint)
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(1)
        shadow.setBlurRadius(3)
        self.setGraphicsEffect(shadow)

    def updateAlpha(self):
        """
        sends the alpha value back to the ui parent class
        :return:
        """
        range = (self.xMax - self.width()) - (self.xMin)
        pos = self.pos().x() - margin
        alpha = -1 * (1.0 - (pos / (range * 0.5)))
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
        if event.button() == Qt.LeftButton:
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
        if event.buttons() == Qt.LeftButton:
            if not self.draggable:
                if self.masterDragger:
                    # dragging one of those dot controls
                    self.setIconStateInactive()
                    self.uiParent.hideAllAnchors()
                    self.masterDragger.setPositionFromSlider(self.pos() + QPoint(self.halfWidth, 0))
            # adjust offset from clicked point to origin of widget
            else:
                self.updatePosition(event.globalPos())

        super(DragButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setIconStateBase()
        self.uiParent.sliderReleased()
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

        if ScreenVal <= self.mapToGlobal(QPoint(self.xMin, 0)).x(): return
        if ScreenVal >= self.mapToGlobal(QPoint(self.xMax, 0)).x(): return
        # if current mouse position out of slider range, diff = 0

        diff = globalPos - self.__mouseMovePos
        diff.setY(0)
        newPos = self.mapFromGlobal(currPos + diff)

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
        self.setHoverSS()
        self.setHoverTint()
        return super(DragButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setNonHoverSS()
        self.setNoTint()
        return super(DragButton, self).enterEvent(event)

    def setHoverTint(self):
        self.setTintEffect()
        self.effect.setColor(hoverTint)

    def setNoTint(self):
        self.setTintEffect()
        self.effect.setColor(noTint)

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
        self.setFixedSize(self.barWidth, 20)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel {background-color: rgba(128, 128, 128, 128);}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        self.uiParent.hideAllAnchors()
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        self.uiParent.dragButton.setPositionFromSlider(self.mapFromGlobal(self.__mousePressPos))
        super(sliderBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.uiParent.hideAllAnchors()
        if event.buttons() == Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        self.uiParent.dragButton.setPositionFromSlider(self.mapFromGlobal(self.__mousePressPos))

        super(sliderBar, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.uiParent.sliderReleased()
        super(sliderBar, self).mouseReleaseEvent(event)


class sliderWidget(QWidget):
    def __init__(self, parent, tweemClass=None,
                 funcs=None,
                 largeAnchors=[0, 50, 100.0],
                 smallAnchors=[12.5, 25.0, 37.5, 62.5, 75.0, 87.5]
                 ):
        QWidget.__init__(self, parent)
        self.funcs = funcs
        self.setFocus()
        self.lastEvent = None
        self.dragButton = None
        self.anchorButtons = list()
        self.largeAnchorPositions = list()
        self.smallAnchorPositions = list()
        self.tweenClass = None
        self.barWidth = 300
        self.largeAnchorPositions = largeAnchors
        self.smallAnchorPositions = smallAnchors
        self.setFixedSize(400, 32)
        self.mainLayout = QHBoxLayout(self)
        # self.setStyleSheet('QWidget{margin-left:-1px;}')
        self.mainLayout.setContentsMargins(margin, margin, margin, margin)
        self.mainLayout.setSpacing(0)
        horizontalBar = sliderBar(self, self.barWidth)
        self.dragButton = DragButton("BD",
                                     xMax=horizontalBar.width(),
                                     parent=horizontalBar,
                                     uiParent=self)

        self.setFocusPolicy(Qt.StrongFocus)

        self.dragButton.setFocusPolicy(Qt.StrongFocus)

        for p in self.largeAnchorPositions:
            anchorBtn = DragButton("BD",
                                   xMax=horizontalBar.width(),
                                   parent=horizontalBar,
                                   uiParent=self,
                                   draggable=False,
                                   percent=p,
                                   masterDragger=self.dragButton,
                                   baseIcon=barSmallIconFile,
                                   hoverIcon=barSmallIconFile,
                                   activeIcon=dotSmallIconFile,
                                   inactiveIcon=inactiveIconFile
                                   )
            self.anchorButtons.append(anchorBtn)
        for p in self.smallAnchorPositions:
            anchorBtn = DragButton("BD",
                                   xMax=horizontalBar.width(),
                                   parent=horizontalBar,
                                   uiParent=self,
                                   draggable=False,
                                   percent=p,
                                   masterDragger=self.dragButton,
                                   baseIcon=dotSmallIconFile,
                                   hoverIcon=dotSmallIconFile,
                                   activeIcon=dotSmallIconFile,
                                   inactiveIcon=inactiveIconFile
                                   )
            self.anchorButtons.append(anchorBtn)
        self.mainLayout.addWidget(horizontalBar)
        for btn in self.anchorButtons:
            self.mainLayout.addWidget(btn)
        self.mainLayout.addWidget(self.dragButton)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setSS()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        self.setGraphicsEffect(shadow)

        if tweemClass is None:
            self.tweenClass = tweenBase()
        else:
            self.tweenClass = tweemClass

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
        fillColor = QColor(255, 165, 0, 180)
        lineColor = QColor(0, 0, 0, 0)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(QBrush(lineColor), 8))
        qp.setBrush(QBrush(fillColor))
        qp.drawRoundedRect(self.rect(), 8, 8)

        qp.end()

    def windowFlags(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint | Qt.Tool)

    def move_UI(self):
        ''' Moves the UI to the widget position '''
        pos = QCursor.pos()
        xOffset = 10  # border?
        self.move(pos.x() - (self.width() * 0.5), pos.y() - (self.height() * 0.5))

    def arrangeUI(self):
        self.dragButton.setButtonToRestPosition()
        for btn in self.anchorButtons:
            btn.setButtonToRestPosition()

    def setSS(self):
        self.setStyleSheet("""
       QWidget{
           background-color: rgba(55, 250, 55, 128);
       }
       QLayout{
           background: rgba(128, 55, 55, 255);
       }
       QFrame{
           border-style: None;
           border-color: rgba(55, 55, 55, 128);
           border-width: 5px;
           border-radius: 5px;
           background-color: rgba(55, 55, 55, 128);
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
        self.tweenClass.updateAlpha(alpha)

    def show(self):
        super(sliderWidget, self).show()
        self.setEnabled(True)
        self.setFocus()

    def close(self):
        super(sliderWidget, self).close()

    def showUI(self):
        self.move_UI()
        self.show()
        self.arrangeUI()
        self.updateTweenClass()

    def sliderReleased(self):
        self.tweenClass.apply()
        self.showAllAnchors()
        self.updateTweenClass()
        self.arrangeUI()

    def updateTweenClass(self):
        self.tweenClass.setAffectedObjects()
        self.tweenClass.cacheValues()

    def get_modifier(self):
        self.keyboardModifier = {0: None, 1: 'shift', 4: 'ctrl'}[cmds.getModifiers()]




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

