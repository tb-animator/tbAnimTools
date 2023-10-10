
import maya.utils as mutils
import maya.cmds as cmds
if not cmds.about(batch=True):
    print("********************")
    print("TB AnimTools LOADING")
    print("********************")
    mutils.executeDeferred('import module_startup as module_startup;module_startup.initialise().load_everything()')
else:
    print("****************************************")
    print("TB AnimTools BATCH MODE (not) LOADING")
    print("****************************************")