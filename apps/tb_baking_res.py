import maya

maya.stringTable['y_tb_Baking.kSettingOptVar'] = u'Setting optionVar: %s=%s'
maya.stringTable['y_tb_Baking.quickMergeAllLayers'] = u'Quickly merge all layers down to base__' \
                                                      u'Faster than a standard maya merge all layers'
maya.stringTable['y_tb_Baking.quickMergeSelectionToNew'] = u'Quickly merge all animation from selected__' \
                                                           u'objects to a new layer.__' \
                                                           u'Animation is removed from old layers'
maya.stringTable['y_tb_Baking.quickMergeSelectionToBase'] = u'Quickly merge all animation from selected__' \
                                                            u'objects to a the base layer.__' \
                                                            u'Animation is removed from old layers'
maya.stringTable['y_tb_Baking.bakeConstraintToAdditive'] = u'Currently Broken'
maya.stringTable['y_tb_Baking.additiveExtractSelection'] = u'Extract the selected time range to two layers.____' \
                                                           u'One override layer containing a linear pose interpolation.__' \
                                                           u'One child additive layer containing the original motion relative to the override layer.____' \
                                                           u'Useful for dialing out/scaling down a motion.'
maya.stringTable[
    'y_tb_Baking.simpleBakeToOverride'] = u'Quickly bake your key range or selected timeline range to a new override layer.'
maya.stringTable['y_tb_Baking.simpleBakeToBase'] = u'Quickly bake your animation to the base layer__' \
                                                   u'Layers above are kept intact'
maya.stringTable['y_tb_Baking.quickCreateAdditiveLayer'] = u'Quickly create an additive layer based on your selection'
maya.stringTable['y_tb_Baking.quickCreateOverrideLayer'] = u'Quickly create an override layer based on your selection'
maya.stringTable[
    'y_tb_Baking.counterAnimLayer'] = u'Used to counter the animation from a parent controller on an additive layer__' \
                                      u'__' \
                                      u'Select your affected controls, then the one animated in an additive layer__' \
                                      u'The affected  controls will be baked to an additive layer parented to your original layer.____' \
                                      u'The affected controls animation on this layer will be in their original locations as if the additive was off.____' \
                                      u'You can now play with the weight of both your original additive layer and this to blend in/out how much the original layer affects the child controls.'

maya.stringTable['y_tb_Baking.worldOffsetSelection'] = u'Bake the current selected objects rotation to a temp control, used as a world space additive control, __' \
                                                       u'a second control is added as a final local offset.'
maya.stringTable['y_tb_Baking.redirectSelected'] = u'Bake the current selected objects to a mini rig to redirect translation/rotation.__Good for turning a walk into a strafe.'
maya.stringTable['y_tb_Baking.bakeToLocator'] = u'Bake the current selected objects to world space locators.__' \
                                                u'Supports locked channels.'
maya.stringTable['y_tb_Baking.bakeToLocatorRotation'] = u'Bake the current selected objects to world space locators.__' \
                                                        u'Only rotation is constrained on the original controls.'
maya.stringTable['y_tb_Baking.simpleConstraintOffset'] = u'Constrain your control to another, maintaining the offset.__' \
                                                         u'Select parent>child control.'
maya.stringTable['y_tb_Baking.simpleConstraintNoOffset'] = u'Constrain your control to another, __' \
                                                           u'controls are constrained with no offset.__' \
                                                           u'Select parent>child control.'
maya.stringTable[
    'y_tb_Baking.simpleConstraintOffsetPostBake'] = u'Constrain your control to another, maintaining the offset__' \
                                                    u'Animation is immediately baked out__' \
                                                    u'Select parent>child control.'
maya.stringTable['y_tb_Baking.simpleConstraintNoOffsetPostBake'] = u'Constrain your control to another, __' \
                                                                   u'controls are constrained with no offset.__' \
                                                                   u'Animation is immediately baked out.__' \
                                                                   u'Select parent>child control.'
maya.stringTable['y_tb_Baking.simpleConstraintOffsetPostBakeReverse'] = u'Constrain your control to another, __' \
                                                                        u'controls are constrained with their current offset.__' \
                                                                        u'Animation is immediately baked out.__' \
                                                                        u'After baking, the parent control is constrained with __' \
                                                                        u'offset to the newly baked out child control.' \
                                                                        u'Select parent>child control.'
maya.stringTable['y_tb_Baking.simpleConstraintNoOffsetPostBakeReverse'] = u'Constrain your control to another, __' \
                                                                          u'controls are constrained with no offset.__' \
                                                                          u'Animation is immediately baked out.' \
                                                                          u'After baking, the parent control is constrained with __' \
                                                                          u'offset to the newly baked out child control.' \
                                                                          u'Select parent>child control.'
