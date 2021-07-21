import maya.mel as mel
import maya.cmds as cmds
import pymel.core as pm
import os, stat
import sys
import inspect
import io

from functools import partial

import maya.OpenMayaUI as omUI
qssFile = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +"\\", 'darkorange.qss'))

def getStyleSheet():
    stream = QFile(qssFile)
    if stream.open(QFile.ReadOnly):
        st = str(stream.readAll())
        stream.close()
    else:
        print(stream.errorString())
    return st

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    #from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    #from pyside2uic import *
    from shiboken2 import wrapInstance

class module_maker():
    def __init__(self):
        self.colours = {'red': "color:#F05A5A;",
                        'green': "color:#82C99A;",
                        'yellow': "color:#F4FA58;"
                        }
        self.win_versions = ['win32', 'win64'][pm.about(is64=True)]
        self.maya_version = pm.about(version=True)
        self.filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +"\\"  # script directory
        self.python_paths = ['', 'apps', 'proApps']  # empty string is the base dir (don't forget again)
        self.maya_script_paths = ['scripts']
        self.maya_plugin_paths = ['plugins/%s' % pm.about(version=True)]
        self.maya_common_plugin_paths = ['plugins/common']
        self.xbmlang_paths = ['Icons']
        self.out_lines = []
        self.module_file = 'tbAnimTools.mod'
        self.module_template = os.path.join(self.filepath, self.module_file)
        self.current_module_data = None
        self.firstInstall = False

    def maya_module_dir(self):
        return os.path.join(pm.internalVar(userAppDir=True) + "modules\\")

    def module_path(self):
        return os.path.join(self.maya_module_dir(), self.module_file)

    def make_module_path_data(self):
        module_path = '+ PLATFORM:' \
                      + self.win_versions \
                      + ' MAYAVERSION:' \
                      + self.maya_version \
                      + ' tbAnimTools 1.0 ' \
                      + self.filepath + '\\'
        return module_path

    def make_core_module_path_data(self):
        module_path = '+  tbAnimTools 1.0 ' + self.filepath + '\\'
        return module_path

    def make_core_module_data(self):
        out_lines = [self.make_core_module_path_data()]
        for paths in self.python_paths:
            out_lines.append('PYTHONPATH+:=' + paths)
        for paths in self.maya_script_paths:
            out_lines.append('MAYA_SCRIPT_PATH+:=' + paths)
        for paths in self.maya_common_plugin_paths:
            out_lines.append('MAYA_PLUG_IN_PATH+:=' + paths)
        for paths in self.xbmlang_paths:
            out_lines.append('XBMLANGPATH+:=' + paths)
        return out_lines

    def make_module_data(self, version):
        out_lines = ['\n']
        out_lines.append(version)

        for paths in self.maya_plugin_paths:
            out_lines.append('MAYA_PLUG_IN_PATH+:=' + paths)
        print ('make_module_data', out_lines)
        return out_lines

    def write_module_file(self):
        self.read_module_file()
        # mod_file = self.maya_module_dir + "\\" + self.module_file
        # shutil.copyfile(self.module_template, mod_file)
        if not self.current_module_data:
            return cmds.error('no module data to write')
        if os.access(os.path.join(self.module_path()), os.W_OK):
            with io.open(self.module_path(), 'w') as f:
                f.writelines(line + u'\n' for line in self.current_module_data)
                return True
                io.close(self.module_path())
        else:
            return False

    def read_module_file(self):
        existingVersions = list()
        if os.path.isfile(self.module_path()):
            f = open(self.module_path(), 'r')
            self.current_module_data = f.read().splitlines()
            match = False
            f.close()
            for lineIndex, line in enumerate(self.current_module_data):
                if line.startswith('+ PLATFORM'):
                    # finding a new block
                    existingVersions.append(line)
                if 'PLATFORM:%s' % self.win_versions and 'MAYAVERSION:%s' % self.maya_version in line:
                    match = True

        self.out_lines = list()
        self.out_lines.extend(self.make_core_module_data())
        for version in existingVersions:
            self.out_lines.extend(self.make_module_data(version))

        if not match:
            # create a new entry
            self.out_lines.extend(self.make_module_data(self.make_module_path_data()))
        '''
        for line in self.out_lines:
            print line
        '''
        self.current_module_data = self.out_lines

    def replace_path(self, fileName, path, newpath):
        f = open(fileName,'r')
        filedata = f.read()
        f.close()

        newdata = filedata.replace(path, newpath)

        f = open(fileName, 'w')
        f.write(newdata)
        f.close()

    def check_module_file(self):
        # file doesn't exist yet so create one
        if not os.path.isfile(self.module_path()):
            self.firstInstall = True
            f = open(str(self.module_path()), 'a+')  # open file in append mode
            f.writelines('')
            f.close()
        if os.path.isfile(self.module_path()):
            os.chmod(self.module_path(), stat.S_IWRITE)
            return False
        else:
            return True

    def make_module_folder(self):
        if not os.path.isdir(self.maya_module_dir()):
            os.mkdir(self.maya_module_dir())
        else:
            os.chmod(self.maya_module_dir(), stat.S_IWRITE)

    def install(self):
        # create module folder if not existing
        self.make_module_folder()

        # create module file if not existing
        state = self.check_module_file()

        self.write_module_file()

        result_message = "<h3>Installation result</h3>\t\n"

        if self.firstInstall:
            result_message += "module file created <span style=\""+self.colours['green']+ "\">Successfully</span> \n"
            result_message += "module file location <span style=\""+self.colours['yellow']+ "\">" \
                              + self.module_path() + "</span>\n\nEnjoy!"
            resultUI = ResultWindow()
            resultUI.show()

    def result_window(self):
        if pm.window("installWin", exists=True):
            pm.deleteUI("installWin")
        window = pm.window( title="success!")
        layout = pm.columnLayout(adjustableColumn=True )
        pm.text(font="boldLabelFont",label="tbtools installed")
        pm.text(label="")
        pm.text(label="please restart maya for everything to load")

        pm.button( label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        pm.setParent('..')
        pm.showWindow(window)

class installer():
    filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "\\"  # script directory
    iconPath = os.path.join(filepath, 'Icons')
    appPath = os.path.join(filepath, 'apps')
    colours = {'red': "color:#F05A5A;",
               'green': "color:#82C99A;",
               'yellow': "color:#F4FA58;"
               }

    def __init__(self):
        pass

    def install(self):
        try:
            self.clearMultipleSysPaths()
            if self.filepath not in sys.path:
                sys.path.append(self.filepath)
            if self.iconPath not in sys.path:
                sys.path.append(self.iconPath)
            if self.appPath not in sys.path:
                sys.path.append(self.appPath)

            import module_startup
            module_startup.initialise().load_everything()
        except Exception as e:
            pm.warning(e.message)

    def clearMultipleSysPaths(self):
        if self.filepath in sys.path:
            sys.path.remove(self.filepath)
        if self.iconPath in sys.path:
            sys.path.remove(self.iconPath)
        if self.appPath in sys.path:
            sys.path.remove(self.appPath)

class ResultWindow(QDialog):
    def __init__(self):
        super(ResultWindow, self).__init__(parent=wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget))
        self.setStyleSheet(getStyleSheet())
        layout = QVBoxLayout()

        text = QLabel('tbAnimTools installation successful')

        openHotkeyWindowBtn = QPushButton("Open Hotkey Window")
        openHotkeyWindowBtn.clicked.connect(self.openHotkeyWindow)
        openOptionsWindowBtn = QPushButton("Open Options Window")
        openOptionsWindowBtn.clicked.connect(self.openOptionWindow)
        btnBakePoseAdjustment = QPushButton("Close")
        btnBakePoseAdjustment.clicked.connect(partial(self.close))

        # layout.addWidget(btnSetFolder)
        layout.addWidget(text)
        layout.addWidget(openHotkeyWindowBtn)
        layout.addWidget(openOptionsWindowBtn)

        layout.addWidget(btnBakePoseAdjustment)

        self.setLayout(layout)

        #self.win.show()

    def openHotkeyWindow(self, *args):
        mel.eval("hotkeyEditorWindow")

    def openOptionWindow(self, *args):
        import tb_options as tbo
        tbo.showOptions()

if __name__ == "__main__":
    module_maker().install()
    installer().install()
