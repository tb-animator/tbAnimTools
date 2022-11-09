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
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import math
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omUI
import pymel.core.datatypes as dt
import re
from difflib import SequenceMatcher, get_close_matches, ndiff
from colorsys import rgb_to_hls, hls_to_rgb

API_TYPES = {'animCurve': [om2.MFn.kAnimCurveTimeToAngular,
                           om2.MFn.kAnimCurveTimeToDistance,
                           om2.MFn.kAnimCurveTimeToUnitless,
                           om2.MFn.kAnimCurveTimeToTime],
             'selection':
                 [om2.MItSelectionList.kDagSelectionItem,
                  om2.MItSelectionList.kDNselectionItem],
             'animCurveSelection': [om2.MItSelectionList.kDagSelectionItem,
                                    om2.MItSelectionList.kAnimSelectionItem,
                                    om2.MItSelectionList.kDNselectionItem],
             'blendModes': [om2.MFn.kBlendNodeDoubleLinear,
                            om2.MFn.kBlendNodeAdditiveRotation,
                            om2.MFn.kBlendNodeAdditiveScale,
                            om2.MFn.kBlendNodeBoolean,
                            om2.MFn.kBlendNodeEnum,
                            om2.MFn.kBlendNodeDouble,
                            om2.MFn.kBlendNodeDoubleAngle,
                            om2.MFn.kBlendNodeFloat,
                            om2.MFn.kBlendNodeFloatAngle,
                            om2.MFn.kBlendNodeFloatLinear,
                            om2.MFn.kBlendNodeInt16,
                            om2.MFn.kBlendNodeInt32,
                            om2.MFn.kBlendNodeBase],
             'rotation': [om2.MFn.kBlendNodeAdditiveRotation]}

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance
from contextlib import contextmanager
import maya.OpenMaya as om
import maya.api.OpenMayaAnim as oma2
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omui
import os
import json

dataPath = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir, 'appData', 'controlShapes.json'))
pointLists = json.load(open(dataPath))

