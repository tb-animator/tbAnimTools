# utils.py

import functools



def create_callback(func, *args, **kwargs):
    """
    Create a callback function that can be used in Maya cmds commands.

    Parameters:
        func (function): The function to be called.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        function: A callable function that can be used as a callback.
    """

    return functools.partial(func, *args, **kwargs)
