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
        return


class Playback(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    #__metaclass__ = abc.ABCMeta
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

    if not cmds.optionVar(exists=playbackModeOption):
        cmds.optionVar(stringValue=(playbackModeOption, defaultPlaybackMode))

    if not cmds.optionVar(exists=manipulationModeOption):
        cmds.optionVar(stringValue=(manipulationModeOption, defaultManipulationMode))

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

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        self.playback_state = cmds.play(query=True, state=True)

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
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def get_flip_frames(self):
        return get_option_var(self.flipFrame_opv, self.flipFrame_default)

    def isPlaying(self):
        return cmds.play(query=True, state=True)

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
                # cmds.currentTime(self.funcs.getTimelineHighlightedRange(min=True))
                self.funcs.setTimelineMinMax(highlightMin, highlightMax)

        cmds.evaluationManager(mode={False: get_option_var(self.playbackModeOption),
                                   True: get_option_var(self.manipulationModeOption)}[self.isPlaying()])

        cmds.play(state=not self.isPlaying())

    def flipPlayback(self):
        if self.cached_start is None:
            self.cached_start, self.cached_end = self.funcs.getTimelineRange()
        highlight = self.funcs.isTimelineHighlighted()
        highlightMin, highlightMax = self.funcs.getTimelineHighlightedRange()
        if self.isPlaying():
            self.funcs.setTimelineMinMax(self.cached_start, self.cached_end)
            self.cropped = False
            cmds.play(state=False)
        else:
            self.cached_currentTime = cmds.currentTime(query=True)
            if self.funcs.isTimelineHighlighted():
                self.cached_start, self.cached_end = self.funcs.getTimelineRange()
                self.cropped = True
                self.funcs.setTimelineMinMax(highlightMin, highlightMax)
            else:
                self.funcs.setTimelineMax(cmds.currentTime(query=True) + self.get_flip_frames())
        self.funcs.setPlaybackOnce()
        cmds.play(state=True, wait=True)
        self.funcs.setPlaybackLoop()
        self.funcs.setTimelineMinMax(self.cached_start, self.cached_end)
        if self.cached_currentTime:
            cmds.currentTime(self.cached_currentTime)


