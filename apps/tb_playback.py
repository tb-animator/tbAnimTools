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
import maya.OpenMayaAnim as oma
from maya.OpenMayaAnim import MAnimControl

from Abstract import *


qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance

from apps.tb_UI import *

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('timeline'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='toggle_playback_tool',
                                     annotation='does fancy playback toggling',
                                     category=self.category,
                                     command=['Playback.playPause()']))
        self.addCommand(self.tb_hkey(name='toggle_playback_viewport',
                                     annotation='does fancy playback toggling viewport modes',
                                     category=self.category,
                                     command=['Playback.toggleAll()']))
        self.addCommand(self.tb_hkey(name='flip_playback',
                                     annotation='does fancy playback toggling',
                                     category=self.category,
                                     command=['Playback.flipPlayback()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class Playback(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Playback'
    hotkeyClass = None
    funcs = None

    optionList = ['off', 'serial', 'parallel']
    playbackModeOption = 'playback mode'
    manipulationModeOption = 'manipulation mode'
    defaultPlaybackMode = 'parallel'
    defaultManipulationMode = 'parallel'

    flipFrame_opv = 'tb_flip_frames'
    flipFrame_default = 10

    if not pm.optionVar(exists=playbackModeOption):
        pm.optionVar(stringValue=(playbackModeOption, defaultPlaybackMode))

    if not pm.optionVar(exists=manipulationModeOption):
        pm.optionVar(stringValue=(manipulationModeOption, defaultManipulationMode))

    playback_state = False
    cropped = False
    cached_start = None
    cached_end = None
    cached_currentTime = None

    def __new__(cls):
        if Playback.__instance is None:
            Playback.__instance = object.__new__(cls)

        Playback.__instance.val = cls.toolName
        return Playback.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.playback_state = pm.play(query=True, state=True)

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(Playback, self).optionUI()
        flipWidget = intFieldWidget(optionVar=self.flipFrame_opv, defaultValue=self.flipFrame_default, label='Flip frame count')
        self.layout.addWidget(flipWidget)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def get_flip_frames(self):
        return pm.optionVar.get(self.flipFrame_opv, self.flipFrame_default)

    def isPlaying(self):
        return pm.play(query=True, state=True)

    def playPause(self, flip=False):
        if self.cached_start is None:
            self.cached_start, self.cached_end = self.funcs.getTimelineRange()
        # currently playing, so reset any time range
        highlight = self.funcs.isTimelineHighlighted()
        highlightMin, highlightMax = self.funcs.getTimelineHighlightedRange()

        if self.isPlaying():
            if self.cropped:
                self.funcs.setTimelineMinMax(self.cached_start, self.cached_end)
                self.cropped = False
        else:
            self.funcs.setPlaybackLoop()
            self.cached_start, self.cached_end = self.funcs.getTimelineRange()
            if self.funcs.isTimelineHighlighted():
                self.cropped = True
                # TODO - make the time frame reset an option
                # pm.setCurrentTime(self.funcs.getTimelineHighlightedRange(min=True))
                self.funcs.setTimelineMinMax(highlightMin, highlightMax)

        pm.evaluationManager(mode={False: pm.optionVar[self.playbackModeOption],
                                   True: pm.optionVar[self.manipulationModeOption]}[self.isPlaying()])

        pm.play(state=not self.isPlaying())

    def flipPlayback(self):
        if self.cached_start is None:
            self.cached_start, self.cached_end = self.funcs.getTimelineRange()
        highlight = self.funcs.isTimelineHighlighted()
        highlightMin, highlightMax = self.funcs.getTimelineHighlightedRange()
        if self.isPlaying():
            self.funcs.setTimelineMinMax(self.cached_start, self.cached_end)
            self.cropped = False
            pm.play(state=False)
        else:
            self.cached_currentTime = cmds.currentTime(query=True)
            if self.funcs.isTimelineHighlighted():
                self.cached_start, self.cached_end = self.funcs.getTimelineRange()
                self.cropped = True
                self.funcs.setTimelineMinMax(highlightMin, highlightMax)
            else:
                self.funcs.setTimelineMax(pm.currentTime(query=True) + self.get_flip_frames())
        self.funcs.setPlaybackOnce()
        pm.play(state=True, wait=True)
        self.funcs.setPlaybackLoop()
        self.funcs.setTimelineMinMax(self.cached_start, self.cached_end)
        if self.cached_currentTime:
            pm.currentTime(self.cached_currentTime)


