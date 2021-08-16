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
import maya.mel as mel
import pymel.core as pm
import webbrowser
from pluginLookup import ClassFinder


class main_menu(object):
    def __init__(self):
        self.main_menu = "tbAnimTools"
        self.updateMenuItems = []
        self.updateImageDict = {True: 'recycle_green.png', False: 'empty.png'}

    def build_menu(self):
        tbtoolsCLS = ClassFinder()
        pm.setParent(pm.melGlobals['gMainWindow'])
        if pm.menu(self.main_menu, exists=True):
            pm.deleteUI(self.main_menu)
        self.main_menu = pm.menu("tbAnimTools", label="tbAnimTools", tearOff=True)

        pm.menuItem(label="Options", command=open_options, image='hotkeySetSettings.png', parent=self.main_menu)
        # pm.menuItem(label="download updates (experimental)",command=download_updates, parent=self.main_menu)
        editorMenu = pm.menuItem(label='editors', subMenu=True, parent=self.main_menu)
        # find tools with UI, make list of tool keys?
        for index, tool in enumerate(sorted(tbtoolsCLS.tools.keys(), key=lambda x: x.lower())):
            if tbtoolsCLS.tools[tool] is not None:
                tbtoolsCLS.tools[tool].drawMenuBar(editorMenu)

        self.drawUpdateMenu()

        pm.menuItem(label="about", command=show_aboutWin, parent=self.main_menu)
        pm.menuItem(label="Discord server", command=open_discord_link, parent=self.main_menu)
        pm.menuItem(label="online help - (old)", command=open_anim_page, parent=self.main_menu)

    def drawUpdateMenu(self):
        updateMode = pm.optionVar.get('tbUpdateType', 0)

        updateMenu = pm.menuItem(label='Startup Update modes', subMenu=True, parent=self.main_menu)
        pm.radioMenuItemCollection()
        menu = pm.menuItem(label="Update To Stable Releases", radioButton=updateMode == 0,
                           command=pm.Callback(self.setUpdateMode, 0),
                           parent=updateMenu)
        self.updateMenuItems.append(menu)
        menu = pm.menuItem(label="Update To Latest", radioButton=updateMode == 1,
                           command=pm.Callback(self.setUpdateMode, 1),
                           parent=updateMenu)
        self.updateMenuItems.append(menu)
        menu = pm.menuItem(label="Update Manually", radioButton=updateMode == 2,
                           command=pm.Callback(self.setUpdateMode, 2), parent=updateMenu)
        menu = pm.menuItem(label="Check For Updates",
                           command=pm.Callback(self.downloadUpdate), parent=updateMenu)
        self.updateMenuItems.append(menu)

    def setUpdateMode(self, mode):
        print ('setUpdateMode', mode)
        pm.optionVar['tbUpdateType'] = mode
        updateMode = pm.optionVar.get('tbUpdateType', 0)
        '''
        for index, menu in enumerate(self.updateMenuItems):
            print (menu, self.updateImageDict[updateMode == index])
            pm.menuItem(menu, edit=True, radioButton=updateMode == index)
        '''

    def downloadUpdate(self):
        print ('downloadUpdate')

def make_ui():
    main_menu().build_menu()


def open_options(*args):
    import tb_options as tbo
    tbo.showOptions()


def open_discord_link(*args):
    webbrowser.open('https://discord.gg/yxfP8rVS')


def open_anim_page(*args):
    webbrowser.open('http://tb-animator.blogspot.co.uk/p/tools-documentaion.html')


def download_updates(*args):
    import updater as upd
    reload(upd)
    upd.updaterWindow().showUI()


def show_aboutWin(*args):
    about_win().showUI()


class about_win(object):
    def __init__(self):
        self.version = pm.optionVar.get('tb_version', 1.0)

    def showUI(self):
        if pm.window("aboutWindow", exists=True):
            pm.deleteUI("aboutWindow")
        window = pm.window("aboutWindow", title="About")
        layout = pm.columnLayout(adjustableColumn=True)
        pm.text(font="boldLabelFont", label="Version : %s" % self.version)

        pm.button(label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        pm.showWindow(window)
