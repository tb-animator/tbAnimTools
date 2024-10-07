from . import *

def getScreenCenter():
    if QTVERSION < 6:
        return QApplication.desktop().availableGeometry().center()
    else:
        # Get the primary screen
        screen = QGuiApplication.primaryScreen()

        # Get the available geometry of the primary screen
        available_geometry = screen.availableGeometry()

        # Get the center of the available geometry
        center = available_geometry.center()
        return center
