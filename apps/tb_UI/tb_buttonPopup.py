from . import *

class ButtonPopup(QWidget):
    def __init__(self, name, parent=None):
        super(ButtonPopup, self).__init__(parent)

        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        pass
        self.radioGroup = radioGroupVertical(formLayout=self.layout,
                                             optionVarList=['test', 'test2', 'test3'],
                                             optionVar='testVar',
                                             defaultValue='test',
                                             label=str())

    def create_layout(self):
        for label, widget in self.radioGroup.returnedWidgets:
            self.layout.addRow("%s:" % label, widget)
        # layout.addRow("Size:", self.size_sb)
        # layout.addRow("Opacity:", self.opacity_sb)

class HotkeyPopup(ButtonPopup):
    def __init__(self, name, cls=None, parent=None, command=str(), hideLabel=False):
        super(ButtonPopup, self).__init__(parent)
        self.hideLabel = hideLabel
        self.setWindowTitle("{0} Options".format(name))
        self.cls = cls
        self.command = command
        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.hotkeyWidget = hotKeyWidget(cls=self.cls, command=self.command, text='Hotkey')
        self.hotkeyWidget.assignSignal.connect(self.cls.assignHotkey)
        self.helpLabelStr = str()
        try:
            self.helpLabel = QLabel(maya.stringTable['tbCommand.{0}'.format(self.command)].replace('__', ' '))
        except:
            self.helpLabel = QLabel(self.helpLabelStr)
        self.helpLabel.setWordWrap(True)
        self.imageGif = os.path.join(helpPath, self.command + '.gif')
        self.imageJpeg = os.path.join(helpPath, self.command + '.jpeg')
        self.imageLabel = QLabel(self)

        if os.path.isfile(self.imageGif):
            self.movie = QMovie(os.path.join(helpPath, self.imageGif))
            self.imageLabel.setMovie(self.movie)
            self.movie.start()
        elif os.path.isfile(self.imageJpeg):
            self.imagePixmap = QPixmap(os.path.join(helpPath, self.imageGif))
            self.imageLabel.setPixmap(self.imagePixmap)

    def create_layout(self):
        self.layout.addRow(self.hotkeyWidget)
        self.layout.addRow(self.helpLabel)
        self.layout.addRow(self.imageLabel)