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
import os.path
from tb_timeline import timeline
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

from tb_UI import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory('tbtools_cameras')
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='incremental_playblast_quicktime',
                                     annotation='incrememnt and save playblasts in mov',
                                     category=self.category,
                                     command=[
                                         'playblastTool.make_playblast(ext="mov")']))
        self.addCommand(self.tb_hkey(name='incremental_playblast_avi',
                                     annotation='incrememnt and save playblasts in avi',
                                     category=self.category,
                                     command=[
                                         'playblastTool.make_playblast(ext="avi")']))

        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class playblastTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'playblastTool'
    hotkeyClass = hotkeys()
    funcs = functions()

    playblastDir_opv = 'tb_playblast_folder'
    playblastDir_default = 'c://playblasts//'
    playblastExt_opv = 'tb_playblast_ext'
    playblastExt_values = ['mp4', 'avi', 'mov']
    playblastExt_default = 'mov'

    def __new__(cls):
        if playblastTool.__instance is None:
            playblastTool.__instance = object.__new__(cls)

        playblastTool.__instance.val = cls.toolName
        return playblastTool.__instance

    def __init__(self, **kwargs):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(playblastTool, self).optionUI()

        dirWidget = filePathWidget('tb_playblast_folder', self.playblastDir_default)

        fileTypeWidget = radioGroupWidget(optionVarList=self.playblastExt_values,
                                          optionVar=self.playblastExt_opv,
                                          defaultValue=self.playblastExt_values[0], label='Output file type')

        self.layout.addWidget(dirWidget)
        self.layout.addWidget(fileTypeWidget)

        '''
        videoTypeLayout = QHBoxLayout()
        videoTypeLabel = QLabel('output file type')
        videoTypeGrp = QButtonGroup()  # Letter group
        movBtn = QRadioButton("mov")
        movBtn.toggled.connect(lambda: self.extBtnState(movBtn))
        videoTypeGrp.addButton(movBtn)
        aviBtn = QRadioButton("avi")
        aviBtn.toggled.connect(lambda: self.extBtnState(aviBtn))
        videoTypeGrp.addButton(aviBtn)
        videoTypeLayout.addWidget(videoTypeLabel)
        videoTypeLayout.addWidget(movBtn)
        videoTypeLayout.addWidget(aviBtn)
        layout.addWidget(dirWidget)
        layout.addLayout(videoTypeLayout)

        self.playblastExt_opv = pm.optionVar.get(self.playblastExt_opv, self.playblastExt_default)
        aviBtn.setChecked(self.playblastExt_opv == 'avi')
        movBtn.setChecked(self.playblastExt_opv == 'mov')
        '''
        return self.layout

    def showUI(self):
        return cmds.warning(self, 'showUI', ' function not implemented')

    def make_playblast(self, ext="mov"):
        # TODO - mp4 support
        formats = {"mov": "qt", "avi": "avi"}

        directory = pm.optionVar.get(self.playblastDir_opv, self.playblastDir_default)
        file = cmds.file(query=True, sceneName=True, shortName=True)
        filename = file.split('.')[0]

        folderName = '%sp_%s/' % (directory, filename)
        if not os.path.exists(folderName):
            os.makedirs(folderName)
        count = len(cmds.getFileList(fld=folderName))
        string_count = len(str(count))
        string_base = "0000"
        string_base_count = len(string_base)
        index = string_base_count - string_count
        string_result = string_base[:index]
        blast_name = '%s%s_%s%s.%s' % (folderName, filename, string_result, count, ext)

        if self.funcs.isTimelineHighlighted():
            range = self.funcs.getTimelineHighlightedRange()
        else:
            range = self.funcs.getTimelineRange()
        print "pb range", range
        print "file name to save", blast_name
        cmds.playblast(startTime=range[0], endTime=range[1], format=formats[ext],
                       clearCache=False, percent=75, filename=blast_name)
