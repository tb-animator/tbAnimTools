import maya
from maya import OpenMaya
from Abstract import *
from apps.tb_UI import *
from tb_mainFunctions import Functions

maya.utils.loadStringResourcesForModule(__name__)

import socket
import pickle
import hashlib
import os, sys
import traceback

if sys.version_info >= (2, 8):
    from urllib.request import *
    from urllib import request, parse, error
else:
    from urllib2 import *

import maya.api.OpenMayaAnim as oma2
import maya.api.OpenMaya as om2


scriptLocation = os.path.realpath(__file__)
scriptLocation2 = os.path.dirname(sys.argv[0])

baseAttrs = ['translateX', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
tAttrs = ['translateX', 'translateY', 'translateZ']
rAttrs = ['rotateX', 'rotateY', 'rotateZ']
Attrs = ['translate', 'rotate']

globalControlModeOptionVar = 'poseBlenderGlobalControlMode'
globalControlModes = ["Simple", "Ignore", "Set to start pose", "Set to end pose"]
channelModeOptionVar = 'poseBlenderChannelMode'
channelModes = ["Combined",
                "Individual",
                # "Combined, separate tY"
                ]
globalControlMode = get_option_var(globalControlModeOptionVar, globalControlModes[0])
channelMode = get_option_var(channelModeOptionVar, channelModes[0])


class windowInfo(object):
    """
    Used to store the window ranges
    """

    def __init__(self, start=0, end=0, startIndex=0, endIndex=0):
        self.start = start
        self.end = end
        self.startIndex = startIndex
        self.endIndex = endIndex


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory('tbAnimTools_AdjustmentBlend')

        self.addCommand(self.tb_hkey(name='tbAdjustmentBlend',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['tbAdjustmentBlender.adjustSelectedLayerDefault()']))
        self.addCommand(self.tb_hkey(name='tbAdjustmentBlendSelectionOnly',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['tbAdjustmentBlender.adjustSelectedLayerSelectedOnly()']))
        self.addCommand(self.tb_hkey(name='tbExtractThisFrame',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['tbAdjustmentBlender.extractThisFrame()']))
        self.addCommand(self.tb_hkey(name='tbExtractStartFrame',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['tbAdjustmentBlender.extractStartFrame()']))
        self.addCommand(self.tb_hkey(name='tbExtractEndFrame',
                                     annotation='useful comment',
                                     category=self.category,
                                     command=['tbAdjustmentBlender.extractEndFrame()']))
        self.addCommand(self.tb_hkey(name='tbOpenAdjustmentBlendToolbox',
                                     annotation='useful comment',
                                     category=self.category, command=['tbAdjustmentBlender.toolBoxUI()']))

        return self.commandList

    def assignHotkeys(self):
        return


class AdjustmentBlendTool(toolAbstractFactory):
    __instance = None
    toolName = 'tbAdjustmentBlender'
    hotkeyClass = hotkeys()
    funcs = Functions()

    productID = 'tbAdjustmentBlend'
    version = 1.1

    # global control
    globalControls = list()
    globalControlsConstraints = list()
    globalControlPins = dict()

    # LAYERS
    adjustmentBlendLayer = str()

    # DATA
    progressData = dict()
    bakeStart = float()
    bakeEnd = float()
    bakeDuration = float()

    # ASSET
    container = str()
    # MISC
    allPanels = list()
    filePath = None

    commandDict = dict()
    toolbox = None

    overrideLayerColour = 19
    additiveLayerColour = 18

    def __new__(cls):
        if AdjustmentBlendTool.__instance is None:
            AdjustmentBlendTool.__instance = object.__new__(cls)

        AdjustmentBlendTool.__instance.val = cls.toolName
        AdjustmentBlendTool.__instance.loadData()

        return AdjustmentBlendTool.__instance


    def __init__(self, **kwargs):
        self.globalControlMode = get_option_var(globalControlModeOptionVar, globalControlModes[0])
        self.commandDict = {"Simple": self.adjustSelectedLayer,
                            "Ignore Selected": self.adjustSelectedLayerIgnore,
                            "Set to start pose": self.adjustSelectedLayerKeepStart,
                            "Set to end pose": self.adjustSelectedLayerKeepEnd}

        set_option_var(globalControlModeOptionVar, self.globalControlMode)
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        self.layerAttributes = list()
        self.referenceLayerMPlugs = dict()
        self.referenceLayerMFnAnimCurves = dict()
        self.adjustmentLayerMPlugs = dict()
        self.adjustedLayerMFnAnimCurves = dict()
        self.resultLayerKeyValues = dict()
        self.additiveKeyValues = dict()  # the new positions, calculated as additive
        self.resultLayerCurveValues = dict()

        self.progressionLayerMPlugs = dict()
        self.progressionLayerMFnAnimCurves = dict()
        self.tempLayerKeyValues = dict()
        self.controlTranslationKeyTimes = dict()
        self.controlRotationKeyTimes = dict()
        self.controlTransformAtKeyTimes = dict()
        self.controlResultTranslatesAtKeyTimes = dict()
        self.controlResultRotatesAtKeyTimes = dict()

        self.affectedControls = dict()
        self.affectedMfnDepNodes = dict()

        self.tempControlDict = dict()
        self.tempControlMobjDict = dict()
        self.tempControlMfnDepNode = dict()
        self.tempControlConstraints = dict()

        # layers
        self.referencePoseLayer = None
        self.bakedProgressionLayer = None
        self.adjustmentBlendLayer = None
        self.globalControlLayer = None

        self.adjustmentWindows = list()
        self.uiUnit = om2.MTime.uiUnit()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(AdjustmentBlendTool, self).optionUI()
        return self.optionWidget

    def animLayerTabUI(self):
        adjustmentBlendButton = AnimLayerTabButton(icon='adjustmentBlend_SM.png',
                                                   toolTip=maya.stringTable['y_tb_AdjustmentBlend.kButton'])
        adjustmentBlendButton.setPopupMenu(AdjustmentButtonPopup)
        adjustmentBlendButton.clicked.connect(self.adjustSelectedLayerButtonCmd)
        return [adjustmentBlendButton]

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='Adjustment Blend', image='greasePencilPreGhostOff.png',
                    command='tbOpenAdjustmentBlendToolbox', sourceType='mel',
                    parent=parentMenu)

    def getToolboxWidget(self, widget):
        buttonWidth = 108
        buttonHeight = 40
        '''
        cmds.setParent()
        if cmds.menu(TOOLBOX_MENU, exists=True):
            cmds.deleteUI(TOOLBOX_MENU)
        menuBar = cmds.menu(TOOLBOX_MENU, label=TOOLBOX_MENU, tearOff=True)
        '''

        toolBoxWidget = QWidget()
        toolBoxLayout = QVBoxLayout()
        toolBoxLayout.setContentsMargins(0, 0, 0, 0)
        toolBoxLayout.setSpacing(0)
        toolBoxWidget.setLayout(toolBoxLayout)

        popupWidget = AdjustmentButtonPopup('AdjustmentButtonPopup', hideLabel=True)
        toolBoxLayout.addWidget(popupWidget)
        UILayout = QHBoxLayout()

        mainUIButton = ToolButton(text='Blend',
                                  width=None,
                                  icon=':/greasePencilPreGhostOff.png',
                                  command='tbAdjustmentBlend')

        UILayout.addWidget(mainUIButton)

        toolBoxLayout.addLayout(UILayout)
        return toolBoxWidget

    def toolBoxUI(self):
        if not self.toolbox:
            self.toolbox = BaseDialog(parent=getMainWindow(),
                                      title='tbAdjustmentBlend Toolbox', text=str(),
                                      lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, )
            # self.toolbox.setWindowOpacity(0.5)
            self.toolbox.mainLayout.addWidget(self.getToolboxWidget(self.toolbox))

        self.toolbox.show()
        self.toolbox.setFixedSize(self.toolbox.sizeHint())

    '''
    def __init__(self, layer=str(), globalControls=list(), globalControlMode="Ignore"):
        if layer:
            self.setAnimLayer(layer)
        self.globalControlMode = globalControlMode
        # TODO - make the global controls stored / viewable
        self.setGlobalControls(globalControls)
    '''

    def adjustSelectedLayerKeepStart(self):
        """
        Perform the adjustment blend on the selected layer, keep the global controls at the start pose
        :return:
        """
        self.globalControlMode = "Set to start pose"
        self.setAnimLayerFromSelection()
        self.adjustLayer(self.referencePoseLayer)

    def adjustSelectedLayerKeepEnd(self):
        """
        Perform the adjustment blend on the selected layer, keep the global controls at the end pose
        :return:
        """
        print('adjustSelectedLayerKeepEnd')
        self.globalControlMode = "Set to end pose"
        self.setAnimLayerFromSelection()
        self.adjustLayer(self.referencePoseLayer)

    def adjustSelectedLayerIgnore(self):
        """
        Perform the adjustment blend on the selected layer, keep the global controls at the end pose
        :return:
        """
        print('adjustSelectedLayerIgnore')
        self.globalControlMode = "Ignore Selected"
        self.setAnimLayerFromSelection()
        self.adjustLayer(self.referencePoseLayer)

    def adjustSelectedLayer(self):
        """
        Perform the adjustment blend on the selected layer, ignore the global control
        :return:
        """
        print('adjustSelectedLayer')
        if not self.getSelectedLayer():
            return noLayerWidget()
        self.setAnimLayerFromSelection()
        if not self.referencePoseLayer:
            return noLayerWidget()
        self.adjustLayer(self.referencePoseLayer)

    def adjustSelectedLayerNoIgnore(self):
        """
        Perform the adjustment blend on the selected layer, ignore the global control
        :return:
        """
        print('adjustSelectedLayerNoIgnore')
        cmds.select(clear=True)
        self.setAnimLayerFromSelection()
        self.adjustLayer(self.referencePoseLayer)

    def adjustSelectedLayerDefault(self):
        """
        Perform the adjustment blend on the selected layer, ignore the global control
        :return:
        """
        # self.commandDict[get_option_var(globalControlModeOptionVar, globalControlModes[0])]()
        self.commandDict[globalControlModes[0]]()

    def adjustSelectedLayerButtonCmd(self):
        if cmds.getModifiers() == 4:
            # CTRL is pressed - use selection only
            self.adjustSelectedLayerSelectedOnly()
        else:
            self.adjustSelectedLayerDefault()

    def adjustSelectedLayerSelectedOnly(self):
        """
        Extract the selected objects
        :return:
        """
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning("No objects selected, select some objects in the current layer")
        layer = self.getSelectedLayer()
        if not layer:
            return noLayerWidget()

        # get the selected controls from this layer
        extractedLayer = self.funcs.extractAnimationLayers(sel)
        self.funcs.deselectLayer(layer)
        self.funcs.selectLayer(extractedLayer[0])

        self.adjustSelectedLayerDefault()

    def adjustLayer(self, layerName=None):
        self.referencePoseLayer = layerName
        autoKeyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(state=False)
        cmds.undoInfo(openChunk=True)
        try:
            self.calculate()
        except:
            cmds.warning(traceback.format_exc())
        finally:
            cmds.refresh()
            cmds.currentTime(cmds.currentTime(query=True))
            cmds.undoInfo(closeChunk=True)
            cmds.autoKeyframe(state=autoKeyState)

    def calculate(self):
        self.layerAttributes = list()
        self.referenceLayerMPlugs = dict()
        self.referenceLayerMFnAnimCurves = dict()
        self.adjustmentLayerMPlugs = dict()
        self.adjustedLayerMFnAnimCurves = dict()
        self.resultLayerKeyValues = dict()
        self.additiveKeyValues = dict()  # the new positions, calculated as additive
        self.resultLayerCurveValues = dict()

        self.progressionLayerMPlugs = dict()
        self.progressionLayerMFnAnimCurves = dict()
        self.tempLayerKeyValues = dict()
        self.controlTranslationKeyTimes = dict()
        self.controlRotationKeyTimes = dict()
        self.controlTransformAtKeyTimes = dict()
        self.controlResultTranslatesAtKeyTimes = dict()
        self.controlResultRotatesAtKeyTimes = dict()

        self.affectedControls = dict()
        self.affectedMfnDepNodes = dict()

        self.tempControlDict = dict()
        self.tempControlMobjDict = dict()
        self.tempControlMfnDepNode = dict()
        self.tempControlConstraints = dict()

        # layers
        # self.referencePoseLayer = None
        self.bakedProgressionLayer = None
        self.adjustmentBlendLayer = None
        self.globalControlLayer = None

        self.adjustmentWindows = list()
        self.uiUnit = om2.MTime.uiUnit()

        # TODO - one object in layer, should not ignore itself, breaks things
        self.globalControls = None
        '''
        if mode != "Simple":
            sel = cmds.ls(selection=True, type='transform')
            if sel:
                self.globalControls = sel
            else:
                self.globalControls = None
        '''

        if not self.referencePoseLayer or self.referencePoseLayer == 'BaseAnimation':
            return InfoPromptWidget(title='No layer selected',
                                    buttonText='Ok',
                                    imagePath=helpPath,
                                    error=True,
                                    image='BAD',
                                    gif=False,
                                    helpString='Please select your additive animation layer')
        self.setControls(self.referencePoseLayer)
        self.referenceLayerMPlugs, self.referenceLayerMFnAnimCurves = self.getPlugsFromLayer(self.referencePoseLayer)
        self.calculateAdjustmentWindows()
        self.bakeProgression()
        self.progressionLayerMPlugs, self.progressionLayerMFnAnimCurves = self.getPlugsFromLayer(
            self.bakedProgressionLayer)

        self.calculateProgress()
        self.createAdjustmentBlendLayer()
        self.adjustmentLayerMPlugs, self.adjustedLayerMFnAnimCurves = self.getPlugsFromLayer(self.adjustmentBlendLayer)

        # self.setGlobalControlRestPosition()
        # self.getControlTransformsAtKeyTimes()
        # cmds.autoKeyframe(state=autoKeyState)

        self.getResultLayerCurveValues()
        # get the curves from the baked layer
        # calculate the progression on the baked layer

        self.getTempLayerCurveValues()
        self.getAdditiveDifference()

        self.adjustKeyValues()
        self.setFinalCurveValues()
        self.restoreAdjustedLayer()
        # self.setGlobalControlPosition()
        self.deleteTempLayer()
        self.deselect_layers()

    def deselect_layers(self):
        for layers in cmds.ls(type='animLayer'):
            self.funcs.deselectLayer(layers)
        self.funcs.selectLayer(self.adjustmentBlendLayer)

    def restoreAdjustedLayer(self):
        zeroedAttrTypes = ['enum', 'bool']
        layerAttributes = cmds.animLayer(self.adjustmentBlendLayer, query=True, attribute=True)

        zeroedAttrs = list()
        if layerAttributes:
            zeroedAttrs = [a for a in layerAttributes if cmds.getAttr(a, type=True) in zeroedAttrTypes]
            if zeroedAttrs:
                cmds.animLayer(self.adjustmentBlendLayer, edit=True, removeAttribute=zeroedAttrs)
                cmds.animLayer(self.adjustmentBlendLayer, edit=True, attribute=zeroedAttrs)
                cmds.setKeyframe(zeroedAttrs, identity=True, time=self.bakeStart)
                cmds.setKeyframe(zeroedAttrs, identity=True, time=self.bakeEnd)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, override=False)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, mute=False)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, selected=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, preferred=True)

        cmds.animLayer(self.adjustmentBlendLayer, edit=True, lock=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, lock=False)
        cmds.setAttr(self.adjustmentBlendLayer + ".scaleAccumulationMode", 1)

    @staticmethod
    def getMDagPath(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDagPath(0)

    @staticmethod
    def getMObject(node):
        selList = om2.MSelectionList()
        selList.add(node)
        return selList.getDependNode(0)

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

    @staticmethod
    def has_anim_curve(plug_name):
        # Get the MPlug object from the plug name
        sel = om2.MSelectionList()
        sel.add(plug_name)
        plug = sel.getPlug(0)

        # Check if there is an animation curve connected to this plug
        connected_plugs = plug.connectedTo(True, False)  # Get the source plugs only

        for p in connected_plugs:
            if p.node().hasFn(om2.MFn.kAnimCurve):
                return True
        return False

    def getPlugsFromLayer(self, layer):
        MPlugDict = dict()
        MFnCurveDict = dict()
        for attribute in cmds.animLayer(layer, query=True, attribute=True):
            # insert a check for a proxy attribute
            if self.getIsProxyAttribute(attribute):
                continue
            plugName = getChannelPlugsFromAnimLayer(attribute, layer)
            if not plugName:
                continue
            if not self.has_anim_curve(plugName):
                continue
            mObj, mfnCurve = self.getMFnCurveFromPlug(plugName)

            if not mObj:
                continue
            if not mfnCurve:
                continue
            MPlugDict[attribute] = mObj
            MFnCurveDict[attribute] = mfnCurve
        return MPlugDict, MFnCurveDict

    def getIsProxyAttribute(self, obj_attr):
        # Takes a string like 'psphere1.attributeName'
        # checks if the attribute is a proxy attribute
        # returns mel command to create that proxy attribute

        if '.' not in obj_attr:
            return None  # Ensure the input is in the correct format 'object.attribute'

        node, attr_name = obj_attr.split('.', 1)  # Split into object and attribute

        proxyAttrCmds = []
        selectionList = OpenMaya.MSelectionList()
        try:
            selectionList.add(node)
        except:
            return None

        mobj = OpenMaya.MObject()
        selectionList.getDependNode(0, mobj)
        dep = OpenMaya.MFnDependencyNode(mobj)

        for i in range(dep.attributeCount()):
            attr = OpenMaya.MFnAttribute(dep.attribute(i))
            if attr.name() == attr_name:
                if attr.isProxyAttribute():
                    # We have full access to MFnAttribute here
                    proxyAttrCmds.append(f'{node}.{attr_name}')
                break  # Exit loop after finding the attribute
        return proxyAttrCmds if proxyAttrCmds else None

    def setControls(self, layer):
        layerMPlugs, layerMFnAnimCurves = self.getPlugsFromLayer(layer)
        self.affectedControls.clear()
        self.affectedMfnDepNodes.clear()
        self.layerAttributes = layerMPlugs.keys()
        for attr in self.layerAttributes:
            control = attr.split('.')[0]
            if control not in self.affectedControls.keys():
                self.affectedControls[control] = self.getMObject(control)
                self.affectedMfnDepNodes[control] = om2.MFnDependencyNode(self.affectedControls[control])
            if control not in self.controlTransformAtKeyTimes.keys():
                self.controlTransformAtKeyTimes[control] = list()
                self.controlResultTranslatesAtKeyTimes[control] = list()
                self.controlResultRotatesAtKeyTimes[control] = list()
                self.controlTranslationKeyTimes[control] = list()
                self.controlRotationKeyTimes[control] = list()

    def createTempControls(self):
        """
        Create temporary nodes that will drive our anim control (minus the global control)
        These are needed as we don't know what order to set the world transforms of each control in
        :return:
        """
        self.tempControlDict.clear()
        self.tempControlMfnDepNode.clear()
        self.tempControlConstraints.clear()
        dag = om2.MDagModifier()
        for control in self.affectedControls.keys():
            if control in self.globalControls:
                continue
            tempControl = cmds.createNode('transform', name=control + '_temp')
            self.tempControlDict[control] = tempControl
            self.tempControlMobjDict[control] = self.getMObject(tempControl)
            self.tempControlMfnDepNode[control] = om2.MFnDependencyNode(self.tempControlMobjDict[control])
            self.tempControlConstraints[control] = cmds.parentConstraint(tempControl, control)
        dag.doIt()

    def deleteTempControls(self):
        for item in self.tempControlDict.values():
            cmds.delete(item)

    def deleteTempConstraints(self):
        for item in self.tempControlConstraints.values():
            cmds.delete(item)

    def deleteTempLayer(self):
        cmds.delete(self.bakedProgressionLayer)
        if self.globalControlLayer:
            cmds.delete(self.globalControlLayer)

    def setGlobalControls(self, controls):
        if not isinstance(controls, list):
            controls = [controls]
        self.globalControls = controls

    def setAnimLayer(self, layer):
        self.referencePoseLayer = layer

    def getSelectedLayer(self):
        allLayers = cmds.ls(type='animLayer')
        if not allLayers:
            return None
        for layer in allLayers:
            if cmds.animLayer(layer, query=True, selected=True):
                return layer
        return None

    def setAnimLayerFromSelection(self):
        layer = self.getSelectedLayer()
        if not layer:
            return noLayerWidget()
        self.referencePoseLayer = layer

    def calculateAdjustmentWindows(self):
        """
        Calculate the pairs of keys for adjustment
        :return:
        """
        layerKeys = list()
        for attribute in self.layerAttributes:
            curve = self.referenceLayerMFnAnimCurves[attribute]
            for key in range(curve.numKeys):
                value = curve.input(key).value
                if value not in layerKeys:
                    layerKeys.append(value)
        self.layerkeys = sorted(layerKeys)

        if not self.layerkeys:
            return cmds.error('no curves found on layer')

        self.layerKeyMTimes = [om2.MTime(int(x), self.uiUnit) for x in self.layerkeys]
        self.keyRange = int(self.layerkeys[-1]) - int(self.layerkeys[0]) + 1
        self.bakeStart = self.layerkeys[0]
        self.bakeEnd = self.layerkeys[-1]
        # loop over key pairs and set up adjustment window info
        for i in range(1, len(self.layerkeys)):
            self.adjustmentWindows.append(windowInfo(start=int(self.layerkeys[i - 1]),
                                                     end=int(self.layerkeys[i]),
                                                     startIndex=i - 1,
                                                     endIndex=i))

    def createMTimeArray(self, initialFrame, count):
        mTimeArray = om2.MTimeArray(count, om2.MTime())
        for x in range(count):
            mTimeArray[x] = om2.MTime(initialFrame + x, self.uiUnit)
        return mTimeArray

    def getResultLayerCurveValues(self):
        for key, mcurve in self.adjustedLayerMFnAnimCurves.items():
            self.resultLayerKeyValues[key] = [mcurve.value(x) for x in range(len(self.layerkeys))]

    def getTempLayerCurveValues(self):
        for key, mcurve in self.progressionLayerMFnAnimCurves.items():
            self.tempLayerKeyValues[key] = [mcurve.value(x) for x in range(len(self.layerkeys))]

    def getControlTransformsAtKeyTimes(self, animLayer=str()):
        """
        get each controls world transform at each key time on the adjustment layer
        :return:
        """
        # TODO - looks like this is giving bad values, maybe just rely on getAttr etc
        tempNodes = dict()
        tempConstraints = dict()

        for control, mobj in self.affectedControls.items():
            tempNodes[control] = cmds.createNode('transform', name=control + '_pin')
        # self.adjustmentBlendLayer = cmds.animLayer('Adjusted', override=True, passthrough=True)

        layerKeys = list()
        self.layerAttributes = cmds.animLayer(animLayer, query=True, attribute=True)
        self.referenceLayerMPlugs, self.referenceLayerMFnAnimCurves = self.getPlugsFromLayer(animLayer)
        for attribute in self.layerAttributes:
            curve = self.referenceLayerMFnAnimCurves[attribute]
            for key in range(curve.numKeys):
                value = curve.input(key).value
                if value not in layerKeys:
                    layerKeys.append(value)
        self.layerkeys = sorted(layerKeys)

        if not self.layerkeys:
            return cmds.error('no curves found on layer')

        self.layerKeyMTimes = [om2.MTime(int(x), self.uiUnit) for x in self.layerkeys]

        for key in self.layerkeys:
            cmds.currentTime(key)
            # toggle off the temp layer
            if self.globalControlLayer:
                self.toggleGlobalControlLayer(state=True)
            for control, mobj in self.affectedControls.items():
                if control in self.globalControls:
                    continue
                # pin the temp control to the control
                cmds.delete(cmds.parentConstraint(control, tempNodes[control]))
                # constrain the control to a temp node
                constraint = str(self.funcs.safeParentConstraint(tempNodes[control],
                                                                 control,
                                                                 orientOnly=False,
                                                                 maintainOffset=False))
                tempConstraints[control] = constraint

            # restore the temp layer
            if self.globalControlLayer:
                self.toggleGlobalControlLayer(state=False)

            for control, mobj in self.affectedControls.items():
                if control in self.globalControls:
                    continue
            # read the control translate/rotates
            cmds.setKeyframe(list(self.affectedControls.keys()))
            cmds.delete(list(tempConstraints.values()))

            # self.controlTranslationKeyTimes[control].append(cmds.xform(control, translation=True, worldSpace=False, absolute=False, query=True))
            # self.controlRotationKeyTimes[control].append(cmds.xform(control, rotation=True, worldSpace=False, absolute=False,  query=True))

            # delete the temp control
            '''
            targetMTMatrix = om2.MTransformationMatrix(om2.MMatrix(cmds.xform(control, matrix=True, ws=1, q=True)))
            rotatePivot = om2.MVector(cmds.xform(control, rotatePivot=True, ws=1, q=True))
            targetMTMatrix.setTranslation(rotatePivot, om2.MSpace.kWorld)
            currentTransform = self.om_plug_worldMatrix_at_time('worldMatrix', mobj, currentMDG)
            # currentRotatePivot = self.om_plug_worldMatrix_at_time('worldMatrix', mobj, currentMDG)

            tfmMatrix = om2.MTransformationMatrix(currentTransform)
            # tfmMatrix.setTranslation(om2.MVector(0, 0, 0), om2.MSpace.kWorld)
            self.controlTransformAtKeyTimes[control].append(tfmMatrix)
            '''

        if self.globalControlLayer:
            self.toggleGlobalControlLayer(state=True)
            cmds.delete(self.globalControlLayer)
            self.removeGlobalControlsFromLayer(animLayer)
        # cmds.filterCurve(cmds.animLayer(self.adjustmentBlendLayer, query=True, animCurves=True))
        for key in self.layerkeys:
            cmds.currentTime(key)
            for control, mobj in self.affectedControls.items():
                if control in self.globalControls:
                    continue
                # read the control translate/rotate

                self.controlTranslationKeyTimes[control].append(
                    cmds.xform(control, translation=True, worldSpace=False, absolute=False, query=True))
                self.controlRotationKeyTimes[control].append(
                    cmds.xform(control, rotation=True, worldSpace=False, absolute=False, query=True))
        cmds.delete(list(tempNodes.values()))

    @staticmethod
    def om_plug_worldMatrix_at_time(matrix, dep_node, mdg):

        '''
        Getting the plug from openMaya.
        Then create a time mdgContext and evaluate it.
        This is the fastest with layer compatability... however i suspect there to be issues when doing complex simulations.

        :param dep_node: object string name i.e. "pSphere1"
        :param attr: the attribute to check i.e. "tx"
        :return: a list of values per frame.
        '''

        objMfn = om2.MFnDependencyNode(dep_node)
        ## Get the plug of the node. (networkedplug = False, as it no longer profides a speed improvement)
        plug = objMfn.findPlug(matrix, False).elementByLogicalIndex(0)
        rotatePivotXPlug = objMfn.findPlug('rotatePivotX', False)
        rotatePivotYPlug = objMfn.findPlug('rotatePivotY', False)
        rotatePivotZPlug = objMfn.findPlug('rotatePivotZ', False)
        value = om2.MFnMatrixData(plug.asMObject(mdg)).matrix()
        rotatePivotValueX = rotatePivotXPlug.asFloat(mdg)
        rotatePivotValueY = rotatePivotYPlug.asFloat(mdg)
        rotatePivotValueZ = rotatePivotZPlug.asFloat(mdg)
        tfmMatrix = om2.MTransformationMatrix()
        tfmMatrix.setTranslation(om2.MVector(rotatePivotValueX, rotatePivotValueY, rotatePivotValueZ),
                                 om2.MSpace.kWorld)
        return tfmMatrix.asMatrix() * value

    def createAdjustmentBlendLayer(self):
        self.adjustmentBlendLayer = cmds.animLayer(self.referencePoseLayer + "_adjust", copy=self.referencePoseLayer)
        cmds.setAttr(self.adjustmentBlendLayer + '.ghostColor', self.additiveLayerColour)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, moveLayerAfter=self.referencePoseLayer)

        for key in self.layerkeys:
            cmds.setKeyframe(list(self.affectedControls.keys()), time=(key,), insert=True,
                             animLayer=self.adjustmentBlendLayer)

    def removeGlobalControlsFromLayer(self, layer):
        for control in self.globalControls:
            for attr in self.layerAttributes:
                if mel.eval("plugNode \"%s\"" % (attr)) == control:
                    cmds.animLayer(layer, edit=True, removeAttribute=attr)

    def bakeProgression(self):
        """
        Bake a temp layer to get a snapshot of the main animation
        Add support for using just the base anim layer as reference
        :return:
        """
        cmds.animLayer(self.referencePoseLayer, edit=True, mute=True)
        self.bakedProgressionLayer = cmds.animLayer(self.referencePoseLayer + '_bakedProgress', override=True)

        allLayers = cmds.ls(type='animLayer')

        muteStateDict = {layer: cmds.animLayer(layer, query=True, mute=True) for layer in allLayers}

        cmds.bakeResults(list(self.affectedControls.keys()),
                         time=(self.bakeStart, self.bakeEnd),
                         simulation=False,
                         destinationLayer=self.bakedProgressionLayer,
                         bakeOnOverrideLayer=True,
                         sampleBy=1)
        cmds.filterCurve(cmds.animLayer(self.bakedProgressionLayer, query=True, animCurves=True))
        cmds.animLayer(self.bakedProgressionLayer, edit=True, mute=True)

    def getAdditiveDifference(self):
        """
        Get the difference between the temp result layer and the additive result layer
        :return:
        """
        for key, tempCurve in self.progressionLayerMFnAnimCurves.items():
            resultLayerKeyValues = self.resultLayerKeyValues.get(key, None)
            tempLayerKeyValues = self.tempLayerKeyValues.get(key, None)

            if not resultLayerKeyValues:
                continue
            if not tempLayerKeyValues:
                continue
            self.additiveKeyValues[key] = [0.0] * len(resultLayerKeyValues)
            refCurve = self.adjustedLayerMFnAnimCurves[key]

            for index, keyTime in enumerate(self.layerkeys):
                t = om2.MTime(keyTime, self.uiUnit)
                self.additiveKeyValues[key][index] = refCurve.evaluate(t) - tempCurve.evaluate(t)

    def calculateProgress(self):
        # make progress combined for rotation, also one for translation, other stuff is by curve
        self.progressData = dict()
        channelOption = get_option_var(channelModeOptionVar, channelModes[0])
        for key, mcurve in self.progressionLayerMFnAnimCurves.items():
            # get the progress of each individual curve, for the whole length of the animation
            # if attribute name is in translate or rotate list, remove the axis from the name, add the result to the existing entry
            keyValues = accumulateProgress([mcurve.value(x) for x in range(mcurve.numKeys)])
            obj, attr = key.split('.')
            finalKey = key

            if channelOption == channelModes[0]:  # combined
                if attr in baseAttrs:
                    finalKey = key[:-1]
                else:
                    finalKey = key
            if finalKey not in list(self.progressData.keys()):
                self.progressData[finalKey] = keyValues
            else:
                self.progressData[finalKey] = [x + y for x, y in zip(self.progressData[finalKey], keyValues)]

    def adjustKeyValues(self):
        for key, mcurve in self.adjustedLayerMFnAnimCurves.items():
            progressData = self.progressData.get(key, self.progressData.get(key[:-1], None))
            if not progressData:
                continue
            self.shiftKeyValuesInWindow(mCurve=mcurve, key=key, progressData=progressData)

    def shiftKeyValuesInWindow(self, mCurve=None, key=None, progressData=None):
        resultValues = [0.0] * self.keyRange

        for window in self.adjustmentWindows:
            progressStart = progressData[window.start - int(self.bakeStart)]
            progressEnd = progressData[window.end - int(self.bakeStart)]

            startValue = self.resultLayerKeyValues[key][window.startIndex]
            endValue = self.resultLayerKeyValues[key][window.endIndex]

            for x in range(window.start, window.end + 1):
                if progressEnd - progressStart != 0:
                    windowProgress = (progressData[x - int(self.bakeStart)] - progressStart) / (
                            progressEnd - progressStart)
                else:
                    windowProgress = float(x - window.start) / float(window.end - window.start)
                # might not work if not starting at frame 0
                resultValues[x - int(self.bakeStart)] = lerpFloat(startValue,
                                                                  endValue,
                                                                  windowProgress)
        self.resultLayerCurveValues[key] = resultValues

    def setFinalCurveValues(self):
        dg = om2.MDGModifier()
        self.resultMTimeArray = self.createMTimeArray(self.layerKeyMTimes[0].value, self.keyRange)
        for key, mcurve in self.adjustedLayerMFnAnimCurves.items():
            sources = self.adjustmentLayerMPlugs[key].connectedTo(True, False)
            for i in range(len(sources)):
                dg.disconnect(sources[i], self.adjustmentLayerMPlugs[key])

            dg.doIt()

            adjustedCurve = oma2.MFnAnimCurve(self.adjustmentLayerMPlugs[key])
            adjustedCurve.create(self.adjustmentLayerMPlugs[key], self.adjustedLayerMFnAnimCurves[key].animCurveType,
                                 dg)
            adjustedCurve.addKeys(self.resultMTimeArray,
                                  self.resultLayerCurveValues[key],
                                  oma2.MFnAnimCurve.kTangentGlobal,
                                  oma2.MFnAnimCurve.kTangentGlobal)
            dg.doIt()

    def setGlobalControlRestPosition(self, controls=list(), animLayer=str()):
        """
        Get the position to place the global control at
        Place the global control at the location on a temporary layer
        :return:
        """
        if not animLayer:
            return
        if not controls:
            return
        self.globalControlLayer = cmds.animLayer(animLayer + 'globalTemp', override=True)
        cmds.animLayer(self.globalControlLayer, edit=True, passthrough=True)
        cmds.select(controls, replace=True)
        cmds.animLayer(self.globalControlLayer, edit=True, addSelectedObjects=True)
        cmds.animLayer(self.globalControlLayer, edit=True, selected=True, preferred=True)

        cmds.setKeyframe(identity=True)

    def pinControls(self, frame=0):
        cmds.setCurrentTime(frame)

    def toggleGlobalControlLayer(self, state=False):
        if not self.globalControlLayer:
            return
        cmds.animLayer(self.globalControlLayer, edit=True, mute=state)

    def setGlobalControlPosition(self):
        if not self.globalControls:
            return None

        translates = dict()
        rotates = dict()
        # if self.globalControlMode != "Ignore":
        cmds.animLayer(self.globalControlLayer, edit=True, mute=False)
        for c in self.globalControls:
            translates[c] = cmds.xform(c, query=True, translation=True, absolute=True)
            rotates[c] = cmds.xform(c, query=True, rotation=True, absolute=True)
        cmds.animLayer(self.globalControlLayer, edit=True, mute=True)
        cmds.select(self.globalControls, replace=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, addSelectedObjects=True)

        for c in self.globalControls:
            cmds.xform(c, translation=translates[c], absolute=True)
            cmds.xform(c, rotation=rotates[c], absolute=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, selected=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, preferred=True)
        cmds.setKeyframe()

    def copyResultToControls(self):
        cmds.animLayer(self.referencePoseLayer, edit=True, mute=True)
        cmds.bakeResults(list(self.controlSpaceAdditiveNodes.values()),
                         time=(self.bakeStart, self.bakeEnd),
                         simulation=False,
                         sampleBy=1)

        cmds.select(list(self.controlSpaceAdditiveNodes.keys()), replace=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, addSelectedObjects=True)
        if self.globalControlMode != "Ignore":
            cmds.select(self.globalControls)
            cmds.animLayer(self.adjustmentBlendLayer, edit=True, addSelectedObjects=True)
            cmds.animLayer(self.adjustmentBlendLayer, edit=True, selected=True, preferred=True)
            cmds.setKeyframe(self.globalControls, time=cmds.currentTime(query=True),
                             animLayer=self.adjustmentBlendLayer,
                             dirtyDG=True)
            cmds.delete(list(self.globalControlPins.values()))

        for control in self.affectedControls.keys():
            cmds.animLayer(self.adjustmentBlendLayer, edit=True,
                           removeAttribute=cmds.listAttr(control, userDefined=True))
        for layer in cmds.ls(type='animLayer'):
            cmds.animLayer(layer, edit=True, selected=False, preferred=False)

        cmds.animLayer(self.adjustmentBlendLayer, edit=True, selected=True)
        cmds.animLayer(self.adjustmentBlendLayer, edit=True, preferred=True)

        for key, node in self.controlSpaceAdditiveNodes.items():
            if key not in self.globalControls:
                cmds.copyKey(node, animLayer='BaseAnimation')
                cmds.pasteKey(key, animLayer=self.adjustmentBlendLayer)

    def extractGlobalControl(self):
        layer = self.funcs.get_selected_layers()
        self.globalControls = cmds.ls(sl=True)
        if not self.globalControls:
            return cmds.warning('Please select global control')
        if not layer:
            return cmds.warning('No layer selected')
        self.setGlobalControlRestPosition(controls=self.globalControls, animLayer=str(layer[0]))
        cmds.warning('Not currently implemented')
        self.setControls(str(layer[0]))
        self.getControlTransformsAtKeyTimes(str(layer[0]))

    def extractThisFrame(self):
        self.extractGlobalControl()

    def extractStartFrame(self):
        currentTime = cmds.currentTime(query=True)
        cmds.currentTime(cmds.playbackOptions(query=True, min=True))
        self.extractGlobalControl()
        cmds.currentTime(currentTime)

    def extractEndFrame(self):
        currentTime = cmds.currentTime(query=True)
        cmds.currentTime(cmds.playbackOptions(query=True, max=True))
        self.extractGlobalControl()
        cmds.currentTime(currentTime)


