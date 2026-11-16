from . import *

class CollapsibleBox(QWidget):
    collapsedIcon = QIcon(":openBar.png")
    expandedIcon = QIcon(":closeBar.png")
    collapseSignal = Signal(bool)

    def __init__(self, title="", parent=None, optionVar=str(), toolTip=None):
        super(CollapsibleBox, self).__init__(parent)
        self.optionVar = optionVar
        if toolTip:
            self.setToolTip(toolTip)
        self.toggleButton = QToolButton(
            text=title, checkable=True, checked=self.getState()
        )
        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setFixedSize(12 * dpiScale(), 20 * dpiScale())
        self.setFixedHeight(24 * dpiScale())
        self.toggleButton.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggleButton.setIcon(
            self.collapsedIcon if not self.getState() else self.expandedIcon
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
        lay.setAlignment(Qt.AlignCenter | Qt.AlignTop)
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
        self.setMouseTracking(True)

    def playAnimationByState(self, force=False, state=False):
        checked = self.getState()
        if force:
            self.toggleAnimation.setDirection(
                QAbstractAnimation.Forward
                if state
                else QAbstractAnimation.Backward
            )
        else:
            self.toggleAnimation.setDirection(
                QAbstractAnimation.Forward
                if not checked
                else QAbstractAnimation.Backward
            )
        self.toggleAnimation.start()

    def getState(self):
        return get_option_var(self.optionVar, False)

    @Slot()
    def on_pressed(self):
        self.setIconByState()
        self.playAnimationByState()
        self.setOptionVarByState()
        self.collapseSignal.emit(self.toggleButton.isChecked())

    def setOptionVarByState(self):
        checked = self.toggleButton.isChecked()
        cmds.optionVar(intValue = (self.optionVar, checked))
    def setIconByState(self):
        checked = self.getState()
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
