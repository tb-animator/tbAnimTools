import pymel.core as pm
qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance

def selectDirectory(basePath=''):
    dialog = QFileDialog(None, caption="Pick Folder")
    dialog.setOption(QFileDialog.DontUseNativeDialog, False)
    dialog.setDirectory(basePath)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    selected_directory = dialog.getExistingDirectory()

    if selected_directory:
        return selected_directory
