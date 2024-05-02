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

