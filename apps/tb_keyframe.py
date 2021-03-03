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

    this script holds a bunch of useful keyframe related functions to make life easier

    send issues/ requests to brimblashman@gmail.com
    visit tb-animator.blogspot.com for "stuff"

*******************************************************************************
'''
import pymel.core as pm
import tb_timeline as tl
import maya.mel as mel
import maya.cmds as cmds
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
        self.setCategory('tbtools_keyframing')
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='match_tangent_start_to_end', annotation='',
                                     category=self.category, command=['key_mod.match(\"start\")']))
        self.addCommand(self.tb_hkey(name='match_tangent_end_to_start', annotation='',
                                     category=self.category, command=['key_mod.match(\"end\")']))
        self.addCommand(self.tb_hkey(name='filter_channelBox',
                                     annotation='filters the current channelBox seletion in the graph editor',
                                     category=self.category, command=['channels.filterChannels()']))

        self.addCommand(self.tb_hkey(name='setTangentsLinear',
                                     annotation='Sets your current key selection or timeline key to linear',
                                     category=self.category, command=['keyModifers.setTangentsLinear()']))
        self.addCommand(self.tb_hkey(name='setTangentsAuto',
                                     annotation='Sets your current key selection or timeline key to auto',
                                     category=self.category, command=['keyModifers.setTangentsAuto()']))
        self.addCommand(self.tb_hkey(name='setTangentsSpline',
                                     annotation='Sets your current key selection or timeline key to spline',
                                     category=self.category, command=['keyModifers.setTangentsSpline()']))
        self.addCommand(self.tb_hkey(name='setTangentsFlat',
                                     annotation='Sets your current key selection or timeline key to flat',
                                     category=self.category, command=['keyModifers.setTangentsFlat()']))
        self.addCommand(self.tb_hkey(name='toggleDockedGraphEditor',
                                     annotation='Toggle the collapsed state of the graph editor - if docked',
                                     category=self.category, command=['keyModifers.toggleDockedGraphEd()']))

        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class keys(object):
    def __init__(self):
        pass

    def get(self):
        pass

    @staticmethod
    def get_selected_curves():
        """ returns the currently selected curve names
        """
        return pm.keyframe(query=True, selected=True, name=True)

    @staticmethod
    def get_selected_keys():
        """ returns the currently selected curve names
        """
        return pm.keyframe(query=True, selected=True)

    @staticmethod
    def get_selected_keycount():
        return pm.keyframe(selected=True, query=True, keyframeCount=True)

    @staticmethod
    def get_key_times(curve):
        return pm.keyframe(curve, query=True, selected=True, timeChange=True)

    @staticmethod
    def get_key_values(curve):
        return pm.keyframe(curve, query=True, selected=True, valueChange=True)

    @staticmethod
    def get_key_values_from_range(curve, time_range):
        return pm.keyframe(curve, query=True, time=time_range, valueChange=True)


class keyModifers(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'keyModifers'
    hotkeyClass = hotkeys()
    funcs = functions()

    def __new__(cls):
        if keyModifers.__instance is None:
            keyModifers.__instance = object.__new__(cls)

        keyModifers.__instance.val = cls.toolName
        return keyModifers.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(keyModifers, self).optionUI()
        testButton = QPushButton('Flip frame count')
        self.layout.addWidget(testButton)
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    @staticmethod
    def match(data):
        ## match tangents for looping animations
        #
        # from tb_keyframe import key_mod
        # key_mod().match("start")
        # or
        # key_mod().match("end")
        #
        __dict = {'start': True, 'end': False
                  }
        state = __dict[data]
        print "state", state
        print "mode", data
        range = tl.timeline().get_range()
        s = range[state]
        e = range[not state]
        print "start", s, "end", e
        animcurves = pm.keyframe(query=True, name=True)
        tangent = []
        if animcurves and len(animcurves):
            for curve in animcurves:
                tangent = pm.keyTangent(curve, query=True, time=(s, s), outAngle=True, inAngle=True)
                print "tangent", tangent
                pm.keyTangent(curve, edit=True, lock=False, time=(e, e),
                              outAngle=tangent[state], inAngle=tangent[not state])
        else:
            print "no anim curves found"

    def setTangentsLinear(self):
        self.setTangentType('linear')

    def setTangentsSpline(self):
        self.setTangentType('spline')

    def setTangentsAuto(self):
        self.setTangentType('auto')

    def setTangentsFlat(self):
        self.setTangentType('flat')

    def setTangentType(self, input):
        graphEditorState = self.funcs.getGraphEditorState()
        timeSlider = self.funcs.getPlayBackSlider()

        minTime, maxTime = self.funcs.getTimelineHighlightedRange()
        currentKeys = cmds.keyframe(query=True, selected=True)

        if currentKeys and graphEditorState:
            cmds.keyTangent(itt=input, ott=input)
        else:
            sel = cmds.ls(sl=True)
            channels = mel.eval('selectedChannelBoxPlugs')
            if channels:
                attributes = [at.split('.')[-1] for at in channels]
            else:
                attributes = self.funcs.getValidAttributes(sel)
            if self.funcs.isTimelineHighlighted():
                minTime, maxTime = self.funcs.getTimelineHighlightedRange()
                timeRange = (minTime, (maxTime))
            else:
                timeRange = (cmds.currentTime(query=True), )
            cmds.keyTangent(sel,
                            attribute=attributes,
                            edit=True,
                            inTangentType=input,
                            outTangentType=input,
                            time=timeRange)
            self.funcs.infoMessage(prefix="Tangent :: ", message=input)
            #mel.eval("timeSliderSetTangent %s" % input)

    def toggleDockedGraphEd(self):
        self.funcs.toggleDockedGraphEd()

