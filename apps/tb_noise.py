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



class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('noise'))
        self.commandList = list()

        self.addCommand(self.tb_hkey(name='tbOpenNoiseUI',
                                     annotation='',
                                     category=self.category,
                                     command=['Noise.toolBoxUI()']))
        return self.commandList

    def assignHotkeys(self):
        return pm.warning(self, 'assignHotkeys', ' function not implemented')


class NoiseTool(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'Noise'
    hotkeyClass = hotkeys()
    funcs = functions()
    toolbox = None

    def __new__(cls):
        if NoiseTool.__instance is None:
            NoiseTool.__instance = object.__new__(cls)

        NoiseTool.__instance.val = cls.toolName
        return NoiseTool.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        return super(NoiseTool, self).optionUI()

    def showUI(self):
        return cmds.warning(self, 'optionUI', ' function not implemented')

    def drawMenuBar(self, parentMenu):
        return None


    def toolBoxUI(self):
        if not self.toolbox:
            self.toolbox = BaseDialog(parent=wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget),
                             title='tbNoise Toolbox', text=str(),
                             lockState=False, showLockButton=False, showCloseButton=True, showInfo=True, )
            widget = ToolBoxWidget()
            self.toolbox.mainLayout.addWidget(widget)

        self.toolbox.show()
        self.toolbox.setFixedSize(self.toolbox.sizeHint())


class ToolBoxWidget(QWidget):
    loopOption = 'tbNoiseLoop'
    loopOptions = ['On','Off']
    loopModes = ['NoiseLoop', 'Noise']

    def __init__(self):
        super(ToolBoxWidget, self).__init__()
        buttonWidth = 108
        buttonHeight = 40

        self.amplitude = 0
        self.frequency = 0
        self.isCached = False

        toolBoxLayout = QVBoxLayout()
        toolBoxLayout.setContentsMargins(0, 0, 0, 0)
        toolBoxLayout.setSpacing(0)
        self.setLayout(toolBoxLayout)

        menuBar = None
        restoreLayout = QHBoxLayout()
        self.frequencySlider = SliderFloatField(label='Frequency')
        self.frequencySlider.slider.setOrientation(Qt.Horizontal)
        self.frequencySlider.slider.setFixedWidth(200)
        self.frequencySlider.slider.setMinimum(-100)
        self.frequencySlider.slider.setMaximum(100)
        self.frequencySlider.slider.setValue(0)
        self.frequencySlider.slider.setTickInterval(1)

        self.amplitudeSlider = SliderFloatField(label='Amplitude')
        self.amplitudeSlider.slider.setOrientation(Qt.Horizontal)
        self.amplitudeSlider.slider.setFixedWidth(200)
        self.amplitudeSlider.slider.setMinimum(-100)
        self.amplitudeSlider.slider.setMaximum(100)
        self.amplitudeSlider.slider.setValue(0)
        self.amplitudeSlider.slider.setTickInterval(1)

        self.frequencySlider.valueChanged.connect(self.frequencyChanged)
        self.amplitudeSlider.valueChanged.connect(self.amplitudeChanged)
        '''
        self.slider.sliderMoved.connect(self.sliderValueChanged)
        self.slider.sliderMoved.connect(self.slider.sliderMovedEvent)
        self.slider.wheelSignal.connect(self.sliderWheelUpdate)
        self.slider.sliderReleased.connect(self.sliderReleased)
        self.slider.sliderReleased.connect(self.slider.sliderReleasedEvent)
        '''

        restoreLayout.addWidget(self.frequencySlider)

        cacheLayout = QHBoxLayout()
        cacheButton = ToolButton(text='Cache Selection',
                                 width=buttonWidth,
                                 height=24,
                                 icon=":/advancedSettings.png",
                                 sourceType='python')
        resetButton = ToolButton(text='Reset',
                                 width=buttonWidth,
                                 height=24,
                                 icon=":/advancedSettings.png",
                                 sourceType='python')
        noiseType = radioGroupWidget(optionVarList=self.loopOptions,
                         optionVar=self.loopOption,
                         defaultValue=self.loopOptions[0], label='Looping')
        cacheButton.clicked.connect(self.cache)
        resetButton.clicked.connect(self.reset)
        noiseType.editedSignal.connect(self.doTween)

        cacheLayout.addWidget(cacheButton)
        cacheLayout.addWidget(resetButton)
        cacheLayout.addWidget(noiseType)

        commitLayout = QHBoxLayout()
        commitButton = ToolButton(text='Commit',
                                  width=buttonWidth,
                                  height=24,
                                  icon=":/advancedSettings.png",
                                  command='tbCollisionPresetUI')
        cancelButton = ToolButton(text='Cancel',
                                  width=buttonWidth,
                                  height=24,
                                  icon=":/advancedSettings.png",
                                  command='tbCollisionPresetUI')
        commitLayout.addWidget(cancelButton)
        commitLayout.addWidget(commitButton)

        toolBoxLayout.addLayout(cacheLayout)
        toolBoxLayout.addWidget(self.frequencySlider)
        toolBoxLayout.addWidget(self.amplitudeSlider)

    def frequencyChanged(self, value):
        self.frequency = value
        self.doTween()

    def amplitudeChanged(self, value):
        self.amplitude = value
        self.doTween()

    def doTween(self):
        if self.isCached:
            cmds.tbKeyTween(alpha=self.frequency, alphaB=self.amplitude, blendMode=self.getMode(), clearCache=False)

    def getMode(self):
        return self.loopModes[self.loopOptions.index(pm.optionVar.get(self.loopOption, self.loopOptions[0]))]

    def cache(self):
        self.frequencySlider.reset()
        self.amplitudeSlider.reset()

        cmds.tbKeyTween(alpha=0.0, alphaB=0.0, blendMode=self.getMode(), clearCache=True)
        self.isCached = True

    def reset(self):
        self.amplitude = 0
        self.frequency = 0
        self.doTween()
        self.frequencySlider.reset()
        self.amplitudeSlider.reset()
