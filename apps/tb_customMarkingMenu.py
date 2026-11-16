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

# maya.utils.loadStringResourcesForModule(__name__)

__author__ = 'tom.bailey'
ctrlMod = 4  # control button pressed during menu
ignoredEvents = [QEvent.Type.NonClientAreaMouseMove, QEvent.Type.UpdateRequest, QEvent.Type.HoverMove,
                 QEvent.Type.Paint]
# these events will trigger the dag menu override to set the post menu command on modelEditor popup menus
refreshEvents = [QEvent.Type.ChildPolished, QEvent.Type.HoverEnter, QEvent.Type.WindowActivate]
menuModes = {True: 'contextToolsMM', False: 'buildObjectMenuItemsNow'}


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('view'))
        self.commandList = list()

        return self.commandList

    def assignHotkeys(self):
        return


class CustomMarkingMenu(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'CustomMarkingMenu'
    hotkeyClass = hotkeys()
    funcs = Functions()
    start_time = 0
    last_time = 0
    mainWindowFilter = None
    customRightClickMenuOption = 'tbCustomRightClickMenu'
    attributeMethods = ['toolName', 'toolName2'] # list of main tools that have right click menus, in the order they should be drawn

    def __new__(cls):
        if CustomMarkingMenu.__instance is None:
            CustomMarkingMenu.__instance = object.__new__(cls)

        CustomMarkingMenu.__instance.val = cls.toolName
        return CustomMarkingMenu.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def optionUI(self):
        super(CustomMarkingMenu, self).optionUI()

        customRightClickHeader = subHeader('Menu toggling')
        customRightClickEnableInfo = infoLabel('WIP')
        customRightClickEnableOptionWidget = optionVarBoolWidget('Enable right click menu',
                                                                 self.customRightClickMenuOption)
        self.layout.addWidget(customRightClickHeader)
        self.layout.addWidget(customRightClickEnableInfo)
        self.layout.addWidget(customRightClickEnableOptionWidget)
        self.layout.addStretch()
        return self.optionWidget

    def showUI(self):
        return None

    def drawMenuBar(self, parentMenu):
        return None

    def deferredLoad(self):
        print('================================')
        print(' Adding custom right click menu')
        print('================================')
        self.installMainFilter(install=True)

    def removeMainFilter(self):
        if self.mainWindowFilter:
            getMainWindow().removeEventFilter(self.mainWindowFilter)

    def installMainFilter(self, install=True):
        main_widget = getMainWindow()

        # event filter is a global variable or maya garbage collects it

        self.removeMainFilter()
        self.mainWindowFilter = RightClickFilter()
        self.mainWindowFilter.cls = self

        # install the new one
        if install:
            main_widget.installEventFilter(self.mainWindowFilter)

        # manually set the dag menu override once, the filter will run when the ui changes so won't install anything at first
        self.overrideDefaultRightClickMenu(mode=install)

    def hasModelEd(self, panelName):
        # check the model panel has a model editor
        modelEd = cmds.modelEditor(panelName, query=True, control=True)
        if modelEd != 'NONE':
            return modelEd
        else:
            return None

    def list_all_modelEditors(self):
        return [x for x in [[self.hasModelEd(panelName), panelName] for panelName in cmds.getPanel(type='modelPanel')]
                if x[0]]

    def overrideDefaultRightClickMenu(self, mode=True):
        # loop over all model panels to see which have a model editor
        for modelEd in self.list_all_modelEditors():

            # object popup menus attached to modelEditors are always named after the model panel with the suddix ObjectPop
            ObjectPopMenu = '%sObjectPop' % modelEd[1]
            ConvertPop = '%sConvertPop' % modelEd[1]
            # if the menu doesn't exists then create it
            menus = [ObjectPopMenu, ConvertPop]
            for menu in menus:
                try:

                    if not cmds.popupMenu(menu, query=True, exists=True):
                        cmds.popupMenu(menu, parent=modelEd[0])
                except:
                    cmds.warning('failing to add non existent popup menu, %s' % menu)

                # change the post menu command for the model editor popup menu to use our wrapper
                cmds.popupMenu(menu,
                               edit=True,
                               postMenuCommand={True: self.mayaMarkingMenuOverride, False: self.mayaMarkingMenuDefault}[
                                   mode],
                               postMenuCommandOnce=False)

    def getWidgetAtMouse(self):
        currentPos = QCursor().pos()
        widget = QApplication.widgetAt(currentPos)
        return widget

    def mayaMarkingMenuOverride(self, menuName, modelPanel):
        '''
        wraps the buildObjectMenuItemsNow mel command in another command which can decide on
        drawing a custom menu or not
        :param menuName:
        :param modelPanel:
        :return:
        '''
        item = None

        try:
            # set outputs to some internal string stream (stop spamming the output window with '[]'
            # sys.stderr = sys.stdout = StringIO.StringIO()

            mel.eval("%s %s " % (menuModes[cmds.getModifiers() == ctrlMod], menuName))
            widget = self.getWidgetAtMouse()
            mousePos = widget.mapFromGlobal(QCursor().pos())
            item = self.funcs.selectFromScreenApi(mousePos.x(), self.getWidgetAtMouse().height() - mousePos.y())
            # get the object under the pointer
            item = self.funcs.selectFromScreenApi(mousePos.x(), widget.height() - mousePos.y()) or cmds.ls(
                selection=True) or None
            if not item:
                return

            self.custom_menu(item[0], menuName)
            # restore the output handles
            # sys.stderr = sys.__stderr__

        except Exception as e:
            cmds.warning('dag menu override failed for item %s' % item, Exception, e)

    def mayaMarkingMenuDefault(self, menuName, modelPanel):
        '''
        maya didn't seem to like being sent a mel.eval command so after overriding the popup menu
        in a session, just change the wrapper when disabling the override
        :param menuName:
        :param modelPanel:
        :return:
        '''

        try:
            mel.eval("%s %s " % (menuModes[cmds.getModifiers() == ctrlMod], menuName))
        except Exception as e:
            cmds.warning('dag menu standard failed', e.message)

    def custom_menu(self, item, parent):
        '''
        The main function to decide what if any, custom menu items to draw
        :param item: the item under pointer, or selected item if none is under pointer
        :param parent: this gets sent from the 'createSelectMenuItems' proc in dagMenuProc.mel
        :return: returns true if a custom menu is drawn - this stops the main 'createSelectMenuItems' from drawing the rest
        of the marking menu
        '''

        custom = 0  # this will be our return value, to stop the main mel script from drawing more menuItems
        if get_option_var(self.customRightClickMenuOption, False):
            CharacterTool = self.allTools.tools['CharacterTool']
            currentCharacter, namespace = CharacterTool.getSelectedChar([item])
            characterKeys = list(CharacterTool.allCharacters.keys())

            if not currentCharacter in characterKeys:
                return

            cmds.menu(parent, edit=True, deleteAllItems=True)

            # figure out what extras to add to the menu,

            """
            Baking
            Space switching
            Pivots
            Mirroring
            set to default
            """

            # __node = pm.PyNode(item)    # pynode for our item under pointer
            #
            # # get the attribute names for all custom attributes on our node - minus the object name etc
            # user_attrs = [attr.split('.')[-1] for attr in __node.listAttr(userDefined=True)]
            #
            # # check attributes to see if we will draw a custom menu
            # for attr in user_attrs:
            #     if attr in cAttributes.attributeMethods.keys() or attr in cAttributes.toggleAttributes or attr in cAttributes.toggleAttributes_alt:
            #         if not custom: custom = 1
            #

            # # look through user attributes for matching keys in customAttributes class
            # for attr in user_attrs:
            #     if attr in cAttributes.attributeMethods.keys():
            #         # if not custom: custom = 1
            #         # run the menu command based on the attribute name from our method dictionary
            #         if isinstance(cAttributes.attributeMethods[attr], list):
            #             for method in cAttributes.attributeMethods[attr]:
            #                 method(__node, cAttributes)
            #         else:
            #             cAttributes.attributeMethods[attr](__node, cAttributes)
            #
            # # toggleable attribute redirector
            # visAttrs = [[attr, 'control'] for attr in cAttributes.toggleAttributes if __node.hasAttr(attr)]
            # # need a better way of determining this
            # visAttrs.extend([[attr, 'object'] for attr in cAttributes.toggleAttributes_alt if __node.hasAttr(attr)])
            # if visAttrs:
            #     custom = 1
            #     pm.menuItem(label=str("- Visibility -"), boldFont=True, enable=False)
            #     for attr in visAttrs:
            #         cAttributes.toggleMethod(__node, cAttributes, attr[0], attr[1])


class RightClickFilter(QObject):
    cls = None

    # event filter which fires on ui changes
    def eventFilter(self, obj, event):
        # always return false for all eventualitis

        # useful for debugging
        if event.type() not in ignoredEvents:
            return False

        try:
            # menu update
            if event.type() in refreshEvents:
                try:
                    self.cls.overrideDefaultRightClickMenu()
                except Exception as e:
                    cmds.error(Exception, e.message)
                return False

        except Exception as e:
            cmds.warning('dag menu install filter failed', e)
        return False
