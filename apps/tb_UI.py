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
import math
import maya
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaUI as omUI
import maya.api.OpenMaya as om2
import maya.api.OpenMayaUI as omui2
import pymel.core as pm
from functools import partial
import subprocess

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
import getStyleSheet as getqss
import os
from colorsys import rgb_to_hls, hls_to_rgb

scriptLocation = os.path.dirname(os.path.realpath(__file__))
IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Icons'))
helpPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Help'))

baseIconFile = 'checkBox.png'


def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def darken_color(colour, factor=0.1):
    return adjust_color_lightness(colour[0], colour[1], colour[2], 1 - factor)

def hex_to_rgb(hex):
    return [float((hex[x:x + 2])) for x in [1, 3, 5]]

def rgb_to_hex(colour=[0.5, 0.5,0.5]):
    return "#%02x%02x%02x" % (int(colour[0]), int(colour[1]), int(colour[2]))

def getColourBasedOnRGB(inputColour, lightColour, darkColour):
    isLight = ((inputColour[0] * 0.299) + (inputColour[1] * 0.587) + (inputColour[2] * 0.114)) > 186
    if isLight:
        return darkColour, False
    return lightColour, True

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent=parent)
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Something happened, is that OK?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class BaseDialog(QDialog):
    widgetClosed = Signal()
    oldPos = None

    def __init__(self, parent=None, title='', text='',
                 lockState=False, showLockButton=False, showCloseButton=True, showInfo=True,
                 *args, **kwargs):
        super(BaseDialog, self).__init__(parent=parent)
        self.stylesheet = getqss.getStyleSheet()
        self.setStyleSheet(self.stylesheet)
        self.lockState = lockState
        self.showLockButton = showLockButton
        self.showCloseButton = showCloseButton
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setFixedSize(400, 120)
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.layout = QVBoxLayout()
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.pinButton = LockButton('', None, lockState=self.lockState)
        self.pinButton.lockSignal.connect(self.togglePinState)
        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)
        self.titleText = QLabel(title)
        self.titleText.setFont(QFont('Lucida Console', 12))
        self.titleText.setStyleSheet("font-weight: lighter; font-size: 12px;")
        self.titleText.setStyleSheet("background-color: rgba(255, 0, 0, 0);")
        self.titleText.setStyleSheet("QLabel {"
                                     "border-width: 0;"
                                     "border-radius: 4;"
                                     "border-style: solid;"
                                     "border-color: #222222;"
                                     "font-weight: bold; font-size: 12px;}"
                                     )

        self.titleText.setAlignment(Qt.AlignCenter)
        self.infoText = QLabel(text)
        if not showInfo: self.infoText.hide()

        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleText, alignment=Qt.AlignCenter)
        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.pinButton, alignment=Qt.AlignRight)
        self.titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

        self.mainLayout.addLayout(self.titleLayout)
        self.infoText.setStyleSheet(self.stylesheet)
        self.layout.addWidget(self.infoText)

        self.mainLayout.addLayout(self.layout)
        self.setLayout(self.mainLayout)

        self.pinButton.setVisible(self.showLockButton)
        self.closeButton.setVisible(self.showCloseButton)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.controlKeyPressed = False
        return False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Control:
            self.controlKeyPressed = True
        return super(BaseDialog, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.lockState and not modifiers == Qt.ControlModifier:
            return
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.lockState and not modifiers == Qt.ControlModifier:
            return
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            opacity = self.windowOpacity()
            opacity += event.delta() * 0.001
            opacity = min(max(opacity, 0.2), 1)
            self.setWindowOpacity(opacity)
        # cmds.warning(self.x(), event.delta() / 120.0 * 25)
        # self.setValue(self.value() + event.delta() / 120.0 * 25)
        # super(PySlider, self).wheelEvent(event)
        # self.wheelSignal.emit(self.value())

    def togglePinState(self, pinState):
        self.lockState = pinState
        self.closeButton.setVisible(True)

    def close(self):
        self.widgetClosed.emit()
        super(BaseDialog, self).close()


class markingMenu_filter(QObject):
    '''A simple event filter to catch MouseMove events'''

    def eventFilter(self, obj, event):
        return


class markingMenuKeypressHandler(QObject):
    def __init__(self, UI=None):
        super(markingMenuKeypressHandler, self).__init__()
        self.UI = UI

    def eventFilter(self, target, event):
        if event.type() == event.KeyRelease:
            if event.isAutoRepeat():
                return True
            self.UI.keyReleaseEvent(event)
            return False
        elif event.type() == event.KeyPress:
            self.UI.keyPressEvent(event)
            return False
        return False


class ViewportDialog(QDialog):
    closeSignal = Signal()
    keyReleasedSignal = Signal()

    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget), parentMenu=None, menuDict=dict(),
                 *args, **kwargs):
        super(ViewportDialog, self).__init__(parent=parent)
        self.app = QApplication.instance()
        self.keyPressHandler = None
        self.menuDict = menuDict
        self.parentMenu = parentMenu
        self.invokedKey = None
        self.returnButton = None

        self.hasExecutedCommand = False

        self.recentlyOpened = False
        self.activeButton = None
        self.centralRadius = 16
        self.scalar = math.cos(math.radians(45)) * self.centralRadius
        self.allButtons = list()
        self.widgets = {'NE': list(),
                        'NW': list(),
                        'SE': list(),
                        'SW': list(),
                        'radial': list()
                        }
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
            self.returnButton.hoverSignal.connect(self.returnButtonHovered)
            # print ('parent pos', self.parentMenu.cursorPos)
            distance = self.distance(self.cursorPos, self.parentMenu.cursorPos)
            delta = self.parentMenu.cursorPos - self.cursorPos
            delta = om2.MVector(delta.x(), delta.y(), 0).normal()
            # print ('returnButton', delta)
            self.returnButton.move(delta[0] * 200 + self.cursorPos.x(), delta[1] * 200 + self.cursorPos.y())
        else:
            self.keyPressHandler = markingMenuKeypressHandler(UI=self)
            self.app.installEventFilter(self.keyPressHandler)
        self.tooltipEnabled = True

    def returnButtonHovered(self):
        print ('returnButtonHovered')

    def addAllButtons(self):
        for key, items in self.menuDict.items():
            for item in items:
                self.addButton(quad=key,
                               button=item)

    def addButton(self, quad='NE', button=QWidget):
        if not self.widgets[quad]:
            existingPos = self.cursorPos + {'NE': QPoint(0, -self.scalar),
                                            'NW': QPoint(0, -self.scalar),
                                            'SE': QPoint(0, self.scalar),
                                            'SW': QPoint(0, self.scalar),
                                            }[quad]
            existingSize = QSize(0, 0)
        else:
            existingButton = self.widgets[quad][-1]
            existingPos = existingButton.pos()
            existingSize = existingButton.size()

        offsetX = {'NE': self.cursorPos.x() + self.scalar,
                   'NW': self.cursorPos.x() - button.width() - self.scalar,
                   'SE': self.cursorPos.x() + self.scalar,
                   'SW': self.cursorPos.x() - button.width() - self.scalar,
                   }
        offsetY = {'NE': existingPos.y() - button.height(),
                   'NW': existingPos.y() - button.height(),
                   'SE': existingPos.y() + existingSize.height(),
                   'SW': existingPos.y() + existingSize.height(),
                   }
        # print (quad, offsetX[quad], offsetY[quad])
        # print ('existingSize', existingSize.height())
        button.move(offsetX[quad], offsetY[quad])

        if isinstance(button, ToolboxButton):
            self.widgets[quad].append(button)
            button.absPos = button.pos()
            self.allButtons.append(button)
            button.hoverSignal.connect(self.buttonHovered)
            button.commandExecutedSignal.connect(self.commandExecuted)
            self.closeSignal.connect(button.hidePopup)
        elif isinstance(button, ToolboDivider):
            self.widgets[quad].append(button)
        elif isinstance(button, ToolboxDoubleButton):
            self.widgets[quad].append(button)
            for b in button.buttons:
                b.hoverSignal.connect(self.buttonHovered)
                b.commandExecutedSignal.connect(self.commandExecuted)
                self.closeSignal.connect(b.hidePopup)
                b.absPos = button.pos()  # + b.parent().pos()
                self.allButtons.append(b)

    @Slot()
    def commandExecuted(self):
        self.hasExecutedCommand = True
        for b in self.allButtons:
            b.disableExecuteOnHover()

    def enableLayer(self):
        # print ('enableLayer')
        self.tooltipEnabled = True

    def disableLayer(self):
        # print ('disableLayer')
        self.tooltipEnabled = False

    def moveAll(self):
        if self.returnButton:
            return
        cursorPos = QCursor.pos()  # or event.getCursor()

        offset = self.mapToGlobal(self.cursorPos) - cursorPos
        for c in self.children():
            c.move(c.pos().x() - offset.x(), c.pos().y() - offset.y())
            c.absPos = c.pos()
        self.cursorPos = QCursor.pos()

    def buttonHovered(self, widget):
        for w in self.allButtons:
            if w is not widget:
                w.setNonHoverSS()
        self.activeButton = widget
        self.update()
        # print ('buttonHovered', widget)

    def show(self):
        t = cmds.timerX()
        self.cursorPos = QCursor.pos()
        self.currentCursorPos = QCursor.pos()
        screens = QApplication.screens()
        for s in screens:
            if s.availableGeometry().contains(QCursor.pos()):
                screen = s

        self.screenGeo = screen.availableGeometry()
        self.setFixedSize(self.screenGeo.width(), self.screenGeo.height())
        if not self.parentMenu:
            self.recentlyOpened = True
        self.moveToCursor()
        # self.grabKeyboard()
        self.setFocus()
        self.addAllButtons()
        self.repaint()
        super(ViewportDialog, self).show()
        # print (cmds.timerX() - t)

    def hide(self):
        # print ('being hidden', self)
        super(ViewportDialog, self).hide()

    def closeMenu(self):
        if self.parentMenu:
            self.parentMenu.closeMenu()
        self.hide()
        self.releaseKeyboard()

    def close(self):
        if self.keyPressHandler:
            self.app.removeEventFilter(self.keyPressHandler)
        try:
            super(ViewportDialog, self).close()
        except:
            pass
        try:
            self.closeSignal.emit()
        except:
            pass

    def hideCurrentLayer(self):
        self.close()
        self.parentMenu.setEnabled(True)
        event = QMouseEvent(QEvent.MouseButtonPress,
                            self.parentMenu.cursorPos,
                            Qt.MouseButton.LeftButton,
                            Qt.MouseButton.LeftButton,
                            Qt.NoModifier)

        QApplication.instance().sendEvent(self.parentMenu, event)
        self.parentMenu.setFocusPolicy(Qt.StrongFocus)
        self.parentMenu.setFocus()
        self.parentMenu.enableLayer()

        self.parentMenu.moveAll()

    def moveToCursor(self):
        pos = QCursor.pos()
        xOffset = 10  # border?
        # self.move(pos.x() - (self.width() * 0.5), pos.y() - (self.height() * 0.5) - 12)
        # print ('self.cursorPos', self.cursorPos)
        # print self.mapFromGlobal(self.cursorPos)
        self.cursorPos = QPoint(self.cursorPos.x() - self.screenGeo.left(), self.cursorPos.y() - self.screenGeo.top())
        self.move(self.screenGeo.left(), self.screenGeo.top())

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        lineColor = QColor(68, 68, 68, 128)
        linePenColor = QColor(255, 160, 47, 255)
        blank = QColor(124, 124, 124, 1)
        empty = QColor(124, 124, 124, 0)

        centralColour = QColor(68, 68, 68, 64)
        centralColourMid = QColor(68, 68, 68, 32)
        centralColourFade = QColor(68, 68, 68, 0)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.drawRoundedRect(0, 0, self.width(), self.height(), self.width() * 0.5, self.width() * 0.5)

        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setBrush(QBrush(blank))
        qp.drawRoundedRect(self.rect(), 8, 8)

        # subtle central shadow
        shadowGrad = QRadialGradient(self.cursorPos, 200)
        shadowGrad.setColorAt(0, centralColour)
        shadowGrad.setColorAt(0.2, centralColourMid)
        shadowGrad.setColorAt(1, centralColourFade)
        qp.setPen(QPen(QBrush(empty), 0))
        qp.setBrush(QBrush(shadowGrad))
        qp.drawEllipse(self.cursorPos.x() - 300,
                       self.cursorPos.y() - 300,
                       600,
                       600)

        # central dot
        qp.setBrush(QBrush(lineColor))
        qp.drawEllipse(self.cursorPos.x() - self.centralRadius / 2,
                       self.cursorPos.y() - self.centralRadius / 2,
                       self.centralRadius,
                       self.centralRadius)
        # print (self.currentCursorPos.x(), self.currentCursorPos.y())

        if self.activeButton:
            qp.setPen(QPen(QBrush(linePenColor), 4))
            offset = 0
            buttonPos = self.activeButton.absPos
            '''
            if isinstance(self.activeButton.parent(), ToolboxDoubleButton):
                buttonPos += self.activeButton.parent().pos()
            '''
            if buttonPos.x() < self.cursorPos.x():
                offset = self.activeButton.width()
            endPoint = QPoint(buttonPos.x() + offset,
                              buttonPos.y() + self.activeButton.height() / 2)
            angle = math.atan2(self.cursorPos.x() - endPoint.x(), self.cursorPos.y() - endPoint.y())
            # print ('angle', angle)
            # print (math.cos(angle) * (self.centralRadius/2))
            # print (math.sin(angle) * (self.centralRadius/2))

            qp.drawLine(endPoint.x(),
                        endPoint.y(),
                        self.cursorPos.x() - (math.sin(angle) * (self.centralRadius / 1.5)),
                        self.cursorPos.y() - (math.cos(angle) * (self.centralRadius / 1.5)))
        '''
        qp.setPen(QPen(QBrush(blank), 0))
        qp.setBrush(QBrush(blank))
        qp.drawRoundedRect(self.rect(), 8, 8)
        '''
        # super(ViewportDialog, self).paintEvent(event)
        qp.end()

    def mouseMoveEvent(self, event):
        # print ('mouseMoveEvent', event.pos())
        self.currentCursorPos = self.mapFromGlobal(event.globalPos())
        self.getClosesWidget()
        self.update()

    def mousePressEvent(self, event):
        # print ('mousePressEvent', event)
        event.accept()
        '''
        event = QKeyEvent(QEvent.KeyPress,
                              self.invokedKey)
        QApplication.instance().sendEvent(self, event)
        '''

    def getClosesWidget(self):
        # print ('getClosesWidget')
        distance = self.distance(self.cursorPos, self.currentCursorPos)
        for w in self.allButtons:
            w.setNonHoverSS()
        if distance < self.scalar:
            self.activeButton = None
            return
        if self.allButtons:
            closest = 9999
            closestWidget = None
            for w in self.allButtons:
                if not isinstance(w, ToolboxButton):
                    # print ('skip', w)
                    continue
                # w.setNonHoverSS()
                # TODO - fix central point lookup as it's shit
                widgetPos = QPoint(w.absPos.x() + w.width() / 2, w.absPos.y() + w.height() / 2)
                distance = self.distance(widgetPos, self.currentCursorPos)
                if distance < closest:
                    closestWidget = w
                    closest = distance

                # print (widgetPos, distance)
            # print ('closest', closestWidget)
            self.activeButton = closestWidget
            if self.activeButton:
                self.activeButton.setHoverSS()
            self.update()

    def distance(self, point_a, point_b):
        distance = math.sqrt(math.pow(point_a.x() - (point_b.x()), 2) + math.pow(point_a.y() - (point_b.y()), 2))
        return distance

    def tabletEvent(self, e):
        print(e.pressure())

    def keyPressEvent(self, event):
        if event.type() == event.KeyPress:
            if self.recentlyOpened:
                if event.key() is not None:
                    self.invokedKey = event.key()
                    self.recentlyOpened = False

        if not self.invokedKey or self.invokedKey == event.key():
            return
        super(ViewportDialog, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() != Qt.Key_Control and event.key() != Qt.Key_Shift and event.key() != Qt.Key_Alt:
            if not self.invokedKey or self.invokedKey == event.key():
                if self.activeButton:
                    if isinstance(self.activeButton, ToolboxButton):
                        if self.activeButton.executeOnHover:
                            self.activeButton.executeCommand()

                self.close()
                if self.parentMenu:
                    # print ('sending keyreleaseevent')
                    self.parentMenu.keyReleaseEvent(event)
                self.invokedKey = None
        try:
            self.keyReleasedSignal.emit()
        except:
            pass

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            opacity = self.windowOpacity()
            opacity += event.delta() * 0.001
            opacity = min(max(opacity, 0.2), 1)
            self.setWindowOpacity(opacity)


class ReturnButton(QPushButton):
    hoverSignal = Signal(object)

    def __init__(self, label, parent, cls=None, closeOnPress=True, radial=False):
        super(ReturnButton, self).__init__(label, parent)
        self.setIcon(QIcon(':\polySpinEdgeBackward.png'))
        self.setFixedSize(32, 32)
        self.cls = cls
        self.radial = radial
        self.closeOnPress = closeOnPress
        self.clicked.connect(self.buttonClicked)
        self.setNonHoverSS()
        self.setMouseTracking(True)

    def buttonClicked(self):
        self.executeCommand()
        if self.closeOnPress:
            # print ('closeOnPress', self.cls)
            self.cls.closeMenu()
            self.cls.deleteLater()

    def inBoundingBox(self, pos):
        bb = QRect(0, 0, self.width, self.height)
        return bb.contains(pos)

    def setHoverSS(self):
        rounded = int(self.width()) * 0.5
        self.setStyleSheet("ReturnButton{"
                           "border-color: #ffa02f;"
                           "border-radius: %s;"
                           "border-width: 4px;"
                           "border-color: #1e1e1e;"
                           "}" % rounded
                           )

    def setNonHoverSS(self):
        rounded = int(self.width()) * 0.5
        if self.radial:
            self.setStyleSheet("ReturnButton{"
                               "color: #b1b1b1;"
                               "background-color: qradialgradient(cx: 0.5, cy: 0.5 fx: 0.5, fy: 0.5, radius: 1, stop: 0 #bdb3b2 opacity 1, stop: 0.5 #565656);"
                               "border-color: #1e1e1e;"
                               "border-radius: %s;"
                               "}" % (rounded)
                               )
            return
        self.setStyleSheet("ReturnButton{"
                           "color: #b1b1b1;"
                           "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                           "border-width: 4px;"
                           "border-color: #1e1e1e;"
                           "border-radius: %s;"
                           "}" % rounded
                           )

    def mouseMoveEvent(self, event):
        if self.distance(QPoint(self.width() * 0.5, self.height() * 0.5), event.pos()) <= self.height() * 0.5:
            self.setHoverSS()
            self.hoverSignal.emit(self)
            # print ('hover hide current', self.cls)
            self.cls.hideCurrentLayer()

    def executeCommand(self):
        pass

    def distance(self, point_a, point_b):
        distance = math.sqrt(math.pow(point_a.x() - (point_b.x()), 2) + math.pow(point_a.y() - (point_b.y()), 2))
        return distance


class ToolboxButton(QPushButton):
    hoverSignal = Signal(object)
    colourChangedSignal = Signal(str, float, float, float)
    commandExecutedSignal = Signal()

    def __init__(self, label, parent, cls=None, icon=str(), command=None, closeOnPress=True, popupSubMenu=False,
                 subMenuClass=None,
                 subMenu=None,
                 iconWidth=16, iconHeight=16,
                 isSmall=False,
                 fixedWidth=None,
                 colour=[55, 55, 55],
                 colouredBackground=False,
                 ):
        super(ToolboxButton, self).__init__(label, parent)
        self.isSmall = isSmall
        self.borderColour = QColor(30, 30, 30)
        self.colouredBackground = colouredBackground
        self.colourRGB = colour
        # print ('the colour', colour)
        self.colour = rgb_to_hex(colour)
        self.colourDark = list()
        for x in range(1, 5):
            self.colourDark.append(rgb_to_hex(darken_color(colour, float(x) * 0.1)))
        self.lightColour = QColor(198, 198, 198)
        self.darkColour = QColor(32, 32, 32)
        self.textColour, self.isLight = getColourBasedOnRGB(colour, self.lightColour, self.darkColour)
        self.executeOnHover = True
        self.subMenu = subMenu  # sub menu instance
        self.subMenuClass = subMenuClass  # sub menu class for button
        self.setFixedSize(48, 22)
        self.executed = False
        self.labelText = label
        self.cls = cls
        self.command = command
        self.closeOnPress = closeOnPress
        self.clicked.connect(self.buttonClicked)
        self.setNonHoverSS()
        self.setMouseTracking(True)
        self.popupSubMenu = popupSubMenu
        self.pop_up_window = None

        if not fixedWidth:
            fontWidth = self.fontMetrics().boundingRect(self.text()).width() + 16
        else:
            fontWidth = fixedWidth + 16
        if icon:
            fontWidth += iconWidth
        self.setText(str())

        if popupSubMenu:
            self.icon = IconPath + '\popupMenu.png'
        else:
            self.icon = icon

        if self.icon:
            self.pixmap = QPixmap(self.icon).scaled(iconWidth, iconHeight, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.pixmap = QPixmap()
        if isSmall:
            self.setFixedSize(22, 22)
        else:
            self.setFixedSize(max(32, ((fontWidth / 64.0) * 64) + 64), 22)
        # self.setAttribute(Qt.WA_TransparentForMouseEvents)


    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        """
        Move this to somewhere better
        :param pos:
        :return:
        """
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)

            self.pop_up_window.show()

    def disableExecuteOnHover(self):
        self.executeOnHover = False

    def buttonClicked(self):
        try:
            self.executeCommand()
        except:
            pass
        if self.closeOnPress:
            # print ('closeOnPress', self.cls)
            self.cls.closeMenu()
            self.cls.deleteLater()

    def inBoundingBox(self, pos):
        bb = QRect(0, 0, self.width, self.height)
        return bb.contains(pos)

    def setHoverSS(self):
        self.borderColour = QColor(255, 160, 47)
        self.borderWidth = 1
        self.setStyleSheet("ToolboxButton {"
                           "text-align:left;"
                           "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #222936, stop: 0.1 #222936, stop: 0.5 #222936, stop: 0.9 #222936, stop: 1 #222936);"
                           "border-color: #ffa02f}"
                           )
        self.textColour, self.isLight = getColourBasedOnRGB(hex_to_rgb('#222936'), self.lightColour, self.darkColour)

    def setNonHoverSS(self):
        self.borderColour = QColor(30, 30, 30)
        self.borderWidth = 1
        self.setStyleSheet("ToolboxButton {"
                           "color: #b1b1b1;"
                           "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 %s, stop: 0.1 %s, stop: 0.5 %s, stop: 0.9 %s, stop: 1 %s);"
                           "border-width: 1px;"
                           "border-color: #1e1e1e;"
                           "border-style: solid;"
                           "border-radius: 6;"
                           "padding: 3px;"
                           "font-size: 12px;"
                           "text-align:left;"
                           "padding-left: 5px;"
                           "padding-right: 5px;"
                           "}" % (self.colour,
                                  self.colourDark[0],
                                  self.colourDark[1],
                                  self.colourDark[2],
                                  self.colourDark[3],
                                  )
                           )
        self.textColour, self.isLight = getColourBasedOnRGB(self.colourRGB, self.lightColour, self.darkColour)

    def mouseMoveEvent(self, event):
        self.setHoverSS()
        if self.popupSubMenu:
            if not self.subMenu:
                self.subMenu = self.subMenuClass(parentMenu=self.cls)
            self.subMenu.show()
        self.hoverSignal.emit(self)

    def executeCommand(self):
        if self.command:
            if not self.executed:
                self.command()
                self.commandExecutedSignal.emit()
            if self.closeOnPress:
                self.executed = True
            if self.subMenu:
                self.cls.closeMenu()

    def paintEvent(self, event):
        QPushButton.paintEvent(self, event)
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setRenderHint(QPainter.SmoothPixmapTransform, True)
        lineColor = QColor(32, 32, 32, 32)

        lineColorFull = QColor(32, 32, 32)
        fillColor = QColor(198, 198, 198)
        # qp.setCompositionMode(qp.CompositionMode_Source)
        if self.isSmall:
            pos_x = 0.5 * (self.width() - self.pixmap.width())  # hardcoded horizontal margin
        else:
            pos_x = 4  # hardcoded horizontal margin
        pos_y = (self.height() - self.pixmap.height()) / 2

        if self.pixmap:
            qp.drawPixmap(pos_x, pos_y, self.pixmap)

        '''
        if self.colouredBackground:
            grad = QLinearGradient(200, 0, 200, 32)
            grad.setColorAt(0, self.colourDark)
            grad.setColorAt(0.1, self.colour)
            grad.setColorAt(1, self.colourDark)
            qp.setBrush(QBrush(grad))
            qp.setPen(QPen(QBrush(self.borderColour), self.borderWidth))
            qp.drawRoundedRect(-1, -1, self.width()+1, self.height()+1, 6, 6)
        '''
        path = QPainterPath()
        pen = QPen()
        brush = QBrush()
        font = QFont("Console", 10, 10, False)

        pen.setWidth(3.5)
        pen.setColor(lineColor)
        brush.setColor(fillColor)
        qp.setFont(font)
        qp.setPen(pen)
        textPos = QPoint(8, 0)
        if self.pixmap:
            textPos.setX(self.pixmap.width() + textPos.x())
        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(self.labelText)
        pixelsHigh = fontMetrics.height()

        path.addText(textPos.x(), pixelsHigh, font, self.labelText)

        pen = QPen(lineColor, 6.5, Qt.SolidLine, Qt.RoundCap)
        pen2 = QPen(lineColor, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(self.textColour)


        if self.isLight: qp.setCompositionMode(qp.CompositionMode_ColorBurn)
        else: qp.setCompositionMode(qp.CompositionMode_ColorDodge)
        qp.strokePath(path, pen)
        qp.strokePath(path, pen2)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.fillPath(path, brush)

        font = qp.font()
        font.setBold(True)
        qp.setFont(font)
        # qp.drawText(textPos.x(), 16, self.labelText)  # fifth option
        qp.end()

    @Slot()
    def hidePopup(self):
        if self.pop_up_window:
            self.pop_up_window.close()

class ToolboxColourButton(ToolboxButton):
    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        """
        Move this to somewhere better
        :param pos:
        :return:
        """
        pop_up_pos = QCursor.pos()
        self.commandExecutedSignal.emit()
        cmds.colorEditor(mini=True,
                         position=(pop_up_pos.x()-355, pop_up_pos.y()-105),
                         rgbValue=[x/255 for x in self.colourRGB])
        if cmds.colorEditor(query=True, result=True):
            values = cmds.colorEditor(query=True, rgb=True)
            #print 'RGB = ' + str(values)
            self.colourChangedSignal.emit(self.labelText, values[0], values[1],values[2])
        else:
            return

        return

        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)

            self.pop_up_window.show()


class ToolboxDoubleButton(QWidget):
    hoverSignal = Signal(object)

    def __init__(self, label, parent, cls=None, buttons=list(), labelWidth=128, colour="#373737", colourDark="#323232",
                 buttonsOnRight=False, hideLabel=False):
        super(ToolboxDoubleButton, self).__init__(parent)
        self.hideLabel = hideLabel
        self.colour = colour
        self.colourDark = colourDark
        self.setFixedHeight(22)
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        self.label = DropShadowLabel(label)
        self.label.setStyleSheet("background-color:transparent")
        font = QFont("Console", 10, 10, False)
        self.label.setFixedWidth(QFontMetrics(font).width(self.label.text()) + 8)
        self.buttons = buttons

        if not hideLabel: self.mainLayout.addWidget(self.label)

        for button in self.buttons:
            self.mainLayout.addWidget(button)

        if not buttonsOnRight:
            if not hideLabel: self.mainLayout.addWidget(self.label)

    def buttonClicked(self):
        self.executeCommand()
        if self.closeOnPress:
            # print ('closeOnPress', self.cls)
            self.cls.closeMenu()
            self.cls.deleteLater()

    def inBoundingBox(self, pos):
        bb = QRect(0, 0, self.width, self.height)
        return bb.contains(pos)

    def setHoverSS(self):
        self.setStyleSheet("ToolboxButton {"
                           "text-align:left;"
                           "border-color: #ffa02f}"
                           )

    def setNonHoverSS(self):
        self.setStyleSheet("ToolboxButton {"
                           "color: #b1b1b1;"
                           "border-width: 1px;"
                           "border-color: #1e1e1e;"
                           "border-style: solid;"
                           "border-radius: 6;"
                           "padding: 3px;"
                           "font-size: 12px;"
                           "text-align:left;"
                           "padding-left: 5px;"
                           "padding-right: 5px;"
                           "}"
                           )
        self.setStyleSheet("ToolboxButton {"
                           "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                           "}"
                           )

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        lineColor = QColor(68, 68, 68, 128)
        linePenColor = QColor(255, 160, 47, 255)
        blank = QColor(124, 124, 124, 64)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        if not self.hideLabel:
            grad = QLinearGradient(200, 0, 200, 32)
            grad.setColorAt(0, self.colourDark)
            grad.setColorAt(0.1, self.colour)
            grad.setColorAt(1, self.colourDark)
            qp.setBrush(QBrush(grad))

        qp.setPen(QPen(QBrush(lineColor), 0))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        qp.end()

    def mouseMoveEvent(self, event):
        self.setHoverSS()
        if self.popupSubMenu:
            if not self.subMenu:
                # print ('creating submenu, ', self.cls)
                self.subMenu = self.subMenuClass(parentMenu=self.cls)
            self.subMenu.show()
        self.hoverSignal.emit(self)

    def executeCommand(self):
        if self.command:
            self.command()
            if self.subMenu:
                self.cls.closeMenu()


