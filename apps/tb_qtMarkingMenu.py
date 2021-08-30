import inspect
import math
import maya.OpenMaya as api
import pymel.core as pm
import maya.OpenMayaUI as omui
import getStyleSheet as getqss
import os
import maya.cmds as cmds

qtVersion = pm.about(qtVersion=True)

if qtVersion.split('.')[0] < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from PySide.QtWidgets import *

    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from shiboken2 import wrapInstance

filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "\\"  # script directory

iconPath2 = filepath.replace('apps', 'Icons') + 'icecream.png'


class EventFilterManager(object):
    __instance = None
    mainWindow = wrapInstance(int(omui.MQtUtil.findControl(pm.melGlobals['gMainWindow'])), QWidget)
    uiUpdateFilter = None
    markingMenuFilter = None
    markingMenuClass = None

    def __new__(cls):
        if EventFilterManager.__instance is None:
            EventFilterManager.__instance = object.__new__(cls)
            EventFilterManager.markingMenuFilter = QtMarkingMenu()
            EventFilterManager.markingMenuClass = animated_scene()

        EventFilterManager.__instance.val = 'EventFilterManager'
        return EventFilterManager.__instance

    def installMainFilter(self):
        self.uiUpdateFilter = UiUpdateFilter()

        # firstly try to remove the existing filter
        self.removeMainFilter()
        # install the new one
        self.mainWindow.installEventFilter(self.uiUpdateFilter)
        self.uiUpdateFilter.forceAddition()

    def removeMainFilter(self):
        try:
            self.mainWindow.removeEventFilter(self.uiUpdateFilter)
        except Exception as e:
            pm.warning(e.message)

    def isPanelWidget(self, widget):
        return len(widget.children()) == 0 and \
               widget.__class__ == QWidget and \
               (widget.parent().__class__ == QStackedWidget or widget.parent().__class__ == QObject) \
               and not widget.isHidden()

    def recursive_widget_lookup(self, widget, filter, remove=False):
        matches = [x for x in widget.children() if self.isPanelWidget(x)]
        try:
            if remove:
                matches[0].removeEventFilter(filter)
            else:
                matches[0].installEventFilter(filter)
            # print "installing event filter,", filter, "on", matches[0], matches[0].__class__
        except Exception as e:
            print e
            for child in widget.children():
                self.recursive_widget_lookup(child, filter)

    def addFilterToModelPanels(self, filter):
        for p in pm.lsUI(editors=True):
            if pm.objectTypeUI(p) == 'modelEditor':
                self.recursive_widget_lookup(self.getQObjectFromName(p), filter)

    def removeFilterToModelPanels(self, filter):
        for p in pm.lsUI(editors=True):
            if pm.objectTypeUI(p) == 'modelEditor':
                self.recursive_widget_lookup(self.getQObjectFromName(p), filter, remove=True)

    def getQObjectFromName(self, name):
        ptr = omui.MQtUtil.findControl(name)
        if ptr is None:
            ptr = omui.MQtUtil.findLayout(name)
            if ptr is None:
                ptr = omui.MQtUtil.findMenuItem(name)
        if ptr is not None:
            return wrapInstance(int(ptr), QObject)

    def addMarkingMenuFilters(self):
        self.addFilterToModelPanels(self.markingMenuFilter)

    def removeMarkingMenuFilters(self):
        self.removeFilterToModelPanels(self.markingMenuFilter)


class UiUpdateFilter(QObject):
    def eventFilter(self, widget, event):
        try:
            if event.type() in [QEvent.Type.ChildPolished, QEvent.Type.WindowActivate]:
                try:
                    EventFilterManager().addMarkingMenuFilters()
                except Exception as e:
                    pm.error(Exception, e.message)
                return False

        except Exception as e:
            pm.warning('UiUpdateFilter', e.message)
        return False

    def forceAddition(self):
        print ('add custom menus')


