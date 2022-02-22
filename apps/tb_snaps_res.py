import maya

maya.stringTable['tbCommand.store_ctrl_transform'] = u'Snapshot the current selected controls world space transform.__' \
                                                     u'Restore it again with restore_ctrl_transform.__'
maya.stringTable['tbCommand.restore_ctrl_transform'] = u'Restore the snapshots of the selected controls transforms.__' \
                                                       u'Works for the selected timeline, it will key the highlighted ' \
                                                       u'range.'
maya.stringTable[
    'tbCommand.store_relative_transform'] = u'Snapshot the transforms of the selected objects, relative to the last ' \
                                            u'selected object.__' \
                                            u'__' \
                                            u'Selection order can be swapped to the first object being the driver ' \
                                            u'in the options window. '
maya.stringTable['tbCommand.restore_relative_transform'] = u'Restores the relative transform for your selection.__' \
                                                           u'Select your controls to restore, then the driver, unless ' \
                                                           u'the order is switched in the otions.__' \
                                                           u'Works on highlighted timeline range.__' \
                                                           u'__' \
                                                           u'Useful for maintaining a contact or a world position ' \
                                                           u'without using a constraint.__' \
                                                           u'Hint - restore multiple poses on different layers and ' \
                                                           u'blend between them.'
maya.stringTable[
    'tbCommand.restore_relative_transform_last_used'] = u'Restores the relative transform for your selection.__' \
                                                        u'Select your controls to restore, the driver is ' \
                                                        u'automatically picked from the last driver used to ' \
                                                        u'store a transform for the selected objects ' \
                                                        u'Works on highlighted timeline range.__' \
                                                        u'__' \
                                                        u'Useful for maintaining a contact or a world position ' \
                                                        u'without using a constraint.__' \
                                                        u'Hint - restore multiple poses on different layers and ' \
                                                        u'blend between them.'
maya.stringTable['tbCommand.snap_objects'] = u'Snap two objects together.__' \
                                             u'Default order is first selected object is the parent (doesn\'nt move), ' \
                                             u'second is the child (will be moved).__' \
                                             u'Order can be reversed in the options window.__' \
                                             u'Works over the selected timeline range.'
maya.stringTable['tbCommand.point_snap_objects'] = u'Snap two objects together - Translation Only.__' \
                                             u'Default order is first selected object is the parent (doesn\'nt move), ' \
                                             u'second is the child (will be moved).__' \
                                             u'Order can be reversed in the options window.__' \
                                             u'Works over the selected timeline range.'
maya.stringTable['tbCommand.orient_snap_objects'] = u'Snap two objects together - Rotation Only.__' \
                                             u'Default order is first selected object is the parent (doesn\'nt move), ' \
                                             u'second is the child (will be moved).__' \
                                             u'Order can be reversed in the options window.__' \
                                             u'Works over the selected timeline range.'

maya.stringTable['SnapTools.selectionOrderInfo'] = u'If checked, the first selected object will be moved to the second.' \
                                                   u'If unchecked, the second object will be moved to the first'

maya.stringTable['SnapTools.selectionOrderOption'] = u'Last selected object is magnet'
maya.stringTable['SnapTools.relativeSnapOrderHeader'] = u'Relative Snap Order'
maya.stringTable[
    'SnapTools.relativeOrderInfo'] = u'If checked, the first selected object will be the reference control.' \
                                     u'If unchecked, the last object will be reference control. ' \
                                     u'The other controls in the selection will be cached/moved.'
maya.stringTable['SnapTools.relativeOrderOptionWidget'] = u'First selected object is the driver'
maya.stringTable[
    'SnapTools.relativeSelectionConstraintOptionWidget'] = u'Use Constraint method (slower, order independent)'
maya.stringTable[
    'SnapTools.relativeSelectionChannelOptionWidget'] = u'Restore transform on selected channels (if selected)'

maya.stringTable['SnapTools.kGetOptVarValues'] = u'Get optionVar values'
maya.stringTable['SnapTools.tbSnapSelectionOrder'] = u'Get optionVar values'
maya.stringTable['SnapTools.tbRelativeSnapSelectionOrder'] = u'Get optionVar values'
maya.stringTable['SnapTools.tbRelativeSnapConstraintMethod'] = u'Get optionVar values'
