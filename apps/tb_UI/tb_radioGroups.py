from . import *

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
        self.optionValue = get_option_var(self.optionVar, defaultValue)

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
                cmds.optionVar(stringValue=(self.optionVar, button.text()))
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
        self.optionValue = get_option_var(self.optionVar, defaultValue)

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
                cmds.optionVar(stringValue=(self.optionVar, button.text()))


class RadioGroup(QWidget):
    editedSignal = Signal(str)
    optionVar = None
    dirButton = None
    optionVarList = list()
    optionVar = str()
    optionValue = str()

    def __init__(self, optionVarList=list(), defaultValue=str(), label=str(),
                 tooltips=list()):
        super(RadioGroup, self).__init__()
        self.tooltips = tooltips
        self.optionVarList = optionVarList
        self.defaultValue = defaultValue
        self.optionValue = get_option_var(self.optionVar, defaultValue)
        self.formLayout = QFormLayout()
        self.setLayout(self.formLayout)
        self.btnGrp = QButtonGroup()  # Letter group
        self.returnedWidgets = list()
        self.buttons = list()
        for index, option in enumerate(self.optionVarList):
            self.buttons.append(QRadioButton(option))
            self.btnGrp.addButton(self.buttons[index])
            self.returnedWidgets.append(['option', self.buttons[index]])
            self.buttons[index].setChecked(self.optionValue == option)
            self.buttons[index].toggled.connect(self.buttonChecked)

            self.formLayout.addRow(option, self.buttons[index])

            try:
                self.buttons[index].setToolTip(self.tooltips[index])
            except:
                pass

    def buttonChecked(self, value):
        for button in self.buttons:
            if button.isChecked() == True:
                self.editedSignal.emit(button.text())