def safeDeleteList(input):
    for i in input:
        if not cmds.objExists(i):
            continue
        cmds.delete(i)


def getChannelPlugsFromAnimLayer(nodeAttr, animLayer):
    """
    Find the animBlendNode plug corresponding to the given node, attribute,
    and animation layer.
    """
    if not isInAnimationLayer(nodeAttr, animLayer):
        return None
    plug = None
    basePlug = None
    layerPlug = None
    if animLayer == cmds.animLayer(q=True, root=True):
        # For the base animation layer, traverse the chain of animBlendNodes all
        # the way to the end.  The plug will be "inputA" on that last node.
        blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
        blendNodeHistory = cmds.listHistory(blendNode)
        lastAnimBlendNode = cmds.ls(blendNodeHistory, type='animBlendNodeBase')[-1]
        if cmds.objectType(lastAnimBlendNode, isa='animBlendNodeAdditiveRotation'):
            letterXYZ = nodeAttr[-1]
            plug = '{0}.inputA{1}'.format(lastAnimBlendNode, letterXYZ.upper())
        else:
            plug = '{0}.inputA'.format(lastAnimBlendNode)
    else:
        cmd = 'animLayer -q -layeredPlug "{0}" "{1}"'.format(nodeAttr, animLayer)
        blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
        blendNodeHistory = cmds.listHistory(blendNode)
        firstAnimBlendNode = cmds.ls(blendNodeHistory, type='animBlendNodeBase')[0]
        basePlug = firstAnimBlendNode + '.inputA'
        layerPlug = firstAnimBlendNode + '.inputB'

        plug = mel.eval(cmd)
    return plug


