from . import *


class markingMenuKeypressHandler(QObject):
    def __init__(self, UI=None):
        super(markingMenuKeypressHandler, self).__init__()
        self.UI = UI

    def eventFilter(self, target, event):
        if event.type() == event.KeyRelease:
            if event.isAutoRepeat():
                return True
            if not self.UI:
                return False
            self.UI.keyReleaseEvent(event)
            return False
        elif event.type() == event.KeyPress:
            if self.UI:
                try:
                    self.UI.keyPressEvent(event)
                except:
                    self.UI = None
            return False
        return False
