from . import *

class ComboBox(QComboBox):
    def wheelEvent(self, e):
        return


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
            self.optionValue = get_option_var(self.optionVar, defaultValue)
        else:
            self.optionValue = None
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.mainLayout)

        label = QLabel(label)

        self.comboBox = ComboBox()

        if self.values:
            for c in self.values:
                self.comboBox.addItem(c)
            self.comboBox.setCurrentIndex(self.values.index(self.defaultValue))
        self.comboBox.setFixedWidth(self.comboBox.sizeHint().width())
        view = self.comboBox.view()
        view.setFixedWidth(self.comboBox.sizeHint().width() + (32 * dpiScale()))
        self.mainLayout.addWidget(label)
        self.mainLayout.addWidget(self.comboBox)
        self.comboBox.currentIndexChanged.connect(self.interactivechange)
        self.mainLayout.addStretch()

    def interactivechange(self, b):
        if self.optionVar is not None:
            cmds.optionVar(stringValue=(self.optionVar, self.comboBox.currentText()))
        self.changedSignal.emit(self.comboBox.currentText())
        self.editedSignalKey.emit(self.key, self.comboBox.currentText())

    def updateValues(self, valueList, default):
        self.comboBox.clear()
        self.values = valueList
        for c in self.values:
            self.comboBox.addItem(c)
        self.comboBox.setCurrentIndex(self.values.index(default))



