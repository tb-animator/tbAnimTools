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
import maya.cmds as cmds
import maya.OpenMayaAnim as oma
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omUI
import pymel.core.datatypes as dt

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
from contextlib import contextmanager
import maya.OpenMaya as om

orbPointList = [[0.0, 25.0, 0.0],
                [0.0, 23.097, 9.567074999999999],
                [0.0, 17.677675, 17.677675],
                [0.0, 9.567074999999999, 23.097],
                [0.0, 0.0, 25.0],
                [0.0, -9.567074999999999, 23.097],
                [0.0, -17.677675, 17.677675],
                [0.0, -23.097, 9.567074999999999],
                [0.0, -25.0, 0.0],
                [0.0, -23.097, -9.567074999999999],
                [0.0, -17.677675, -17.677675],
                [0.0, -9.567074999999999, -23.097],
                [0.0, 0.0, -25.0],
                [0.0, 9.567074999999999, -23.097],
                [0.0, 17.677675, -17.677675],
                [0.0, 23.097, -9.567074999999999],
                [0.0, 25.0, 0.0],
                [9.567074999999999, 23.097, 0.0],
                [17.677675, 17.677675, 0.0],
                [23.097, 9.567074999999999, 0.0],
                [25.0, 0.0, 0.0],
                [23.097, -9.567074999999999, 0.0],
                [17.677675, -17.677675, 0.0],
                [9.567074999999999, -23.097, 0.0],
                [0.0, -25.0, 0.0],
                [-9.567074999999999, -23.097, 0.0],
                [-17.677675, -17.677675, 0.0],
                [-23.097, -9.567074999999999, 0.0],
                [-25.0, 0.0, 0.0],
                [-23.097, 9.567074999999999, 0.0],
                [-17.677675, 17.677675, 0.0],
                [-9.567074999999999, 23.097, 0.0],
                [0.0, 25.0, 0.0],
                [0.0, 23.097, -9.567074999999999],
                [0.0, 17.677675, -17.677675],
                [0.0, 9.567074999999999, -23.097],
                [0.0, 0.0, -25.0],
                [-9.567074999999999, 0.0, -23.097],
                [-17.677675, 0.0, -17.677675],
                [-23.097, 0.0, -9.567074999999999],
                [-25.0, 0.0, 0.0],
                [-23.097, 0.0, 9.567074999999999],
                [-17.677675, 0.0, 17.677675],
                [-9.567074999999999, 0.0, 23.097],
                [0.0, 0.0, 25.0],
                [9.567074999999999, 0.0, 23.097],
                [17.677675, 0.0, 17.677675],
                [23.097, 0.0, 9.567074999999999],
                [25.0, 0.0, 0.0],
                [23.097, 0.0, -9.567074999999999],
                [17.677675, 0.0, -17.677675],
                [9.567074999999999, 0.0, -23.097],
                [0.0, 0.0, -25.0]]
