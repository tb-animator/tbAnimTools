'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2020-Tom Bailey
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    send issues/ requests to brimblashman@gmail.com
    visit https://tbanimtools.blogspot.com/ for "more info"

    usage


*******************************************************************************
'''
import maya.mel as mel
import maya.cmds as cmds

import os, stat
import sys
import inspect
import io

from functools import partial



qtVersion = cmds.about(qtVersion=True)
QTVERSION = int(qtVersion.split('.')[0])
if QTVERSION < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance

elif QTVERSION < 6:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance
else:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    # from pyside2uic import *
    from shiboken6 import wrapInstance
import maya.OpenMayaUI as omUI
qssFile = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +"\\", 'darkorange.qss'))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), 'apps')))

def getStyleSheet():
    stream = QFile(qssFile)
    if stream.open(QFile.ReadOnly):
        st = str(stream.readAll())
        stream.close()
    else:
        print(stream.errorString())
    return st


from apps.tb_UI import *

# temp stylesheet here just in case
styleSheet = '''
QLabel
{
    font-weight: bold; font-size: 24px;
    font-family: courier;
}
QPushButton
{
    color: #b1b1b1;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
    border-width: 1px;
    border-color: #1e1e1e;
    border-style: solid;
    border-radius: 6;
    padding: 3px;
    font-size: 18px;
    font-weight: bold;
    padding-left: 5px;
    padding-right: 5px;
    font-family: courier;
}

QPushButton:pressed
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
}

QPushButton:hover
{
    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);
}
'''
labelStyleSheet = '''
QLabel
{
    font-weight: demibold; font-size: 14px;
    font-family: courier;
}
'''
def onMayaDroppedPythonFile(*args):
    module_maker().install()
    installer().install()
    print ('done')

class module_maker():
    def __init__(self):
        self.colours = {'red': "color:#F05A5A;",
                        'green': "color:#82C99A;",
                        'yellow': "color:#F4FA58;"
                        }
        self.win_versions = ['win32', 'win64'][cmds.about(is64=True)]
        self.maya_version = cmds.about(version=True)
        self.filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +"\\"  # script directory
        self.python_paths = ['', 'apps']
        #'proApps/Python39', 'proApps/Python3', 'proApps/Python2']  # empty string is the base dir (don't forget again)
        self.maya_script_paths = ['scripts']
        self.maya_plugin_paths = ['plugins/%s' % cmds.about(version=True)]
        self.maya_common_plugin_paths = ['plugins/common']
        self.xbmlang_paths = ['Icons']
        self.out_lines = []
        self.module_file = 'tbAnimTools.mod'
        self.module_template = os.path.join(self.filepath, self.module_file)
        self.current_module_data = None
        self.firstInstall = False

    def maya_module_dir(self):
        return os.path.join(cmds.internalVar(userAppDir=True) + "modules\\")

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
        #print ('make_module_data', out_lines)
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
        if cmds.window("installWin", exists=True):
            cmds.deleteUI("installWin")
        window = cmds.window( title="success!")
        layout = cmds.columnLayout(adjustableColumn=True )
        cmds.text(font="boldLabelFont", label="tbtools installed")
        cmds.text(label="")
        cmds.text(label="please restart maya for everything to load")

        cmds.button( label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        cmds.setParent('..')
        cmds.showWindow(window)

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

        self.clearMultipleSysPaths()
        if self.filepath not in sys.path:
            sys.path.append(self.filepath)
        if self.iconPath not in sys.path:
            sys.path.append(self.iconPath)
        if self.appPath not in sys.path:
            sys.path.append(self.appPath)

        import module_startup
        module_startup.initialise().load_everything()


    def clearMultipleSysPaths(self):
        if self.filepath in sys.path:
            sys.path.remove(self.filepath)
        if self.iconPath in sys.path:
            sys.path.remove(self.iconPath)
        if self.appPath in sys.path:
            sys.path.remove(self.appPath)

class ResultWindow(BaseDialog):
    def __init__(self):
        super(ResultWindow, self).__init__(parent=getMainWindow())

        self.titleText.setText('tbAnimTools')
        self.titleText.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.infoText.setText('Installation Successful')
        self.infoText.setAlignment(Qt.AlignCenter)

        blankLabel = QLabel("")
        openHotkeyWindowBtn = QPushButton("Open Hotkey Window")
        openHotkeyWindowLabel = QLabel("Check out the maya hotkey window for all the new commands")
        openHotkeyWindowBtn.clicked.connect(self.openHotkeyWindow)

        openOptionsWindowLabel = QLabel("tbAnimTools Options window for all the tool settings")
        openOptionsWindowBtn = QPushButton("Open Options Window")
        openOptionsWindowBtn.clicked.connect(self.openOptionWindow)

        openCustomHotkeyWindowLabel = QLabel("tbAnimTools custom hotkey window - just the custom commands")
        openCustomHotkeyWindowBtn = QPushButton("Open tbAnimtools Hotkey Window")
        openCustomHotkeyWindowBtn.clicked.connect(self.openCustomHotkeyWindow)

        openDiscordWindowBtn = QPushButton("- Go To Discord -")
        openDiscordWindowBtn.clicked.connect(self.openDiscord)
        btnCloseWIndow = QPushButton("Close")
        btnCloseWIndow.clicked.connect(partial(self.close))

        self.layout.addWidget(blankLabel)

        self.layout.addWidget(openCustomHotkeyWindowLabel)
        self.layout.addWidget(openCustomHotkeyWindowBtn)

        self.layout.addWidget(openOptionsWindowLabel)
        self.layout.addWidget(openOptionsWindowBtn)

        self.layout.addWidget(openHotkeyWindowLabel)
        self.layout.addWidget(openHotkeyWindowBtn)

        self.layout.addWidget(openDiscordWindowBtn)
        self.layout.addWidget(btnCloseWIndow)
        self.setStyleSheet(styleSheet)
        openHotkeyWindowLabel.setStyleSheet(labelStyleSheet)
        openOptionsWindowLabel.setStyleSheet(labelStyleSheet)
        openCustomHotkeyWindowLabel.setStyleSheet(labelStyleSheet)
        self.setFixedSize(self.sizeHint().width()+(36* dpiScale()), self.sizeHint().height()+(36*dpiScale()))


    def openHotkeyWindow(self, *args):
        mel.eval("hotkeyEditorWindow")

    def openOptionWindow(self, *args):

        pass
        # TODO - hook up option window
        #  showOptions()

    def openCustomHotkeyWindow(self, *args):
        from pluginLookup import ClassFinder
        pLookupCLS = ClassFinder()
        import tb_keyCommands as keyCommands

        win = keyCommands.mainHotkeyWindow(commandData=pLookupCLS.hotkeyClass.hotkeys,
                                           commandCategories=pLookupCLS.hotkeyClass.categories)
        win.showUI()

    def openDiscord(self):
        import webbrowser
        webbrowser.open('https://discord.gg/SyUyyJb8xw')


def install():
    module_maker().install()
    installer().install()
