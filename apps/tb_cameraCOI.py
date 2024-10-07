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

__author__ = 'tom.bailey'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('cameras'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='updateCameraPivot',
                                     annotation='',
                                     category=self.category,
                                     command=['CameraPivot.doIt()']))
        self.addCommand(self.tb_hkey(name='createCameraPivotScriptJob',
                                     annotation='',
                                     category=self.category,
                                     command=['CameraPivot.createCameraPivotScriptJob()']))

        return self.commandList

    def assignHotkeys(self):
        return


def unit_conversion():
    conversion = {'mm': 0.1, 'cm': 1.0, 'm': 100.0, 'in': 2.54, 'ft': 30.48, 'yd': 91.44}
    return conversion[cmds.currentUnit(query=True, linear=True)]


def midPoint(pointArray):
    midPoint = [0, 0, 0]

    # Get Center Point
    total = len(pointArray)
    for point in pointArray:
        midPoint = [midPoint[0] + point[0], midPoint[1] + point[1], midPoint[2] + point[2]]

    # Calculate Average Position
    midPoint = [midPoint[0] / total, midPoint[1] / total, midPoint[2] / total]

    # Return Result
    return midPoint


def getPivot(obj):
    return cmds.xform(obj, query=True, rotatePivot=True, worldSpace=True)


def getPivotAsBbox(boundingBox, obj):
    '''
    returns the bounding box of the input objects, in case of nulls that have no bounding box for some reason,
    it uses the rotate pivot. If a new point is outside the bounding box, then the returned value will enlarge
    to accommodate it.
    :param boundingBox:
    :param obj:
    :return:
    '''
    pivot = cmds.xform(obj, query=True, rotatePivot=True, absolute=True, worldSpace=True)
    if not boundingBox:
        return [pivot[0], pivot[1], pivot[2], pivot[0], pivot[1], pivot[2]]
    else:
        lowX = min(pivot[0], boundingBox[0])
        lowY = min(pivot[1], boundingBox[1])
        lowZ = min(pivot[2], boundingBox[2])
        highX = max(pivot[0], boundingBox[3])
        highY = max(pivot[1], boundingBox[4])
        highZ = max(pivot[2], boundingBox[5])
        return [lowX, lowY, lowZ, highX, highY, highZ]


def get_bbox(boundingBox, obj):
    bbox = cmds.exactWorldBoundingBox(obj)
    if not boundingBox:
        return bbox
    else:
        lowX = min(bbox[0], boundingBox[0])
        lowY = min(bbox[1], boundingBox[1])
        lowZ = min(bbox[2], boundingBox[2])
        highX = max(bbox[3], boundingBox[3])
        highY = max(bbox[4], boundingBox[4])
        highZ = max(bbox[5], boundingBox[5])
        return [lowX, lowY, lowZ, highX, highY, highZ]


def get_bounding_box_mid(box):
    x = ((box[0] + box[3]) / 2)
    y = ((box[1] + box[4]) / 2)
    z = ((box[2] + box[5]) / 2)
    return [x, y, z]


def get_bounding_box_centre(objects):
    box = cmds.exactWorldBoundingBox(objects)  # Do standard BB computation
    x = ((box[0] + box[3]) / 2)
    y = ((box[1] + box[4]) / 2)
    z = ((box[2] + box[5]) / 2)
    return [x, y, z]


def getMoveManipPosition(*args):
    return cmds.manipMoveContext('Move', query=True, position=True)


def getRotateManipPosition(*args):
    return cmds.manipRotateContext('Rotate', query=True, position=True)


def getScaleManipPosition(*args):
    return cmds.manipScaleContext('Scale', query=True, position=True)


def getSelectManipPosition(*args):
    # hack to set manipulator pivot when in component selection mode
    mel.eval("setToolTo $gMove;")
    pos = cmds.manipMoveContext('Move', query=True, position=True)
    mel.eval("setToolTo $gSelect")
    return pos


