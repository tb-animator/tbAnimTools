import maya

maya.stringTable['tbCommand.createTempPivotInteractive'] = u'Interactively place a temporary animation control ' \
                                                             u'on the selected control. The tool will then bake the control to a tempary control\n' \
                                                             u'\n' \
                                                             u'Move the temporary node to the desired position and ' \
                                                             u'either deselect it or change tool to trigger the bake'
maya.stringTable[
    'tbCommand.createTempPivotAtSelection'] = u'Select two controls, this tool will bake the first control to a temporary control.' \
                                              u'The location of the new control will be at the second selected object'
maya.stringTable['tbCommand.createPersistentTempPivotInteractive'] =  u'Interactively place a temporary animation control ' \
                                                             u'on the selected control. The tool will then bake the control to a tempary control\n' \
                                                             u'\n' \
                                                             u'Move the temporary node to the desired position and ' \
                                                             u'either deselect it or change tool to trigger the bake.' \
                                                                      u'\n' \
                                                                      u'This tool will leave a temporary node inside an asset. ' \
                                                                      u'This node can be used to quickly rebake the same temporary pivot control placement'
maya.stringTable['tbCommand.createPersistentTempPivotNodeAtSelection'] = u'This will create a temporary pivot node marker on the selected control. ' \
                                                                         u'This can be used to quickly bake a tempoary pivot control using the right click menu. ' \
                                                                         u'\n' \
                                                                         u'The node can be saved to be reused in another scene - also in the right click menu.'
maya.stringTable['tbCommand.restorePersistentPivots'] = u'Loads any pivot markers saved out for the current selected controls'
maya.stringTable['tbCommand.bakePersistentPivotFromSel'] = u'Loads any pivot markers saved out for the current selected controls. ' \
                                                           u'This command will also bake the controls to the first pivot marker for each control'
maya.stringTable['tbCommand.createTempPivotHierarchy'] = u'Creates temporary controls from the current selection. Last selected will be the top of the hierarchy. Move the pivot to place the top parent control before baking. ' \
                                                         u'\n' \
                                                         u'Deselect the pivot to trigger the bake.'
maya.stringTable['tbCommand.createTempParentInteractive'] = u'This will create a temporary parent control for the current frame. ' \
                                                            u'Interactively place the pivot point to where you want to rotate your selection from. Then change your selection/tool to create the new control. ' \
                                                            u'\n' \
                                                            u'This new temporary control will be removed once deselected'
maya.stringTable['tbCommand.createTempParentLastSelected'] = u'This will create a temporary control for the current frame. The control will be placed at the last selected control. Deselecting the control will remove the temporary control.'

maya.stringTable['TempPivot.updatePivot'] = u'Update Pivot Offset'
maya.stringTable['TempPivot.bakePointToControl'] = u'Create temp pivot control'
maya.stringTable['TempPivot.saveTempPivots'] = u'Save temp pivots'
