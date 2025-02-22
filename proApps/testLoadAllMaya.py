import subprocess
import sys
import os
import zipfile
import inspect, importlib
import py_compile
import maya.mel as mel
from Abstract import *
import shutil
toolDirectory = 'C:/AnimationWork/tbAnimTools/proApps'
baseDirectory = 'proApps'

stub = '_for_tbAnimTools_v'

initPyFile = 'C:/AnimationWork/tbAnimTools/proApps/zipBase/__init__.py'
compiledFolder = "C:/AnimationWork/compiledFiles"
appDict = {
    'tb_collisionTools': {
        'zipFile': 'tb_collisionTool',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_collisionTools.py",
                 "C:/AnimationWork/tbAnimTools/proApps/tb_collisionToolsMisc.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_collisionTools_res.py",
    },
    'tb_adjustmentBlend': {
        'zipFile': 'tb_adjustmentBlend',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_adjustmentBlend.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_adjustmentBlend_res.py",
    },

    'tb_physicsTools': {
        'zipFile': 'tb_physicsTools',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_physicsTool.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_physicsTool_res.py",
    },
    'tb_ikfkTools': {
        'zipFile': 'tb_ikfkTools',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_ikfkTools.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_ikfkTools_res.py",
    },
    'tb_phaseBakeTools': {
        'zipFile': 'tb_phaseBakeTools',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_phaseBake.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_phaseBake_res.py",
    },
    'tb_animatedPath': {
        'zipFile': 'tb_animatedPath',
        'file': ["C:/AnimationWork/tbAnimTools/proApps/tb_animatedPath.py"],
        'res_file': "C:/AnimationWork/tbAnimTools/proApps/tb_animatedPath_res.py",
    }
}

# 'tb_gimbalTools': {
#     'zipFile': 'tb_gimbalTools',
#     'file': "C:/AnimationWork/tbAnimTools/proApps/tbGimbalTools/tb_gimbalTools.py",
#     'res_file': "C:/AnimationWork/tbAnimTools/proApps/tbGimbalTools/tb_gimbalTools_res.py",
# },

def add_to_zip(zip_filename, files_to_add, path_inside_zip):
    print ("Adding to zip::", zip_filename)
    print ('    files_to_add', files_to_add)
    print ('    path_inside_zip', path_inside_zip)
    if not isinstance(files_to_add, list):
        files_to_add = [files_to_add]
    for file_to_add in files_to_add:
        if not os.path.isfile(file_to_add):
            return cmds.warning(f'file not found {file_to_add}')
        if not zip_filename.endswith('.zip'):
            zip_filename = zip_filename + '.zip'
        with zipfile.ZipFile(zip_filename, 'a') as zip_file:
            zip_file.write(file_to_add, arcname=path_inside_zip)

def collateZipFiles(key):
    print ('key', key)
    data = appDict.get(key, None)
    if not data:
        return cmds.warning('no data')

    fileData = getCompiledPyFiles(data['file'])
    print ('fileData', fileData)
    version = fileData['version']
    zipBase = data['zipFile']
    zipName = zipBase + stub + str(version)
    zipPath = os.path.join(compiledFolder, zipName)

    if not os.path.isfile(os.path.join(compiledFolder, zipName)):
        shutil.make_archive(zipPath, 'zip', initPyFile)

    add_to_zip(zipPath, initPyFile, 'python2\\__init__.py')
    add_to_zip(zipPath, initPyFile, 'python3\\__init__.py')
    add_to_zip(zipPath, initPyFile, 'python39\\__init__.py')
    add_to_zip(zipPath, initPyFile, 'python310\\__init__.py')
    add_to_zip(zipPath, initPyFile, 'python311\\__init__.py')

    print ('fileData')
    print (fileData['py27'])
    print (fileData['py37'])
    print (fileData['py39'])
    print (fileData['py310'])
    print (fileData['py311'])
    print (fileData['baseName'])

    for index, fileName in enumerate(fileData["baseName"]):
        add_to_zip(zipPath, fileData['py27'][index], f'python2\\{fileData["baseName"][index]}')
        add_to_zip(zipPath, fileData['py37'][index], f'python3\\{fileData["baseName"][index]}')
        add_to_zip(zipPath, fileData['py39'][index], f'python39\\{fileData["baseName"][index]}')
        add_to_zip(zipPath, fileData['py310'][index], f'python310\\{fileData["baseName"][index]}')
        add_to_zip(zipPath, fileData['py311'][index], f'python311\\{fileData["baseName"][index]}')

    add_to_zip(zipPath, initPyFile, '\\__init__.py')

    res_file = data.get('res_file', None)
    if res_file is not None:
        res_file_base = os.path.basename(res_file)
        add_to_zip(zipPath, res_file, f'python2\\{res_file_base}')
        add_to_zip(zipPath, res_file, f'python3\\{res_file_base}')
        add_to_zip(zipPath, res_file, f'python39\\{res_file_base}')
        add_to_zip(zipPath, res_file, f'python310\\{res_file_base}')
        add_to_zip(zipPath, res_file, f'python311\\{res_file_base}')


