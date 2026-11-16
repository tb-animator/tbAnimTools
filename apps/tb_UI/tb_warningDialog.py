from . import *


class WarningDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(WarningDialog, self).__init__(parent=parent, title=title, text=text)
        self.setFixedWidth(200)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout.addWidget(self.buttonBox)
