import maya

maya.stringTable['tbCommand.kSettingOptVar'] = u'Setting optionVar: %s=%s'
maya.stringTable['tbCommand.aimAtTempControl'] = u'Creates a temporary animation control with the current selection being aim constrained to it. Move the pivot to the desired location and deselect it to trigger the baking.\n' \
                                                 u'\n' \
                                                 u'Use the right click menu on the temporary control for extra functions'
maya.stringTable['tbCommand.bakeAim'] = u''
maya.stringTable['tbCommand.bakeAim_X_Yup'] = u''
maya.stringTable['tbCommand.bakeAim_X_Zup'] = u''
maya.stringTable['tbCommand.bakeAim_Y_Xup'] = u''
maya.stringTable['tbCommand.bakeAim_Y_Zup'] = u''
maya.stringTable['tbCommand.bakeAim_Z_Xup'] = u''
maya.stringTable['tbCommand.bakeAim_Z_Yup'] = u''
maya.stringTable['tbCommand.aimToolsMMPressed'] = u''

# maya.stringTable['tbCommand.kbakeOutSelected'] = u'Bake out the selected temp controls'
# maya.stringTable['tbCommand.kbakeOutAll'] = u'Bake out all the temp controls in the asset'
maya.stringTable['AimTools.CreateHelpTitle'] = u'AimTools.CreateHelpTitle'
maya.stringTable['AimTools.AimToolDefaultHelp'] = u'image.png'
maya.stringTable['AimTools.CreateIsGif'] = False
maya.stringTable['AimTools.CreateHelp'] = u'Use this window to set the default forwards (2 axis) ' \
                                          u'and up (twist axis) values for the selected object. ' \
                                          u'\nSet the default size of the temporary controls and ' \
                                          u'distance from the original control.\n' \
                                          u'When running the command "bakeAim" these values will be used for the bake.'

