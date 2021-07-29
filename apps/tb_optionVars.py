'''TB Animation Tools is a toolset for animators

*******************************************************************************
    License and Copyright
    Copyright 2020-Tom Bailey
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    send issues/ requests to brimblashman@gmail.com
    visit https://tbanimtools.blogspot.com/ for "stuff"


*******************************************************************************
'''
import pymel.core as pm

class optionVar_utils(object):
    def __init__(self):
        pass

    @staticmethod
    def set_option_var(variable, value):
        pm.optionVar(stringValue=(variable, value))


    @staticmethod
    def get_option_var(variable):
        if not pm.optionVar[variable]:
            pm.optionVar(stringValue=(variable, "None"))
        return pm.optionVar.get(variable, False)

    @staticmethod
    # list from option var
    def cycleOption(option_name="", full_list=[], current=int(), default=""):
        # get list from optionvar array
        optionVar_list = pm.optionVar.get(option_name, [default])
        print ('optionlist', optionVar_list, current)
        print ('full_list', full_list)
        print ('rotateMode', pm.manipRotateContext('Rotate', query=True, mode=True))
        if not optionVar_list:
            optionVar_list = [default]
        # find the current index in the full list
        if current < len(full_list):
            current_name = full_list[current]
        else:
            current_name = full_list[0]

        # check if the current name is in our option var list
        if current_name in optionVar_list:
            index = optionVar_list.index(current_name) + 1
            # loop around the list
            name = optionVar_list[index % len(optionVar_list)]

        else:
            print ("current value not in option var list, set to first")
            name = optionVar_list[0]
        index = full_list.index(name)
        return index, name

    @staticmethod
    # list from option var
    def cycleCurrentOption(optionVar_list="", full_list=[], current=str(), default=""):
        # get list from optionvar array

        print ('optionlist', optionVar_list, current)
        print ('full_list', full_list)
        print ('rotateMode', pm.manipRotateContext('Rotate', query=True, mode=True))
        if not optionVar_list:
            optionVar_list = [default]
        # find the current index in the full list
        if current < len(full_list):
            current_name = full_list[current]
        else:
            current_name = full_list[0]

        # check if the current name is in our option var list
        if current_name in optionVar_list:
            index = optionVar_list.index(current_name) + 1
            # loop around the list
            name = optionVar_list[index % len(optionVar_list)]

        else:
            print ("current value not in option var list, set to first")
            name = optionVar_list[0]
        index = full_list.index(name)
        return index, name

def set_default_values():
    if pm.optionVar.get('tb_firstRun', True):
        from tb_manipulators import Manipulators
        print ("setting up default option vars for first run")

        pm.optionVar(intValue=(Manipulators().translate_optionVar + "_msg", 1))
        pm.optionVar(stringValue=(Manipulators().translate_messageVar + "_msg", 'topLeft'))

        pm.optionVar(intValue=(Manipulators().rotate_optionVar + "_msg", 1))
        pm.optionVar(stringValue=(Manipulators().rotate_messageVar + "_msg", 'topLeft'))

        pm.optionVar(intValue=(Manipulators().key_optionVar + "_msg", 1))
        pm.optionVar(stringValue=(Manipulators().key_messageVar + "_msg", 'topLeft'))

        default_moves = ['Object', 'Local', 'World']
        pm.optionVar.pop(Manipulators().translate_optionVar)
        for modes in default_moves:
            pm.optionVar(stringValueAppend=(Manipulators().translate_optionVar, modes))

        default_rotations = ['Local', 'World', 'Gimbal']
        pm.optionVar.pop(Manipulators().rotate_optionVar)
        for modes in default_rotations:
            pm.optionVar(stringValueAppend=(Manipulators().rotate_optionVar, modes))

        default_keys = ['spline', 'linear', 'step']
        pm.optionVar.pop(Manipulators().key_optionVar)
        for modes in default_keys:
            pm.optionVar(stringValueAppend=(Manipulators().key_optionVar, modes))
        return True
    else:
        return False
