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

    usage


*******************************************************************************
'''
import maya.cmds as cmds
import maya.utils as mutils
import maya.mel as mel
from tb_mainFunctions import Functions
from tb_mainUtility import *

import tbtoolsUpdater as upd
import os


class initialise(object):
    def check_for_updates(self):
        if not get_option_var('tbUpdateType', -1) == 2:
            updater = upd.updater()
            updater.check_version()


    def loadRMB(self, *args):
        pass
        '''
        try:
            eventFilterManager = qtm.EventFilterManager()
            eventFilterManager.installMainFilter()
        except Exception as e:
            print ("EventFilterManager Failed", Exception, e)
        '''

    def load_everything(self):
        if cmds.about(batch=True):
            return
        if os.name == 'nt':
            import tbtoolsInstaller

            tbtoolsInstaller.module_maker().install()

            try:

                self.check_for_updates()

            except Exception as e:
                cmds.warning(e)

            #self.loadRMB()
        #import apps.tb_keyCommands as tb_hotKeys
        '''
        keyLoader = tb_hotKeys.tbToolLoader()
        keyLoader.loadAllCommands()
        '''

        if set_default_values():
            set_option_var('tb_firstRun', 0)

        mutils.executeDeferred('import tb_mainMenu as tb_menu;tb_menu.make_ui()', lp=True)

        mutils.executeDeferred('from pluginLookup import ClassFinder', lp=True)

        # camera pivot update
        mutils.executeDeferred('import maya.mel as mel', lp=True)

        # mutils.executeDeferred('import maya.mel as mel; mel.eval("createToolbar")', lp=True)

        mutils.executeDeferred('import maya.mel as mel; mel.eval("createCameraPivotScriptJob")', lp=True)





