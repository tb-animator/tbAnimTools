from . import *

class ToolTipPushButton(QPushButton):
    def __init__(self, text, tooltipTitle='', tooltip='', **kwargs):
        super(ToolTipPushButton, self).__init__(text, **kwargs)
        self.helpWidget = None
        self.helpWidget = InfoPromptWidget(title=tooltipTitle,
                                           buttonText='Ok',
                                           imagePath='',
                                           error=False,
                                           image='',
                                           gif='',
                                           helpString=tooltip,
                                           showCloseButton=False,
                                           show=False,
                                           showButton=False)
        self.setToolTipClass(self.helpWidget)

    def setToolTipClass(self, cls):
        if cls:
            self.helpWidget = cls
            self.installEventFilter(self)

    def showRelativeToolTip(self):
        if not self.helpWidget:
            return

        self.helpWidget.showRelative(screenPos=self.mapToGlobal(QPoint(0, 0)), widgetSize=self.size())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            self.showRelativeToolTip()
            return True
        return super(ToolTipPushButton, self).eventFilter(obj, event)

    def enterEvent(self, event):
        if self.helpWidget:
            self.helpWidget.hide()
        return super(ToolTipPushButton, self).enterEvent(event)

    def leaveEvent(self, event):
        if self.helpWidget:
            self.helpWidget.hide()
        return super(ToolTipPushButton, self).leaveEvent(event)


class MiniButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon=baseIconFile, toolTip='Close'):
        super(MiniButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(18 * dpiScale(), 18 * dpiScale())

        pixmap = QPixmap(os.path.join(IconPath, icon))
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())


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
        pixmap = QPixmap(os.path.join(IconPath, icon)).scaled(18 * dpiScale(), 18 * dpiScale())

        self.setIcon(pixmap)
        self.setFixedSize(18 * dpiScale(), 18 * dpiScale())
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


class GraphToolbarButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon='',
                 toolTip=dict(),
                 width=24,
                 height=24,
                 tint='#222936',
                 tintStrength=0.5,):
        super(GraphToolbarButton, self).__init__()
        pixmap = QPixmap(os.path.join(IconPath, icon)).scaled(28 * dpiScale(optionName='tbCustomGeDpiScale'),
                                                              28 * dpiScale(optionName='tbCustomGeDpiScale'))
        self.setIcon(pixmap)
        self.setFixedSize(width * dpiScale(optionName='tbCustomGeDpiScale'),
                          height * dpiScale(optionName='tbCustomGeDpiScale'))
        self.setToolTip(toolTip.get('title', 'toolTipText'))
        self.setFlat(True)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)
        self.pop_up_window = None
        self.tintStrength = tintStrength

        if self.graphicsEffect() is None:
            self.effect = QGraphicsColorizeEffect(self)
            self.effect.setStrength(0.0)
            self.setGraphicsEffect(self.effect)
            # print ('tint', tint)
            rgbColour = QColor(*hex_to_rgb(tint))
            self.effect.setColor(rgbColour)
            self.setGraphicsEffect(self.effect)

        self.helpWidget = InfoPromptWidget(title=toolTip.get('title', 'toolTipText'),
                                           buttonText='Ok',
                                           imagePath='',
                                           error=False,
                                           image='',
                                           gif=toolTip.get('gif', ''),
                                           helpString=toolTip.get('text', 'toolTipText'),
                                           showCloseButton=False,
                                           show=False,
                                           showButton=False)

        self.setMouseTracking(True)
        self.installEventFilter(self)

    def raiseToolTip(self):
        if not self.getTooltipState():
            return
        if not self.hoverState:
            return
        if self.tooltipRaised:
            return
        self.tooltipRaised = True
        # + QPoint(0, self.height())
        self.helpWidget.showRelative(screenPos=self.mapToGlobal(QPoint(0,0)), widgetSize=self.size())

    def showRelativeToolTip(self):
        self.helpWidget.showRelative(screenPos=self.mapToGlobal(QPoint(0,0)), widgetSize=self.size())

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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            self.showRelativeToolTip()
            return True
        return super(GraphToolbarButton, self).eventFilter(obj, event)

    def enterEvent(self, event):
        # print (self, 'enterEvent')
        self.hoverState = True

        self.graphicsEffect().setStrength(self.tintStrength)
        self.helpWidget.hide()
        return super(GraphToolbarButton, self).enterEvent(event)

    def leaveEvent(self, event):
        # print(self, 'leaveEvent')
        self.hoverState = False

        self.graphicsEffect().setStrength(0.0)
        self.helpWidget.hide()
        return super(GraphToolbarButton, self).leaveEvent(event)

    def setPopupMenu(self, menuClass):
        self.pop_up_window = menuClass('name', self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showMenu)

    def _showMenu(self, pos):
        pop_up_pos = self.mapToGlobal(QPoint(8, self.height() + 8))
        if self.pop_up_window:
            self.pop_up_window.move(pop_up_pos)

            self.pop_up_window.show()


class HelpButton(QPushButton):
    def __init__(self, toolTip='Help', width=32, height=32):
        super(HelpButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(width * dpiScale(), height * dpiScale())

        pixmap = QPixmap(":/help.png")
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())


