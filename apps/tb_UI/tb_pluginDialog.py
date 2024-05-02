from . import *

class PluginExtractor(BaseDialog):
    installSignal = Signal(str)

    def __init__(self, parentCLS):
        super(PluginExtractor, self).__init__(parent=getMainWindow())
        self.parentCLS = parentCLS
        self.titleText.setText('tbAnimTools Plugin Extractor')
        self.titleText.setStyleSheet("font-weight: normal; font-size: 18px;")
        self.infoText.setText('Install plugins from the zip file')
        self.infoText.setAlignment(Qt.AlignCenter)

        self.btnCloseWIndow = QPushButton("Close")
        self.btnCloseWIndow.clicked.connect(partial(self.close))

        self.btnInstall = QPushButton("Install")
        self.btnInstall.clicked.connect(partial(self.install))
        self.btnInstall.setEnabled(False)

        self.filePathLayout = QHBoxLayout()
        self.pathLabel = QLabel('Install to ::')
        self.pathLineEdit = QLineEdit('')
        self.pathLineEdit.setPlaceholderText('zip file path')
        self.cle_action_pick = self.pathLineEdit.addAction(QIcon(":/folder-open.png"),
                                                           QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Select your downloaded zip file')
        self.cle_action_pick.triggered.connect(self.pickZipFile)
        self.pathLineEdit.textChanged.connect(self.pathEdited)

        self.layout.addLayout(self.filePathLayout)
        self.filePathLayout.addWidget(self.pathLineEdit)
        self.layout.addWidget(self.btnInstall)
        self.layout.addWidget(self.btnCloseWIndow)
        self.setFixedSize(self.sizeHint())

    def pathEdited(self, *args):
        self.btnInstall.setEnabled(os.path.isfile(self.pathLineEdit.text()))

    def install(self, *args):
        self.installSignal.emit(self.pathLineEdit.text())

    def pickZipFile(self, *args):
        filename, filter = QFileDialog.getOpenFileName(parent=self,
                                                       caption='Open file',
                                                       dir='.',
                                                       filter='Zip Files (*.zip)')
        if filename:
            self.pathLineEdit.setText(filename)
