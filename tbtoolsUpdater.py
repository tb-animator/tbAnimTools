import urllib2
import json
import datetime
import shutil
import os
import pymel.core as pm
import zipfile
from distutils.dir_util import copy_tree

import getStyleSheet as getqss
from apps.tb_UI import *

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from pyside2uic import *
    from shiboken2 import wrapInstance


class updater():
    def __init__(self):
        self.datUrl = 'https://api.github.com/repos/tb-animator/tbAnimTools'
        self.master_url = 'https://raw.githubusercontent.com/tb-animator/tbtools/master/'
        self.latestZip = 'https://github.com/tb-animator/tbAnimTools/archive/refs/heads/main.zip'
        self.realPath = os.path.realpath(__file__)
        self.basename = os.path.basename(__file__)
        self.base_dir = os.path.normpath(os.path.dirname(__file__))
        if not os.path.isdir(os.path.join(self.base_dir, 'appData')):
            os.mkdir(os.path.join(self.base_dir, 'appData'))
        self.versionDataFile = os.path.join(self.base_dir, 'appData', 'tbVersion.json')
        self.dateFormat = '%Y-%m-%dT%H:%M'
        self.uiDateFormat = '%Y-%m-%d'
        self.timeFormat = '%H:%M'
        if not os.path.isfile(self.versionDataFile):
            self.save((datetime.datetime.now() - datetime.timedelta(days=365)))
        self.jsonProjectData = json.load(open(self.versionDataFile))
        self.currentVersion = self.convertDateFromString(self.jsonProjectData['version'])

    def save(self, version):
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)

        jsonObjectInfo['version'] = version.strftime(self.dateFormat)
        j = json.dumps(jsonObjectInfo, indent=4, separators=(',', ': '))
        f = open(self.versionDataFile, 'w')
        print >> f, j
        f.close()

    def convertDateFromString(self, date_time):
        try:
            datetime_str = datetime.datetime.strptime(date_time, self.dateFormat)
        except:
            datetime_str = datetime.datetime.strptime(date_time, self.uiDateFormat)
        return datetime_str

    def check_version(self):
        response = urllib2.urlopen(self.datUrl)
        data = json.load(response)
        lastPush = datetime.datetime.strptime(data.get('pushed_at')[0:16], self.dateFormat)
        if lastPush > self.currentVersion:
            lastPushDay = lastPush.strftime(self.uiDateFormat)
            lastPushTime = lastPush.strftime(self.timeFormat)

            currentVersionDay = self.currentVersion.strftime(self.uiDateFormat)
            currentVersionTime = self.currentVersion.strftime(self.timeFormat)

            updateWin = UpdateWin(newVersion=lastPushDay + ' ' + lastPushTime,
                                  oldVersion=currentVersionDay + ' ' + currentVersionTime,
                                  updateText='Looks like there is a newer version of tbAnimTools available. Would you like to download the latest scripts?')
            if updateWin.exec_() != 1:
                return
            self.download_project_files()
            self.save(lastPush)

    def get_url_dir(self, dir):
        out = dir.replace(self.base_dir, self.master_url).replace("\\", "/")
        return out

    def download_project_files(self):
        print "downloading zip file to", self.base_dir
        filedata = urllib2.urlopen(self.latestZip)
        datatowrite = filedata.read()
        zipFile = os.path.join(self.base_dir, 'tbAnimToolsLatest.zip')
        with open(zipFile, 'wb') as f:
            f.write(datatowrite)

        destinationPath = os.path.normpath(os.path.join(self.base_dir, 'extract'))
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(destinationPath)
        destinationPathFinal = os.path.normpath(os.path.join(self.base_dir))

        copy_tree(os.path.join(destinationPath, 'tbAnimTools-main'), destinationPathFinal)

        message_state = pm.optionVar.get("inViewMessageEnable", 1)
        pm.optionVar(intValue=("inViewMessageEnable", 1))
        pm.inViewMessage(amg='tbAnimTools update complete',
                         pos='botRight',
                         dragKill=True,
                         fadeOutTime=10.0,
                         fade=False)
        pm.optionVar(intValue=("inViewMessageEnable", message_state))

    def CopyFolder(in_fold, out_fold):
        copy_tree(in_fold, out_fold)
