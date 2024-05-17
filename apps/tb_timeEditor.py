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

from Abstract import *
import maya

# maya.utils.loadStringResourcesForModule(__name__)
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
__author__ = 'tom.bailey'

animCompositions = 'animCompositions'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='addSelectionToTimeEditor',
                                     annotation='',
                                     category=self.category,
                                     help='add selected controls as clip in the time editor',
                                     command=['isolator.toggle_isolate()']))
        self.addCommand(self.tb_hkey(name='tbOpenTimeEditorToolBoxUI',
                                     annotation='',
                                     category=self.category,
                                     command=['TimeEditor.timeEditorToolBoxUI()']))
        return self.commandList

    def assignHotkeys(self):
        return


class TimeEditorTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'TimeEditor'
    hotkeyClass = hotkeys()
    funcs = functions()
    timeEditorToolbox = None
    timeEditorExportOption = 'tbTimeEditorDir'

    def __new__(cls):
        if TimeEditorTool.__instance is None:
            TimeEditorTool.__instance = object.__new__(cls)
            TimeEditorTool.__instance.initData()
        TimeEditorTool.__instance.val = cls.toolName
        return TimeEditorTool.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(TimeEditorTool, self).optionUI()

        dirWidget = filePathWidget(self.timeEditorExportOption, None)

        self.layout.addWidget(dirWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        pm.menuItem(label='Time Editor Tools', image='out_timeEditor.png', command='tbOpenTimeEditorToolBoxUI',
                    sourceType='mel',
                    parent=parentMenu)

    def getExportFolder(self):
        if not pm.optionVar.get(self.timeEditorExportOption, None):
            self.selectDirectory()

        return pm.optionVar.get(self.timeEditorExportOption, None)

    def selectDirectory(self, *args):
        dialog = QFileDialog(None, caption="Pick GPU Cache Folder")
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setWindowTitle("Pick GPU Cache Folder")
        dialog.setDirectory(self.dataPath)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_directory = dialog.getExistingDirectory()

        if selected_directory:
            pm.optionVar[self.timeEditorExportOption] = selected_directory

    def timeEditorToolBoxUI(self):
        if self.timeEditorToolbox:
            self.timeEditorToolbox.show()
        self.timeEditorToolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                                            title='tb Time Editor', text=str(),
                                            lockState=False, showLockButton=False, showCloseButton=True, showInfo=True)
        toolboxWidget = QWidget()
        buttonLayout = QVBoxLayout()
        toolboxWidget.setLayout(buttonLayout)
        addClipFromSelectionButton = QPushButton('Add Clip from Selected Controls')
        addClipFromLayerButton = QPushButton('Add Clip from Selected Layer')
        addRelocatorButton = QPushButton('Add Relocator to Selected Controls')
        exportClipButton = QPushButton('Export Selected Clip')
        importClipButton = QPushButton('Import Clip')

        buttonLayout.addWidget(addClipFromSelectionButton)
        buttonLayout.addWidget(addClipFromLayerButton)
        buttonLayout.addWidget(addRelocatorButton)
        buttonLayout.addWidget(importClipButton)
        buttonLayout.addWidget(exportClipButton)


        self.timeEditorToolbox.mainLayout.addWidget(toolboxWidget)

        addRelocatorButton.clicked.connect(lambda: self.createRelocatorForSelectedClip())
        addClipFromSelectionButton.clicked.connect(lambda: self.addClipFromSelectedControls())
        addClipFromLayerButton.clicked.connect(lambda: self.addClipFromSelectedLayer())
        exportClipButton.clicked.connect(lambda: self.exportSelectedClips())
        importClipButton.clicked.connect(lambda: self.importClip())

        self.timeEditorToolbox.show()
        self.timeEditorToolbox.setFixedSize(self.timeEditorToolbox.sizeHint())

    def getSelectedClips(self):
        clipIds = cmds.timeEditor(selectedClips='')
        if not clipIds:
            return list(), list()
        clipNames = [self.getClipName(clip) for clip in clipIds]
        return clipNames, clipIds

    def getClipName(self, clipID):
        return cmds.timeEditorClip(clipID, query=True, name=True)

    def createMainComposition(self):
        allCompositions = cmds.timeEditorComposition(q=True, allCompositions=True)
        if not allCompositions:
            ## Create composition
            cmds.timeEditorComposition(animCompositions)

    def createTrack(self, trackName='trackName'):
        ## Mute composition so you can add and create new anim clips
        cmds.timeEditor(mute=True)
        ## Create track
        track = cmds.timeEditorTracks(self.getCurrentComposition(), e=1, addTrack=1, tn=trackName)
        ## UnMute composition to use clips
        cmds.timeEditor(mute=False)
        return track

    def createClip(self, clipName='clipName', trackName='trackName', timeSpan=[]):
        ## Mute composition so you can add and create new anim clips
        cmds.timeEditor(mute=True)
        ## Create clip with animation name
        clip = cmds.timeEditorClip(clipName, track='%s|%s' % (self.getCurrentComposition(), trackName),
                                   addSelectedObjects=True,
                                   startTime=timeSpan[0],
                                   # duration=timeSpan[1]-timeSpan[0],
                                   )
        clipStartTime = cmds.timeEditorClip(clip, query=True, startTime=True)
        clipEndTime = cmds.timeEditorClip(clip, query=True, endTime=True)

        cmds.timeEditorClip(clipId=clip, edit=True, trimStart=timeSpan[0])
        cmds.timeEditorClip(clipId=clip, edit=True, trimEnd=timeSpan[1])

        ## UnMute composition to use clips
        cmds.timeEditor(mute=False)
        return clip

    def getCurrentComposition(self):
        currentComposition = cmds.timeEditorComposition(query=True, active=True)
        print('currentComposition', currentComposition)
        return currentComposition

    def addClipFromFile(self, fbx=None):
        if not fbx:
            return cmds.warning('No clip')
        if not os.path.isfile(fbx):
            return cmds.warning('Clip not found')
        clipName = os.path.basename(fbx).split('.')[0]
        cmds.timeEditorClip(clipName, showAnimSourceRemapping=True,
                            importOption='generate',
                            importFbx=fbx,
                            ipo="curves;",
                            importAllFbxTakes=True,
                            importTakeDestination=0, startTime=0,
                            track="%s:0" % self.getCurrentComposition())


    def addClipFromSelectedLayer(self):
        selectedLayer = self.funcs.get_selected_layers()
        if not selectedLayer:
            return raiseError('Please select a layer to add it as a time editor clip', title='No selected layer')
        animLayer = selectedLayer[0]
        plugs = self.funcs.getAllPlugsFromLayer(animLayer)
        # curves = [cmds.listConnections(p, source=True, destination=False) for p in plugs]
        # curves = self.funcs.flattenList(curves)

        cmds.select(plugs)
        clipName = "clip_" + animLayer

        newClip = cmds.timeEditorClip(clipName,
                                      showAnimSourceRemapping=False,
                                      type=[
                                          "animCurveTL",
                                          "animCurveTA",
                                          "animCurveTT",
                                          "animCurveTU"
                                      ],
                                      addRelatedKG=True,
                                      recursively=True,
                                      includeRoot=True,
                                      rsa=1,
                                      rootClipId=1,
                                      aso=True,
                                      track="%s:-1" % self.getCurrentComposition())

    def addClipFromSelectedControls(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return raiseError('Please select some controls to create a clip', title='Cannot create clip')
        # curves = [cmds.listConnections(p, source=True, destination=False) for p in plugs]
        # curves = self.funcs.flattenList(curves)

        clipName = "clip_" + cmds.file(query=True, sceneName=True, shortName=True).split('.')[0]
        newClip = cmds.timeEditorClip(clipName,
                                      showAnimSourceRemapping=False,
                                      type=[
                                          "animCurveTL",
                                          "animCurveTA",
                                          "animCurveTT",
                                          "animCurveTU"
                                      ],
                                      addRelatedKG=True,
                                      recursively=True,
                                      includeRoot=True,
                                      rsa=1,
                                      rootClipId=1,
                                      aso=True,
                                      track="%s:-1" % self.getCurrentComposition())

    def getRelocatorForClip(self, clipID):
        print ('getRelocatorForClip', clipID)
        return cmds.timeEditorClipOffset(clipID, query=True, offsetTransform=True)

    def getRelocatorRoots(self, clipID):
        print('getRelocatorRoots', clipID)
        roots = cmds.timeEditorClipOffset(clipID, query=True, rootObj=True)
        return roots

    def getControlsFromClip(self, clipID):
        print('getControlsFromClip', clipID)
        return cmds.timeEditorClip(clipID, query=True, drivenRootObjects=True)

    def matchClips(self):
        selection = cmds.ls(sl=True, type='transform')
        selectedClips, selectedClipIds = self.getSelectedClips()
        if not selectedClips:
            return
        allControls = self.getControlsFromClip(selectedClipIds[0])
        roots = self.getRelocatorRoots(selectedClipIds[0])

        mel.eval('teRootOffsetOptions(2, {0});'.format(selectedClips[0]))
        cmds.checkBox('cteRootOffsetUseClipRoots', edit=True, value=False)
        mel.eval('teUpdateRootOffsetRoots')
        cmds.select(roots, replace=True)
        mel.eval('teUpdateRootObjectsFromSelection')

        if selection:
            cmds.select(selection[0], replace=True)
            mel.eval('teUpdateMatchingObject')

    def createRelocatorForSelectedClip(self):
        selectedClips, selectedClipIds = self.getSelectedClips()

        if not selectedClips:
            return
        print ('selectedClips', selectedClips)
        print ('selectedClipIds', selectedClipIds)
        relocator = self.getRelocatorForClip(selectedClipIds[0])
        if not relocator:
            controls = cmds.ls(sl=True)
            if not controls:
                return raiseError('Please select the worldspace controls to create a relocator',
                                  title='Cannot create relocator')
            relocator = self.createRelocatorForClip(selectedClipIds[0], controls)
        cmds.select(relocator, replace=True)

    def createRelocatorForClip(self, clip, controls):
        print ('createRelocatorForClip', clip)
        print ('controls', controls)
        # controlList = ['%s:cnt_Global' % namespace]
        cmds.timeEditorClipOffset(clipId=clip, offsetTransform=True,
                                              rootObj=controls)
        relocator = self.getRelocatorForClip(clip)
        print ('relocator', relocator)
        assetShapeControl = self.funcs.tempControl(name='delete', suffix='Root', drawType='redirectRoot', scale=1.5)

        pm.delete(assetShapeControl, ch=True)
        pm.parent(assetShapeControl.getShapes(), relocator, r=True, s=True)
        pm.delete(assetShapeControl)
        return relocator

    def browseToFile(self):
        fname = QFileDialog.getOpenFileName(QWidget(), 'Open file',
                                            self.getExportFolder(),
                                            "Clip files (*.ma)")
        return fname[0] or None
    def importClip(self):
        clipFile = self.browseToFile()
        if not clipFile:
            return cmds.warning('User cancelled clip import')
        print (clipFile)

        clipName = os.path.basename(clipFile).split('.')[0]
        cmds.timeEditorClip(clipName,
                            showAnimSourceRemapping=True,
                            importOption='connect',
                            ipo="curves",
                            track="%s:-1" % self.getCurrentComposition(),
                            importMayaFile=clipFile,
                            startTime=cmds.currentTime(query=True))
        return
        """
        timeEditorClip -showAnimSourceRemapping -importOption connect -track "Composition1:0" -importMayaFile "C:/AnimationWork/TimeEditor/clip_SecurityMerk_combat_run_FWD_N.ma" -startTime 20 "clip_SecurityMerk_combat_run_FWD_N";
        // File read in  0.22 seconds.
        // Animation Source "clip_SecurityMerk_combat_run_FWD_N_BakedAnimSource_Export1" has been imported into the scene
        if (!exists("teAnimSourceRemapNamespacesWindow")) source "teAnimSourceNamespace.mel"; teAnimSourceRemapNamespacesWindow("clip_SecurityMerk_combat_run_FWD_N_BakedAnimSource_Export1", "timeEditorClip -populateImportedAnimSources  \"clip_SecurityMerk_combat_run_FWD_N_BakedAnimSource_Export1\"  -showAnimSourceRemapping  -importOption \"connect\" -track \"Composition1:0\" -startTime 20 \"clip_SecurityMerk_combat_run_FWD_N\"", 1 );
        // Result: 0
        timeEditorClip -populateImportedAnimSources  "clip_SecurityMerk_combat_run_FWD_N_BakedAnimSource_Export1"  -showAnimSourceRemapping  -importOption "connect" -track "Composition1:0" -startTime 20 "clip_SecurityMerk_combat_run_FWD_N";
        Clip and its Animation Source created.
        The Time Editor now drives the clip's keyable attributes.
        // Result: 1
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator1.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator2.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator4.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator3.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator5.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)
        // Warning: Cycle on 'clip_SecurityMerk_combat_run_FWD_N_ClipEvaluator6.output' may not evaluate as expected.  (Use 'cycleCheck -e off' to disable this warning.)

        """
        cmds.timeEditorClip(clipName, showAnimSourceRemapping=True,
                            importOption='generate',
                            ipo="curves;",
                            importTakeDestination=0, startTime=0,
                            track="%s:-1" % self.getCurrentComposition())

    def exportSelectedClips(self):
        selectedClips, selectedClipIds = self.getSelectedClips()
        print(selectedClips)
        for clipName, clipId in zip(selectedClips, selectedClipIds):
            outputPath = self.getExportFolder() + '//' + clipName + '.ma'
            print ('outputPath', outputPath)
            self.exportClip(clipId, outputPath)

    def exportClip(self, clipId, path):
        clipNode = cmds.timeEditorClip(clipId, query=True, clipNode=True)

        cmds.select(clipNode + ".clip[0]", replace=True)
        # bake its animation to a new anim source
        clipName = cmds.timeEditorClip(clipId, query=True, name=True)

        animSourceName = clipName + "_BakedAnimSource_Export"
        animSourceName = cmds.timeEditorBakeClips(sampleBy=1,
                                                  keepOriginalClip=True,
                                                  bakeToAnimSource=animSourceName)
        # export that anim source to a file
        cmds.timeEditorAnimSource(animSourceName, edit=True, export=path)

        # delete baked anim source  node and baked curves
        cmds.delete(animSourceName)