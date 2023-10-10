import pymel.core as pm
import os
import re

qtVersion = pm.about(qtVersion=True)
QTVERSION = int(qtVersion.split('.')[0])
if QTVERSION < 5:
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

from apps.tb_UI import intFieldWidget, dpiScale, ToolbarButton, IconPath, ButtonPopup, radioGroupVertical

sliderStyleSheet = """
QSlider {{ margin: 0px; }}
QSlider::groove:horizontal {{
    height: {_bg_height}px;
    margin: 0px;
    background-color: {_bg_color};
    border: 1px solid #2d2d2d;
    border-radius: {_bg_radius}px;
}}
QSlider::groove:horizontal:hover {{ 
    height: {_bg_height}; 
    background-color: {_bg_color_hover}; 
    }}
QSlider::handle:horizontal {{
    background-color: {_handle_color};
    border: none;
    height: {_handle_height}px;
    width: {_handle_width}px;
    margin: {_handle_margin}px;
    border-radius: {_handle_radius}px;
    image: url("{_icon}");
}}
QSlider::handle:horizontal:hover {{ background-color: {_handle_color_hover}; }}
QSlider::handle:horizontal:pressed {{  background-color: {_handle_color_pressed}; }}

"""

overShootSliderStyleSheet = """
QSlider {{ margin: 0px;
 height: 20px;
 border: 1px solid #343B48;
 border-radius: 5px;
 }}
QSlider::handle:horizontal {{
    background-color: rgb(189, 147, 249);
    border: none;
    height: 20px;
    width: 20px;
    margin: 0px;
    border-radius: 5px;
    image: url(":greasePencilPreGhostOff.png");
}}
QSlider::handle:horizontal:hover {{
    background-color: rgb(195, 155, 255);
}}
QSlider::handle:horizontal:pressed {{

    background-color: rgb(255, 121, 198);
}}

QSlider::groove:vertical {{
    border-radius: 5px;
    width: 10px;
    margin: 0px;
    background-color: rgb(52, 59, 72);
}}
QSlider::groove:vertical:hover {{
    background-color: rgb(55, 62, 76);
}}
QSlider::handle:vertical {{
    background-color: rgb(189, 147, 249);
    border: none;
    height: 10px;
    width: 10px;
    margin: 0px;
	border-radius: 5px;
}}
QSlider::handle:vertical:hover {{
    background-color: rgb(195, 155, 255);
}}
QSlider::handle:vertical:pressed {{
    background-color: rgb(255, 121, 198);
}}
}}
"""

overShootSliderStyleSheetBar = """
QSlider::groove:horizontal {{
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, 
stop: 0 {baseColour}, 
stop: {stop1} {barColour}, 
stop: {stop2} {barColour}, 
stop: {stop3} {baseColour}, 
stop: {stop4} {baseColour}, 
stop: {stop5} {barColour}, 
stop: {stop6} {barColour}, 
stop: 1 {baseColour});
    height: 20px;
	margin: 0px;
}}
QSlider::groove:horizontal:hover {{
background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, 
stop: 0 {hoverColour}, 
stop: {stop1} {barColour}, 
stop: {stop2} {barColour}, 
stop: {stop3} {hoverColour}, 
stop: {stop4} {hoverColour}, 
stop: {stop5} {barColour}, 
stop: {stop6} {barColour}, 
stop: 1 {hoverColour});
}}
"""

buttonStyle = """
QPushButton:: {{
    background-color: rgba(255, 121, 198, 0);
}}
"""
labelStyle = """
QLabel:: {{
    border-radius: 8px;
    background-color: rgba(255, 255, 255, 255);
}}
"""
buttonStyleSheet = '''
    QLabel {{
        border: none;
        background-color: rgba(0, 0, 0, 45%); /* Semi-transparent background on hover */
        border-radius: {_radius}px; /* Half of the button size for round shape */
    }}
    QLabel:hover {{
        background-color: rgba(0, 0, 0, 20%); /* Semi-transparent background on hover */
    }}
    '''