def getCompiledPyFiles(fileNames):
    value = str()
    if not isinstance(fileNames, list):
        fileNames = [fileNames]

    baseFile = list()
    baseNames = list()
    py27 = list()
    py37 = list()
    py39 = list()
    py310 = list()
    py311 = list()

    for fileName in fileNames:
        basePath = os.path.dirname(fileName)
        baseFile = os.path.basename(fileName.rsplit('.', 1)[0])
        subFolder = str(os.path.relpath(os.path.dirname(fileName), toolDirectory)).replace('\\', '.')
        print('baseFile', baseFile)
        # hacky check to see if the script is in the start folder
        if subFolder == '.':
            module_name = baseDirectory + '.' + baseFile
        else:
            module_name = baseDirectory + '.' + subFolder + '.' + baseFile
        # print ('folder', os.path.split(fileName))
        # print('FUCK', module_name)
        # print(inspect.getmembers(importlib.import_module(module_name), inspect.isclass))
        classes = getClasses(module_name)
        toolClasses = [cls for cls in classes if cls.__base__ == toolAbstractFactory]
        module = importlib.import_module(module_name)
        importlib.reload(module)

        if toolClasses:
            version = toolClasses[0].version
        else:
            main_variables = {name: obj for name, obj in inspect.getmembers(module)
                              if not inspect.isclass(obj) and not inspect.isfunction(obj)}

            if 'version' in main_variables:
                version = main_variables['version']
            else:
                return cmds.error('No version variable fount')
        # print(version)
        baseNames.append(baseFile + '.pyc')
        py27.append(fileName.replace('.py', '.pyc'))
        py37.append(os.path.join(basePath, '__pycache__\\' + baseFile + '.cpython-37.pyc'))
        py39.append(os.path.join(basePath, '__pycache__\\' + baseFile + '.cpython-39.pyc'))
        py310.append(os.path.join(basePath, '__pycache__\\' + baseFile + '.cpython-310.pyc'))
        py311.append(os.path.join(basePath, '__pycache__\\' + baseFile + '.cpython-311.pyc'))

    return {'version': version,
            'baseName': baseNames,
            'py27': py27,
            'py37': py37,
            'py39': py39,
            'py310': py310,
            'py311': py311,
            }


def getClasses(module_name):
    for name, cls in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
        if cls.__module__ == module_name:
            yield cls


def loadAll():
    DETACHED_PROCESS = 0x00000008
    MAYA_LOCATIONS = [
        "C:/Program Files/Autodesk/Maya2020/bin",
        "C:/Program Files/Autodesk/Maya2022/bin",
        "C:/Program Files/Autodesk/Maya2023/bin",
        "C:/Program Files/Autodesk/Maya2024/bin",
        "C:/Program Files/Autodesk/Maya2025/bin",
    ]

    for MAYA_LOCATION in MAYA_LOCATIONS:
        sys.path.append(MAYA_LOCATION)

        mayaPath = "mayapy.exe"
        scriptPath = "C:\\AnimationWork\\tbAnimTools\\proApps\\" + "testCompile.py"
        thePath = "C:\\AnimationWork\\tbAnimTools\\proApps\\"
        fileList = ['testNameA', 'testNameB']
        # for f in os.listdir(thePath):
        #     if f.endswith(".py"):
        #         fileList.append(os.path.join(thePath, f))

        strFileList = ','.join(fileList)
        outputDir = "C:\\AnimationWork"
        # scriptPath = r"C:/Users/Tom/AppData/Roaming/JetBrains/PyCharmCE2022.2/scratches/mayaPyScratch.py"
        print('mayaPath', mayaPath)
        command = '"{mayapy}" "{script}" "{files}" "{output}"'.format(mayapy=MAYA_LOCATION + '/' + mayaPath,
                                                                      script=scriptPath,
                                                                      files=strFileList,
                                                                      output=outputDir)

        process = subprocess.Popen(command,
                                   shell=False,
                                   stdout=None,
                                   stderr=None,
                                   universal_newlines=True,
                                   # creationflags=DETACHED_PROCESS
                                   )
        sys.path.remove(MAYA_LOCATION)
        process.wait()

def collateAll(key=None):
    if key is None:
        for k in appDict.keys():
            collateZipFiles(k)
    else:
        collateZipFiles(key)

