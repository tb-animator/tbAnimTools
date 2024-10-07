from . import *


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
            self.optionValue = get_option_var(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(label)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.spinBox = QDoubleSpinBox()
        self.spinBox.setMaximum(maximum)
        self.spinBox.setMinimum(minimum)
        self.spinBox.setSingleStep(step)
        self.spinBox.setValue(defaultValue)
        if step == 1:
            self.spinBox.setDecimals(0)
        self.spinBox.setProperty("value", self.optionValue)
        self.layout.addWidget(self.label)
        self.layout.addItem(spacerItem)
        self.layout.addWidget(self.spinBox)
        self.spinBox.valueChanged.connect(self.interactivechange)
        self.layout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            cmds.optionVar(floatValue=(self.optionVar, self.spinBox.value()))
        self.changedSignal.emit(self.spinBox.value())
        # print ('interactiveChange', self.spinBox.value())
        self.editedSignalKey.emit(self.key, self.spinBox.value())

    def updateValues(self, value):
        self.spinBox.setValue(value)