class QtMarkingMenu(QObject):
    '''A simple event filter to catch MouseMove events'''

    menuWidget = None

    def __init__(self):
        print "here?"
        super(QtMarkingMenu, self).__init__()

        # auto build methods for ik/spaces etc
        #  automatically added menu items based on object attributes

        # commands for execution by ight click menu

        # the right click menu object itself

        # object to hold all menu data
        self.keyMod = None
        self.node = None
        self.isRaised = False

    def eventFilter(self, obj, event):
        self.keyMod = QApplication.keyboardModifiers()
        # print event.type(), obj, self.keyMod
        if event.type() == QEvent.MouseButtonPress:
            print 'press'
        try:
            # is the menu raised?
            '''
            if self.isRaised:
                if event.type() == QEvent.MouseButtonRelease and not self.isRightClickHeld():
                    self.isRaised = False

                    print ('close menu')
                    menu_command, menu_data = EventFilterManager().markingMenuClass.delayed_hide()

                    print "received menu command::", menu_command

                    if menu_command in self.right_click_commands.keys():
                        self.right_click_commands[menu_command]().run(node=self.node, data=menu_data)

                    return True
                if event.type() == QEvent.Type.MouseMove:
                    # print ("mouse update", QCursor.pos())
                    EventFilterManager().markingMenuClass.mouseMove(QCursor.pos())
                    return True
                return True
            '''
            if self.isRightClick(event):
                print ('isRightClick')
                from pluginLookup import ClassFinder
                tbtoolCLS = ClassFinder()

                selection = cmds.ls(sl=True)
                if not selection:
                    selection = selectFromScreenApi(event.pos().x(), obj.height() - event.pos().y())
                if not selection:
                    return False
                menuDataDict = tbtoolCLS.collectQtMarkingMenuData(selection)

                self.isRaised = True
                EventFilterManager().markingMenuClass.rebuild(menuData=menuDataDict['IkFkTools'])
                EventFilterManager().markingMenuClass.reveal()
                print ('open menu')
                return True
            if self.isMiddleClick(event):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                _clicked_node = "nothing"
                _clicked_node = selectFromScreenApi(event.pos().x(), obj.height() - event.pos().y())
                print _clicked_node
                self.double_click()
                return True
            else:
                return False
        except Exception as e:
            print e
            return False

    def open_menu(self, node=[]):
        print "node", node
        return False

    def double_click(self):
        print "double clicked"

    def isRightClickHeld(self):
        return qApp.mouseButtons() & Qt.RightButton

    def isRightClick(self, event):
        return event.type() == QEvent.MouseButtonPress and self.isRightClickHeld()

    def isMiddleClick(self, event):
        return event.type() == QEvent.MouseButtonPress and qApp.mouseButtons() & Qt.MiddleButton

    def isMiddleClick(self, event):
        return event.type() == QEvent.MouseButtonPress and qApp.mouseButtons() & Qt.MiddleButton


def selectFromScreenApi(x, y, x_rect=None, y_rect=None):
    # get current selection
    sel = api.MSelectionList()
    api.MGlobal.getActiveSelectionList(sel)

    # api.MGlobal.selectionMethod()
    # select from screen
    args = [x, y]
    if x_rect and y_rect:
        api.MGlobal.selectFromScreen(x, y, x_rect, y_rect, api.MGlobal.kReplaceList)
    else:
        api.MGlobal.selectFromScreen(x, y, api.MGlobal.kReplaceList, 0)
    objects = api.MSelectionList()
    api.MGlobal.getActiveSelectionList(objects)

    # restore selection
    api.MGlobal.setActiveSelectionList(sel, api.MGlobal.kReplaceList)

    # return the objects as strings
    fromScreen = []
    objects.getSelectionStrings(fromScreen)
    return fromScreen


def getWidgetAtMouse():
    currentPos = QCursor().pos()
    widget = qApp.widgetAt(currentPos)
    return widget


class testMenuData(object):
    """
    Collaects menu data from all tool classes based on menu requirements
    """

    def __init__(self):
        self.menuItemList = []
        self.menu_data = MarkingMenuData()
        self.add_items()

    def add_items(self):
        # add individual menu items
        self.menuItemList.append(MarkingMenuItem(label="boring", command="testMethod", textColour='#C72ABC'))
        self.menuItemList.append(MarkingMenuItem(label="test", command="testMethod", textColour='#C7832A'))
        self.menuItemList.append(MarkingMenuItem(label="menu", command="testMethod", textColour='#89F5A2'))

        # add to main data object
        self.menu_data.menu_items = self.menuItemList

    def return_menu(self):
        return self.menu_data