acceptedConstraintTypes = ['pairBlend', 'constraint']


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

    """
    API Classes - layers
    """

    class AnimLayerData(object):
        __attrs__ = ['override', 'lock', 'passthrough', 'selected']

        def __init__(self, layer=None):
            """
            pass in string name for layer, store api info
            """
            # get MObject from root layer name
            sel = om2.MSelectionList()
            # print ('layer', layer)
            sel.add(layer)
            self.layer = sel.getDependNode(0)
            self.mfnDepNode = om2.MFnDependencyNode(self.layer)
            self.cache()

        def cache(self):
            for attr in self.__attrs__:
                plug = self.mfnDepNode.findPlug(attr, True)
                self.__dict__[attr] = plug and plug.asBool()

    def getBaseLayerAPI(self):
        baseAnimLayer = cmds.animLayer(query=True, root=True)
        if not baseAnimLayer:
            return None

        sel = om2.MSelectionList()
        sel.add(baseAnimLayer)
        return self.AnimLayerData(layer=baseAnimLayer)

    def getAnimLayersAPI(self):
        baseAnimLayer = self.getBaseLayerAPI()

        if not baseAnimLayer:
            return []

        allAnimLayers = [baseAnimLayer.layer]
        baseMFnDepNode = baseAnimLayer.mfnDepNode

        # get the child layers from the root, so we get them in order
        plug = baseMFnDepNode.findPlug('childrenLayers', True)
        for i in range(plug.numElements() - 1, -1, -1):  # walk backwards through the children
            connections = plug.elementByPhysicalIndex(i).connectedTo(True, False)
            if connections:
                allAnimLayers.append(connections[0].node())
        return allAnimLayers

    def cacheAllAnimLayersAPI(self):
        return [self.AnimLayerData(k) for k in self.getAnimLayersAPI()]

    def selectedLayers(self, cache):
        if not cache:
            cache = self.cacheAllAnimLayersAPI()
        return [x.layer for x in cache if x.selected]

    def sceneHasAnimLayers(self):
        layerIterator = om2.MItDependencyNodes(om2.MFn.kAnimLayer)
        count = 0

        while not layerIterator.isDone():
            if count > 0:
                return True

            count += 1
            layerIterator.next()

        return False

    def getBestLayerFromPlugAPI(self, plug, layerCache=None, baseAnimLayer=None):
        """
        Traverse the attribute plug hiearchy in search of animation layers and find the best candidate.

        :param plug: MPlug for where to start the search
        :type plug: om.MPlug
        :return: Best layer or None
        :rtype: om.MObject or None
        """
        if not baseAnimLayer:
            baseAnimLayer = self.getBaseLayerAPI()
        if not layerCache:
            layerCache = self.cacheAllAnimLayersAPI()
        selectedLayers = self.selectedLayers(layerCache)
        unlockedLayers = [x for x in layerCache if not x.lock]
        allLayers = [x.layer for x in layerCache]

        # if baseAnimLayer layer is selected and not locked, use that
        if baseAnimLayer.lock:
            baseAnimLayer.layer = None
        elif baseAnimLayer.selected and not len(selectedLayers) > 1:
            return baseAnimLayer.layer

        it = om2.MItDependencyGraph(plug, om2.MFn.kAnimLayer,
                                    direction=om2.MItDependencyGraph.kDownstream,
                                    traversal=om2.MItDependencyGraph.kBreadthFirst,
                                    level=om2.MItDependencyGraph.kNodeLevel)
        # it.pruningOnFilter = True
        bestLayer = None

        if selectedLayers:
            while not it.isDone():
                # store the node, and move iterator immediately
                layer = it.currentNode()

                if layer in allLayers:
                    it.prune()
                    if layer in selectedLayers:
                        bestLayer = layer

                it.next()
        if bestLayer:
            return bestLayer

        it.reset()

        while not it.isDone():
            layer = it.currentNode()

            if layer in allLayers:
                it.prune()
                if layer in unlockedLayers:
                    bestLayer = layer

            it.next()
        if not bestLayer:
            return baseAnimLayer
        return bestLayer

    def getAnimCurvesForObjectsAPI(self, MFnDepNodes):
        """ Gets the animation curves connected to nodes.

        :param nodes: List with MFnDependencyNode
        :type nodes: list of om.MFnDependencyNode
        :return: Tuple of curves and plugs
        :rtype: (list of om.MFnDependencyNode, list of om.MPlug)
        """

        curves = []
        plugs = []
        animLayerCache = self.cacheAllAnimLayersAPI()
        channelBoxSelection = self.getChannels()
        sceneHasAnimLayers = self.sceneHasAnimLayers()
        layersLocked = all([x.lock for x in animLayerCache])
        baseAnimLayer = self.getBaseLayerAPI()

        if sceneHasAnimLayers and layersLocked:
            return cmds.warning('Animation layers are locked. Cannot proceed')

        for node in MFnDepNodes:
            # get all attributes
            attributeList = node.attributeCount()
            for index in range(attributeList):
                attribute = node.attribute(index)
                plug = node.findPlug(attribute, True)

                if plug.isLocked or not plug.isKeyable:
                    continue

                connections = plug.connectedTo(True, False)
                if not connections: continue
                connectedNode = connections[0].node()

                apiType = connectedNode.apiType()
                if apiType in self.apiTypes('animCurve'):
                    if channelBoxSelection:
                        attributeName = om2.MFnAttribute(attribute).shortName
                        if attributeName not in channelBoxSelection:
                            continue

                    # add the node if it matches one of the types we want
                    curves.append(om2.MFnDependencyNode(connectedNode))
                    plugs.append(plug)

                # find curve in animation layer
                elif sceneHasAnimLayers and apiType in self.apiTypes('blendModes'):
                    # filter out attributes not selected in channelbox
                    if channelBoxSelection:
                        attributeName = om2.MFnAttribute(attribute).shortName
                        if attributeName not in channelBoxSelection:
                            continue

                    # for testing purposes
                    # print('Attribute: %s' % plug)

                    # benchmark_start = time.clock()
                    bestLayer = self.getBestLayerFromPlugAPI(plug)
                    if not bestLayer:
                        continue
                    '''
                    # test
                    try:
                        print('>> Best layer is {l}'.format(l=om.MFnDependencyNode(bestLayer).name()))
                    except Exception as e:
                        pass
                    '''
                    curve = self.getCurvesFromLayerAPI(plug, bestLayer, animLayerCache, baseAnimLayer)
                    # animlayers.cache.benchmark += time.clock() - benchmark_start
                    if curve:
                        curves.append(om2.MFnDependencyNode(curve))
                        plugs.append(plug)

        # sys.stdout.write('# Retrieved %d curves in %.4f sec\n' % (len(curve_list), animlayers.cache.benchmark))
        return curves, plugs

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
        curPanel = cmds.getPanel(withFocus=True) or self.lastPanel  # pm.getPanel(underPointer=True)
        if pm.objectTypeUI(curPanel) == 'modelEditor':
            self.lastPanel = curPanel
            return curPanel
        elif self.lastPanel:
            return self.lastPanel
        else:
            return self.get_modelEditors(pm.lsUI(editors=True))[-1]

    def getAllModelPanels(self):
        return self.get_modelEditors(pm.lsUI(editors=True))

    def tempNull(self, name='loc', suffix='baked'):
        node = pm.createNode('transform', name=name + '_' + suffix)
        node.rotateOrder.set(3)
        return node

    def tempLocator(self, name='loc', suffix='baked', scale=1.0, color=(1.0, 0.537, 0.016)):
        loc = pm.spaceLocator(name=name + '_' + suffix)
        size = scale * self.locator_unit_conversion()
        loc.localScale.set(size, size, size)
        loc.rotateOrder.set(3)
        loc.getShape().overrideEnabled.set(True)
        loc.getShape().overrideRGBColors.set(True)
        loc.getShape().overrideColorRGB.set(color)
        return loc

    def tempControl(self, name='loc', suffix='baked', scale=1.0, color=(1.0, 0.537, 0.016), drawType='orb',
                    unlockScale=False):
        points = pointLists['pointLists'].get(drawType, pointLists['pointLists']['cross'])
        control, shape = self.drawControl(points, scale=float(scale))
        control.rename(name + '_' + suffix)

        control.rotateOrder.set(3)
        control.scaleX.set(channelBox=True)
        control.scaleY.set(channelBox=True)
        control.scaleZ.set(channelBox=True)
        control.scaleX.set(keyable=unlockScale)
        control.scaleY.set(keyable=unlockScale)
        control.scaleZ.set(keyable=unlockScale)
        shape.overrideEnabled.set(True)
        shape.overrideRGBColors.set(True)
        shape.overrideColorRGB.set(color)
        return control

    def getSetColour(self, ref, control, brightnessOffset=0):
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
            if shape:
                overrideState = shape.overrideEnabled.get()
                if overrideState:
                    refObj = shape
        control.overrideEnabled.set(True)
        if not refObj.overrideRGBColors.get():

            if refObj.overrideColor.get() == 0:
                rgbColour = [125, 125, 125]
            else:
                rgbColour = [x * 255 for x in cmds.colorIndex(refObj.overrideColor.get(), q=True)]
        else:
            rgbColour = [x * 255 for x in refObj.overrideColorRGB.get()]
        rgbColourOut = self.adjust_color_lightness(rgbColour[0], rgbColour[1], rgbColour[2], 1 + brightnessOffset)
        rgbColourOut = [x / 255.0 for x in rgbColourOut]
        control.overrideColorRGB.set(rgbColourOut)

        control.overrideRGBColors.set(True)
        # control.overrideColor.set(refObj.overrideColor.get())
        for s in control.getShapes():
            s.overrideEnabled.set(0)

    def adjust_color_lightness(self, r, g, b, factor):
        h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        l = max(min(l * factor, 1.0), 0.0)
        r, g, b = hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)

    def lighten_color(self, colour, factor=0.1):
        return self.adjust_color_lightness(colour[0], colour[1], colour[2], 1 + factor)

    def darken_color(self, colour, factor=0.1):
        return self.adjust_color_lightness(colour[0], colour[1], colour[2], 1 - factor)

    def hex_to_rgb(self, hex):
        return [(hex[x:x + 2], 16) for x in [1, 3, 5]]

    def rgb_to_hex(self, colour):
        return "#%02x%02x%02x" % (colour[0], colour[1], colour[2])

    def addPickwalk(self, control=str(), destination=str(), direction=str(), reverse=bool):
        # print ('addPickwalk', control, direction)
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

    def get_all_key_times_for_node(self, node, animLayer=None):
        allLayers = pm.ls(type='animLayer')
        keyTimes = []
        if animLayer:
            animLayer = pm.PyNode(animLayer)

        if allLayers:
            for layers in allLayers:
                layers.selected.set(False)
                layers.preferred.set(False)
                pm.refresh()
            for layers in allLayers:
                if not animLayer or layers._name == animLayer._name:
                    layers.preferred.set(True)
                    layers.selected.set(True)
                pm.refresh()
                if isinstance(node, list):
                    if pm.keyframe(node, query=True):
                        keyTimes.extend(pm.keyframe(node, query=True))
                else:
                    if cmds.keyframe(str(node), query=True):
                        keyTimes.extend(pm.keyframe(str(node), query=True))
                layers.preferred.set(False)
                layers.selected.set(False)
        else:
            if isinstance(node, list):
                if cmds.keyframe(node, query=True):
                    keyTimes.extend(pm.keyframe(node, query=True))
            else:
                keyTimes = pm.keyframe(node, query=True)
        return sorted(list(set(keyTimes)))

    def getAllAnimatedChannels(self, controls):
        allAttributes = list()
        for c in controls:
            attributes = cmds.listAttr(c, keyable=True, settable=True)
            allAttributes.extend([c + '.' + a for a in attributes])
        return allAttributes

    def getIntermediateNodes(self, topObject=None, bottomObject=None):
        oobjectList = []
        if isinstance(topObject, str):
            topObject = pm.PyNode(topObject)

        if isinstance(bottomObject, str):
            bottomObject = pm.PyNode(bottomObject)
        j = pm.PyNode(bottomObject)

        if topObject and bottomObject:
            while j is not topObject and j.getParent():
                oobjectList.insert(0, j)
                if j == topObject:
                    break
                else:
                    j = j.getParent()
        return oobjectList

    def sortByParents(self, selection):
        selection = [pm.PyNode(x) for x in selection]
        parentDict = {}
        for x in selection:
            allParents = x.getAllParents()[::-1]
            parentDict[x] = allParents

        mostParentKeys = sorted(parentDict, key=lambda k: len(parentDict[k]), reverse=True)
        leastParentKeys = sorted(parentDict, key=lambda k: len(parentDict[k]))

        returnedList = [x for x in selection]
        for key in leastParentKeys:
            found = False
            for p in mostParentKeys:
                if found:
                    continue
                if p not in parentDict[key]:
                    continue
                if p in selection:
                    found = True
                    returnedList.insert(returnedList.index(p) + 1, returnedList.pop(returnedList.index(key)))
                if not found:
                    returnedList.insert(0, returnedList.pop(returnedList.index(key)))

        return returnedList

    def splitSelectionToChains(self, selection, requiresParent=True, returnTopParent=False):
        selection = [pm.PyNode(x) for x in selection]
        outputDict = {}

        parentDict = {}
        # get all object parents for all objects
        for x in selection:
            allParents = x.getAllParents()[::-1]
            parentDict[x] = allParents

        mostParentKeys = sorted(parentDict, key=lambda k: len(parentDict[k]), reverse=True)
        leastParentKeys = sorted(parentDict, key=lambda k: len(parentDict[k]))

        discardedIntermediates = list()
        for key in mostParentKeys:
            found = False
            if key in discardedIntermediates:
                continue
            for p in leastParentKeys:
                if found:
                    continue
                if p not in parentDict[key]:
                    continue
                found = True
                intermediateObjects = self.getIntermediateNodes(topObject=p, bottomObject=key)
                discardedIntermediates.extend(intermediateObjects)
                if returnTopParent:
                    intermediateObjects.insert(0, intermediateObjects[0].getParent())
                outputDict[str(p)] = [str(o) for o in intermediateObjects]
        return outputDict

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

    def getBakeRange(self, sel):
        """
        Returns a list of all key times for the input object list, if the timeline is highlighted
        :param sel: input object list
        :param timeline: Force visible timeline range
        :return:
        """
        startTime, endTime = self.getTimelineRange()
        return [x for x in self.get_all_key_times_for_node(sel) if x <= endTime and x >= startTime]

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
    def get_graph_editor_curves():
        """
        gets the curves visible in the graph editor
        :return:
        """
        result = cmds.selectionConnection('graphEditor1FromOutliner', query=True, object=True)
        curves = list()
        for r in result:
            c = cmds.listConnections(r, source=True, destination=False)
            if c:
                curves.append(c)
        filteredCurves = [item for sublist in curves for item in sublist if item]
        return filteredCurves

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

    def get_preferred_layers(self, selection, ignoreBase=False):
        if cmds.animLayer(q=True, root=True) == None:
            self.initBaseAnimationLayer()
            return []
        cmds.select(selection, replace=True)
        affectedLayers = cmds.animLayer(query=True, affectedLayers=True)
        selectedLayers = []
        if not affectedLayers:
            return list()
        for layer in affectedLayers:
            if cmds.animLayer(layer, query=True, preferred=True):
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
            cmds.animLayer(str(layer), edit=True, preferred=True)
            cmds.animLayer(str(layer), edit=True, selected=True)

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
                if keyTimes[1] is None: keyTimes[1] = times[-1]
                if times[0] < keyTimes[0]: keyTimes[0] = times[0]
                if times[-1] > keyTimes[1]: keyTimes[1] = times[-1]
                cmds.animLayer(layer, edit=True, selected=False),
                cmds.animLayer(layer, edit=True, preferred=False)
            for layer in layers:
                cmds.animLayer(layer, edit=True, selected=layerStates[layer][0]),
                cmds.animLayer(layer, edit=True, preferred=layerStates[layer][1])
        if not keyTimes[0]:
            keyTimes[0] = cmds.playbackOptions(query=True, minTime=True)
        if not keyTimes[1]:
            keyTimes[1] = cmds.playbackOptions(query=True, maxTime=True)
        return keyTimes

    def match(self, data):
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
            cmds.warning("no anim curves found")

    def getChannels(self, *arg):
        channels = set()
        mainChannelBox = self.getChannelBoxName()
        flags = ['selectedMainAttributes',
                 'selectedShapeAttributes',
                 'selectedHistoryAttributes',
                 'selectedOutputAttributes'
                 ]
        for flag in flags:
            ch = cmds.channelBox(mainChannelBox, q=True, **{flag: True})
            if ch: channels |= set(ch)

        if not len(channels):
            return []
        return channels

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

    def graphEdKeysSelected(self):
        """
        Returns true if graph editor is raised, with keys selected
        :return:
        """
        activeSelectionList = om2.MGlobal.getActiveSelectionList()
        selIterator = om2.MItSelectionList(activeSelectionList, om2.MFn.kAnimCurve)
        selectedCurveState = not selIterator.isDone()
        if not selectedCurveState:
            return False

        return self.getGraphEditorState()

    def getValidAttributes(self, nodes):
        returnAttributes = list()
        for node in nodes:
            attrs = cmds.listAttr(node, inUse=True, keyable=True)
            if not attrs:
                return list()
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

    def isConstrained(self, node):
        conns = cmds.listConnections(node, source=True, destination=False, plugs=False)
        if not conns:
            return False, None, None
        conns = [c for c in list(set(conns)) if cmds.objectType(c) in acceptedConstraintTypes]
        if conns:
            rel = cmds.listRelatives(node, type='constraint')
            return True, conns, rel
        return False, None, None

    def getConstrainTargets(self, constraint):
        constraint = pm.PyNode(constraint)
        targets = constraint.getTargetList()
        return targets

    def getConstrainWeights(self, constraint):
        constraint = pm.PyNode(constraint)
        targets = constraint.getWeightAliasList()
        return targets

    @staticmethod
    def getAvailableTranslates(node):
        return [attr.lower()[-1] for attr in ['translateX', 'translateY', 'translateZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]

    @staticmethod
    def getAvailableRotates(node):
        return [attr.lower()[-1] for attr in ['rotateX', 'rotateY', 'rotateZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]

    @staticmethod
    def getAvailableScales(node):
        return [attr.lower()[-1] for attr in ['scaleX', 'scaleY', 'scaleZ'] if
                not cmds.getAttr(node + '.' + attr, settable=True)]

    def safeParentConstraint(self, drivers, target, orientOnly=False, maintainOffset=False, channels=list()):
        skipR = self.getAvailableRotates(target)
        skipT = self.getAvailableTranslates(target)

        if channels:
            if 'rx' not in channels:
                if 'x' not in skipR:
                    skipR.append('x')
            if 'ry' not in channels:
                if 'y' not in skipR:
                    skipR.append('y')
            if 'rz' not in channels:
                if 'z' not in skipR:
                    skipR.append('z')

            if 'tx' not in channels:
                if 'x' not in skipT:
                    skipT.append('x')
            if 'ty' not in channels:
                if 'y' not in skipT:
                    skipT.append('y')
            if 'tz' not in channels:
                if 'z' not in skipT:
                    skipT.append('z')

        constraint = pm.parentConstraint(drivers, target,
                                         skipTranslate={True: ('x', 'y', 'z'),
                                                        False: [x.split('translate')[-1] for x in skipT]}[orientOnly],
                                         skipRotate=[x.split('rotate')[-1] for x in skipR],
                                         maintainOffset=maintainOffset)
        return constraint

    # this disables the default maya inview messages (which are pointless after a while)
    def disable_messages(self):
        pm.optionVar(intValue=(self.messageOptionVar_name, 0))
        pass

    def enable_messages(self):
        pm.optionVar(intValue=(self.messageOptionVar_name, 1))
        pass

    # yellow info prefix highlighting
    def infoMessage(self, position="botRight", prefix="", message="", fadeInTime=30, fadeStayTime=30, fadeOutTime=30,
                    fade=True):
        prefix = '<hl>%s</hl>' % prefix
        self.enable_messages()
        pm.inViewMessage(amg=prefix + message,
                         pos=position,
                         fadeInTime=fadeInTime,
                         fadeStayTime=fadeStayTime,
                         fadeOutTime=fadeOutTime,
                         dragKill=True,
                         fade=fade)
        self.disable_messages()

    # prefix will be highlighted in red!
    def errorMessage(self, position="botRight", prefix="", message="", fadeInTime=30, fadeStayTime=30, fadeOutTime=30,
                     fade=True):
        # self.optionVar_name = "inViewMessageEnable"
        # self.optionVar_name = Message().optionVar_name
        prefix = '<span %s>%s</span>' % (self.messageColours['red'], prefix)
        self.enable_messages()
        pm.inViewMessage(amg='%s : %s' % (prefix, message),
                         pos=position,
                         fadeInTime=fadeInTime,
                         fadeStayTime=fadeStayTime,
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
        if GraphEdWindow:
            cmds.workspaceControl(GraphEdWindow, edit=True, collapse=not state)

    @contextmanager
    def undoNoQueue(self):
        cmds.undoInfo(stateWithoutFlush=False)

        yield

        cmds.undoInfo(stateWithoutFlush=True)

    @contextmanager
    def undoChunk(self):
        cmds.undoInfo(openChunk=True)

        yield

        cmds.undoInfo(closeChunk=True)

    @contextmanager
    def keepSelection(self):
        # setup
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)

        yield

        # cleanup
        om.MGlobal.setActiveSelectionList(sel)

    @contextmanager
    def suspendUpdate(self):
        self.suspendSkinning()

        yield

        self.resumeSkinning()

    def suspendSkinning(self):
        allSkins = cmds.ls(type='skinCluster')
        for skin in allSkins:
            cmds.setAttr(skin + '.frozen', 1)
            cmds.setAttr(skin + '.nodeState', 1)

        cmds.refresh(su=True)

    def resumeSkinning(self):
        allSkins = cmds.ls(type='skinCluster')
        for skin in allSkins:
            cmds.setAttr(skin + '.frozen', 0)
            cmds.setAttr(skin + '.nodeState', 0)

        cmds.refresh(su=False)

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
        return mel.eval('getCadenceLineWorkingUnitInFPS')

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

    def extractAnimationLayers(self, nodes):
        cmds.select(nodes, replace=True)
        extracted_layers = []
        if not cmds.animLayer(query=True, affectedLayers=True):
            return list()

        layers_to_extract = [layer for layer in cmds.animLayer(query=True, affectedLayers=True) if
                             str(layer) != 'BaseAnimation']
        for layer in layers_to_extract:
            # skip muted layers during bakedown
            if not cmds.animLayer(layer, query=True, mute=True):
                exLayer = cmds.animLayer(layer + '_extracted', copyNoAnimation=layer, moveLayerAfter=layer)
                attributes = cmds.animLayer(layer, query=True, attribute=True)
                for attr in attributes:
                    keep = False
                    for n in nodes:
                        if mel.eval("plugNode {0}".format(attr)) == n:
                            keep = True
                            break
                    if not keep:
                        cmds.animLayer(exLayer, edit=True, removeAttribute=attr)

                cmds.animLayer(exLayer, edit=True, override=cmds.animLayer(layer, query=True, override=True))
                cmds.animLayer(exLayer, edit=True, passthrough=cmds.animLayer(layer, query=True, passthrough=True))
                cmds.animLayer(exLayer, edit=True, mute=cmds.animLayer(layer, query=True, mute=True))

                cmds.setAttr(exLayer + '.rotationAccumulationMode', cmds.getAttr(layer + '.rotationAccumulationMode'))

                cmds.animLayer(exLayer, edit=True, extractAnimation=layer)

                # copy layer weight curve
                weight_plug = cmds.listConnections(layer + '.weight', plugs=True, source=True, destination=False)
                if weight_plug:
                    cmds.connectAttr(weight_plug[0], exLayer + '.weight')
                if not cmds.animLayer(layer, query=True, attribute=True):
                    cmds.delete(layer)
                extracted_layers.append(str(exLayer))
        return extracted_layers

    def merge_layers(self, layers):
        # takes a string list of layers and merges them down
        layers.insert(0, 'BaseAnimation')
        layerString = ""
        for layer in layers:
            layerString += '"' + layer + '" ,'
        layerString = '{ %s }' % layerString[:-1]

        pm.optionVar['bakeSimulationByTime'] = 1
        pm.optionVar['animLayerMergeSmartFidelity'] = 1
        mel.eval('animLayerMerge( %s )' % layerString)

    def getLowerLayerPlugs(self, nodeAttr, animLayer):
        if animLayer == cmds.animLayer(q=True, root=True):
            return None, None
        else:
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)
            if not blendNode:
                return None, None
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
            history = cmds.listHistory(blendNode)
            firstAnimBlendNode = cmds.ls(history, type='animBlendNodeBase')[0]
            basePlug = firstAnimBlendNode + '.inputA'
            layerPlug = firstAnimBlendNode + '.inputB'
            if cmds.nodeType(blendNode) == 'animBlendNodeAdditiveRotation':
                basePlug += nodeAttr[-1]
                layerPlug += nodeAttr[-1]
            return basePlug, layerPlug
        return None, None

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
            # print ('getPlugsFromLayer', nodeAttr)
            cmd = 'animLayer -q -layeredPlug "{0}" "{1}"'.format(nodeAttr, animLayer)
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)
            # print (blendNode, 'blendNode')
            blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
            history = cmds.listHistory(blendNode)
            firstAnimBlendNode = cmds.ls(history, type='animBlendNodeBase')[0]
            basePlug = firstAnimBlendNode + '.inputA'
            layerPlug = firstAnimBlendNode + '.inputB'
            plug = mel.eval(cmd)
        return plug

    def getClosestPointOnCurveNEW(self, curve, position, guess=None):
        selList = om.MSelectionList()
        selList.add(curve)
        curveFn = om.MFnNurbsCurve(selList.getDagPath(0))

        p, u, v = curveFn.closestPoint(om2.MPoint(*position),
                                       guess=None,
                                       tolerance=0.01,
                                       space=om.MSpace.kWorld)

        return [(p[0], p[1], p[2]), (u, v)]

    def getCurveParamAtPosition(self, crv, position):
        point = om.MPoint(position[0], position[1], position[2])

        dag = om.MDagPath()
        obj = om.MObject()
        oList = om.MSelectionList()
        oList.add(crv.name())
        oList.getDagPath(0, dag, obj)

        curveFn = om.MFnNurbsCurve(dag)
        length = curveFn.length()
        crv.findParamFromLength(length)

        paramUtill = om.MScriptUtil()
        paramPtr = paramUtill.asDoublePtr()
        lengthUtill = om.MScriptUtil()
        currentLengthPtr = lengthUtill.asDoublePtr()

        point = curveFn.closestPoint(point, paramPtr, 0.001, om.MSpace.kObject)
        curveFn.getParamAtPoint(point, paramPtr, 0.001, om.MSpace.kObject)

        param = paramUtill.getDouble(paramPtr)
        currentLength = curveFn.findLengthFromParam(param)
        return param, currentLength, length

    def getCurvesFromLayerAPI(self, plug, layer, layerCache, baseAnimLayer):
        """
        """
        # special case for root layer
        if layer == baseAnimLayer.layer:
            isBaseAnimLayer = True
        else:
            isBaseAnimLayer = False

        allLayers = [x.layer for x in layerCache]

        it = om2.MItDependencyGraph(plug, om2.MFn.kInvalid,
                                    direction=om2.MItDependencyGraph.kUpstream,
                                    traversal=om2.MItDependencyGraph.kBreadthFirst,
                                    level=om2.MItDependencyGraph.kNodeLevel)

        target = None

        while not it.isDone():
            node = it.currentNode()

            if node in allLayers:
                it.prune()

            it.next()
            if node.apiType() in self.apiTypes('blendModes'):
                # iterate to the last node if is root
                if isBaseAnimLayer:
                    target = node
                    continue
                # otherwise check if the layer connected to weightA is the desired layer
                targetMFnDepNode = om2.MFnDependencyNode(node)
                layerPlug = targetMFnDepNode.findPlug('wa', True)  # weightA
                if layerPlug:
                    if layer == layerPlug.source().node():
                        target = node
                        break

        if target:
            targetMFnDepNode = om2.MFnDependencyNode(target)

            if isBaseAnimLayer:
                inputPlug = targetMFnDepNode.findPlug('ia', True)  # inputA
            else:
                inputPlug = targetMFnDepNode.findPlug('ib', True)  # inputB

            # is the blend node a rotation type?
            if target.apiType() in self.apiTypes('rotation'):
                idx = 0
                # find which index we come from
                if plug.isChild:
                    parent = plug.parent()
                    for i in range(parent.numChildren()):
                        if parent.child(i) == plug:
                            idx = i

                # try to get the same index from the input
                if inputPlug.isCompound and idx < inputPlug.numChildren():
                    inputPlug = inputPlug.child(idx)
                    curve = inputPlug.source().node()
                    if curve and curve.apiType() in self.apiTypes('animCurve'):
                        return curve

            elif inputPlug:
                curve = inputPlug.source().node()
                if curve and curve.apiType() in self.apiTypes('animCurve'):
                    return curve

        return None

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
        points = pointLists['pointLists'].get('orb', pointLists['pointLists']['cross'])
        return self.drawControl(points, list(range(0, len(points))), scale=scale)

    def drawCross(self, scale=1.0):
        points = pointLists['pointLists'].get('cross', pointLists['pointLists']['cross'])
        return self.drawControl(points, list(range(0, len(points))), scale=scale)

    def drawRedirectRoot(self, scale=1.0):
        points = pointLists['pointLists'].get('redirectRoot', pointLists['pointLists']['cross'])
        return self.drawControl(points, list(range(0, len(points))), scale=scale)

    def drawControl(self, pointlist, scale=1.0):
        curve = cmds.curve(degree=1,
                           knot=list(range(0, len(pointlist))),
                           point=[dt.Vector(x) * (scale / self.unit_conversion()) for x in pointlist])
        curve = pm.PyNode(curve)
        return curve, curve.getShape()

    @staticmethod
    def getMDagPath(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDagPath(0)

    @staticmethod
    def getDagNode(node):
        selList = om.MSelectionList()
        selList.add(node)
        nodeDagPath = om.MDagPath()
        selList.getDagPath(0, nodeDagPath)
        return nodeDagPath

    @staticmethod
    def getMObject(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDependNode(0)

    @staticmethod
    def getMatrix(node, matrix="worldMatrix"):
        '''
        Gets the world matrix of an object based on name.
        '''
        # TODO - have this use a shared function from self.funcs
        # Selection list object and MObject for our matrix
        selection = om2.MSelectionList()
        matrixObject = om2.MObject()

        # Adding object
        selection.add(node)

        # New api is nice since it will just return an MObject instead of taking two arguments.
        MObjectA = selection.getDependNode(0)

        # Dependency node so we can get the worldMatrix attribute
        fnThisNode = om2.MFnDependencyNode(MObjectA)

        # Get it's world matrix plug
        worldMatrixAttr = fnThisNode.attribute(matrix)

        # Getting mPlug by plugging in our MObject and attribute
        matrixPlug = om2.MPlug(MObjectA, worldMatrixAttr)
        try:
            matrixPlug = matrixPlug.elementByLogicalIndex(0)
        except:
            pass

        # Get matrix plug as MObject so we can get it's data.
        matrixObject = matrixPlug.asMObject()

        # Finally get the data
        worldMatrixData = om2.MFnMatrixData(matrixObject)
        worldMatrix = worldMatrixData.matrix()

        return worldMatrix

    def getMatrixOffset(self, node, storedMtx, postMtx, parentMtx):
        offset = parentMtx * (postMtx.inverse() * storedMtx) * parentMtx.inverse()

        transformMatrixObj = om2.MTransformationMatrix(offset)
        resultTranslate = transformMatrixObj.translation(om2.MSpace.kWorld)
        resultRotate = transformMatrixObj.rotation(asQuaternion=False)
        rotOrder = cmds.getAttr('%s.rotateOrder' % node)
        resultRotate.reorderIt(rotOrder)
        angles = [math.degrees(angle) for angle in (resultRotate.x, resultRotate.y, resultRotate.z)]

        resultScale = transformMatrixObj.scale(om2.MSpace.kWorld)
        return resultTranslate, angles
        # pm.xform('pCube1', relative=True, translation=resultTranslate)
        # pm.xform('pCube1', relative=True, rotation=angles)

    def getVectorToTarget(self, target, control):
        tempNode = cmds.createNode('transform')
        cmds.delete(cmds.parentConstraint(control, tempNode))
        controlMatrix = self.getMatrix(tempNode)
        targetMatrix = self.getMatrix(target)

        offset = targetMatrix * controlMatrix.inverse()
        mTransformMtx = om2.MTransformationMatrix(offset)
        trans = mTransformMtx.translation(om2.MSpace.kWorld)
        cmds.delete(tempNode)
        return trans

    def getWorldSpaceVectorOffset(self, control, target, vec=om.MVector.yAxis):
        controlNode = self.getDagNode(control)
        controlMatrix = controlNode.inclusiveMatrix()

        targetNode = self.getDagNode(target)
        targetMatrix = targetNode.inclusiveMatrix()

        vec = ((vec * controlMatrix) * targetMatrix.inverse()).normal()
        return dt.Vector(vec.x, vec.y, vec.z)

    @staticmethod
    def getMFnCurveFromPlug(plug):
        omslist = om2.MSelectionList()
        omslist.add(plug)
        mplug = omslist.getPlug(0)
        mcurve = oma2.MFnAnimCurve(mplug)

        return mplug, mcurve

    @staticmethod
    def getMfnCurveValues(mfnCurve, mTimeArray):
        return [mfnCurve.evaluate(m) for m in mTimeArray]



    def omGetPlugsFromLayer(self, layer, layerAttributes):
        MPlugDict = dict()
        MFnCurveDict = dict()
        for attribute in layerAttributes:
            plugName = self.getPlugsFromLayer(attribute, layer)
            if not plugName:
                continue
            mObj, mfnCurve = self.getMFnCurveFromPlug(plugName)
            if not mObj:
                continue
            if not mfnCurve:
                continue
            MPlugDict[attribute] = mObj
            MFnCurveDict[attribute] = mfnCurve
        return MPlugDict, MFnCurveDict

    def createMTimeArray(self, initialFrame, count):
        mTimeArray = om2.MTimeArray(count, om2.MTime())
        for x in xrange(count):
            mTimeArray[x] = om2.MTime(initialFrame + x, om2.MTime.uiUnit())
        return mTimeArray

    def createMTimePairArray(self, initialFrame, finalFrame):
        mTimeArray = om2.MTimeArray(2, om2.MTime())
        mTimeArray[0] = initialFrame
        mTimeArray[1] = finalFrame
        return mTimeArray

    def stripTailDigits(self, input):
        if input[-1].isdigit() or input[-1] == '_':
            return self.stripTailDigits(input[:-1])
        return input

    def getNotesAttr(self, node):
        node = pm.PyNode(node)
        if node.hasAttr('notes'):
            return node.notes.get()
        else:
            # go ahead and create attr
            node.addAttr('notes', dt='string')
            return node.notes.get()

    def isObjectMoving(self, obj):
        conns = cmds.listConnections(obj, source=True, destination=False)
        if conns:
            return True
        parent = cmds.listRelatives(obj, parent=True)
        if not parent:
            return False
        return self.isObjectMoving(parent[0])

    def splitSelectionToCharacters(self, sel):
        """
        Returns a dictionary for all characters found in the selection, namespace as key, controls as items
        :param sel:
        :return:
        """
        if not sel:
            return

        # split selection by character
        namespaces = list(set([x.split(':', 1)[0] for x in sel if ':' in x]))

        characters = {k: list() for k in namespaces}
        for s in sel:
            splitString = s.split(':', 1)
            if len(splitString) == 1:
                if ('') not in characters.keys():
                    characters[''] = list()
                characters[''].append(s)
                continue
            for ns in namespaces:
                if splitString[0] == ns:
                    characters[ns].append(s)
                    continue
        return characters

    def getCurrentRig(self, sel=None):
        """
        Used to determine the rig name/file, used when saving out rig data for tools
        :param sel:
        :return:
        """
        refName = None
        mapName = None
        fname = None
        if sel is None:
            sel = cmds.ls(sl=True)
        namespace = str()
        refNamespace = None
        if sel:
            refState = cmds.referenceQuery(sel[0], isNodeReferenced=True)
            if refState:
                # if it is referenced, check against pickwalk library entries
                refName = cmds.referenceQuery(sel[0], filename=True, shortName=True).split('.')[0]
                namespace = cmds.referenceQuery(sel[0], namespace=True)
            else:
                # might just be working in the rig file itself
                refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
            '''
            if ':' in sel[0]:
                namespace = sel[0].split(':', 1)[0]
            '''
        else:
            refName = cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]

        return refName, namespace  # TODO - fix up data path etc

    """
    SELECTION
    
    """

    def getSimilarControlsMinusPrefix(self, namespace, control, prefix, constraint=False, shape=False):
        wildcard = ('{ns}:*'.format(ns=namespace))
        matching = cmds.ls(wildcard, type='transform')
        if not constraint:
            matching = [x for x in matching if 'Constraint' not in cmds.objectType(x)]
        if shape:
            matching = [x for x in matching if cmds.listRelatives(x, shapes=True)]
        if control in matching:
            matching.remove(control)
        return [x.split(':')[-1] for x in matching]

    def getOppositeControl(self, name):
        namespace, control = name.rsplit(':', 1)
        prefix = re.split('[^a-zA-Z0-9]+', control)

        for pre in prefix:
            matches = self.getSimilarControlsMinusPrefix(namespace, control, pre, constraint=False, shape=False)
            close_matches = get_close_matches(control, [x.split(':')[-1] for x in matches])
            shorter = sorted(list(x for x in close_matches if len(x) < len(control)), key=len)
            longer = sorted(list(x for x in close_matches if len(x) >= len(control)), key=len)
            if len(shorter) < len(longer):
                shorter.extend([None] * (len(longer) - len(shorter)))
            if len(longer) < len(shorter):
                longer.extend([None] * (len(shorter) - len(longer)))
            longer = [x for x in longer if x != control]
            shorter = [x for x in shorter if x != control]
            merged = list()
            for index, x in enumerate(longer):
                merged.append(x)
                merged.append(shorter[index])
            merged = [i for i in merged if i is not control]

            for x in merged:
                obj = '{ns}:{ct}'.format(ns=namespace, ct=x)
                if cmds.objExists(obj):
                    return obj
        return
        st = self.stripTailDigits(control)
        tailLen = len(control) - len(st)

        strippedMatches = [c.rsplit(':', 1)[-1] for c in matchingPrefix if st not in c]
        if st in strippedMatches:
            strippedMatches.remove(st)
        # print ('matchingPrefix', matchingPrefix)
        # print ('strippedMatches', strippedMatches)
        matches = get_close_matches(st, [x[:len(x) - tailLen] for x in strippedMatches], cutoff=0.5)
        opposites = [m for m in matches if m != st]

        if opposites:
            if tailLen > 0:
                op = opposites[0] + control[-tailLen:]
            else:
                op = opposites[0]
            return namespace + ':' + op

    def getLowerControl(self, input):
        s = input.split(':')[-1]
        prefix = re.split('[^a-zA-Z0-9]+', s)
        matchingPrefix = self.getSimilarControls(input, prefix)
        st = self.stripTailDigits(s)
        tailLen = len(s) - len(st)

        matches = get_close_matches(st, [x[:len(x) - tailLen] for x in matchingPrefix])

    def getSimilarControls(self, namespace, sel, prefix, constraint=False, shape=True):
        matching = cmds.ls('{ns}:{ct}*'.format(ns=namespace, ct=prefix[0]), type='transform')
        if not constraint:
            matching = [x for x in matching if 'Constraint' not in cmds.objectType(x)]
        if shape:
            matching = [x for x in matching if cmds.listRelatives(x, shapes=True)]
        if sel in matching:
            matching.remove(sel)
        return matching

    """
    UI gubbinz
    """

    @staticmethod
    def findUI(name):
        allUI = cmds.lsUI(controls=True)
        matching = [x for x in allUI if name == x]
        return matching[-1]

    @staticmethod
    def getParentLayout(uiElement):
        UIType = cmds.objectTypeUI(uiElement)
        UIParent = mel.eval(UIType + " -query -parent " + uiElement)
        return UIParent

    @staticmethod
    def getWidgetPointer(name):
        ptr = omui.MQtUtil.findControl(findUI(name))
        if ptr:
            return ptr

    @staticmethod
    def addButton(form, uiElement, newButton):
        cmds.formLayout(form, e=True, attachForm=(newButton, 'top', 1))
        cmds.formLayout(form, e=True, attachNone=(newButton, 'left'))
        cmds.formLayout(form, e=True, attachNone=(newButton, 'bottom'))
        cmds.formLayout(form, e=True, attachControl=(newButton, 'right', 1, form + '|' + uiElement))

    def apiTypes(self, filter):
        if filter not in API_TYPES.keys():
            return cmds.error('type must be one of - ', API_TYPES.keys(), filter)
        return API_TYPES[filter]

    def getSelectedTransforms(self):
        nodes = []
        sel = om2.MGlobal.getActiveSelectionList()
        selectionIterator = om2.MItSelectionList(sel, om2.MFn.kDependencyNode)

        while not selectionIterator.isDone():
            s = selectionIterator.itemType()
            if s in self.apiTypes('selection'):
                nodes.append(om2.MFnDependencyNode(selectionIterator.getDependNode()))

            selectionIterator.next()

        return nodes

    def getAnimCurveSelectionAPI(self):
        return self.apiTypes('animCurveSelection')

    def getAnimCurveTypesAPI(self):
        return self.apiTypes('animCurve')

    def getNextFreeMultiIndex(self, attr_name, start_index=0, max_index=1000):
        '''Find the next unconnected multi index starting at the passed in index.'''
        # assume a max of 10 million connections
        for index in range(start_index, max_index):
            if len(cmds.connectionInfo('{}[{}]'.format(attr_name, index), sfd=True) or []) == 0:
                return index
            index += 1

        # No connections means the first index is available
        return 0

    def selectFromScreenApi(self, x, y, x_rect=None, y_rect=None):
        # get current selection
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)

        # api.MGlobal.selectionMethod()
        # select from screen
        args = [x, y]
        if x_rect and y_rect:
            om.MGlobal.selectFromScreen(x, y, x_rect, y_rect, om.MGlobal.kReplaceList)
        else:
            om.MGlobal.selectFromScreen(x, y, om.MGlobal.kReplaceList, 0)
        objects = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(objects)

        # restore selection
        om.MGlobal.setActiveSelectionList(sel, om.MGlobal.kReplaceList)

        # return the objects as strings
        fromScreen = []
        objects.getSelectionStrings(fromScreen)
        return fromScreen