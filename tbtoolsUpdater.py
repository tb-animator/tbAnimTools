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
    visit https://tbanimtools.blogspot.com/ for "more info"

    usage


*******************************************************************************
'''
from __future__ import absolute_import
from __future__ import print_function
import sys
if sys.version_info >= (2, 8):
    from urllib.request import *
else:
    from urllib2 import *

import json
import datetime
import zipfile
from distutils.dir_util import copy_tree

from apps.tb_UI import *

qtVersion = pm.about(qtVersion=True)
if int(qtVersion.split('.')[0]) < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    #from pysideuic import *
    from shiboken import wrapInstance
else:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    #from pyside2uic import *
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
        self.data = self.getGithubData()
        self.lastPush = datetime.datetime.strptime(self.data.get('pushed_at')[0:16], self.dateFormat)
        if not os.path.isfile(self.versionDataFile):
            self.save(self.lastPush)
        self.jsonProjectData = json.load(open(self.versionDataFile))
        self.currentVersion = self.convertDateFromString(self.jsonProjectData['version'])

    def save(self, version):
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)

        jsonObjectInfo['version'] = version.strftime(self.dateFormat)
        j = json.dumps(jsonObjectInfo, indent=4, separators=(',', ': '))
        f = open(self.versionDataFile, 'w')
        f.write(j)
        f.close()


    def convertDateFromString(self, date_time):
        try:
            datetime_str = datetime.datetime.strptime(date_time, self.dateFormat)
        except:
            datetime_str = datetime.datetime.strptime(date_time, self.uiDateFormat)
        return datetime_str

    def check_version(self):
        print ('lastPush', self.lastPush)
        print ('currentVersion', self.currentVersion)
        if self.lastPush > self.currentVersion:
            lastPushDay = self.lastPush.strftime(self.uiDateFormat)
            lastPushTime = self.lastPush.strftime(self.timeFormat)

            currentVersionDay = self.currentVersion.strftime(self.uiDateFormat)
            currentVersionTime = self.currentVersion.strftime(self.timeFormat)

            updateWin = UpdateWin(newVersion=lastPushDay + ' ' + lastPushTime,
                                  oldVersion=currentVersionDay + ' ' + currentVersionTime,
                                  updateText='Looks like there is a newer version of tbAnimTools available. Would you like to download the latest scripts?')
            if updateWin.exec_() != 1:
                return
            self.download_project_files()
            self.save(self.lastPush)

    def getGithubData(self):
        response = urlopen(self.datUrl)
        data = json.load(response)
        return data

    def get_url_dir(self, dir):
        out = dir.replace(self.base_dir, self.master_url).replace("\\", "/")
        return out

    def download_project_files(self):
        print("downloading zip file to", self.base_dir)
        filedata = urlopen(self.latestZip)
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
