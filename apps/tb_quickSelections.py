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
import time
import pymel.core as pm

QSS_Suffix = '_qss'

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

import maya.cmds as cmds
import maya.mel as mel
import os, stat
import pickle
import json
import maya.OpenMayaUI as omUI
from Abstract import *
from tb_UI import *
import getStyleSheet as getqss

_repeat_function = None
_args = None
_kwargs = None

import inspect

def get_class_that_defined_method(meth):
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls
    return None

def repeatable(function):
    '''A decorator that will make commands repeatable in maya'''

    def decoratorCode(*args, **kwargs):
        functionReturn = None
        argString = ''
        if args:
            for each in args:
                argString += str(each) + ', '

        if kwargs:
            for key, item in kwargs.iteritems():
                argString += str(key) + '=' + str(item) + ', '

        commandToRepeat = 'python("global tbtoolCLS;tbtoolCLS.tools[\'QuickSelectionSets\'].' + function.__name__ + '()")'

        functionReturn = function(*args, **kwargs)
        try:
            cmds.repeatLast(ac=commandToRepeat, acl=function.__name__)
        except:
            pass

        return functionReturn

    return decoratorCode


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('selection'))
        self.commandList = list()

        # quick selection set - select
        self.addCommand(self.tb_hkey(name='tbOpenQuickSelectionMMenu',
                                     annotation='useful comment',
                                     category=self.category, command=['QuickSelectionSets.openMM()']))
        self.addCommand(self.tb_hkey(name='select_quick_select_set_objs',
                                     annotation='',
                                     category=self.category,
                                     command=['QuickSelectionSets.qs_select()']))
        self.addCommand(self.tb_hkey(name='quick_select_load_window',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['QuickSelectionSets.openQssLoadWindow()']))
        self.addCommand(self.tb_hkey(name='save_quick_selects_to_file',
                                     annotation='load quick selects from saved files',
                                     category=self.category,
                                     command=['QuickSelectionSets.save_qs_to_file()']))
        self.addCommand(self.tb_hkey(name='create_quick_select_set',
                                     annotation='create a new quick selection set from current selection',
                                     category=self.category,
                                     command=['QuickSelectionSets.saveQssDialog()']))
        return self.commandList

    def assignHotkeys(self):
        return


class QuickSelectionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'QuickSelectionSets'
    hotkeyClass = hotkeys()
    funcs = functions()

    quickSelectFolderOption = 'tb_qs_folder'
    quickSelectFolder = 'qssFiles'
    quickSelectFolderDefault = None
    quickSelectSavePath = None

    quickSelectOnQssSuffix = 'quickSelectOnQssSuffix'
    quickSelectionIgnore = 'quickSelectionIgnore'

    namespace_mode = 0

    def __new__(cls):
        if QuickSelectionTools.__instance is None:
            QuickSelectionTools.__instance = object.__new__(cls)
            QuickSelectionTools.__instance.initData()

        QuickSelectionTools.__instance.val = cls.toolName
        return QuickSelectionTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

        self.all_sets = self.get_sets()

        self.quickSelectSavePath = pm.optionVar.get(self.quickSelectFolderOption, self.quickSelectFolderDefault)

        self.qss_files = list()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(QuickSelectionTools, self).optionUI()
        self.initData()
        dirWidget = filePathWidget(self.quickSelectFolderOption, self.quickSelectFolderDefault)
        quickSelectOnQssWidget = optionVarBoolWidget('Quick select selection only on sets named _qss',
                                                     self.quickSelectOnQssSuffix)
        quickSelectIgnoreListWidget = optionVarStringListWidget('Ignore lists with suffix (separate multiple with ;)',
                                                                self.quickSelectionIgnore)

        self.layout.addWidget(dirWidget)
        self.layout.addWidget(quickSelectOnQssWidget)
        self.layout.addWidget(quickSelectIgnoreListWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def initData(self):
        super(QuickSelectionTools, self).initData()
        self.quickSelectFolderDefault = os.path.join(self.dataPath, self.quickSelectFolder)
        if not os.path.isdir(self.quickSelectFolderDefault):
            os.mkdir(self.quickSelectFolderDefault)

    def create_main_set(self, sel=None):
        if not sel:
            sel = cmds.ls(sl=True)
        if not sel:
            return
        elif ':' not in sel[0]:
            namespace = ':'
        else:
            namespace = sel[0].rsplit(':', 1)[0] + ':'
        if namespace.startswith(':'):
            namespace = namespace[1:]
        mainSetName = namespace + "QuickSelects"
        if not cmds.objExists(mainSetName):
            cmds.select(clear=True)
            main_set = cmds.sets(name=mainSetName)
            cmds.select(sel, replace=True)

        return mainSetName

    def get_sets(self, forceAll=False):
        all_sets = cmds.ls(sets=True)
        qs_sets = list()

        all_sets = [q for q in all_sets if cmds.sets(q, query=True, text=True) == 'gCharacterSet']
        if pm.optionVar.get(self.quickSelectOnQssSuffix, True) and not forceAll:
            all_sets = [q for q in all_sets if q.endswith(QSS_Suffix)]
        ignoreValues = pm.optionVar.get(self.quickSelectionIgnore, '')

        ignoredSets = list()

        for s in all_sets:
            for x in ignoreValues.split(';'):
                if not x:
                    continue
                if x in s:
                    ignoredSets.append(s)

        for s in ignoredSets:
            if s not in all_sets:
                continue
            all_sets.remove(s)

        for qs_name in all_sets:
            # if cmds.sets(qs_name, query=True, text=True) == 'gCharacterSet':
            self.addColourAttribute(qs_name)
            qs_sets.append(qs_name)

        return qs_sets

    def getMatchingSets(self, sel, all_sets):
        matchedSets = list()
        unmatchedSets = list()
        if not all_sets:
            return matchedSets, unmatchedSets

        for s in all_sets:
            if self.check_set_membership(sel, s):
                matchedSets.append(s)
            else:
                unmatchedSets.append(s)
        return matchedSets, unmatchedSets

    def selectQuickSelectionSet(self, name, add=True):
        cmds.select(self.get_set_contents(name), add=add, replace=not add)

    def addColourAttribute(self, name):
        if not cmds.attributeQuery('Colour', node=name, exists=True):
            cmds.addAttr(name, longName='Colour', usedAsColor=True, attributeType='float3')
            cmds.addAttr(name, longName='ColourX', attributeType="float", p='Colour')
            cmds.addAttr(name, longName='ColourY', attributeType="float", p='Colour')
            cmds.addAttr(name, longName='ColourZ', attributeType="float", p='Colour')
            cmds.setAttr(name + '.Colour', 1.0, 0.769, 0.0, type='float3')
            cmds.setAttr(name + '.Colour', edit=True, keyable=False, channelBox=True)
            cmds.setAttr(name + '.ColourX', edit=True, keyable=False, channelBox=True)
            cmds.setAttr(name + '.ColourY', edit=True, keyable=False, channelBox=True)
            cmds.setAttr(name + '.ColourZ', edit=True, keyable=False, channelBox=True)

    def getSetColour(self, name):
        self.addColourAttribute(name)
        return cmds.getAttr(name + '.Colour')[0]

    @repeatable
    def qs_select(self, *args, **kwargs):
        sel = cmds.ls(sl=True)
        if not sel:
            return

        all_sets = self.get_sets()

        if all_sets:
            for a_set in all_sets:
                qs_result = self.check_set_membership(sel, a_set)
                if qs_result:
                    cmds.select(self.get_set_contents(a_set), add=True)
            for s in sel:
                # skip non object sets
                if cmds.nodeType(s) == 'objectSet':
                    cmds.select(self.get_set_contents(s), add=True)
        else:
            msg = 'no quick selects found for selection'
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=5.0,
                                   fadeOutTime=4.0, fade=False)

    @staticmethod
    def existing_obj_in_list(sel):
        existing = []
        for ob in sel:
            if cmds.objExists(ob):
                existing.append(ob)
        return existing

    @staticmethod
    def get_set_contents(qss_set):
        return cmds.listConnections(qss_set, source=True, d=False, plugs=False, c=0)

    def check_set_membership(self, selection, sel_set):
        sel_set_members = cmds.sets(sel_set, query=True)

        if sel_set_members:
            if [i for i in selection if i in sel_set_members]:
                return sel_set
            else:
                return None
        else:
            msg = 'no quick selects found in scene'
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=3.0,
                                   fadeOutTime=4.0)

    def create_qs_set(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return

        result = cmds.promptDialog(
            title='Quick selection name',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            qs_name = cmds.promptDialog(query=True, text=True)
            save = True
            if qs_name in self.all_sets:
                if not cmds.confirmDialog(
                        title='Overwrite existing set?',
                        message='Are you sure?',
                        button=['Yes', 'No'],
                        defaultButton='Yes',
                        cancelButton='No',
                        dismissString='No'):
                    save = False
            if save:
                self.save_qs(qs_name, sel)

        else:
            msg = "can't save a quick selection set with nothing selected!"
            self.funcs.infoMessage(position="botRight", prefix="Warning", message=msg, fadeStayTime=3.0,
                                   fadeOutTime=4.0)
    @repeatable
    def saveQssDialog(self, quick=False):
        sel = cmds.ls(selection=True)
        if not sel:
            return pm.warning('Unable to save empty selection')

        dialog = QssSaveWidget(title='Save Selection Set', label='Enter Name', buttonText="Save",
                               default=sel[-1].split(':')[-1],
                               qss=quick,
                               checkBox='Mirror')
        dialog.acceptedCBSignal.connect(self.getSaveQssSignal)

    def getSaveQssSignal(self, name, quick, mirror):
        """

        :param name:
        :param quick:
        :param mirror:
        :return:
        """
        sel = cmds.ls(sl=True)
        if not sel:
            return cmds.warning('Nothing selected')
        if name:
            self.save_qs(name, sel, quick=quick, colour=self.funcs.getControlColour(sel[-1]))

        MirrorTools = self.allTools.tools['MirrorTools']
        mirrorControls = MirrorTools.splitControls(sel)
        opposites = [x[1] for x in mirrorControls]
        if opposites:
            self.save_qs(opposites[-1], opposites, colour=self.funcs.getControlColour(opposites[-1]))

    def save_qs(self, qs_name, selection, quick=True, colour=[0.5, 0.5, 0.5]):
        # print ('save colour', colour)
        qs_name = qs_name.split(':')[-1]
        if not selection:
            return cmds.warning('Nothing selected')
        pre_sel = cmds.ls(selection=True)
        # make sure we have the main set
        self.create_main_set()
        # only select existing objects
        existing_obj = self.existing_obj_in_list(selection)
        if existing_obj:
            cmds.select(existing_obj, replace=True)
            newSetNamespace = pm.PyNode(existing_obj[0]).namespace()
            if newSetNamespace:
                qs_name = newSetNamespace + ':' + qs_name
            if qs_name.startswith(':'):
                qs_name = qs_name[1:]


            if quick:
                if not qs_name.endswith(QSS_Suffix):
                    qs_name += QSS_Suffix

            if cmds.objExists(qs_name):
                if cmds.nodeType(qs_name) == 'objectSet':
                    # TODO - maybe add a query to replace here?
                    cmds.delete(qs_name)

            qs = cmds.sets(name=qs_name, text="gCharacterSet")
            # print ('qs', qs)
            self.getSetColour(qs)

            self.setSetColourFromUI(qs, colour[0] / 255.0, colour[1] / 255.0, colour[2] / 255.0)
            cmds.select(qs, replace=True)
            cmds.sets(qs, addElement=self.create_main_set())
            cmds.select(pre_sel, replace=True)
        self.create_main_set()

    def save_qs_from_file(self, qs_name, selection):
        namespace_override = None

        def process_namespace():
            sel = pm.ls(selection=True)
            if sel:
                namespace_override = sel[0].namespace()
            else:
                return pm.warning('Nothing selected, cannot match namespace')
            for sel in selection:
                processed_list.append(namespace_override + sel.split(":")[-1])
            return processed_list

        def replace_namespace(namespace=""):
            for sel in selection:
                processed_list.append(namespace + sel.split(":")[-1])

        processed_list = []
        if self.namespace_mode == 1:
            processed_list = process_namespace()
            msg = 'quick selects created for %s' % qs_name
        else:
            processed_list = selection
            msg = 'quick selects created for %s' % qs_name
        if processed_list:
            self.save_qs(qs_name, processed_list)
            self.funcs.infoMessage(position="botRight", prefix="info", message=msg, fadeStayTime=10, fadeOutTime=10.0)
        else:
            # process failed, make error
            self.funcs.infoMessage(position="botRight", prefix="Error", message=msg, fadeStayTime=10, fadeOutTime=10.0)

    def save_qs_to_file(self):
        allSets = self.get_sets()
        if not allSets:
            return cmds.warning('no sets found to save')
        # [item for sublist in curves for item in sublist if item]

        refname, namespace = self.funcs.getCurrentRig(sel=self.get_set_contents(allSets))
        dialog = TextInputWidget(title='Save Quick Selection Sets To File', label='Enter FileName', buttonText="Save",
                                 default=refname)
        dialog.acceptedSignal.connect(self.getSaveFileSignal)

    def getSaveFileSignal(self, fileName):
        """
        For some reason all the logic for saving is here, go figure
        :param fileName:
        :return:
        """
        if fileName:
            save_file = os.path.join(self.quickSelectSavePath, fileName + ".qss")
            jsonFile = os.path.join(self.quickSelectSavePath, fileName + ".json")
            if not os.path.isdir(self.quickSelectSavePath):
                os.mkdir(self.quickSelectSavePath)
            else:
                os.chmod(self.quickSelectSavePath, stat.S_IWRITE)
            out_data = []

            jsonData = '''{}'''
            setData = json.loads(jsonData)
            setData['setNames'] = dict()
            # TODO - save non qss sets as well
            # TODO - add qss option and colour option on save?
            for qset in self.get_sets():
                data = qss_data_obj(qs_name=str(qset),
                                    qs_objects=self.get_set_contents(qset),
                                    colour=self.getSetColour(qset))

                setData['setNames'][str(qset)] = data.toJson()
            # pickle.dump(out_data, open(save_file, "wb"))
            self.saveJsonFile(jsonFile, setData)

    def load_qss_file(self, qss_name):
        """
        :param qss_name:
        :return:
        """
        file_name = os.path.join(self.quickSelectSavePath, qss_name)
        rawJsonData = json.load(open(file_name))
        # print ('qss_name')
        if 'setNames' not in rawJsonData.keys():
            cmds.warning('Loading legacy set')
            for qs_name, qs_objects in rawJsonData.items():
                self.save_qs_from_file(qs_name, qs_objects)
            return
        # print (rawJsonData)
        for qs_name, qs_objects in rawJsonData['setNames'].items():
            # print ('qs_name', qs_name)
            # print ('qs_objects', qs_objects)
            self.save_qs_from_file(qs_name, qs_objects.get('qs_objects', list()))

    def restore_qs_from_dir(self):
        qss_files = list()
        for qss_files in os.listdir(self.quickSelectSavePath):
            if qss_files.endswith(".json"):
                self.qss_files.append(qss_files)

    def openQssLoadWindow(self):
        win = LoadQuickSelectWindow()
        win.show()

    def restore_legacy_files_from_dir(self):
        all_qss_files = list()
        for qss_files in os.listdir(self.quickSelectSavePath):
            if qss_files.endswith(".qss"):
                all_qss_files.append(qss_files)
        return all_qss_files

    def convertPickleToJson(self):
        all_qss_files = self.restore_legacy_files_from_dir()
        for qss in all_qss_files:
            loaded_data = pickle.load(open(os.path.join(self.quickSelectFolderDefault, qss), "rb"))
            jsonData = '''{}'''
            setData = json.loads(jsonData)
            for qs in loaded_data:
                setData[str(qs.qs_name)] = qs.qs_objects
            self.saveJsonFile(os.path.join(self.quickSelectFolderDefault, (qss.split('.')[0] + '.json')), setData)

    def loadDataForCharacters(self, characters):
        namespaceToCharDict = dict()
        if not characters:
            return
        for key, value in characters.items():
            '''
            if not key:
                continue  # skip non referenced chars
            '''
            refname, namespace = self.funcs.getCurrentRig([value[0]])
            if namespace.startswith(':'):
                namespace = namespace.split(':', 1)[-1]
            namespaceToCharDict[namespace] = refname
            '''
            if refname not in self.loadedSpaceData.keys():
                self.saveRigFileIfNew(refname, SpaceData().toJson())
            '''
            # spaceData = self.loadRigData(SpaceData(), refname)
            # self.loadedSpaceData[refname] = None
        self.namespaceToCharDict = namespaceToCharDict

    def openMM(self):
        self.build_MM()
        self.markingMenuWidget.show()
        self.markingMenuWidget.keyReleasedSignal.connect(self.menuClosed)
        self.markingMenuWidget.closeSignal.connect(self.setSelectionTool)
        self.markingMenuWidget.setVisible(False)
        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.delayedShow)
        self.timer.start(1)

    @Slot()
    def delayedShow(self, *args):
        if time.time() - self.start_time >= 0.06:  # this would be 420 seconds
            if self.timer.isActive():
                self.markingMenuWidget.setVisible(True)
            self.timer.stop()

    @Slot()
    def menuClosed(self):
        self.timer.stop()
        self.markingMenuWidget.close()
        self.markingMenuWidget.setVisible(False)
        if not self.markingMenuWidget.hasExecutedCommand:
            self.qs_select()

    def build_MM(self, parentMenu=None):
        menuDict = {'NE': list(),
                    'NW': list(),
                    'SE': list(),
                    'SW': list()
                    }

        self.markingMenuWidget = ViewportDialog(menuDict=menuDict, parentMenu=parentMenu)

        sel = cmds.ls(sl=True)
        allSets = self.get_sets(forceAll=True)
        matchedSets, unmatchedSets = self.getMatchingSets(sel, allSets)
        matchedQss = list()
        if matchedSets:
            matchedQss = [x for x in matchedSets if x.endswith(QSS_Suffix)]
        # main select quik select button
        tmpLabel = QLabel()
        fontWidth = 0
        for mset in allSets:
            tmpLabel.setText(mset)
            tFontWidth = tmpLabel.fontMetrics().boundingRect(tmpLabel.text()).width() + 16
            if tFontWidth > fontWidth:
                fontWidth = tFontWidth
        if sel:
            menuDict['NE'].append(
                ToolboxButton(label='Quick Select', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                              icon=IconPath + '\local_base.png',
                              command=lambda: self.qs_select(),
                              closeOnPress=True))
            menuDict['NW'].append(ToolboxButton(label='Add Selection Set', parent=self.markingMenuWidget,
                                                cls=self.markingMenuWidget,
                                                icon=IconPath + '\local_base.png',
                                                command=lambda: self.saveQssDialog(quick=False),
                                                fixedWidth=120,
                                                closeOnPress=True))
            menuDict['NW'].append(ToolboxButton(label='Add Quick Selection Set', parent=self.markingMenuWidget,
                                                cls=self.markingMenuWidget,
                                                icon=IconPath + '\local_base.png',
                                                command=lambda: self.saveQssDialog(quick=True),
                                                fixedWidth=120,
                                                closeOnPress=True))

        for mset in matchedSets:
            setColour = self.getSetColoursForUI(mset)

            button = ToolboxButton(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                   command=pm.Callback(self.selectQuickSelectionSet, mset, add=True),
                                   closeOnPress=False,
                                   icon=':\create.png',
                                   isSmall=True)
            altButton = ToolboxColourButton(label=mset, parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                            command=pm.Callback(self.selectQuickSelectionSet, mset, add=False),
                                            closeOnPress=False,
                                            isSmall=False,
                                            colour=setColour,
                                            fixedWidth=fontWidth,
                                            colouredBackground=True,
                                            )
            altButton.setPopupMenu(AdjustmentButtonPopup)
            altButton.colourChangedSignal.connect(self.setSetColourFromUI)
            menuDict['SE'].append(ToolboxDoubleButton(mset,
                                                      self.markingMenuWidget,
                                                      cls=self.markingMenuWidget,
                                                      buttons=[button, altButton],
                                                      colour=setColour,
                                                      hideLabel=True, ))

        menuDict['SE'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))

        # print ('max font width', fontWidth)
        for mset in unmatchedSets:
            setColour = self.getSetColoursForUI(mset)

            button = ToolboxButton(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                   command=pm.Callback(self.selectQuickSelectionSet, mset, add=True),
                                   closeOnPress=False,
                                   icon=':\create.png',
                                   isSmall=True)
            altButton = ToolboxColourButton(label=mset, parent=self.markingMenuWidget, cls=self.markingMenuWidget,
                                            command=pm.Callback(self.selectQuickSelectionSet, mset, add=False),
                                            closeOnPress=False,
                                            isSmall=False,
                                            colour=setColour,
                                            fixedWidth=fontWidth,
                                            colouredBackground=True,
                                            )
            altButton.setPopupMenu(AdjustmentButtonPopup)
            altButton.colourChangedSignal.connect(self.setSetColourFromUI)
            menuDict['SE'].append(ToolboxDoubleButton(mset,
                                                      self.markingMenuWidget,
                                                      cls=self.markingMenuWidget,
                                                      buttons=[button, altButton],
                                                      colour=setColour,
                                                      buttonsOnRight=False,
                                                      hideLabel=True, ))

        characters = self.funcs.splitSelectionToCharacters(sel)
        self.loadDataForCharacters(characters)
        # make this better...?

        # get sets associated with selection

        menuDict['SW'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Load Quick Selects    ',
                                            icon=IconPath + '\popupWindow.png',
                                            parent=self.markingMenuWidget,
                                            cls=self.markingMenuWidget,
                                            command=lambda: self.openQssLoadWindow(),
                                            closeOnPress=True))

        menuDict['SW'].append(ToolboDivider(label='', parent=self.markingMenuWidget, cls=self.markingMenuWidget))
        menuDict['SW'].append(ToolboxButton(label='Save Current Sets ...     ',
                                            icon=IconPath + '\popupWindow.png',
                                            parent=self.markingMenuWidget,
                                            cls=self.markingMenuWidget,
                                            command=lambda: self.save_qs_to_file(),
                                            closeOnPress=True))

    def getSetColoursForUI(self, mset):
        colour = self.getSetColour(mset)
        colour = [colour[0] * 255, colour[1] * 255, colour[2] * 255]
        return colour

    def setSetColourFromUI(self, mset, colourR, colourG, colourB):
        cmds.setAttr(mset + '.Colour', colourR, colourG, colourB, type='double3')

    def setSelectionTool(self):
        cmds.setToolTo('selectSuperContext')

    def quickSelectViewportDialog(self):
        sel = cmds.ls(ls=True)

        for s in sel:
            setMembership = cmds.listSets(object=s)
            setMembership = [x for x in setMembership if x.endswith(QSS_Suffix)]
        return
        for s in sel:
            if cmds.objectType(s) == 'objectSet':
                cmds.select(s, add=True)
                cmds.select(s, deselect=True, noExpand=True)


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
        pass

    def create_layout(self):
        tbAdjustmentBlendLabel = QLabel('tbAdjustmentBlend')
        extractOptionLabel = QLabel('Extract Controls')
        rootOptionLabel = QLabel('Global control stripping')
        channelOptionLabel = QLabel('Channel options')
        if not self.hideLabel:
            self.layout.addRow(tbAdjustmentBlendLabel)
        self.layout.addRow(rootOptionLabel)
        button = QPushButton('Extract Selection')

        self.layout.addRow(button)
        self.layout.addRow(extractOptionLabel)


