import os

import maya.OpenMayaUI as omui
import re
import maya.mel as mel
import maya.cmds as cmds
import math
from functools import partial
import maya.api.OpenMaya as om2

qtVersion = cmds.about(qtVersion=True)
QTVERSION = int(qtVersion.split('.')[0])
if QTVERSION < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance
    from shiboken import getCppPointer

elif QTVERSION < 6:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance
    from shiboken2 import getCppPointer
else:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtGui import QPainter
    # from pyside2uic import *
    from shiboken6 import wrapInstance
    from shiboken6 import getCppPointer

    # pyside version hacks
    QRegExp = QRegularExpression
    QRegExpValidator = QRegularExpressionValidator

import maya.OpenMayaUI as omUI

def getMainWindow():
    if not cmds.about(batch=True):
        return wrapInstance(int(omUI.MQtUtil.mainWindow()), QWidget)
    return None


def toQtObject(maya_name):
    """
    Convert a Maya UI control to its corresponding Qt object.

    Parameters:
    - maya_name (str): The name of the Maya UI control.

    Returns:
    - QWidget or QWindow: The corresponding Qt object.
    """
    # Get the pointer to the Maya UI control
    ptr = int(cmds.control(maya_name, q=True, fullPathName=True))
    if ptr:
        return wrapInstance(ptr, QWidget) or wrapInstance(ptr, QWindow)
    return None


def stripNamespace(obj):
    if ':' not in obj:
        return obj
    return obj.split(':')[-1]

margin = 2
MOD_MASK = (Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META)
scriptLocation = os.path.dirname(os.path.realpath(__file__))
IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Icons'))
helpPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Help'))
baseIconFile = 'checkBox.png'
import traceback
from colorsys import rgb_to_hls, hls_to_rgb
from tb_mainUtility import *
import getStyleSheet as getqss
from .tb_screens import getScreenCenter
from .tb_UIScale import dpiScale, dpiFontScale, defaultFont, boldFont, semiBoldFont, adjust_color_lightness, \
    darken_color, hex_to_rgb, rgb_to_hex, getColourBasedOnRGB, darken_hex_color, generate_linear_gradient
from .tb_labels import Header, subHeader, infoLabel, QBoldLabel, DropShadowLabel
from .tb_collapsingWidgets import CollapsibleBox
from .tb_promptWidget import promptWidget, InfoPromptWidget, raiseOk, raiseError
from .tb_buttons import ToolTipPushButton, MiniButton, LockButton, AnimLayerTabButton, GraphToolbarButton, HelpButton, SimpleIconButton, \
    ToolButton, HotkeyToolButton, ToolboxButton, ReturnButton, ToolbarButton
from .tb_baseDialog import BaseDialog
from .tb_boldGroupBox import QBoldGroupBox
from .tb_buttonPopup import ButtonPopup
from .tb_comboBoxes import ComboBox, comboBoxWidget
from .tb_SlidingCheckBox import AnimatedCheckBox
from .tb_customDialog import CustomDialog
from .tb_fileWidget import filePathWidget
from .tb_hotkeyWidget import hotKeyWidget, HotkeyPopup, hotkeyLineEdit
from .tb_intfield import intFieldWidget
from .tb_inputWidget import TextInputWidget, ChannelInputWidget, IntInputWidget, ObjectInputWidget
from .tb_licenseWin import LicenseWin, OfflineActivateInputWidget
from .tb_lineEdit import ObjectSelectLineEdit, ObjectSelectLineEditNoLabel, \
    ObjectSelectLineEditEnforced, ChannelSelectLineEdit, ChannelSelectLineEditEnforced
from .tb_markingMenuHandler import getMarkingMenuFilter, MarkingMenuKeypressHandlerPyside2, MarkingMenuKeypressHandler
from .tb_optionWidgets import optionWidget, optionVarWidget, optionVarBoolWidget, optionVarStringListWidget, \
    optionVarListWidget
from .tb_pickListDialog import PickListDialog
from .tb_pickObjectDialog import PickObjectDialog
from .tb_pickwalkWidgets import PickwalkQueryWidget, PickObjectWidget, PickwalkDestinationWidget, StandardPickButton, \
    PickObjectLineEdit, PickwalkLabelledDoubleSpinBox, PickwalkLabelledLineEdit, MiniDestinationWidget
from .tb_qTreeView import QTreeSingleViewWidget
from .tb_radioGroups import radioGroupWidget, radioGroupVertical, radioGroupVertical, RadioGroup
from .tb_textInputDialog import TextInputDialog, TextOptionInputDialog
from .tb_toolboxWidgets import ToolboxColourButton, ToolboxDoubleButton, ToolboDivider
from .tb_toolTip import CustomToolTip
# from .tb_updateWin import UpdateWin
from .tb_viewportDialog import ViewportDialog
from .tb_warningDialog import WarningDialog
from .tbUI_pyslider import StyledButtonDemo, map_value_to_range, Slider, SliderPopup, sliderButton, SliderFloatField
from .tbUI_pyslider import SliderToolbarWidget, PopupSlider, PopupSliderDialog, PopupSliderWidget, PopupSliderButton, \
    SliderButtonPopupMenu
from .tb_viewportSlider import ViewportSliderWidget
from .tbUI_toolbar import DockableUI
from .tb_overlay import TranslucentWidget, OverlayContents, Overlay
from .tb_pluginDialog import PluginExtractor
from .tb_collapsibleContainer import CollapsingContainerBackground, CollpasingContainerHeader, CollapsingContainer
from .tb_optionsWindow import MainOptionWindow