class SimpleIconButton(QPushButton):
    def __init__(self, toolTip='Save', text='blank', width=32, height=32, icon=":/save.png"):
        super(SimpleIconButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        # self.setFixedSize(width, height)

        pixmap = QPixmap(icon)
        icon = QIcon(pixmap)

        self.setIcon(icon)
        self.setText(text)
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
            self.setFixedWidth(width * dpiScale())
        if height:
            self.setFixedHeight(height * dpiScale())
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
            currentShelf = cmds.tabLayout(mel.eval('$temp=$gShelfTopLevel'), query=True, selectTab=True)
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
            # print('assign hotkey')
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
            currentShelf = cmds.tabLayout(mel.eval('$temp=$gShelfTopLevel'), query=True, selectTab=True)
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


class ToolboxButton(QPushButton):
    hoverSignal = Signal(object)
    colourChangedSignal = Signal(str, float, float, float)
    commandExecutedSignal = Signal()

    def __init__(self, label, parent, cls=None, icon=str(), command=None, closeOnPress=True, popupSubMenu=False,
                 subMenuClass=None,
                 subMenu=None,
                 iconWidth=24, iconHeight=24,
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
        self.darkColour = QColor(0.0, 0.0, 0.0)
        self.textColour, self.isLight = getColourBasedOnRGB(colour, self.lightColour, self.darkColour)
        self.executeOnHover = True
        self.subMenu = subMenu  # sub menu instance
        self.subMenuClass = subMenuClass  # sub menu class for button
        self.setFixedSize(48 * dpiScale(), 22 * dpiScale())
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
        fontWidth = self.fontMetrics().boundingRect(self.text()).width() + (16 * dpiScale())
        fontHeight = self.fontMetrics().boundingRect(self.text()).height() + (8 * dpiScale())

        if fixedWidth:
            fontWidth = fixedWidth + (24 * dpiScale())
        if icon:
            fontWidth += (iconWidth * dpiScale())
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
            self.setFixedSize(22 * dpiScale(), 22 * dpiScale())
        else:
            minVal = 32 * dpiScale()
            scaleVar = 64.0 * dpiScale()
            maxVal = ((fontWidth / scaleVar) * scaleVar) + scaleVar
            self.setFixedSize(max(minVal, maxVal), fontHeight)
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
        pop_up_pos = self.mapToGlobal(QPoint(8 * dpiScale(), self.height() + 8 * dpiScale()))
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
        self.borderWidth = 1 * dpiScale()
        self.setStyleSheet("ToolboxButton {"
                           "text-align:left;"
                           "background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #222936, stop: 0.1 #222936, stop: 0.5 #222936, stop: 0.9 #222936, stop: 1 #222936);"
                           "border-color: #ffa02f}"
                           )
        self.textColour, self.isLight = getColourBasedOnRGB(hex_to_rgb('#222936'), self.lightColour, self.darkColour)

    def setNonHoverSS(self):
        self.borderColour = QColor(30, 30, 30)
        self.borderWidth = 1 * dpiScale()
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
        # qp.setCompositionMode(QPainter.CompositionMode_Source)
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
        font = defaultFont()
        pen.setColor(lineColor)
        pen.setWidth(3.5)

        brush.setColor(fillColor)
        qp.setFont(font)
        qp.setPen(pen)
        textPos = QPoint(8, 0)
        if self.pixmap:
            textPos.setX(self.pixmap.width() + textPos.x())
        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.boundingRect(self.labelText).width()
        pixelsHigh = fontMetrics.height()

        path.addText(textPos.x(), pixelsHigh, font, self.labelText)

        pen = QPen(lineColor, 6.5, Qt.SolidLine, Qt.RoundCap)
        pen2 = QPen(lineColor, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(self.textColour)

        if self.isLight:
            qp.setCompositionMode(QPainter.CompositionMode_ColorBurn)
        else:
            qp.setCompositionMode(QPainter.CompositionMode_ColorDodge)
        qp.strokePath(path, pen)
        qp.strokePath(path, pen2)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
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


class ReturnButton(QPushButton):
    hoverSignal = Signal(object)

    def __init__(self, label, parent, cls=None, closeOnPress=True, radial=False):
        super(ReturnButton, self).__init__(label, parent)
        self.setIcon(QIcon(':\polySpinEdgeBackward.png'))
        self.setFixedSize(32 * dpiScale(), 32 * dpiScale())
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


class ToolbarButton(QLabel):
    clicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()

    def __init__(self, icon=str(), altIcon=str(),
                 width=30,
                 height=30,
                 iconHeight=30,
                 iconWidth=30):
        super(ToolbarButton, self).__init__()
        self.tooltipState = False
        self.tooltipRaised = False
        self.icon = icon
        self.altIcon = altIcon
        self.currentIcon = icon
        self.baseWidth = width
        self.baseHeight = height
        self.iconWidth = iconWidth * dpiScale()
        self.iconHeight = iconHeight * dpiScale()
        self.pixmap = QPixmap(os.path.join(IconPath, icon))
        self.altPixmap = QPixmap(os.path.join(IconPath, altIcon))
        self.setPixmap(self.pixmap.scaled(self.iconWidth, self.iconHeight))
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # self.setStyleSheet(getqss.getStyleSheet())

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
        self.setFixedSize(self.baseWidth * dpiScale(), self.baseHeight * dpiScale())
        self.installEventFilter(self)

        self.effect = QGraphicsColorizeEffect(self)
        self.effect.setStrength(0.0)
        self.effect.setColor(QColor('silver'))
        self.setGraphicsEffect(self.effect)

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

        # self.raiseToolTip()

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

    def showRelativeToolTip(self):
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
        # print ('enterEvent')
        self.hoverState = True

        self.graphicsEffect().setStrength(0.5)
        self.helpWidget.hide()
        return super(ToolbarButton, self).enterEvent(event)

    def leaveEvent(self, event):
        # print('leaveEvent')
        self.hoverState = False

        self.graphicsEffect().setStrength(0.0)
        self.helpWidget.hide()
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
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            self.showRelativeToolTip()
            return True
        return super(ToolbarButton, self).eventFilter(obj, event)

    def show_custom_tooltip(self):
        self.customTooltip.show()
        self.customTooltip.move(self.mapToGlobal(QPoint(8, self.height() + 8)))
