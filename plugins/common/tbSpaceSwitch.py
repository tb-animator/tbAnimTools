import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
from apps.tb_spaceSwitch import SpaceSwitch


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


"""
examples
add the current selected controls as space switched controls. Space switch attribute is defined. The attribute value is case-insenstive, it will find the matching one from a partial name - here the value should be "space" but it will work with the bad input.
cmds.spaceSwitch(edit=True, attribute='SPace')

Add the current selected controls as space switched controls:
space attribute is NOT defined, the tool will find currently used attribute from existing data
cmds.spaceSwitch(edit=True)
Add specific controls - not the current selection, let it determine the space attrbute automatically
cmds.spaceSwitch(selection='bill:CTRL_l_hand_IK, bill:CTRL_r_hand_IK', edit=True)

If in doubt, specify the attribute
cmds.spaceSwitch(edit=True, attribute='worldOrient')

Save the currently selected objects and their space values as a preset (in their current state)
cmds.spaceSwitch(edit=True, presetName='customLoco')

Use a preset to space switch (requires part of the rig to be selected, or specified)
Switch the current frame
cmds.spaceSwitch(switch=True, presetName='customLoco')
Switch the timeline
cmds.spaceSwitch(switch=True, timeline=True,  presetName='customLoco')
Bake
cmds.spaceSwitch(bake=True, presetName='customLoco')

Switch the selected controls to "Master" space
cmds.spaceSwitch(switch=True, value="Master")
Bake the selected controls to 0 space
cmds.spaceSwitch(bake=True, value=0)
Switch the selected controls to the value on the layer below the current one (good for swapping after pasting a pose etc)
cmds.spaceSwitch(switch=True, getLowerLayer=True)
or bake to the lower layer
cmds.spaceSwitch(bake=True, getLowerLayer=True)

Override the value for the preset, instead of getting the current value - only one value can be set
cmds.spaceSwitch(edit=True, presetName='GlobalAlt', attribute='space', value='Master Offset') 
"""


