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
# from tb_optionVars import optionVar_utils
import tb_optionVars as tb_optionVars
from Abstract import *

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


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='zero_translates', annotation='zero translation values',
                                     category=self.category, command=['Manipulators.zero_translates()']))
        self.addCommand(self.tb_hkey(name='zero_rotates', annotation='zero rotation values',
                                     category=self.category, command=['Manipulators.zero_rotates()']))
        self.addCommand(self.tb_hkey(name='zero_scales', annotation='zero scale values',
                                     category=self.category, command=['Manipulators.zero_scales()']))

        # manipulator tools
        cat = self.helpStrings.category.get('manipulators')

        self.addCommand(self.tb_hkey(name='cycle_current_manipulator',
                                     annotation='cycle the rotation mode',
                                     category=cat,
                                     command=['Manipulators.cycleCurrentManipulator()'],
                                     help=self.helpStrings.cycleCurrentMode))
        self.addCommand(self.tb_hkey(name='cycle_rotation',
                                     annotation='cycle the rotation mode',
                                     category=cat,
                                     command=['Manipulators.cycleRotation()'],
                                     help=self.helpStrings.cycleRotateMode))
        self.addCommand(self.tb_hkey(name='cycle_translation',
                                     annotation='cycle the translation mode',
                                     category=cat,
                                     command=['Manipulators.cycleTranslation()'],
                                     help=self.helpStrings.cycleTranslateMode))
        self.addCommand(self.tb_hkey(name='cycle_object_selection_mask',
                                     annotation='cycle the selection mask',
                                     category=cat,
                                     command=['Manipulators.cycle_selection_mask()']))
        self.addCommand(self.tb_hkey(name='cycle_set_keyframe_type',
                                     annotation='cycle the setkey type',
                                     category=cat,
                                     command=['Manipulators.cycle_key_type()']))
        return self.commandList

    def assignHotkeys(self):
        return cmds.warning(self, 'assignHotkeys', ' function not implemented')