class StyledButtonDemo(QLabel):
    clickedSignal = Signal(int)
    releasedSignal = Signal()

    def __init__(self, increment=0, radius=16):
        super(StyledButtonDemo, self).__init__()
        self.radius = radius
        self.icon = QPixmap(os.path.join(IconPath, 'sliderButton.png')).scaled(2 * self.radius * dpiScale(),
                                                                               2 * self.radius * dpiScale())
        self.blankIcon = QPixmap()
        self.increment = increment

        self.HoverlineColor = QColor(128, 255, 128, 128)
        self.NonHoverlineColor = QColor(128, 128, 128, 128)

        self.initUI()

    def initUI(self):
        # Create a QPushButton

        self.setPixmap(self.icon.scaled(2 * self.radius * dpiScale(), 2 * self.radius * dpiScale()))
        #self.setMask(self.icon.mask())
        # self.setIcon(QIcon(':tag.png'))  # Replace 'icon.png' with your icon file
        # self.setIconSize(QSize(16, 16))  # Set the icon size as needed
        self.setFixedSize(2 * self.radius * dpiScale(), 2 * self.radius * dpiScale())  # Set the button size as needed
        #print(buttonStyleSheet.format(_radius=self.radius * dpiScale()))
        #self.setStyleSheet(buttonStyleSheet.format(_radius=self.radius * dpiScale() // 1))
        self.setAttribute(Qt.WA_TranslucentBackground)

    def hideIcon(self):
        self.setPixmap(self.blankIcon.scaled(2 * self.radius * dpiScale(), 2 * self.radius * dpiScale()))

        # self.setPixmap(self.blankIcon)
        # self.setMask(self.blankIcon.mask())

    def showIcon(self):
        self.setPixmap(self.icon.scaled(2 * self.radius * dpiScale(), 2 * self.radius * dpiScale()))

        # self.setPixmap(self.icon)
        # self.setMask(self.icon.mask())

    # def enterEvent(self, event):
    #     # self.setHoverSS()
    #     self.setHoverTint()
    #     return super(StyledButtonDemo, self).enterEvent(event)
    #
    # def leaveEvent(self, event):
    #     self.setNoTint()
    #     return super(StyledButtonDemo, self).enterEvent(event)
    #
    # def setHoverTint(self):
    #     self.innerLineColour = self.HoverlineColor
    #     self.update()
    #
    # def setNoTint(self):
    #     self.innerLineColour = self.NonHoverlineColor
    #     self.update()
    #
    # def setTintEffect(self):
    #     if self.graphicsEffect() is None:
    #         self.effect = QGraphicsColorizeEffect(self)
    #         self.effect.setStrength(0.6)
    #         self.setGraphicsEffect(self.effect)

