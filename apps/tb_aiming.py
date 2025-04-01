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


xAx = om.MVector.xAxis
yAx = om.MVector.yAxis
zAx = om.MVector.zAxis
rad_to_deg = 57.2958
axisMapping = {
    0: xAx,
    1: yAx,
    2: zAx
}
kRotateOrderMapping = {
    'xyz': om.MEulerRotation.kXYZ,
    'yzx': om.MEulerRotation.kYZX,
    'zxy': om.MEulerRotation.kZXY,
    'xzy': om.MEulerRotation.kXZY,
    'yxz': om.MEulerRotation.kYXZ,
    'zyx': om.MEulerRotation.kZYX,
    '0': om.MEulerRotation.kXYZ,
    '1': om.MEulerRotation.kYZX,
    '2': om.MEulerRotation.kZXY,
    '3': om.MEulerRotation.kXZY,
    '4': om.MEulerRotation.kYXZ,
    '5': om.MEulerRotation.kZYX
}



assetCommandName = 'aimToolAssetMenu'
maya.utils.loadStringResourcesForModule(__name__)


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.commandList = list()
        self.setCategory(self.helpStrings.category.get('TempControls'))
        self.addCommand(self.tb_hkey(name='bakeAim',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAim()']))

        self.addCommand(self.tb_hkey(name='bakeAim_X_Yup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimXY()']))
        self.addCommand(self.tb_hkey(name='bakeAim_X_Zup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimXZ()']))

        self.addCommand(self.tb_hkey(name='bakeAim_Y_Xup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimYX()']))
        self.addCommand(self.tb_hkey(name='bakeAim_Y_Zup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimYZ()']))

        self.addCommand(self.tb_hkey(name='bakeAim_Z_Xup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimZX()']))
        self.addCommand(self.tb_hkey(name='bakeAim_Z_Yup',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.quickAimZY()']))

        self.addCommand(self.tb_hkey(name='aimAtTempControl',
                                     annotation='Creates a new control at your selection, position it then deselect to bake it out',
                                     category=self.category, command=['AimTools.aimAtTempControl()']))

        self.setCategory(self.helpStrings.category.get('markingMenus'))
        self.addCommand(self.tb_hkey(name='aimToolsMMPressed',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.openMM()']))
        self.addCommand(self.tb_hkey(name='aimToolsMMReleased',
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.closeMM()']))

        self.setCategory(self.helpStrings.category.get('ignore'))
        self.addCommand(self.tb_hkey(name=assetCommandName,
                                     annotation='useful comment',
                                     category=self.category, command=['AimTools.assetRmbCommand()']))

        return self.commandList

    def assignHotkeys(self):
        return


class AimTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'AimTools'
    hotkeyClass = hotkeys()
    funcs = Functions()

    foundControls = dict()  # use this to save the last used settings to a file
    axisDict = {'x': om.MVector.xAxis,
                'y': om.MVector.yAxis,
                'z': om.MVector.zAxis,
                }

    distance = 100.0
    aimData = dict()
    lastUseData = dict()
    defaultData = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': 100.0}
    defaultAimData = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False, 'distance': 100.0}

    tempAimSizeOption = 'tbTempAimLocatorSize'
    aimFwdMotionTrailOption = 'aimFwdMotionTrailOption'
    aimUpMotionTrailOption = 'aimUpMotionTrailOption'
    aimTempMotionTrailOption = 'aimTempMotionTrailOption'
    mainAssetAttr = 'mainAsset'
    constraintTargetAttr = 'constraintTarget'
    tempControlPairAttr = 'tempControlPair'

    aimAtTempControlScriptJobs = list()

    def __new__(cls):
        if AimTools.__instance is None:
            AimTools.__instance = object.__new__(cls)

        AimTools.__instance.val = cls.toolName
        AimTools.__instance.loadData()

        return AimTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

        self.target = None
        self.Ptarget = None
        self.name = None
        self.pos = None
        self.up = None
        self.fwd = None
        self.constraints = list()

        self.aimAxis = None
        self.upAxis = None
        self.flipAim = False
        self.flipUp = False

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(AimTools, self).optionUI()
        infoText = QLabel()
        infoText.setText(
            'Set the default quick aim values here. If a control does not have a specific preset created, the tool will default to these values.\n'
            'The distance value will be used for quick anim bakes for specific axis')
        infoText.setWordWrap(True)
        self.aimWidget = AimAxisWidget(itemList=['x', 'y', 'z'],
                                       aimAxis=self.defaultAimData.get('aimAxis'),
                                       upAxis=self.defaultAimData.get('upAxis'),
                                       flipAim=self.defaultAimData.get('flipAim'),
                                       flipUp=self.defaultAimData.get('flipUp'),
                                       distance=self.defaultAimData.get('distance'))
        tempControlHeader = subHeader('Aim at temp control')
        tempControlInfo = infoLabel(['Creates a temp control at the current selection.',
                                     'Move it into the desired position and once deselected it will baked out relative to the control. The control will then be aimed at the new temp control'])
        crossSizeWidget = intFieldWidget(optionVar=self.tempAimSizeOption,
                                         defaultValue=1.0,
                                         label='Aim to temp control size',
                                         minimum=0.1, maximum=100, step=0.1)
        crossSizeWidget.changedSignal.connect(self.updateTempControlPreview)
        motionTrailHeader = subHeader('Motion Trails')
        motionTrailInfo = infoLabel(['Add motion trails to newly created temp controls.'])

        aimFwdMotionTrailWidget = optionVarBoolWidget('Motion Trail On Aim Forward',
                                                      self.aimFwdMotionTrailOption)
        aimUpMotionTrailWidget = optionVarBoolWidget('Motion Trail On Aim Up',
                                                     self.aimUpMotionTrailOption)
        aimTempMotionTrailWidget = optionVarBoolWidget('Motion Trail On Temp Control',
                                                       self.aimTempMotionTrailOption)
        formLayout = QFormLayout()
        formLayout.addRow(aimFwdMotionTrailWidget.labelText, aimFwdMotionTrailWidget.checkBox)
        formLayout.addRow(aimUpMotionTrailWidget.labelText, aimUpMotionTrailWidget.checkBox)
        formLayout.addRow(aimTempMotionTrailWidget.labelText, aimTempMotionTrailWidget.checkBox)

        self.aimWidget.itemLayout.addStretch()
        self.layout.addWidget(infoText)
        self.layout.addWidget(self.aimWidget)
        self.layout.addWidget(tempControlHeader)
        self.layout.addWidget(tempControlInfo)
        self.layout.addWidget(crossSizeWidget)
        self.layout.addWidget(motionTrailHeader)
        self.layout.addWidget(motionTrailInfo)
        self.layout.addLayout(formLayout)
        self.layout.addStretch()
        self.aimWidget.editedSignal.connect(self.updateDefault)
        return self.optionWidget

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None

    def build_MM(self):
        cmds.menuItem(label='tbAimTools',
                      divider=0,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick Aim at Temp Control',
                      command=self.aimAtTempControl,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick Aim',
                      command=self.quickAim,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Quick aim X Y',
                      command=self.quickAimXY,
                      )
        cmds.menuItem(label='Quick aim Z Y',
                      command=self.quickAimZY,
                      )
        cmds.menuItem(label='Quick aim X Z',
                      command=self.quickAimXZ,
                      )
        cmds.menuItem(label='Quick aim Y Z',
                      command=self.quickAimYZ,
                      )
        cmds.menuItem(label='Quick aim Y X',
                      command=self.quickAimYX,
                      )
        cmds.menuItem(label='Quick aim Z X',
                      command=self.quickAimZX,
                      )
        cmds.menuItem(label='tbAimTools',
                      divider=1,
                      boldFont=True,
                      enable=False,
                      )
        cmds.menuItem(label='Set default for selection',
                      command=self.setDefaultUI,
                      )

    """
    Functions
    """

    def quickAim(self, *args):
        # TODO make this handle multiple objects
        self.aimToLocators(directionDict=self.aimData,
                           default=self.defaultAimData)

    def quickAimXY(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimZY(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimXZ(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'z', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimYZ(self, *args):
        default = {'aimAxis': 'y', 'upAxis': 'z', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimYX(self, *args):
        default = {'aimAxis': 'x', 'upAxis': 'y', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def quickAimZX(self, *args):
        default = {'aimAxis': 'z', 'upAxis': 'x', 'flipAim': False, 'flipUp': False,
                   'distance': self.defaultAimData.get('distance')}
        self.aimToLocators(directionDict=self.aimData, default=default, forceDefault=True)

    def aimToLocators(self, directionDict=dict(), default=dict(), forceDefault=False):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        self.targets = sel
        self.constraints = list()
        self.locators = list()
        self.controlInfo = dict()

        for target in self.targets:
            name = target.split(':')[-1]
            refName, refState = self.funcs.getRefName(target)
            # compare to see if there is a preset in directionDict
            if refName not in directionDict.keys():
                data = default
            elif name not in directionDict[refName].keys():
                data = default
            else:
                if forceDefault:
                    # forcing an override to the preset aim, if there is a preset, grab it's distance value
                    data = default
                    data['distance'] = directionDict[refName][name]['distance']
                else:
                    data = directionDict[refName][name]
            self.aimToLocator(refName, name, target, data)

        self.bake()
        print (self.controlInfo.keys())


        for key, values in self.controlInfo.items():
            self.constraintControls(key, values)


        # select new controls
        cmds.select(self.locators, replace=True)

    def aimToLocator(self, refName, name, target, data):
        asset = self.createAsset(name=name + '_asset')
        aimAxis, upAxis = self.getAimAxis(data)

        up = self.funcs.tempControl(name=name, suffix='upLoc', scale=data.get('scale', 1.0))
        aim = self.funcs.tempControl(name=name, suffix='fwdLoc', scale=data.get('scale', 1.0))

        cmds.addAttr(up, ln=self.mainAssetAttr, at='message')
        cmds.addAttr(aim, ln=self.mainAssetAttr, at='message')
        cmds.addAttr(up, ln=self.constraintTargetAttr, at='message')
        cmds.addAttr(up, ln=self.tempControlPairAttr, at='message')
        cmds.addAttr(aim, ln=self.constraintTargetAttr, at='message')
        cmds.addAttr(aim, ln=self.tempControlPairAttr, at='message')
        cmds.connectAttr(asset + '.message', up + '.' + self.mainAssetAttr)
        cmds.connectAttr(asset + '.message', aim + '.' + self.mainAssetAttr)
        cmds.connectAttr(target + '.message', up + '.' + self.constraintTargetAttr)
        cmds.connectAttr(target + '.message', aim + '.' + self.constraintTargetAttr)
        cmds.connectAttr(aim + '.message', up + '.' + self.tempControlPairAttr)
        cmds.connectAttr(up + '.message', aim + '.' + self.tempControlPairAttr)

        self.locators.extend([str(up), str(aim)])
        self.controlInfo[target] = [str(aim), aimAxis, str(up), upAxis]
        targetPos = cmds.xform(target, query=True, worldSpace=True, absolute=True, rotatePivot=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])

        fwdPos = self.getPosition(target, self.getAxis(data['aimAxis'], data['flipAim']), data['distance'])
        upPos = self.getPosition(target, self.getAxis(data['upAxis'], data['flipUp']), data['distance'])
        cmds.setAttr(aim + '.translate', *fwdPos)
        cmds.setAttr(up + '.translate', *upPos)

        self.constraints.append(cmds.parentConstraint(target, str(aim),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z'))[0])
        self.constraints.append(cmds.parentConstraint(target, str(up),
                                                      maintainOffset=True,
                                                      skipRotate=('x', 'y', 'z'))[0])

        if refName not in self.foundControls.keys():
            self.foundControls[refName] = dict()
        self.foundControls[refName][name] = {'aimAxis': aimAxis,
                                             'upAxis': upAxis,
                                             'flipAim': data['flipAim'],
                                             'flipUp': data['flipUp'],
                                             'distance': data['distance'],
                                             'scale': data.get('scale', 1.0)
                                             }

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=[up, aim])
        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=self.constraints)

        if get_option_var(self.aimFwdMotionTrailOption, False):
            cmds.select(str(aim), replace=True)
            mel.eval('createMotionTrail')
        if get_option_var(self.aimUpMotionTrailOption, False):
            cmds.select(str(up), replace=True)
            mel.eval('createMotionTrail')

    def getAimAxis(self, data):
        flipVector = {True: -1.0, False: 1.0}  # make this data driven somehow?
        aimAxis = self.axisDict[data['aimAxis']] * flipVector[data['flipAim']]
        upAxis = self.axisDict[data['upAxis']] * flipVector[data['flipUp']]
        return aimAxis, upAxis

    def getAxis(self, axis, flip):
        flipVector = {True: -1.0, False: 1.0}  # make this data driven somehow?
        return self.axisDict[axis] * flipVector[flip]

    def bake(self):
        '''

        :return:
        '''
        '''
        keyRange = self.funcs.get_all_layer_key_times(self.targets)
        if keyRange[0] is None:
            keyRange = self.funcs.getTimelineRange()
        '''
        keyRange = self.funcs.getBestTimelineRangeForBake()
        bakeTools = self.allTools.tools['BakeTools']

        bakeTools.quickBake(self.locators, startTime=keyRange[0], endTime=keyRange[1],
                            deleteConstraints=True)

    def constraintControls(self, key, values):
        cmds.aimConstraint(values[0], key,
                           worldUpObject=values[2],
                           aimVector=[values[1][0],values[1][1],values[1][2]],
                           upVector=[values[3][0],values[3][1],values[3][2]],
                           worldUpVector=[values[3][0],values[3][1],values[3][2]],
                           worldUpType='object')

    def setDefaultUI(self, *args):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        aimAxis = 'z'
        upAxis = 'y'
        flipAim = False
        flipUp = False
        distance = 100.0
        refName, refState = self.funcs.getRefName(sel[0])
        if refName in self.aimData.keys():
            name = sel[0].split(':')[-1]
            if name in self.aimData[refName].keys():
                aimAxis = self.aimData[refName][name].get('aimAxis', 'z')
                upAxis = self.aimData[refName][name].get('upAxis', 'y')
                flipAim = self.aimData[refName][name].get('flipAim', False)
                flipUp = self.aimData[refName][name].get('flipUp', False)
                distance = self.aimData[refName][name].get('distance', 100)
                scale = self.aimData[refName][name].get('scale', 1.0)
        prompt = AimAxisDialog(parent=self.funcs.getMainWindow(),
                               controlName=sel[0],
                               title='Set Default Aim Values',
                               text='Control : {s}'.format(s=sel[0]),
                               itemList=['x', 'y', 'z'],
                               aimAxis=aimAxis,
                               upAxis=upAxis,
                               flipAim=flipAim,
                               flipUp=flipUp,
                               distance=distance)
        prompt.show()
        prompt.assignSignal.connect(self.assignDefault)
        prompt.editedSignal.connect(self.updatePreview)
        prompt.closeSignal.connect(self.deletePreview)
        prompt.aimWidget.widgetedited()
        '''
        if prompt.exec_():
            pass
        else:
            pass
        '''

    def updatePreview(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        fwdPreview = 'fwd_Preview'
        upPreview = 'up_Preview'
        if not cmds.objExists(fwdPreview):
            fwdPreview = self.funcs.tempControl(name='fwd', suffix='Preview', scale=scale)
            fwdAnn = cmds.annotate(fwdPreview, tx='Aim Forward', p=(0, 1, 0))
            cmds.parent(fwdAnn, fwdPreview)
        if not cmds.objExists(upPreview):
            upPreview = self.funcs.tempControl(name='up', suffix='Preview', scale=scale)
            upAnn = cmds.annotate(upPreview, tx='Aim Up', p=(0, 1, 0))
            cmds.parent(upAnn, upPreview)

        cmds.setAttr(fwdPreview + '.scale', scale, scale, scale)
        cmds.setAttr(upPreview + '.scale', scale, scale, scale)
        fwdPos = self.getPosition(controlName, self.getAxis(aimAxis, flipAim), distance)
        upPos = self.getPosition(controlName, self.getAxis(upAxis, flipUp), distance)
        cmds.setAttr(fwdPreview + '.translate', *fwdPos)
        cmds.setAttr(upPreview + '.translate', *upPos)

    def updateDefault(self, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        self.defaultAimData['aimAxis'] = aimAxis
        self.defaultAimData['upAxis'] = upAxis
        self.defaultAimData['flipAim'] = flipAim
        self.defaultAimData['flipUp'] = flipUp
        self.defaultAimData['distance'] = distance
        self.defaultAimData['scale'] = scale
        self.saveData()

    def deletePreview(self):
        fwdPreview = 'fwd_Preview'
        upPreview = 'up_Preview'
        if cmds.objExists(fwdPreview):
            cmds.delete(fwdPreview)
        if cmds.objExists(upPreview):
            cmds.delete(upPreview)

    def getPosition(self, target, axis, distance):
        targetPos = cmds.xform(target, query=True, worldSpace=True, absolute=True, rotatePivot=True)
        targetPosMVector = om.MVector(targetPos[0], targetPos[1], targetPos[2])

        # depending on the rig this really doesn't work
        vec = getLocalVecToWorldSpaceAPI(target, vec=axis, offset=targetPosMVector,
                                         mult=distance / self.funcs.unit_conversion())
        return vec

    def createAsset(self, name, imageName=None):
        asset = cmds.container(name=name,
                               includeHierarchyBelow=False,
                               includeTransform=True,
                               )
        if imageName:
            cmds.setAttr(asset + '.iconName', imageName, type="string")
        cmds.setAttr(asset + '.rmbCommand', assetCommandName, type='string')
        return asset

    def assetRmbCommand(self):
        panel = cmds.getPanel(underPointer=True)
        parentMMenu = panel + 'ObjectPop'
        cmds.popupMenu(parentMMenu, edit=True, deleteAllItems=True)
        sel = cmds.ls(sl=True)
        asset = cmds.container(query=True, findContainer=sel[0])

        cmds.menuItem(label='Aim Tool', enable=False, boldFont=True, image='container.svg')
        cmds.menuItem(divider=True)
        cmds.menuItem(label='Re bake to fixed distance', command=create_callback(self.rebakeCommand, asset))
        cmds.menuItem(label='Bake out to layer', command=create_callback(self.bakeOutCommand, sel, asset))
        cmds.menuItem(label='Delete all controls', command=create_callback(self.deletControlsCommand, asset))
        cmds.menuItem(divider=True)

    def rebakeCommand(self, asset, *args):
        sel = cmds.ls(sl=True)
        control = cmds.listConnections(asset + '.' + self.constraintTargetAttr)[0]
        locators = cmds.listConnections(asset + '.message')
        temp = list()
        constraints = list()
        for loc in locators:
            tmp = cmds.createNode('transform')
            cmds.delete(cmds.pointConstraint(loc, tmp))
            constraints.append(cmds.parentConstraint(control, tmp, maintainOffset=True, skipRotate=('x', 'y', 'z'))[0])
            temp.append(tmp)

        cmds.select(temp, replace=True)

        self.allTools.tools['BakeTools'].simpleBake(sel=temp)
        cmds.delete(constraints)
        for index, loc in enumerate(locators):
            cmds.pointConstraint(temp[index], loc)

        self.allTools.tools['BakeTools'].bake_to_override(sel=locators)
        cmds.delete(temp)
        cmds.select(sel, replace=True)

    def bakeOutCommand(self, sel, asset, *args):
        filteredTargets = list()
        allControls = list()
        for s in sel:
            if not cmds.attributeQuery(self.mainAssetAttr, node=str(s), exists=True):
                continue
            mainAsset = cmds.listConnections(str(s) + '.' + self.mainAssetAttr)
            if mainAsset:
                controls = cmds.listConnections(str(mainAsset[0]) + '.' + self.constraintTargetAttr)
            if not controls:
                continue
            filteredTargets.append(controls[0])
            allControls.append(controls[0])

        locators = cmds.listConnections(asset + '.message')
        filteredTargets.extend(locators)
        filteredTargets = list(set(filteredTargets))
        self.allTools.tools['BakeTools'].bake_to_override(sel=filteredTargets)
        cmds.delete(asset)
        cmds.select(allControls)

    def deletControlsCommand(self, asset, *args):
        cmds.delete(asset)

    def assignDefault(self, controlName, aimAxis, upAxis, flipAim, flipUp, distance, scale):
        refName, refState = self.funcs.getRefName(controlName)
        if refName not in self.aimData.keys():
            self.aimData[refName] = dict()
        self.aimData[refName][controlName.split(':')[-1]] = {'aimAxis': aimAxis,
                                                             'upAxis': upAxis,
                                                             'flipAim': flipAim,
                                                             'flipUp': flipUp,
                                                             'distance': distance,
                                                             'scale': scale
                                                             }
        self.saveData()

    def loadData(self):
        super(AimTools, self).loadData()
        self.aimData = self.rawJsonData.get('aimData', dict())
        self.defaultAimData = self.rawJsonData.get('defaultAimData', self.defaultData)

    def toJson(self):
        jsonData = '''{}'''
        self.classData = json.loads(jsonData)
        self.classData['aimData'] = self.aimData
        self.classData['defaultAimData'] = self.defaultAimData

    """
    Hacky stuff for aim at locator
    """

    def clearAimAtTempControlScriptJobs(self):
        allJobs = cmds.scriptJob(listJobs=True)
        allJobID = [int(i.split(':')[0]) for i in allJobs]
        for j in self.aimAtTempControlScriptJobs:
            if j in allJobID:
                try:
                    cmds.scriptJob(kill=j)
                except:
                    pass

    def aimAtTempControl(self, *args):
        sel = cmds.ls(selection=True)
        parentControl = None
        if not sel:
            return
        control = sel[0]

        if len(sel) == 2:
            parentControl = sel[1]

        cmds.undoInfo(openChunk=True, chunkName='aimAtTempControl', stateWithoutFlush=False)
        tempControl = self.funcs.tempLocator(name=control, suffix='AimTempNode')
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)
        cmds.delete(cmds.parentConstraint(control, tempControl))
        cmds.MoveTool()
        cmds.manipMoveContext('Move', edit=True, mode=0)
        cmds.setToolTo(cmds.currentCtx())
        cmds.ctxEditMode()

        self.clearAimAtTempControlScriptJobs()
        self.aimAtTempControlScriptJobs.append(cmds.scriptJob(runOnce=True,
                                                              killWithScene=True,
                                                              compressUndo=True,
                                                              event=("SelectionChanged",
                                                                     create_callback(self.bakeTempAim, control,
                                                                                     tempControl,
                                                                                     parentControl=parentControl))))
        self.aimAtTempControlScriptJobs.append(cmds.scriptJob(runOnce=True,
                                                              killWithScene=True,
                                                              compressUndo=True,
                                                              event=("ToolChanged",
                                                                     create_callback(self.bakeTempAim, control,
                                                                                     tempControl,
                                                                                     parentControl=parentControl))))

    def bakeTempAim(self, control, tempControl, parentControl=None, *args):

        aimLocator = self.funcs.tempControl(name=control, suffix='aim', scale=1.0, color=(1.0, 0.537, 0.016),
                                            drawType='orb')
        if parentControl:
            cmds.connectAttr(str(parentControl) + '.worldMatrix[0]', str(aimLocator) + '.offsetParentMatrix')

        cmds.delete(cmds.orientConstraint(tempControl, aimLocator))
        cmds.delete(cmds.pointConstraint(tempControl, aimLocator))

        cmds.undoInfo(openChunk=True, chunkName='aimAtTempControl', stateWithoutFlush=False)
        cmds.delete(tempControl)
        cmds.undoInfo(closeChunk=True, stateWithoutFlush=True)

        tempConstraint = cmds.parentConstraint(control, aimLocator, maintainOffset=True)
        keyTimes = self.funcs.get_object_key_times(str(control))
        if not keyTimes:
            keyTimes = [cmds.playbackOptions(query=True, min=True), cmds.playbackOptions(query=True, max=True)]
        min_key = min(keyTimes)
        max_key = max(keyTimes)
        keyRange = self.funcs.getBestTimelineRangeForBake()

        cmds.bakeResults(aimLocator,
                         attribute=['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'],
                         simulation=False,
                         minimizeRotation=True,
                         time=(keyRange[0], keyRange[1]))

        cmds.filterCurve(str(aimLocator) + '.rotateX', str(aimLocator) + '.rotateY', str(aimLocator) + '.rotateZ',
                         filter='euler')
        cmds.delete(tempConstraint)

        constraint = self.constrainAimToTarget(str(control), str(aimLocator))

        asset = self.createAsset(name=control + '_AimAsset')
        cmds.addAttr(aimLocator, ln=self.mainAssetAttr, at='message')
        cmds.addAttr(asset, ln=self.constraintTargetAttr, at='message')
        cmds.connectAttr(asset + '.message', aimLocator + '.' + self.mainAssetAttr)
        cmds.connectAttr(control + '.message', asset + '.' + self.constraintTargetAttr)

        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=str(aimLocator))
        cmds.container(asset, edit=True,
                       includeHierarchyBelow=True,
                       force=True,
                       addNode=constraint)

        self.clearAimAtTempControlScriptJobs()

        if get_option_var(self.aimTempMotionTrailOption, False):
            mel.eval('createMotionTrail')

        cmds.select(str(aimLocator), replace=True)

    def constrainTargetToControl(self, control, target):
        keyTimes = self.funcs.get_object_key_times(control)

        min_key = min(keyTimes)
        max_key = max(keyTimes)

        constraint = cmds.parentConstraint(control, target, maintainOffset=True)
        keyRange = self.funcs.getBestTimelineRangeForBake()
        cmds.bakeResults(target,
                         attribute=['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'],
                         simulation=False,
                         minimizeRotation=False,
                         time=(keyRange[0], keyRange[1]))
        cmds.delete(constraint)

    def getLocalVector(self, node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
        animNode = self.getDagNode(node)
        matrix = animNode.inclusiveMatrix()
        vec = ((vec * matrix).normal() * mult) + offset
        return om2.MVector(vec.x, vec.y, vec.z)

    def getWorldSpaceVectorOffset(self, control, target, vec=om.MVector.yAxis):
        controlNode = self.getDagNode(control)
        controlMatrix = controlNode.inclusiveMatrix()

        targetNode = self.getDagNode(target)
        targetMatrix = targetNode.inclusiveMatrix()

        vec = ((vec * controlMatrix) * targetMatrix.inverse()).normal()
        return om2.MVector(vec.x, vec.y, vec.z)

    def getDagNode(self, node):
        selList = om.MSelectionList()
        selList.add(node)
        nodeDagPath = om.MDagPath()
        selList.getDagPath(0, nodeDagPath)
        return nodeDagPath

    def constrainAimToTarget(self, control, target):
        locatorPos = om2.MVector(cmds.xform(target, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        controlPos = om2.MVector(cmds.xform(control, query=True, worldSpace=True,
                                            # translation=True,
                                            rotatePivot=True))
        aimVec = (locatorPos - controlPos).normal()

        xDot = aimVec * om2.MVector(1, 0, 0)
        yDot = aimVec * om2.MVector(0, 1, 0)
        zDot = aimVec * om2.MVector(0, 0, 1)

        axisList = [abs(xDot), abs(yDot), abs(zDot)]
        localAxisVecList = [om2.MVector(1, 0, 0), om2.MVector(0, 1, 0), om2.MVector(0, 0, 1)]
        upXxisIndex = axisList.index(min(axisList))

        aimVector = self.getVectorToTarget(target, control)
        upVector = localAxisVecList[upXxisIndex]
        worldUpVector = self.getWorldSpaceVectorOffset(control, target, vec=axisMapping[upXxisIndex])
        aimConstraint = cmds.aimConstraint(target, control,
                                           aimVector=aimVector,
                                           worldUpObject=target,
                                           worldUpVector=worldUpVector,
                                           upVector=upVector,
                                           worldUpType='objectRotation',
                                           maintainOffset=False)[0]
        return aimConstraint

    def getMatrix(self, node):
        '''
        Gets the world matrix of an object based on name.
        # TODO - set the position of the mfn transform to match the rotate pivot
        '''
        selection = om2.MSelectionList()
        selection.add(node)
        MObjectA = selection.getDependNode(0)
        fnThisNode = om2.MFnDependencyNode(MObjectA)
        worldMatrixAttr = fnThisNode.attribute("worldMatrix")
        matrixPlug = om2.MPlug(MObjectA, worldMatrixAttr)
        matrixPlug = matrixPlug.elementByLogicalIndex(0)
        matrixObject = matrixPlug.asMObject()

        worldMatrixData = om2.MFnMatrixData(matrixObject)
        worldMatrix = worldMatrixData.matrix()

        return worldMatrix

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

    def drawTempControlPreview(self):
        self.funcs.tempControl(name='temp',
                               suffix='Preview',
                               scale=get_option_var(self.tempAimSizeOption, 1),
                               drawType='orb')

    def updateTempControlPreview(self, scale):
        if not cmds.objExists('temp_Preview'):
            self.drawTempControlPreview()

        cmds.setAttr('temp_Preview.scaleX', scale)
        cmds.setAttr('temp_Preview.scaleY', scale)
        cmds.setAttr('temp_Preview.scaleZ', scale)


def getLocalVecToWorldSpaceAPI(node, vec=om.MVector.yAxis, offset=om.MVector(0, 0, 0), mult=1.0):
    selList = om.MSelectionList()
    selList.add(node)
    nodeDagPath = om.MDagPath()
    selList.getDagPath(0, nodeDagPath)
    matrix = nodeDagPath.inclusiveMatrix()
    vec = ((vec * matrix).normal() * mult)
    vec += offset
    return vec.x, vec.y, vec.z


class AimAxisDialog(BaseDialog):
    assignSignal = Signal(str, str, str, bool, bool, float, float)
    editedSignal = Signal(str, str, str, bool, bool, float, float)
    closeSignal = Signal()

    def __init__(self, controlName=str, parent=None,
                 title='Set Default',
                 text='Set the parameters for the selected object',
                 itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100,
                 scale=1.0):
        super(AimAxisDialog, self).__init__(parent=parent, title=title, text=text)
        # self.setFixedSize(300 * dpiScale(), 400 * dpiScale())
        self.controlName = controlName
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.assignButton.setFixedHeight(22 * dpiScale())
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.setFixedHeight(22 * dpiScale())
        self.cancelButton.clicked.connect(self.close)
        self.aimHelpButton = HelpButton(width=22, height=22)
        self.aimHelpButton.clicked.connect(self.openCreateHelpWindow)
        self.aimWidget = AimAxisWidgetVertical(itemList=itemList,
                                               aimAxis=aimAxis,
                                               upAxis=upAxis,
                                               flipAim=flipAim,
                                               flipUp=flipUp,
                                               distance=distance,
                                               scale=scale)
        '''
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.itemLayout = QHBoxLayout()
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(32)
        self.upComboBox.setFixedWidth(32)

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80)
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(0.1)
        self.itemLayout.addWidget(aimLabel)
        self.itemLayout.addWidget(self.aimComboBox)
        self.itemLayout.addWidget(upLabel)
        self.itemLayout.addWidget(self.upComboBox)
        self.itemLayout.addWidget(flipAimLabel)
        self.itemLayout.addWidget(self.flipAimCB)
        self.itemLayout.addWidget(flipUpLabel)
        self.itemLayout.addWidget(self.flipUpCB)
        self.itemLayout.addWidget(distanceLabel)
        self.itemLayout.addWidget(self.distanceSpinBox)
        '''
        self.layout.addWidget(self.aimWidget)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.aimHelpButton)
        '''
        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        '''
        self.aimWidget.editedSignal.connect(self.widgetedited)
        self.setFixedSize(self.sizeHint())

    def openCreateHelpWindow(self):
        helpWidget = InfoPromptWidget(title=maya.stringTable['AimTools.CreateHelpTitle'],
                                      buttonText='Ok',
                                      imagePath=helpPath,
                                      error=False,
                                      image=maya.stringTable['AimTools.AimToolDefaultHelp'],
                                      gif=maya.stringTable['AimTools.CreateIsGif'],
                                      helpString=maya.stringTable['AimTools.CreateHelp'])

    def assignPressed(self):
        self.assignSignal.emit(self.controlName,
                               str(self.aimWidget.aimComboBox.currentText()),
                               str(self.aimWidget.upComboBox.currentText()),
                               self.aimWidget.flipAimCB.isChecked(),
                               self.aimWidget.flipUpCB.isChecked(),
                               self.aimWidget.distanceSpinBox.value(),
                               self.aimWidget.scaleSpinBox.value()
                               )
        self.close()

    def close(self):
        self.closeSignal.emit()
        super(AimAxisDialog, self).close()

    def widgetedited(self, aim, up, flipAim, flipUp, distance, scale):
        self.editedSignal.emit(self.controlName,
                               aim,
                               up,
                               flipAim,
                               flipUp,
                               distance,
                               scale
                               )


class AimAxisWidget(QWidget):
    editedSignal = Signal(str, str, bool, bool, float, float)

    def __init__(self, itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100.0,
                 scale=1.0):
        super(AimAxisWidget, self).__init__()
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        self.distance = distance
        self.scale = scale
        self.itemLayout = QHBoxLayout()
        self.setLayout(self.itemLayout)
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(42 * dpiScale())
        self.upComboBox.setFixedWidth(42 * dpiScale())

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.scaleSpinBox = QDoubleSpinBox()
        scaleLabel = QLabel('Scale')
        self.scaleSpinBox.setFixedWidth(80 * dpiScale())
        self.scaleSpinBox.setValue(scale)
        self.scaleSpinBox.setMinimum(0.01)
        self.scaleSpinBox.setSingleStep(0.1)

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80 * dpiScale())
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(1)

        self.itemLayout.addWidget(aimLabel)
        self.itemLayout.addWidget(self.aimComboBox)
        self.itemLayout.addWidget(upLabel)
        self.itemLayout.addWidget(self.upComboBox)
        self.itemLayout.addWidget(flipAimLabel)
        self.itemLayout.addWidget(self.flipAimCB)
        self.itemLayout.addWidget(flipUpLabel)
        self.itemLayout.addWidget(self.flipUpCB)
        self.itemLayout.addWidget(distanceLabel)
        self.itemLayout.addWidget(self.distanceSpinBox)

        # draw scale
        self.itemLayout.addWidget(scaleLabel)
        self.itemLayout.addWidget(self.scaleSpinBox)

        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        self.scaleSpinBox.valueChanged.connect(self.widgetedited)

    def widgetedited(self, *args):
        self.editedSignal.emit(str(self.aimComboBox.currentText()),
                               str(self.upComboBox.currentText()),
                               self.flipAimCB.isChecked(),
                               self.flipUpCB.isChecked(),
                               self.distanceSpinBox.value(),
                               self.scaleSpinBox.value()
                               )


class AimAxisWidgetVertical(QWidget):
    editedSignal = Signal(str, str, bool, bool, float, float)

    def __init__(self, itemList=['x', 'y', 'z'],
                 aimAxis='x',
                 upAxis='z',
                 flipAim=False,
                 flipUp=False,
                 distance=100.0,
                 scale=1.0):
        super(AimAxisWidgetVertical, self).__init__()
        self.aimAxis = aimAxis
        self.upAxis = upAxis
        self.flipAim = flipAim
        self.flipUp = flipUp
        self.distance = distance
        self.scale = scale
        self.itemLayout = QFormLayout()
        self.setLayout(self.itemLayout)
        aimLabel = QLabel('Aim Axis')
        upLabel = QLabel('Up Axis')
        flipAimLabel = QLabel('Flip Aim')
        flipUpLabel = QLabel('Flip Up')
        self.flipAimCB = QCheckBox()
        self.flipAimCB.setChecked(flipAim)
        self.flipUpCB = QCheckBox()
        self.flipUpCB.setChecked(flipUp)
        self.aimComboBox = QComboBox()
        for item in itemList:
            self.aimComboBox.addItem(item)
        self.upComboBox = QComboBox()
        for item in itemList:
            self.upComboBox.addItem(item)
        self.aimComboBox.setFixedWidth(32 * dpiScale())
        self.upComboBox.setFixedWidth(32 * dpiScale())

        self.aimComboBox.setCurrentIndex(itemList.index(self.aimAxis))
        self.upComboBox.setCurrentIndex(itemList.index(self.upAxis))

        self.scaleSpinBox = QDoubleSpinBox()
        scaleLabel = QLabel('Scale')
        self.scaleSpinBox.setFixedWidth(80 * dpiScale())
        self.scaleSpinBox.setValue(scale)
        self.scaleSpinBox.setMinimum(0.01)
        self.scaleSpinBox.setSingleStep(0.1)

        self.distanceSpinBox = QDoubleSpinBox()
        distanceLabel = QLabel('Distance')
        self.distanceSpinBox.setFixedWidth(80 * dpiScale())
        self.distanceSpinBox.setValue(distance)
        self.distanceSpinBox.setMaximum(1000.0)
        self.distanceSpinBox.setSingleStep(1)

        # self.itemLayout.addWidget(aimLabel)
        # self.itemLayout.addWidget(self.aimComboBox)
        # self.itemLayout.addWidget(upLabel)
        # self.itemLayout.addWidget(self.upComboBox)
        # self.itemLayout.addWidget(flipAimLabel)
        # self.itemLayout.addWidget(self.flipAimCB)
        # self.itemLayout.addWidget(flipUpLabel)
        # self.itemLayout.addWidget(self.flipUpCB)
        # self.itemLayout.addWidget(distanceLabel)
        # self.itemLayout.addWidget(self.distanceSpinBox)

        aimLabel.setFixedWidth(64 * dpiScale())
        upLabel.setFixedWidth(64 * dpiScale())
        flipAimLabel.setFixedWidth(64 * dpiScale())
        flipUpLabel.setFixedWidth(64 * dpiScale())
        distanceLabel.setFixedWidth(64 * dpiScale())
        scaleLabel.setFixedWidth(64 * dpiScale())
        self.itemLayout.addRow(aimLabel, self.aimComboBox)
        self.itemLayout.addRow(upLabel, self.upComboBox)
        self.itemLayout.addRow(flipAimLabel, self.flipAimCB)
        self.itemLayout.addRow(flipUpLabel, self.flipUpCB)
        self.itemLayout.addRow(distanceLabel, self.distanceSpinBox)
        self.itemLayout.addRow(scaleLabel, self.scaleSpinBox)

        self.aimComboBox.currentIndexChanged.connect(self.widgetedited)
        self.upComboBox.currentIndexChanged.connect(self.widgetedited)
        self.flipAimCB.clicked.connect(self.widgetedited)
        self.flipUpCB.clicked.connect(self.widgetedited)
        self.distanceSpinBox.valueChanged.connect(self.widgetedited)
        self.scaleSpinBox.valueChanged.connect(self.widgetedited)

    def widgetedited(self, *args):
        self.editedSignal.emit(str(self.aimComboBox.currentText()),
                               str(self.upComboBox.currentText()),
                               self.flipAimCB.isChecked(),
                               self.flipUpCB.isChecked(),
                               self.distanceSpinBox.value(),
                               self.scaleSpinBox.value()
                               )
