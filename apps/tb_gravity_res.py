import maya

maya.stringTable['tbCommand.kSettingOptVar'] = u'Setting optionVar: %s=%s'
maya.stringTable[
    'tbCommand.doQuickJump'] = u'Create a ballistic arc between the previous and next keyframes on your currently active layer.__' \
                                  u'Supports multiple objects and layer combinations.__' \
                                  u'Animating the layer weight is not supported'

maya.stringTable[
    'tbCommand.doJumpAllKeypairs'] = u'Create a ballistic arc between all key pairs on your currently active layer__' \
                                        u'Supports multiple objects and layer combinations__' \
                                        u'Animating the layer weight is not supported'
maya.stringTable[
    'tbCommand.doJumpUsingInitialFrameVelocity'] = u'Create a ballistic arc based on the velocity between the current frame and previous__' \
                                                      u'Supports multiple objects and layer combinations__' \
                                                      u'Animating the layer weight is not supported'
