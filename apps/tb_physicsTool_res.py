import maya

maya.stringTable['y_tb_physicsTool.errorNoParent'] = 'Cannot add single node with no parent. <br>' \
                                                        'The tool requires the first collision control to have a ' \
                                                        'parent node. The parent node should be at the same location ' \
                                                        'as the collision control.'
maya.stringTable['y_tb_physicsTool.errorNoParentTitle'] = 'Error adding element'

maya.stringTable['y_tb_physicsTool.groupCombo'] = 'Choose the type of surface for the group to be added.<br>' \
                                                     'The type can be changed later.'
maya.stringTable['y_tb_physicsTool.addChain'] = 'Add chain tooltip'
maya.stringTable['y_tb_physicsTool.addPoint'] = 'Add point tooltip'
maya.stringTable['y_tb_physicsTool.create'] = 'create'
maya.stringTable['y_tb_physicsTool.saveCurrentPosesButtonLabel'] = 'Save All Collision Object Poses'
maya.stringTable['y_tb_physicsTool.saveCurrentPosesToolTip'] = 'Save All Collision Object Poses'
maya.stringTable['y_tb_physicsTool.saveSelectedPosesToolTip'] = 'Restore All Collision Object Poses'
maya.stringTable['y_tb_physicsTool.saveSelectedPosesButtonLabel'] = 'Restore All Collision Object Poses'
maya.stringTable['y_tb_physicsTool.deleteGroup'] = "Delete group and all it's contents"

maya.stringTable['y_tb_physicsTool.addChainLabel'] = 'Add Chain'
maya.stringTable[
    'y_tb_physicsTool.addChainToolTip'] = 'Add a separate collision entry for every control selected<br> Use for tails etc.'
maya.stringTable['y_tb_physicsTool.addFingerLabel'] = 'Add Finger'
maya.stringTable[
    'y_tb_physicsTool.addFingerEntryToolTip'] = 'Add one or more finger style fk collision entries<br> Hierarchy will be automatically detected.'

maya.stringTable['y_tb_physicsTool.AddNewGroupPopupText'] = 'Each collision group has it\'s own floor plane. <br>' \
                                                               'Good practice is to add one per hand and foot.<br>' \
                                                               'When adding a group with an object selected, this ' \
                                                               'popup <b>will not appear</b> and the selected object ' \
                                                               'will be used for the group name.'
maya.stringTable['y_tb_physicsTool.AddNewGroupHelpTitle'] = 'Adding new collision groups'
maya.stringTable['y_tb_physicsTool.AddNewGroupHelpImage'] = 'save current'
maya.stringTable['y_tb_physicsTool.AddNewGroupIsGif'] = False
maya.stringTable['y_tb_physicsTool.AddNewGroupHelp'] = 'A collision group is a collection of fk collision elements, ' \
                                                          'all sharing the same surface / ground plane object. <br>' \
                                                          'Pick your surface type from the drop down, your choice can ' \
                                                          'be changed after adding the group. <br><br>' \
                                                          '<b>Simple Plane:</b><br>' \
                                                          '<div>Simple plane collision uses an infinite plane for your ' \
                                                          'fk collision. Only the position and rotation of the plane ' \
                                                          'will affect the collision result. Manipulating the surface ' \
                                                          'of the nurbs plane will have no effect.</div>' \
                                                          '<br><br>' \
                                                          '<b>Plane / Sphere / Cylinder</b><br>' \
                                                          '<div>These modes will create a nurbs surface, which is deformable ' \
                                                          'in any way you see fit. The fk collision will attempt to ' \
                                                          'align to the closest point on the surface to your animated pose.</div>' \
                                                          '<br><br>' \
                                                          '<b>Once built, these modes can be changed via the UI, and surface object can be swapped out for others.</b>' \
                                                          ''

maya.stringTable['y_tb_physicsTool.AddNewElementHelpTitle'] = 'Adding new collision entries'
maya.stringTable['y_tb_physicsTool.AddNewElementHelpImage'] = 'save current'
maya.stringTable['y_tb_physicsTool.AddNewElementIsGif'] = False
maya.stringTable[
    'y_tb_physicsTool.AddNewElementHelp'] = 'A collision entry is a list of controls and intermediate nodes.<br> ' \
                                               'The topmost control must have a parent node at the same location. <br>' \
                                               'This parent node is where the topmost control will rotate from during collision. <br><br>' \
                                               '<b>Add Chain ::</b><br>' \
                                               '<div>Each control in your selection will be added in as a ' \
                                               'separate entry. Each selection must have a parent node at the same location ' \
                                               'to have the correct effect when colliding.' \
                                               '</div>' \
                                               '<br><br>' \
                                               '<b>Add Finger ::</b><br>' \
                                               '<div>Each distinct hierarchy in your selection will be added as separate' \
                                               'collision entry. For instance, all finger controls can be selected at once,' \
                                               ' the tool will sort them automatically. Only the topmost and bottom control need </div>' \
                                               'to be selected per digit, the tool will find the nodes in between.<br><br>' \
                                               '<b>The collision group type can be changed using the drop down list.</b>' \
                                               '<br><br>' \
                                               '<b>When adding a new entry, if any objects being added are present in other existing elements,' \
                                               ' those elements will be removed to prevent duplication, which would result in failure on creation.</b>' \
                                               ''

maya.stringTable['y_tb_physicsTool.CreateHelpTitle'] = 'Collision Creation'
maya.stringTable['y_tb_physicsTool.CreateHelpImage'] = 'save current'
maya.stringTable['y_tb_physicsTool.CreateIsGif'] = False
maya.stringTable[
    'y_tb_physicsTool.CreateHelp'] = '<b>Create ::</b><br><br> ' \
                                        'Use this button to create your collision setup currently displayed in the UI. ' \
                                        '<br>' \
                                        'The collision will be applied to the namespace of your selection at the time. ' \
                                        'With no selection, the collision will be applied to the root namespace. ' \
                                        '<br><br>' \
                                        'If all of the objects referenced in the current data cannot be found, the tool ' \
                                        'will raise an error and not create the collision objects.<br><br>' \
                                        '<b>Save All Collision Poses ::</b><br>' \
                                        '<div>This will store all found collision tip control transforms to a preset ' \
                                        'for the rig they are associated with. This data is associated with the ' \
                                        'referenced rig file. ' \
                                        'The offsets saved will be automatically applied to newly created collision ' \
                                        'with the same name in the future. <bv><br>' \
                                        '</div>' \
                                        '<br><br>' \
                                        '<b>Restore All Collision Object Poses</b><br>' \
                                        '<div>Restore all collision tip poses from saved data.' \
                                        '</div>' \
                                        '<br><br>' \
                                        ''

maya.stringTable['y_tb_physicsTool.createErrorNoDataTitle'] = 'Nothing to create'
maya.stringTable[
    'y_tb_physicsTool.createErrorNoData'] = 'No collision entries found, please add a group, and collision entry via the UI'
