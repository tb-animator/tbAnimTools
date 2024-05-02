from . import *


class optionWidget(QWidget):
    def __init__(self, label=str):
        super(optionWidget, self).__init__()
        self.labelText = label
        self.initUI()

    def initUI(self):
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.scrollWidget = QWidget()  # Widget that contains the collection of Vertical Box
        self.layout = QVBoxLayout()  # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        self.scrollWidget.setLayout(self.layout)

        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollWidget)

        self.mainLayout.addWidget(self.scroll)

        self.label = QLabel(self.labelText)
        self.label.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.label)
        self.setGeometry(600, 100, 1000, 900)
        self.setWindowTitle('Scroll Area Demonstration')


class optionVarWidget(QWidget):
    def __init__(self, label=str, optionVar=str):
        super(optionVarWidget, self).__init__()
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.labelText = QLabel(label)


class optionVarBoolWidget(optionVarWidget):
    changedSignal = Signal(bool)

    def __init__(self, label=str, optionVar=str):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.checkBox = AnimatedCheckBox(text='On', offText='Off', width=36, height=14)
        self.checkBox.setChecked(pm.optionVar.get(self.optionVar, False))
        pm.optionVar(intValue=(self.optionVar, pm.optionVar.get(self.optionVar, False)))
        self.checkBox.clicked.connect(self.checkBoxEdited)
        if len(label):
            self.layout.addWidget(self.labelText)
        self.layout.addWidget(self.checkBox)
        self.layout.addStretch()

    def checkBoxEdited(self):
        pm.optionVar(intValue=(self.optionVar, self.checkBox.isChecked()))
        self.sendChangedSignal()

    def sendChangedSignal(self):
        self.changedSignal.emit(self.checkBox.isChecked())


class optionVarStringListWidget(optionVarWidget):
    changedSignal = Signal(bool)

    def __init__(self, label=str, optionVar=str):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.lineEdit = QLineEdit()

        optionValue = pm.optionVar(stringValue=(self.optionVar, pm.optionVar.get(self.optionVar, '')))
        self.lineEdit.setText(optionValue)
        self.lineEdit.textEdited.connect(self.lineEditChanged)
        self.layout.addWidget(self.labelText)
        self.layout.addWidget(self.lineEdit)

    def lineEditChanged(self):
        pm.optionVar[self.optionVar] = self.lineEdit.text()

    def sendChangedSignal(self):
        self.changedSignal.emit(self.lineEdit.isChecked())


class optionVarListWidget(optionVarWidget):
    """
    changing to use classdata instead of maya option vars
    """
    changedSignal = Signal(str, list)

    def __init__(self, label=str(), optionVar=str(), optionList=list(), classData=dict()):
        QWidget.__init__(self)
        self.optionVar = optionVar
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.labelText = QLabel(label)
        self.labelText.setAlignment(Qt.AlignTop)
        self.cbLayout = QGridLayout()
        optionVarValues = classData.get(optionVar, list())
        self.checkBoxes = list()
        numColumns = 2
        currentRow = 0
        count = 0
        for op in optionList:
            checkBox = QCheckBox()
            self.checkBoxes.append(checkBox)
            checkBox.setText(op)
            checkBox.setObjectName(optionVar + '_' + op)
            checkBox.setChecked(op in optionVarValues)
            self.cbLayout.addWidget(checkBox, count / 2, count % numColumns)
            checkBox.clicked.connect(self.checkBoxEdited)
            count += 1

        self.layout.addWidget(self.labelText)
        self.layout.addLayout(self.cbLayout)

    def checkBoxEdited(self, *args):
        activeValues = list()
        for cb in self.checkBoxes:
            if cb.isChecked():
                activeValues.append(cb.text())

        self.changedSignal.emit(self.optionVar, activeValues)
