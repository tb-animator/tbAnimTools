import pymel.core as pm
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

from ..tb_UI import intFieldWidget

sliderStyleSheet = """
QSlider {{ margin: 0px;
 height: 20px;
 border: 1px solid #2d2d2d;
 border-radius: 5px;
 }}
QSlider::groove:horizontal {{
    height: 20px;
	margin: 0px;
	background-color: #343B48;
}}
QSlider::groove:horizontal:hover {{
	background-color: #373E4C;
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

    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);
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
}}"""

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


class Slider(QSlider):
    wheelSignal = Signal(float)

    def __init__(self,
                 margin=0,
                 bg_size=20,
                 bg_radius=10,
                 bg_color="#1b1e23",
                 bg_color_hover="#1e2229",
                 handle_margin=2,
                 handle_size=16,
                 handle_radius=8,
                 handle_color="#568af2",
                 handle_color_hover="#6c99f4",
                 handle_color_pressed="#3f6fd1",
                 minValue=-100,
                 minOvershootValue=-200,
                 maxValue=100,
                 maxOvershootValue=200,
                 ):
        super(Slider, self).__init__()

        self.minValue = minValue
        self.minOvershootValue = minOvershootValue
        self.maxValue = maxValue
        self.maxOvershootValue = maxOvershootValue

        self.adjust_style = sliderStyleSheet.format()
        self.resetStyle()
        self.overshootState = False
        # self.setPopupMenu(SliderButtonPopup)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)

    def contextMenuEvent(self, event):
        pass
        # print ('contextMenuEvent', event.globalPos())

    def resetStyle(self):
        self.setStyleSheet(self.adjust_style)

    def toggleOvershoot(self, overshootState):
        self.overshootState = overshootState
        if self.overshootState:
            self.setMaximum(self.maxOvershootValue)
            self.setMinimum(self.minOvershootValue)
            self.updateOvershootStyle()
        else:
            self.setMaximum(self.maxValue)
            self.setMinimum(self.minValue)
            self.resetStyle()

    def wheelEvent(self, event):
        # cmds.warning(self.x(), event.delta() / 120.0 * 25)
        self.setValue(self.value() + event.delta() / 120.0 * 25)
        # super(PySlider, self).wheelEvent(event)
        self.wheelSignal.emit(self.value())

    def sliderMovedEvent(self, *args):
        if self.overshootState:
            self.updateOvershootStyle()

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

    def paintEvent(self, event):
        super(Slider, self).paintEvent(event)
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 64)

        qp.setCompositionMode(qp.CompositionMode_Overlay)
        qp.setRenderHint(QPainter.Antialiasing)
        if self.overshootState:
            qp.setPen(QPen(QBrush(lineColor), 0))
            qp.setBrush(QBrush(lineColor))
            leftBarPos = (self.width() * 0.25) + 5
            righBarPos = (self.width() * 0.75) - 5
            minSize = self.minimumSizeHint()
            offset = minSize.width() * 0.5

            qp.drawLine(righBarPos, 0, righBarPos, self.height())
            qp.drawLine(leftBarPos, 0, leftBarPos, self.height())
            qp.drawRect(0, 0, leftBarPos, self.height())
            qp.drawRect(righBarPos, 0, righBarPos, self.height())
        qp.end()

    def sliderReleasedEvent(self, *args):
        self.resetStyle()

    def expandRange(self, value):
        if value < self.minimum():
            self.setMinimum(value)
        if value > self.maximum():
            self.setMaximum(value)

class sliderButton(QPushButton):
    def __init__(self, label,
                 parent,
                 bg_color="#1b1e23",

                 ):
        super(sliderButton, self).__init__(label, parent)

        adjust_style = sliderStyleSheet.format()
        # self.setStyleSheet(adjust_style)
        self.setFixedSize(20, 20)

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
        self.layout().setContentsMargins(0,0,0,0)
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