class SpaceSwitchCommand(om.MPxCommand):
    COMMAND_NAME = "spaceSwitch"

    QUERY_FLAG = ["-q", "-query"]
    EDIT_FLAG = ["-e", "-edit"]
    SELECTION = ["-s", "-selection"]
    SPACEATTR_FLAG = ["-a", "-attribute"]
    SPACEVALUE_STRING = ["-v", "-value"]
    SPACEQUICKVALUE_STRING = ["-sqv", "-spaceQuickValue"]
    SPACEPRESETVALUE_STRING = ["-pr", "-presetName"]

    SWITCH_FLAG = ["-sw", "-switch"]
    BAKE_FLAG = ["-b", "-bake"]
    TIMELINE_FLAG = ["-tl", "-timeline"]

    GETLOWERLAYER_BOOL = ["-gll", "-getLowerLayer"]

    query = False
    getLowerLayer = False
    edit = False
    spaceAttribute = None
    switch = False
    bake = False
    timeline = False
    switchMode = None
    spaceValue = None
    spacePreset = ""
    allowedSwitchModes = ['bake', 'switch', 'switchtimeline']
    omSelection = ""
    selection = list()
    spaceTool = SpaceSwitch()

    defaultPresetNames = [spaceTool.str_spaceDefault,
                          spaceTool.str_spaceMirror,
                          spaceTool.str_spaceLocal,
                          spaceTool.str_spaceGlobal]

    # avoiding repetition, just put bake/switch methods in a dictionary and call it based on the switch/bake input
    bakeMethods = {'bake': spaceTool.bake,
                   'switch': spaceTool.switch,
                   'switchtimeline': spaceTool.switch}
    bakePresetMethods = {'bake': spaceTool.bakePreset,
                         'switch': spaceTool.switchPreset,
                         'switchtimeline': spaceTool.switchPreset}

    def __init__(self):
        super(SpaceSwitchCommand, self).__init__()

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

        # space attribute
        if arg_db.isFlagSet(SpaceSwitchCommand.SPACEATTR_FLAG[0]):
            self.spaceAttribute = arg_db.flagArgumentString(SpaceSwitchCommand.SPACEATTR_FLAG[0], 0)

        if arg_db.isFlagSet(SpaceSwitchCommand.GETLOWERLAYER_BOOL[0]):
            self.getLowerLayer = arg_db.flagArgumentString(SpaceSwitchCommand.GETLOWERLAYER_BOOL[0], 0)

        # space preset value
        if arg_db.isFlagSet(SpaceSwitchCommand.SPACEPRESETVALUE_STRING[0]):
            self.spacePreset = arg_db.flagArgumentString(SpaceSwitchCommand.SPACEPRESETVALUE_STRING[0], 0).lower()

        if arg_db.isFlagSet(SpaceSwitchCommand.SPACEVALUE_STRING[0]):
            self.spaceValue = arg_db.flagArgumentString(SpaceSwitchCommand.SPACEVALUE_STRING[0], 0)

        # get selection first
        if arg_db.isFlagSet(SpaceSwitchCommand.SELECTION[0]):
            raw_string = arg_db.flagArgumentString(SpaceSwitchCommand.SELECTION[0], 0)
            self.selection = [s.strip() for s in raw_string.split(",")]  # Parse comma-separated values
        else:
            # Use current selection if no string array is provided
            self.selection = cmds.ls(sl=True, type='transform')

        # edit
        if arg_db.isFlagSet(SpaceSwitchCommand.EDIT_FLAG[0]):
            # edit - add objects with this attribute
            self.edit = arg_db.flagArgumentBool(SpaceSwitchCommand.EDIT_FLAG[0], 0)

        # query
        if arg_db.isFlagSet(SpaceSwitchCommand.QUERY_FLAG[0]):
            self.query = arg_db.flagArgumentBool(SpaceSwitchCommand.QUERY_FLAG[0], 0)

        if arg_db.isFlagSet(SpaceSwitchCommand.SWITCH_FLAG[0]):
            self.switch = arg_db.flagArgumentString(SpaceSwitchCommand.SWITCH_FLAG[0], 0)

        if arg_db.isFlagSet(SpaceSwitchCommand.BAKE_FLAG[0]):
            self.bake = arg_db.flagArgumentString(SpaceSwitchCommand.BAKE_FLAG[0], 0)

        if arg_db.isFlagSet(SpaceSwitchCommand.TIMELINE_FLAG[0]):
            self.timeline = arg_db.flagArgumentString(SpaceSwitchCommand.TIMELINE_FLAG[0], 0)

        if self.bake and self.switch:
            self.displayError('Cannot bake AND switch at the same time, specify one or the other')

        if self.bake:
            self.switchMode = self.allowedSwitchModes[0]
        elif self.switch:
            if self.timeline:
                self.switchMode = self.allowedSwitchModes[2]
            else:
                self.switchMode = self.allowedSwitchModes[1]
        self.redoIt()

    def undoIt(self):
        cmds.undo()

    def redoIt(self):
        # Open the chunk
        if self.edit:
            self.displayInfo('edit')
            if self.spacePreset:
                if self.spaceValue:
                    self.displayInfo('adding spacePreset with specific value')
                    self.spaceTool.captureData(selection=self.selection,
                                               presetName=self.spacePreset,
                                               valueOverride=self.spaceValue)
                else:
                    self.displayInfo(self.spacePreset)
                    if self.spaceValue:
                        self.spaceTool.captureData(selection=self.selection,
                                                   presetName=self.spacePreset,
                                                   valueOverride=self.spaceValue)
                    else:
                        self.spaceTool.captureData(selection=self.selection,
                                                   presetName=self.spacePreset)
            else:
                # add the current object(s) as a space switch object
                self.displayInfo('adding space object')
                self.spaceTool.addControlsWithMatchingAttribute(selection=self.selection,
                                                                attribute=self.spaceAttribute)

        elif self.query:
            if self.getLowerLayer:
                self.displayInfo('Get lower layer values')
            if self.spaceAttribute: self.displayInfo(self.spaceAttribute)
            if self.spaceValue: self.displayInfo(self.spaceValue)
            if self.switchMode: self.displayInfo(self.switchMode)
            for s in self.selection:
                self.displayInfo(str(s))
        elif self.spacePreset:
            """
            Baking / switching using a preset
            """
            self.displayInfo(str(self.spacePreset))
            cmds.undoInfo(openChunk=True)
            self.bakePresetMethods[self.switchMode](selection=self.selection,
                                                    presetName=self.spacePreset,
                                                    forceTimeline=self.switchMode == 'SwitchTimeline')
            cmds.undoInfo(closeChunk=True)
        else:
            """
            Baking / switching using a value
            """
            cmds.undoInfo(openChunk=True)
            self.bakeMethods[self.switchMode](selection=self.selection,
                                              attribute=self.spaceAttribute,
                                              spaceValue=safe_int_cast(self.spaceValue),
                                              fromLowerLayer=self.getLowerLayer,
                                              forceTimeline=self.switchMode == 'SwitchTimeline')

            cmds.undoInfo(closeChunk=True)

    def isUndoable(self):
        # self.displayInfo("Info: isUndoable() method called")
        return self.undoable

    @classmethod
    def creator(cls):
        return SpaceSwitchCommand()

    @classmethod
    def create_syntax(cls):
        syntax = om.MSyntax()

        syntax.addFlag(SpaceSwitchCommand.QUERY_FLAG[0], SpaceSwitchCommand.QUERY_FLAG[1], om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.EDIT_FLAG[0], SpaceSwitchCommand.EDIT_FLAG[1], om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.SWITCH_FLAG[0], SpaceSwitchCommand.SWITCH_FLAG[1], om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.BAKE_FLAG[0], SpaceSwitchCommand.BAKE_FLAG[1], om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.TIMELINE_FLAG[0], SpaceSwitchCommand.TIMELINE_FLAG[1], om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.SELECTION[0], SpaceSwitchCommand.SELECTION[1], om.MSyntax.kString)
        #
        syntax.addFlag(SpaceSwitchCommand.SPACEATTR_FLAG[0], SpaceSwitchCommand.SPACEATTR_FLAG[1], om.MSyntax.kString)
        syntax.addFlag(SpaceSwitchCommand.GETLOWERLAYER_BOOL[0], SpaceSwitchCommand.GETLOWERLAYER_BOOL[1],
                       om.MSyntax.kBoolean)
        syntax.addFlag(SpaceSwitchCommand.SPACEVALUE_STRING[0], SpaceSwitchCommand.SPACEVALUE_STRING[1],
                       om.MSyntax.kString)
        # syntax.addFlag(SpaceSwitchCommand.SWITCHMODE_FLAG[0], SpaceSwitchCommand.SWITCHMODE_FLAG[1], om.MSyntax.kString)
        syntax.addFlag(SpaceSwitchCommand.SPACEQUICKVALUE_STRING[0], SpaceSwitchCommand.SPACEQUICKVALUE_STRING[1],
                       om.MSyntax.kString)
        syntax.addFlag(SpaceSwitchCommand.SPACEPRESETVALUE_STRING[0], SpaceSwitchCommand.SPACEPRESETVALUE_STRING[1],
                       om.MSyntax.kString)

        return syntax


def initializePlugin(plugin):
    """
    """
    vendor = "tbAnimTools"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)
    try:
        plugin_fn.registerCommand(SpaceSwitchCommand.COMMAND_NAME, SpaceSwitchCommand.creator,
                                  SpaceSwitchCommand.create_syntax)
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


def iterSelection():
    """
    generator style iterator over current Maya active selection
    :return: [MObject) an MObject for each item in the selection
    """
    sel = om.MGlobal.getActiveSelectionList()
    for i in range(sel.length()):
        yield sel.getDependNode(i)


def safe_int_cast(value):
    if value is None:
        return value
    try:
        return int(value)
    except ValueError:
        return value


if __name__ == "__main__":
    cmds.file(new=True, force=True)

    plugin_name = "tbSpaceSwitch.py"
    cmds.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    cmds.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))

    cmds.evalDeferred('cmds.polyCube()')
