'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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

    this script holds a bunch of useful timeline functions to make life easier

    send issues/ requests to brimblashman@gmail.com
    visit tb-animator.blogspot.com for "stuff"

*******************************************************************************
'''
import pymel.core as pm
import maya.mel as mel
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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_view')
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='shift_time_range_start',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.shift_start()']))
        self.addCommand(self.tb_hkey(name='shift_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.shift_end()']))
        self.addCommand(self.tb_hkey(name='crop_time_range_start',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.crop_start()']))
        self.addCommand(self.tb_hkey(name='crop_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.crop_end()']))
        self.addCommand(self.tb_hkey(name='skip_forward',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.skip(mode=1)']))
        self.addCommand(self.tb_hkey(name='skip_backward',
                                     annotation='',
                                     category=self.category,
                                     command=['timeline.skip(mode=-1)']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')

class timeline(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'timeline'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if timeline.__instance is None:
            timeline.__instance = object.__new__(cls)

        timeline.__instance.val = cls.toolName
        return timeline.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(timeline, self).optionUI()
        testButton = QPushButton('some test button')
        self.layout.addWidget(testButton)
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

        self.range = [self.get_min(), self.get_max()]
        #
        self.cached_range = []
        # current selected range
        self.highlight = self.get_highlighted_range()
        # cached range
        self.cached_range = self.recall_range()

    def skip(self, mode=-1):
        amount = pm.optionVar.get('tb_skip', 5)
        pm.currentTime(int(amount * mode + pm.getCurrentTime()))

        pm.optionVar(intValue=('tb_skip', amount))

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






