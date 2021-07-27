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
import maya.mel as mel
from Abstract import hotKeyAbstractFactory

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
import maya.cmds as cmds
import maya.mel as mel

from Abstract import *
from functools import partial

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('timeline'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='smooth_drag_timeline_on',
                                     annotation='timeslider tool with no frame snapping',
                                     category=self.category,
                                     command=['timeDragger.drag(True)']))
        self.addCommand(self.tb_hkey(name='smooth_drag_timeline_off',
                                     annotation='set to same hotkey as ON, but tick release',
                                     category=self.category,
                                     command=['timeDragger.drag(False)']))
        self.addCommand(self.tb_hkey(name='step_drag_timeline_on',
                                     annotation='timeslider tool with no frame snapping',
                                     category=self.category,
                                     command=['timeDragger.stepDrag()']))
        self.addCommand(self.tb_hkey(name='step_drag_timeline_off',
                                     annotation='set to same hotkey as ON, but tick release',
                                     category=self.category,
                                     command=['timeDragger.stepDrag(state=False)']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class timeDragger(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    #__metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'timeDragger'
    hotkeyClass = None
    funcs = None

    messagePos = "tb_timedrag_msg_pos"
    messageVar = "tb_timedrag_msg"
    optionVar = "tb_timedrag"
    modes = ['toggleBackground']
    step_modes = ['odd frames only']
    step_var = "tb_timedrag_step_frame"
    step_optionVar = "tb_step_odd"
    MessagePos = None
    showMessage = None
    toggle_background = None

    background_state = cmds.displayPref(query=True, displayGradient=True)
    previous_tool = None
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    failsafe = None
    step_ctx = None
    start_time = pm.getCurrentTime()
    dragPosition = []
    pressPosition = []
    step = pm.optionVar.get("tb_step_size", 2)
    even_only = pm.optionVar.get("tb_step_even", True)
    # for maya 2016 dag evaluation madness
    evaluate_mode = ""

    def __new__(cls):
        if timeDragger.__instance is None:
            timeDragger.__instance = object.__new__(cls)

        timeDragger.__instance.val = cls.toolName
        return timeDragger.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.update_options()
        self.previous_tool = self.get_previous_ctx()
        self.step_ctx = pm.draggerContext(name='step_ctx',
                                          pressCommand=self.step_drag_press,
                                          dragCommand=self.step_drag_dragged,
                                          # releaseCommand=self.step_drag_released,
                                          cursor='hand')

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(timeDragger, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    # in case you change the options mid session
    def update_options(self):
        self.MessagePos = pm.optionVar.get(self.messagePos, 'topLeft')
        self.showMessage = pm.optionVar.get(self.messageVar, 0)
        self.toggle_background = pm.optionVar.get(self.optionVar, 0)

    def get_previous_ctx(self):
        if pm.currentCtx() == "TimeDragger" or pm.currentCtx() == "step_ctx":
            previous_tool = 'selectSuperContext'
        else:
            previous_tool = pm.currentCtx()
        return previous_tool

    def drag(self, state):
        self.update_options()
        print (self.get_previous_ctx())
        print ("state", state)
        cmds.timeControl(self.aPlayBackSliderPython, edit=True, snap=not state)
        if state:
            mel.eval('storeLastAction("restoreLastContext ' + self.get_previous_ctx() + '")')
            if self.toggle_background:
                cmds.displayPref(displayGradient=False)
            if self.showMessage:
                msg = 'on'
                self.funcs.infoMessage(prefix='smooth drag',
                             message=' : %s' % msg,
                             position=self.MessagePos
                             )
            cmds.setToolTo('TimeDragger')
        else:
            if self.showMessage:
                msg = 'off'
                self.funcs.infoMessage(prefix='smooth drag',
                             message=' : %s' % msg,
                             position=self.MessagePos
                             )
            pm.setCurrentTime(int(pm.getCurrentTime()))
            cmds.displayPref(displayGradient=self.background_state)
            mel.eval('invokeLastAction')

    def warn(self):
        self.failsafe = None
        msg = "you pressed some weird combination of alt or maybe the windows key"
        print (msg)
        self.funcs.errorMessage(prefix='Warning',
                      message=' : %s' % msg,
                      position='botRight'
                      )

    def stepDrag(self, state=True):
        if state:
            try:
                # disable the parallel processing (crashes a lot in 2016)
                self.evaluate_mode = cmds.evaluationManager(mode='off')
            except:
                pass
            self.step = pm.optionVar.get(self.step_var, 1)
            self.even_only = pm.optionVar.get(self.step_optionVar, True)
            print ("step even", self.even_only)
            cmds.setToolTo(self.step_ctx)
        else:
            mel.eval('invokeLastAction')
            # stepped scrub bypasses evaluation manager as hardly anything in 2016 is thread safe
            try:
                if cmds.evaluationManager(query=True, enabled=True):
                    cmds.evaluationManager(mode=str(self.evaluate_mode))
            except:
                pass

    # Procedure called on press
    def step_drag_press(self):
        self.pressPosition = pm.draggerContext(self.step_ctx, query=True, anchorPoint=True)
        self.start_time = pm.getCurrentTime()

    # Procedure called on drag
    def step_drag_dragged(self):
        self.dragPosition = pm.draggerContext(self.step_ctx, query=True, dragPoint=True)
        distance = self.dragPosition[0] - self.pressPosition[0]
        step_destination = self.start_time + int(distance * 0.05) * self.step
        if self.even_only:
            # snap to odd frames only
            step_destination = int(step_destination / 2) * 2 + 1

        pm.setCurrentTime(max(self.funcs.getTimelineMin(), min(step_destination, self.funcs.getTimelineMax())))

    def step_drag_released(self):
        mel.eval('invokeLastAction')

    # this should reset the drag state when the tool is changed, in case you press alt or the windows key when dragging
    def failsafe_scriptjob(self):
        return pm.scriptJob(runOnce=True, event=['ToolChanged', partial(self.drag, False)])

    def info(self):
        print ("toggle background :", self.toggle_background)
        print ("background state  :", self.background_state)
        print ("previous tool     :", self.previous_tool)