class SaveCurrentStateWidget(ViewportDialog):
    def __init__(self, parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                 parentMenu=None):
        super(SaveCurrentStateWidget, self).__init__(parent=parent, parentMenu=parentMenu)

        if self.parentMenu:
            self.parentMenu.setEnabled(False)

        self.addButton(quad='SW', button=ToolboxButton(label='Store as Global', parent=self, cls=self,
                                                       command=lambda: QuickSelectionTools().qs_select(),
                                                       closeOnPress=True))
        self.addButton(quad='SW', button=ToolboxButton(label='Store as local', parent=self, cls=self,
                                                       command=lambda: QuickSelectionTools().qs_select(),
                                                       closeOnPress=True))

        self.addButton(quad='SW', button=ToolboxButton(label='Store as Default', parent=self, cls=self,
                                                       command=lambda: lambda: QuickSelectionTools().qs_select(),
                                                       closeOnPress=True))
        '''
        self.addButton(quad='SW', button=ToolboxButton(label='SubMENU SW', parent=self, cls=self, command=None,
                                                       closeOnPress=True,
                                                       subMenuClass=SubToolboxWidget,
                                                       popupSubMenu=True
                                                       ))
        '''


class qss_data_obj(object):
    def __init__(self, qs_name="", qs_objects=[], colour=list()):
        self.qs_name = qs_name
        self.qs_objects = qs_objects
        self.qs_colour = colour

    def toJson(self):
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)
        jsonObjectInfo['qs_name'] = self.qs_name
        jsonObjectInfo['qs_objects'] = self.qs_objects
        jsonObjectInfo['qs_colour'] = self.qs_colour
        return jsonObjectInfo