orbKnotList = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
               21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
               39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52]


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

    lastPanel = None

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
        curPanel = pm.getPanel(withFocus=True) or self.lastPanel  # pm.getPanel(underPointer=True)
        if pm.objectTypeUI(curPanel) == 'modelEditor':
            self.lastPanel = curPanel
            return curPanel
        elif self.lastPanel:
            return self.lastPanel
        else:
            return self.get_modelEditors(pm.lsUI(editors=True))[-1]

    def getAllModelPanels(self):
        return self.get_modelEditors(pm.lsUI(editors=True))

    def tempLocator(self, name='loc', suffix='baked', scale=1.0, color=(1.0, 0.537, 0.016)):
        loc = pm.spaceLocator(name=name + '_' + suffix)
        size = scale * self.locator_unit_conversion()
        loc.localScale.set(size, size, size)
        loc.rotateOrder.set(3)
        loc.getShape().overrideEnabled.set(True)
        loc.getShape().overrideRGBColors.set(True)
        loc.getShape().overrideColorRGB.set(color)
        return loc

    def tempControl(self, name='loc', suffix='baked', scale=1.0, color=(1.0, 0.537, 0.016)):
        control, shape = self.drawOrb(scale=scale)
        control.rename(name + '_' + suffix)

        control.rotateOrder.set(3)
        shape.overrideEnabled.set(True)
        shape.overrideRGBColors.set(True)
        shape.overrideColorRGB.set(color)
        return control

    def getSetColour(self, ref, control):
        """
        Copies the colour override from ref to control
        :param ref:
        :param control:
        :return:
        """
        node = pm.PyNode(ref)
        control = pm.PyNode(control)
        refObj = node
        overrideState = node.overrideEnabled.get()
        if not overrideState:
            shape = node.getShape()
            overrideState = shape.overrideEnabled.get()
            if overrideState:
                refObj = shape
        control.overrideEnabled.set(True)
        control.overrideRGBColors.set(refObj.overrideRGBColors.get())
        control.overrideColorRGB.set(refObj.overrideColorRGB.get())
        control.overrideColor.set(refObj.overrideColor.get())

    def addPickwalk(self, control=str(), destination=str(), direction=str(), reverse=bool):
        print ('addPickwalk', control, direction)
        walkDirectionNames = {'up': ['pickUp', 'pickDown'],
                              'down': ['pickDown', 'pickUp'],
                              'left': ['pickLeft', 'pickRight'],
                              'right': ['pickRight', 'pickLeft']
                              }

        attrName, reverseName = walkDirectionNames.get(direction, None)
        if not attrName:
            return pm.warning('Bad attribute name for pickwalk - direction %s' % direction)
        if not pm.attributeQuery(attrName, node=control, exists=True):
            pm.addAttr(control, ln=attrName, at='message')
        pm.connectAttr(destination + '.message', control + '.' + attrName, force=True)
        if not reverse:
            return
        if not pm.attributeQuery(reverseName, node=destination, exists=True):
            pm.addAttr(destination, ln=reverseName, at='message')
        pm.connectAttr(control + '.message', destination + '.' + reverseName, force=True)

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
        return cmds.keyframe(curve, query=True, keyframeCount=True) - 1

    @staticmethod
    def get_key_times(curve, selected=True):
        return cmds.keyframe(curve, query=True, selected=selected, timeChange=True)

    @staticmethod
    def get_object_key_times(target):
        keyTimes = cmds.keyframe(target, query=True, timeChange=True)
        if keyTimes: return sorted(list(set(keyTimes)))
        return list()

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
        return cmds.keyframe(curve, query=True, index=((max(0, index - 1)),), valueChange=True)

    def get_next_key_values_from_index(self, curve, index):
        return cmds.keyframe(curve, query=True, index=((min(index + 1, self.get_max_index(curve))),), valueChange=True)

    def initBaseAnimationLayer(self):
        cmds.delete(cmds.animLayer())

    def get_selected_layers(self, ignoreBase=False):
        if cmds.animLayer(q=True, root=True) == None:
            self.initBaseAnimationLayer()
            return []
        allLayers = cmds.ls(type='animLayer')
        selectedLayers = []
        for layer in allLayers:
            if cmds.animLayer(layer, query=True, selected=True):
                if ignoreBase:
                    if layer == cmds.animLayer(q=True, root=True):
                        continue
                selectedLayers.append(layer)

        return selectedLayers

    def select_layer(self, layerName):
        layers = cmds.ls(type='animLayer')
        for layer in layers:
            cmds.animLayer(layer, edit=True, selected=False)
            cmds.animLayer(layer, edit=True, preferred=False)
        if not isinstance(layerName, list):
            layerName = [layerName]
        for layer in layerName:
            cmds.animLayer(layer, edit=True, preferred=True)
            cmds.animLayer(layer, edit=True, selected=True)

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
            print ("no anim curves found")

    def getChannels(self, *arg):
        # TODO make this work with assets
        chList = cmds.channelBox(self.getChannelBoxName(),
                                 query=True,
                                 selectedMainAttributes=True)
        if chList:
            for channel in chList:
                print (channel)
        else:
            print ("no channels selected")
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
            timeRange = cmds.timeControl(self.getPlayBackSlider(), query=True, rangeArray=True)
            return timeRange[0], timeRange[1] - 1

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

    def lockTransform(self, nodes, translate=True, rotate=True, scale=True):
        attrNames = ['X', 'Y', 'Z']
        if not isinstance(nodes, list): nodes = [nodes]
        for n in nodes:
            if translate:
                for a in attrNames:
                    pm.setAttr(n + '.translate' + a, lock=True, keyable=False, channelBox=False)
            if rotate:
                for a in attrNames:
                    pm.setAttr(n + '.rotate' + a, lock=True, keyable=False, channelBox=False)
            if scale:
                for a in attrNames:
                    pm.setAttr(n + '.scale' + a, lock=True, keyable=False, channelBox=False)

    @staticmethod
    def getAvailableTranslates(node):
        return [attr.lower() for attr in ['translateX', 'translateY', 'translateZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]

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
        return wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)

    @staticmethod
    def getWidgetAtCursor():
        view = omUI.M3dView()
        omUI.M3dView.getM3dViewFromModelPanel('modelPanel4', view)
        viewWidget = wrapInstance(int(view.widget()), QWidget)
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

        if len(GraphEdWindow):
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

    @staticmethod
    def checkKeyableState(input):
        if not isinstance(input, list):
            input = [input]

        newLayer = pm.animLayer('ChannelTest')
        for i in input:
            if not cmds.attributeQuery('rotateOrder', node=i, keyable=True):
                try:
                    cmds.setAttr(i + '.rotateOrder', channelBox=True)
                    cmds.setAttr(i + '.rotateOrder', keyable=True)
                except:
                    pm.warning('Unable to set keyable state on %s' % i)
                pm.animLayer(newLayer, edit=True, attribute=i + '.rotateOrder')
                if not i + '.rotateOrder' in pm.animLayer(newLayer, query=True, attribute=True):
                    pm.warning('%s cannot be added to a layer as it is not set to keyable' % i)
                    pm.delete(newLayer)
                    return False

        if pm.animLayer(newLayer, query=True, exists=True):
            pm.delete(newLayer)

        return True

    def getPlugsFromLayer(self, nodeAttr, animLayer):
        """ Find the animBlendNode plug corresponding to the given node, attribute,
        and animation layer.
        """
        if not self.is_in_anim_layer(nodeAttr, animLayer):
            return None
        # print 'getPlugsFromLayer', nodeAttr, animLayer
        plug = None
        basePlug = None
        layerPlug = None
        if animLayer == cmds.animLayer(q=True, root=True):
            # For the base animation layer, traverse the chain of animBlendNodes all
            # the way to the end.  The plug will be "inputA" on that last node.
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
            history = cmds.listHistory(blendNode)
            lastAnimBlendNode = cmds.ls(history, type='animBlendNodeBase')[-1]
            if cmds.objectType(lastAnimBlendNode, isa='animBlendNodeAdditiveRotation'):
                letterXYZ = nodeAttr[-1]
                plug = '{0}.inputA{1}'.format(lastAnimBlendNode, letterXYZ.upper())
            else:
                plug = '{0}.inputA'.format(lastAnimBlendNode)
        else:
            # For every layer other than the base animation layer, we can just use
            # the "animLayer" command.  Unfortunately the "layeredPlug" flag is
            # broken in Python, so we have to use MEL.
            print ('getPlugsFromLayer', nodeAttr)
            cmd = 'animLayer -q -layeredPlug "{0}" "{1}"'.format(nodeAttr, animLayer)
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)
            print (blendNode, 'blendNode')
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
            history = cmds.listHistory(blendNode)
            firstAnimBlendNode = cmds.ls(history, type='animBlendNodeBase')[0]
            basePlug = firstAnimBlendNode + '.inputA'
            layerPlug = firstAnimBlendNode + '.inputB'
            plug = mel.eval(cmd)
        return plug

    @staticmethod
    def is_in_anim_layer(nodeName, animLayer):
        """ Determine if the given object is in the given animation layer.

        Parameters:
        * obj - Can be either a node name, like "pCube1", or a node/attribute combo,
            like "pCube1.translateX".
        * animLayer - The name of an animation layer.

        """

        objAnimLayers = cmds.animLayer([nodeName], q=True, affectedLayers=True) or []
        if animLayer in objAnimLayers:
            return True
        return False

    def drawOrb(self, scale=1.0):
        # print [dt.Vector(x) * scale * self.unit_conversion() for x in orbPointList]
        curve = cmds.curve(degree=1,
                           knot=orbKnotList,
                           point=[dt.Vector(x) * (scale / self.unit_conversion()) for x in orbPointList])
        curve = pm.PyNode(curve)
        return curve, curve.getShape()
