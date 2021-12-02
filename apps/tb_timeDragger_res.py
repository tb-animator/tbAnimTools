import maya
maya.stringTable['y_tb_timeDragger.stepDragInfo'] = u'Step drag even/odd frames, step skip frames etc'
maya.stringTable['y_tb_timeDragger.smooth_drag_timeline_on'] = u'This is like the default maya "k" + left click drag ' \
                                                               u'tool that scrubs your animation only there is no ' \
                                                               u'frame snapping.__' \
                                                               u'! Remember to set the release command ' \
                                                               u'"smooth_drag_timeline_on" to the same hotkey but as "on released"!'
maya.stringTable[
    'y_tb_timeDragger.smooth_drag_timeline_off'] = u'This is the release command for smooth_drag_timeline_on.__' \
                                                   u'Without it you will get stuck in the timedrag tool'
maya.stringTable['y_tb_timeDragger.step_drag_timeline_on'] = u'This is like the default maya "k" + left click drag ' \
                                                             u'tool that scrubs your animation only if can scrub ' \
                                                             u'on 2\'s, 3\'s etc.__' \
                                                             u'Set the number of frames to skip in the options ' \
                                                             u'window.__' \
                                                             u'! Remember to set the release command ' \
                                                             u'"step_drag_timeline_off" to the same hotkey but as "on released"!'
maya.stringTable[
    'y_tb_timeDragger.step_drag_timeline_off'] = u'This is the release command for step_drag_timeline_on.__' \
                                                 u'Without it you will get stuck in the timedrag tool'
