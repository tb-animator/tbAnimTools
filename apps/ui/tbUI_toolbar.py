import sys

import pymel.core as pm

toolbarName = 'WorkspaceControl'
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
from shiboken2 import getCppPointer

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import apps.tb_UI as tbui
sheet = """
QTabBar::tab {
    background-color: transparent;
    color: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}
QTabBar::tab:selected {
    background-color: transparent;
}
"""

def getWorkspaceControlWidget(workspace_control):
    """
    Returns the QWidget of a workspaceControl by its name
    """
    control_widget_ptr = omui.MQtUtil.findControl(workspace_control)
    control_widget = wrapInstance(long(control_widget_ptr), QWidget)
    return control_widget

class WorkspaceControl(object):

    def __init__(self, name):
        self.name = name
        self.widget = None

    def create(self, label, widget, ui_script=None):
        print('create', ui_script)
        workspace = cmds.workspaceControl(self.name, label=label,
                              #dockToPanel=['modelPanel4', 'bottom', True],
                              )

        # workspace_widget  = getWorkspaceControlWidget(workspace)
        # workspace_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        #
        # # set a fixed size for the widget
        # workspace_widget.setFixedSize(200, 200)
        if ui_script:
            cmds.workspaceControl(self.name, e=True,
                                  uiScript=ui_script,
                                  heightProperty='fixed',
                                  initialHeight=40)

        self.add_widget_to_layout(widget)
        self.set_visible(True)

    def restore(self, widget):
        self.add_widget_to_layout(widget)

    def add_widget_to_layout(self, widget):
        if widget:
            self.widget = widget
            self.widget.setAttribute(Qt.WA_DontCreateNativeAncestors)

            if sys.version_info.major >= 3:
                workspace_control_ptr = int(omui.MQtUtil.findControl(self.name))
                widget_ptr = int(getCppPointer(self.widget)[0])
            else:
                workspace_control_ptr = long(omui.MQtUtil.findControl(self.name))
                widget_ptr = long(getCppPointer(self.widget)[0])

            omui.MQtUtil.addWidgetToMayaLayout(widget_ptr, workspace_control_ptr)

    def exists(self):
        return cmds.workspaceControl(self.name, q=True, exists=True)

    def is_visible(self):
        return cmds.workspaceControl(self.name, q=True, visible=True)

    def set_visible(self, visible):
        if visible:
            cmds.workspaceControl(self.name, e=True, restore=True)
        else:
            cmds.workspaceControl(self.name, e=True, visible=False)

    def set_label(self, label):
        cmds.workspaceControl(self.name, e=True, label=label)

    def is_floating(self):
        return cmds.workspaceControl(self.name, q=True, floating=True)

    def is_collapsed(self):
        return cmds.workspaceControl(self.name, q=True, collapse=True)

    def setWidth(self, value):
        cmds.workspaceControl(self.name, e=True, resizeWidth=value)

    def getOrientation(self):
        layout_object = omui.MQtUtil.findControl(self.name)
        layout_widget = wrapInstance(long(layout_object), QWidget)
        if self.is_floating:
            splitterParent = layout_widget.parent().parent().parent().parent()
            if not isinstance(splitterParent, QSplitter):
                return Qt.Orientation.Horizontal
            return splitterParent.orientation()
        return Qt.Orientation.Horizontal

