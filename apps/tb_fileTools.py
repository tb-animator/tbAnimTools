import maya.cmds as cmds
# TODO - move this bs to the ui classes


def selectDirectory(basePath=''):
    dialog = QFileDialog(None, caption="Pick Folder")
    dialog.setOption(QFileDialog.DontUseNativeDialog, False)
    dialog.setDirectory(basePath)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    selected_directory = dialog.getExistingDirectory()

    if selected_directory:
        return selected_directory
