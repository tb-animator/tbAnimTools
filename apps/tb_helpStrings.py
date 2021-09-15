tbAnimTools = 'tbAnimTools'
category = {'snap': '%s_Snaps' % tbAnimTools,
            'spaceSwitch': '%s_SpaceSwitch' % tbAnimTools,
            'layers': '%s_AnimLayers' % tbAnimTools,
            'view': '%s_Viewport' % tbAnimTools,
            'timeline': '%s_TimeSlider' % tbAnimTools,
            'selection': '%s_Selection' % tbAnimTools,
            'motionTrails': '%s_MotionTrails' % tbAnimTools,
            'cameras': '%s_Cameras' % tbAnimTools,
            'gravity': '%s_Gravity' % tbAnimTools,
            'manipulators': '%s_Manipulators' % tbAnimTools,
            'keying': '%s_Keyframe' % tbAnimTools,
            'sliders': '%s_Sliders' % tbAnimTools,
            'tempPivot': '%s_TempPivot' % tbAnimTools,
            'pickwalk': '%s_Pickwalk' % tbAnimTools,
            'constraints': '%s_Constraints' % tbAnimTools,
            'footpath': '%s_FootPath' % tbAnimTools,
            'ikfk': '%s_IKFK' % tbAnimTools,
            }
quickMergeSelectionToNew = ['Fast bake currently selected objects to a new layer']
quickMergeSelectionToBase = ['Fast bake currently selected objects to the base layer']
simpleBakeToOverride = ['bake current selection to an override layer']
quickCreateAdditiveLayer = ['create a new additive layer, selection is', 'added to the layer']
quickCreateOverrideLayer = ['create a new override layer, selection is', 'added to the layer']
counterAnimLayer = ['creates an additive layer which will counter',
                    'the animation in the selected layer.',
                    'Tast selected object is the driver,',
                    'other objects will be baked into an additive',
                    'layer that fully counter animates the selected layer.']
bakeToLocator = ['bake current selection to world space locators']

cycleTranslateMode = ['Cycle the translate manipulator mode', 'between user defined modes']
cycleRotateMode = ['Cycle the rotate manipulator mode ', 'between user defined modes']
cycleCurrentMode = ['Cycle the current manipulator mode', ' between user defined modes']

OpenPickwalkCreator = ['Open the pickwalk creation UI']
OpenPickwalkLibrary = ['Open the pickwalk map assignment UI']
toggleMotionTrail = ['Toggles motion trail states',
                     'Creates a motion trail if needed',
                     'If nothing is selected, all trails are toggled on/off',
                     'If nodes are selected, trails are toggled on/off based on current state',
                     'Automatically added to the currently isolated selection']
createMotionTrail = ['Creates a motion trail set to the current timeline',
                     'Automatically added to the currently isolated selection']
createCameraRelativeMotionTrail = ['Creates a motion trail set to the current timeline',
                                   'Automatically added to the currently isolated selection',
                                   'Trail is relative to the current canera']
toggleMotionTrailCameraRelative = ['Toggles the currently selected trail, or trails associated with a control',
                                   'to be world space or camera relative',
                                   'If nothing is selected, all motion trails are toggled']
removeMotionTrail = ['Removes motion trails connected to selection']

gravity = {'quickJump': ['Uses the highlighted time slider range to plot',
                         'a ballistic arc between the start and end positions'],
           'jumpAllKeyWindows': ['Uses pairs of keys to plot multiple jump arcs',
                                 'using the highlighted time slider range'],
           'jumpUsingInitialFrameVelocity': ['Plots a ballistic arc for the duration of the highlighted',
                                             'time slider range using the first frames velocity']}