class MarkingMenuItem(object):
    def __init__(self,
                 label=None,
                 command=None,
                 textColour=None,
                 variable_data={},
                 radial=False,
                 font=QFont("Segoe UI", 9, QFont.DemiBold),
                 radial_position=None,
                 bold=False):
        # self.available_commands = right_click_methods.get_methods()
        self.label = label
        self.radial = radial
        self.radial_position = radial_position
        self.command = command
        '''
        if command in self.available_commands.keys():
            self.__dict__['command'] = command
        else:
            self.__dict__['command'] = None
        '''
        self.variable_data = variable_data
        self.textColour = textColour
        self.font = font


class MarkingMenuData(object):
    """
    Holds the data for the marking menu
    """

    def __init__(self):
        self.menu_items = []
        self.central_image = None

    # add a list of menu items to this menu data, useful for auto generated menu items
    def add_items(self, menuItems=[]):
        if menuItems:
            print "__ appending menu items"
            for item in menuItems:
                self.menu_items.append(item)


class Communicate(QObject):
    transition_in = Signal()
    transition_out = Signal()
    ui_hide = Signal()


class _textItem(QGraphicsTextItem):
    def __init__(self, text, background, parent=None):
        super(_textItem, self).__init__(parent)
        self.setPlainText(text)
        self.background = background
        self.setDefaultTextColor(background)

    def paint(self, painter, option, widget):
        # paint the background
        # painter.fillRect(option.rect, QtGui.QColor(self.background))

        # paint the normal TextItem with the default 'paint' method
        super(_textItem, self).paint(painter, option, widget)


def createItem(minimum, preferred, maximum, name):
    w = QGraphicsProxyWidget()

    w.setWidget(QPushButton(name))
    w.setMinimumSize(QSizeF(20, 20))
    w.setPreferredSize(QSizeF(20, 20))
    w.setMaximumSize(QSizeF(20, 20))
    w.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    return w


class _pMap(QGraphicsPixmapItem):
    def __init__(self, pix, parent, holder):
        super(_pMap, self).__init__(pix)
        self.parent = parent
        self.holder = holder
        self.label = holder.label
        self.textColour = holder.textColour
        self.font = holder.font
        self.setAcceptHoverEvents(True)
        self.hover_brush = QColor(82, 133, 166)
        self.no_hover_brush = QColor(82, 82, 82)
        self.borderPen = QColor(50, 50, 50)
        self.current_brush = self.no_hover_brush
        self.drawWidth = 100
        self.drawHeight = 18
        self.xOffset = 0
        self.yOffset = 0
        # font = QtGui.QFont('Comic Sans MS')
        self.dot1 = _textItem(self.label, self.textColour, self)
        self.dot1.setFont(self.font)
        self.dot1.setPos(-0, -0)
        self.drawWidth = self.dot1.boundingRect().width()
        print self.dot1.boundingRect().width()
        print self.boundingRect().width()


    def paint(self, painter, option, widget):
        '''
        try:
            super(_pMap,self).paint(painter, option, widget)
        except Exception as e:
            print e
        '''
        painter.setBrush(self.current_brush)
        painter.setPen(self.borderPen)
        # painter.setPen(QtGui.Qt.NoPen)
        painter.drawRoundedRect(self.xOffset, self.yOffset, 200, self.drawHeight, 4, 4)
        self.setOpacity(0.75)

        pass

    def set_hover(self):
        self.current_brush = self.hover_brush
        self.borderPen = QColor(255, 165, 0)
        self.update()

    def set_no_hover(self):
        self.current_brush = self.no_hover_brush
        self.borderPen = QColor(50, 50, 50)
        self.update()


class markingMenu_filter(QObject):
    '''A simple event filter to catch MouseMove events'''

    def eventFilter(self, obj, event):
        print event.type()


class centre_image(QObject):
    def __init__(self, image=iconPath2, parent=None, scale=64):
        super(centre_image, self).__init__()
        self.parent = parent

        self.image = QPixmap(image).scaled(scale, scale, Qt.KeepAspectRatio,
                                           Qt.SmoothTransformation)
        self.pixMap = QGraphicsPixmapItem(self.image)

        self.pixMap.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    def get_pos(self):
        return self.pixmap_item.pos()

    def get_int_pos(self):
        return QPoint(int(self.pixmap_item.pos().x()), int(self.pixmap_item.pos().y()))


