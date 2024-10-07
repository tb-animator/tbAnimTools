from . import *
import apps.tb_fileTools as ft


class filePathWidget(QWidget):
    layout = None
    path = None
    optionVar = None
    dirButton = None

    def __init__(self, optionVar, defaultValue, requiresRestart=False):
        super(filePathWidget, self).__init__()
        self.optionVar = optionVar
        self.path = get_option_var(self.optionVar, defaultValue)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.pathLabel = QLabel('Path:')
        self.pathLineEdit = QLineEdit(self.path)
        self.dirButton = QPushButton("Set folder")
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.dirButton)
        self.dirButton.clicked.connect(self.selectDirectory)

        self.requiresRestart = requiresRestart

    def selectDirectory(self, *args):
        selected_directory = ft.selectDirectory(basePath=self.path)

        if selected_directory:
            cmds.optionVar(stringValue=(self.optionVar, selected_directory))
            self.path = selected_directory
            self.pathLineEdit.setText(self.path)
        if self.requiresRestart:
            mel.eval('SavePreferences')
            raiseOk('RESTART MAYA NOW',
                    title='RESTART MAYA NOW')
