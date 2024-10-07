from . import *

class ViewportSliderWidget(BaseDialog):
    __instance = None
    # call the tween classes by name, send value
    sliderUpdateSignal = Signal(str, float, float)
    sliderEndedSignal = Signal(str, float, float)
    sliderBeginSignal = Signal(str, float, float)
    modeChangedSignal = Signal(str)
    sliderCancelSignal = Signal()
    removeHandlerSignal = Signal()

    minValue = -101
    minOvershootValue = -201
    maxValue = 101
    maxOvershootValue = 201
    baseSliderWidth = 350 * dpiScale()
    baseWidth = baseSliderWidth + (8 * dpiScale())

    baseLabel = 'baseLabel'
    shiftLabel = 'shiftLabel'
    controlLabel = 'controlLabel'
    controlShiftLabel = 'controlShiftLabel'
    altLabel = 'altLabel'
    '''
    def __new__(cls):
        if SliderWidget.__instance is None:
            if cmds.about(version=True) == '2022':
                SliderWidget.__instance = BaseDialog.__new__(cls)
            else:
                if QTVERSION < 5:
                    SliderWidget.__instance = BaseDialog.__new__(cls)
                else:
                    SliderWidget.__instance = object.__new__(cls)

        SliderWidget.__instance.val = 'SliderWidget'
        SliderWidget.__instance.app = QApplication.instance()
        return SliderWidget.__instance
    '''

    def __init__(self,
                 parent=getMainWindow(),
                 showLockButton=True, showCloseButton=False,
                 title='inbetween',
                 text='test',
                 modeList=list(),
                 baseLabel='baseLabel',
                 shiftLabel='shiftLabel',
                 controlLabel='controlLabel',
                 controlShiftLabel='controlShiftLabel',
                 altLabel='altLabel',
                 showInfo=True,
                 ):
        super(ViewportSliderWidget, self).__init__(parent=parent,
                                           title=title,
                                           text=text,
                                           showLockButton=showLockButton, showCloseButton=showCloseButton)

        self.isCancelled = False
        self.recentlyOpened = False
        self.invokedKey = None
        self.modeList = modeList
        self.regularWidth = 500 * dpiScale()
        self.setFixedSize(self.baseWidth, 60 * dpiScale())
        self.setWindowOpacity(0.9)
        #
        if not showInfo:
            self.infoText.hide()
        # labels
        self.baseLabel = baseLabel
        self.shiftLabel = shiftLabel
        self.controlLabel = controlLabel
        self.controlShiftLabel = controlShiftLabel
        self.altLabel = altLabel

        # self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.isDragging = False

        self.container = QFrame()
        self.container.setStyleSheet("QFrame {{ background-color: #343b48; color: #8a95aa; }}")
        slider_height = 28
        self.slider = Slider(
            margin=0,
            bg_height=slider_height,
            bg_radius=6,
            handle_width=slider_height,
            bg_color="#373E4C",
            bg_color_hover="#4c566b",
            handle_height=slider_height,
            handle_radius=4,
            handle_color="#373E4C",
            handle_color_hover="#435270",
            handle_color_pressed="#435270",
            icon=os.path.join(IconPath, 'iceCream.png').replace('\\', '//'))
        # self.slider_2 = PySlider()
        # self.slider_2.setStyleSheet(sliderStyleSheet.format())

        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimumWidth(self.baseSliderWidth)
        # self.slider_2.setFixedWidth(300*dpiScale())
        self.slider.setValue(0)
        self.slider.setTickInterval(1)

        self.slider.sliderPressed.connect(self.sliderPressed)
        self.slider.sliderMoved.connect(self.sliderValueChanged)
        self.slider.sliderMoved.connect(self.slider.sliderMovedEvent)
        self.slider.wheelSignal.connect(self.sliderWheelUpdate)
        self.slider.sliderReleased.connect(self.sliderReleased)
        self.slider.sliderReleased.connect(self.slider.sliderReleasedEvent)

        self.setLayout(self.layout)
        self.layout.addWidget(self.slider)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.overlayLabel = QLabel('', self)
        self.overlayLabel.setStyleSheet("background: rgba(255, 0, 0, 0); color : rgba(255, 255, 255, 168)")
        self.overlayLabel.setEnabled(False)
        self.overlayLabel.setFixedWidth(60 * dpiScale())
        self.overlayLabel.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet(getqss.getStyleSheet())
        if self.modeList:
            self.titleLayout.insertWidget(3, self.comboBox)
        self.overshootButton = LockButton('', self, icon='overshootOn.png',
                                          unlockIcon='overshoot.png', )
        self.overshootButton.lockSignal.connect(self.toggleOvershoot)
        self.titleLayout.insertWidget(3, self.overshootButton)
        for c in self.modeList:
            self.comboBox.addItem(c)
        self.currentMode = self.comboBox.currentText()
        self.comboBox.currentIndexChanged.connect(self.modeChanged)
        width = self.comboBox.minimumSizeHint().width()
        self.comboBox.view().setMinimumWidth(width)
        self.comboBox.setMinimumWidth((width + 16) * dpiScale())
        # self.resize(self.sizeHint())
        self.setFocusPolicy(Qt.StrongFocus)
        self.infoText.setText(self.baseLabel)

        # emit the mode change signal to load the labels
        self.modeChangedSignal.emit(self.currentMode)
        self.overlayLabel.move(20, self.height() - 20)
        self.setFixedSize(self.baseWidth, self.sizeHint().height())

    def show(self):
        super(ViewportSliderWidget, self).show()
        # print('showing')
        self.resetValues()
        self.setEnabled(True)
        self.setFocus()
        self.recentlyOpened = True

    def moveToCursor(self):
        pos = QCursor.pos()
        xOffset = 10  # border?
        self.move(pos.x() - (self.width() * 0.5), pos.y() - (self.height() * 0.5) - (16 * dpiScale()))

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        qp.setCompositionMode(QPainter.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def keyPressEvent(self, event):
        # print('keyPressEvent', event.type())
        if event.type() == QEvent.KeyPress:
            if self.recentlyOpened:
                if event.key() is not None:
                    self.invokedKey = event.key()
                    self.recentlyOpened = False
            modifiers = QApplication.keyboardModifiers()

            if not event.isAutoRepeat():
                if event.key() == Qt.Key_Alt:
                    self.altPressed()
                    return
                if event.key() == Qt.Key_Control:
                    if modifiers == Qt.ShiftModifier:
                        self.controlShiftPressed()
                    else:
                        self.controlPressed()
                elif event.key() == Qt.Key_Shift:
                    if modifiers == Qt.ControlModifier:
                        self.controlShiftPressed()
                    else:
                        self.shiftPressed()
        if not self.invokedKey or self.invokedKey == event.key():
            return
        super(ViewportSliderWidget, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # print('keyReleaseEvent', event.type())
        if event.key() != Qt.Key_Control and event.key() != Qt.Key_Shift and event.key() != Qt.Key_Alt:
            if not self.lockState:
                if not self.invokedKey or self.invokedKey == event.key():
                    self.removeHandlerSignal.emit()
                    self.hide()
        if event.type() == QEvent.KeyRelease:
            modifiers = QApplication.keyboardModifiers()

            if event.key() == Qt.Key_Alt:
                self.modifierReleased()
            if event.key() == Qt.Key_Control:
                if modifiers == (Qt.ShiftModifier | Qt.ControlModifier):
                    self.shiftPressed()
                else:
                    self.modifierReleased()
            elif event.key() == Qt.Key_Shift:
                if modifiers == (Qt.ShiftModifier | Qt.ControlModifier):
                    self.controlPressed()
                else:
                    self.modifierReleased()

    def modifierReleased(self):
        self.infoText.setText(self.baseLabel)

    def controlReleased(self):
        self.infoText.setText(self.baseLabel)

    def controlPressed(self):
        self.infoText.setText(self.controlLabel)

    def controlShiftPressed(self):
        self.infoText.setText(self.controlShiftLabel)

    def shiftPressed(self):
        self.infoText.setText(self.shiftLabel)

    def altPressed(self):
        self.infoText.setText(self.altLabel)

    def mousePressEvent(self, event):
        # print ("Mouse Clicked", event.buttons(), event.button() == Qt.RightButton)
        if event.button() == Qt.RightButton:
            self.sliderReleased(cancel=True)
        if event.button() == Qt.LeftButton:
            self.restoreSlider()
        super(ViewportSliderWidget, self).mousePressEvent(event)

    def sliderValueChanged(self):
        if self.slider.value() > self.slider.maximum() * 0.6:
            self.overlayLabel.move(10, self.height() - 20)
            self.overlayLabel.setAlignment(Qt.AlignLeft)
        elif self.slider.value() < self.slider.minimum() * 0.6:
            self.overlayLabel.move(self.width() - self.overlayLabel.width() - 10, self.height() - 20)
            self.overlayLabel.setAlignment(Qt.AlignRight)
        self.overlayLabel.setText(str(self.slider.value() * 0.01))
        self.sliderUpdateSignal.emit(self.currentMode, self.slider.getOutputValue(), 0.0)
        # print (self.currentMode, self.slider_2.value())
        # self.slider_2.setStyleSheet(overShootSliderStyleSheet.format(stop=self.slider_2.value() * 0.1))

    def sliderPressed(self):
        self.sliderBeginSignal.emit(self.currentMode, self.slider.getOutputValue(), 0.0)
        self.isDragging = True

    def restoreSlider(self):
        self.slider.setEnabled(True)
        self.isCancelled = False

    def sliderReleased(self, cancel=False):
        # print ('sliderReleased', cancel)
        if cancel:
            self.isCancelled = True
            self.sliderCancelSignal.emit()
            click_pos = QPoint(0, 0)
            event = QMouseEvent(QEvent.MouseButtonPress,
                                click_pos,
                                Qt.MouseButton.LeftButton,
                                Qt.MouseButton.LeftButton,
                                Qt.NoModifier)
            QApplication.instance().sendEvent(self, event)
            self.slider.setEnabled(False)
            # self.slider_2.clearFocus()
            # self.setFocus()
            # self.update()
            self.slider.setSliderDown(False)
            # self.slider_2.setEnabled(True)
        else:
            self.sliderEndedSignal.emit(self.currentMode, self.slider.lastValue, 0.0)
        self.isDragging = False
        self.slider.resetStyle()
        self.resetValues()

    def resetValues(self):
        # self.overlayLabel.setText('')
        self.slider.blockSignals(True)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.overlayLabel.hide()

    def sliderWheelUpdate(self):
        if not self.isDragging:
            self.sliderUpdateSignal.emit(self.currentMode, self.slider.value())
            self.sliderValueChanged()

    def modeChanged(self, *args):
        self.currentMode = self.comboBox.currentText()
        self.modeChangedSignal.emit(self.currentMode)

    def toggleOvershoot(self, overshootState):
        self.slider.toggleOvershoot(overshootState, self.baseSliderWidth)
        currentPos = self.pos()
        if overshootState:
            self.setFixedWidth(self.baseWidth * 2)
            currentPos.setX(currentPos.x() - (self.baseSliderWidth * 0.5))
        else:

            self.setFixedWidth(self.baseWidth)

            currentPos.setX(currentPos.x() + (self.baseSliderWidth * 0.5))
        self.move(currentPos)