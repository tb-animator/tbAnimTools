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

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('timeline'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='shift_time_range_start',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.shift_time_range_start'],
                                     command=['Timeline.shift_start()']))
        self.addCommand(self.tb_hkey(name='shift_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.shift_time_range_end'],
                                     command=['Timeline.shift_end()']))
        self.addCommand(self.tb_hkey(name='crop_time_range_start',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.crop_time_range_start'],
                                     command=['Timeline.crop_start()']))
        self.addCommand(self.tb_hkey(name='crop_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.crop_time_range_end'],
                                     command=['Timeline.crop_end()']))
        self.addCommand(self.tb_hkey(name='skip_forward',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.skip_forward'],
                                     command=['Timeline.skip(mode=1)']))
        self.addCommand(self.tb_hkey(name='skip_backward',
                                     annotation='',
                                     category=self.category,
                                     help=maya.stringTable['tbCommand.skip_backward'],
                                     command=['Timeline.skip(mode=-1)']))
        return self.commandList

    def assignHotkeys(self):
        return


class Timeline(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Timeline'
    hotkeyClass = hotkeys()
    funcs = Functions()

    skipFramesOption = 'tb_skip'

    def __new__(cls):
        if Timeline.__instance is None:
            Timeline.__instance = object.__new__(cls)

        Timeline.__instance.val = cls.toolName
        return Timeline.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(Timeline, self).optionUI()
        StepFramesWidget = intFieldWidget(optionVar=self.skipFramesOption,
                                          defaultValue=5,
                                          label='Next/Previous skip frames count',
                                          minimum=1, maximum=100, step=1)

        self.layout.addWidget(StepFramesWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return None

        self.range = [self.get_min(), self.get_max()]
        #
        self.cached_range = []
        # current selected range
        self.highlight = self.get_highlighted_range()
        # cached range
        self.cached_range = self.recall_range()

    def drawMenuBar(self, parentMenu):
        return None

    def skip(self, mode=-1):
        amount = get_option_var(self.skipFramesOption, 5)
        cmds.currentTime(int(amount * mode + cmds.currentTime(query=True)))

        cmds.optionVar(intValue=(self.skipFramesOption, amount))

    def crop_start(self):
        if self.funcs.isTimelineHighlighted():
            self.funcs.cropTimelineToSelection()
        else:
            self.funcs.cropTimeline(start=True)

    def crop_end(self):
        if self.funcs.isTimelineHighlighted():
            self.funcs.cropTimelineToSelection()
        else:
            self.funcs.cropTimeline(start=False)

    def crop_to_selection(self):
        self.funcs.cropTimelineToSelection()

    def shift_start(self):
        self.funcs.shiftTimelineRangeStartToCurrentFrame()

    def shift_end(self):
        self.funcs.shiftTimelineRangeEndToCurrentFrame()