class ToolboDivider(QLabel):
    hoverSignal = Signal(object)

    def __init__(self, label, parent, cls=None):
        super(ToolboDivider, self).__init__(label, parent)
        self.setFixedSize(128, 22)
        self.cls = cls
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: transparent;")

    def inBoundingBox(self, pos):
        bb = QRect(0, 0, self.width, self.height)
        return bb.contains(pos)

    def setHoverSS(self):
        pass

    def setNonHoverSS(self):
        pass


class AimAxisWidget(QWidget):
    editedSignal = Signal(str, str, bool, bool, float, float)

    def __init__(self, itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100.0,
                 scale=1.0):
        super(AimAxisWidget, self).__init__()
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        self.distance = distance
        self.scale = scale
        self.itemLayout = QHBoxLayout()
        self.setLayout(self.itemLayout)
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(32)
        self.upComboBox.setFixedWidth(32)

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.scaleSpinBox = QDoubleSpinBox()
        scaleLabel = QLabel('Scale')
        self.scaleSpinBox.setFixedWidth(80)
        self.scaleSpinBox.setValue(scale)
        self.scaleSpinBox.setMinimum(0.01)
        self.scaleSpinBox.setSingleStep(0.1)

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80)
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(1)

        self.itemLayout.addWidget(aimLabel)
        self.itemLayout.addWidget(self.aimComboBox)
        self.itemLayout.addWidget(upLabel)
        self.itemLayout.addWidget(self.upComboBox)
        self.itemLayout.addWidget(flipAimLabel)
        self.itemLayout.addWidget(self.flipAimCB)
        self.itemLayout.addWidget(flipUpLabel)
        self.itemLayout.addWidget(self.flipUpCB)
        self.itemLayout.addWidget(distanceLabel)
        self.itemLayout.addWidget(self.distanceSpinBox)

        # draw scale
        self.itemLayout.addWidget(scaleLabel)
        self.itemLayout.addWidget(self.scaleSpinBox)

        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        self.scaleSpinBox.valueChanged.connect(self.widgetedited)

    def widgetedited(self, *args):
        self.editedSignal.emit(str(self.aimComboBox.currentText()),
                               str(self.upComboBox.currentText()),
                               self.flipAimCB.isChecked(),
                               self.flipUpCB.isChecked(),
                               self.distanceSpinBox.value(),
                               self.scaleSpinBox.value()
                               )