class QssSaveWidget(QWidget):
    """
    Simple prompt with text input
    """
    acceptedSignal = Signal(str)
    acceptedCBSignal = Signal(str, bool, bool)
    rejectedSignal = Signal()
    oldPos = None

    def __init__(self, title='Save Selection Set', label='Name', buttonText=str(), default=str(), combo=list(),
                 checkBox=None, overlay=False, showCloseButton=True, key=str(), subKey=str(),
                 helpString=None,
                 parentWidget=None,
                 qss=False,
                 parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)):
        super(QssSaveWidget, self).__init__(parent=parent)
        self.showCloseButton = showCloseButton
        self.parentWidget = parentWidget
        self.key = key
        self.subKey = subKey
        self.helpString = helpString
        self.overlay = overlay
        self.setStyleSheet(getqss.getStyleSheet())

        self.combo = combo
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.PopupFocusReason | Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.windowFlags()
        self.setWindowTitle('Custom')
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedSize(400, 64)
        titleLayout = QHBoxLayout()
        mainLayout = QVBoxLayout()
        layout = QHBoxLayout()

        self.closeButton = MiniButton()
        self.closeButton.clicked.connect(self.close)

        sel = pm.ls(sl=True)

        self.titleText = QLabel(title)
        self.titleText.setAlignment(Qt.AlignCenter)
        self.text = QLabel(label)

        self.mirrorCheckbox = QCheckBox()
        self.mirrorCheckbox.setText('Mirror')
        self.qssCheckbox = QCheckBox()
        self.qssCheckbox.setChecked(qss)
        self.qssCheckbox.setText('Quick')

        self.saveButton = QPushButton(buttonText)
        self.saveButton.setStyleSheet(getqss.getStyleSheet())
        # layout.addWidget(btnSetFolder)

        titleLayout.addWidget(self.titleText)
        titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(layout)

        self.lineEdit = QLineEdit(default)
        self.lineEdit.setMinimumWidth(120)
        self.lineEdit.setFocusPolicy(Qt.StrongFocus)
        reg_ex = QRegExp("[a-z-A-Z0123456789_:]+")
        input_validator = QRegExpValidator(reg_ex, self.lineEdit)
        self.lineEdit.setValidator(input_validator)

        layout.addWidget(self.text)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.qssCheckbox)
        layout.addWidget(self.mirrorCheckbox)
        layout.addWidget(self.saveButton)

        if self.helpString:
            self.helpLabel = QLabel(self.helpString)
            self.helpLabel.setWordWrap(True)
            mainLayout.addWidget(self.helpLabel)
        self.saveButton.clicked.connect(self.acceptedFunction)

        self.setLayout(mainLayout)
        # self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())

        # self.lineEdit.setFocus()
        self.lineEdit.setFixedWidth(
            max(120, self.lineEdit.fontMetrics().boundingRect(self.lineEdit.text()).width() + 28))
        self.setStyleSheet(
            "QssSaveWidget { "
            "border-radius: 8;"
            "}"
        )

        self.closeButton.setVisible(self.showCloseButton)
        self.resize(self.sizeHint())

        self.show()
        # self.setFixedSize(400, 64)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(qp.CompositionMode_Clear)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 16, 16)
        qp.end()

    def acceptedFunction(self, *args):
        self.acceptedSignal.emit(self.lineEdit.text())
        self.acceptedCBSignal.emit(self.lineEdit.text(),
                                   self.qssCheckbox.isChecked(),
                                   self.mirrorCheckbox.isChecked())
        self.close()

    def close(self):
        self.rejectedSignal.emit()
        if self.overlay:
            self.parent().close()
        super(QssSaveWidget, self).close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.acceptedFunction()
        if event.key() == Qt.Key_Escape:
            self.close()
        try:
            return super(QssSaveWidget, self).keyPressEvent(event)
        except:
            return

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        if self.overlay:
            return
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def show(self):
        position_x = (self.parent().pos().x() + (self.parent().width() - self.frameGeometry().width()) / 2)
        position_y = (self.parent().pos().y() + (self.parent().height() - self.frameGeometry().height()) / 2)

        self.move(position_x, position_y)
        super(QssSaveWidget, self).show()


