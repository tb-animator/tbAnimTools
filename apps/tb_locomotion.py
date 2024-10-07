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
maya.utils.loadStringResourcesForModule(__name__)

__author__ = 'tom.bailey'

turnexpressionName = '_turnExpression'
attrName = 'DegreesPerMeter'
circleCentreAttr = 'CircleCentre'
offsetAttrName = 'OffsetPosition'

assetCommandName = 'blankCommandName'


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='redirectSelected',
                                     annotation='constrain to object to locator - rotate only',
                                     category=self.category,
                                     command=['LocomotionTools.redirectSelected()'],
                                     help=maya.stringTable['tbCommand.redirectSelected']))
        self.addCommand(self.tb_hkey(name='tbOpenCircleWalkUI',
                                     annotation='',
                                     category=self.category,
                                     command=['LocomotionTools.circleToolBoxUI()']))
        self.addCommand(self.tb_hkey(name='tbOpenStrafeUI',
                                     annotation='',
                                     category=self.category,
                                     command=['LocomotionTools.strafeToolBoxUI()']))
        return self.commandList

    def assignHotkeys(self):
        return


class LocomotionTools(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'LocomotionTools'
    hotkeyClass = hotkeys()
    funcs = Functions()
    start_time = 0
    last_time = 0
    circleToolbox = None
    strafeToolbox = None

    turnAssetName = 'Turn_Control'
    strafeAssetName = 'Strafe_Control'

    autoAlignFeetOption = 'tbAutoAlignFeet'

    def __new__(cls):
        if LocomotionTools.__instance is None:
            LocomotionTools.__instance = object.__new__(cls)

        LocomotionTools.__instance.val = cls.toolName
        return LocomotionTools.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(LocomotionTools, self).optionUI()

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        cmds.menuItem(label='Curved Locomotion Tool', image='redirectSelected.png', command='tbOpenCircleWalkUI',
                    sourceType='mel',
                    parent=parentMenu)
        cmds.menuItem(label='Strafe Locomotion Tool', image='directKeySmall.png', command='tbOpenStrafeUI',
                    sourceType='mel',
                    parent=parentMenu)

    def strafeToolBoxUI(self):
        if self.strafeToolbox:
            self.strafeToolbox.show()
            return
        self.strafeToolbox = BaseDialog(parent=getMainWindow(),
                                        title='tb Strafe Maker', text=str(),
                                        lockState=False, showLockButton=False, showCloseButton=True, showInfo=True)
        toolboxWidget = QWidget()
        buttonLayout = QVBoxLayout()
        toolboxWidget.setLayout(buttonLayout)
        addSelectedButton = QPushButton('Add Strafe to Selected controls')
        addSelectedRotationButton = QPushButton('Add Strafe to Selected controls (rotate only)')
        walkAngleQuickButtonLayout = QHBoxLayout()
        anglesAndLabels = {'S': -180,
                           'SE': -135,
                           'E': -90,
                           'NE': -45,
                           'N': 0,
                           'NW': 45,
                           'W': 90,
                           'SW': 135,
                           'S': 180}
        for key, angle in anglesAndLabels.items():
            angleButton = QPushButton(key)
            angleButton.angle = angle
            angleButton.clicked.connect(create_callback(self.strafeUpdated, value=angle))
            walkAngleQuickButtonLayout.addWidget(angleButton)
        walkAngleLayout = QHBoxLayout()
        walkAngleField = intFieldWidget(defaultValue=0, minimum=-180, maximum=180, step=1)
        strafeAngleLabel = QLabel('Strafe Angle')
        autoFootPeelLabel = QLabel('Auto Adjust Foot peel')
        self.autoFootPeelCheckbox = AnimatedCheckBox(text='On', offText='Off', width=36, height=14)
        walkAngleButton = QPushButton('Set strafe angle')
        walkAngleLayout.addWidget(strafeAngleLabel)
        walkAngleLayout.addWidget(walkAngleField)
        walkAngleLayout.addWidget(autoFootPeelLabel)
        walkAngleLayout.addWidget(self.autoFootPeelCheckbox)
        # walkAngleLayout.addWidget(walkAngleButton)
        tagFootButton = QPushButton('Tag as Foot')
        alignFootButton = QPushButton('Align Foot Peel To Move Direction')
        resetCurveButton = QPushButton('Reset Strafe')
        bakeOutButton = QPushButton('- Bake Out -')
        buttonLayout.addWidget(addSelectedButton)
        buttonLayout.addWidget(addSelectedRotationButton)
        buttonLayout.addLayout(walkAngleQuickButtonLayout)
        buttonLayout.addLayout(walkAngleLayout)
        buttonLayout.addWidget(resetCurveButton)
        buttonLayout.addWidget(tagFootButton)
        buttonLayout.addWidget(alignFootButton)
        buttonLayout.addWidget(bakeOutButton)
        self.strafeToolbox.mainLayout.addWidget(toolboxWidget)

        self.autoFootPeelCheckbox.setChecked(get_option_var(self.autoAlignFeetOption, False))
        cmds.optionVar(intValue=(self.autoAlignFeetOption, get_option_var(self.autoAlignFeetOption, False)))

        addSelectedButton.clicked.connect(lambda: self.addStrafeToSelected(rotateOnly=False))
        addSelectedRotationButton.clicked.connect(lambda: self.addStrafeToSelected(rotateOnly=True))
        walkAngleField.changedSignal.connect(lambda x: self.strafeUpdated(value=x))
        tagFootButton.clicked.connect(self.tagAsFoot)
        alignFootButton.clicked.connect(self.alignFeet)
        resetCurveButton.clicked.connect(self.resetStrafe)
        bakeOutButton.clicked.connect(self.bakeOut)

        self.autoFootPeelCheckbox.clicked.connect(lambda x: cmds.optionVar(intValue=(self.autoAlignFeetOption, x)))

        self.strafeToolbox.show()
        self.strafeToolbox.setFixedSize(self.strafeToolbox.sizeHint())

    def circleToolBoxUI(self):
        if self.circleToolbox:
            self.circleToolbox.show()
            return
        self.circleToolbox = BaseDialog(parent=getMainWindow(),
                                        title='tb Circle Walk', text=str(),
                                        lockState=False, showLockButton=False, showCloseButton=True, showInfo=True)
        toolboxWidget = QWidget()
        buttonLayout = QVBoxLayout()
        toolboxWidget.setLayout(buttonLayout)
        addSelectedButton = QPushButton('Add Selected controls')
        addSelectedRotationButton = QPushButton('Add Selected controls (rotate only)')
        selectCurveButton = QPushButton('Select Curve Main')
        resetCurveButton = QPushButton('Reset curve')
        bakeOutButton = QPushButton('- Bake Out -')
        buttonLayout.addWidget(addSelectedButton)
        buttonLayout.addWidget(addSelectedRotationButton)
        buttonLayout.addWidget(selectCurveButton)
        buttonLayout.addWidget(resetCurveButton)
        buttonLayout.addWidget(bakeOutButton)
        self.circleToolbox.mainLayout.addWidget(toolboxWidget)

        addSelectedButton.clicked.connect(lambda: self.addCircleToSelected(rotateOnly=False))
        addSelectedRotationButton.clicked.connect(lambda: self.addCircleToSelected(rotateOnly=True))
        selectCurveButton.clicked.connect(self.selectCurveMain)
        resetCurveButton.clicked.connect(self.resetCurve)
        bakeOutButton.clicked.connect(self.bakeOut)

        self.circleToolbox.show()
        self.circleToolbox.setFixedSize(self.circleToolbox.sizeHint())

    def bakeOut(self):
        curveMains = cmds.ls('*:Turn_Control')
        allTempControls = list()
        for curve in curveMains:
            childNodes = cmds.listRelatives(curve, children=True, allDescendents=True)
            childNodes = [c for c in childNodes if cmds.attributeQuery('animControl', node=c, exists=True)]
            for c in childNodes:
                tempControls = cmds.listConnections(c + '.' + 'animControl')
                if not tempControls:
                    continue
                allTempControls.append(tempControls[0])
        self.allTools.tools['BakeTools'].quickBake(allTempControls,
                                                   startTime=cmds.playbackOptions(query=True, min=True),
                                                   endTime=cmds.playbackOptions(query=True, max=True),
                                                   deleteConstraints=True)
        cmds.delete(curveMains)

    def selectStrafeMain(self):
        curveMains = cmds.ls('*:Strafe_Control')
        cmds.select(curveMains, replace=True)

    def selectCurveMain(self):
        curveMains = cmds.ls('*:Turn_Control')
        cmds.select(curveMains, replace=True)

    def resetCurve(self):
        curveMains = cmds.ls('*:Turn_Control')
        for c in curveMains:
            try:
                cmds.setAttr(c + '.' + attrName, 0)
            finally:
                pass

    def tagAsFoot(self):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return raiseError('Please select a control to tag as a foot', title='Failed to tag as foot')
        CharacterTool = self.allTools.tools['CharacterTool']
        characters = self.funcs.splitSelectionToCharacters(sel)

        for ch, controls in characters.items():
            refname, namespace = CharacterTool.getSelectedChar(controls[0])
            strippedControls = [c.rsplit(':')[-1] for c in controls]
            CharacterTool.allCharacters[refname].setFeetControls(strippedControls)
            CharacterTool.saveJsonFile(CharacterTool.allCharacters[refname].getJsonFile(),
                                       CharacterTool.allCharacters[refname].toJson())

    def alignFeet(self):
        curveMains = cmds.ls('*:Strafe_Control')
        print('curveMains', curveMains)
        # get the controls that are tagged as feet
        animControls = list()
        for c in curveMains:
            assetControls = cmds.container(c, query=True, nodeList=True)
            print('assetControls', assetControls)
            for control in assetControls:
                if not cmds.attributeQuery('animControl', node=control, exists=True):
                    continue
                animControl = cmds.listConnections(control + '.animControl')
                if not animControl:
                    continue
                animControls.append(animControl[0])
        print('animControls')
        print(animControls)

        CharacterTool = self.allTools.tools['CharacterTool']
        characters = self.funcs.splitSelectionToCharacters(animControls)

        mainCurveRotation = cmds.xform(curveMains[0], query=True, rotation=True, worldSpace=True)

        for ch, controls in characters.items():
            refname, namespace = CharacterTool.getSelectedChar(controls[0])
            feetControls = CharacterTool.allCharacters[refname].getFeetControl(namespace)
            print(refname, feetControls)
            if not feetControls:
                continue
            for f in feetControls:
                cmds.xform(f + '_TiltDirection', rotation=mainCurveRotation, worldSpace=True)

    def resetStrafe(self):
        curveMains = cmds.ls('*:Strafe_Control')
        for c in curveMains:
            try:
                cmds.setAttr(c + '.rotate', 0, 0, 0)
            finally:
                pass

    def strafeUpdated(self, value=0, *args):
        upAxis = cmds.upAxis(query=True, axis=True)
        curveMains = cmds.ls('*:Strafe_Control')
        for c in curveMains:
            try:
                if upAxis == 'y':
                    cmds.setAttr(c + '.rotate', 0, value, 0)
                else:
                    cmds.setAttr(c + '.rotate', 0, 0, value)
            finally:
                pass
        if get_option_var(self.autoAlignFeetOption, False):
            self.alignFeet()

    def addStrafeToSelected(self, rotateOnly=False):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return raiseError('No valid selection', title='Cannot bend loco')

        namespace = sel[0].split(':')[0]
        strippedControllers = [x.split(':')[-1] for x in sel]

        self.redirect(sel, rotateOnly=rotateOnly)

    def addCircleToSelected(self, rotateOnly=False):
        sel = cmds.ls(sl=True, type='transform')
        if not sel:
            return raiseError('No valid selection', title='Cannot bend loco')

        namespace = sel[0].split(':')[0]
        strippedControllers = [x.split(':')[-1] for x in sel]
        turnControllerName = self.createGlobalTurnController(namespace=namespace)

        currentTurnAmount = cmds.getAttr(turnControllerName + '.' + attrName)
        cmds.setAttr(turnControllerName + '.' + attrName, 0)
        rotateOnlyList = list()
        if rotateOnly:
            rotateOnlyList = strippedControllers
        controlData = self.createCircleAnimControllers(namespace=namespace, controls=strippedControllers,
                                                       rotateOnly=rotateOnlyList)
        controlDict = {x: 0 for x in strippedControllers}
        self.addExpressionToNodes(globalControl=turnControllerName,
                                  controls=controlDict,
                                  controlData=controlData)

        cmds.setAttr(turnControllerName + '.' + attrName, currentTurnAmount)

    def createCircleAnimControllers(self, namespace=str(), controls=list(), rotateOnly=list()):
        controlData = dict()
        globalControl = self.createGlobalTurnController(namespace=namespace)
        for cnt in controls:
            thisControl = '{ns}:{ob}'.format(ns=namespace, ob=cnt)
            controlData[cnt] = self.createTempController(control='{ns}:{ob}'.format(ns=namespace, ob=cnt))
            tempController = controlData[cnt]['tempController']
            tempControllerParent = controlData[cnt]['tempParent']
            cmds.addAttr(tempController, ln='animControl', at='message')
            cmds.connectAttr(thisControl + '.message', tempController + '.animControl')
            cmds.addAttr(tempController, ln=circleCentreAttr, at='float')
            cmds.setAttr(tempController + '.' + circleCentreAttr, edit=True, channelBox=True)

            # cmds.container(globalControl, edit=True,
            #              includeHierarchyBelow=True,
            #              force=True,
            #              addNode=[tempControllerParent])
            cmds.parent(tempControllerParent, globalControl)

        allControls = [x['tempController'] for x in controlData.values()]
        self.allTools.tools['BakeTools'].quickBake(allControls,
                                                   startTime=cmds.playbackOptions(query=True, min=True),
                                                   endTime=cmds.playbackOptions(query=True, max=True),
                                                   deleteConstraints=True)

        for cnt in controls:
            if cnt in rotateOnly:
                cmds.parentConstraint(controlData[cnt]['tempController'], '{ns}:{ob}'.format(ns=namespace, ob=cnt),
                                      skipTranslate=('x', 'y', 'z'))
            else:
                cmds.parentConstraint(controlData[cnt]['tempController'], '{ns}:{ob}'.format(ns=namespace, ob=cnt))
        return controlData

    def createGlobalTurnController(self, namespace=str()):
        turnControllerName = '{ns}:{n}'.format(ns=namespace, n=self.turnAssetName)
        if not cmds.objExists(turnControllerName):
            assetShapeControl = self.funcs.tempControl(name=turnControllerName,
                                                       suffix='Shape',
                                                       drawType='arrow',
                                                       scale=2.0)
            cmds.delete(assetShapeControl, ch=True)
            cicleControlAsset = self.createAsset(turnControllerName,
                                                 transform=True,
                                                 imageName='redirectSelected.png',
                                                 assetCommandName=assetCommandName)
            cmds.parent(self.funcs.getShapes(assetShapeControl), cicleControlAsset, r=True, s=True)
            cmds.delete(str(assetShapeControl))

        if not cmds.attributeQuery(attrName, node=turnControllerName, exists=True):
            cmds.addAttr(turnControllerName, ln=attrName, at='double')
            cmds.setAttr(turnControllerName + '.' + attrName, channelBox=True)
        return turnControllerName

    def createGlobalStrafeController(self, namespace=str()):
        turnControllerName = '{ns}:Strafe_Control'.format(ns=namespace)
        if not cmds.objExists(turnControllerName):
            turnControllerName = str(
                self.funcs.tempControl(name='{ns}:Strafe'.format(ns=namespace), suffix='Control', scale=1.0,
                                       drawType='pin'))
        return turnControllerName

    def createTempController(self, control=None):
        if not control:
            return None, None
        if not cmds.objExists(control):
            return None, None
        tempController = str(self.funcs.tempControl(name=control, suffix='Loco', scale=1.0))
        tempParent = str(self.funcs.tempNull(name=control, suffix='LocoGrp'))
        constraint = cmds.parentConstraint(control, tempController)[0]
        cmds.parent(tempController, tempParent)
        forwardAxis = self.guessForwardAxis(control=tempController)
        return {'tempParent': tempParent,
                'tempController': tempController,
                'forwardAxis': forwardAxis,
                'constraint': constraint}

    def max_difference_axis(self, vec1, vec2):
        """
        Returns the axis name with the largest delta
        :param vec1:
        :param vec2:
        :return:
        """
        # Calculate absolute differences for each axis
        diff_x = abs(vec1[0] - vec2[0])
        diff_y = abs(vec1[1] - vec2[1])
        diff_z = abs(vec1[2] - vec2[2])

        # Find the maximum difference among the axes
        max_diff = max(diff_x, diff_y, diff_z)

        # Determine which axis has the maximum difference
        if max_diff == diff_x:
            return 'x'
        elif max_diff == diff_y:
            return 'y'
        else:
            return 'z'

    def guessForwardAxis(self, control=None, startFrame=cmds.playbackOptions(query=True, min=True),
                         endFrame=cmds.playbackOptions(query=True, max=True)):
        if not control:
            return None, None
        if not cmds.objExists(control):
            return None, None

        thisMob = self.funcs.getMObject(control)
        startTranslation = self.getTranslationAtFrame(startFrame, thisMob)
        endTranslation = self.getTranslationAtFrame(endFrame, thisMob)

        return self.max_difference_axis(startTranslation, endTranslation)

    def getTranslationAtFrame(self, endFrame, thisMob):
        currentMDG = OpenMaya.MDGContext(OpenMaya.MTime(endFrame, om2.MTime.uiUnit()))
        currentTransform = self.funcs.om_plug_worldMatrix_at_time('worldMatrix', thisMob, currentMDG)
        mfnTransform = om2.MTransformationMatrix(currentTransform)
        endTranslation = mfnTransform.translation(om2.MSpace.kWorld)
        return endTranslation

    def addExpressionToNodes(self,
                             globalControl=None,
                             controls=dict(),
                             controlData=dict()
                             ):
        """
        Adds an expression to offset the space group, using a multmatrix node to insert the offset, plugs in
        to the driven controls choice node
        :param namespace:
        :param controls:
        :param offsetData:
        :param axis:
        :param space:
        :return:
        """

        upAxis = cmds.upAxis(query=True, axis=True)

        for cnt, offset in controls.items():
            availableAxis = ['x', 'y', 'z']
            # remove the forward axis
            availableAxis = [x for x in availableAxis if x is not controlData[cnt]['forwardAxis']]
            availableAxis = [x for x in availableAxis if x is not upAxis]

            translateAxis = 'translate' + controlData[cnt]['forwardAxis'].upper()
            rotateAxis = 'rotate' + upAxis.upper()
            floorForwardAxis = 'translate' + controlData[cnt]['forwardAxis'].upper()
            floorSideAxis = 'translate' + availableAxis[0].upper()

            if not cmds.attributeQuery(offsetAttrName, node=controlData[cnt]['tempController'], exists=True):
                cmds.addAttr(controlData[cnt]['tempController'], ln=offsetAttrName, at='double')
                cmds.setAttr(controlData[cnt]['tempController'] + '.' + offsetAttrName, channelBox=True)
                cmds.setAttr(controlData[cnt]['tempController'] + '.' + offsetAttrName, offset)

            # print(globalControl, driverNode, offsetNode)

            circleExpression(turnControl=globalControl,
                             turnAttr=attrName,
                             circleCentreAttr=circleCentreAttr,
                             outputNode=controlData[cnt]['tempParent'],
                             driverAttr=translateAxis,
                             rotateAttr=rotateAxis,
                             floorForwardAttr=floorForwardAxis,
                             floorSideAttr=floorSideAxis,
                             offsetAttr=controlData[cnt]['tempController'] + '.' + offsetAttrName,
                             driverControl=controlData[cnt]['tempController']
                             )

    def redirectSelected(self):
        sel = cmds.ls(sl=True)
        if not sel:
            return
        with self.funcs.suspendUpdate():
            try:
                self.redirect(sel)
            except Exception:
                cmds.warning(traceback.format_exc())
                self.funcs.resumeSkinning()

    def redirect(self, sel, rotateOnly=False):
        if not sel:
            return

        roots = dict()
        rotationRoots = dict()
        translateAnimNodes = dict()
        rotateAnimNodes = dict()
        translateAnimOffsetNodes = dict()
        rotateAnimOffsetNodes = dict()
        tempConstraints = list()

        assetShapeControl = self.funcs.tempControl(name='delete', suffix='Root', drawType='arrow', scale=1.0)
        currentAssetName = sel[0].split(':')[0] + ':' + self.strafeAssetName
        if not cmds.objExists(currentAssetName):
            strafeControl = self.createAsset(sel[0].split(':')[0] + ':' + self.strafeAssetName,
                                             transform=True,
                                             imageName='directKeySmall.png',
                                             assetCommandName=assetCommandName)
        else:
            strafeControl = currentAssetName
        cmds.delete(assetShapeControl, ch=True)
        cmds.parent(self.funcs.getShapes(assetShapeControl), strafeControl, r=True, s=True)
        cmds.delete(assetShapeControl)
        # cache the strafe value
        rotateCache = cmds.getAttr(strafeControl + '.rotate')[0]
        cmds.setAttr(strafeControl + '.rotate', 0, 0, 0)
        bakeAttrs = list()
        upAxis = cmds.upAxis(query=True, axis=True)
        for s in sel:
            # root = self.funcs.tempControl(name=s, suffix='Root', drawType='redirectRoot', scale=0.5)

            rotationRoot = self.funcs.tempControl(name=s, suffix='RotationRoot', drawType='sphereZ', scale=0.7)
            cmds.addAttr(str(rotationRoot), ln='animControl', at='message')
            cmds.connectAttr(s + '.message', str(rotationRoot) + '.animControl')
            # worldOffsetControl = self.funcs.tempControl(name=s, suffix='TranslateOffset', drawType='redirectRoot',
            #                                             scale=1)

            # translateAnimOFfsetNode = self.funcs.tempControl(name=s, suffix='TranslateOffset', drawType='plus',
            #                                                  scale=0.75)
            # self.funcs.getSetColour(s, translateAnimOFfsetNode, brightnessOffset=0.15)

            rotateAnimNode = self.funcs.tempNull(name=s, suffix='RotateBaked')
            rotateAnimOffsetNode = self.funcs.tempControl(name=s, suffix='RotateOffset', drawType='diamond',
                                                          scale=1, rotateOrder=2)
            tiltAnimOffsetNode = self.funcs.tempControl(name=s, suffix='TiltDirection', drawType='arrow',
                                                        scale=1.0, rotateOrder=3)
            cmds.setAttr(tiltAnimOffsetNode + '.rotateX', lock=True, channelBox=False)
            cmds.setAttr(tiltAnimOffsetNode + '.rotateY', lock=True, channelBox=False)
            cmds.setAttr(tiltAnimOffsetNode + '.rotateZ', lock=True, channelBox=False)
            cmds.setAttr(tiltAnimOffsetNode + '.translate', lock=True, channelBox=False)
            cmds.setAttr(tiltAnimOffsetNode + '.scale', lock=True, channelBox=False)
            cmds.setAttr(tiltAnimOffsetNode + '.rotate' + upAxis.upper(), lock=False, channelBox=True)

            self.funcs.getSetColour(s, rotationRoot, brightnessOffset=-0.15)
            self.funcs.getSetColour(s, rotateAnimOffsetNode, brightnessOffset=0.15)

            if cmds.attributeQuery('jointOrient', node=s, exists=True):
                tiltComposeMatrix = cmds.createNode('composeMatrix')
                tiltInverseMatrix = cmds.createNode('inverseMatrix')

                jointOrientComposeMatrix = cmds.createNode('composeMatrix')
                jointOrientMultMatrix = cmds.createNode('multMatrix')
                jointOrientInverseMatrix = cmds.createNode('inverseMatrix')
                jointOrientOutMultMatrix = cmds.createNode('multMatrix')

                cmds.connectAttr(tiltAnimOffsetNode + '.rotate', tiltComposeMatrix + '.inputRotate')
                cmds.connectAttr(tiltComposeMatrix + '.outputMatrix', rotateAnimNode + ' .offsetParentMatrix')

                # connect the joint orient to some mult matrices to compensate
                cmds.connectAttr(s + '.jointOrient', jointOrientComposeMatrix + '.inputRotate')
                cmds.connectAttr(jointOrientComposeMatrix + '.outputMatrix', jointOrientMultMatrix + '.matrixIn[0]')
                cmds.connectAttr(tiltComposeMatrix + '.outputMatrix', jointOrientMultMatrix + '.matrixIn[1]')

                cmds.connectAttr(jointOrientMultMatrix + '.matrixSum', jointOrientOutMultMatrix + '.matrixIn[0]')
                cmds.connectAttr(jointOrientComposeMatrix + '.outputMatrix', jointOrientInverseMatrix + '.inputMatrix')
                cmds.connectAttr(jointOrientInverseMatrix + '.outputMatrix', jointOrientOutMultMatrix + '.matrixIn[1]')
                cmds.connectAttr(jointOrientOutMultMatrix + '.matrixSum', tiltInverseMatrix + '.inputMatrix')
                cmds.connectAttr(tiltInverseMatrix + '.outputMatrix', rotateAnimOffsetNode + ' .offsetParentMatrix')
            else:
                tiltComposeMatrix = cmds.createNode('composeMatrix')
                tiltInverseMatrix = cmds.createNode('inverseMatrix')

                cmds.connectAttr(tiltAnimOffsetNode + '.rotate', tiltComposeMatrix + '.inputRotate')
                cmds.connectAttr(tiltComposeMatrix + '.outputMatrix', tiltInverseMatrix + '.inputMatrix')
                cmds.connectAttr(tiltComposeMatrix + '.outputMatrix', rotateAnimNode + ' .offsetParentMatrix')
                cmds.connectAttr(tiltInverseMatrix + '.outputMatrix', rotateAnimOffsetNode + ' .offsetParentMatrix')

            cmds.parent(tiltAnimOffsetNode, rotationRoot)
            cmds.parent(rotateAnimOffsetNode, rotateAnimNode)
            cmds.parent(rotateAnimNode, rotationRoot)

            # cmds.parent(translateAnimOFfsetNode, translateAnimNode)

            cmds.setAttr(rotationRoot + '.inheritsTransform', 0)

            tempConstraints.append(cmds.parentConstraint(s, rotateAnimNode)[0])

            # tempConstraints.append(cmds.parentConstraint(s, worldOffsetControl, skipRotate=('x', 'y', 'z')))
            tempConstraints.append(cmds.parentConstraint(s, rotationRoot, skipRotate=('x', 'y', 'z'))[0])
            # cmds.pointConstraint(worldOffsetControl, rotationRoot)

            bakeAttrs.extend([str(rotationRoot) + '.translate' + x for x in ['X','Y','Z']])
            bakeAttrs.extend([str(rotateAnimNode) + '.rotate' + x for x in ['X','Y','Z']])
            bakeAttrs.extend([str(rotateAnimNode) + '.translate' + x for x in ['X','Y','Z']])
            rotationRoots[s] = rotationRoot
            rotateAnimNodes[s] = rotateAnimNode
            # translateAnimOffsetNodes[s] = worldOffsetControl
            rotateAnimOffsetNodes[s] = rotateAnimOffsetNode

            # cmds.parent(worldOffsetControl, strafeControl)
            cmds.parent(rotationRoot, strafeControl)
        # cmds.container(strafeControl, edit=True,
        #              includeHierarchyBelow=False,
        #              force=True,
        #              addNode=list(roots.values()))

        bakeTargets = list(rotationRoots.values()) + list(rotateAnimNodes.values())

        keyRange = self.funcs.getBestTimelineRangeForBake()
        with self.funcs.suspendUpdate():
            cmds.bakeResults(bakeAttrs,
                           time=(keyRange[0], keyRange[1]),
                           simulation=True,
                           sampleBy=1,
                           oversamplingRate=1,
                           disableImplicitControl=True,
                           preserveOutsideKeys=False,
                           sparseAnimCurveBake=True,
                           removeBakedAttributeFromLayer=False,
                           removeBakedAnimFromLayer=False,
                           bakeOnOverrideLayer=False,
                           minimizeRotation=True,
                           controlPoints=False,
                           shape=False)
        cmds.delete(tempConstraints)

        if int(cmds.about(majorVersion=True)) >= 2020:
            for o in rotationRoots.values():
                o = str(o)
                composeMatrix = cmds.createNode('composeMatrix')
                multMatrix = cmds.createNode('multMatrix')
                pickMatrix = cmds.createNode('pickMatrix')
                cmds.setAttr(pickMatrix + '.useScale', False)
                cmds.setAttr(pickMatrix + '.useRotate', False)
                cmds.setAttr(pickMatrix + '.useShear', False)
                cmds.connectAttr(multMatrix + '.matrixSum', pickMatrix + '.inputMatrix')
                cmds.connectAttr(composeMatrix + '.outputMatrix', multMatrix + '.matrixIn[0]')
                cmds.connectAttr(strafeControl + '.worldMatrix[0]', multMatrix + '.matrixIn[1]')
                cmds.connectAttr(pickMatrix + '.outputMatrix', o + '.offsetParentMatrix')
                for a in ['X', 'Y', 'Z']:
                    conns = cmds.listConnections(o + '.translate' + a, source=True, destination=False,
                                                 plugs=True)
                    if not conns:
                        print('no connections', o)
                        continue
                    conns = conns[0]
                    cmds.disconnectAttr(conns, o + '.translate' + a)
                    cmds.connectAttr(conns, composeMatrix + '.inputTranslate.inputTranslate' + a)

                cmds.setAttr(o + '.translate', 0, 0, 0)
        # TODO - add scalar/blend to animated nodes-rest position

        for s in sel:
            translateTarget = rotateAnimOffsetNodes.get(s, None)
            rotateTarget = rotateAnimOffsetNodes.get(s, None)
            if translateTarget:
                if not rotateOnly:
                    cmds.pointConstraint(rotateAnimOffsetNodes[s], s)
            if rotateTarget:

                if self.funcs.getAvailableRotates(s):
                    continue
                cmds.orientConstraint(rotateAnimOffsetNodes[s], s)

        cmds.setAttr(strafeControl + '.rotate', *rotateCache)


def circleExpression(turnControl=str(),
                     turnAttr=str(),
                     driverAttr=str(),
                     rotateAttr=str(),
                     circleCentreAttr=str(),
                     floorForwardAttr=str(),
                     floorSideAttr=str(),
                     offsetAttr=str(),
                     driverControl=str(),
                     outputNode=str()):
    """
    Builds the actual expression used to bend the x/y axis into a circular motion
    :param namespace:
    :param turnControl:
    :param turnAttr:
    :param driverAttr:
    :param offsetAttr:
    :param driverControl:
    :param outputNode:
    :return:
    """
    upAxis = cmds.upAxis(query=True, axis=True)

    if upAxis == 'y':
        outFwdCalc = "{out}.{t} = (-$rot_offset.x + $circle.x -$offset.x);".format(out=outputNode,
                                                                                   t=floorForwardAttr)
        outSideCalc = "{out}.{t} = -(-$rot_offset.z + $circle.z - $offset.z);".format(out=outputNode,
                                                                                      t=floorSideAttr)
    else:
        outFwdCalc = "{out}.{t} = (-$rot_offset.x + $circle.x -$offset.x);".format(out=outputNode,
                                                                                   t=floorSideAttr)
        outSideCalc = "{out}.{t} = (-$rot_offset.z + $circle.z - $offset.z);".format(out=outputNode,
                                                                                     t=floorForwardAttr)
    if 'X' in driverAttr:
        circleLine1 = "float $circleX = $radius * cos($angle) - $radius;"
        circleLine2 = "float $circleZ = $radius * sin($angle);"
        progressString = "vector $rot_offset = rot( << 0, 0, $progress >>, << 0, 1, 0 >>, -$angle);"
        offsetString = "vector $offset = rot( <<0, 0, {offsetAttr} >>, << 0, 1, 0 >>, -$angle);".format(
            offsetAttr=offsetAttr)
        groupOffsetLine = "vector $group_offset = rot($circle, << 0, 1, 0 >>, -$angle);"
        outAngleLine = "{out}.{r} = rad_to_deg(-$angle);".format(out=outputNode, r=rotateAttr)
    else:
        circleLine1 = "float $circleX = $radius * sin($angle);"
        circleLine2 = "float $circleZ = ($radius * cos($angle))- $radius;"
        progressString = "vector $rot_offset = rot( <<$progress, 0, 0 >>, << 0, 1, 0 >>, $angle);"
        offsetString = "vector $offset = rot( <<{offsetAttr}, 0, 0 >>, << 0, 1, 0 >>, -$angle);".format(
            offsetAttr=offsetAttr)
        groupOffsetLine = "vector $group_offset = rot($circle, << 0, 1, 0 >>, $angle);"
        outAngleLine = "{out}.{r} = rad_to_deg($angle);".format(out=outputNode, r=rotateAttr)

    expString = [
        "float $progress = {driverControl}.{driverAttr};".format(driverControl=driverControl,
                                                                 driverAttr=driverAttr),
        "float $offset = {offsetAttr};".format(offsetAttr=offsetAttr),
        "float $turn = {control}.{attr};".format(control=turnControl, attr=turnAttr),
        "float $circumference = 0.0;",
        "float $angle = 0.0;",
        "float $radius = 0.0;",
        "if (abs($turn) > 0.0)",
        "{",
        "$circumference = 100.0 * (360.0 /$turn);",
        "$radius = 0.5 * ($circumference / 3.14159265359);",
        "$angle = 2.0 * 3.14159265359 * (($progress + $offset) / $circumference);",
        offsetString,
        circleLine1,
        circleLine2,
        "$circle = << $circleX, 0.0, $circleZ >>;",
        progressString,
        groupOffsetLine,
        outFwdCalc,
        outSideCalc,
        "{out}.{t} = $radius;".format(out=driverControl, t=circleCentreAttr),
        outAngleLine,
        "}",
        "else",
        "{",
        "{out}.{t} = 0.0;".format(out=outputNode, t=floorForwardAttr),
        "{out}.{t} = 0.0;".format(out=outputNode, t=floorSideAttr),
        "{out}.{r} = 0.0;".format(out=outputNode, r=rotateAttr),
        "{out}.{r} = 0.0;".format(out=driverControl, r=circleCentreAttr),
        "}"]
    cmds.expression(name=outputNode + turnexpressionName, s=str('\n').join(expString))


def removeExpressionFromNodes(namespace=str(),
                              globalControl=str(),
                              controls=list()):
    """
    Removes any turning expression applied to a certain space.
    Also cleans up any attributes that were added to controls
    :param namespace:
    :param driverData:
    :param space:
    :return:
    """
    control = '{ns}:{S}'.format(ns=namespace, S=globalControl)
    if cmds.attributeQuery(attrName, node=control, exists=True):
        cmds.deleteAttr(control + '.' + attrName)

    for control in controls:
        node = '{ns}:{ob}'.format(ns=namespace, ob=control)
        expression = cmds.listConnections(node + '.' + offsetAttrName, source=False, destination=True, plugs=False)
        cmds.delete(expression)