class AimAxisDialog(BaseDialog):
    assignSignal = Signal(str, str, str, bool, bool, float, float)
    editedSignal = Signal(str, str, str, bool, bool, float, float)
    closeSignal = Signal()

    def __init__(self, controlName=str, parent=None,
                 title='Assign default aim for control',
                 text='what  what?',
                 itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100,
                 scale=1.0):
        super(AimAxisDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedSize(580, 130)
        self.controlName = controlName
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        self.aimWidget = AimAxisWidget(itemList=itemList,
                                       aimAxis=aimAxis,
                                       upAxis=upAxis,
                                       flipAim=flipAim,
                                       flipUp=flipUp,
                                       distance=distance,
                                       scale=scale)
        '''
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.itemLayout = QHBoxLayout()
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(32)
        self.upComboBox.setFixedWidth(32)

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80)
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(0.1)
        self.itemLayout.addWidget(aimLabel)
        self.itemLayout.addWidget(self.aimComboBox)
        self.itemLayout.addWidget(upLabel)
        self.itemLayout.addWidget(self.upComboBox)
        self.itemLayout.addWidget(flipAimLabel)
        self.itemLayout.addWidget(self.flipAimCB)
        self.itemLayout.addWidget(flipUpLabel)
        self.itemLayout.addWidget(self.flipUpCB)
        self.itemLayout.addWidget(distanceLabel)
        self.itemLayout.addWidget(self.distanceSpinBox)
        '''
        self.layout.addWidget(self.aimWidget)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)
        '''
        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        '''
        self.aimWidget.editedSignal.connect(self.widgetedited)

    def assignPressed(self):
        self.assignSignal.emit(self.controlName,
                               str(self.aimWidget.aimComboBox.currentText()),
                               str(self.aimWidget.upComboBox.currentText()),
                               self.aimWidget.flipAimCB.isChecked(),
                               self.aimWidget.flipUpCB.isChecked(),
                               self.aimWidget.distanceSpinBox.value(),
                               self.aimWidget.scaleSpinBox.value()
                               )
        self.close()

    def close(self):
        self.closeSignal.emit()
        super(AimAxisDialog, self).close()

    def widgetedited(self, aim, up, flipAim, flipUp, distance, scale):
        self.editedSignal.emit(self.controlName,
                               aim,
                               up,
                               flipAim,
                               flipUp,
                               distance,
                               scale
                               )


class PickListDialog(BaseDialog):
    assignSignal = Signal(str, str)

    def __init__(self, rigName=str, parent=None, title='title!!!?', text='what  what?', itemList=list()):
        super(PickListDialog, self).__init__(parent=parent, title=title, text=text)
        self.rigName = rigName
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        self.itemComboBox = QComboBox()
        for item in itemList:
            self.itemComboBox.addItem(item)
        self.layout.addWidget(self.itemComboBox)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)

    def assignPressed(self):
        self.assignSignal.emit(str(self.itemComboBox.currentText()), str(self.rigName))
        self.close()


class PickObjectDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(PickObjectDialog, self).__init__(parent=parent, title=title, text=text)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)
        self.show()

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))
        self.assignSignal.emit(str(sel[0]))


class PickwalkQueryWidget(QDialog):
    AssignNewRigSignal = Signal(str)
    CreateNewRigMapSignal = Signal(str)
    IgnoreRigSignal = Signal(str)

    def __init__(self, parent=None, title='title?', rigName=str(), text='message?',
                 assignText='Assign existing map',
                 createText='Create new map',
                 ignoreText='Ignore',
                 cancelText='Cancel',
                 ):
        super(PickwalkQueryWidget, self).__init__(parent=parent)
        self.rigName = rigName
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Ignore | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # self.layout = QVBoxLayout()
        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.layout)

        # self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(400, 120)
        mainLayout = QVBoxLayout()
        layout = QVBoxLayout()
        buttonLayout = QHBoxLayout()

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(text)
        self.text.setStyleSheet(getqss.getStyleSheet())

        self.assignExistingButton = QPushButton(assignText)
        self.assignExistingButton.setStyleSheet(getqss.getStyleSheet())

        self.createButton = QPushButton(createText)
        self.createButton.setStyleSheet(getqss.getStyleSheet())

        self.ignoreButton = QPushButton(ignoreText)
        self.ignoreButton.setStyleSheet(getqss.getStyleSheet())

        self.cancelButton = QPushButton(cancelText)
        self.cancelButton.setStyleSheet(getqss.getStyleSheet())

        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignExistingButton)
        buttonLayout.addWidget(self.createButton)
        buttonLayout.addWidget(self.ignoreButton)
        buttonLayout.addWidget(self.cancelButton)

        self.assignExistingButton.clicked.connect(self.assignNewRig)
        self.createButton.clicked.connect(self.createNewRigMap)
        self.ignoreButton.clicked.connect(self.ignoreRigMap)
        self.cancelButton.clicked.connect(self.close)

        self.setLayout(mainLayout)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def assignNewRig(self, *args):
        self.AssignNewRigSignal.emit(self.rigName)
        self.close()

    def createNewRigMap(self, *args):
        self.CreateNewRigMapSignal.emit(self.rigName)
        self.close()

    def ignoreRigMap(self, *args):
        self.IgnoreRigSignal.emit(self.rigName)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(PickwalkQueryWidget, self).keyPressEvent(event)


class QTreeSingleViewWidget(QFrame):
    pressedSignal = Signal(str)
    itemChangedSignal = Signal(str)

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

        # self.topLayout.addWidget(self.label)
        self.topLayout.addWidget(self.filterLineEdit)

        self.listView = QListView()

        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.model = QStandardItemModel()

        self.proxyModel.setSourceModel(self.model)
        self.listView.setModel(self.proxyModel)
        self.listView.clicked.connect(self.itemClicked)
        self.model.itemChanged.connect(self.itemChanged)
        self.filterLineEdit.textChanged.connect(self.filterRegExpChanged)

        self.listView.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.listView.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.toolTypeScrollArea = QScrollArea()
        self.toolTypeScrollArea.setWidget(self.listView)
        self.toolTypeScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.toolTypeScrollArea)

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
        # print 'itemClicked', index
        item = self.model.itemFromIndex(self.proxyModel.mapToSource(index))
        self.pressedSignal.emit(item.text())

    def itemChanged(self, item):
        self.itemChangedSignal.emit(item.text())

    def selectItem(self, itemText):
        for item in self.model.findItems(itemText):
            ix = self.model.indexFromItem(item)
            sm = self.listView.selectionModel()
            sm.select(ix, QItemSelectionModel.Select)
            return


class TextInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedComboSignal = Signal(str, str)
    acceptedKeyComboSignal = Signal(str, str, str)
    acceptedKeySubComboSignal = Signal(str, str, str)
    acceptedCBSignal = Signal(str, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText=str(), default=str(), combo=list(),
                 checkBox=None, overlay=False, showCloseButton=True, key=str(), subKey=str(),
                 objectLineEdit=False,
                 helpString=None,
                 parentWidget=None,
                 lineEditPlaceholder=str(),
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(TextInputWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())
        self.checkBox = checkBox
        self.combo = combo
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        self.checkBoxWD = QCheckBox()
        self.checkBoxWD.setText(self.checkBox)

        self.comboBox = QComboBox()
        for c in self.combo:
            self.comboBox.addItem(c)
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width() + 32)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)

        if objectLineEdit:
            objLineEdit = ObjectSelectLineEdit(stripNamespace=True, placeholderTest=lineEditPlaceholder)
            self.lineEdit = objLineEdit.itemLabel
            layout.addWidget(objLineEdit)
        else:
            self.lineEdit = QLineEdit(default)
            self.lineEdit.setFocusPolicy(Qt.StrongFocus)
            reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
            input_validator = QRegExpValidator(reg_ex, self.lineEdit)
            self.lineEdit.setValidator(input_validator)

            layout.addWidget(self.lineEdit)
        if len(self.combo):
            layout.addWidget(self.comboBox)
        if self.checkBox is not None:
            layout.addWidget(self.checkBoxWD)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        # self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        self.lineEdit.setFocus()
        self.lineEdit.setFixedWidth(self.lineEdit.fontMetrics().boundingRect(self.lineEdit.text()).width() + 16)
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        width = self.comboBox.minimumSizeHint().width()
        self.comboBox.view().setMinimumWidth(width)
        self.comboBox.setMinimumWidth(width)
        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.sizeHint())

        self.show()
        # self.setFixedSize(400, 64)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
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
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedComboSignal.emit(self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeyComboSignal.emit(self.key, self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeySubComboSignal.emit(self.key, self.lineEdit.text(), self.subKey)
        self.acceptedCBSignal.emit(self.lineEdit.text(), self.checkBoxWD.isChecked())
        self.close()

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(TextInputWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(TextInputWidget, self).keyPressEvent(event)

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
        super(TextInputWidget, self).show()


class InfoPromptWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedComboSignal = Signal(str, str)
    acceptedKeyComboSignal = Signal(str, str, str)
    acceptedKeySubComboSignal = Signal(str, str, str)
    acceptedCBSignal = Signal(str, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText=str(), default=str(), combo=list(),
                 checkBox=None, overlay=False, showCloseButton=True, key=str(), subKey=str(),
                 helpString=None,
                 image=str(),
                 imagePath=IconPath,
                 gif=bool,
                 error=False,
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                 show=True,
                 showButton=True):
        super(InfoPromptWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.error = error
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())
        self.checkBox = checkBox
        self.combo = combo
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

        if image:
            self.imageLabel = QLabel(self)
            if gif:
                self.movie = QMovie(os.path.join(imagePath, image))

                self.imageLabel.setMovie(self.movie)
                self.movie.start()

            else:
                self.imagePixmap = QPixmap(os.path.join(imagePath, image))
                self.imageLabel.setPixmap(self.imagePixmap)

        self.titleText = QLabel(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit(default)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        self.checkBoxWD = QCheckBox()
        self.checkBoxWD.setText(self.checkBox)

        self.comboBox = QComboBox()
        for c in self.combo:
            self.comboBox.addItem(c)
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())

        # layout.addWidget(btnSetFolder)

        self.helpLabel = QLabel(self.helpString)
        self.helpLabel.setWordWrap(True)

        titleLayout.addWidget(self.titleText)

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)
        # layout.addWidget(self.text)
        # layout.addWidget(self.lineEdit)
        if len(self.combo):
            layout.addWidget(self.comboBox)
        if self.checkBox is not None:
            layout.addWidget(self.checkBoxWD)

        if self.helpString:
            mainLayout.addWidget(self.helpLabel)
        if image:
            mainLayout.addWidget(self.imageLabel)
        if showButton:
            self.saveButton = QPushButton(buttonText)
            self.saveButton.setStyleSheet(getqss.getStyleSheet())
            self.saveButton.clicked.connect(self.acceptedFunction)
            mainLayout.addWidget(self.saveButton)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        width = self.comboBox.minimumSizeHint().width()
        self.comboBox.view().setMinimumWidth(width)
        self.comboBox.setMinimumWidth(width)
        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.sizeHint())
        # self.setFixedSize(400, 64)
        if show:
            self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        if self.error:
            lineColor = QColor(240, 68, 68, 128)
        else:
            lineColor = QColor(68, 240, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedComboSignal.emit(self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeyComboSignal.emit(self.key, self.lineEdit.text(), self.comboBox.currentText())
        self.acceptedKeySubComboSignal.emit(self.key, self.lineEdit.text(), self.subKey)
        self.acceptedCBSignal.emit(self.lineEdit.text(), self.checkBoxWD.isChecked())
        self.close()

    def showRelative(self, screenPos=QPoint(0, 0), widgetSize=QPoint(0, 0)):

        screens = QApplication.screens()
        for s in screens:
            if s.availableGeometry().contains(QCursor.pos()):
                screen = s

        screenGeo = screen.availableGeometry()
        screenGeo.width()
        screenGeo.height()
        finalPos = QPoint(0, 0)

        if screenPos.y() + widgetSize.height() + self.height() > screenGeo.height():
            finalPos.setY(screenPos.y() - self.height())
        else:
            finalPos.setY(screenPos.y() + widgetSize.height())

        if screenPos.x() + widgetSize.width() + self.width() > screenGeo.width():
            finalPos.setX(screenPos.x() + widgetSize.width() - self.width())
        else:
            finalPos.setX(screenPos.x())

        self.move(finalPos)
        self.show(auto=False)

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(InfoPromptWidget, self).close()
        self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(InfoPromptWidget, self).keyPressEvent(event)

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

    def show(self, auto=True):
        if auto:
            position_x = (self.parent().pos().x() + (self.parent().width() - self.frameGeometry().width()) / 2)
            position_y = (self.parent().pos().y() + (self.parent().height() - self.frameGeometry().height()) / 2)

            self.move(position_x, position_y)
        super(InfoPromptWidget, self).show()


class ChannelInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(ChannelInputWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will replace your current path.')
        self.lineEdit.setPlaceholderText(default)
        self.cle_action_pick.triggered.connect(self.pickChannel)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        self.pickChannel()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return pm.warning('no channel selected')
        self.lineEdit.setText(channels[0].rsplit('.', 1)[-1])

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(ChannelInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class IntInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(int)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept"):
        super(IntInputWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = intFieldWidget(optionVar=None,
                                       defaultValue=1,
                                       minimum=1, maximum=100, step=1)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )
        # self.setFixedSize(self.sizeHint())

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
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
        self.acceptedSignal.emit(self.lineEdit.spinBox.value())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(IntInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class ObjectInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedDataSignal = Signal(str, list)
    oldPos = None

    def __init__(self, title=str(), label=str(), buttonText="Accept", default="Accept", data=None,
                 objectType='nurbsCurve'):
        super(ObjectInputWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())
        self.data = data
        self.objectType = objectType
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will replace your current path.')
        self.lineEdit.setPlaceholderText(default)
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return

        if self.objectType == "nurbsCurve":
            shape = sel[0].getShape()
            if not shape:
                return
            if pm.nodeType(shape) == "nurbsCurve":
                self.lineEdit.setText(str(sel[0]))
        elif self.objectType == "nurbsSurface":
            shape = sel[0].getShape()
            if not shape:
                return
            if pm.nodeType(shape) == "nurbsSurface":
                self.lineEdit.setText(str(sel[0]))
        elif self.objectType == "transform":
            if not cmds.objectType(str(sel[0])) == 'transform':
                return
            self.lineEdit.setText(str(sel[0]))

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedDataSignal.emit(self.lineEdit.text(), self.data)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(ObjectInputWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class promptWidget(QWidget):
    saveSignal = Signal(str)

    def __init__(self, title=str(), text=str(), defaultInput=str(), buttonText=str()):
        super(promptWidget, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getqss.getStyleSheet())

        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(300, 64)
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(text)
        self.lineEdit = QLineEdit(defaultInput)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_]")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        self.confirmButton = QPushButton(buttonText)
        self.confirmButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        mainLayout.addWidget(self.titleText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.confirmButton)

        self.confirmButton.clicked.connect(self.confirm)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def confirm(self, *args):
        self.saveSignal.emit(self.lineEdit.text())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(promptWidget, self).keyPressEvent(event)


class subHeader(QLabel):
    """
    label with wordwrap
    """

    def __init__(self, label=str()):
        super(subHeader, self).__init__()
        self.setText(label)
        self.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


class infoLabel(QLabel):
    def __init__(self, textLines=list()):
        super(infoLabel, self).__init__()
        text = str()
        for line in textLines:
            text += line + '\n'
        self.setText(text)
        self.setWordWrap(True)


class optionWidget(QWidget):
    def __init__(self, label=str):
        super(optionWidget, self).__init__()
        self.labelText = label
        self.initUI()

    def initUI(self):
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.scrollWidget = QWidget()  # Widget that contains the collection of Vertical Box
        self.layout = QVBoxLayout()  # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        self.scrollWidget.setLayout(self.layout)

        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollWidget)

        self.mainLayout.addWidget(self.scroll)

        self.label = QLabel(self.labelText)
        self.label.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.label)
        self.setGeometry(600, 100, 1000, 900)
        self.setWindowTitle('Scroll Area Demonstration')


class optionVarWidget(QWidget):
    def __init__(self, label=str, optionVar=str):
        super(optionVarWidget, self).__init__()
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.labelText = QLabel(label)


class optionVarBoolWidget(optionVarWidget):
    changedSignal = Signal(bool)

    def __init__(self, label=str, optionVar=str):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.checkBox = QCheckBox()
        self.checkBox.setChecked(pm.optionVar.get(self.optionVar, False))
        pm.optionVar(intValue=(self.optionVar, pm.optionVar.get(self.optionVar, False)))
        self.checkBox.clicked.connect(self.checkBoxEdited)
        self.layout.addWidget(self.labelText)
        self.layout.addWidget(self.checkBox)

    def checkBoxEdited(self):
        pm.optionVar(intValue=(self.optionVar, self.checkBox.isChecked()))
        self.sendChangedSignal()

    def sendChangedSignal(self):
        self.changedSignal.emit(self.checkBox.isChecked())


class optionVarListWidget(optionVarWidget):
    """
    changing to use classdata instead of maya option vars
    """
    changedSignal = Signal(str, list)

    def __init__(self, label=str(), optionVar=str(), optionList=list(), classData=dict()):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.labelText.setAlignment(Qt.AlignTop)
        self.cbLayout = QGridLayout()
        optionVarValues = classData.get(optionVar, list())
        self.checkBoxes = list()
        numColumns = 2
        currentRow = 0
        count = 0
        for op in optionList:
            checkBox = QCheckBox()
            self.checkBoxes.append(checkBox)
            checkBox.setText(op)
            checkBox.setObjectName(optionVar + '_' + op)
            checkBox.setChecked(op in optionVarValues)
            self.cbLayout.addWidget(checkBox, count / 2, count % numColumns)
            checkBox.clicked.connect(self.checkBoxEdited)
            count += 1

        self.layout.addWidget(self.labelText)
        self.layout.addLayout(self.cbLayout)

    def checkBoxEdited(self, *args):
        activeValues = list()
        for cb in self.checkBoxes:
            if cb.isChecked():
                activeValues.append(cb.text())

        self.changedSignal.emit(self.optionVar, activeValues)


class filePathWidget(QWidget):
    layout = None
    path = None
    optionVar = None
    dirButton = None

    def __init__(self, optionVar, defaultValue):
        super(filePathWidget, self).__init__()
        self.optionVar = optionVar
        self.path = pm.optionVar.get(self.optionVar, defaultValue)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.pathLabel = QLabel('Path:')
        self.pathLineEdit = QLineEdit(self.path)
        self.dirButton = QPushButton("Set folder")
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.dirButton)
        self.dirButton.clicked.connect(self.selectDirectory)

    def selectDirectory(self, *args):
        dialog = QFileDialog(None, caption="Pick Folder")
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setDirectory(self.path)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_directory = dialog.getExistingDirectory()

        if selected_directory:
            pm.optionVar[self.optionVar] = selected_directory
            self.path = selected_directory
            self.pathLineEdit.setText(self.path)


class ChannelSelectLineEdit(QWidget):
    label = None
    lineEdit = None
    editedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), text=str, tooltip=str(), lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False):
        super(ChannelSelectLineEdit, self).__init__()
        self.stripNamespace = stripNamespace
        self.key = key
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignLeft)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)
        self.label = QLabel(text)
        self.lineEdit = QLineEdit()
        self.lineEdit.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.lineEdit.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.pickChannel)
        self.lineEdit.setPlaceholderText(placeholderTest)
        self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        if text:
            self.mainLayout.addWidget(self.label)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.lineEdit)

        if text:
            self.label.setFixedWidth(60)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    def pickChannel(self, *args):
        channels = mel.eval('selectedChannelBoxPlugs')
        if not channels:
            return pm.warning('no channel selected')
        refState = cmds.referenceQuery(channels[0].split('.')[0], isNodeReferenced=True)

        if refState:
            if self.stripNamespace:
                refNamespace = cmds.referenceQuery(channels[0].split('.')[0], namespace=True)
                # print ('refNamespace', refNamespace)
                if refNamespace.startswith(':'):
                    refNamespace = refNamespace[1:]
                channel = channels[0]
                self.lineEdit.setText(channel.replace(refNamespace, ''))
            else:
                self.lineEdit.setText(channels[0].rsplit(':', 1)[-1])
        else:
            self.lineEdit.setText(channels[0])

    @Slot()
    def sendtextChangedSignal(self):
        self.editedSignal.emit(self.lineEdit.text())
        self.editedSignalKey.emit(self.key, self.lineEdit.text())


class ChannelSelectLineEditEnforced(ChannelSelectLineEdit):
    def __init__(self, key=str(), text=str(), tooltip=str(), lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False, baseNamespace=str()):
        super(ChannelSelectLineEditEnforced, self).__init__(key=key,
                                                            text=text,
                                                            tooltip=tooltip,
                                                            lineEditWidth=lineEditWidth,
                                                            placeholderTest=placeholderTest,
                                                            stripNamespace=stripNamespace)

        self.baseNamespace = baseNamespace
        self.lineEdit.textChanged.connect(self.validateText)

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.lineEdit.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.lineEdit.setStyleSheet(getqss.getStyleSheet())

    def validateText(self):
        if not '.' in self.lineEdit.text():
            self.errorHighlight()
            return
        node, attr = str(self.baseNamespace + ':' + self.lineEdit.text()).split('.')
        if not cmds.objExists(node):
            self.errorHighlight()
            return
        if not cmds.attributeQuery(attr, node=node, exists=True):
            self.errorHighlight()
        else:
            self.errorHighlightRemove()


MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)


class hotkeyLineEdit(QLineEdit):
    keyPressed = Signal(str)

    def keyPressEvent(self, event):
        keyname = ''
        key = event.key()
        modifiers = int(event.modifiers())
        if (modifiers and modifiers & MOD_MASK == modifiers and
                key > 0 and key != Qt.Key_Shift and key != Qt.Key_Alt and
                key != Qt.Key_Control and key != Qt.Key_Meta):

            keyname = QKeySequence(modifiers + key).toString()

            # print('event.text(): %r' % event.text())
            # print('event.key(): %d, %#x, %s' % (key, key, keyname))
        elif (key > 0 and key != Qt.Key_Shift and key != Qt.Key_Alt and
              key != Qt.Key_Control and key != Qt.Key_Meta):
            keyname = QKeySequence(key).toString()
            # print('event.text(): %r' % event.text())
        self.keyPressed.emit(keyname)


class hotKeyWidget(QWidget):
    label = None
    lineEdit = None
    assignSignal = Signal(str, str, bool, bool)

    def __init__(self, cls=None, command=str(), text=str(), tooltip=str(), placeholderTest=str()):
        super(hotKeyWidget, self).__init__()
        # print('self.command', command)
        self.command = command
        self.cls = cls
        niceCommandName = '{0}NameCommand'.format(command)
        existingData = self.cls.commandData.get(niceCommandName, {'key': str(),
                                                                  'ctrl': False,
                                                                  'alt': False,
                                                                  'Command': niceCommandName,
                                                                  'Release': False,
                                                                  'KeyRepeat': True
                                                                  })
        commandString = ''
        if existingData['key']:
            if existingData['ctrl']:
                commandString += 'Ctrl+'
            if existingData['alt']:
                commandString += 'Alt+'
            if existingData['key'].isupper():
                commandString += 'Shift+'
            commandString += existingData['key']
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.label = QLabel('Existing Hotkey')
        self.lineEdit = hotkeyLineEdit(commandString)
        self.lineEdit.keyPressed.connect(self.setLabelText)

        self.assignButton = QPushButton('Assign')
        self.toolButton = HotkeyToolButton(text='test',
                                           imgLabel=command,
                                           width=64,
                                           height=22,
                                           icon=":/pythonFamily.png",
                                           command=command)
        self.clipboardButton = QPushButton()
        self.clipboardButton.setIcon(QIcon(':/menuIconCopy.png'))
        self.clipboardButton.clicked.connect(self.copyText)
        pixmap = QPixmap(":/arrowDown.png")
        pixmap = pixmap.scaled(QSize(22, 22), Qt.KeepAspectRatio)

        icon = QIcon(pixmap)
        icon = QIcon(pixmap)
        self.cle_action_pick = self.lineEdit.addAction(icon, QLineEdit.TrailingPosition)
        # self.cle_action_clear = self.lineEdit.addAction(QIcon(":/hotkeyFieldClear.png"), QLineEdit.TrailingPosition)

        self.cle_action_pick.setToolTip(tooltip)
        self.cle_action_pick.triggered.connect(self.show_category_table_Popup)
        self._category_table_Popup = QMenu(self)
        self.recentAction = QAction('Recent Command List', self._category_table_Popup, checkable=True,
                                    checked=existingData['KeyRepeat'])
        self.onPressAction = QAction('On Press', self._category_table_Popup, checkable=True,
                                     checked=not existingData['Release'])
        self.onReleaseAction = QAction('On Release', self._category_table_Popup, checkable=True,
                                       checked=existingData['Release'])
        self._category_table_Popup.addAction(self.recentAction)
        self._category_table_Popup.addSeparator()
        self._category_table_Popup.addAction(self.onPressAction)
        self._category_table_Popup.addAction(self.onReleaseAction)

        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.action_group.addAction(self.onPressAction)
        self.action_group.addAction(self.onReleaseAction)

        self.lineEdit.setPlaceholderText(placeholderTest)
        # self.lineEdit.textChanged.connect(self.sendtextChangedSignal)
        self.assignButton.clicked.connect(self.assinHotkey)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.assignButton)
        self.layout.addWidget(self.toolButton)
        self.layout.addWidget(self.clipboardButton)

        # self.label.setFixedWidth(60)

        self.label.setStyleSheet("QFrame {"
                                 "border-width: 0;"
                                 "border-radius: 0;"
                                 "border-style: solid;"
                                 "border-color: #222222}"
                                 )

    def copyText(self):
        cmd = 'echo ' + self.command + '|clip'
        return subprocess.check_call(cmd, shell=True)

    @Slot()
    def setLabelText(self, text):
        self.lineEdit.setText(text)

    @Slot()
    def sendtextChangedSignal(self):
        # print ('sendtextChangedSignal', self.lineEdit.text())
        self.editedSignal.emit(self.command, self.lineEdit.text(), self.onPressAction.isChecked(),
                               self.recentAction.isChecked())

    @Slot()
    def assinHotkey(self):
        self.assignSignal.emit(self.command, self.lineEdit.text(), self.onPressAction.isChecked(),
                               self.recentAction.isChecked())

    @Slot()
    def show_category_table_Popup(self):
        '''
        Show Popup Menu on Category Table
        '''
        self._category_table_Popup.exec_(QCursor.pos())


