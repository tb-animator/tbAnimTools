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

import maya.cmds as cmds

# translation
translate_modes = ['Object', 'Local', 'World', 'Normal',
                   'RotationAxis', 'LiveAxis', 'CustomAxis']
translate_modesDict = {'Object': 0,
                       'Local': 1,
                       'World': 2,
                       'Normal': 3,
                       'RotationAxis': 4,
                       'LiveAxis': 5,
                       'CustomAxis': 6}
translate_optionVar = "translate_modes"
translate_messageVar = "tb_cycle_translation_msg_pos"
translate_messageLabel = "message position"
# rotation
rotate_modes = ['Local', 'World', 'Gimbal', 'Custom axis', 'Component space']
rotate_modesDict = {'Local': 0,
                    'World': 1,
                    'Gimbal': 2,
                    'Custom axis': 3,
                    'Component space': 9}
rotate_optionVar = "rotate_modes"
rotate_messageVar = "tb_cycle_rotation_msg_pos"
rotate_messageLabel = "message position"
# selection mask
selection_modes = ['All', 'Controls']
selection_optionVar = "tb_cycle_selection"
rotate_messageVar = "tb_cycle_selection_msg_pos"
# key types
key_modes = ["spline", "linear", "clamped", "step", "flat", "plateau", "auto", 'autoease', 'automix']
key_optionVar = "tb_cycle_keytype"
key_messageVar = "tb_cycle_keytype_msg_pos"
key_messageLabel = "message position"

def cycleOption(option_name="", full_list=[], current=int(), default=""):
    # get list from optionvar array
    optionVar_list = get_option_var(option_name, [default])

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
        #print ("current value not in option var list, set to first")
        name = optionVar_list[0]
    index = full_list.index(name)
    return index, name

def cycleCurrentOption(optionVar_list="", full_list=[], current=str(), default=""):
    # get list from optionvar array
    '''
    print ('optionlist', optionVar_list, current)
    print ('full_list', full_list)
    '''
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
        #print ("current value not in option var list, set to first")
        name = optionVar_list[0]
    index = full_list.index(name)
    return index, name

def set_default_values():
    if get_option_var('tb_firstRun', True):
        set_option_var(translate_optionVar + "_msg", 1)
        set_option_var(translate_messageVar + "_msg", 'topLeft')

        set_option_var(rotate_optionVar + "_msg", 1)
        set_option_var(rotate_messageVar + "_msg", 'topLeft')

        set_option_var(key_optionVar + "_msg", 1)
        set_option_var(key_messageVar + "_msg", 'topLeft')

        default_moves = ['Object', 'Local', 'World']
        delete_option_var(translate_optionVar)
        for modes in default_moves:
            set_option_var(translate_optionVar, modes)

        default_rotations = ['Local', 'World', 'Gimbal']
        set_option_var(rotate_optionVar, default_rotations)

        default_keys = ['spline', 'linear', 'step']
        delete_option_var(key_optionVar)
        set_option_var(key_optionVar, default_keys)
        return True
    else:
        return False



def get_option_var(var_name, default=None):
    """
    Get the value of an option variable.

    Parameters:
    - var_name (str): The name of the option variable.
    - default (any): The default value to return if the option variable does not exist.

    Returns:
    - The value of the option variable or the default value.
    """
    if cmds.optionVar(exists=var_name):
        return cmds.optionVar(q=var_name)
    return default


def set_option_var(var_name, value, *args):
    """
    Set the value of an option variable.

    Parameters:
    - var_name (str): The name of the option variable.
    - value (any): The value to set for the option variable.
    """
    if isinstance(value, int):
        cmds.optionVar(iv=(var_name, value))
    elif isinstance(value, float):
        cmds.optionVar(fv=(var_name, value))
    elif isinstance(value, str):
        cmds.optionVar(sv=(var_name, value))
    elif isinstance(value, list):
        if all(isinstance(item, int) for item in value):
            cmds.optionVar(clearArray=var_name)
            for item in value:
                cmds.optionVar(iva=(var_name, item))
        elif all(isinstance(item, float) for item in value):
            cmds.optionVar(clearArray=var_name)
            for item in value:
                cmds.optionVar(fva=(var_name, item))
        elif all(isinstance(item, str) for item in value):
            cmds.optionVar(clearArray=var_name)
            for item in value:
                cmds.optionVar(sva=(var_name, item))
    else:
        cmds.optionVar(sv=(var_name, str(value)))


def delete_option_var(var_name):
    """
    Delete an option variable.

    Parameters:
    - var_name (str): The name of the option variable.
    """
    if cmds.optionVar(exists=var_name):
        cmds.optionVar(remove=var_name)

def format_arg(val):
    """Encapsulate strings in quotes, leave other types as-is."""
    return f"'{val}'" if isinstance(val, str) else str(val)
def decodePartial(partial_func):
    original_func = partial_func.func.__name__
    args = ", ".join(format_arg(arg) for arg in partial_func.args)
    kwargs = ", ".join(f"{k}={format_arg(v)}" for k, v in partial_func.keywords.items())

    # Reconstruct the function call as a string
    command_string = f"cmds.{original_func}({args}{', ' if args and kwargs else ''}{kwargs})"

    # Wrap it in MEL syntax
    mel_command = f'python("{command_string}");'
    return mel_command

def addRepeatLast(partial_func):
    commandString = decodePartial(partial_func)
    cmds.repeatLast(addCommand=commandString, addCommandLabel=commandString)