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

maya.utils.loadStringResourcesForModule(__name__)

__author__ = 'tom.bailey'

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='toggle_isolate_selection',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.toggle_isolate_selection'],
                                     command=['isolator.toggle_isolate()']))
        self.addCommand(self.tb_hkey(name='addToIsolation',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.addToIsolation'],
                                     command=['isolator.addToIsolation()']))

        return self.commandList

    def assignHotkeys(self):
        return


class isolator(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'isolator'
    hotkeyClass = hotkeys()
    funcs = Functions()
    start_time = 0
    last_time = 0

    def __new__(cls):
        if isolator.__instance is None:
            isolator.__instance = object.__new__(cls)

        isolator.__instance.val = cls.toolName
        return isolator.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(isolator, self).optionUI()

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def toggle_isolate(self):
        '''
        import isolate as iso
        reload (iso)
        iso.isolate()
        '''
        panel = self.funcs.getModelPanel()

        self.start_time = time.time()
        if self.start_time - self.last_time < 0.2:
            self.last_time = self.start_time
            self.doubleTap(panel)
            return

        state = cmds.isolateSelect(panel, query=True, state=True)
        if state:
            cmds.isolateSelect(panel, state=0)
            cmds.isolateSelect(panel, removeSelected=True)
        else:
            cmds.isolateSelect(panel, state=1)
            cmds.isolateSelect(panel, addSelected=True)
            sel = cmds.ls(sl=True, type='transform')
            polyMeshes = self.getMeshesInSelection(sel)
            cmds.select(polyMeshes, deselect=True)

        self.last_time = self.start_time

    def doubleTap(self, panel):
        cmds.isolateSelect(panel, state=0)
        self.allTools.tools['QuickSelectionSets'].uber_qs_select()
        # deselect all mesh objects
        cmds.isolateSelect(panel, state=1)
        cmds.isolateSelect(panel, addSelected=True)
        sel = cmds.ls(sl=True, type='transform')
        polyMeshes = self.getMeshesInSelection(sel)
        cmds.select(sel, replace=True)
        cmds.select(polyMeshes, deselect=True)

    def getMeshesInSelection(self, selection):
        non_polyMeshes = list()
        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == "mesh":
                    # If it's a polyMesh, add its transform node to non_polyMeshes list
                    non_polyMeshes.append(obj)
                    break  # Move to the next transform node
        return non_polyMeshes
    def addToIsolation(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        panels = self.funcs.getAllModelPanels()
        if not panels:
            return
        for p in panels:
            state = cmds.isolateSelect(p, query=True, state=True)
            if state:
                cmds.isolateSelect(p, addSelected=True)
