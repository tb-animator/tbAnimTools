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
    visit https://tbanimtools.blogspot.com/ for "stuff"


*******************************************************************************
'''
import pymel.core as pm
import maya.cmds as cmds

from Abstract import *
import maya
import ui.tbUI_toolbar as tbuit
try:
    reload(tbuit)
except:
    import importlib
    importlib.reload(tbuit)
from ui.tbUI_toolbar import *
str_TOOLBAR = 'tbAnimTools'

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
__author__ = 'tom.bailey'
global tbToolBarDialog

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='createToolbar',
                                     annotation='',
                                     category=self.category,
                                     help='',
                                     command=['toolbar.createToolbar()']))

        return self.commandList

    def assignHotkeys(self):
        return


class TBToolBar(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'toolbar'
    hotkeyClass = hotkeys()
    funcs = functions()
    toolbar = None

    def __new__(cls):
        if TBToolBar.__instance is None:
            TBToolBar.__instance = object.__new__(cls)

        TBToolBar.__instance.val = cls.toolName
        return TBToolBar.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(TBToolBar, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def createToolbar(self):
        if self.toolbar:
            self.toolbar.deleteLater()
        workspace_control_name = DockableUI.get_workspace_control_name()
        if cmds.window(workspace_control_name, exists=True):
            cmds.deleteUI(workspace_control_name)

        DockableUI.module_name_override = "workspace_control"
        self.toolbar = DockableUI()


class TbToolBarDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        # Main Widgets

        self.setWindowTitle(str_TOOLBAR)

        ''' Shape library stuff '''