class ObjectSelectLineEdit(QWidget):
    pickedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), label=str(), hint=str(), labelWidth=65, lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False,
                 tooltip=str()):
        QWidget.__init__(self)
        self.key = key
        self.stripNamespace = stripNamespace
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.mainLayout)
        self.label = QLabel(label)
        # self.label.setFixedWidth(labelWidth)
        self.itemLabel = QLineEdit()
        self.itemLabel.setPlaceholderText(placeholderTest)
        self.itemLabel.setFixedWidth(lineEditWidth)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(hint)
        self.cle_action_pick.triggered.connect(self.pickObject)
        self.itemLabel.textChanged.connect(self.textEdited)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.itemLabel)

    def pickObject(self):
        # print ('pickObject')
        sel = pm.ls(sl=True)
        if not sel:
            return
        if self.stripNamespace:
            s = str(sel[0]).split(':', 1)[-1]
        else:
            s = str(sel[0])
        self.itemLabel.setText(s)
        self.pickedSignal.emit(s)
        # self.editedSignalKey.emit(self.key, str(sel[0]))

    def setTextNoUpdate(self, text):
        self.blockSignals(True)
        self.itemLabel.setText(text)
        self.blockSignals(False)

    @Slot()
    def textEdited(self):
        self.editedSignalKey.emit(self.key, self.itemLabel.text())

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 1px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.itemLabel.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.itemLabel.setStyleSheet(getqss.getStyleSheet())


class ObjectSelectLineEditEnforced(ObjectSelectLineEdit):
    def __init__(self, key=str(), label=str(), hint=str(), labelWidth=65, lineEditWidth=200, placeholderTest=str(),
                 stripNamespace=False,
                 baseNamespace=str(),
                 tooltip=str()):
        super(ObjectSelectLineEditEnforced, self).__init__(key=key, label=label, hint=hint, labelWidth=labelWidth,
                                                           lineEditWidth=lineEditWidth, placeholderTest=placeholderTest,
                                                           stripNamespace=stripNamespace,
                                                           tooltip=tooltip)
        self.baseNamespace = baseNamespace
        self.itemLabel.textChanged.connect(self.validateText)

    def errorHighlight(self):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        self.itemLabel.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self):
        self.itemLabel.setStyleSheet(getqss.getStyleSheet())

    def validateText(self):
        if not cmds.objExists(self.baseNamespace + ':' + self.itemLabel.text()):
            self.errorHighlight()
        else:
            self.errorHighlightRemove()


class comboBoxWidget(QWidget):
    mainLayout = None
    optionVar = None
    optionValue = 0

    changedSignal = Signal(str)
    editedSignalKey = Signal(str, str)

    def __init__(self, key=str(), optionVar=None, values=list(), defaultValue=int(), label=str()):
        QWidget.__init__(self)
        self.key = key
        self.values = values
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        if optionVar is not None:
            self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        label = QLabel(label)

        self.comboBox = QComboBox()
        if self.values:
            for c in self.values:
                self.comboBox.addItem(c)
            self.comboBox.setCurrentIndex(self.values.index(self.defaultValue))
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())

        self.mainLayout.addWidget(label)
        self.mainLayout.addWidget(self.comboBox)
        self.comboBox.currentIndexChanged.connect(self.interactivechange)
        self.mainLayout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            pm.optionVar[self.optionVar] = self.comboBox.currentText()
        self.changedSignal.emit(self.comboBox.currentText())
        self.editedSignalKey.emit(self.key, self.comboBox.currentText())

    def updateValues(self, valueList, default):
        self.comboBox.clear()
        self.values = valueList
        for c in self.values:
            self.comboBox.addItem(c)
        self.comboBox.setCurrentIndex(self.values.index(default))


class intFieldWidget(QWidget):
    layout = None
    optionVar = None
    optionValue = 0

    changedSignal = Signal(float)
    editedSignalKey = Signal(str, float)

    def __init__(self, key=str(), optionVar=None, defaultValue=int(), label=str(), minimum=0, maximum=1, step=0.1,
                 tooltip=str()):
        QWidget.__init__(self)
        self.key = key

        self.optionVar = optionVar
        self.defaultValue = defaultValue
        if optionVar is not None:
            self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        label = QLabel(label)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.spinBox = QDoubleSpinBox()
        self.spinBox.setMaximum(maximum)
        self.spinBox.setMinimum(minimum)
        self.spinBox.setSingleStep(step)
        self.spinBox.setValue(defaultValue)
        if step == 1:
            self.spinBox.setDecimals(0)
        self.spinBox.setProperty("value", self.optionValue)
        self.layout.addWidget(label)
        self.layout.addItem(spacerItem)
        self.layout.addWidget(self.spinBox)
        self.spinBox.valueChanged.connect(self.interactivechange)
        self.layout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            pm.optionVar[self.optionVar] = self.spinBox.value()
        self.changedSignal.emit(self.spinBox.value())
        # print ('interactiveChange', self.spinBox.value())
        self.editedSignalKey.emit(self.key, self.spinBox.value())

    def updateValues(self, value):
        self.spinBox.setValue(value)


class radioGroupWidget(QWidget):
    layout = None
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionVar = str()
    optionValue = str()
    editedSignal = Signal()

    def __init__(self, optionVarList=list(), optionVar=str(), defaultValue=str(), label=str()):
        super(radioGroupWidget, self).__init__()
        self.optionVarList = optionVarList
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addStretch()
        label = QLabel(label)
        btnGrp = QButtonGroup()  # Letter group
        layout.addWidget(label)
        self.buttons = list()
        for index, option in enumerate(self.optionVarList):
            btn = QRadioButton(option)
            btn.toggled.connect(lambda: self.extBtnState(btn))
            self.buttons.append(btn)
            btnGrp.addButton(btn)
            layout.addWidget(btn)
            btn.setChecked(self.optionValue == option)

    def extBtnState(self, button):
        for button in self.buttons:
            if button.isChecked() == True:
                pm.optionVar[self.optionVar] = button.text()
        self.editedSignal.emit()


class radioGroupVertical(object):
    layout = None
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionVar = str()
    optionValue = str()

    def __init__(self, formLayout=QFormLayout, optionVarList=list(), optionVar=str(), defaultValue=str(), label=str(),
                 tooltips=list()):
        super(radioGroupVertical, self).__init__()
        self.tooltips = tooltips
        self.optionVarList = optionVarList
        self.optionVar = optionVar
        self.defaultValue = defaultValue
        self.optionValue = pm.optionVar.get(self.optionVar, defaultValue)

        self.btnGrp = QButtonGroup()  # Letter group
        self.returnedWidgets = list()
        self.buttons = list()
        for index, option in enumerate(self.optionVarList):
            self.buttons.append(QRadioButton(option))
            self.btnGrp.addButton(self.buttons[index])
            self.returnedWidgets.append(['option', self.buttons[index]])
            self.buttons[index].setChecked(self.optionValue == option)
            self.buttons[index].toggled.connect(self.buttonChecked)
            try:
                self.buttons[index].setToolTip(self.tooltips[index])
            except:
                pass

    def buttonChecked(self, value):
        for button in self.buttons:
            if button.isChecked() == True:
                pm.optionVar[self.optionVar] = button.text()


class LicenseWin(BaseDialog):
    ActivateSignal = Signal(str, str)
    OfflineActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title='Tool Name?', machineOnly=False,
                 infoText='Please enter your license key and email address used for this purchase'):
        super(LicenseWin, self).__init__(parent=parent)
        self.setWindowTitle("LicenseWin!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        if machineOnly:
            offlineButton = self.buttonBox.addButton("Offline Activate", QDialogButtonBox.ActionRole)
            offlineButton.clicked.connect(lambda: self.offlineActivate())
        self.buttonBox.addButton("Activate", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.activate)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400, 180)
        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText(infoText)
        self.infoText.setWordWrap(True)

        self.titleText.setAlignment(Qt.AlignCenter)
        self.licenseKeyLabel = QLabel('License key::')
        self.licenseKeyLabel.setStyleSheet(getqss.getStyleSheet())
        self.licenseLineEdit = QLineEdit()
        self.emailLabel = QLabel('Email Address::')
        self.emailLabel.setStyleSheet(getqss.getStyleSheet())
        self.emailLineEdit = QLineEdit()

        # self.mainLayout.addWidget(self.titleText)
        # self.mainLayout.addWidget(self.infoText)
        self.gridLayout.addWidget(self.licenseKeyLabel, 0, 0)
        self.gridLayout.addWidget(self.licenseLineEdit, 0, 1)
        self.gridLayout.addWidget(self.emailLabel, 1, 0)
        self.gridLayout.addWidget(self.emailLineEdit, 1, 1)
        self.mainLayout.addLayout(self.gridLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            self.update()
            self.updateGeometry()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(LicenseWin, self).keyPressEvent(event)

    def activate(self):
        self.errorHighlightRemove(self.licenseLineEdit)
        self.errorHighlightRemove(self.emailLineEdit)
        if not len(self.licenseLineEdit.text()) == 35:
            return cmds.warning('Invalid length license key')
        if not '@' in self.emailLineEdit.text():
            return cmds.warning('Invalid email address')
        if not '.' in self.emailLineEdit.text():
            return cmds.warning('Invalid email address')
        self.ActivateSignal.emit(self.licenseLineEdit.text(), self.emailLineEdit.text())

    def offlineActivate(self):
        self.errorHighlightRemove(self.licenseLineEdit)
        self.errorHighlightRemove(self.emailLineEdit)
        if not len(self.licenseLineEdit.text()) == 35:
            self.errorHighlight(self.licenseLineEdit)
            return cmds.warning('Invalid length license key')
        if not '@' in self.emailLineEdit.text():
            self.errorHighlight(self.emailLineEdit)
            return cmds.warning('Invalid email address')
        if not '.' in self.emailLineEdit.text():
            self.errorHighlight(self.emailLineEdit)
            return cmds.warning('Invalid email address')
        self.OfflineActivateSignal.emit(self.licenseLineEdit.text(), self.emailLineEdit.text())

    def cancel(self):
        self.close()

    def errorHighlight(self, widget):
        borderHighlightQSS = "QLineEdit {border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a)}"

        widget.setStyleSheet(borderHighlightQSS)

    def errorHighlightRemove(self, widget):
        widget.setStyleSheet(getqss.getStyleSheet())


class WarningDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(WarningDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedWidth(200)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout.addWidget(self.buttonBox)


class PickObjectDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(PickObjectDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedWidth(200)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)

    def pickObject(self):
        sel = pm.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))