class Manipulators(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Manipulators'
    hotkeyClass = hotkeys()
    funcs = functions()

    # translation
    translate_modes = ['Object', 'Local', 'World', 'Normal',
                       'RotationAxis', 'LiveAxis', 'CustomAxis']
    translate_modesDict = {'Object': 0,
                           'Local': 1,
                           'World': 2,
                           'Normal': 3,
                           'RotationAxis': 4,
                           'LiveAxis': 5,
                           'CustomAxis': 6}

    translate_optionVar = "translate_modes"
    translate_messageVar = "tb_cycle_translation_msg_pos"
    translate_messageLabel = "message position"

    # rotation
    rotate_modes = ['Local', 'World', 'Gimbal', 'Custom axis', 'Component space']
    rotate_modesDict = {'Local': 0,
                        'World': 1,
                        'Gimbal': 2,
                        'Custom axis': 3,
                        'Component space': 9}

    rotate_optionVar = "rotate_modes"
    rotate_messageVar = "tb_cycle_rotation_msg_pos"
    rotate_messageLabel = "message position"

    # selection mask
    selection_modes = ['All', 'Controls']
    selection_optionVar = "tb_cycle_selection"
    rotate_messageVar = "tb_cycle_selection_msg_pos"

    # key types
    key_modes = ["spline", "linear", "clamped", "step", "flat", "plateau", "auto"]
    key_optionVar = "tb_cycle_keytype"
    key_messageVar = "tb_cycle_keytype_msg_pos"
    key_messageLabel = "message position"

    defaultData = {'translate_modes': ['Object', 'Local', 'World'],
                   'rotate_modes': ['Local', 'World', 'Gimbal']}

    modeData = defaultData

    def __new__(cls):
        if Manipulators.__instance is None:
            Manipulators.__instance = object.__new__(cls)
            Manipulators.__instance.initData()

        Manipulators.__instance.val = cls.toolName
        Manipulators.__instance.loadData()
        return Manipulators.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(Manipulators, self).optionUI()
        infoText = QLabel()

        infoText.setText(
            '<P>Set the move/rotate modes that you like to use here.\n'
            'The <b>cycle_rotation</b>, <b>cycle_translation</b> and <b>cycle_current_manipulator</b> commands will use these values.<P>\n')
        infoText.setWordWrap(True)
        self.translateWidget = optionVarListWidget(label='Translate modes',
                                                   optionVar='translate_modes',
                                                   optionList=self.translate_modes,
                                                   classData=self.modeData)
        self.rotateWidget = optionVarListWidget(label='Rotate modes',
                                                optionVar='rotate_modes',
                                                optionList=self.rotate_modes,
                                                classData=self.modeData)
        self.layout.addWidget(infoText)
        self.layout.addWidget(self.translateWidget)
        self.layout.addWidget(self.rotateWidget)

        self.translateWidget.changedSignal.connect(self.updateOptions)
        self.rotateWidget.changedSignal.connect(self.updateOptions)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def loadData(self):
        super(Manipulators, self).loadData()
        self.modeData = self.rawJsonData.get('modeData', self.defaultData)

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['modeData'] = self.modeData

    def updateOptions(self, key, values):
        self.modeData[key] = values
        self.saveData()

    def set_optionVars(self):
        if not pm.optionVar(exists=self.translate_optionVar):
            pass

    def cycleCurrentManipulator(self):
        currentCtx = pm.currentCtx()
        ctxDict = {'RotateSuperContext': self.cycleRotation,
                   'moveSuperContext': self.cycleTranslation,
                   'selectSuperContext': self.cycle_selection_mask}
        ctxDict.get(currentCtx, 'selectSuperContext')()

    def cycleIndex(self, current, keyDict=dict(), user_modes=list(), default=str()):
        currentMode = list(keyDict.keys())[list(keyDict.values()).index(current)]
        print ('currentMode', currentMode)
        print ('user modes', user_modes)
        if currentMode not in user_modes:
            index = 0
            print ('current index NOT in user modes', user_modes)
            print ('next index in user modes', index)
            return user_modes[0], index
        else:
            index = (user_modes.index(currentMode) + 1) % (len(user_modes))
            print ('current index in user modes', user_modes.index(currentMode))
            print ('next index in user modes', index)
            print ('next index name from user modes', user_modes[index])
            return user_modes[index], 0
        indexName = keyDict.keys()[index]
        print ('next mode', indexName, index)
        return indexName, index

    def cycleRotation(self):
        '''
        cycleRotation()
        '''
        # get the name of the move type
        cmds.RotateTool()
        rotateMode = cmds.manipRotateContext('Rotate', query=True, mode=True)
        modeName, modeIndex = self.cycleIndex(current=rotateMode,
                                              keyDict=self.rotate_modesDict,
                                              user_modes=self.modeData[self.rotate_optionVar],
                                              default='Local')
        print ('setting rotate mode to ', modeName, self.rotate_modesDict[modeName])
        pm.manipRotateContext('Rotate', edit=True, mode=self.rotate_modesDict[modeName])
        if pm.optionVar.get(self.rotate_optionVar + "_msg", 0):
            self.funcs.infoMessage(prefix='rotate',
                                   message=' : %s' % modeName,
                                   position=pm.optionVar.get(self.rotate_messageVar, 'topLeft')
                                   )

    def cycleTranslation(self):
        """
        Translate mode:
        0 - Object Space
        1 - Local Space
        2 - World Space (default)
        3 - Move Along Vertex Normal
        4 - Move Along Rotation Axis
        5 - Move Along Live Object Axis
        6 - Custom Axis Orientation
        """
        cmds.MoveTool()
        moveMode = cmds.manipMoveContext('Move', query=True, mode=True)
        modeName, modeIndex = self.cycleIndex(current=moveMode,
                                              keyDict=self.translate_modesDict,
                                              user_modes=self.modeData[self.translate_optionVar],
                                              default='World')

        pm.manipMoveContext('Move', edit=True, mode=self.translate_modesDict[modeName])
        if pm.optionVar.get(self.translate_optionVar + "_msg", 0):
            self.funcs.infoMessage(prefix='translate',
                                   message=' : %s' % modeName,
                                   position=pm.optionVar.get(self.translate_messageVar, 'topLeft')
                                   )

    # this cycle tool doesn't bother with options yet, just toggles between 2 states
    def cycle_selection_mask(self):
        _mode = pm.selectType(query=True, polymesh=True)

        pm.selectType(allObjects=not _mode)

        if _mode:
            cmds.selectType(joint=_mode, nurbsCurve=_mode)
        pm.selectMode(object=True)

        self.funcs.infoMessage(prefix='masking',
                               message=' : %s' % self.selection_modes[_mode],
                               position=pm.optionVar.get(self.translate_messageVar, 'midCenter')
                               )

    def cycle_key_type(self):
        _current_key_type = pm.keyTangent(g=True, query=True, outTangentType=True)[0]

        new_mode, new_name = tb_optionVars.optionVar_utils.cycleOption(option_name=self.key_optionVar,
                                                                       full_list=self.key_modes,
                                                                       current=self.key_modes.index(_current_key_type),
                                                                       default='spline'
                                                                       )
        if new_name == "step":
            _in = 'spline'
        else:
            _in = new_name
        _out = new_name

        display_message = 'default spline tangents'
        cmds.keyTangent(g=True, edit=True, inTangentType=_in, outTangentType=_out)
        self.funcs.infoMessage(prefix='key type',
                               message=' : %s' % _out,
                               position=pm.optionVar.get(self.key_messageVar, 'topLeft')
                               )

    def zero_channel(self, channels, value):
        sel = pm.ls(sl=True)

        for channel in channels:
            for each in sel:
                plug = each + '.' + channel
                try:
                    locked = pm.getAttr(plug, lock=True)
                    if locked:
                        pm.setAttr(plug, lock=False)

                    if pm.getAttr(plug):
                        print (plug)
                        pm.setAttr(plug, value)

                    if locked:
                        pm.setAttr(plug, lock=True)
                except:
                    pass

    def zero_translates(self):
        self.zero_channel(["translateX", "translateY", "translateZ"], 0.0)

    def zero_rotates(self):
        self.zero_channel(["rotateX", "rotateY", "rotateZ"], 0.0)

    def zero_scales(self):
        self.zero_channel(["scaleX", "scaleY", "scaleZ"], 1.0)
