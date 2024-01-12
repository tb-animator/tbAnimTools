import maya

maya.stringTable['tbCommand.kSettingOptVar'] = u'Setting optionVar: %s=%s'

maya.stringTable['tbCommand.kbakeOutSelected'] = u'Bake out the selected temp controls'
maya.stringTable['tbCommand.kbakeOutAll'] = u'Bake out all the temp controls in the asset'
maya.stringTable['tbCommand.kremoveAll'] = u'Delete all the temp controls in the asset'

maya.stringTable['tbCommand.quickMergeAllLayers'] = u'Quickly merge all layers down to base__' \
                                                      u'Faster than a standard maya merge all layers'
maya.stringTable['tbCommand.quickMergeSelectionToNew'] = u'Quickly merge all animation from selected__' \
                                                           u'objects to a new layer.__' \
                                                           u'Animation is removed from old layers'
maya.stringTable['tbCommand.quickMergeSelectionToBase'] = u'Quickly merge all animation from selected__' \
                                                            u'objects to a the base layer.__' \
                                                            u'Animation is removed from old layers'
maya.stringTable['tbCommand.bakeConstraintToAdditive'] = u'Currently Broken'
maya.stringTable['tbCommand.additiveExtractSelection'] = u'Extract the selected time range to two layers.____' \
                                                           u'One override layer containing a linear pose interpolation.__' \
                                                           u'One child additive layer containing the original motion relative to the override layer.____' \
                                                           u'Useful for dialing out/scaling down a motion.'
maya.stringTable[
    'tbCommand.simpleBakeToOverride'] = u'Quickly bake your key range or selected timeline range to a new override layer.'
maya.stringTable['tbCommand.simpleBakeToBase'] = u'Quickly bake your animation to the base layer__' \
                                                   u'Layers above are kept intact'
maya.stringTable['tbCommand.quickCreateAdditiveLayer'] = u'Quickly create an additive layer based on your selection'
maya.stringTable['tbCommand.quickCreateOverrideLayer'] = u'Quickly create an override layer based on your selection'
maya.stringTable[
    'tbCommand.counterAnimLayer'] = u'Used to counter the animation from a parent controller on an additive layer__' \
                                      u'__' \
                                      u'Select your affected controls, then the one animated in an additive layer__' \
                                      u'The affected  controls will be baked to an additive layer parented to your original layer.____' \
                                      u'The affected controls animation on this layer will be in their original locations as if the additive was off.____' \
                                      u'You can now play with the weight of both your original additive layer and this to blend in/out how much the original layer affects the child controls.'

maya.stringTable['tbCommand.worldOffsetSelection'] = u'Bake the current selected objects rotation to a temp control, used as a world space additive control, __' \
                                                       u'a second control is added as a final local offset. Good for consistent world space offsets on controls ' \
                                                     u'when a standard additive layer would introduce too much wobble.'
maya.stringTable['tbCommand.worldOffsetSelectionRotation'] = u'Bake the current selected objects rotation to a temp control, used as a world space additive control, __' \
                                                       u'a second control is added as a final local offset. Good for consistent world space offsets on controls ' \
                                                     u'when a standard additive layer would introduce too much wobble.' \
                                                             u'Original control is only constrained in rotation.' \
                                                             u''
maya.stringTable['tbCommand.redirectSelected'] = u'Bake the current selected objects to a mini rig to redirect translation/rotation.__Good for turning a walk into a strafe.'
maya.stringTable['tbCommand.bakeToLocator'] = u'Bake the current selected objects to world space locators.__' \
                                                u'Supports locked channels.'
maya.stringTable['tbCommand.bakeToLocatorRotation'] = u'Bake the current selected objects to world space locators.__' \
                                                        u'Only rotation is constrained on the original controls.'
maya.stringTable['tbCommand.simpleConstraintOffset'] = u'Constrain your control to another, maintaining the offset.__' \
                                                         u'Select parent>child control.'
maya.stringTable['tbCommand.simpleConstraintNoOffset'] = u'Constrain your control to another, __' \
                                                           u'controls are constrained with no offset.__' \
                                                           u'Select parent>child control.'
maya.stringTable[
    'tbCommand.simpleConstraintOffsetPostBake'] = u'Constrain your control to another, maintaining the offset__' \
                                                    u'Animation is immediately baked out__' \
                                                    u'Select parent>child control.'
maya.stringTable['tbCommand.simpleConstraintNoOffsetPostBake'] = u'Constrain your control to another, __' \
                                                                   u'controls are constrained with no offset.__' \
                                                                   u'Animation is immediately baked out.__' \
                                                                   u'Select parent>child control.'
maya.stringTable['tbCommand.simpleConstraintOffsetPostBakeReverse'] = u'Constrain your control to another, __' \
                                                                        u'controls are constrained with their current offset.__' \
                                                                        u'Animation is immediately baked out.__' \
                                                                        u'After baking, the parent control is constrained with __' \
                                                                        u'offset to the newly baked out child control.' \
                                                                        u'Select parent>child control.'
maya.stringTable['tbCommand.simpleConstraintNoOffsetPostBakeReverse'] = u'Constrain your control to another, __' \
                                                                          u'controls are constrained with no offset.__' \
                                                                          u'Animation is immediately baked out.' \
                                                                          u'After baking, the parent control is constrained with __' \
                                                                          u'offset to the newly baked out child control.' \
                                                                          u'Select parent>child control.'
maya.stringTable['tbCommand.bakeToLocatorPinned'] = u'Bake the selected controls to temporary controls. \n' \
                                                    u'The last selected control will be the the new parent for the temporary controls'
