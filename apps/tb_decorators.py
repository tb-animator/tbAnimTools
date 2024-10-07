# -----------------------------------------------------------------
#   REPEAT COMMAND
# -----------------------------------------------------------------

from . import *
_repeat_function = None
_args = None
_kwargs = None


def repeat_command():
    if _repeat_function is not None:
        _repeat_function(*_args, **_kwargs)

    def wrap(function):
        def wrapper(*args, **kwargs):
            global _repeat_function
            global _args
            global _kwargs

            _repeat_function = function
            _args = args
            _kwargs = kwargs

            commandToRepeat = ('python("%s.repeat_command()")' % __name__)

            ret = function(*args, **kwargs)

            cmds.repeatLast(addCommand=commandToRepeat, addCommandLabel=function.__name__)

            return ret

        return wrapper

    return wrap
