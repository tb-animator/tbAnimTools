import maya.utils as mutils
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
# '''
hasSingleShot = False
callback_id = None  # Variable to store the callback ID

def callbackFunction(*args):
    global hasSingleShot

    if not hasSingleShot:
        hasSingleShot = True
        cmds.evalDeferred(startupFunction, lp=True)  # Pass the function directly

def startupFunction(*args):
    import module_startup as module_startup
    module_startup.initialise().load_everything()
    remove_plugin_callback()


def add_plugin_callback():
    global callback_id
    # Add the callback and store the ID
    callback_id = OpenMaya.MSceneMessage.addStringArrayCallback(OpenMaya.MSceneMessage.kAfterPluginLoad, startupFunction)

def remove_plugin_callback():
    global callback_id
    # If the callback is active, remove it to clean up
    if callback_id is not None:
        OpenMaya.MMessage.removeCallback(callback_id)
        callback_id = None


if not cmds.about(batch=True):
    print("********************")
    print("TB AnimTools LOADING")
    print("********************")
    add_plugin_callback()

else:
    print("****************************************")
    print("TB AnimTools BATCH MODE (not) LOADING")
    print("****************************************")
# '''