from . import *

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
                         position=(pop_up_pos.x() - 355, pop_up_pos.y() - 105),
                         rgbValue=[x / 255 for x in self.colourRGB])
        if cmds.colorEditor(query=True, result=True):
            values = cmds.colorEditor(query=True, rgb=True)
            # print 'RGB = ' + str(values)
            self.colourChangedSignal.emit(self.labelText, values[0], values[1], values[2])
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
        self.setFixedHeight(22 * dpiScale())
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)

        self.label = DropShadowLabel(label)
        self.label.setStyleSheet("background-color:transparent")
        font = defaultFont()
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
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 8 * dpiScale(), 8 * dpiScale())

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
        self.setFixedSize(128 * dpiScale(), 22 * dpiScale())
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