class CameraPivot(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'CameraPivot'
    hotkeyClass = hotkeys()
    funcs = Functions()

    cameraPivotOption = 'tbCameraPivot'
    frequency = 0.1667
    contextQuery = {'manipMove': getMoveManipPosition,
                    'manipRotate': getRotateManipPosition,
                    'manipScale': getScaleManipPosition,
                    'selectTool': getSelectManipPosition}

    SomethingSelectedScriptJob = int(-1)
    DragReleaseScriptJob = int(-1)
    ModelPanelSetFocusScriptJob = int(-1)
    playbackModeChangedScriptJob = int(-1)

    if not cmds.optionVar(exists='tumbler_enabled'):
        # TODO - make the option window so this is editable
        cmds.optionVar(intValue=('tumbler_enabled', 0))

    def __new__(cls):
        if CameraPivot.__instance is None:
            CameraPivot.__instance = object.__new__(cls)

        CameraPivot.__instance.val = cls.toolName
        return CameraPivot.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        self.time = cmds.timerX()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(CameraPivot, self).optionUI()
        useTumbleOptionWidget = optionVarBoolWidget('Center camera pivot on selection ', self.cameraPivotOption)
        self.layout.addWidget(useTumbleOptionWidget)
        # connect the checkbox changed event to the function that handles removing/adding the camera scriptJobs
        useTumbleOptionWidget.changedSignal.connect(self.updateScriptJobStatus)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def reset_tumble(self, *args):
        pivot = [0, 0, 0]
        self.update_tumble_pivots(pivot)
        all_cameras = cmds.ls(dag=True, cameras=True)
        for cam in all_cameras:
            try:
                # set the tumble pivot of the camera to the coordinates we have calculated before
                cmds.setAttr(cam + ".tumblePivot", pivot[0], pivot[1], pivot[2])
            except Exception as e:
                pass

    def update_tumble_pivots(self, pivot):
        # Do the actual tumble pivot setting
        all_cameras = cmds.ls(dag=True, cameras=True)
        cmds.tumbleCtx("tumbleContext", edit=True,
                       localTumble=0)  # Set the tumble tool to honor the cameras tumble pivot
        pivot[0] *= unit_conversion()
        pivot[1] *= unit_conversion()
        pivot[2] *= unit_conversion()
        # print 'pivots', pivot[0], pivot[1], pivot[2]
        for cam in all_cameras:
            try:
                # set the tumble pivot of the camera to the coordinates we have calculated before
                cmds.setAttr(cam + ".tumblePivot", pivot[0], pivot[1], pivot[2])
            except:
                Warning("Setting camera tumble pivot on " + cam + "failed!")

    def elapsedTime(self):
        # print('anti spam: Time - ', self.time, ' frequency - ', self.frequency)
        return self.time + self.frequency < cmds.timerX()

    def doIt(self, *args):
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            if get_option_var(self.cameraPivotOption, False) and self.elapsedTime():
                self.time = cmds.timerX()  # set a new time stamp to prevent spamming
                selection = cmds.ls(selection=True)
                if not selection:
                    return None
                pivots = []
                current_context = cmds.currentCtx()
                current_tool = ""
                if cmds.contextInfo(current_context, exists=True):
                    current_tool = cmds.contextInfo(current_context, c=True)
                current_joint = ""
                '''
                This section is for identifiying the joint based on the paint weights tool
                '''
                if current_tool == "artAttrSkin":
                    whichTool = cmds.artAttrSkinPaintCtx(current_context, query=True, whichTool=True)
                    if whichTool == "skinWeights":
                        current_joint = cmds.artAttrSkinPaintCtx(current_context,
                                                                 query=True,
                                                                 influence=True)
                    if len(selection) > 1:
                        mel.eval("setToolTo $gMove;")
                        self.update_tumble_pivots(cmds.manipMoveContext('Move', query=True, position=True))
                        mel.eval("ArtPaintSkinWeightsToolOptions")
                        return
                    elif current_joint:
                        self.update_tumble_pivots(cmds.xform(current_joint,
                                                             query=True,
                                                             worldSpace=True,
                                                             absolute=True,
                                                             translation=True))
                        return
                else:
                    # print 'not using skinning'
                    boundingBox = []
                    selected_verts = [v for v in cmds.ls(sl=True, fl=True) if '.vtx' in v]
                    if selected_verts:
                        for vertex in selected_verts:
                            # Get the world translation of the vertex
                            pivots.append(cmds.xform(vertex, query=True, translation=True, worldSpace=True))
                    if not pivots:
                        selected_cv = [v for v in cmds.ls(sl=True, fl=True) if '.cv' in v]
                        if selected_cv:
                            for cv in selected_cv:
                                # Get the world translation of the CV
                                pivots.append(cmds.pointPosition(cv, world=True))
                    if not pivots:
                        selected_faces = [v for v in cmds.ls(sl=True, fl=True) if '.f' in v]
                        if selected_faces:
                            vertices = cmds.polyListComponentConversion(selected_faces, fromFace=True, toVertex=True)
                            for vertex in vertices:
                                # Get the world translation of the vertex
                                pivots.append(cmds.xform(vertex, query=True, translation=True, worldSpace=True))
                    if not pivots:
                        selected_objects = cmds.ls(selection=True, flatten=True, type='transform', objectsOnly=True)
                        if not len(selected_objects):
                            return
                        pivots = [getPivotAsBbox(boundingBox, selected_objects[-1])]
                        #
                        # if selected_objects:
                        #     self.boundingBox = []
                        #
                        #     transforms_with_shapes = [x for x in selected_objects if
                        #                               cmds.listRelatives(x, fullPath=True, shapes=True)]
                        #
                        #     transforms_without_shapes = [x for x in selected_objects if x not in transforms_with_shapes]
                        #
                        #     if transforms_with_shapes:
                        #         self.boundingBox = get_bbox(None, transforms_with_shapes)
                        #     if transforms_without_shapes:
                        #         for x in transforms_without_shapes:
                        #             self.boundingBox = getPivotAsBbox(self.boundingBox, x)
                        #     if self.boundingBox:
                        #         # gets the mid point of the min/max bounding box for the selection
                        #         self.update_tumble_pivots(get_bounding_box_mid(self.boundingBox))

                    if pivots:
                        if pivots[0]:
                            self.update_tumble_pivots(midPoint(pivots))
        finally:
            cmds.undoInfo(stateWithoutFlush=True)


    def updateScriptJobStatus(self, status):
        if status:
            self.createCameraPivotScriptJob()
        else:
            self.removePivotScriptJobs()

    def removePivotScriptJobs(self):
        if self.SomethingSelectedScriptJob != -1:
            try:
                cmds.scriptJob(kill=self.SomethingSelectedScriptJob)
            except:
                pass
        if self.DragReleaseScriptJob != -1:
            try:
                cmds.scriptJob(kill=self.DragReleaseScriptJob)
            except:
                pass
        if self.ModelPanelSetFocusScriptJob != -1:
            try:
                cmds.scriptJob(kill=self.ModelPanelSetFocusScriptJob)
            except:
                pass
        if self.playbackModeChangedScriptJob != -1:
            try:
                cmds.scriptJob(kill=self.playbackModeChangedScriptJob)
            except:
                pass

    def createCameraPivotScriptJob(self):
        self.removePivotScriptJobs()
        if self.SomethingSelectedScriptJob == -1:
            self.SomethingSelectedScriptJob = cmds.scriptJob(conditionTrue=("SomethingSelected", CameraPivot().doIt))
        if self.DragReleaseScriptJob == -1:
            self.DragReleaseScriptJob = cmds.scriptJob(event=("DragRelease", CameraPivot().doIt))
        # if self.ModelPanelSetFocusScriptJob == -1:
        #     self.ModelPanelSetFocusScriptJob = cmds.scriptJob(event=("ModelPanelSetFocus", CameraPivot().doIt))
        if self.playbackModeChangedScriptJob == -1:
            self.playbackModeChangedScriptJob = cmds.scriptJob(event=("playbackModeChanged", CameraPivot().doIt))
