from . import *

class ViewportDialog(QDialog):
    closeSignal = Signal()
    keyReleasedSignal = Signal()

    def __init__(self, parent=getMainWindow(), parentMenu=None, menuDict=dict(),
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
        self.centralRadius = 16 * dpiScale()
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
        self.mainLayout.setContentsMargins(margin, margin, margin, margin)
        if self.parentMenu:
            self.invokedKey = self.parentMenu.invokedKey
            self.returnButton = ReturnButton(label='', parent=self, cls=self)
            self.returnButton.hoverSignal.connect(self.returnButtonHovered)
            # print ('parent pos', self.parentMenu.cursorPos)
            distance = self.distance(self.cursorPos, self.parentMenu.cursorPos)
            delta = self.parentMenu.cursorPos - self.cursorPos
            delta = om2.MVector(delta.x(), delta.y(), 0).normal()

            self.returnButton.move(self.parentMenu.cursorPos.x() - (self.returnButton.width() * 0.5),
                                   self.parentMenu.cursorPos.y() - (self.returnButton.height() * 0.5))

        else:
            self.keyPressHandler = markingMenuKeypressHandler(UI=self)
            self.app.installEventFilter(self.keyPressHandler)
        self.tooltipEnabled = True

    def returnButtonHovered(self):
        print('returnButtonHovered')

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
            self.cursorPos = QCursor.pos()
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
        if self.parentMenu:
            self.parentMenu.scaleOpacity()
        super(ViewportDialog, self).show()
        # print (cmds.timerX() - t)

    def hide(self):
        # print ('being hidden', self)
        super(ViewportDialog, self).hide()

    def resetOpacity(self):
        self.setWindowOpacity(1.0)

    def scaleOpacity(self, factor=0.8):
        opacity = self.windowOpacity() * factor
        opacity = min(max(opacity, 0.2), 1)
        self.setWindowOpacity(opacity)

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
        self.parentMenu.resetOpacity()
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

        qp.setPen(QPen(QBrush(lineColor), 2 * dpiScale()))
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
        qp.drawRoundedRect(self.rect(), 8 * dpiScale(), 8 * dpiScale())

        # subtle central shadow
        shadowGrad = QRadialGradient(self.cursorPos, 200)
        shadowGrad.setColorAt(0, centralColour)
        shadowGrad.setColorAt(0.2, centralColourMid)
        shadowGrad.setColorAt(1, centralColourFade)
        qp.setPen(QPen(QBrush(empty), 0))
        qp.setBrush(QBrush(shadowGrad))
        qp.drawEllipse(self.cursorPos.x() - (300 * dpiScale()),
                       self.cursorPos.y() - (300 * dpiScale()),
                       600 * dpiScale(),
                       600 * dpiScale())

        # central dot
        qp.setBrush(QBrush(lineColor))
        qp.drawEllipse(self.cursorPos.x() - self.centralRadius / 2,
                       self.cursorPos.y() - self.centralRadius / 2,
                       self.centralRadius,
                       self.centralRadius)
        # print (self.currentCursorPos.x(), self.currentCursorPos.y())

        if self.activeButton:
            qp.setPen(QPen(QBrush(linePenColor), 4 * dpiScale()))
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