class TextInputDialog(BaseDialog):
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title=str, label=str, buttonText=str, default=str):
        super(TextInputDialog, self).__init__(parent=parent, title=title)
        self.setWindowTitle("TextInputDialog!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.addButton(buttonText, QDialogButtonBox.AcceptRole)
        # self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)

        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400, 180)

        self.titleText.setAlignment(Qt.AlignCenter)
        self.lineEditLabel = QLabel('%s::' % label)
        self.lineEditLabel.setStyleSheet(getqss.getStyleSheet())
        self.lineEdit = QLineEdit(default)

        self.lineEditLayout = QHBoxLayout()
        self.lineEditLayout.addWidget(self.lineEditLabel)
        self.lineEditLayout.addWidget(self.lineEdit)
        self.mainLayout.addLayout(self.lineEditLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            self.update()
            self.updateGeometry()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(TextInputDialog, self).keyPressEvent(event)


class TextOptionInputDialog(BaseDialog):
    leftClick = False
    oldPos = None

    def __init__(self, parent=None, title=str, label=str, buttonText=str, default=str, text='TextOptionInputDialog'):
        super(TextOptionInputDialog, self).__init__(parent=parent, title=title, text=text)
        self.setWindowTitle("TextInputDialog!")

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.selLayout = QHBoxLayout()
        self.footstepLayout = QHBoxLayout()
        self.layout.addLayout(self.selLayout)
        self.layout.addLayout(self.footstepLayout)

        self.AddSelectionLabel = QLabel('Add selection to sub path')
        self.AddSelectionCB = QCheckBox()
        self.AddSelectionCB.setChecked(True)
        self.UseFootstepsLabel = QLabel('Use footsteps (From first selection)')
        self.UseFootstepsCB = QCheckBox()
        self.UseFootstepsCB.setChecked(True)

        self.selLayout.addWidget(self.AddSelectionCB)
        self.selLayout.addWidget(self.AddSelectionLabel)
        self.selLayout.addStretch()
        self.footstepLayout.addWidget(self.UseFootstepsCB)
        self.footstepLayout.addWidget(self.UseFootstepsLabel)
        self.footstepLayout.addStretch()

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.addButton(buttonText, QDialogButtonBox.AcceptRole)
        # self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)

        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400, 180)

        self.titleText.setAlignment(Qt.AlignCenter)
        self.lineEditLabel = QLabel('%s::' % label)
        self.lineEditLabel.setStyleSheet(getqss.getStyleSheet())
        self.lineEdit = QLineEdit(default)

        self.lineEditLayout = QHBoxLayout()
        self.lineEditLayout.addWidget(self.lineEditLabel)
        self.lineEditLayout.addWidget(self.lineEdit)
        self.mainLayout.addLayout(self.lineEditLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            self.update()
            self.updateGeometry()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(TextOptionInputDialog, self).keyPressEvent(event)


class UpdateWin(BaseDialog):
    ActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None,
                 title='tbAnimTools Update Found',
                 newVersion=str(),
                 oldVersion=str(),
                 updateText=str()):
        super(UpdateWin, self).__init__(parent=parent)
        self.setWindowTitle(title)

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.addButton("Update To Latest", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.setFixedSize(400, 180)
        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 14px;");
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText(updateText)
        self.infoText.setWordWrap(True)

        self.currentVersionLabel = QLabel('Current Version')
        self.currentVersionInfoText = QLabel(oldVersion)
        self.latestVersionLabel = QLabel('Latest Version')
        self.latestVersionInfoText = QLabel(newVersion)

        # self.mainLayout.addWidget(self.titleText)
        # self.mainLayout.addWidget(self.infoText)
        self.gridLayout.addWidget(self.currentVersionLabel, 0, 0)
        self.gridLayout.addWidget(self.currentVersionInfoText, 0, 1)
        self.gridLayout.addWidget(self.latestVersionLabel, 1, 0)
        self.gridLayout.addWidget(self.latestVersionInfoText, 1, 1)
        self.mainLayout.addLayout(self.gridLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
            self.update()
            self.updateGeometry()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(UpdateWin, self).keyPressEvent(event)


class MiniButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon=baseIconFile, toolTip='Close'):
        super(MiniButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(18, 18)

        pixmap = QPixmap(os.path.join(IconPath, icon))
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())


class HelpButton(QPushButton):
    def __init__(self, toolTip='Help', width=32, height=32):
        super(HelpButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(width, height)

        pixmap = QPixmap(":/help.png")
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())


class ToolButton(QPushButton):
    def __init__(self, toolTip='Help', width=32, height=32):
        super(ToolButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(width, height)

        pixmap = QPixmap(":/help.png")
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px; font-size:12px;text-align:right;")
        self.setStyleSheet(getqss.getStyleSheet())


class ToolButton(QPushButton):
    def __init__(self, text=str(), icon=str(), iconWidth=24, iconHeight=24, width=108, height=40, command=None,
                 menuBar=None, imgLabel=str(), sourceType='mel', *args, **kwargs):
        super(ToolButton, self).__init__(*args, **kwargs)
        self.icon = icon
        self.pixmap = None
        self.sourceType = sourceType
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        self.setLayout(QGridLayout())
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, 1)
        pb_layout = self.layout().addWidget(self.label)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent;border: 0px; font-size:12px;text-align:right; margin: 0px;")
        self.label.setStyleSheet("margin-left: 68px;margin-top:0px;margin-right:0px;margin-bottom:0px")
        self.setStyleSheet(getqss.getStyleSheet())
        if self.icon:
            self.label.setStyleSheet("QLabel{background-color: transparent;text-align:right;margin-left: 28px;}")
        else:
            self.label.setStyleSheet("QLabel{background-color: transparent;text-align:right;margin-left: 8px;}")
        self.command = command
        self.menuBar = menuBar
        self.menuItem = None
        self.imgLabel = imgLabel

        if self.command:
            self.clicked.connect(self.evalCommand)
        if self.icon:
            self.pixmap = QPixmap(self.icon).scaled(iconWidth, iconHeight, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.pixmap = QPixmap()

    @Slot()
    def evalCommand(self):
        if self.sourceType == 'mel':
            mel.eval(self.command)
        else:
            self.command()

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            currentShelf = cmds.tabLayout(pm.melGlobals['gShelfTopLevel'], query=True, selectTab=True)
            cmds.setParent(currentShelf)
            shelfButton = cmds.shelfButton(image1=self.icon,
                                           imageOverlayLabel=self.imgLabel,
                                           label=self.imgLabel,
                                           style=cmds.shelfLayout(currentShelf, q=True, style=True),
                                           width=cmds.shelfLayout(currentShelf, q=True, cellWidth=True),
                                           height=cmds.shelfLayout(currentShelf, q=True, cellHeight=True),
                                           ann=self.imgLabel)
            cmds.shelfButton(shelfButton, edit=True, imageOverlayLabel=self.imgLabel,
                             overlayLabelBackColor=(0.101, 0.101, 0.101, 0.3),
                             overlayLabelColor=(1.0, 0.769, 0.0))
            cmds.shelfButton(shelfButton, e=True, command=self.command, sourceType=self.sourceType)
            return
        elif modifiers == Qt.AltModifier:
            print ('assign hotkey')
            return
        return super(ToolButton, self).mousePressEvent(event)

    def sizeHint(self):
        return QSize(self.label.sizeHint().width() + self.pixmap.width() + 24,
                     max(self.label.sizeHint().height(), self.pixmap.height()) + 16)

    def paintEvent(self, event):
        QPushButton.paintEvent(self, event)

        pos_x = 5  # hardcoded horizontal margin
        pos_y = (self.height() - self.pixmap.height()) / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        if self.pixmap:
            painter.drawPixmap(pos_x, pos_y, self.pixmap)


class HotkeyToolButton(QPushButton):
    def __init__(self, text=str(), icon=str(), iconWidth=24, iconHeight=24, width=108, height=40, command=None,
                 menuBar=None, imgLabel=str(), sourceType='mel', *args, **kwargs):
        super(HotkeyToolButton, self).__init__(*args, **kwargs)
        self.icon = icon
        self.pixmap = None
        self.labelText = text
        self.sourceType = sourceType
        if width:
            self.setFixedWidth(width)
        if height:
            self.setFixedHeight(height)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QGridLayout())
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, 1)
        # pb_layout = self.layout().addWidget(self.label)
        self.setStyleSheet("background-color: transparent;border: 0px; font-size:12px;text-align:right;")
        self.label.setStyleSheet("margin-left: 64px;margin-top: 0px;")
        self.setStyleSheet(getqss.getStyleSheet())
        self.label.setStyleSheet("QLabel{background-color: transparent;text-align:right;margin-left: 20px;}")
        self.command = command
        self.menuBar = menuBar
        self.menuItem = None
        self.imgLabel = imgLabel

        if command:
            self.clicked.connect(self.evalCommand)

        if self.icon:
            self.pixmap = QPixmap(self.icon).scaled(iconWidth, iconHeight, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.pixmap = QPixmap()

    @Slot()
    def evalCommand(self):
        mel.eval(self.command)

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            currentShelf = cmds.tabLayout(pm.melGlobals['gShelfTopLevel'], query=True, selectTab=True)
            cmds.setParent(currentShelf)
            shelfButton = cmds.shelfButton(image1=self.icon,
                                           imageOverlayLabel=self.imgLabel,
                                           label=self.imgLabel,
                                           style=cmds.shelfLayout(currentShelf, q=True, style=True),
                                           width=cmds.shelfLayout(currentShelf, q=True, cellWidth=True),
                                           height=cmds.shelfLayout(currentShelf, q=True, cellHeight=True),
                                           ann=self.imgLabel)
            cmds.shelfButton(shelfButton, edit=True, imageOverlayLabel=self.imgLabel,
                             overlayLabelBackColor=(0.101, 0.101, 0.101, 0.3),
                             overlayLabelColor=(1.0, 0.769, 0.0))
            cmds.shelfButton(shelfButton, e=True, command=self.command, sourceType=self.sourceType)
            return
        if self.sourceType == 'mel':
            mel.eval(self.command)
        # return super(HotkeyToolButton, self).mousePressEvent(event)

    def sizeHint(self):
        return QSize(self.label.sizeHint().width() + self.pixmap.width() + 24,
                     max(self.label.sizeHint().height(), self.pixmap.height()) + 16)

    def paintEvent(self, event):
        QPushButton.paintEvent(self, event)

        pos_x = 5  # hardcoded horizontal margin
        pos_y = 5 + (self.height() - self.pixmap.height()) / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        if self.pixmap:
            painter.drawPixmap(pos_x, pos_y, self.pixmap)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.pixmap.width() + 12, 15, self.labelText)  # fifth option


class LockButton(MiniButton):
    lockSignal = Signal(bool)

    def __init__(self, label, parent,
                 icon='pinned_small.png',
                 unlockIcon='pin.png',
                 lockState=False,
                 toolTip='Lock UI on screen, hold control+left mouse click to move'):
        super(LockButton, self).__init__(icon=icon, toolTip=toolTip)
        self.lockState = False

        self.lockIcon = QPixmap(os.path.join(IconPath, icon))
        self.unlockIcon = QPixmap(os.path.join(IconPath, unlockIcon))

        self.clicked.connect(self.toggleLock)
        self.setLockIcon()

    def setLockIcon(self):
        if self.lockState:
            self.setIcon(self.lockIcon)
        else:
            self.setIcon(self.unlockIcon)

    def toggleLock(self, *args):
        self.lockState = not self.lockState
        self.lockSignal.emit(self.lockState)
        self.setLockIcon()


class AnimLayerTabButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon='', toolTip=''):
        super(AnimLayerTabButton, self).__init__()
        self.setIcon(QIcon(":/{0}".format(icon)))
        self.setFixedSize(18, 18)
        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)
        self.pop_up_window = None

    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)

            self.pop_up_window.show()


sliderStylesheet = """


QSlider::groove:horizontal {
border: 1px solid #bbb;
background: transparent;
height: 4;
border-radius: 4px;
}

QSlider::sub-page:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2:1, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #66e, stop: 1 #bbf);
border: 1px solid #2d2d2d;
height: 4;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::add-page:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);
border: 1px solid #2d2d2d;
height: 4px;
margin-top: -2px; 
margin-bottom: -2px; 
border-radius: 2px;
}

QSlider::handle:horizontal {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
border: 2px solid #444;
width: 16px; 
height: 16px; 
line-height: 20px; 
margin-top: -8px; 
margin-bottom: -8px; 
border-radius: 8px; 
image: url(":greasePencilPreGhostOff.png");
}

QSlider::handle:horizontal:hover {
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
border: 2px solid #777;
}

QSlider::sub-page:horizontal:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:horizontal:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:horizontal:disabled {
background: #eee;
border: 1px solid #aaa;
border-radius: 4px;
"""

buttonSS = """
QPushButton {
color: #333;
border: 2px solid #555;
border-radius: 6px;
border-style: outset;
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #888
);
padding: 5px;
}

QPushButton:hover {
background: qradialgradient(
cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,
radius: 1.35, stop: 0 #fff, stop: 1 #bbb
);
}
"""


class testDialog(QDialog):
    AssignNewRigSignal = Signal(str)
    CreateNewRigMapSignal = Signal(str)
    IgnoreRigSignal = Signal(str)

    def __init__(self, parent=None, title='title?', rigName=str(), text='message?',
                 assignText='Assign existing map',
                 createText='Create new map',
                 ignoreText='Ignore',
                 cancelText='Cancel',
                 ):
        super(testDialog, self).__init__(parent=parent)
        self.rigName = rigName
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(0.9)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # self.layout = QVBoxLayout()
        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.layout)

        # self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        sliderLayout = QHBoxLayout()
        sliderLayout.setContentsMargins(0, 0, 0, 0)

        leftButton = QPushButton()
        rightButton = QPushButton()
        leftButton.setStyleSheet(buttonSS)
        leftButton.setFixedSize(12, 12)
        rightButton.setStyleSheet(buttonSS)
        rightButton.setFixedSize(12, 12)
        sliderLayout.setAlignment(Qt.AlignCenter)
        sliderLayout.setSpacing(0)
        self.slider_label = QLabel()
        self.slider_label.setFixedHeight(20)
        self.slider_label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksAbove)
        self.slider.setFixedHeight(24)
        self.slider.setFixedWidth(220)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(0.1)
        self.slider.setStyleSheet(sliderStylesheet)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.sliderReleased.connect(self.slider_released)

        self.slider_label.setText(str(self.slider.value()))

        sliderLayout.addWidget(leftButton)
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(rightButton)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addWidget(self.slider_label)
        self.setLayout(mainLayout)
        self.resize(self.sizeHint())

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def move_UI(self):
        ''' Moves the UI to the widget position '''
        pos = QCursor.pos()
        self.move(pos.x() - (self.width() * 0.5), pos.y() - (self.height() * 0.5))

    def slider_changed(self):
        self.slider_label.setText(str(self.slider.value()))

    def slider_released(self):
        cmds.warning('Value is %d' % self.slider.value())

    def button_clicked(self, obj):
        self.button.setText('Clicked')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(testDialog, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


class ButtonPopup(QWidget):
    def __init__(self, name, parent=None):
        super(ButtonPopup, self).__init__(parent)

        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        pass
        self.radioGroup = radioGroupVertical(formLayout=self.layout,
                                             optionVarList=['test', 'test2', 'test3'],
                                             optionVar='testVar',
                                             defaultValue='test',
                                             label=str())

    def create_layout(self):
        for label, widget in self.radioGroup.returnedWidgets:
            self.layout.addRow("%s:" % label, widget)
        # layout.addRow("Size:", self.size_sb)
        # layout.addRow("Opacity:", self.opacity_sb)


class HotkeyPopup(ButtonPopup):
    def __init__(self, name, cls=None, parent=None, command=str(), hideLabel=False):
        super(ButtonPopup, self).__init__(parent)
        self.hideLabel = hideLabel
        self.setWindowTitle("{0} Options".format(name))
        self.cls = cls
        self.command = command
        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.hotkeyWidget = hotKeyWidget(cls=self.cls, command=self.command, text='Hotkey')
        self.hotkeyWidget.assignSignal.connect(self.cls.assignHotkey)
        self.helpLabelStr = str()
        try:
            self.helpLabel = QLabel(maya.stringTable['tbCommand.{0}'.format(self.command)].replace('__', ' '))
        except:
            self.helpLabel = QLabel(self.helpLabelStr)
        self.helpLabel.setWordWrap(True)
        self.imageGif = os.path.join(helpPath, self.command + '.gif')
        self.imageJpeg = os.path.join(helpPath, self.command + '.jpeg')
        self.imageLabel = QLabel(self)

        if os.path.isfile(self.imageGif):
            self.movie = QMovie(os.path.join(helpPath, self.imageGif))
            self.imageLabel.setMovie(self.movie)
            self.movie.start()
        elif os.path.isfile(self.imageJpeg):
            self.imagePixmap = QPixmap(os.path.join(helpPath, self.imageGif))
            self.imageLabel.setPixmap(self.imagePixmap)

    def create_layout(self):
        self.layout.addRow(self.hotkeyWidget)
        self.layout.addRow(self.helpLabel)
        self.layout.addRow(self.imageLabel)


class PluginExtractor(BaseDialog):
    installSignal = Signal(str)

    def __init__(self, parentCLS):
        super(PluginExtractor, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        self.parentCLS = parentCLS
        self.titleText.setText('tbAnimTools Plugin Extractor')
        self.titleText.setStyleSheet("font-weight: normal; font-size: 18px;")
        self.infoText.setText('Install plugins from the zip file')
        self.infoText.setAlignment(Qt.AlignCenter)

        self.btnCloseWIndow = QPushButton("Close")
        self.btnCloseWIndow.clicked.connect(partial(self.close))

        self.btnInstall = QPushButton("Install")
        self.btnInstall.clicked.connect(partial(self.install))
        self.btnInstall.setEnabled(False)

        self.filePathLayout = QHBoxLayout()
        self.pathLabel = QLabel('Install to ::')
        self.pathLineEdit = QLineEdit('')
        self.pathLineEdit.setPlaceholderText('zip file path')
        self.cle_action_pick = self.pathLineEdit.addAction(QIcon(":/folder-open.png"),
                                                           QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Select your downloaded zip file')
        self.cle_action_pick.triggered.connect(self.pickZipFile)
        self.pathLineEdit.textChanged.connect(self.pathEdited)

        self.layout.addLayout(self.filePathLayout)
        self.filePathLayout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.btnInstall)
        self.layout.addWidget(self.btnCloseWIndow)
        self.setFixedSize(self.sizeHint())

    def pathEdited(self, *args):
        self.btnInstall.setEnabled(os.path.isfile(self.pathLineEdit.text()))

    def install(self, *args):
        self.installSignal.emit(self.pathLineEdit.text())

    def pickZipFile(self, *args):
        filename, filter = QFileDialog.getOpenFileName(parent=self,
                                                       caption='Open file',
                                                       dir='.',
                                                       filter='Zip Files (*.zip)')
        if filename:
            self.pathLineEdit.setText(filename)


class OverlayContents(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.button = QPushButton("Close Overlay")
        self.button2 = QPushButton("Close Overlay")
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.button)
        self.layout().addWidget(self.button2)

        self.button.clicked.connect(self.hideOverlay)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 4, 4)
        # mask = QRegion(path.toFillPolygon().toPolygon())
        pen = QPen(Qt.white, .2)
        linePen = QPen(Qt.white, 2, Qt.SolidLine)

        painter.setPen(linePen)
        painter.drawLine(0, 0, 200, 200)

        painter.setPen(pen)
        painter.fillPath(path, Qt.white)
        painter.drawPath(path)
        painter.end()

    def hideOverlay(self):
        self.parent().hide()


class Overlay(QWidget):
    def __init__(self, parent, widget):
        QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

        self.widget = widget
        self.widget.setParent(self)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(0, 0, 0, 127)))
        painter.end()

    def resizeEvent(self, event):
        position_x = (self.frameGeometry().width() - self.widget.frameGeometry().width()) / 2
        position_y = (self.frameGeometry().height() - self.widget.frameGeometry().height()) / 2

        self.widget.move(position_x, position_y)
        event.accept()


class OfflineActivateInputWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str, str, str)

    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title='Input activation code', label=str(), buttonText=str(), default=str(),
                 overlay=False, showCloseButton=True, licenseVal=str(), emailVal=str(),
                 productStr=str(),
                 helpString=None,
                 parentWidget=None,
                 lineEditPlaceholder=str(),
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(OfflineActivateInputWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = licenseVal
        self.subKey = emailVal
        self.helpString = helpString
        self.overlay = overlay

        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        productLineEditLayout = QHBoxLayout()

        self.productLineEdit = QLineEdit(productStr)
        self.productLineEdit.setReadOnly(True)
        self.productLineEdit.setFixedWidth(400)
        self.copyToCLipButton = QPushButton('Copy to clipboard')
        productLineEditLayout.addWidget(self.productLineEdit)
        productLineEditLayout.addWidget(self.copyToCLipButton)
        self.copyToCLipButton.clicked.connect(self.copyText)

        self.infoText = QLabel(
            'Copy the above text and email to to <b>tbanimtools@gmail.com</b> to get an offline activation code. <br>'
            'Make sure your email and license key are correct. <br><br>'
            'Once you get a response code, paste it into the box below')
        self.infoText.setWordWrap(True)
        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(productLineEditLayout)
        mainLayout.addWidget(self.infoText)
        mainLayout.addLayout(layout)
        layout.addWidget(self.text)

        self.lineEdit = QLineEdit(default)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        layout.addWidget(self.lineEdit)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.show()
        self.lineEdit.setFocus()
        self.setStyleSheet(
            "TextInputWidget { "
            "border-radius: 8;"
            "}"
        )

        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.productLineEdit.sizeHint().width() + 48, self.sizeHint().height())
        self.resize(self.sizeHint())
        self.setStyleSheet(getqss.getStyleSheet())
        # self.setFixedSize(400, 64)

    def copyText(self):
        cmd = 'echo ' + self.productLineEdit.text().strip() + '|clip'
        return subprocess.check_call(cmd, shell=True)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
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
        if not len(self.lineEdit.text()) == 8:
            return cmds.warning('Wrong length for activation code')
        self.acceptedSignal.emit(self.lineEdit.text(), self.key, self.subKey)

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(OfflineActivateInputWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        return super(OfflineActivateInputWidget, self).keyPressEvent(event)

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
        super(OfflineActivateInputWidget, self).show()


class CollapsibleBox(QWidget):
    collapsedIcon = QIcon(":openBar.png")
    expandedIcon = QIcon(":closeBar.png")

    def __init__(self, title="", parent=None, isCollapsed=False, optionVar=str()):
        super(CollapsibleBox, self).__init__(parent)
        self.optionVar = optionVar
        self.toggleButton = QToolButton(
            text=title, checkable=True, checked=isCollapsed
        )
        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setFixedSize(12, 22)
        self.toggleButton.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggleButton.setIcon(
            self.collapsedIcon if not isCollapsed else self.expandedIcon
        )
        self.toggleButton.clicked.connect(self.on_pressed)

        self.toggleAnimation = QParallelAnimationGroup(self)

        self.contentArea = QScrollArea(
            maximumWidth=0, minimumWidth=0,

        )
        self.contentArea.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.contentArea.setFrameShape(QFrame.NoFrame)

        lay = QHBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggleButton)
        lay.addWidget(self.contentArea)

        anim = QPropertyAnimation(self, b"minimumWidth")
        anim.setEasingCurve(QEasingCurve.InCubic)
        self.toggleAnimation.addAnimation(
            anim
        )
        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setEasingCurve(QEasingCurve.InCubic)
        self.toggleAnimation.addAnimation(
            anim
        )
        anim = QPropertyAnimation(self.contentArea, b"maximumWidth")
        anim.setEasingCurve(QEasingCurve.OutBack)
        self.toggleAnimation.addAnimation(
            anim
        )

    def playAnimationByState(self):
        checked = self.toggleButton.isChecked()
        self.toggleAnimation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        self.toggleAnimation.start()

    @Slot()
    def on_pressed(self):
        self.setIconByState()
        self.playAnimationByState()
        self.setOptionVarByState()

    def setOptionVarByState(self):
        checked = self.toggleButton.isChecked()
        pm.optionVar[self.optionVar] = checked

    def setIconByState(self):
        checked = self.toggleButton.isChecked()
        self.toggleButton.setIcon(
            self.collapsedIcon if not checked else self.expandedIcon
        )
        return checked

    def setContentLayout(self, layout):
        lay = self.contentArea.layout()
        del lay
        self.contentArea.setLayout(layout)
        collapsed_width = 16
        content_width = layout.sizeHint().width()
        for i in range(self.toggleAnimation.animationCount()):
            animation = self.toggleAnimation.animationAt(i)
            animation.setDuration(100)
            animation.setStartValue(collapsed_width)
            animation.setEndValue(collapsed_width + content_width)

        content_animation = self.toggleAnimation.animationAt(
            self.toggleAnimation.animationCount() - 1
        )
        content_animation.setDuration(100)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_width)
        self.playAnimationByState()

    def show(self):
        super(CollapsibleBox, self).show()
        # self.playAnimationByState()


