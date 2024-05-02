import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
from tb_sliders import SlideTools


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

"""
use space switch to switch a lot of objects to world/local/default at once
use it to query the current spaces for all objects
use it to set spaces, give attribute, space name + value
make it easy to insert into other non tbAnimTools functions
"""

class SpaceSwitchCommand(om.MPxCommand):
    COMMAND_NAME = "spaceSwitch"

    QUERY_FLAG = ["-q", "-query"]
    SPACEATTR_FLAG = ["-a", "-attribute"]
    STRINGVALUE_FLAG = ["-sv", "-stringValue"]
    FLOATVALUE_FLAG = ["-fv", "-floatValue"]
    SPACEMODE_FLAG = ["-s", "-spacedMode"]
    CLEARCACHE_FLAG = ["-c", "-clearCache"]

    spaceMode = None
    id = 'default'
    clearCache = True
    animCurveChange = None

    def __init__(self):
        super(SpaceSwitchCommand, self).__init__()

        self.undoable = True
        self.keyframeData = None
        self.keyframeRefData = None

    def doIt(self, arg_list):
        try:
            arg_db = om.MArgDatabase(self.syntax(), arg_list)
        except:
            self.displayError('Error parsing arguments')
            raise
        if arg_db.numberOfFlagsUsed == 0:
            self.displayError('No flags used')
            return
        if arg_db.isFlagSet(SpaceSwitchCommand.ALPHA_FLAG[0]):
            self.alpha = arg_db.flagArgumentDouble(SpaceSwitchCommand.ALPHA_FLAG[0], 0)

        if arg_db.isFlagSet(SpaceSwitchCommand.SPACEMODE_FLAG[0]):
            self.spaceMode = arg_db.flagArgumentString(SpaceSwitchCommand.SPACEMODE_FLAG[0], 0)
        if arg_db.isFlagSet(SpaceSwitchCommand.ID_FLAG[0]):
            self.id = arg_db.flagArgumentString(SpaceSwitchCommand.ID_FLAG[0], 0)
        if arg_db.isFlagSet(SpaceSwitchCommand.CLEARCACHE_FLAG[0]):
            self.clearCache = arg_db.flagArgumentBool(SpaceSwitchCommand.CLEARCACHE_FLAG[0], 0)

        slideTool = SlideTools()

        if self.clearCache:
            self.displayInfo('clearCache')
            cmds.undoInfo(stateWithoutFlush=False)
            self.animCurveChange = oma.MAnimCurveChange()
            slideTool.animCurveChange = self.animCurveChange
            slideTool.cacheKeyData()
            cmds.undoInfo(stateWithoutFlush=True)
        else:
            self.animCurveChange = slideTool.animCurveChange
        slideTool.doKeyTween(self.alpha, self.alphaB, self.spaceMode, self.animCurveChange)

    def undoIt(self):
        self.animCurveChange.undoIt()

    def redoIt(self):
        self.animCurveChange.redoIt()

    def isUndoable(self):
        # self.displayInfo("Info: isUndoable() method called")
        return self.undoable

    @classmethod
    def creator(cls):
        return SpaceSwitchCommand()

    @classmethod
    def create_syntax(cls):
        syntax = om.MSyntax()

        # add all the flags
        # blend alpha amount
        syntax.addFlag(SpaceSwitchCommand.ALPHA_FLAG[0], SpaceSwitchCommand.ALPHA_FLAG[1], om.MSyntax.kDouble)
        syntax.addFlag(SpaceSwitchCommand.ALPHA2_FLAG[0], SpaceSwitchCommand.ALPHA2_FLAG[1], om.MSyntax.kDouble)
        # blend method
        syntax.addFlag(SpaceSwitchCommand.SPACEMODE_FLAG[0], SpaceSwitchCommand.SPACEMODE_FLAG[1], om.MSyntax.kString)
        # recache base values
        syntax.addFlag(SpaceSwitchCommand.CLEARCACHE_FLAG[0], SpaceSwitchCommand.CLEARCACHE_FLAG[1], om.MSyntax.kBoolean)

        return syntax


def initializePlugin(plugin):
    """
    """
    vendor = "tbAnimTools"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    try:
        plugin_fn.registerCommand(SpaceSwitchCommand.COMMAND_NAME, SpaceSwitchCommand.creator, SpaceSwitchCommand.create_syntax)
    except:
        om.MGlobal.displayError("Failed to register command: {0}".format(SpaceSwitchCommand.COMMAND_NAME))


def uninitializePlugin(plugin):
    """
    """
    plugin_fn = om.MFnPlugin(plugin)
    try:
        plugin_fn.deregisterCommand(SpaceSwitchCommand.COMMAND_NAME)
    except:
        om.MGlobal.displayError("Failed to deregister command: {0}".format(SpaceSwitchCommand.COMMAND_NAME))


if __name__ == "__main__":
    cmds.file(new=True, force=True)

    plugin_name = "tbSpaceSwitch.py"
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))

    cmds.evalDeferred('cmds.polyCube()')
