import maya

maya.stringTable['tbCommand.clampKeysAbove'] = u'Clamp the values of the selected curves above the current value. __' \
                                               u'Sparse keys are preserved.'
maya.stringTable['tbCommand.clampKeysBelow'] = u'Clamp the values of the selected curves below the current value. __' \
                                               u'Sparse keys are preserved.'
maya.stringTable['tbCommand.match_tangent_start_to_end'] = u'Adjust the selected curves start tangents to match the end tangents - Use it to clean up loops'
maya.stringTable['tbCommand.match_tangent_end_to_start'] = u'Adjust the selected curves end tangents to match the start tangents - Use it to clean up loops'
maya.stringTable['tbCommand.shift_selected_keys_to_start_at_current_time'] = u'Shifts the selected keys as a group so their start time matches the current frame'
maya.stringTable['tbCommand.shift_selected_keys_to_end_at_current_time'] = u'Shifts the selected keys as a group so their end time matches the current frame'
maya.stringTable['tbCommand.flip_selected_key_values'] = u'Performs a -1 scale on the selected keys'
maya.stringTable['tbCommand.flip_selected_key_values_start'] = u'Performs a -1 scale on the selected keys, the pivot of the flip is at the first key value'
maya.stringTable['tbCommand.flip_selected_key_values_end'] = u'Performs a -1 scale on the selected keys, the pivot of the flip is at the last key value'
maya.stringTable['tbCommand.filter_channelBox'] = u'Filters the currently viewed anim curves in the graph editor to match the channelBox attribute selection'
maya.stringTable['tbCommand.setTangentsLinear'] = u'Sets the selected key tangents to LINEAR, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.setTangentsStepped'] = u'Sets the selected key tangents to STEPPED, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.setTangentsAuto'] = u'Sets the selected key tangents to AUTO, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.setTangentsSpline'] = u'Sets the selected key tangents to SPLINE, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.setTangentsFlat'] = u'Sets the selected key tangents to FLAT, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.setTangentsEase'] = u'Sets the selected key tangents to AUTOEASE, if keys are not selected it will set the keys for the current frame'
maya.stringTable['tbCommand.flattenControl'] = u'Flatten the up axis of a control to align to the world up. Useful for feet to flatten them to the ground plane without adjusting their yaw rotation.'
maya.stringTable['tbCommand.eulerFilterSelection'] = u''
maya.stringTable['tbCommand.quickCopyKeys'] = u'Copies and pastes the selected graph editor keys to the current frame'
maya.stringTable['tbCommand.quickCopyKeysConnect'] = u'Copies and pastes the selected graph editor keys to the current frame. Uses paste>connect, so values will be offset'
maya.stringTable['tbCommand.clampKeysBelow'] = u'Clamps the values of the selected keys to the current frame value, if they are above the current value '
maya.stringTable['tbCommand.clampKeysAbove'] = u'Clamps the values of the selected keys to the current frame value, if they are below the current value '
maya.stringTable['tbCommand.autoTangent'] = u'Sets the tangent angle to smooth, uses the default value set from the UI in the graph editor'
maya.stringTable['tbCommand.guessKeyValue'] = u'Places the selected key value to a best guess position based on the previous and next tangent values'
