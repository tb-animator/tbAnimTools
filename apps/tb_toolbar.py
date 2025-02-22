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
from . import *

str_TOOLBAR = 'tbAnimTools'

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
    funcs = Functions()
    toolbar = None

    def __new__(cls):
        if TBToolBar.__instance is None:
            TBToolBar.__instance = object.__new__(cls)

        TBToolBar.__instance.val = cls.toolName
        return TBToolBar.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    def initData(self):
        super(TBToolBar, self).initData()
        self.baseDataFile = os.path.join(self.dataPath, self.toolName + 'BaseData.json')

    def loadData(self):
        super(TBToolBar, self).loadData()
        self.rawJsonBaseData = json.load(open(self.baseDataFile))

        print(self.rawJsonBaseData)
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
        widgets = self.collectToolbarWidgets()
        self.toolbar.widgets.extend(widgets)

    def collectToolbarWidgets(self):
        widgets = list()
        for tool, cls in self.allTools.tools.items():
            if not cls:
                continue
            widgets.extend(cls.toolBarUI())
        return widgets

class TbToolBarDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        # Main Widgets

        self.setWindowTitle(str_TOOLBAR)

        ''' Shape library stuff '''

