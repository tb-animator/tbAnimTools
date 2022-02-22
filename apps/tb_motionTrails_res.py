import maya


maya.stringTable['tbCommand.toggleMotionTrail'] = u'With objects selected, it will toggle motion trails on or off for the selection.__' \
                                                          u'With nothing selected, it will globally toggle all motion trails either on or off.__' \
                                                          u'The tool remembers which objects had motion trails and restores their individual settings.'
maya.stringTable['tbCommand.createCameraRelativeMotionTrail'] = u'Specifically create a camera relative motion trail on the selected object(s)'
maya.stringTable['tbCommand.toggleMotionTrailCameraRelative'] = u'Toggles the motion trails for the selected object to be relative to the current camera, or the world.'
maya.stringTable['tbCommand.createMotionTrail'] = u'Basic create motion trail command.__' \
                                                          u'toggleMotionTrail is more useful'
maya.stringTable['tbCommand.removeMotionTrail'] = u'Removes the trail from the selected controls'
