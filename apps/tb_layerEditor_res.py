import maya

maya.stringTable['tbCommand.select_best_layer'] = u'Selects the top most preferred layer if an object is selected.__' \
                                                         u'On repeat it will cycle down through available layers.__' \
                                                         u'Changing selection will reset the repeat state.__' \
                                                         u'If no object is selected, the topmost layer will be selected.'
maya.stringTable['tbCommand.toggleLayerWeight'] = u'Toggles the weight of the selected layer and sets the keys to flat.__' \
                                                  u'If the current weight is less than 0.5 it will be set to 1.__' \
                                                  u'If it is greater than 0.5 it will be set to 0'


