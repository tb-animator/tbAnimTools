'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2015-Tom Bailey
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
    visit tb-animator.blogspot.com for "stuff"

    usage


*******************************************************************************
'''
import maya.utils as mutils
import apps.tb_optionVars as tbo
import pymel.core as pm
import apps.tb_keyCommands as tb_hotKeys
import maya.mel as mel

class initialise(object):
    def check_for_updates(self):
        pass
        #upd.updater().check_version()
    '''
    def loadRMB(self, *args):
        try:
            mml.customloadRMBer().load()
        except Exception as e:
            print "BAD CALLBACK", Exception, e
    '''
    def load_everything(self):
        keyLoader = tb_hotKeys.tbToolLoader()
        keyLoader.loadAllCommands()

        if tbo.set_default_values():
            pm.optionVar(intValue=('tb_firstRun', 0))

        mutils.executeDeferred('import tb_menu as tb_menu;tb_menu.make_ui()')
        mutils.executeDeferred('from pluginLookup import ClassFinder')
        mutils.executeDeferred('import apps.tb_keyCommands as tb_hotKeys;keyLoader = tb_hotKeys.tbToolLoader();keyLoader.assignHotkeysFromLoadedClasses()')
        #mutils.executeDeferred('import updater as upd;upd.updater().check_version()')
        #mutils.executeDeferred('import tb_graphEditor as ge;ge.graphEditor().add_graph_editor_callback()')

        # load dag menu edit
        #mutils.executeDeferred('import apps.mayaMod.mayaModLoader as mml;mml.customloadRMBer().load()')
        #mutils.executeDeferred('import maya.mel as mel')
        #mutils.executeDeferred('mel.eval(\'scriptJob -conditionTrue \"SomethingSelected\" updateTumble\')')
        #mutils.executeDeferred('mel.eval(\'scriptJob -event \"DragRelease\" updateTumble\')')
        #mutils.executeDeferred('mel.eval(\'scriptJob -event \"ModelPanelSetFocus\" updateTumble\')')
        #mutils.executeDeferred('mel.eval(\'scriptJob -event \"playbackModeChanged\" updateTumble\')')
        #Om.MSceneMessage.addCallback(6, self.loadRMB)
