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
            'pickwalk': '%s_Pickwalk' % tbAnimTools,
            'constraints': '%s_Constraints' % tbAnimTools,
            'footpath': '%s_FootPath' % tbAnimTools,
            }
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
createMotionTrail = ['Creates a motion trail set to the current timeline',
                     'Automatically added to the currently isolated selection']
removeMotionTrail = ['Removes motion trails connected to selection']

gravity = {'quickJump': ['Uses the highlighted time slider range to plot',
                         'a ballistic arc between the start and end positions'],
           'jumpAllKeyWindows': ['Uses pairs of keys to plot multiple jump arcs',
                                 'using the highlighted time slider range'],
           'jumpUsingInitialFrameVelocity': ['Plots a ballistic arc for the duration of the highlighted',
                                             'time slider range using the first frames velocity']}