def isInAnimationLayer(nodeName, animLayer):
    objAnimLayers = cmds.animLayer([nodeName], q=True, affectedLayers=True) or []
    if animLayer in objAnimLayers:
        return True
    return False


def getAvailableAttributes(node):
    '''
    returns 2 lists of attrs that are not available for constraining
    '''
    attrs = ['X', 'Y', 'Z']

    lockedTranslates = []
    lockedRotates = []
    for attr in attrs:
        if not cmds.getAttr(node + '.' + 'translate' + attr, settable=True):
            lockedTranslates.append(attr.lower())
        if not cmds.getAttr(node + '.' + 'rotate' + attr, settable=True):
            lockedRotates.append(attr.lower())

    return lockedTranslates, lockedRotates


def accumulateProgress(values):
    # create an empty list
    result = [float()] * len(values)
    for i in range(1, len(values)):
        result[i] = (result[max(0, i - 1)] + abs(values[i] - values[max(0, i - 1)]))
    return result


def lerpFloat(a, b, w):
    return a + w * (b - a);


class AdjustmentButtonPopup(ButtonPopup):
    def __init__(self, name, parent=None, hideLabel=False):
        super(ButtonPopup, self).__init__(parent)
        self.hideLabel = hideLabel
        self.setWindowTitle("{0} Options".format(name))

        self.setWindowFlags(Qt.Popup)

        self.layout = QFormLayout(self)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.channelRadioGroup = radioGroupVertical(formLayout=self.layout,
                                                    tooltips=[maya.stringTable['y_tb_AdjustmentBlend.kChannelCombined'],
                                                              maya.stringTable[
                                                                  'y_tb_AdjustmentBlend.kChannelIndividual']],
                                                    optionVarList=channelModes,
                                                    optionVar=channelModeOptionVar,
                                                    defaultValue=get_option_var(channelModeOptionVar,
                                                                                  channelModes[0]),
                                                    label=str())

    def create_layout(self):
        tbAdjustmentBlendLabel = QLabel('tbAdjustmentBlend')
        extractOptionLabel = QLabel('Extract Controls')
        rootOptionLabel = QLabel('Global control stripping')
        channelOptionLabel = QLabel('Channel options')
        if not self.hideLabel:
            self.layout.addRow(tbAdjustmentBlendLabel)
        self.layout.addRow(rootOptionLabel)
        button = QPushButton('Extract Selection')
        button.clicked.connect(create_callback(create_callback(AdjustmentBlendTool().extractThisFrame)))
        self.layout.addRow(button)
        self.layout.addRow(extractOptionLabel)
        # make buttons for control extraction
        for label in ['kSimple', 'kStart', 'kEnd']:
            lbl = maya.stringTable['y_tb_AdjustmentBlend.%s' % label]
            button = QPushButton(lbl)
            commands = {'kSimple': AdjustmentBlendTool().extractThisFrame,
                        'kStart': AdjustmentBlendTool().extractStartFrame,
                        'kEnd': AdjustmentBlendTool().extractEndFrame}
            button.clicked.connect(create_callback(commands[label]))

            self.layout.addRow(button)

        self.layout.addRow(channelOptionLabel)
        for label, widget in self.channelRadioGroup.returnedWidgets:
            self.layout.addRow(widget)
        # layout.addRow("Size:", self.size_sb)
        # layout.addRow("Opacity:", self.opacity_sb)


def noLayerWidget():
    return InfoPromptWidget(title='No layer selected',
                            buttonText='Ok',
                            imagePath=helpPath,
                            error=True,
                            image='BAD',
                            gif=False,
                            helpString='Please select your additive animation layer')