class picButton(QObject):
    def __init__(self, pix, menuItem, parent):
        super(picButton, self).__init__()

        self.menuItem = menuItem
        self.parent = parent
        self.label = menuItem.label
        self.font = menuItem.font
        self.textColour = menuItem.textColour
        self.font = menuItem.font
        self.pixmap_item = _pMap(pix, parent, self)
        self.pixmap_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        #self.pixmap_item.setScale(4)
        menu_filter = markingMenu_filter()
        self.installEventFilter(menu_filter)

    def paint(self, painter, option, widget):
        '''
        try:
            super(_pMap,self).paint(painter, option, widget)
        except Exception as e:
            print e
        '''
        painter.setBrush(QColor(82, 133, 166))

        painter.setPen(QColor(82, 133, 166))

        # painter.setPen(QtGui.Qt.NoPen)
        painter.drawRoundedRect(0, 0, 200, 20, 4, 4)
        self.setOpacity(0.75)

        pass

    def set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    def get_pos(self):
        return self.pixmap_item.pos()

    def get_int_pos(self):
        return QPoint(int(self.pixmap_item.pos().x()) + self.pixmap_item.xOffset,
                      int(self.pixmap_item.pos().y() + self.pixmap_item.yOffset))

    def inBoundingBox(self, pos):
        xPos = pos.x() - self.get_int_pos().x() - 350
        yPos = pos.y() - self.get_int_pos().y() - 350
        pos = QPoint(xPos, yPos)
        bb = QRect(0, 0, self.pixmap_item.drawWidth, self.pixmap_item.drawHeight + 1)
        return bb.contains(pos)

    def removeItem(self):
        self.deleteLater()

    def mousePressEvent(self, event):
        print ('picButton mousePressEvent', self, event)

    def mouseReleaseEvent(self, pos):
        if self.inBoundingBox(pos):
            print ('picButton mouseReleaseEvent', self.menuItem.label)
            try:
                self.menuItem.command()
            except:
                cmds.warning(self.menuItem.command, 'failed')

    def mouseMoveEvent(self, pos):
        if self.inBoundingBox(pos):
            self.pixmap_item.set_hover()
        else:
            self.pixmap_item.set_no_hover()

    pos = Property(QPointF, get_pos, set_pos)


class radial_info(object):
    def __init__(self, item=None, angle=[0.0]):
        self.item = item
        self.angle = angle

    def get_delta(self, in_angle=0.0):
        return min(self.angle, key=lambda x: abs(x - in_angle))


