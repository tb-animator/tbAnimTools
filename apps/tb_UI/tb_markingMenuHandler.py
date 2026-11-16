from . import *

def getMarkingMenuFilter(UI=None):
    import maya.cmds as cmds
    qtVersion = cmds.about(qtVersion=True)
    QTVERSION = int(qtVersion.split('.')[0])
    if QTVERSION < 6:
        return MarkingMenuKeypressHandlerPyside2(UI=UI)
    else:
        return MarkingMenuKeypressHandler(UI=UI)

class MarkingMenuKeypressHandlerPyside2(QObject):
    def __init__(self, UI=None):
        super(MarkingMenuKeypressHandlerPyside2, self).__init__()
        self.UI = UI
    def eventFilter(self, target, event):
        if event.type() == QEvent.KeyRelease:
            print('MarkingMenuKeypressHandlerPyside2')
            if event.isAutoRepeat():
                return True
            if not self.UI:
                return False
            print ('is this the event?????')
            self.UI.keyReleaseEvent(event)
            return True
        elif event.type() == QEvent.KeyPress:
            if self.UI:
                try:
                    self.UI.keyPressEvent(event)
                except:
                    self.UI = None
            return False
        return False


class MarkingMenuKeypressHandler(QObject):
    def __init__(self, UI=None):
        super(MarkingMenuKeypressHandler, self).__init__()
        self.UI = UI

    def eventFilter(self, target, event):
        if event.type() == QEvent.KeyRelease:
            if event.isAutoRepeat():
                return True
            if not self.UI:
                return False
            print ('or is this the event here?')
            self.UI.keyReleaseEvent(event)
            return False
        elif event.type() == QEvent.KeyPress:
            if self.UI:
                try:
                    self.UI.keyPressEvent(event)
                except Exception as e:
                    print(f"Error handling key press event: {e}")
                    self.UI = None
            return False
        return False