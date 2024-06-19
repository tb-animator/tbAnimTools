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
import maya.mel as mel
from Abstract import hotKeyAbstractFactory
import maya
import maya.OpenMaya as om

maya.utils.loadStringResourcesForModule(__name__)
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
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui
from Abstract import *
from functools import partial


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('timeline'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='timeDrag',
                                     annotation='simple time drag, no mouse click needed',
                                     category=self.category,
                                     help='TODO',
                                     command=['TimeDragger.timeDrag()']))
        self.addCommand(self.tb_hkey(name='timeDragSmooth',
                                     annotation='simple time drag, no mouse click needed',
                                     category=self.category,
                                     help='TODO',
                                     command=['TimeDragger.timeDragSmooth()']))
        self.addCommand(self.tb_hkey(name='smooth_drag_timeline_on',
                                     annotation='timeslider tool with no frame snapping',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.smooth_drag_timeline_on'],
                                     command=['TimeDragger.drag(True)']))
        self.addCommand(self.tb_hkey(name='smooth_drag_timeline_off',
                                     annotation='set to same hotkey as ON, but tick release',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.smooth_drag_timeline_off'],
                                     command=['TimeDragger.drag(False)']))
        self.addCommand(self.tb_hkey(name='step_drag_timeline_on',
                                     annotation='timeslider tool with no frame snapping',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.step_drag_timeline_on'],
                                     command=['TimeDragger.stepDrag()']))
        self.addCommand(self.tb_hkey(name='step_drag_timeline_off',
                                     annotation='set to same hotkey as ON, but tick release',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.step_drag_timeline_off'],
                                     command=['TimeDragger.stepDrag(state=False)']))

        return self.commandList

    def assignHotkeys(self):
        return