class animated_scene(QWidget):
    def __init__(self, itemList=[]):
        super(animated_scene, self).__init__()

        self.setStyleSheet("""QGraphicsView { border-style: none; \n
                           background: transparent }; \n
                           QGraphicsItem { border-style: none; \n
                           border-radius: 40px; }""")

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.c = Communicate()
        self.state = False
        # position over mouse
        self._wdith = 700
        self._height = 700
        self.resize(self._wdith, self._height)
        self.move_to_mouse()

        # radial position dict
        self.radial_positions = dict(n=0, e=90, s=180, w=-90, ne=60, se=120, sw=240, nw=300)
        self.available_positions = self.radial_positions.keys()
        self.taken_positions = []

        # on off timers
        self.timer = QTimer()
        self.out_timer = QTimer()

        # graphics scene object
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-350, -350, 700, 700)

        # graphics view
        self.view = QGraphicsView(self.scene, self)
        self.view.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # remove the border
        self.setWindowFlags(Qt.FramelessWindowHint)
        # set the background to be transparent
        palette = QPalette()
        palette.setColor(QPalette.Base, Qt.transparent)
        self.setPalette(palette)

        # central image
        central_image = iconPath2
        # centre_image = centre_image.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.centre_pix = centre_image(image=central_image, scale=24)
        self.centre_pix.pixMap.setOffset(-self.centre_pix.image.width() / 2, -self.centre_pix.image.height() / 2)
        self.centre_pix.pixMap.setZValue(100)
        self.scene.addItem(self.centre_pix.pixMap)

        # add the buttons to the layout
        self.itemList = itemList
        self.radial_items = []
        self.vertical_items = []
        self.total = len(self.itemList)
        self.radius = 120
        self.closest_item = None
        self.closest_index = None
        self.init_pos = None

        # create the main states
        self.rootState = QState()
        self.out_state = QState(self.rootState)
        self.centeredState = QState(self.rootState)

        self.states = QStateMachine()
        self.states.setAnimated(False)
        self.states.addState(self.rootState)
        self.states.setInitialState(self.rootState)
        self.rootState.setInitialState(self.centeredState)

        self.group = QParallelAnimationGroup()

        # animation transition objects
        self.trans = self.rootState.addTransition(self.c.transition_out, self.out_state)
        self.trans.addAnimation(self.group)

        # self.trans = self.rootState.addTransition(self.c.transition_in, self.centeredState)
        # self.trans.addAnimation(self.group)

        # self.reveal()

    def rebuild(self, menuData=MarkingMenuData()):
        # clear the menu
        self.menuData = menuData
        self.all_items = list()
        self.specific_radial_items = []
        self.radial_items = []
        self.vertical_items = []
        central_image = iconPath2
        kineticPix = QPixmap(central_image).scaled(400, 100, Qt.IgnoreAspectRatio,
                                                   Qt.SmoothTransformation)

        # create all button objects
        for i, menu_item in enumerate(self.menuData):

            item = picButton(kineticPix, menu_item, self)
            #item.pixmap_item.setOffset(-kineticPix.width() / 2, -kineticPix.height() / 2)
            item.pixmap_item.setZValue(i)
            item.index = i
            self.all_items.append(item)
            if menu_item.radial:
                if menu_item.radial_position in self.radial_positions.keys():
                    print "ooo look its in the place"
                self.radial_items.append(item)

            else:
                self.vertical_items.append(item)
            self.scene.addItem(item.pixmap_item)

        if len(self.radial_items):
            # animation state Values.
            arc = 360.0 / len(self.radial_items)
            # out state UI positions
            for i, item in enumerate(self.radial_items):
                angle = self.radial_positions.get(self.menuData[item.index].radial_position, 0.0)
                self.taken_positions.append(radial_info(item=item, angle=[angle, angle + 360, angle - 360]))
                # print "angle", angle
                self.out_state.assignProperty(item, 'pos',
                                              QPointF(math.sin((math.radians(angle))) * self.radius,
                                                      -math.cos((math.radians(angle))) * self.radius * 0.5))

                self.out_state.assignProperty(item, 'opacity', 1.0)
                self.out_state.assignProperty(self, 'windowOpacity', 1.0)
                #self.centeredState.assignProperty(item, 'pos', QPointF(0, 0))
                #self.centeredState.assignProperty(item, 'opacity', 0.0)
                #self.centeredState.assignProperty(self, 'windowOpacity', 0.0)

            for i, item in enumerate(self.radial_items):
                anim = QPropertyAnimation(item, 'pos')
                # anim.setDuration(10 + i * 25)
                anim.setDuration(0)
                # anim.setEasingCurve(QEasingCurve.OutBack)
                self.group.addAnimation(anim)

        if self.vertical_items:
            # out state UI positions
            for i, item in enumerate(self.vertical_items):
                offset = 50
                if len(self.radial_items) > 0:
                    offset = self.radius
                self.out_state.assignProperty(item, 'pos', QPointF(0.0, offset + 25 + (i * 19)))
                self.out_state.assignProperty(item, 'opacity', 1.0)
                self.out_state.assignProperty(self, 'windowOpacity', 1.0)
                #self.centeredState.assignProperty(item, 'pos', QPointF(0, 0))
                #self.centeredState.assignProperty(item, 'opacity', 0.0)
                #self.centeredState.assignProperty(self, 'windowOpacity', 0.0)

            for i, item in enumerate(self.vertical_items):
                anim = QPropertyAnimation(item, 'pos')
                # anim.setDuration(50 + i * 50)
                anim.setDuration(0)
                anim.setEasingCurve(QEasingCurve.OutExpo)
                self.group.addAnimation(anim)

        anim = QPropertyAnimation(self, 'opacity')
        anim.setDuration(0)
        # anim.setEasingCurve(QEasingCurve.OutExpo)
        #self.group.addAnimation(anim)

        #self.timer.start(0)
        #self.timer.setSingleShot(True)

        # activate the state machine
        self.states.start()
        cmds.refresh()

    def button_triggered(self, *args):
        # print "start", args
        self.delayed_hide()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_1:
            self.c.transition_out.emit()
            print "1"
        elif e.key() == Qt.Key_2:
            self.delayed_hide()
            print "2"
        elif e.key() == Qt.Key_3:
            print "3"
            self.close()

    def hide(self):
        self.close()
        self.state = False
        self.releaseMouse()

    def delayed_hide(self):
        print ('delayed_hide')
        # print self.itemList[self.closest_index].label
        self.c.transition_in.emit()
        self.timer = QTimer()
        QCoreApplication.processEvents()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.timer.start(10)
        '''
        if self.closest_index >= 0:
            command = self.menuData.menu_items[self.closest_index].command
            data = None
            if self.menuData.menu_items[self.closest_index].variable_data:
                data = self.menuData.menu_items[self.closest_index].variable_data
            return command, data

        else:
            return None, None
        '''

    def reveal(self):
        self.grabMouse()
        self.state = True
        self.move_to_mouse()
        self.init_pos = QCursor.pos()
        self.timer.stop()
        # self.trans = self.rootState.addTransition(self.c.transition_out, self.out_state)
        # self.trans.addAnimation(self.group)
        self.c.transition_out.emit()

        self.show()
        self.raise_()

    def move_to_mouse(self):
        self.move(QCursor.pos().x() - 0.5 * self._wdith, QCursor.pos().y() - 0.5 * self._height)

    def mouseMove(self, pos):
        # print "menu received mouse update"
        self.cursor_pos = pos
        # print pos
        self.get_closest_widget()

    def get_closest_widget(self):
        distance = 10000
        delta = 360

        if self.dist(self.init_pos, QCursor.pos()) > 500:
            current_angle = self.get_angle(self.init_pos, QCursor.pos())
            # print current_angle
            for i, item in enumerate(self.all_items):
                current_distance = self.distance(item.get_int_pos(), self.view.mapFromGlobal(QCursor.pos()))
                if current_distance < distance:
                    distance = current_distance
                    closest_item = item
                    closest_index = i
            if closest_item not in self.vertical_items:
                for index, position in enumerate(self.taken_positions):
                    # print position.item, "delta to ", position.get_delta(in_angle=current_angle)
                    current_delta = abs(position.get_delta(in_angle=current_angle) - current_angle)
                    # print index, delta, current_delta
                    if current_delta < delta:
                        delta = current_delta
                        closest_item = position.item.label
                        closest_index = index
                print "radial section", closest_item

            if self.closest_item is not closest_item:
                self.closest_item = closest_item
                self.closest_index = closest_index
                print "closest item", self.closest_item, self.closest_index, current_distance
        else:
            self.closest_item = -1
            self.closest_index = -1
        # self.highlight_item()

    def highlight_item(self):
        # print self.closest_item, self.closest_index
        for i, item in enumerate(self.all_items):
            item.pixmap_item.set_no_hover()
        if self.closest_index >= 0:
            self.all_items[self.closest_index].pixmap_item.set_hover()

    def get_angle(self, point_a, point_b):
        x = point_a.x() - point_b.x()
        y = point_a.y() - point_b.y()
        return math.degrees(math.atan2(-x, y))

    def dist(self, point_a, point_b):
        distance = math.pow(point_a.x() - (point_b.x()), 2) + math.pow(point_a.y() - (point_b.y()), 2)
        return distance

    def distance(self, point_a, point_b):
        # print "item", point_a.x() ,  point_a.y(), "mouse", (point_b.x() - 350 ) , (point_b.y() - 350)
        distance = math.sqrt(
            math.pow(point_a.x() - (point_b.x() - 350), 2) + math.pow(point_a.y() - (point_b.y() - 350), 2))
        return distance

    def paintEvent(self, e):
        # print "paint", self, e
        pass

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        # print pos
        self.get_closest_widget()
        for item in self.all_items:
            item.mouseMoveEvent(self.view.mapFromGlobal(QCursor.pos()))

    def mouseReleaseEvent(self, event):
        for item in self.all_items:
            item.mouseReleaseEvent(self.view.mapFromGlobal(QCursor.pos()))
        if not qApp.mouseButtons() & Qt.RightButton:
            self.releaseMouse()
            self.delayed_hide()

    def mousePressEvent(self, event):
        for item in self.all_items:
            item.mousePressEvent(event)
