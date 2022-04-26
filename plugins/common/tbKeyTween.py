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


class KeyTweenCommand(om.MPxCommand):
    COMMAND_NAME = "tbKeyTween"

    TIMES_FLAG = ["-t", "-times", (om.MSyntax.kTime)]
    VERSION_FLAG = ["-v", "-version"]
    NAME_FLAG = ["-n", "-name"]

    ALPHA_FLAG = ["-a", "-alpha"]
    ALPHA2_FLAG = ["-ab", "-alphaB"]
    BLENDMODE_FLAG = ["-b", "-blendMode"]
    CLEARCACHE_FLAG = ["-c", "-clearCache"]

    alpha = 0.0
    alphaB = 0.0
    blendMode = None
    clearCache = True
    animCurveChange = None

    def __init__(self):
        super(KeyTweenCommand, self).__init__()

        self.undoable = True

    def doIt(self, arg_list):
        try:
            arg_db = om.MArgDatabase(self.syntax(), arg_list)
        except:
            self.displayError('Error parsing arguments')
            raise
        if arg_db.numberOfFlagsUsed == 0:
            self.displayError('No flags used')
            return
        if arg_db.isFlagSet(KeyTweenCommand.ALPHA_FLAG[0]):
            self.alpha = arg_db.flagArgumentDouble(KeyTweenCommand.ALPHA_FLAG[0], 0)
        if arg_db.isFlagSet(KeyTweenCommand.ALPHA_FLAG[0]):
            self.alphaB = arg_db.flagArgumentDouble(KeyTweenCommand.ALPHA2_FLAG[0], 0)
        if arg_db.isFlagSet(KeyTweenCommand.BLENDMODE_FLAG[0]):
            self.blendMode = arg_db.flagArgumentString(KeyTweenCommand.BLENDMODE_FLAG[0], 0)
        if arg_db.isFlagSet(KeyTweenCommand.CLEARCACHE_FLAG[0]):
            self.clearCache = arg_db.flagArgumentBool(KeyTweenCommand.CLEARCACHE_FLAG[0], 0)

        slideTool = SlideTools()

        if self.clearCache:
            self.displayInfo('clearCache')
            cmds.undoInfo(stateWithoutFlush=False)
            self.animCurveChange = oma.MAnimCurveChange()
            slideTool.animCurveChange = self.animCurveChange
            slideTool.cacheKeyData()
            cmds.undoInfo(stateWithoutFlush=True)

        slideTool.doKeyTween(self.alpha, self.alphaB, self.blendMode)

    def undoIt(self):
        SlideTools().animCurveChange.undoIt()

    def redoIt(self):
        SlideTools().animCurveChange.redoIt()

    def isUndoable(self):
        # self.displayInfo("Info: isUndoable() method called")
        return self.undoable

    @classmethod
    def creator(cls):
        return KeyTweenCommand()

    @classmethod
    def create_syntax(cls):
        syntax = om.MSyntax()

        # add all the flags
        # blend alpha amount
        syntax.addFlag(KeyTweenCommand.ALPHA_FLAG[0], KeyTweenCommand.ALPHA_FLAG[1], om.MSyntax.kDouble)
        syntax.addFlag(KeyTweenCommand.ALPHA2_FLAG[0], KeyTweenCommand.ALPHA2_FLAG[1], om.MSyntax.kDouble)
        # blend method
        syntax.addFlag(KeyTweenCommand.BLENDMODE_FLAG[0], KeyTweenCommand.BLENDMODE_FLAG[1], om.MSyntax.kString)
        # recache base values
        syntax.addFlag(KeyTweenCommand.CLEARCACHE_FLAG[0], KeyTweenCommand.CLEARCACHE_FLAG[1], om.MSyntax.kBoolean)

        return syntax


def initializePlugin(plugin):
    """
    """
    vendor = "tbAnimTools"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    try:
        plugin_fn.registerCommand(KeyTweenCommand.COMMAND_NAME, KeyTweenCommand.creator, KeyTweenCommand.create_syntax)
    except:
        om.MGlobal.displayError("Failed to register command: {0}".format(KeyTweenCommand.COMMAND_NAME))


def uninitializePlugin(plugin):
    """
    """
    plugin_fn = om.MFnPlugin(plugin)
    try:
        plugin_fn.deregisterCommand(KeyTweenCommand.COMMAND_NAME)
    except:
        om.MGlobal.displayError("Failed to deregister command: {0}".format(KeyTweenCommand.COMMAND_NAME))


if __name__ == "__main__":
    cmds.file(new=True, force=True)

    plugin_name = "tbKeyTween.py"
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))

    cmds.evalDeferred('cmds.polyCube()')