class DockableUI(QDialog):

    WINDOW_TITLE = "tbToolbar"

    ui_instance = None

    @classmethod
    def display(cls):
        if cls.ui_instance:
            cls.ui_instance.show_workspace_control()
        else:
            print ('creating new workspace control')
            cls.ui_instance = cls()

    @classmethod
    def get_workspace_control_name(cls):
        return "{0}WorkspaceControl".format(toolbarName)

    @classmethod
    def get_ui_script(cls):
        module_name = cls.__module__
        if module_name == "__main__":
            module_name = cls.module_name_override

        ui_script = "from {0} import {1}\n{1}.display()".format(module_name, toolbarName)
        return ui_script

    def __init__(self):
        super(DockableUI, self).__init__()

        self.setObjectName(self.__class__.__name__)

        self.create_actions()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_workspace_control()

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
        qp.drawRoundedRect(self.rect(), 8, 8)
        qp.end()

    def create_actions(self):
        pass

    def create_widgets(self):
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn2 = QPushButton("Refresh poo")
        self.widgets = [self.refresh_btn, self.refresh_btn2]

    def create_layout(self):
        self.verticalLayout = QVBoxLayout()
        self.horizontalLayout = QHBoxLayout()

    def create_connections(self):
        pass

    def create_workspace_control(self):
        self.workspace_control_instance = WorkspaceControl(self.get_workspace_control_name())
        if self.workspace_control_instance.exists():
            self.workspace_control_instance.restore(self)
        else:
            self.workspace_control_instance.create(self.WINDOW_TITLE, self, ui_script=self.get_ui_script())
        print ('self.workspace_control_instance', self.workspace_control_instance)

        p = self.parent()
        pp = p.parent()

        self.tabWidget = pp.parent()

        self.tabWidget.setTabPosition(QTabWidget.West)
        self.tabBar = self.tabWidget.children()[1]
        # self.tabBar.setAttribute(QStyle.SH_TabBar_PreferNoArrows,True)
        # self.tabBar.setAttribute(QStyle.SH_TabBar_PreferNoArrows,True)
        print (self.tabBar)
        print (self.tabBar.children())
        # TabWidget.setVisible(True)
        # TabWidget.children()[1].setVisible(False)
        self.tabWidget.children()[1].setTabText(0, '')
        # self.tabWidget.children()[1].setTabIcon(0, QtGui.QIcon('delete.png'))

        self.tabBar.setExpanding(True)
        self.tabBar.children()[1].setFixedSize(0, 0)
        self.tabBar.children()[0].setFixedSize(0, 0)
        self.tabBar.setStyleSheet(sheet)

        print (self.tabBar.children())
        self.parent().parent().resize(200,100)

    def show_workspace_control(self):
        self.workspace_control_instance.set_visible(True)

    def save_state(self):
        """
        Save the state of the dockable window
        """
        settings = QSettings("MyCompany", "MyApp")
        settings.setValue("MyDockableWindow/geometry", self.saveGeometry())
        settings.setValue("MyDockableWindow/state", self.saveState())

    def restore_state(self):
        """
        Restore the state of the dockable window
        """
        settings = QSettings("MyCompany", "MyApp")
        geometry = settings.value("MyDockableWindow/geometry")
        state = settings.value("MyDockableWindow/state")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def showEvent(self, event):
        """
        Triggered when the dockable window is shown
        """
        self.restore_state()
        super(DockableUI, self).showEvent(event)

        p = self.parent()
        pp = p.parent()

        self.tabWidget = pp.parent()

        self.tabWidget.setTabPosition(QTabWidget.West)
        self.tabBar = self.tabWidget.children()[1]
        # self.tabBar.setAttribute(QStyle.SH_TabBar_PreferNoArrows,True)
        # self.tabBar.setAttribute(QStyle.SH_TabBar_PreferNoArrows,True)
        print (self.tabBar)
        print (self.tabBar.children())
        # TabWidget.setVisible(True)
        # TabWidget.children()[1].setVisible(False)
        self.tabWidget.children()[1].setTabText(0, '')
        self.tabWidget.children()[1].setVisible(True)
        self.tabWidget.children()[1].setTabIcon(0, QIcon(':delete.png'))
        self.tabWidget.children()[1].setTabIcon(0, QIcon('C:/AnimationWork/tbAnimTools/Icons/gpuCacheRestore.png'))
        print ('!!', self.tabWidget.children()[0].children())
        self.tabBar.setExpanding(True)
        # self.tabBar.children()[1].setFixedSize(0, 0)
        # self.tabBar.children()[0].setFixedSize(0, 0)
        self.tabBar.setStyleSheet(sheet)
        # print (self.size())
        # self.parent().resize(20,20)
        print ('is floating', self.workspace_control_instance.is_floating())
        print ('state', self.workspace_control_instance.getOrientation())
        if self.workspace_control_instance.is_floating():
            print ('is floating, resize')
            self.parent().resize(self.sizeHint().width(), 60)
            self.resize(self.sizeHint().width(), 60)
            self.parent().setMaximumHeight(60)
            self.setMaximumHeight(60)
        else:
            if self.parent().height() > self.parent().width():
                print ('side docked?')
            else:
                print ('horizontal docked')

        if 'Horizontal' in str(self.workspace_control_instance.getOrientation()):
            layout = QHBoxLayout()
            self.setLayout(layout)
            for w in self.widgets:
                print('reparenting widget horizontalLayout', w)
                #layout.addWidget(w)
        else:
            self.parent().resize(60, self.sizeHint().height())
            self.resize(60, self.sizeHint().height())
            self.parent().setMaximumWidth()

            self.workspace_control_instance.setWidth(100)
            layout = QVBoxLayout()
            self.setLayout(layout)
            for w in self.widgets:
                print('reparenting widget verticalLayout', w)
                #layout.addWidget(w)



    def closeEvent(self, event):
        """
        Triggered when the dockable window is closed
        """
        self.save_state()
        super(DockableUI, self).closeEvent(event)


if __name__ == "__main__":
    try:
        test_dialog.ui_instance = None
    except:
        pass
    workspace_control_name = DockableUI.get_workspace_control_name()
    if cmds.window(workspace_control_name, exists=True):
        cmds.deleteUI(workspace_control_name)

    DockableUI.module_name_override = "workspace_control"
    test_dialog = DockableUI()