class PopupSlider(QWidget):
    sliderBeginSignal = Signal(str, float, float)
    sliderUpdateSignal = Signal(str, float, float)
    sliderEndedSignal = Signal(str, float, float)

    def __init__(self, width=400, minValue=-100, maxValue=100, overshootMin=-200, overshootMax=200,
                 closeOnRelease=False,
                 mode=str(),
                 label=str(),
                 vertical=False,
                 altMode=str(),
                 axisLabelX='',
                 axisLabelY='',
                 opacity=128,
                 icon=str()):
        super(PopupSlider, self).__init__()

        layout = QHBoxLayout()
        self.closeOnRelease = closeOnRelease
        self.mode = mode
        self.label = label
        self.vertical = vertical
        self.lastMode = None
        self.axisLabelX = axisLabelX
        self.axisLabelY = axisLabelY

        layout = QHBoxLayout()
        self.overshootState = False
        pixmap = QPixmap(os.path.join(IconPath, icon))
        self.button = QLabel('B')
        self.overlayLabelAlignment = Qt.AlignLeft
        self.button.setPixmap(pixmap.scaled(24, 24))

        self.button.setFixedSize(24, 24)
        self.setLayout(layout)
        self.margin = 2
        self.padding = 4
        self.baseWidth = width
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        layout.addWidget(self.button)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setWindowOpacity(1.0)
        if self.vertical:
            self.resize(width, width)
        else:
            self.resize(width, self.button.height() + self.padding)
        self.setFixedWidth(width)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        # self.setStyleSheet("QLabel {background-color: rgba(128, 128, 128, 128);}")
        self.button.setStyleSheet("QLabel {"
                                  "background-color: rgba(128, 128, 128, 196);"
                                  "border-radius: 6;"
                                  "border-width:2px; "
                                  "border-color: #ffa02f;}")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.currentAlpha = 0.0
        self.currentAlphaY = 0.0
        self.outAlphaY = 0.0
        self.lastAlpha = 0.0
        self.lastAlphaY = 0.0
        self.outAlpha = 0.0

        # assume pixel width of 400 (-200 <> 200 )
        self.scale = float(width) / 400.0
        self.halfWidth = width * 0.5
        self.minValue = (width * 0.25) + (self.button.width() * 0.5)
        self.maxValue = (width * 0.75) - (self.button.width() * 0.5)
        self.overshootMin = (self.button.width() * 0.5)
        self.overshootMax = (width) - (self.button.width() * 0.5) - 2.0
        self.range = self.maxValue - self.minValue
        self.overshootRange = self.overshootMax - self.overshootMin

        self.outMin = minValue
        self.outMax = maxValue
        self.outOvershootMin = overshootMin
        self.outOvershootMax = overshootMax

        self.leftBorder = (width * 0.25)
        self.rightBorder = (width * 0.75)
        self.brushOpacity = 128

        self.white = QColor(255, 255, 255, 255)
        self.text = QColor(196, 196, 196, 255)
        self.lightGrey = QColor(196, 196, 196, 255)
        self.darkGrey = QColor(64, 64, 64, self.brushOpacity)
        self.darkestGrey = QColor(32, 32, 32, 255)
        self.midGrey = QColor(128, 128, 128, 128)
        self.midGreyFaint = QColor(128, 128, 128, self.brushOpacity)
        self.background = QColor(96, 96, 96, opacity)
        self.overshootColour = QColor(128, 128, 128, 255)
        self.red = QColor(255, 0, 0, 96)
        self.clear = QColor(255, 0, 0, 0)
        self.textPen = QPen(self.text, 1, Qt.SolidLine)
        self.resetButton()

    def setIcon(self, icon):
        pixmap = QPixmap(os.path.join(IconPath, icon))
        self.button.setPixmap(pixmap.scaled(24, 24))

    def mousePressEvent(self, event):
        self.setFocus()
        self.updatePosition(event)

    def mouseMoveEvent(self, event):
        self.setFocus()
        self.updatePosition(event)

    def mapValue(self, value, inMin, inMax, outMin, outMax):
        return outMin + (value - inMin) * (outMax - outMin) / (inMax - inMin)

    def updatePosition(self, event):
        x = event.pos().x()
        y = event.pos().y()

        clampedX = min(max(x, self.minValue), self.maxValue)
        clampedY = min(max(y, self.minValue), self.maxValue)
        clampedOvershootX = min(max(x, self.overshootMin), self.overshootMax)
        clampedOvershootY = min(max(y, self.overshootMin), self.overshootMax)

        regularX = self.mapValue(clampedX, self.minValue, self.maxValue, self.outMin, self.outMax)
        overshootX = self.mapValue(clampedOvershootX, self.overshootMin, self.overshootMax, self.outOvershootMin,
                                   self.outOvershootMax)

        regularY = self.mapValue(clampedY, self.minValue, self.maxValue, self.outMin, self.outMax)
        overshootY = self.mapValue(clampedOvershootY, self.overshootMin, self.overshootMax, self.outOvershootMin,
                                   self.outOvershootMax)

        self.currentAlpha = clampedOvershootX if self.overshootState else clampedX
        self.outAlpha = overshootX if self.overshootState else regularX

        self.currentAlphaY = clampedOvershootY if self.overshootState else clampedY
        self.outAlphaY = overshootY if self.overshootState else regularY

        if self.vertical:
            self.button.move(self.currentAlpha + self.margin - self.button.width() * 0.5,
                             self.currentAlphaY + self.margin - self.button.height() * 0.5)
        else:
            self.button.move(self.currentAlpha + self.margin - self.button.width() * 0.5, self.button.pos().y())

        if self.outAlpha > self.minValue * 0.6:
            self.overlayLabelPos = self.margin + abs(self.overshootMin - self.minValue)
            self.overlayLabelAlignment = Qt.AlignLeft
        elif self.outAlpha < self.maxValue * 0.6:
            self.overlayLabelPos = 100
            self.overlayLabelAlignment = Qt.AlignRight

        self.sliderUpdateSignal.emit(self.mode, self.outAlpha, self.outAlphaY)

    def mouseReleaseEvent(self, event):
        if self.closeOnRelease:
            self.hide()

        self.sliderEndedSignal.emit(self.mode, self.outAlpha, self.outAlphaY)

        self.lastMode = str(self.mode)
        self.lastAlpha = float(self.outAlpha)
        self.lastAlphaY = float(self.outAlphaY)
        self.resetButton()
        self.outAlpha = 0.0
        self.outAlphaY = 0.0

    def resetButton(self):
        self.button.move(self.width() * 0.5 - self.button.width() * 0.5,
                         self.height() * 0.5 - self.button.height() * 0.5)

    def drawHorizontalBar(self, qp):
        leftBarPos = self.minValue
        righBarPos = self.rightBorder - self.leftBorder + 4
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setBrush(QBrush(self.midGrey))
        qp.setPen(QPen(QBrush(self.midGrey), 2))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        qp.setCompositionMode(qp.CompositionMode_Darken)
        qp.setRenderHint(QPainter.Antialiasing)

        r1 = QRegion(QRect(0, 0, self.width(), self.height()))
        r2 = QRect(self.leftBorder, 0, righBarPos, self.height())  # r2: rectangular region
        r3 = r1.subtracted(r2)
        qp.setClipRegion(r3)
        # qp.drawRect(0, 0, self.width(), self.height())

        # qp.drawLine(righBarPos, 0, righBarPos, self.height())
        # qp.drawLine(leftBarPos, 0, leftBarPos, self.height())
        qp.setBrush(QBrush(self.background))
        qp.drawRect(0, 0, self.width(), self.height())

        qp.setClipRegion(QRect(0, 0, self.width(), self.height()))

        qp.setCompositionMode(qp.CompositionMode_ColorBurn)
        qp.setPen(QPen(QBrush(self.clear), 0))
        backgroundGradient = QLinearGradient(0.0, 0.0, 0.0, self.height())
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.height(), self.clear)
        backgroundGradient.setColorAt((self.height() - 6.0) / self.height(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2, 2)

        backgroundGradient = QLinearGradient(0.0, 0.0, self.width(), 0.0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.width(), self.clear)
        backgroundGradient.setColorAt((self.width() - 6.0) / self.width(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2, 2)

        backgroundGradient = QLinearGradient(self.leftBorder, 0.0, self.rightBorder + 2, 0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.height(), self.clear)
        backgroundGradient.setColorAt((self.height() - 6.0) / self.height(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        # qp.setBrush(QBrush(self.red))
        qp.drawRoundedRect(self.leftBorder, 0, righBarPos, self.height(), 2, 2)

        lineColor = QColor(68, 68, 68, 64)
        qp.setPen(QPen(QBrush(lineColor), 0))
        qp.setBrush(QBrush(lineColor))
        qp.setCompositionMode(qp.CompositionMode_Darken)
        qp.setRenderHint(QPainter.Antialiasing)
        # qp.drawLine(righBarPos, 0, righBarPos, self.height())
        # qp.drawLine(leftBarPos, 0, leftBarPos, self.height())
        qp.setBrush(QBrush(self.darkGrey))

        path = QPainterPath()
        pen = QPen()
        brush = QBrush()
        font = QFont("Console", 11, 11, False)

        pen.setWidth(3.5)
        pen.setColor(self.text)
        brush.setColor(self.darkestGrey)
        qp.setFont(font)
        qp.setPen(pen)

        alphaStr = ' {:.2f} '.format(self.outAlpha * 0.01)

        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(alphaStr)
        pixelsHigh = fontMetrics.height()

        path.addText(0, pixelsHigh + 2, font, alphaStr)
        path.addText(leftBarPos + 2, pixelsHigh + 2, font, self.label)

        pen = QPen(self.darkGrey, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(self.white)
        qp.setCompositionMode(qp.CompositionMode_SourceOver)
        qp.strokePath(path, pen)
        qp.fillPath(path, brush)
        '''

        qp.fillPath(path, brush)
        '''
        qp.setPen(self.textPen)

        '''
        qp.drawText(leftBarPos + 2, 2, self.range + self.button.width() - self.margin - self.margin, self.height(),
                    Qt.AlignLeft, self.mode)

        qp.drawText(0, 2, self.width(), self.height(),  Qt.AlignLeft,
                    alphaStr)
        '''

    def drawBox(self, qp):
        leftBarPos = self.minValue
        righBarPos = self.rightBorder - self.leftBorder

        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setBrush(QBrush(self.midGrey))
        qp.setPen(QPen(QBrush(self.midGrey), 2))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        lineColor = QColor(68, 68, 68, 64)
        qp.setPen(QPen(QBrush(lineColor), 0))
        qp.setBrush(QBrush(lineColor))
        qp.setCompositionMode(qp.CompositionMode_Darken)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setBrush(QBrush(self.darkGrey))

        r1 = QRegion(QRect(0, 0, self.width(), self.height()))
        r2 = QRect(self.leftBorder, self.leftBorder, righBarPos, righBarPos)  # r2: rectangular region
        r3 = r1.subtracted(r2)
        qp.setClipRegion(r3)
        # qp.drawRect(0, 0, self.width(), self.height())

        # qp.drawLine(righBarPos, 0, righBarPos, self.height())
        # qp.drawLine(leftBarPos, 0, leftBarPos, self.height())
        qp.drawRect(0, 0, self.width(), self.height())

        qp.setClipRegion(QRect(0, 0, self.width(), self.height()))

        qp.setCompositionMode(qp.CompositionMode_ColorBurn)

        backgroundGradient = QLinearGradient(0.0, 0.0, 0.0, self.height())
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.height(), self.clear)
        backgroundGradient.setColorAt((self.height() - 6.0) / self.height(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2, 2)

        backgroundGradient = QLinearGradient(0.0, 0.0, self.width(), 0.0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.width(), self.clear)
        backgroundGradient.setColorAt((self.width() - 6.0) / self.width(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.setPen(QPen(QBrush(self.clear), 0))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2, 2)

        backgroundGradient = QLinearGradient(self.leftBorder, self.leftBorder, self.leftBorder, self.rightBorder)
        backgroundGradient.setColorAt(0, self.midGrey)
        backgroundGradient.setColorAt(6.0 / self.range, self.clear)
        backgroundGradient.setColorAt((self.range - 6.0) / self.range, self.clear)
        backgroundGradient.setColorAt(1, self.midGrey)
        qp.setBrush(QBrush(backgroundGradient))
        # qp.setBrush(QBrush(self.red))
        qp.drawRect(self.leftBorder, self.leftBorder, righBarPos, righBarPos)

        backgroundGradient = QLinearGradient(self.leftBorder, self.leftBorder, self.rightBorder, self.leftBorder)
        backgroundGradient.setColorAt(0, self.midGrey)
        backgroundGradient.setColorAt(6.0 / self.range, self.clear)
        backgroundGradient.setColorAt((self.range - 6.0) / self.range, self.clear)
        backgroundGradient.setColorAt(1, self.midGrey)
        qp.setBrush(QBrush(backgroundGradient))
        qp.drawRect(self.leftBorder, self.leftBorder, righBarPos, righBarPos)

        path = QPainterPath()
        pen = QPen()
        brush = QBrush()
        font = QFont("Console", 11, 11, False)

        pen.setWidth(3.5)
        pen.setColor(self.text)
        brush.setColor(self.darkestGrey)
        qp.setFont(font)
        qp.setPen(pen)

        pen.setWidth(3.5)
        pen.setColor(self.text)
        brush.setColor(self.darkestGrey)
        qp.setFont(font)
        qp.setPen(pen)

        labelStr = ' {}'.format(self.label)
        xAxisStr = ' {}'.format("{} {:.2f}".format(self.axisLabelX, self.outAlpha * 0.01))
        yAxisStr = ' {}'.format("{} {:.2f}".format(self.axisLabelY, self.outAlphaY * -0.01))

        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(xAxisStr)
        pixelsHigh = fontMetrics.height()

        path.addText(0, pixelsHigh + 2, font, labelStr)
        path.addText(0, pixelsHigh + 20, font, xAxisStr)
        path.addText(0, pixelsHigh + 38, font, yAxisStr)

        pen = QPen(self.darkGrey, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(self.white)
        qp.setCompositionMode(qp.CompositionMode_SourceOver)
        qp.strokePath(path, pen)
        qp.fillPath(path, brush)

        '''
        qp.drawText(0, pixelsHigh + 2, self.width(), 16,
                    Qt.AlignLeft | Qt.AlignTop, ' {}'.format(self.mode))
        qp.drawText(0, pixelsHigh + 20, self.width(), 16,
                    Qt.AlignLeft | Qt.AlignTop,
                    ' {}'.format("{} {:.2f}".format('self.axisLabelX', self.outAlpha * 0.01)))
        qp.drawText(0, pixelsHigh + 38, self.width(), 16, Qt.AlignLeft | Qt.AlignTop,
                    ' {}'.format("{} {:.2f}".format('self.axisLabelY', self.outAlphaY * 0.01)))
        '''

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.vertical:
            self.drawBox(qp)
        else:
            self.drawHorizontalBar(qp)

        qp.end()
        self.update()

    def moveToCursor(self):
        modifiers = QApplication.keyboardModifiers()
        self.overshootState = modifiers == Qt.ControlModifier
        pos = QCursor.pos()
        size = self.size()

        self.move(QPoint(pos.x() - (size.width() * 0.5), pos.y() - size.height() * 0.5))
        self.button.move(self.mapFromGlobal(pos).x() - self.button.width() * 0.5, self.button.pos().y())
        self.sliderBeginSignal.emit(self.mode, 0.0, 0.0)

    def keyPressEvent(self, event):
        if event.type() == event.KeyPress:
            modifiers = QApplication.keyboardModifiers()
            if event.key() == Qt.Key_Control:
                self.setOvershoot(True)

    def keyReleaseEvent(self, event):
        if event.type() == event.KeyRelease:
            modifiers = QApplication.keyboardModifiers()
            if event.key() == Qt.Key_Control:
                self.setOvershoot(False)

    def setOvershoot(self, state):
        self.overshootState = state


class ToolbarButton(QLabel):
    clicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()

    def __init__(self, icon=str(), altIcon=str(),
                 width=26,
                 height=24,
                 iconHeight=24,
                 iconWidth=26):
        super(ToolbarButton, self).__init__()
        self.tooltipState = False
        self.tooltipRaised = False
        self.icon = icon
        self.altIcon = altIcon
        self.currentIcon = icon
        self.baseWidth = width
        self.baseHeight = height
        self.iconWidth = iconWidth
        self.iconHeight = iconHeight
        self.pixmap = QPixmap(os.path.join(IconPath, icon))
        self.altPixmap = QPixmap(os.path.join(IconPath, altIcon))
        self.setPixmap(self.pixmap.scaled(self.iconWidth, self.iconHeight))
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFixedSize(self.baseWidth, self.baseHeight)
        self.setStyleSheet(getqss.getStyleSheet())
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)
        self.shiftState = False
        self.altState = False
        self.controlState = False
        self.hoverState = False
        self.pop_up_window = None
        # self.setPopupMenu(SliderButtonPopupMenu)
        self.helpWidget = InfoPromptWidget(title='Some helpful thing',
                                           buttonText='Ok',
                                           imagePath='',
                                           error=False,
                                           image='',
                                           gif='',
                                           helpString='Test help string',
                                           showCloseButton=False,
                                           show=False,
                                           showButton=False)

    def keyPressEvent(self, event):
        self.tooltipState = self.getTooltipState()
        if event.key() == Qt.Key_Shift:
            self.shiftState = True
            self.currentIcon = self.altIcon
            self.setPixmap(self.altPixmap.scaled(self.iconWidth, self.iconHeight))
        if event.key() == Qt.Key_Alt:
            self.altState = True
        if event.key() == Qt.Key_Control:
            self.controlState = True

        self.raiseToolTip()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shiftState = False
            self.currentIcon = self.icon
            self.setPixmap(self.pixmap.scaled(self.iconWidth, self.iconHeight))
        if event.key() == Qt.Key_Control:
            self.controlState = False
        if event.key() == Qt.Key_Alt:
            self.altState = False

        self.hideToolTip()

    def raiseToolTip(self):
        if not self.getTooltipState():
            return
        if not self.hoverState:
            return
        if self.tooltipRaised:
            return
        self.tooltipRaised = True
        # + QPoint(0, self.height())
        self.helpWidget.showRelative(screenPos=self.mapToGlobal(self.pos()), widgetSize=self.size())

    def hideToolTip(self):
        if self.getTooltipState():
            return
        if not self.tooltipRaised:
            return
        self.tooltipRaised = False
        self.helpWidget.hide()

    def getTooltipState(self):
        if self.altState and self.controlState:
            return True
        else:
            return False

    def mouseMoveEvent(self, event):
        if self.getTooltipState():
            if self.tooltipRaised:
                return
            self.tooltipRaised = True

    def enterEvent(self, event):
        self.hoverState = True
        return super(ToolbarButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.hoverState = False
        return super(ToolbarButton, self).enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            return
        if event.button() == Qt.MiddleButton:
            self.middleClicked.emit()
            return
        return
        if event.button() == Qt.RightButton:
            modifiers = QApplication.keyboardModifiers()

            if not modifiers == Qt.ControlModifier:
                self.rightClicked.emit()
                return
            return

    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)

            self.pop_up_window.show()


class ButtonWidget(QWidget):
    def __init__(self, closeOnRelease=False,
                 sliderData=dict(),
                 altSliderData=dict(),
                 mode=str(), altMode=str(),
                 sliderIsDual=False,
                 altSliderIsDual=False,
                 toolTipSmall=str(),
                 icon=str(), altIcon=str()):
        super(ButtonWidget, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.setToolTip("%s<br>Hold <b>Ctrl+Alt</b> for info" % toolTipSmall)
        self.icon = sliderData['icon']
        self.altIcon = altSliderData['icon']

        self.button = ToolbarButton(icon=self.icon, altIcon=self.altIcon)

        self.setLayout(layout)
        layout.addWidget(self.button)

        self.setMouseTracking(True)
        self.popup = PopupSlider(**sliderData)
        self.altPopup = PopupSlider(**altSliderData)
        self.button.clicked.connect(self.raisePopup)
        self.button.middleClicked.connect(self.repeatLast)
        # self.button.rightClicked.connect(self.raisePopup)
        self.popup.sliderEndedSignal.connect(self.resetCursor)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        pos = QCursor.pos()
        size = self.sizeHint() * 0.5
        self.cachedCursorPos = QPoint(0, 0)
        self.move(pos.x() - size.width(), pos.y() - size.height())

    def keyPressEvent(self, event):
        self.button.keyPressEvent(event)
        self.popup.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.button.keyReleaseEvent(event)
        self.popup.keyReleaseEvent(event)

    def raisePopup(self):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            popup = self.altPopup
        else:
            popup = self.popup
        popup.setIcon(self.button.currentIcon)
        popup.show()
        popup.setFocus()

        pos = self.mapToGlobal(self.pos())
        screenPos = self.mapToGlobal(self.button.pos())
        pos = (self.button.pos())
        self.cachedCursorPos = QPoint(screenPos.x() + (self.button.width() * 0.5),
                                      screenPos.y() + (self.button.height() * 0.5))
        QCursor.setPos(self.cachedCursorPos)
        popup.moveToCursor()

    def resetCursor(self, *args):
        QCursor.setPos(self.cachedCursorPos)

    def repeatLast(self):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            if not self.altPopup.lastMode:
                return
            self.altPopup.sliderBeginSignal.emit(self.altPopup.lastMode, self.altPopup.lastAlpha,
                                                 self.altPopup.lastAlphaY)
            self.altPopup.sliderUpdateSignal.emit(self.altPopup.lastMode, self.altPopup.lastAlpha,
                                                  self.altPopup.lastAlphaY)
            self.altPopup.sliderEndedSignal.emit(self.altPopup.lastMode, self.altPopup.lastAlpha,
                                                 self.altPopup.lastAlphaY)
        else:
            if not self.popup.lastMode:
                return
            self.popup.sliderBeginSignal.emit(self.popup.lastMode, self.popup.lastAlpha, self.popup.lastAlphaY)
            self.popup.sliderUpdateSignal.emit(self.popup.lastMode, self.popup.lastAlpha, self.popup.lastAlphaY)
            self.popup.sliderEndedSignal.emit(self.popup.lastMode, self.popup.lastAlpha, self.popup.lastAlphaY)

    def setPopupMenu(self, menuClass):
        self.button.setPopupMenu(menuClass)


class SliderButtonPopupMenu(ButtonPopup):
    def __init__(self, name, parent=None):
        super(ButtonPopup, self).__init__(parent)

        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.radioGroup = radioGroupVertical(formLayout=self.layout,
                                             tooltips=['example 1',
                                                       'example 2'],
                                             optionVarList=['example 1',
                                                            'example 2'],
                                             optionVar='test_variable',
                                             defaultValue="Simple",
                                             label=str())

    def create_layout(self):
        tbAdjustmentBlendLabel = QLabel('slider popup menu')
        rootOptionLabel = QLabel('example options')
        self.layout.addRow(tbAdjustmentBlendLabel)
        self.layout.addRow(rootOptionLabel)
        for label, widget in self.radioGroup.returnedWidgets:
            self.layout.addRow(widget)


class DropShadowLabel(QLabel):

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        lineColor = QColor(32, 32, 32, 32)
        fillColor = QColor(198, 198, 198)
        path = QPainterPath()
        pen = QPen()
        brush = QBrush()
        font = QFont("Console", 10, 10, False)

        pen.setWidth(3.5)
        pen.setColor(lineColor)
        brush.setColor(fillColor)
        qp.setFont(font)
        qp.setPen(pen)

        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(self.text())
        pixelsHigh = fontMetrics.height()

        path.addText(0, pixelsHigh, font, self.text())

        pen = QPen(lineColor, 6.5, Qt.SolidLine, Qt.RoundCap)
        pen2 = QPen(lineColor, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(fillColor)
        qp.setCompositionMode(qp.CompositionMode_SourceOver)
        qp.strokePath(path, pen)
        qp.strokePath(path, pen2)
        qp.fillPath(path, brush)
        qp.end()
