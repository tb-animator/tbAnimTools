print ("*******************")
print ("TB TOOLS v2 LOADING")
print ("*******************")
import maya.utils as mutils

mutils.executeDeferred('import module_startup as module_startup;module_startup.initialise().load_everything()')