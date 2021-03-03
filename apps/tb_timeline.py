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
from Abstract import hotKeyAbstractFactory

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
                                     command=[
                                              'timeline.shift_start()',
                                              ]))
        self.addCommand(self.tb_hkey(name='shift_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'timeline.shift_end()',
                                              ]))
        self.addCommand(self.tb_hkey(name='crop_time_range_start',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'timeline.crop()',
                                              ]))
        self.addCommand(self.tb_hkey(name='crop_time_range_end',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'timeline.crop(start=False)',
                                              ]))
        self.addCommand(self.tb_hkey(name='skip_forward',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'tbt.skip(mode=1)'
                                              ]))
        self.addCommand(self.tb_hkey(name='skip_backward',
                                     annotation='',
                                     category=self.category,
                                     command=[
                                              'tbt.skip(mode=-1)'
                                              ]))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')

class timeline(object):
    def __init__(self):
        # get the name of the playback control
        self.time_slider = mel.eval('$tmpVar=$gPlayBackSlider')
        # current animation range
        self.range = [self.get_min(), self.get_max()]
        #
        self.cached_range = []
        # current selected range
        self.highlight = self.get_highlighted_range()
        # cached range
        self.cached_range = self.recall_range()

    @staticmethod
    def get_range():
        return [pm.playbackOptions(query=True, minTime=True), pm.playbackOptions(query=True, maxTime=True)]

    @staticmethod
    def get_min():
        return pm.playbackOptions(query=True, minTime=True)

    @staticmethod
    def get_max():
        return pm.playbackOptions(query=True, maxTime=True)

    def get_highlighted_range(self, min=False, max=False):
        if min:
            return pm.timeControl(self.time_slider, query=True, rangeArray=True)[0]
        elif max:
            return pm.timeControl(self.time_slider, query=True, rangeArray=True)[1]
        else:
            return pm.timeControl(self.time_slider, query=True, rangeArray=True)

    def isHighlighted(self):
        return self.get_highlighted_range()[1] - self.get_highlighted_range()[0] > 1

    # sets the start frame of playback
    @staticmethod
    def set_min(time=None):
        if time == None:
            print "no time specified? setting to c"
            time = pm.getCurrentTime()
        pm.playbackOptions(minTime=time)

    # sets the end frame of playback
    @staticmethod
    def set_max(time=None):
        if time == None:
            time = pm.getCurrentTime()
        pm.playbackOptions(maxTime=time)

    # crops to highlighted range on timeline
    def crop_to_selection(self):
        self.set_min(time=self.highlight[0])
        self.set_max(time=self.highlight[1])

    def range_in_frames(self):
        range = self.get_range()
        return range[1] - range[0]

    # shift active time range so current frame is start frame
    def shift_start(self):
        self.set_max(time=(pm.getCurrentTime() + self.range_in_frames()))
        self.set_min()

    # shift active time range so current frame is start frame
    def shift_end(self):
        print self.range_in_frames()
        self.set_min(time=(pm.getCurrentTime() - self.range_in_frames()))
        self.set_max()

    def cache_range(self):
        return [self.get_min(), self.get_max()]

    # this gets used int he temp playback of highlighted range
    def recall_range(self):
        _min = pm.optionVar.get('tb_tl_min', self.get_min())
        _max = pm.optionVar.get('tb_tl_max', self.get_max())
        return _min, _max

    def crop(self, start=True):
        if not self.isHighlighted():
            if start:
                self.set_min()
            else:
                self.set_max()
        else:
            self.crop_to_selection()

    def info(self):
        print "\ntime control : ", self.time_slider
        print "anim range   : ", self.range
        print "highlight    : ", self.highlight


def skip(mode=-1):
    amount = pm.optionVar.get('tb_skip', 5)
    pm.currentTime(amount * mode + pm.getCurrentTime())

    pm.optionVar(intValue=('tb_skip', amount))
