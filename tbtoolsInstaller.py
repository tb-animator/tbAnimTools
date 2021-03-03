import pymel.core as pm
import os, stat
import sys
import inspect
import io


class module_maker():
    def __init__(self):
        self.colours = {'red': "color:#F05A5A;",
                        'green': "color:#82C99A;",
                        'yellow': "color:#F4FA58;"
                        }
        self.win_versions = ['win32', 'win64'][pm.about(is64=True)]
        self.maya_version = pm.about(version=True)
        self.filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) +"\\"  # script directory
        self.python_paths = ['apps', 'lib', '']
        self.maya_script_paths = ['scripts']
        self.xbmlang_paths = ['Icons']
        self.out_lines = []
        self.module_file = 'tbAnimTools.mod'
        self.module_template = os.path.join(self.filepath, self.module_file)
        self.current_module_data = None

    def maya_module_dir(self):
        return os.path.join(pm.internalVar(userAppDir=True) + "modules\\")

    def module_path(self):
        return os.path.join(self.maya_module_dir(), self.module_file)

    def make_module_path_data(self):
        module_path = '+ PLATFORM:' \
                      + self.win_versions \
                      + ' MAYAVERSION:' \
                      + self.maya_version \
                      + ' tbtools 1.0 ' \
                      + self.filepath + '\\'
        return module_path

    def make_module_data(self):
        self.out_lines = ['\n']
        self.out_lines.append(self.make_module_path_data())
        for paths in self.python_paths:
            self.out_lines.append('PYTHONPATH+:='+paths)
        for paths in self.maya_script_paths:
            self.out_lines.append('MAYA_SCRIPT_PATH+:='+paths)
        for paths in self.xbmlang_paths:
            self.out_lines.append('XBMLANGPATH+:='+paths)

    def write_module_file(self):
        self.read_module_file()
        # mod_file = self.maya_module_dir + "\\" + self.module_file
        # shutil.copyfile(self.module_template, mod_file)
        if not self.current_module_data:
            return cmds.error('no module data to write')
        if os.access(os.path.join(self.module_path()), os.W_OK):
            with io.open(self.module_path(), 'w') as f:
                f.writelines(line + u'\n' for line in self.current_module_data)
                return True
                io.close(self.module_path())
        else:
            return False

    def read_module_file(self):
        print 'read_module_file'
        if os.path.isfile(self.module_path()):
            f = open(self.module_path(), 'r')
            self.current_module_data = f.read().splitlines()
            match = False
            f.close()
            for lineIndex, line in enumerate(self.current_module_data):
                if 'PLATFORM:%s' % self.win_versions and 'MAYAVERSION:%s' % self.maya_version in line:
                    match = True
                    self.current_module_data[lineIndex] = self.make_module_path_data()
            if not match:
                # create a new entry
                print 'making new entry'
                self.make_module_data()
                print 'current_module_data', self.current_module_data
                self.current_module_data.extend(self.out_lines)
                print self.current_module_data

    def replace_path(self, fileName, path, newpath):
        f = open(fileName,'r')
        filedata = f.read()
        f.close()

        newdata = filedata.replace(path, newpath)

        f = open(fileName, 'w')
        f.write(newdata)
        f.close()

    def check_module_file(self):
        # file doesn't exist yet so create one
        print 'checking module file'

        if not os.path.isfile(self.module_path()):
            print self.module_path(), 'not found, creating it'
            f = open(str(self.module_path()), 'a+')  # open file in append mode
            f.writelines('')
            f.close()
        if os.path.isfile(self.module_path()):
            os.chmod(self.module_path(), stat.S_IWRITE)
            return False
        else:
            return True

    def make_module_folder(self):
        print 'make_module_folder'
        if not os.path.isdir(self.maya_module_dir()):
            print "making new maya module folder"
            os.mkdir(self.maya_module_dir())
        else:
            print "setting module folder to writeable"
            os.chmod(self.maya_module_dir(), stat.S_IWRITE)

    def install(self):
        # create module folder if not existing
        self.make_module_folder()

        # create module file if not existing
        state = self.check_module_file()

        self.write_module_file()

        result_message = "<h3>Installation result</h3>\t\n"

        if not state:
            result_message += "module file created <span style=\""+self.colours['green']+ "\">Successfully</span> \n"
            result_message += "module file location <span style=\""+self.colours['yellow']+ "\">" \
                              + self.module_path() + "</span>\n\nEnjoy!"
            self.result_window()
        else:
            result_message += "<span style=\""+self.colours['red']+"<h3>WARNING</h3></span> :module file not created\n"

        message_state = pm.optionVar.get("inViewMessageEnable", 1)
        pm.optionVar(intValue=("inViewMessageEnable", 1))
        pm.inViewMessage(amg=result_message,
                         pos='botRight',
                         dragKill=True,
                         fadeOutTime=2.0,
                         fade=True)
        pm.optionVar(intValue=("inViewMessageEnable", message_state))

    def result_window(self):
        if pm.window("installWin", exists=True):
            pm.deleteUI("installWin")
        window = pm.window( title="success!")
        layout = pm.columnLayout(adjustableColumn=True )
        pm.text(font="boldLabelFont",label="tbtools installed")
        pm.text(label="")
        pm.text(label="please restart maya for everything to load")

        pm.button( label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        pm.setParent('..')
        pm.showWindow(window)

class installer():
    filepath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "\\"  # script directory
    iconPath = os.path.join(filepath, 'Icons')
    appPath = os.path.join(filepath, 'apps')
    colours = {'red': "color:#F05A5A;",
               'green': "color:#82C99A;",
               'yellow': "color:#F4FA58;"
               }

    def __init__(self):
        pass

    def install(self):
        try:
            self.clearMultipleSysPaths()
            if self.filepath not in sys.path:
                sys.path.append(self.filepath)
            if self.iconPath not in sys.path:
                sys.path.append(self.iconPath)
            if self.appPath not in sys.path:
                sys.path.append(self.appPath)

            import module_startup
            module_startup.initialise().load_everything()
            import tb_messages
            tb_messages.info(prefix=' INSTALLATION',
                             message=' : Success',
                             fadeStayTime=5,
                             fadeOutTime=5,
                             fade=True,
                             position='botRight')
        except:
            pm.warning('installation failed')

    def clearMultipleSysPaths(self):
        if self.filepath in sys.path:
            sys.path.remove(self.filepath)
        if self.iconPath in sys.path:
            sys.path.remove(self.iconPath)
        if self.appPath in sys.path:
            sys.path.remove(self.appPath)

    def result_window(self):
        if pm.window("installWin", exists=True):
            pm.deleteUI("installWin")
        window = pm.window(title="success!")
        layout = pm.columnLayout(adjustableColumn=True)
        pm.text(font="boldLabelFont", label="tbtools installed")
        pm.text(label="")
        pm.button(label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)'), parent=layout)
        pm.setParent('..')
        pm.showWindow(window)


module_maker().install()
installer().install()