class QssFileWidget(QWidget):
    loadSignal = Signal(str)

    def __init__(self, name=str, filename=str):
        super(QssFileWidget, self).__init__()
        self.name = name
        self.filename = filename
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self.label = QLabel(self.name)
        self.loadButton = QPushButton('Load')
        self.loadButton.setFixedWidth(64)
        self.loadButton.clicked.connect(self.loadClicked)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.loadButton)

    def loadClicked(self):
        self.loadSignal.emit(self.filename)


class NamespaceWidget(QWidget):
    namespaceChangedSignal = Signal(int)
    namespaceModes = ['From File', 'From Selection']

    namespaceModesOptionVar = 'tb_QssNamespaceMode'

    def __init__(self):
        super(NamespaceWidget, self).__init__()
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.label = QLabel('Namespace source ::')
        self.namespaceModeOption = QComboBox()
        for namespaceMode in self.namespaceModes:
            self.namespaceModeOption.addItem(namespaceMode)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.namespaceModeOption)
        self.namespaceModeOption.setCurrentIndex(pm.optionVar.get(self.namespaceModesOptionVar, 0))
        self.namespaceModeOption.currentIndexChanged.connect(self.namespaceIndexChanged)
        self.namespaceIndexChanged()

    def namespaceIndexChanged(self):
        pm.optionVar(intValue=(self.namespaceModesOptionVar, self.namespaceModeOption.currentIndex()))
        self.namespaceChangedSignal.emit(self.namespaceModeOption.currentIndex())