class TimeDragger(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'TimeDragger'
    hotkeyClass = None
    funcs = None

    messagePos = "tb_timedrag_msg_pos"
    messageVar = "tb_timedrag_msg"
    optionVar = "tb_timedrag"
    modes = ['toggleBackground']
    step_modes = ['odd frames only']
    stepFrameCount_var = "tb_timedrag_step_frame"
    step_optionVar = "tb_step_odd"
    step_unconstrained = "tb_step_unconstrained"
    MessagePos = None
    showMessage = None
    toggle_background = None

    background_state = cmds.displayPref(query=True, displayGradient=True)
    previous_tool = None
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    failsafe = None
    step_ctx = None
    start_time = pm.getCurrentTime()
    dragPosition = []
    pressPosition = []
    step = pm.optionVar.get("tb_step_size", 2)
    even_only = pm.optionVar.get("tb_step_even", True)
    # for maya 2016 dag evaluation madness
    evaluate_mode = ""
    initialPos = None

    def __new__(cls):
        if TimeDragger.__instance is None:
            TimeDragger.__instance = object.__new__(cls)

        TimeDragger.__instance.val = cls.toolName
        return TimeDragger.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.even_only = pm.optionVar.get(self.step_optionVar, True)
        self.update_options()
        self.previous_tool = self.get_previous_ctx()
        self.step_ctx = pm.draggerContext(name='step_ctx',
                                          pressCommand=self.step_drag_press,
                                          dragCommand=self.step_drag_dragged,
                                          # releaseCommand=self.step_drag_released,
                                          cursor='hand')

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(TimeDragger, self).optionUI()

        snapOrderHeader = SubHeader('Stepped Drag')
        stepDragInfo = infoLabel([maya.stringTable['y_tb_timeDragger.stepDragInfo']])

        StepFramesWidget = intFieldWidget(optionVar=self.stepFrameCount_var,
                                          defaultValue=1,
                                          label='Step every x frames',
                                          minimum=1, maximum=100, step=1)
        EvenOnlyOptionWidget = optionVarBoolWidget('Step on even frames only',
                                                   self.step_optionVar)
        unconstrainedOptionWidget = optionVarBoolWidget('Step ouside of playback range',
                                                        self.step_unconstrained)

        self.layout.addWidget(snapOrderHeader)
        self.layout.addWidget(stepDragInfo)
        self.layout.addWidget(EvenOnlyOptionWidget)
        self.layout.addWidget(unconstrainedOptionWidget)
        self.layout.addWidget(StepFramesWidget)

        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    # in case you change the options mid session
    def update_options(self):
        self.MessagePos = pm.optionVar.get(self.messagePos, 'topLeft')
        self.showMessage = pm.optionVar.get(self.messageVar, 0)
        self.toggle_background = pm.optionVar.get(self.optionVar, 0)

    def get_previous_ctx(self):
        if pm.currentCtx() == "TimeDragger" or pm.currentCtx() == "step_ctx":
            previous_tool = 'selectSuperContext'
        else:
            previous_tool = pm.currentCtx()
        return previous_tool

    def drag(self, state):
        self.update_options()
        # print (self.get_previous_ctx())
        # print ("state", state)
        cmds.timeControl(self.aPlayBackSliderPython, edit=True, snap=not state)
        if state:
            mel.eval('storeLastAction("restoreLastContext ' + self.get_previous_ctx() + '")')
            if self.toggle_background:
                cmds.displayPref(displayGradient=False)
            if self.showMessage:
                msg = 'on'
                self.funcs.infoMessage(prefix='smooth drag',
                                       message=' : %s' % msg,
                                       position=self.MessagePos
                                       )
            cmds.setToolTo('TimeDragger')
        else:
            if self.showMessage:
                msg = 'off'
                self.funcs.infoMessage(prefix='smooth drag',
                                       message=' : %s' % msg,
                                       position=self.MessagePos
                                       )
            pm.setCurrentTime(int(pm.getCurrentTime()))
            cmds.displayPref(displayGradient=self.background_state)
            mel.eval('invokeLastAction')

    def warn(self):
        self.failsafe = None
        msg = "you pressed some weird combination of alt or maybe the windows key"
        cmds.warning(msg)
        self.funcs.errorMessage(prefix='Warning',
                                message=' : %s' % msg,
                                position='botRight'
                                )

    def stepDrag(self, state=True):
        if state:
            try:
                # disable the parallel processing (crashes a lot in 2016)
                self.evaluate_mode = cmds.evaluationManager(mode='off')
            except:
                pass
            self.step = pm.optionVar.get(self.stepFrameCount_var, 1)
            self.even_only = pm.optionVar.get(self.step_optionVar, True)
            # print ("step even", self.even_only)
            cmds.setToolTo(self.step_ctx)
        else:
            mel.eval('invokeLastAction')
            # stepped scrub bypasses evaluation manager as hardly anything in 2016 is thread safe
            try:
                if cmds.evaluationManager(query=True, enabled=True):
                    cmds.evaluationManager(mode=str(self.evaluate_mode))
            except:
                pass

    # Procedure called on press
    def step_drag_press(self):
        self.pressPosition = pm.draggerContext(self.step_ctx, query=True, anchorPoint=True)
        self.start_time = pm.getCurrentTime()

    # Procedure called on drag
    def step_drag_dragged(self):
        self.dragPosition = pm.draggerContext(self.step_ctx, query=True, dragPoint=True)
        distance = self.dragPosition[0] - self.pressPosition[0]
        step_destination = self.start_time + int(distance * 0.05) * self.step
        if self.even_only:
            # snap to odd frames only
            step_destination = int(step_destination / 2) * 2 + 1

        pm.setCurrentTime(max(self.funcs.getTimelineMin(), min(step_destination, self.funcs.getTimelineMax())))

    def step_drag_released(self):
        mel.eval('invokeLastAction')

    # this should reset the drag state when the tool is changed, in case you press alt or the windows key when dragging
    def failsafe_scriptjob(self):
        return pm.scriptJob(runOnce=True, event=['ToolChanged', partial(self.drag, False)])

    def info(self):
        pass
        '''
        print ("toggle background :", self.toggle_background)
        print ("background state  :", self.background_state)
        print ("previous tool     :", self.previous_tool)
        '''

    def setInitialPos(self, value):
        self.initialPos = value
        self.start_time = cmds.currentTime(query=True)

    def timeDragMouseMovedQuery(self, startPos, currentPos):
        distance = currentPos - self.initialPos
        step_destination = self.start_time + int(distance * 0.05) * 1  # self.step
        return step_destination

    def timeDragMouseMoved(self, startPos, currentPos):
        distance = currentPos - self.initialPos
        step_destination = self.start_time + int(distance * 0.05) * 1  # self.step
        if self.even_only:
            # snap to odd frames only
            step_destination = int(step_destination / 2) * 2 + 1
        if pm.optionVar.get(self.step_unconstrained, False):
            pm.setCurrentTime(step_destination)
        else:
            pm.setCurrentTime(max(self.funcs.getTimelineMin(), min(step_destination, self.funcs.getTimelineMax())))

    def timeDragSmoothMouseMoved(self, startPos, currentPos):
        distance = currentPos - self.initialPos
        step_destination = self.start_time + (distance * 0.05)
        if pm.optionVar.get(self.step_unconstrained, False):
            # pm.setCurrentTime(step_destination)
            om.MAnimControl.setCurrentTime(step_destination)
        else:
            om.MAnimControl.setCurrentTime(
                max(self.funcs.getTimelineMin(), min(step_destination, self.funcs.getTimelineMax())))

    def timeDragMouseWheel(self, value):
        pm.setCurrentTime(pm.currentTime(query=True) + value)
        self.initialPos = QCursor.pos().x()
        self.start_time = pm.getCurrentTime()

    def timeDrag(self):
        self.timeDragWidget = TimeDragDialog()
        self.initialPos = QCursor.pos().x()
        self.start_time = pm.getCurrentTime()
        self.timeDragWidget.mouseMovedSignal.connect(self.timeDragMouseMoved)
        self.timeDragWidget.mouseWheelSignal.connect(self.timeDragMouseWheel)
        self.timeDragWidget.updateInitialSignal.connect(self.setInitialPos)
        self.timeDragWidget.show()

    def timeDragSmooth(self):
        self.timeDragWidget = TimeDragDialog()
        self.initialPos = QCursor.pos().x()
        self.start_time = pm.getCurrentTime()
        cmds.timeControl(self.aPlayBackSliderPython, edit=True, snap=False)
        self.timeDragWidget.mouseMovedSignal.connect(self.timeDragSmoothMouseMoved)
        self.timeDragWidget.mouseWheelSignal.connect(self.timeDragMouseWheel)
        self.timeDragWidget.updateInitialSignal.connect(self.setInitialPos)
        self.timeDragWidget.closedSignal.connect(self.resetSmoothSlider)
        self.timeDragWidget.show()

    def resetSmoothSlider(self):
        cmds.timeControl(self.aPlayBackSliderPython, edit=True, snap=True)
        cmds.currentTime(int(cmds.currentTime(query=True)))

    def select_time_slider_range_start(self, start,
                                       sliderWidget,
                                       slider_height,
                                       step):
        app = QApplication.instance()

        a_pos = QPoint((step * start), slider_height / 2.0)
        # Trigger some mouse events on the Time Control
        # Somehow we need to have some move events around
        # it so the UI correctly understands it stopped
        # clicking, etc.
        # sliderWidget.blockSignals(True)
        # cmds.refresh(su=True)
        event = QMouseEvent(QEvent.MouseMove,
                            a_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.NoModifier)
        app.sendEvent(sliderWidget, event)

        event = QMouseEvent(QEvent.MouseButtonPress,
                            a_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.ShiftModifier)
        app.sendEvent(sliderWidget, event)
        event = QMouseEvent(QEvent.MouseButtonRelease,
                            a_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.ShiftModifier)
        app.sendEvent(sliderWidget, event)
        app.processEvents()
        # cmds.refresh(su=False)

    def update_selected_time_slider_range(self, start, end,
                                          sliderWidget,
                                          slider_height,
                                          step,
                                          cls):
        cls.isUpdating = True
        try:
            app = QApplication.instance()
            print('update_', start, end)
            a_pos = QPoint((step * start), slider_height / 2.0)
            b_pos = QPoint((step * end) - step, slider_height / 2.0)
            # Trigger some mouse events on the Time Control
            # Somehow we need to have some move events around
            # it so the UI correctly understands it stopped
            # clicking, etc.
            # sliderWidget.blockSignals(True)
            # cmds.refresh(su=True)

            event = QMouseEvent(QEvent.MouseMove,
                                a_pos,
                                Qt.MouseButton.MiddleButton,
                                Qt.MouseButton.MiddleButton,
                                Qt.NoModifier)
            app.sendEvent(sliderWidget, event)

            event = QMouseEvent(QEvent.MouseButtonPress,
                                a_pos,
                                Qt.MouseButton.MiddleButton,
                                Qt.MouseButton.MiddleButton,
                                Qt.ShiftModifier)
            app.sendEvent(sliderWidget, event)

            event = QMouseEvent(QEvent.MouseMove,
                                b_pos,
                                Qt.MouseButton.MiddleButton,
                                Qt.MouseButton.MiddleButton,
                                Qt.ShiftModifier)
            app.sendEvent(sliderWidget, event)

            event = QMouseEvent(QEvent.MouseButtonRelease,
                                b_pos,
                                Qt.MouseButton.MiddleButton,
                                Qt.MouseButton.MiddleButton,
                                Qt.ShiftModifier)
            app.sendEvent(sliderWidget, event)

            app.processEvents()
        finally:
            cls.isUpdating = False
        # sliderWidget.blockSignals(False)

    def select_time_slider_range(self, start, end,
                                 sliderWidget,
                                 slider_height,
                                 step):
        app = QApplication.instance()

        a_pos = QPoint((step * start), slider_height / 2.0)
        b_pos = QPoint((step * end) - step, slider_height / 2.0)
        # Trigger some mouse events on the Time Control
        # Somehow we need to have some move events around
        # it so the UI correctly understands it stopped
        # clicking, etc.
        # sliderWidget.blockSignals(True)
        # cmds.refresh(su=True)

        event = QMouseEvent(QEvent.MouseMove,
                            a_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.NoModifier)
        app.sendEvent(sliderWidget, event)

        event = QMouseEvent(QEvent.MouseButtonPress,
                            a_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.ShiftModifier)
        app.sendEvent(sliderWidget, event)

        event = QMouseEvent(QEvent.MouseMove,
                            b_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.ShiftModifier)
        app.sendEvent(sliderWidget, event)

        event = QMouseEvent(QEvent.MouseButtonRelease,
                            b_pos,
                            Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.MiddleButton,
                            Qt.ShiftModifier)
        app.sendEvent(sliderWidget, event)

        event = QMouseEvent(QEvent.MouseMove,
                            b_pos,
                            Qt.MouseButton.LeftButton,
                            Qt.MouseButton.LeftButton,
                            Qt.NoModifier)
        app.sendEvent(sliderWidget, event)
        app.processEvents()
        # cmds.refresh(su=False)
        # sliderWidget.blockSignals(False)


class TimeDragDialog(QDialog):
    mouseMovedSignal = Signal(float, float)
    mouseWheelSignal = Signal(float)
    openedSignal = Signal(float)
    closedSignal = Signal()
    updateInitialSignal = Signal(float)
    bufferMin = 100
    bufferMax = 200

    shiftKeyDown = False
    shiftDownTime = None
    isUpdating = False

    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget), parentMenu=None, menuDict=dict(),
                 *args, **kwargs):
        super(TimeDragDialog, self).__init__(parent=parent)
        self.app = QApplication.instance()
        self.keyPressHandler = None

        self.minTime = None
        self.maxTime = None
        self.previousTime = None
        self.lastUpdateTime = None
        self.delta = None
        self.menuDict = menuDict
        self.parentMenu = parentMenu
        self.invokedKey = None
        self.returnButton = None

        self.recentlyOpened = False
        self.activeButton = None
        self.centralRadius = 16
        self.scalar = math.cos(math.radians(45)) * self.centralRadius

        self.setMouseTracking(True)
        self.stylesheet = getqss.getStyleSheet()
        self.setStyleSheet(self.stylesheet)
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # screen = QDesktopWidget().availableGeometry()

        self.cursorPos = QCursor.pos()
        self.currentCursorPos = QCursor.pos()

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        if self.parentMenu:
            self.invokedKey = self.parentMenu.invokedKey
            self.returnButton = ReturnButton(label='', parent=self, cls=self)
            # print ('parent pos', self.parentMenu.cursorPos)
            distance = self.distance(self.cursorPos, self.parentMenu.cursorPos)
            delta = self.parentMenu.cursorPos - self.cursorPos
            delta = om2.MVector(delta.x(), delta.y(), 0).normal()
            # print ('returnButton', delta)
            self.returnButton.move(delta[0] * 200 + self.cursorPos.x(), delta[1] * 200 + self.cursorPos.y())
        else:
            self.keyPressHandler = markingMenuKeypressHandler(UI=self)
            self.app.installEventFilter(self.keyPressHandler)

    def show(self):
        """Sow and initialize"""
        widgetStr = mel.eval('$gPlayBackSlider=$gPlayBackSlider')
        ptr = omui.MQtUtil.findControl(widgetStr)
        self.slider = wrapInstance(int(ptr), QWidget)
        min_time = cmds.playbackOptions(query=True, minTime=True)
        max_time = cmds.playbackOptions(query=True, maxTime=True)
        self.slider_width = self.slider.size().width()
        self.slider_height = self.slider.size().height()
        self.buffer = 6
        self.slider_step = float(self.slider_width - self.buffer) / (max_time - min_time + 1)

        self.cursorPos = QCursor.pos()
        self.currentCursorPos = QCursor.pos()
        screens = QApplication.screens()
        '''
        top = 0
        left = 0
        bottom = 0
        right = 0
        for s in screens:
            geo = s.availableGeometry()
            top = min(top, geo.topLeft().y())
            left = min(left, geo.topLeft().x())
            right = max(right, geo.bottomRight().x())
            bottom = max(bottom, geo.bottomRight().y())
            if s.availableGeometry().contains(QCursor.pos()):
                screen = s

        self.screenGeo = screen.availableGeometry()
        self.move(top, left)
        self.setFixedSize(right-left, bottom-top)
        '''
        for s in screens:
            if s.availableGeometry().contains(QCursor.pos()):
                screen = s

        self.screenGeo = screen.availableGeometry()
        self.move(self.screenGeo.left(), self.screenGeo.top())
        self.setFixedSize(self.screenGeo.width(), self.screenGeo.height())

        if not self.parentMenu:
            self.recentlyOpened = True

        super(TimeDragDialog, self).show()
        self.setFocus()
        self.openedSignal.emit(self.cursorPos.x())

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.shiftKeyPressed()

    def hide(self):
        super(TimeDragDialog, self).hide()

    def close(self):
        self.closedSignal.emit()
        if self.keyPressHandler:
            self.app.removeEventFilter(self.keyPressHandler)
        super(TimeDragDialog, self).close()

    def moveToCursor(self):
        pos = QCursor.pos()
        xOffset = 10  # border?
        self.cursorPos = QPoint(self.cursorPos.x() - self.screenGeo.left(), self.cursorPos.y() - self.screenGeo.top())
        self.move(self.screenGeo.left(), self.screenGeo.top())

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        lineColor = QColor(68, 68, 68, 128)
        linePenColor = QColor(255, 160, 47, 255)
        blank = QColor(124, 124, 124, 1)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 1)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(lineColor))
        qp.setCompositionMode(qp.CompositionMode_Clear)

        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setBrush(QBrush(blank))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        qp.setBrush(QBrush(lineColor))
        qp.end()

    def mouseMoveEvent(self, event):
        if self.isUpdating:
            return
        currentTime = cmds.currentTime(query=True)
        if not self.lastUpdateTime: self.lastUpdateTime = cmds.currentTime(query=True)
        if QCursor.pos().x() < self.screenGeo.left() + self.bufferMin:
            QCursor.setPos(self.screenGeo.left() + self.width() - self.bufferMax, QCursor.pos().y())
            self.updateInitialSignal.emit(QCursor.pos().x())

        if QCursor.pos().x() > self.screenGeo.left() + self.width() - self.bufferMin:
            QCursor.setPos(self.screenGeo.left() + self.bufferMax, QCursor.pos().y())
            self.updateInitialSignal.emit(QCursor.pos().x())

        self.currentCursorPos = QCursor.pos()

        updateTime = cmds.currentTime(query=True)
        # print (currentTime, updateTime)
        delta = updateTime - currentTime

        if self.lastUpdateTime:
            self.delta = currentTime - self.lastUpdateTime
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.shiftKeyPressed()
        resultTime = TimeDragger().timeDragMouseMovedQuery(self.cursorPos.x(), QCursor.pos().x())
        if self.shiftKeyDown:
            delta = resultTime - self.lastUpdateTime
            # print('l', self.lastUpdateTime, 'r', resultTime)
            # print ('delta', delta)

            if abs(int(delta)) > 0:
                print('move', delta, currentTime, updateTime)

                TimeDragger().update_selected_time_slider_range(self.shiftDownTime,
                                                                resultTime,
                                                                self.slider,
                                                                self.slider_height,
                                                                self.slider_step,
                                                                self)
                cmds.currentTime(resultTime)
        else:
            self.mouseMovedSignal.emit(self.cursorPos.x(), QCursor.pos().x())

        # TODO - gotta do an update version, which drags from the last updated position

        self.previousTime = cmds.currentTime(query=True)
        self.lastUpdateTime = float(resultTime)

    def mousePressEvent(self, event):
        # print ('mousePressEvent', event)
        event.accept()

    # def tabletEvent(self, e):
    #     print(e.pressure())

    def keyPressEvent(self, event):

        if event.type() == event.KeyPress:
            if self.recentlyOpened:
                if event.key() is not None and event.key() != Qt.Key_Shift:
                    self.invokedKey = event.key()
                    self.recentlyOpened = False

        if not self.invokedKey or self.invokedKey == event.key():
            return
        super(TimeDragDialog, self).keyPressEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shiftKeyPressed()

    def shiftKeyPressed(self):
        if not self.shiftKeyDown:
            self.shiftKeyDown = True
            self.shiftDownTime = cmds.currentTime(query=True)
            self.minTime = cmds.currentTime(query=True)
            self.maxTime = cmds.currentTime(query=True)
            TimeDragger().select_time_slider_range_start(self.minTime,
                                                         self.slider,
                                                         self.slider_height,
                                                         self.slider_step)
    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() == Qt.Key_Shift:
            if self.shiftKeyDown:
                self.shiftKeyDown = False
                self.minTime = None
                self.maxTime = None
                self.previousTime = None
                print('key released')
                return
            # self.close()
        elif not self.invokedKey or self.invokedKey == event.key():
            self.close()

    def wheelEvent(self, event):
        if event.delta() > 0:
            value = -1
        else:
            value = 1
        self.mouseWheelSignal.emit(value)


'''
import tb_functions as tbf
reload(tbf)
funcs = tbf.functions()
import tb_timeDragger as drg
reload(drg)
acls = drg.TimeDragger()
acls.funcs = tbf.functions()
acls.allTools = tbtoolCLS
tbtoolCLS = ClassFinder()
tbtoolCLS.tools[acls.toolName] = acls
'''
