from . import *


class PickObjectDialog(BaseDialog):
    assignSignal = Signal(str)

    def __init__(self, parent=None, title='title!!!?', text='what  what?'):
        super(PickObjectDialog, self).__init__(parent=parent, title=title, text=text)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.itemLabel = QLineEdit()  # TODO add the inline button to this (from path tool)
        self.cle_action_pick = self.itemLabel.addAction(QIcon(":/targetTransfoPlus.png"), QLineEdit.TrailingPosition)
        self.cle_action_pick.setToolTip(
            'Pick path control from selection\nThis object will be used to generate your path.')
        self.cle_action_pick.triggered.connect(self.pickObject)

        self.layout.addWidget(self.itemLabel)

        self.mainLayout.addWidget(self.buttonBox)
        self.show()

    def pickObject(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.itemLabel.setText(str(sel[0]))
        self.assignSignal.emit(str(sel[0]))
