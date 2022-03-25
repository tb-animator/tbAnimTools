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

import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
from Abstract import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('cameras'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='trackingCameraTrack',
                                     annotation='creates/rebuilds a tracking camera to track your current selection',
                                     category=self.category,
                                     command=['TrackingCamera.swapToTrackingCamera()']))
        self.addCommand(self.tb_hkey(name='trackingCameraUpdate',
                                     annotation='updates the object tracked by the tracking camera, switches view',
                                     category=self.category,
                                     command=['TrackingCamera.swapToTrackingCameraUpdateTarget()']))
        self.addCommand(self.tb_hkey(name='trackingCameraPersp',
                                     annotation='swaps the view to the perspective camera, matching your current view',
                                     category=self.category, command=['TrackingCamera.swapToCamera()']))
        return self.commandList

    def assignHotkeys(self):
        return


class TrackingCamera(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    #__metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'TrackingCamera'
    hotkeyClass = hotkeys()
    funcs = functions()

    current_t = None
    current_r = None
    trackerGrp = None
    trackerCam = None
    constraint = None
    camera_target = None

    def __new__(cls):
        if TrackingCamera.__instance is None:
            TrackingCamera.__instance = object.__new__(cls)

        TrackingCamera.__instance.val = cls.toolName
        return TrackingCamera.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(TrackingCamera, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def swapToTrackingCamera(self):
        self.camera_target = cmds.ls(sl=True)
        self.createTrackingCamera()
        cam, camShape = self.getCurrentCamera()
        self.getCameraTransform(cam)
        self.setCameraTransform(self.trackerCam)
        cmds.lookThru(self.trackerCam)

    def swapToTrackingCameraUpdateTarget(self):
        self.updateTrackTarget()
        self.swapToTrackingCamera()

    def swapToCamera(self, camera='persp'):
        perspCameras = [cam for cam in cmds.ls(cameras=True) if 'persp' in cam]
        self.createTrackingCamera()

        if perspCameras:
            cam, camShape = self.getCurrentCamera()
            self.getCameraTransform(self.trackerCam)
            self.setCameraTransform(perspCameras[0])
            cmds.lookThru(perspCameras[0])

    def createTrackingCamera(self):
        """
        create the tracking camera if needed
        :return:
        """
        with self.funcs.keepSelection():
            cam, camShape = self.getCurrentCamera()
            self.getCameraTransform(cam)
            if not cmds.objExists('tracker_cam'):
                self.trackerCam = cmds.duplicate(cam)
                self.trackerCam = cmds.rename(self.trackerCam, 'tracker_cam')
            else:
                self.trackerCam = 'tracker_cam'
            if not cmds.objExists("tracker_grp"):
                self.trackerGrp = cmds.group(empty=True, world=True, name="tracker_grp")
            else:
                self.trackerGrp = "tracker_grp"
            trackingCameraParent = cmds.listRelatives(self.trackerCam, parent=True)
            if not trackingCameraParent:
                cmds.parent(self.trackerCam, self.trackerGrp)
            elif trackingCameraParent[0] != self.trackerGrp:
                cmds.parent(self.trackerCam, self.trackerGrp)

            constraints = cmds.listRelatives(self.trackerGrp, children=True, type='constraint')
            if constraints: cmds.delete(constraints)
            constraints = cmds.listRelatives(self.trackerCam, children=True, type='constraint')
            if constraints: cmds.delete(constraints)


            if self.camera_target:
                self.constraint = cmds.pointConstraint(self.camera_target, self.trackerGrp)
            self.setCameraTransform(self.trackerCam)

    def updateTrackTarget(self):
        with self.funcs.keepSelection():
            self.camera_target = cmds.ls(sl=True)
            if not self.camera_target:
                return cmds.warning('no new target to update')
            if self.trackerCam in self.camera_target:
                return cmds.warning('unable to track tracking camera with tracking camera')
            if self.trackerGrp in self.camera_target:
                return cmds.warning('unable to track tracking camera with tracking camera')

            self.createTrackingCamera()
            cam, camShape = self.getCurrentCamera()
            self.getCameraTransform(cam)
            if self.constraint:
                for c in self.constraint:
                    if cmds.objExists(c):
                        cmds.delete(c)
            self.constraint = cmds.pointConstraint(self.camera_target, self.trackerGrp)
            self.setCameraTransform(cam)

    def getCurrentCamera(self):
        view = OpenMayaUI.M3dView.active3dView()
        cam = OpenMaya.MDagPath()
        view.getCamera(cam)
        cameraShape = cam.fullPathName()
        camera = cmds.listRelatives(cameraShape, parent=True)[0]
        return camera, cameraShape

    def getCameraTransform(self, camera):
        self.current_t = cmds.xform(camera, query=True, worldSpace=True, absolute=True, translation=True)
        self.current_r = cmds.xform(camera, query=True, absolute=True, rotation=True)

    def setCameraTransform(self, camera):
        if not cmds.objectType(camera) == 'transform':
            camera = cmds.listRelatives(camera, parent=True, type='transform')[0]
        cmds.xform(camera, worldSpace=True, absolute=True, translation=self.current_t)
        cmds.xform(camera, absolute=True, rotation=self.current_r)
