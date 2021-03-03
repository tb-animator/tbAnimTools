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
    visit tb-animator.blogspot.com for "stuff"

*******************************************************************************
'''
import pymel.core as pm
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

import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
from Abstract import *
from contextlib import contextmanager
import maya.OpenMaya as om


@contextmanager
def keepSelection():
    # setup
    sel = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(sel)

    yield

    # cleanup
    om.MGlobal.setActiveSelectionList(sel)

class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_cameras')
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tracking_camera_track',
                                     annotation='creates/rebuilds a tracking camera to track your current selection',
                                     category=self.category,
                                     command=['trackingCamera.swapToTrackingCamera()']))
        self.addCommand(self.tb_hkey(name='tracking_camera_update',
                                     annotation='updates the object tracked by the tracking camera, switches view',
                                     category=self.category,
                                     command=['trackingCamera.swapToTrackingCameraUpdateTarget()']))
        self.addCommand(self.tb_hkey(name='tracking_camera_persp',
                                     annotation='swaps the view to the perspective camera, matching your current view',
                                     category=self.category, command=['trackingCamera.swapToCamera()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class trackingCamera(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'trackingCamera'
    hotkeyClass = hotkeys()
    funcs = functions()

    current_t = None
    current_r = None
    trackerGrp = None
    trackerCam = None
    constraint = None
    camera_target = None

    def __new__(cls):
        if trackingCamera.__instance is None:
            trackingCamera.__instance = object.__new__(cls)

        trackingCamera.__instance.val = cls.toolName
        return trackingCamera.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(trackingCamera, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def swapToTrackingCamera(self):
        self.camera_target = cmds.ls(sl=True)
        if self.trackerGrp is None:
            self.createTrackingCamera()
        if not cmds.objExists(self.trackerGrp):
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
        if perspCameras:
            cam, camShape = self.getCurrentCamera()
            self.getCameraTransform(self.trackerCam)
            self.setCameraTransform(perspCameras[0])
            cmds.lookThru(perspCameras[0])

    def createTrackingCamera(self):
        with keepSelection():
            cam, camShape = self.getCurrentCamera()
            print 'current camera', cam
            self.getCameraTransform(cam)

            self.trackerCam = cmds.duplicate(cam)
            self.trackerCam = cmds.rename(self.trackerCam, 'tracker_cam')
            self.trackerGrp = cmds.group(empty=True, world=True, name="tracker_grp")
            pm.parent(self.trackerCam, self.trackerGrp)

            self.constraint = pm.pointConstraint(self.camera_target, self.trackerGrp)
            self.setCameraTransform(self.trackerCam)

    def updateTrackTarget(self):
        with keepSelection():
            self.camera_target = cmds.ls(sl=True)
            if not self.camera_target:
                return cmds.warning('no new target to update')
            if self.trackerCam in self.camera_target:
                return cmds.warning('unable to track tracking camera with tracking camera')
            if self.trackerGrp in self.camera_target:
                return cmds.warning('unable to track tracking camera with tracking camera')
            if not self.trackerGrp:
                self.createTrackingCamera()
            cam, camShape = self.getCurrentCamera()
            self.getCameraTransform(cam)
            pm.delete(self.constraint)
            self.constraint = pm.pointConstraint(self.camera_target, self.trackerGrp)
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
        cmds.xform(camera, worldSpace=True, absolute=True, translation=self.current_t)
        cmds.xform(camera, absolute=True, rotation=self.current_r)
