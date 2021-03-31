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

    send issues/ requests to brimblashman@gmail.com
    visit https://tbanimtools.blogspot.com/ for "stuff"


*******************************************************************************
'''
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMayaAnim as oma
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omUI
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
from contextlib import contextmanager
import maya.OpenMaya as om

class functions(object):
    """
    Huge list of functions that scripts 'should' get built from
    """

    gChannelBoxName = None
    gPlayBackSlider = None

    messagePositions = ["topLeft",
                        "topCenter",
                        "topRight",
                        "midLeft",
                        "midCenter",
                        "midCenterTop",
                        "midCenterBot",
                        "midRight",
                        "botLeft",
                        "botCenter",
                        "botRight"]
    messageOptionVar_name = "inViewMessageEnable"
    messageInView_opt = pm.optionVar.get("inViewMessageEnable")
    messageColours = {'green': 'style=\"color:#33CC33;\"',
                      'red': 'style=\"color:#FF0000;\"',
                      'yellow': 'style=\"color:#FFFF00;\"',
                      }

    def getChannelBoxName(self):
        if not self.gChannelBoxName:
            self.gChannelBoxName = pm.melGlobals['gChannelBoxName']
        return self.gChannelBoxName

    def getPlayBackSlider(self):
        if not self.gPlayBackSlider:
            self.gPlayBackSlider = pm.melGlobals['gPlayBackSlider']
        return self.gPlayBackSlider

    # get the current model panel
    def getModelPanel(self):
        curPanel = pm.getPanel(underPointer=True) or pm.getPanel(withFocus=True)
        if pm.objectTypeUI(curPanel) == 'modelEditor':
            return curPanel
        else:
            return self.get_modelEditors(pm.lsUI(editors=True))[0]

    def tempLocator(self, name='loc', suffix='baked', scale=1.0, color=(1.0, 0.537, 0.016)):
        loc = pm.spaceLocator(name=name + '_' + suffix)
        size = scale * self.locator_unit_conversion()
        loc.localScale.set(size, size, size)
        loc.rotateOrder.set(2)
        loc.getShape().overrideEnabled.set(True)
        loc.getShape().overrideRGBColors.set(True)
        loc.getShape().overrideColorRGB.set(color)
        return loc

    @staticmethod
    def filter_modelEditors(editors):
        return pm.objectTypeUI(editors) == 'modelEditor'

    def get_modelEditors(self, editors):
        return filter(self.filter_modelEditors, editors)

    @staticmethod
    def get_all_curves(node=pm.ls(selection=True)):
        if node:
            return pm.keyframe(node, query=True, name=True)
        else:
            return None

    def get_smart_key_selection(self, node):
        if self.get_selected_keys():
            return self.get_key_indexes_in_selection(node=node)
        else:
            return self.get_keys_indexes_at_frame(node=node)

    def get_keys_indexes_at_frame(self, node=None, time=None):
        if not time:
            time = pm.getCurrentTime()
        curves = pm.keyframe(node, query=True, name=True)
        return_data = {}
        for curve in curves:
            if time in self.get_key_times(curve, selected=False):
                return_data[curve] = pm.keyframe(curve, query=True, time=time, indexValue=True)
        return return_data

    @staticmethod
    def get_key_indexes_in_selection(node=None):
        if not node:
            node = pm.ls(selection=True)

        return_data = {}
        curves = pm.keyframe(node, query=True, name=True)
        for curve in curves:
            return_data[curve] = pm.keyframe(curve, query=True, selected=True, indexValue=True)
        if return_data.keys():
            return return_data
        else:
            return None


    @staticmethod
    def get_keys_from_selection(node=cmds.ls(selection=True)):
        return cmds.keyframe(node, query=True, selected=True, name=True)

    @staticmethod
    def get_max_index(curve):
        return cmds.keyframe(curve, query=True, keyframeCount=True) -1

    @staticmethod
    def get_key_times(curve, selected=True):
        return cmds.keyframe(curve, query=True, selected=selected, timeChange=True)

    @staticmethod
    def get_selected_key_indexes(curve):
        return cmds.keyframe(curve, query=True, selected=True, indexValue=True)

    @staticmethod
    def get_all_key_times(curve, selected=True):
        return cmds.keyframe(curve, query=True, selected=selected, timeChange=True)

    @staticmethod
    def get_selected_curves():
        """ returns the currently selected curve names
        """
        return cmds.keyframe(query=True, selected=True, name=True)

    @staticmethod
    def get_selected_keys():
        """ returns the currently selected curve names
        """
        return cmds.keyframe(query=True, selected=True)

    @staticmethod
    def get_selected_keycount():
        return cmds.keyframe(selected=True, query=True, keyframeCount=True)

    @staticmethod
    def get_key_values(curve):
        return cmds.keyframe(curve, query=True, selected=True, valueChange=True)

    @staticmethod
    def get_key_values_from_range(curve, time_range):
        return cmds.keyframe(curve, query=True, time=time_range, valueChange=True)

    def get_prev_key_values_from_index(self, curve, index):
        return cmds.keyframe(curve, query=True, index=((max(0, index-1)),), valueChange=True)

    def get_next_key_values_from_index(self, curve, index):
        return cmds.keyframe(curve, query=True, index=((min(index+1, self.get_max_index(curve))),), valueChange=True)

    @staticmethod
    def get_selected_layers():
        allLayers = cmds.ls(type='animLayer')
        selectedLayers = []
        for layer in allLayers:
            if cmds.animLayer(layer, query=True, selected=True):
                selectedLayers.append(layer)
        return selectedLayers

    def select_layer(self, layerName):
        layers = cmds.ls(type='animLayer')
        for layer in layers:
            cmds.animLayer(layer, edit=True, selected=False)
            cmds.animLayer(layer, edit=True, preferred=False)
        cmds.animLayer(layerName, edit=True, preferred=True)
        cmds.animLayer(layerName, edit=True, selected=True)

    def get_all_layer_key_times(self, objects):
        layers = cmds.ls(type='animLayer')
        keyTimes = [None, None]
        layerStates = dict()
        if not layers:
            times = sorted(list(cmds.keyframe(objects, query=True, timeChange=True)))
            return [times[0], times[-1]]
        else:
            for layer in layers:
                layerStates[layer] = [cmds.animLayer(layer, query=True, selected=True),
                                      cmds.animLayer(layer, query=True, preferred=True)]
                cmds.animLayer(layer, edit=True, selected=False),
                cmds.animLayer(layer, edit=True, preferred=False)
            for layer in layers:
                cmds.animLayer(layer, edit=True, selected=True),
                cmds.animLayer(layer, edit=True, preferred=True)
                times = cmds.keyframe(objects, query=True, timeChange=True)
                if not times:
                    continue
                times = sorted(times)
                if not len(keyTimes) > 1:
                    continue
                if keyTimes[0] is None: keyTimes[0] = times[0]
                if keyTimes[1] is None: keyTimes[0] = times[-1]
                if times[0] < keyTimes[0]: keyTimes[0] = times[0]
                if times[-1] > keyTimes[1]: keyTimes[1] = times[-1]
                cmds.animLayer(layer, edit=True, selected=False),
                cmds.animLayer(layer, edit=True, preferred=False)
            for layer in layers:
                cmds.animLayer(layer, edit=True, selected=layerStates[layer][0]),
                cmds.animLayer(layer, edit=True, preferred=layerStates[layer][1])
        return keyTimes


    def match(self, data):
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
        range = self.getTimelineRange()
        s = range[state]
        e = range[not state]
        animcurves = pm.keyframe(query=True, name=True)
        tangent = []
        if animcurves and len(animcurves):
            for curve in animcurves:
                tangent = pm.keyTangent(curve, query=True, time=(s, s), outAngle=True, inAngle=True)
                pm.keyTangent(curve, edit=True, lock=False, time=(e, e),
                              outAngle=tangent[state], inAngle=tangent[not state])
        else:
            print "no anim curves found"

    def getChannels(self, *arg):
        # TODO make this work with assets
        chList = cmds.channelBox(self.getChannelBoxName(),
                                 query=True,
                                 selectedMainAttributes=True)
        if chList:
            for channel in chList:
                print channel
        else:
            print "no channels selected"
        return chList

    def filterChannels(self):
        channels = self.getChannels()
        selection = cmds.ls(selection=True)

        if selection and channels:
            cmds.selectionConnection('graphEditor1FromOutliner', edit=True, clear=True)
            for sel in selection:
                for channel in channels:
                    curve = sel + "." + channel
                    cmds.selectionConnection('graphEditor1FromOutliner', edit=True, object=curve)

    def toggleMuteChannels(self):
        channels = self.getChannels()
        selection = cmds.ls(selection=True)

        if selection and channels:
            for sel in selection:
                for channel in channels:
                    curve = sel + "." + channel
                    cmds.mute(sel + "." + channel,
                              disable=cmds.mute(sel + "." + channel, query=True))

    @staticmethod
    def getTimelineRange():
        return [cmds.playbackOptions(query=True, minTime=True), cmds.playbackOptions(query=True, maxTime=True)]

    @staticmethod
    def getTimelineMin():
        return cmds.playbackOptions(query=True, minTime=True)

    @staticmethod
    def getTimelineMax():
        return cmds.playbackOptions(query=True, maxTime=True)

    def getTimelineHighlightedRange(self, min=False, max=False):
        if min:
            return cmds.timeControl(self.getPlayBackSlider(), query=True, rangeArray=True)[0]
        elif max:
            return cmds.timeControl(self.getPlayBackSlider(), query=True, rangeArray=True)[1]
        else:
            return cmds.timeControl(self.getPlayBackSlider(), query=True, rangeArray=True)

    def isTimelineHighlighted(self):
        return self.getTimelineHighlightedRange()[1] - self.getTimelineHighlightedRange()[0] > 1

    def setPlaybackLoop(self):
        oma.MAnimControl.setPlaybackMode(oma.MAnimControl.kPlaybackLoop)

    def setPlaybackOnce(self):
        oma.MAnimControl.setPlaybackMode(oma.MAnimControl.kPlaybackOnce)

    # sets the start frame of playback
    @staticmethod
    def setTimelineMin(time=None):
        if time is None:
            time = pm.getCurrentTime()
        cmds.playbackOptions(minTime=time)

    # sets the end frame of playback
    @staticmethod
    def setTimelineMax(time=None):
        if time is None:
            time = pm.getCurrentTime()
        cmds.playbackOptions(maxTime=time)

    def setTimelineMinMax(self, minTime=None, maxTime=None):
        if minTime is None:
            minTime = pm.getCurrentTime()
        if maxTime is None:
            maxTime = minTime + 1
        self.setTimelineMin(time=minTime)
        self.setTimelineMax(time=maxTime)

    # crops to highlighted range on timeline
    def cropTimelineToSelection(self):
        if not self.isTimelineHighlighted():
            return cmds.warning('Cannot crop to selected range with no selection')
        highlightRange = self.getTimelineHighlightedRange()
        self.setTimelineMin(time=highlightRange[0])
        self.setTimelineMax(time=highlightRange[1])

    def getTimelineRangeFrameCount(self):
        range = self.getTimelineRange()
        return range[1] - range[0]

    # shift active time range so current frame is start frame
    def shiftTimelineRangeStartToCurrentFrame(self):
        self.setTimelineMax(time=(pm.getCurrentTime() + self.getTimelineRangeFrameCount()))
        self.setTimelineMin()

    # shift active time range so current frame is start frame
    def shiftTimelineRangeEndToCurrentFrame(self):
        print self.getTimelineRangeFrameCount()
        self.setTimelineMin(time=(pm.getCurrentTime() - self.getTimelineRangeFrameCount()))
        self.setTimelineMax()

    def cropTimeline(self, start=True):
        """
        If timeline is highlighted, crop to that range
        If not crop the start or end to current frame
        :param start:
        :return:
        """
        if not self.isTimelineHighlighted():
            if start:
                self.setTimelineMin()
            else:
                self.setTimelineMax()
        else:
            self.cropTimelineToSelection()

    def getGraphEditorState(self):
        graphEditor = None
        state = False
        geName = 'graphEditor1GraphEd'
        if cmds.animCurveEditor(geName, query=True, exists=True):
            graphEditorParent = cmds.animCurveEditor(geName, query=True, panel=True)
            if cmds.panel(graphEditorParent, query=True, exists=True):
                graphEditorWindow = cmds.panel(graphEditorParent, query=True, control=True).split('|')[0]
        if graphEditorWindow:
            return not cmds.workspaceControl(graphEditorWindow, query=True, collapse=True)
        else:
            return False

    def getValidAttributes(self, nodes):
        returnAttributes = list()
        for node in nodes:
            attrs = cmds.listAttr(node, inUse=True, keyable=True)
            ignoredAttrs = cmds.attributeInfo(node, bool=True, enumerated=True)
            finalAttrs = [x for x in attrs if x not in ignoredAttrs]
            for at in finalAttrs:
                if at not in returnAttributes:
                    returnAttributes.append(at)
        return returnAttributes

    @staticmethod
    def getAvailableTranslates(node):
        return [attr.lower() for attr in ['translateX', 'translateY', 'translateZ'] if not cmds.getAttr(node + '.' + attr, settable=True)]

    @staticmethod
    def getAvailableRotates(node):
        return [attr.lower() for attr in ['rotateX', 'rotateY', 'rotateZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]
    @staticmethod
    def getAvailableScales(node):
        return [attr.lower() for attr in ['scaleX', 'scaleY', 'scaleZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]

    # this disables the default maya inview messages (which are pointless after a while)
    def disable_messages(self):
        pm.optionVar(intValue=(self.messageOptionVar_name, 0))
        pass

    def enable_messages(self):
        pm.optionVar(intValue=(self.messageOptionVar_name, 1))
        pass

    # yellow info prefix highlighting
    def infoMessage(self, position="botRight", prefix="", message="", fadeStayTime=2.0, fadeOutTime=2.0, fade=True):
            prefix = '<hl>%s</hl>' % prefix
            self.enable_messages()
            pm.inViewMessage(amg=prefix + message,
                             pos=position,
                             fadeStayTime=fadeStayTime,
                             fadeOutTime=fadeOutTime,
                             fade=fade)
            self.disable_messages()

    # prefix will be highlighted in red!
    def errorMessage(self, position="botRight", prefix="", message="", fadeStayTime=0.5, fadeOutTime=4.0, fade=True):
        # self.optionVar_name = "inViewMessageEnable"
        # self.optionVar_name = Message().optionVar_name
        prefix = '<span %s>%s</span>' % (self.messageColours['red'], prefix)
        self.enable_messages()
        pm.inViewMessage(amg='%s : %s' % (prefix, message),
                         pos=position,
                         fadeOutTime=fadeOutTime,
                         dragKill=True,
                         fade=fade)
        self.disable_messages()

    @staticmethod
    def getMainWindow():
        return wrapInstance(long(omUI.MQtUtil.mainWindow()), QWidget)

    @staticmethod
    def getWidgetAtCursor():
        view = omUI.M3dView()
        omUI.M3dView.getM3dViewFromModelPanel('modelPanel4', view)
        viewWidget = wrapInstance(long(view.widget()), QWidget)
        return viewWidget

    def getGraphEditorState(self):
        """
        use this to determine if we should act on selected keys based on graph editor visibility
        :return:
        """
        GraphEdWindow = None
        state = False
        if cmds.animCurveEditor('graphEditor1GraphEd', query=True, exists=True):
            graphEdParent = cmds.animCurveEditor('graphEditor1GraphEd', query=True, panel=True)
            if not cmds.panel(graphEdParent, query=True, exists=True):
                return False
            if cmds.panel(graphEdParent, query=True, exists=True):
                GraphEdWindow = cmds.panel(graphEdParent, query=True, control=True).split('|')[0]

        if GraphEdWindow:
            state = cmds.workspaceControl(GraphEdWindow, query=True, collapse=True)
            return not state
        return False

    def toggleDockedGraphEd(self):
        GraphEdWindow = None
        state = False
        if cmds.animCurveEditor('graphEditor1GraphEd', query=True, exists=True):
            graphEdParent = cmds.animCurveEditor('graphEditor1GraphEd', query=True, panel=True)
            if not cmds.panel(graphEdParent, query=True, exists=True):
                mel.eval("GraphEditor")
            if cmds.panel(graphEdParent, query=True, exists=True):
                GraphEdWindow = cmds.panel(graphEdParent, query=True, control=True).split('|')[0]

        if GraphEdWindow:
            state = cmds.workspaceControl(GraphEdWindow, query=True, collapse=True)
        else:
            mel.eval('GraphEditor;')
        cmds.workspaceControl(GraphEdWindow, edit=True, collapse=not state)

    @contextmanager
    def keepSelection(self):
        # setup
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)

        yield

        # cleanup
        om.MGlobal.setActiveSelectionList(sel)

    @staticmethod
    def unit_conversion():
        conversion = {'mm': 0.1, 'cm': 1.0, 'm': 100.0, 'in': 2.54, 'ft': 30.48, 'yd': 91.44}
        return conversion[pm.currentUnit(query=True, linear=True)]

    @staticmethod
    def linear_unit_conversion():
        conversion = {'mm': 0.1, 'cm': 1.0, 'm': 100.0, 'in': 2.54, 'ft': 30.48, 'yd': 91.44}
        return conversion[pm.currentUnit(query=True, linear=True)]

    @staticmethod
    def locator_unit_conversion():
        conversion = {'mm': 10.0, 'cm': 1.0, 'm': 0.01, 'in': 0.0394, 'ft': 0.0033, 'yd': 0.0011}
        return conversion[pm.currentUnit(query=True, linear=True)]

    # time unit conversion
    @staticmethod
    def time_conversion():
        conversion = {'game': 15, 'film': 24, 'pal': 25, 'ntsc': 30, 'show': 48, 'palf': 50, 'ntscf': 60}
        return float(conversion[pm.currentUnit(query=True, time=True)])

    def getRefName(self, obj):
        refState = cmds.referenceQuery(str(obj), isNodeReferenced=True)
        if refState:
            # if it is referenced, check against pickwalk library entries
            return cmds.referenceQuery(str(obj), filename=True, shortName=True).split('.')[0]
        else:
            # might just be working in the rig file itself
            return cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]