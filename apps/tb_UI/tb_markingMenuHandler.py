from . import *

def getMarkingMenuFilter(UI=None, name='blank'):
    import maya.cmds as cmds
    qtVersion = cmds.about(qtVersion=True)
    QTVERSION = int(qtVersion.split('.')[0])
    if QTVERSION < 6:
        return MarkingMenuKeypressHandlerPyside2(UI=UI, name=name)
    else:
        return MarkingMenuKeypressHandler(UI=UI, name=name)

class MarkingMenuKeypressHandlerPyside2(QObject):
    def __init__(self, UI=None, name='blank'):
        super(MarkingMenuKeypressHandlerPyside2, self).__init__()
        self.UI = UI
        self.name = name

    def eventFilter(self, target, event):
        if event.type() == QEvent.KeyRelease:
            if event.isAutoRepeat():
                return True
            if not self.UI:
                return False
            # print ('is this the event?????', self.name)
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
    def __init__(self, UI=None, name='blank'):
        super(MarkingMenuKeypressHandler, self).__init__()
        self.UI = UI

        self.name = name
    def eventFilter(self, target, event):
        if event.type() == QEvent.KeyRelease:
            if event.isAutoRepeat():
                return True
            if not self.UI:
                return False
            # print ('or is this the event here?')
            self.UI.keyReleaseEvent(event)
            return False
        elif event.type() == QEvent.KeyPress:
            if self.UI:
                try:
                    self.UI.keyPressEvent(event)
                except Exception as e:
                    # print(f"Error handling key press event: {e}")
                    self.UI = None
            return False
        return False