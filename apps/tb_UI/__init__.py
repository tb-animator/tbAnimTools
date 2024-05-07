import os
import pymel.core as pm
import re
import maya.mel as mel
import maya.cmds as cmds
import math
from functools import partial
import maya.api.OpenMaya as om2
qtVersion = pm.about(qtVersion=True)
QTVERSION = int(qtVersion.split('.')[0])
if QTVERSION < 5:
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

import maya.OpenMayaUI as omUI


def getMainWindow():
    if not cmds.about(batch=True):
        return wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)
    return None


margin = 2
MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)
scriptLocation = os.path.dirname(os.path.realpath(__file__))
IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Icons'))
helpPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Help'))
baseIconFile = 'checkBox.png'

from colorsys import rgb_to_hls, hls_to_rgb

import getStyleSheet as getqss
from .tb_UIScale import dpiScale, dpiFontScale, defaultFont, boldFont, semiBoldFont, adjust_color_lightness, \
    darken_color, hex_to_rgb, rgb_to_hex, getColourBasedOnRGB, darken_hex_color, generate_linear_gradient
from .tb_collapsingWidgets import CollapsibleBox
from .tb_buttons import MiniButton, LockButton, AnimLayerTabButton, GraphToolbarButton, HelpButton, SimpleIconButton, \
    ToolButton, HotkeyToolButton, ToolboxButton, ReturnButton, ToolbarButton
from .tb_baseDialog import BaseDialog
from .tb_boldGroupBox import QBoldGroupBox
from .tb_buttonPopup import ButtonPopup
from .tb_comboBoxes import ComboBox, comboBoxWidget
from .tb_SlidingCheckBox import AnimatedCheckBox
from .tb_customDialog import CustomDialog
from .tb_fileWidget import filePathWidget
from .tb_hotkeyWidget import hotKeyWidget, HotkeyPopup, hotkeyLineEdit
from .tb_inputWidget import TextInputWidget, ChannelInputWidget, IntInputWidget, ObjectInputWidget
from .tb_intfield import intFieldWidget
from .tb_labels import subHeader, infoLabel, QBoldLabel, DropShadowLabel
from .tb_licenseWin import LicenseWin, OfflineActivateInputWidget
from .tb_lineEdit import ObjectSelectLineEdit, ObjectSelectLineEditNoLabel, \
    ObjectSelectLineEditEnforced, ChannelSelectLineEdit, ChannelSelectLineEditEnforced
from .tb_markingMenuHandler import markingMenuKeypressHandler
from .tb_optionWidgets import optionWidget, optionVarWidget, optionVarBoolWidget, optionVarStringListWidget, \
    optionVarListWidget
from .tb_pickListDialog import PickListDialog
from .tb_pickObjectDialog import PickObjectDialog
from .tb_pickwalkWidgets import PickwalkQueryWidget
from .tb_promptWidget import promptWidget, InfoPromptWidget, raiseOk, raiseError
from .tb_qTreeView import QTreeSingleViewWidget
from .tb_radioGroups import radioGroupWidget, radioGroupVertical, radioGroupVertical, RadioGroup
from .tb_textInputDialog import TextInputDialog, TextOptionInputDialog
from .tb_toolboxWidgets import ToolboxColourButton, ToolboxDoubleButton, ToolboDivider
from .tb_toolTip import CustomToolTip
from .tb_updateWin import UpdateWin
from .tb_viewportDialog import ViewportDialog
from .tb_warningDialog import WarningDialog
from .tbUI_pyslider import StyledButtonDemo, map_value_to_range, Slider, SliderPopup, sliderButton, SliderFloatField
from .tbUI_pyslider import SliderToolbarWidget, PopupSlider, PopupSliderDialog, PopupSliderWidget, PopupSliderButton, \
    SliderButtonPopupMenu
from .tbUI_toolbar import DockableUI
from .tb_overlay import OverlayContents, Overlay
