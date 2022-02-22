import maya

maya.stringTable['tbCommand.shift_time_range_start'] = u'Shifts the current playback range so ' \
                                                          u'the current time is the start frame'
maya.stringTable['tbCommand.shift_time_range_end'] = u'Shifts the current playback range so ' \
                                           u'the current time is the end frame'
maya.stringTable['tbCommand.crop_time_range_start'] = u'Crops the timeline so the start time is the current frame.__' \
                                                         u'With the timeline highlighted, bot the start and end are cropped to the highlighted range.'
maya.stringTable['tbCommand.crop_time_range_end'] = u'Crops the timeline so the end time is the current frame.__' \
                                                       u'With the timeline highlighted, bot the start and end are cropped to the highlighted range.'
maya.stringTable['tbCommand.skip_forward'] = u'Moves the current time forwards x number of frames.__' \
                                                u'Default is 5, the value can be set in the options window'
maya.stringTable['tbCommand.skip_backward'] = u'Moves the current time backwards x number of frames.__' \
                                                 u'Default is 5, the value can be set in the options window'