class LoadQuickSelectWindow(QMainWindow):
    def __init__(self):
        super(LoadQuickSelectWindow, self).__init__(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget))
        # DATA
        self.setMinimumWidth(300)
        # self.setMinimumHeight(400)
        self.QuickSelectionTools = QuickSelectionTools()

        # Main Widgets
        # setup stylesheet
        self.setStyleSheet(getqss.getStyleSheet())
        self.setWindowTitle('Quick Select Set Loader')

        main_widget = QWidget()

        self.setCentralWidget(main_widget)

        self.main_layout = QVBoxLayout()
        self.left_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        main_widget.setLayout(self.main_layout)

        menu = self.menuBar()
        edit_menu = menu.addMenu('&File')

        add_action = QAction('Convert old format to json', self)
        edit_menu.addAction(add_action)
        add_action.triggered.connect(self.convertlegacy)

        self.qssScrollArea = QScrollArea()
        self.qssScrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.qssScrollArea.setWidgetResizable(True)
        self.qssListWidget = QWidget()
        self.qssLayout = QVBoxLayout(self.qssListWidget)
        self.qssListWidget.setLayout(self.qssLayout)
        self.qssScrollArea.setWidget(self.qssListWidget)
        self.main_layout.addWidget(self.qssScrollArea)
        self.addReferenceButton = QPushButton('Add Rig To Map')

        self.namespaceWidget = NamespaceWidget()
        self.namespaceWidget.namespaceChangedSignal.connect(self.namespaceModeChanged)
        self.main_layout.addWidget(self.namespaceWidget)

        self.updateUI()

    def namespaceModeChanged(self, i):
        self.QuickSelectionTools.namespace_mode = i

    def convertlegacy(self):
        self.QuickSelectionTools.convertPickleToJson()

    def loadQss(self, name):
        self.QuickSelectionTools.namespace_mode = self.namespaceWidget.namespaceModeOption.currentIndex()
        self.QuickSelectionTools.load_qss_file(name)

    def updateUI(self):
        self.QuickSelectionTools.restore_qs_from_dir()
        for item in self.QuickSelectionTools.qss_files:
            widget = QssFileWidget(name=item.split('.')[0], filename=item)
            widget.loadSignal.connect(self.loadQss)
            self.qssLayout.addWidget(widget)
        self.qssLayout.addStretch()