class Slider(QSlider):
    wheelSignal = Signal(float)
    sliderBeginSignal = Signal(str, float, float)
    sliderUpdateSignal = Signal(str, float, float)
    sliderEndedSignal = Signal(str, float, float)

    def __init__(self,
                 label=str(),
                 margin=0,
                 bg_height=36,
                 bg_radius=10,
                 bg_color="#1b1e23",
                 bg_color_hover="#1e2229",
                 handle_margin=2,
                 handle_height=18,
                 handle_width=18,
                 handle_radius=9,
                 handle_color="#568af2",
                 handle_color_hover="#6c99f4",
                 handle_color_pressed="#3f6fd1",
                 minValue=-100,
                 minOvershootValue=-200,
                 maxValue=100,
                 maxOvershootValue=200,
                 icon=str()
                 ):
        super(Slider, self).__init__()
        # label used for mode
        self.label = label
        print ('icon', icon)
        self.handle_icon = QIcon(icon)  # Change this to the path of your handle icon

        self.setFixedHeight(bg_height * dpiScale())
        adjust_style = sliderStyleSheet.format(
            _margin=margin * dpiScale(),
            _bg_height=bg_height * dpiScale(),
            _bg_radius=bg_radius * dpiScale(),
            _bg_color=bg_color,
            _bg_color_hover=bg_color_hover,
            _handle_margin=handle_margin * dpiScale(),
            _handle_height=handle_height * dpiScale(),
            _handle_width=handle_width * dpiScale(),
            _handle_radius=handle_radius * dpiScale(),
            _handle_color=handle_color,
            _handle_color_hover=handle_color_hover,
            _handle_color_pressed=handle_color_pressed,
            _icon = icon
        )

        self.handle_width = handle_width * 0.5 * dpiScale()
        self.handle_margin = handle_margin * dpiScale()
        self.bg_radius = bg_radius * dpiScale()
        self.buttonRadiusOffset = bg_radius * dpiScale() // 2
        self.buttonValues = [-100, -75, -50, -25, 25, 50, 75, 100]
        self.buttonPositions = [0, 12.5, 25, 37.5, 62.5, 75, 87.5, 100]
        self.increment = 25
        self.incrementButtons = list()

        for x, p in zip(self.buttonValues, self.buttonPositions):
            print('adding button')
            # Create buttons inside the slider
            button = StyledButtonDemo(x, radius=bg_radius)
            # Set parent widget for buttons to be the custom slider
            button.setParent(self)
            #button.setStyleSheet(buttonStyle)
            button.position = p
            button.value = x
            button.hide()
            # button.clickedSignal.connect(self.buttonPressed)
            # button.installEventFilter(self)
            # button.releasedSignal.connect(self.buttonReleased)
            self.incrementButtons.append(button)

        self.overShootButtonValues = [-200, -175, -150, -125, -100, -75, -50, -25, 25, 50, 75, 100, 125, 150, 175, 200]
        self.overShootButtonPositions = [0.0, 6.25, 12.5, 18.75, 25.0, 31.25, 37.5, 43.75, 56.25, 62.5, 68.75, 75.0,
                                         81.25, 87.5, 93.75, 100.0]
        self.overShootIncrement = 25
        self.overShootIncrementButtons = list()

        for x, p in zip(self.overShootButtonValues, self.overShootButtonPositions):
            print('adding button')
            # Create buttons inside the slider
            button = StyledButtonDemo(x, radius=bg_radius)
            # Set parent widget for buttons to be the custom slider
            button.setParent(self)
            #button.setStyleSheet(buttonStyle)
            button.position = p
            button.value = x
            button.hide()
            # button.clickedSignal.connect(self.buttonPressed)
            # button.installEventFilter(self)
            # button.releasedSignal.connect(self.buttonReleased)
            self.overShootIncrementButtons.append(button)

        self.adjust_style = adjust_style
        self.setStyleSheet(self.adjust_style)
        self.initialStyle = self.styleSheet()
        self.setOrientation(Qt.Horizontal)

        self.minValue = minValue
        self.minOvershootValue = minOvershootValue
        self.maxValue = maxValue
        self.maxOvershootValue = maxOvershootValue

        self.setMinimum(-100)
        self.setMaximum(100)

        self.overshootState = False

        # self.setPopupMenu(SliderButtonPopup)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.arrangeButtons()
        self.setValue(0)
        self.setSingleStep(1)

        self.sliderPressed.connect(self.sliderPressedEvent)
        self.sliderMoved.connect(self.sliderMovedEvent)
        self.sliderReleased.connect(self.sliderReleasedEvent)

        self.dragged_button = None
        self.buttonState = False

        # copied from popupslider
        self.brushOpacity = 128

        self.white = QColor(255, 255, 255, 255)
        self.text = QColor(196, 196, 196, 255)
        self.lightGrey = QColor(196, 196, 196, 255)
        self.darkGrey = QColor(64, 64, 64, self.brushOpacity)
        self.darkestGrey = QColor(32, 32, 32, 255)
        self.midGrey = QColor(128, 128, 128, 128)
        self.midGreyFaint = QColor(128, 128, 128, self.brushOpacity)
        self.background = QColor(96, 96, 96, 128)
        self.overshootColour = QColor(128, 128, 128, 255)
        self.red = QColor(255, 0, 0, 96)
        self.clear = QColor(255, 0, 0, 0)
        self.textPen = QPen(self.text, 1, Qt.SolidLine)

    def showEvent(self, event):
        super(Slider, self).showEvent(event)
        self.showButtons()
        self.arrangeButtons()

    def paintEvent(self, event):
        super(Slider, self).paintEvent(event)
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 64)

        qp.setCompositionMode(qp.CompositionMode_ColorBurn)
        qp.setRenderHint(QPainter.Antialiasing)


        # # Draw the groove
        # self.style().drawComplexControl(self.style().CC_Slider, QStyleOptionComplex(), qp, self)
        #
        # # Draw the handle
        # handle_rect = self.style().subControlRect(self.style().CC_Slider, QStyleOptionComplex(), self.style().SC_SliderHandle, self)
        # print ('handle_rect', handle_rect)
        # pixmap = self.handle_icon.pixmap(handle_rect.size())
        # qp.drawPixmap(handle_rect, pixmap)


        if self.isSliderDown():
            self.drawTextOverlay(qp)

        if self.overshootState:
            qp.setPen(QPen(QBrush(lineColor), 0))
            qp.setBrush(QBrush(lineColor))
            leftBarPos = (self.width() * 0.25) - self.buttonRadiusOffset
            rightBarPos = (self.width() * 0.75) + self.buttonRadiusOffset
            minSize = self.minimumSizeHint()
            offset = minSize.width() * 0.5

            qp.drawLine(rightBarPos, 0, rightBarPos, self.height())
            qp.drawLine(leftBarPos, 0, leftBarPos, self.height())
            # qp.drawRect(0, 0, leftBarPos, self.height())
            # qp.drawRect(righBarPos, 0, righBarPos, self.height())

            # rounded corner thing
            # Set up the painter properties

            # Create a QPainterPath for the rounded rectangle
            path = QPainterPath()

            # Set the radius of the rounded corners
            corner_radius = self.bg_radius

            # Set the dimensions of the rectangle
            width = self.width()
            height = self.height()


            # Start at the top-left corner and draw the rounded rectangle
            path.moveTo(leftBarPos, 0)
            path.lineTo(self.bg_radius, 0)
            path.arcTo(0, 0, self.bg_radius * 2, self.bg_radius * 2 , 90, 90)
            path.lineTo(0, height-self.bg_radius)
            path.arcTo(0, height - (self.bg_radius * 2), self.bg_radius * 2, self.bg_radius * 2, 180, 90)
            path.lineTo(leftBarPos, height)
            path.closeSubpath()

            # Draw the path
            qp.fillPath(path, qp.brush())

            path.moveTo(rightBarPos, 0)
            path.lineTo(width - self.bg_radius, 0)
            path.arcTo(width - (self.bg_radius * 2), 0, self.bg_radius * 2, self.bg_radius * 2 , 90, -90)
            path.lineTo(width, height-self.bg_radius)
            path.arcTo(width - (self.bg_radius * 2), height - (self.bg_radius * 2), self.bg_radius * 2, self.bg_radius * 2, 0, -90)
            path.lineTo(rightBarPos, height)
            path.closeSubpath()

            # Draw the path
            qp.fillPath(path, qp.brush())

        qp.end()

    def drawTextOverlay(self, qp):
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
        xAxisStr = ' {}'.format("{}".format(self.getOutputValue()))

        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(xAxisStr)
        pixelsHigh = fontMetrics.height()

        path.addText(0, pixelsHigh + 2, font, labelStr)
        path.addText(0, pixelsHigh + 2, font, xAxisStr)

        pen = QPen(self.darkGrey, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(self.white)
        qp.setCompositionMode(qp.CompositionMode_SourceOver)
        qp.strokePath(path, pen)
        qp.fillPath(path, brush)

    def updateOvershootStyle(self):
        '''
        style = overShootSliderStyleSheetBar.format(baseColour='#343B48',
                                                    hoverColour='#373E4C',
                                                    barColour='#ec0636',
                                                    stop1='0.1',
                                                    stop2='0.2',
                                                    stop3='0.1',
                                                    stop4='0.1',
                                                    stop5='0.1',
                                                    )
        self.setStyleSheet(overShootSliderStyleSheet.format(stop=self.value()))
        '''
        pass

    def getOutputValue(self):
        print ('self.buttonState', self.buttonState)
        if self.buttonState:
            multiplier = self.increment
        else:
            multiplier = 1
        if self.overshootState:
            return self.value() * multiplier
        return self.value() * multiplier

    def resizeEvent(self, event):
        self.arrangeButtons()

    def interpolate(self, low, high, percentage):
        if percentage < 0 or percentage > 100.0:
            raise ValueError("Percentage must be between 0 and 100")

        range_ = high - low
        value = low + (range_ * (percentage / 100.0))
        return value

    def arrangeButtons(self):
        if not self.overShootIncrementButtons:
            return
        if not self.incrementButtons:
            return
        halfWidth = self.width() / 2
        halfHeight = self.height() / 2
        increment = halfWidth / 4
        halfButton = self.incrementButtons[0].width() / 2
        button_width = self.incrementButtons[0].width()
        buttonHeight = halfHeight - (self.incrementButtons[0].height() / 2)

        buttonPosMin = self.handle_width + self.handle_margin
        buttonPosMax = self.width() - self.handle_width - self.handle_margin
        if self.overshootState:
            if not self.overShootIncrementButtons:
                return
            for i, x in enumerate(self.incrementButtons):
                x.hide()
            for i, x in enumerate(self.overShootIncrementButtons):
                position = self.interpolate(buttonPosMin, buttonPosMax, x.position)
                position -= x.width() * 0.5
                x.move(position, buttonHeight)
                x.show()
        else:

            for i, x in enumerate(self.overShootIncrementButtons):
                x.hide()
            for i, x in enumerate(self.incrementButtons):
                position = self.interpolate(buttonPosMin, buttonPosMax, x.position)
                position -= x.width() * 0.5

                x.move(position, buttonHeight)
                x.show()

    def contextMenuEvent(self, event):
        print('contextMenuEvent', event.globalPos())

    def toggleOvershoot(self, overshootState, baseWidth):
        self.overshootState = overshootState
        if self.overshootState:
            self.setMaximum(self.maxOvershootValue)
            self.setMinimum(self.minOvershootValue)
            self.setFixedWidth(baseWidth * 2)
            # self.updateOvershootStyle()
        else:
            self.setMaximum(self.maxValue)
            self.setMinimum(self.minValue)
            self.setFixedWidth(baseWidth)
            # self.resetStyle()

    def resetStyle(self):
        pass
        # self.setStyleSheet(self.adjust_style)

    def wheelEvent(self, event):
        # cmds.warning(self.x(), event.delta() / 120.0 * 25)
        self.setValue(self.value() + event.delta() / 120.0 * 25)
        # super(PySlider, self).wheelEvent(event)
        self.wheelSignal.emit(self.value())

    def expandRange(self, value):
        if value < self.minimum():
            self.setMinimum(value)
        if value > self.maximum():
            self.setMaximum(value)

    def buttonPressed(self, button):
        self.buttonState = True
        print("buttonPressed", button, button.increment)
        self.setTickInterval(25)
        self.setSliderDown(button.increment)
        self.setValue(button.increment)
        self.setFocus()

    def buttonReleased(self):
        self.buttonState = False
        print("button released")
        # self.setStyleSheet(self.initialStyle)
        self.resetHandle()

    def resetHandle(self):
        self.blockSignals(True)
        self.setValue(0)
        self.setTickInterval(1)
        self.blockSignals(False)

    def hideButtons(self):
        for w in self.overShootIncrementButtons:
            w.hideIcon()
            # w.hide()

        for w in self.incrementButtons:
            w.hideIcon()
            # w.hide()

    def showButtons(self):
        if self.overshootState:
            for w in self.overShootIncrementButtons:
                w.showIcon()
                w.show()
        else:
            for w in self.incrementButtons:
                w.showIcon()
                w.show()

    def checkMousePosition(self, buttons, event):
        # Get the global mouse position
        for x in buttons:
            label_geometry = x.geometry()

            # Map the top-left and bottom-right corners of the QLabel's bounding rectangle to global coordinates
            label_top_left = label_geometry.topLeft()
            label_bottom_right = label_geometry.bottomRight()

            global_mouse_pos = event.pos()
            # print ('global_mouse_pos', global_mouse_pos)
            # print('label_top_left', label_top_left)
            # print('label_bottom_right', label_bottom_right )
            if label_top_left.x() <= global_mouse_pos.x() <= label_bottom_right.x() and \
                    label_top_left.y() <= global_mouse_pos.y() <= label_bottom_right.y():
                return True, x.increment

        return False, 0

    def mousePressEvent(self, event):
        print('mousePressEvent', event)
        buttonClicked, increment = self.checkMousePosition(self.incrementButtons, event)
        overshootButtonClicked, overshootIncreent = self.checkMousePosition(self.overShootIncrementButtons, event)
        print(buttonClicked, increment)
        if self.overshootState:
            if overshootButtonClicked:
                self.buttonState = True
                # if the button is clicked, change the slider range
                self.setValue(increment // 8)
                self.hideButtons()
                self.setMinimum(-8)
                self.setMaximum(8)
            else:
                self.buttonState = False
                self.hideButtons()
                self.setMinimum(-200)
                self.setMaximum(200)
        else:
            if buttonClicked:
                self.buttonState = True
                # if the button is clicked, change the slider range
                self.setValue(increment // 4)
                self.hideButtons()
                self.setMinimum(-4)
                self.setMaximum(4)
                print(buttonClicked, increment)
            else:
                self.buttonState = False
                self.hideButtons()
                self.setMinimum(-100)
                self.setMaximum(100)

        super(Slider, self).mousePressEvent(event)

    def sliderPressedEvent(self):
        # buttonClicked, increment = self.checkMousePosition()
        # print ("Slider Pressed", increment, (increment/100) * 4)
        # if not buttonClicked:
        #     self.hideButtons()
        # else:
        #     # set the range to the number of increments
        #     self.setValue(increment//4)
        #     self.setMinimum(-4)
        #     self.setMaximum(4)
        #     self.update()

        return
        # Define the pattern for the QSlider::groove:horizontal:hover block
        pattern = r"QSlider::groove:horizontal:hover\s*{[^}]*}"

        # Find the QSlider::groove:horizontal:hover block
        match = re.search(pattern, self.initialStyle)

        if match:
            # Extract the matched block
            groove_block = match.group()

            # Modify the height property using regular expression substitution
            modified_groove_block = re.sub(
                r"height:\s*\d+px;", "height: 10px;", groove_block
            )

            # Replace the modified block within the existing stylesheet
            modified_stylesheet = self.initialStyle.replace(groove_block, modified_groove_block)

            # Set the updated stylesheet
        self.setStyleSheet(modified_stylesheet)

    def sliderMovedEvent(self):
        print("Slider Moved {}".format(self.value()))

    def sliderReleasedEvent(self):
        print("Slider Released")
        self.blockSignals(True)
        self.setValue(0)
        self.setMinimum(-100)
        self.setMaximum(100)
        self.blockSignals(False)
        self.setSingleStep(1)

        # self.setStyleSheet(self.initialStyle)
        self.showButtons()


class sliderButton(QPushButton):
    def __init__(self, label,
                 parent,
                 bg_color="#1b1e23",

                 ):
        super(sliderButton, self).__init__(label, parent)

        adjust_style = sliderStyleSheet.format()
        # self.setStyleSheet(adjust_style)
        self.setFixedSize(20 * dpiScale(), 20 * dpiScale())


class SliderFloatField(QWidget):
    valueChanged = Signal(float)

    def __init__(self,
                 label='label'):
        super(SliderFloatField, self).__init__()

        self.slider = Slider()
        self.floatField = intFieldWidget(defaultValue=0,
                                         label=label, minimum=-9999, maximum=9999, step=0.1)

        self.buildUI()
        self.makeConnections()

    def buildUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.slider)
        self.layout().addWidget(self.floatField)

    def makeConnections(self):
        self.slider.sliderMoved.connect(self.sliderValueChanged)
        self.floatField.editedSignalKey.connect(self.spinBoxValueChanged)
        self.slider.sliderPressed.connect(self.sliderValueChanged)
        self.slider.wheelSignal.connect(self.sliderValueChanged)

    def sliderValueChanged(self, value):
        # update the field widget
        self.floatField.spinBox.blockSignals(True)
        self.floatField.spinBox.setValue(value)
        self.floatField.spinBox.blockSignals(False)
        self.valueChanged.emit(value)

    def spinBoxValueChanged(self, key, value):
        self.slider.blockSignals(True)
        self.slider.expandRange(value)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)

    def reset(self):
        self.slider.blockSignals(True)
        self.floatField.spinBox.blockSignals(True)
        self.floatField.spinBox.setValue(0)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.floatField.spinBox.blockSignals(False)


class SliderToolbarWidget(QWidget):
    """
    The button used in the graph editor toolbar
    """

    def __init__(self, closeOnRelease=False,
                 sliderData=dict(),
                 altSliderData=dict(),
                 mode=str(), altMode=str(),
                 sliderIsDual=False,
                 altSliderIsDual=False,
                 toolTipSmall=str(),
                 icon=str(), altIcon=str()):
        super(SliderToolbarWidget, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # self.setToolTip("%s<br>Hold <b>Ctrl+Alt</b> for info" % toolTipSmall)
        self.icon = sliderData['icon']
        self.altIcon = altSliderData['icon']
        self.defaultWidth = pm.optionVar.get('sliderButtonWidth', 24)
        self.button = ToolbarButton(icon=self.icon, altIcon=self.altIcon, width=self.defaultWidth,
                                    height=self.defaultWidth)

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
        self.setFixedSize(self.defaultWidth * dpiScale(), self.defaultWidth * dpiScale())
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
        self.button.setPixmap(pixmap.scaled(24 * dpiScale(), 24 * dpiScale()))

        self.button.setFixedSize(24 * dpiScale(), 24 * dpiScale())
        self.setLayout(layout)
        self.margin = 2 * dpiScale()
        self.padding = 4 * dpiScale()
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
        self.overshootMax = (width * dpiScale()) - (self.button.width() * 0.5) - 2.0
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
        self.button.setPixmap(pixmap.scaled(24 * dpiScale(), 24 * dpiScale()))

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
        qp.setPen(QPen(QBrush(self.midGrey), 2 * dpiScale()))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 4 * dpiScale(), 4 * dpiScale())

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
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2 * dpiScale(), 2 * dpiScale())

        backgroundGradient = QLinearGradient(0.0, 0.0, self.width(), 0.0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.width(), self.clear)
        backgroundGradient.setColorAt((self.width() - 6.0) / self.width(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2 * dpiScale(), 2 * dpiScale())

        backgroundGradient = QLinearGradient(self.leftBorder, 0.0, self.rightBorder + 2, 0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.height(), self.clear)
        backgroundGradient.setColorAt((self.height() - 6.0) / self.height(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        # qp.setBrush(QBrush(self.red))
        qp.drawRoundedRect(self.leftBorder, 0, righBarPos, self.height(), 2 * dpiScale(), 2 * dpiScale())

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
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 4 * dpiScale(), 4 * dpiScale())

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
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2 * dpiScale(), 2 * dpiScale())

        backgroundGradient = QLinearGradient(0.0, 0.0, self.width(), 0.0)
        backgroundGradient.setColorAt(0, self.midGreyFaint)
        backgroundGradient.setColorAt(6.0 / self.width(), self.clear)
        backgroundGradient.setColorAt((self.width() - 6.0) / self.width(), self.clear)
        backgroundGradient.setColorAt(1, self.midGreyFaint)
        qp.setBrush(QBrush(backgroundGradient))
        qp.setPen(QPen(QBrush(self.clear), 0))
        qp.drawRoundedRect(0, 0, self.width(), self.height(), 2 * dpiScale(), 2 * dpiScale())

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


class SliderToolbarWidget_new(QWidget):
    """
    The button used in the graph editor toolbar
    """

    def __init__(self, closeOnRelease=False,
                 sliderData=dict(),
                 altSliderData=dict(),
                 mode=str(), altMode=str(),
                 sliderIsDual=False,
                 altSliderIsDual=False,
                 toolTipSmall=str(),
                 icon=str(), altIcon=str()):
        super(SliderToolbarWidget_new, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setToolTip("%s<br>Hold <b>Ctrl+Alt</b> for info" % toolTipSmall)
        self.icon = sliderData.get('icon', 'split.png')
        self.altIcon = altSliderData.get('icon', 'split.png')
        self.defaultWidth = pm.optionVar.get('sliderButtonWidth', 24)
        self.button = ToolbarButton(icon=self.icon, altIcon=self.altIcon, width=self.defaultWidth,
                                    height=self.defaultWidth)

        self.setLayout(layout)
        layout.addWidget(self.button)

        self.setMouseTracking(True)
        self.popup = PopupSlider()
        self.altPopup = PopupSlider()
        self.button.clicked.connect(self.raisePopup)
        self.button.middleClicked.connect(self.repeatLast)
        # self.button.rightClicked.connect(self.raisePopup)
        # self.popup.sliderEndedSignal.connect(self.resetCursor)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        pos = QCursor.pos()
        self.setFixedSize(self.defaultWidth * dpiScale(), self.defaultWidth * dpiScale())
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
        # popup.setIcon(self.button.currentIcon)
        popup.show()
        popup.setFocus()
        press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            popup.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        popup.sliderPressed.emit()

        pos = self.mapToGlobal(self.pos())
        screenPos = self.mapToGlobal(self.button.pos())
        pos = (self.button.pos())
        self.cachedCursorPos = QPoint(screenPos.x() + (self.button.width() * 0.5),
                                      screenPos.y() + (self.button.height() * 0.5))
        QCursor.setPos(self.cachedCursorPos)
        # popup.moveToCursor()

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

class PopupSliderButton(QWidget):
    def __init__(self, closeOnRelease=False,
                 sliderData=dict(),
                 altSliderData=dict(),
                 mode=str(), altMode=str(),
                 sliderIsDual=False,
                 altSliderIsDual=False,
                 toolTipSmall=str(),
                 icon=str(), altIcon=str()):
        super(PopupSliderButton, self).__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # self.setToolTip("%s<br>Hold <b>Ctrl+Alt</b> for info" % toolTipSmall)
        self.icon = sliderData['icon']
        self.altIcon = altSliderData['icon']
        self.defaultWidth = pm.optionVar.get('sliderButtonWidth', 24)
        self.button = ToolbarButton(icon=self.icon, altIcon=self.altIcon, width=self.defaultWidth,
                                    height=self.defaultWidth)

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
        self.setFixedSize(self.defaultWidth * dpiScale(), self.defaultWidth * dpiScale())
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