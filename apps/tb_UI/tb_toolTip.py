from . import *
class CustomToolTip(QWidget):
    def __init__(self, text, parent=None):
        super(CustomToolTip, self).__init__(parent, Qt.Tool)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)

    def showEvent(self, event):
        self.adjustSize()
        self.move(QCursor.pos() + Qt.QPoint(10, 10))  # Offset the tooltip slightly
