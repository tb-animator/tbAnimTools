import maya


maya.stringTable['tbCommand.toggleMotionTrail'] = u'With objects selected, it will toggle motion trails on or off for the selection.__' \
                                                          u'With nothing selected, it will globally toggle all motion trails either on or off.__' \
                                                          u'The tool remembers which objects had motion trails and restores their individual settings.'
maya.stringTable['tbCommand.createCameraRelativeMotionTrail'] = u'Specifically create a camera relative motion trail on the selected object(s)'
maya.stringTable['tbCommand.toggleMotionTrailCameraRelative'] = u'Toggles the motion trails for the selected object to be relative to the current camera, or the world.'
maya.stringTable['tbCommand.createMotionTrail'] = u'Basic create motion trail command.__' \
                                                          u'toggleMotionTrail is more useful'
maya.stringTable['tbCommand.removeMotionTrail'] = u'Removes the trail from the selected controls'
maya.stringTable['tbCommand.motionPathSelected'] = u'Creates a nurbs curve matching your animation and attaches a temp node to it. Your control ' \
                                                   u'is constrained to the temp control on a layer.  You can then edit the curve and the uValue on the temp control.' \
                                                   u'Useful for editing the spacing when you are happy with the path an object is taking, or if you are finding soft selection on ' \
                                                   u'regular animated motion trails is too slow.'
