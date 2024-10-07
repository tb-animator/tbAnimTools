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
import ssl

import maya.cmds as cmds

qtVersion = cmds.about(qtVersion=True)
QTVERSION = int(qtVersion.split('.')[0])
if QTVERSION < 5:
    from PySide.QtGui import *
    from PySide.QtCore import *
    # from pysideuic import *
    from shiboken import wrapInstance

elif QTVERSION < 6:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    # from pyside2uic import *
    from shiboken2 import wrapInstance
else:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    # from pyside2uic import *
    from shiboken6 import wrapInstance

import getStyleSheet as getqss
import os
from functools import partial
from apps.tb_optionVars import *
IconPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Icons'))
baseIconFile = 'checkBox.png'

"""
response = urlopen(data['releases_url'].split('{')[0])
data2 = json.load(response)
print data2[0]['tag_name'] - should be latest release
# TODO swap everyone to release update, show ui telling them
"""
'''

urlList = [
'https://github.com/tb-animator/tbAnimTools/archive/6552f653e6a0c4a1cedc05f0374c148cdbcf1f0e.zip',
'https://github.com/tb-animator/tbAnimTools/archive/cbc27c08e880df22756542677acd48a604fde76c.zip',
'https://github.com/tb-animator/tbAnimTools/archive/31a7f1ac4b9d2d916474f08ad3251f7e37c0f278.zip',
'https://github.com/tb-animator/tbAnimTools/archive/5bc584377d5cf0903c3b8cff97dde3d732fdc3df.zip',
'https://github.com/tb-animator/tbAnimTools/archive/48ad70d735ae2a77b5d44413041f471da3fdeaf7.zip',
'https://github.com/tb-animator/tbAnimTools/archive/c46830bf6acc52179c7fe9556eedafa92a4168a0.zip',
'https://github.com/tb-animator/tbAnimTools/archive/a4a67baec9b7643985f65d9598b0f49656fcf754.zip',
'https://github.com/tb-animator/tbAnimTools/archive/a6d54bf49388a359c92be252b525dc368cd9327f.zip',
'https://github.com/tb-animator/tbAnimTools/archive/57facb18c4c29716088df66151038299502bb978.zip'
]
commentList = [
'Pickwalk ui update, also changing the data method, removing prints',
'comment Pickwalk ui update, also changing the data method',
'comment Pickwalk ui update, also changing the data method',
'comment pickwak wip',
'comment placeholder folders',
'comment Reversing selection order on temp pivot tool',
'comment Fiddling with import order for ui elements',
'comment Slightly better handling of mirrored quick selection sets',
'comment Allowing noise to work better on unitless anim curves'
]
'''

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

def set_option_var(var_name, value):
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
        raise ValueError("Unsupported value type: {}".format(type(value)))

def dpiScale():
    if not get_option_var('tbUseWindowsScale', True):
        return QApplication.primaryScreen().logicalDotsPerInch() / 96.0
    return get_option_var('tbCustomDpiScale', 1)


def get_commit_details(repo_owner, repo_name):
    url = "https://api.github.com/repos/{repo_owner}/{repo_name}/commits".format(repo_owner=repo_owner,
                                                                                 repo_name=repo_name)

    with urlopen(url) as response:
        data = response.read().decode('utf-8')
        commits = json.loads(data)
    return commits


def get_commit_comments_and_files(repo_owner, repo_name, commit_sha):

    url = "https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}".format(repo_owner=repo_owner,
                                                                                              repo_name=repo_name,
                                                                                              commit_sha=commit_sha)
    # url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}"
    with urlopen(url) as response:
        data = response.read().decode('utf-8')
        commit_details = json.loads(data)
    comment = commit_details['commit']['message']
    files_changed = [file['filename'] for file in commit_details['files']]
    return comment, files_changed


def download_commit_zip(repo_owner, repo_name, commit_sha):
    url = "https://github.com/{repo_owner}/{repo_name}/archive/{commit_sha}.zip".format(repo_owner=repo_owner,
                                                                                        repo_name=repo_name,
                                                                                        commit_sha=commit_sha)
    # url = f"https://github.com/{repo_owner}/{repo_name}/archive/{commit_sha}.zip"
    zip_filename = "{repo_name}_{commit_sha}.zip".format(repo_name=repo_name,
                                                         commit_sha=commit_sha)
    # zip_filename = f"{repo_name}_{commit_sha}.zip"
    urlretrieve(url, zip_filename)
    print("Downloaded {zip_filename}".format(zip_filename))


def get_update_urls(previousCommits):
    repo_owner = "tb-animator"
    repo_name = "tbAnimTools"
    commits = get_commit_details(repo_owner, repo_name)
    maxCommits = 5
    count = 0

    shaList = list()
    urls = list()
    comments = list()
    for commit in commits:
        commit_sha = commit['sha']

        for previous in previousCommits:
            if previous.get('sha', None):

                return shaList, urls, comments

        count += 1
        if count > maxCommits:
            break
        url = "https://github.com/{repo_owner}/{repo_name}/archive/{commit_sha}.zip".format(repo_owner=repo_owner,
                                                                                            repo_name=repo_name,
                                                                                            commit_sha=commit_sha)
        comment, files_changed = get_commit_comments_and_files(repo_owner, repo_name, commit_sha)
        shaList.append(commit_sha)
        urls.append(url)
        comments.append(comment)

        continue
    return shaList, urls, comments


class updater():
    def __init__(self):
        self.lastUpdateType = -1
        self.updateTypes = ['Latest Stable', 'Latest untested', 'None']
        self.datUrl = 'https://api.github.com/repos/tb-animator/tbAnimTools'
        self.master_url = 'https://raw.githubusercontent.com/tb-animator/tbtools/master/'
        self.latestZip = 'https://github.com/tb-animator/tbAnimTools/archive/refs/heads/main.zip'
        self.realPath = os.path.realpath(__file__)
        self.basename = os.path.basename(__file__)
        self.base_dir = os.path.normpath(os.path.dirname(__file__))

        # make the appData folder if it is not there
        if not os.path.isdir(os.path.join(self.base_dir, 'appData')):
            os.mkdir(os.path.join(self.base_dir, 'appData'))

        # get a reference to where the version file should be located
        self.versionDataFile = os.path.join(self.base_dir, 'appData', 'tbVersion.json')
        self.dateFormat = '%Y-%m-%dT%H:%M'
        self.uiDateFormat = '%Y-%m-%d'
        self.timeFormat = '%H:%M'
        # query github for the latest version info
        self.lastPush = datetime.datetime.strptime("2021-08-16T21:21", self.dateFormat)
        self.latestRelease = None
        self.latestTag = None
        self.releaseZip = None

        # save the project data if it doesn't exist
        if not os.path.isfile(self.versionDataFile):
            self.save(self.lastPush, self.latestRelease)
        # get the project data as a json
        self.jsonProjectData = json.load(open(self.versionDataFile))


        self.data = self.getGithubData()

        self.getPreviousCommits()

        # the most recent github push date
        self.lastPush = datetime.datetime.strptime(self.data.get('pushed_at')[0:16], self.dateFormat)

        # the most recent of the published/released versions
        self.latestRelease, self.latestTag, self.releaseZip = self.getLatestReleaseVersion()

        # convert the time format to the version format
        self.currentVersion = self.convertDateFromString(self.jsonProjectData.get('version', self.lastPush))
        # do the same for the release version
        self.currentRelease = self.convertDateFromString(
            self.jsonProjectData.get('release', self.jsonProjectData.get('version', self.lastPush)))
        # was the last update an untested or a release version
        self.lastUpdateType = self.jsonProjectData.get('lastUpdateType', 'release')

        # what updates is the user subscribed to
        self.updateType = get_option_var('tbUpdateType', -1)
        # set that as an option variable for fun
        set_option_var('tbUpdateType', self.updateType)

        # IF the user has not set an update type, query it with a UI
        if self.updateType == -1:
            # open update type dialog
            prompt = PickListDialog(title='tbAnimTools Update settings', text='Please choose your update type',
                                    itemList=self.updateTypes,
                                    rigName='')
            prompt.titleText.setStyleSheet("font-weight: bold; font-size: 14px;");
            prompt.assignSignal.connect(self.assignUpdateType)
            if prompt.exec_():
                pass
            else:
                pass

    def getPreviousCommits(self):
        shaList, urlList, commentList = get_update_urls(self.jsonProjectData.get('previousCommits', list()))
        newCommits = list()
        if not shaList:
            return False
        for sha, url, comment in zip(shaList, urlList, commentList):
            commitData = {'sha': sha,'url': url,'comment': comment}
            newCommits.append(commitData)
        if newCommits:
            for commit in newCommits.reverse():
                self.jsonProjectData['previousCommits'].insert(0, commit)
        self.saveNewCommitInfo()

    def downloadHelpImages(self):
        try:
            zipUrl = 'https://www.dropbox.com/s/1jwhpe0wsakw6bd/HelpImages.zip?dl=1'
            filedata = urlopen(zipUrl)
            datatowrite = filedata.read()
            zipFile = os.path.normpath(os.path.join(self.base_dir, 'HelpImages.zip'))
            with open(zipFile, 'wb') as f:
                f.write(datatowrite)

            destinationPath = os.path.normpath(os.path.join(self.base_dir))

            with zipfile.ZipFile(zipFile, 'r') as zip_ref:
                zip_ref.extractall(destinationPath)
        except:
            cmds.warning('failed to download help images')

    def assignUpdateType(self, mode, blank):
        set_option_var('tbUpdateType', self.updateTypes.index(mode))

    def saveNewCommitInfo(self):
        j = json.dumps(self.jsonProjectData, indent=4, separators=(',', ': '))
        f = open(self.versionDataFile, 'w')
        f.write(j)
        f.close()

    def save(self, version, release):
        set_option_var('tb_version', version.strftime(self.dateFormat))
        jsonData = '''{}'''
        jsonObjectInfo = json.loads(jsonData)

        jsonObjectInfo['version'] = version.strftime(self.dateFormat)
        jsonObjectInfo['release'] = release.strftime(self.dateFormat)
        jsonObjectInfo['lastUpdateType'] = self.lastUpdateType

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

    def forceUpdate(self):
        lastPushDay = self.lastPush.strftime(self.uiDateFormat)
        lastPushTime = self.lastPush.strftime(self.timeFormat)

        currentVersionDay = self.currentVersion.strftime(self.uiDateFormat)
        currentVersionTime = self.currentVersion.strftime(self.timeFormat)

        updateWin = UpdateWin(newVersion=lastPushDay + ' ' + lastPushTime,
                              oldVersion=currentVersionDay + ' ' + currentVersionTime,
                              updateText='Looks like there is a newer version of tbAnimTools available. Would you like to download the latest scripts?',
                              unstable=True,
                              defaultUrl=self.latestZip,
                              previousCommits=self.jsonProjectData.get('previousCommits', list()),
                              )
        if updateWin.exec_() != 1:
            return
        self.download_project_files(updateWin.selectedUrl)
        self.downloadHelpImages()
        self.save(self.lastPush, self.latestRelease)

    def check_version(self):
        if self.updateType == 0:
            # print('Check for latest stable version')
            # print('lastPush', self.lastPush)
            # print('currentVersion', self.currentVersion)
            # print('currentRelease', self.currentRelease)
            # print('latestRelease', self.latestRelease)
            if self.latestRelease > self.currentRelease:
                lastPushDay = self.latestRelease.strftime(self.uiDateFormat)
                lastPushTime = self.latestRelease.strftime(self.timeFormat)

                currentVersionDay = self.currentRelease.strftime(self.uiDateFormat)
                currentVersionTime = self.currentRelease.strftime(self.timeFormat)

                updateWin = UpdateWin(newVersion=lastPushDay + ' ' + lastPushTime,
                                      oldVersion=currentVersionDay + ' ' + currentVersionTime,
                                      title='tbAnimTools Update - {0}?'.format(self.latestTag),
                                      updateText='Looks like there is a newer release version of tbAnimTools available. Would you like to update to {0}?'.format(
                                          self.latestTag),
                                      defaultUrl=self.releaseZip)
                if updateWin.exec_() != 1:
                    return
                self.download_project_files(updateWin.selectedUrl)
                # self.downloadHelpImages()
                self.save(self.lastPush, self.latestRelease)

        elif self.updateType == 1:
            # print('lastPush', self.lastPush)
            # print('currentVersion', self.currentVersion)
            if self.lastPush > self.currentVersion:
                lastPushDay = self.lastPush.strftime(self.uiDateFormat)
                lastPushTime = self.lastPush.strftime(self.timeFormat)

                currentVersionDay = self.currentVersion.strftime(self.uiDateFormat)
                currentVersionTime = self.currentVersion.strftime(self.timeFormat)

                updateWin = UpdateWin(newVersion=lastPushDay + ' ' + lastPushTime,
                                      oldVersion=currentVersionDay + ' ' + currentVersionTime,
                                      updateText='Looks like there is a newer version of tbAnimTools available. Would you like to download the latest scripts?',
                                      unstable=True,
                                      defaultUrl=self.latestZip,
                                      previousCommits=self.jsonProjectData.get('previousCommits', list()),)
                if updateWin.exec_() != 1:
                    return
                self.download_project_files(updateWin.selectedUrl)
                # self.downloadHelpImages()
                self.save(self.lastPush, self.latestRelease)

    def getGithubData(self):
        try:
            gcontext = ssl.SSLContext()
            response = urlopen(self.datUrl, context=gcontext)
        except:
            response = urlopen(self.datUrl)
        data = json.load(response)

        return data

    def getLatestReleaseVersion(self):
        releasesUrl = self.data['releases_url'].split('{/id}')[0]
        try:
            gcontext = ssl.SSLContext()
            response = urlopen(releasesUrl, context=gcontext)
        except:
            response = urlopen(releasesUrl)
        data = json.load(response)

        releases = {}
        zipFiles = {}
        for release in data:
            creationDate = (release['created_at'])
            tag = (release['name'])
            zipFile = release['zipball_url']
            releaseDate = datetime.datetime.strptime(creationDate[0:16], self.dateFormat)
            releases[releaseDate] = tag
            zipFiles[releaseDate] = zipFile

        latestRelease = max(releases.keys())
        latestZip = zipFiles[latestRelease]
        latestTag = releases[latestRelease]
        latestRelease = datetime.datetime.strptime(self.data.get('pushed_at')[0:16], self.dateFormat)
        return latestRelease, latestTag, latestZip

    def get_url_dir(self, dir):
        out = dir.replace(self.base_dir, self.master_url).replace("\\", "/")
        return out

    def download_project_files(self, zipLocation):
        print("downloading zip file to", self.base_dir)
        filedata = urlopen(zipLocation)
        datatowrite = filedata.read()
        zipFile = os.path.join(self.base_dir, 'tbAnimToolsLatest.zip')
        with open(zipFile, 'wb') as f:
            f.write(datatowrite)

        destinationPath = os.path.normpath(os.path.join(self.base_dir, 'extract'))
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(destinationPath)
        destinationPathFinal = os.path.normpath(os.path.join(self.base_dir))

        copy_tree(os.path.join(destinationPath, 'tbAnimTools-main'), destinationPathFinal)

        message_state = cmds.optionVar(query="inViewMessageEnable")
        cmds.optionVar(intValue=("inViewMessageEnable", 1))
        cmds.inViewMessage(amg='tbAnimTools update complete',
                         pos='botRight',
                         dragKill=True,
                         fadeOutTime=10.0,
                         fade=False)
        cmds.optionVar(intValue=("inViewMessageEnable", message_state))


class UpdateBaseDialog(QDialog):
    widgetClosed = Signal()
    oldPos = None

    def __init__(self, parent=None, title='', text='',
                 lockState=False, showCloseButton=True, showInfo=True,
                 *args, **kwargs):
        super(UpdateBaseDialog, self).__init__(parent=parent)
        self.stylesheet = getqss.getStyleSheet()
        self.setStyleSheet(self.stylesheet)
        self.lockState = lockState
        self.showCloseButton = showCloseButton
        self.setWindowTitle("HELLO!")
        self.setWindowOpacity(1.0)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.autoFillBackground = True
        self.windowFlags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setFixedSize(400 * dpiScale(), 120 * dpiScale())
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(4, 4, 4, 4)
        self.layout = QVBoxLayout()
        self.titleLayout = QHBoxLayout()
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(0, 0, 0, 0)

        self.closeButton = UpdateButton()
        self.closeButton.clicked.connect(self.close)
        self.titleText = QLabel(title)
        # self.titleText.setFont(QFont('Lucida Console', 12))
        # self.titleText.setStyleSheet("font-weight: lighter; font-size: 12px;")
        # self.titleText.setStyleSheet("background-color: rgba(255, 0, 0, 0);")
        # self.titleText.setStyleSheet("QLabel {"
        #                              "border-width: 0;"
        #                              "border-radius: 4;"
        #                              "border-style: solid;"
        #                              "border-color: #222222;"
        #                              "font-weight: bold; font-size: 12px;"
        #                              "}"
        #                              )

        self.titleText.setAlignment(Qt.AlignCenter)
        self.infoText = QLabel(text)
        if not showInfo: self.infoText.hide()

        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.titleText, alignment=Qt.AlignCenter)
        self.titleLayout.addStretch()
        self.titleLayout.addWidget(self.closeButton, alignment=Qt.AlignRight)

        self.mainLayout.addLayout(self.titleLayout)
        self.infoText.setStyleSheet(self.stylesheet)
        self.layout.addWidget(self.infoText)

        self.mainLayout.addLayout(self.layout)
        self.setLayout(self.mainLayout)

        self.closeButton.setVisible(self.showCloseButton)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        lineColor = QColor(68, 68, 68, 128)

        # qp.setCompositionMode(QPainter.CompositionMode_Clear)
        qp.setCompositionMode(QPainter.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(QBrush(lineColor), 2 * dpiScale()))
        grad = QLinearGradient(200, 0, 200, 32)
        grad.setColorAt(0, "#323232")
        grad.setColorAt(0.1, "#373737")
        grad.setColorAt(1, "#323232")
        qp.setBrush(QBrush(grad))
        qp.drawRoundedRect(self.rect(), 8 * dpiScale(), 8 * dpiScale())
        qp.end()

    def close(self):
        self.widgetClosed.emit()
        super(UpdateBaseDialog, self).close()


class UpdateWin(UpdateBaseDialog):
    ActivateSignal = Signal(str, str)
    leftClick = False
    oldPos = None

    def __init__(self, parent=None,
                 title='tbAnimTools Update Found',
                 newVersion=str(),
                 oldVersion=str(),
                 updateText=str(),
                 unstable=False,
                 defaultUrl=None,
                 previousCommits=list(),
                 ):
        super(UpdateWin, self).__init__(parent=parent)

        self.defaultWidth = 800
        self.defaultHeight = 350
        self.setFixedSize(self.defaultWidth, self.defaultHeight)
        self.selectedUrl = defaultUrl

        self.setWindowTitle(title)

        # QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # QBtn.button(QDialogButtonBox.Ok).setText("Activate")
        # QBtn.button(QDialogButtonBox.Cancel).setText("Cancel")
        # self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setFixedWidth(self.defaultWidth - 10)
        self.updateButton = QPushButton("Update To Latest")
        self.cancelButton = QPushButton("Cancel")
        self.updateButton.setFixedWidth(self.defaultWidth - 90)
        self.updateButton.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #52bf90, stop: 0.1 #49ab81, stop: 0.5 #419873, stop: 0.9 #398564, stop: 1 #317256);color: 	#3b2f2f;font-weight: bold; font-size: 14px;')
        self.cancelButton.setFixedWidth(80)
        self.buttonBox.addButton(self.updateButton, QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.cancelButton, QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.buttonBox.accepted.connect(self.activate)
        # self.buttonBox.rejected.connect(self.reject)

        # self.buttonLayout = QVBoxLayout()
        # self.activateButton = QPushButton('Activate')
        # self.quitButton = QPushButton('Exit')

        self.gridLayout = QGridLayout()
        self.titleText.setText(title)
        self.titleText.setStyleSheet("font-weight: bold; font-size: 16px;");
        self.titleText.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.infoText.setText(updateText)
        self.infoText.setWordWrap(True)

        self.currentVersionLabel = QLabel('Current Version')
        self.currentVersionInfoText = QLabel(oldVersion)
        self.latestVersionLabel = QLabel('Latest Version')
        self.latestVersionInfoText = QLabel(newVersion)

        # self.mainLayout.addWidget(self.titleText)
        # self.mainLayout.addWidget(self.infoText)
        self.gridLayout.addWidget(self.currentVersionLabel, 0, 0)
        self.gridLayout.addWidget(self.currentVersionInfoText, 0, 1)
        self.gridLayout.addWidget(self.latestVersionLabel, 1, 0)
        self.gridLayout.addWidget(self.latestVersionInfoText, 1, 1)
        self.mainLayout.addLayout(self.gridLayout)
        # self.buttonWidget.activateSignal.connect(self.dragLeaveEvent())
        self.mainLayout.addWidget(self.buttonBox)

        # part for specific commits
        self.formLayout = QFormLayout()
        label1 = QLabel('')
        label = QLabel('- Previous Commits -')
        label.setStyleSheet("font-weight: bold; font-size: 14px;");
        label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.mainLayout.addWidget(label1)
        self.mainLayout.addWidget(label)
        self.mainLayout.addLayout(self.formLayout)

        if previousCommits:
            for commit in previousCommits:
                url = commit.get('url')
                comment = commit.get('comment')
                button = QPushButton(' Get ')
                button.url = url
                button.clicked.connect(partial(self.getSpecificZip, commit))
                self.formLayout.addRow(button, QLabel(comment))

        # self.activateButton.clicked.connect(self.activate)
        self.startPos = None
        self.move(0, 0)

    def getSpecificZip(self, url):
        self.selectedUrl = url
        self.accept()


class PickListDialog(UpdateBaseDialog):
    assignSignal = Signal(str, str)

    def __init__(self, rigName=str, parent=None, title='title!!!?', text='what  what?', itemList=list()):
        super(PickListDialog, self).__init__(parent=parent, title=title, text=text)
        self.rigName = rigName
        buttonLayout = QHBoxLayout()
        self.assignButton = QPushButton('Assign')
        self.assignButton.clicked.connect(self.assignPressed)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)

        self.itemComboBox = QComboBox()
        for item in itemList:
            self.itemComboBox.addItem(item)
        self.layout.addWidget(self.itemComboBox)
        self.layout.addLayout(buttonLayout)
        buttonLayout.addWidget(self.assignButton)
        buttonLayout.addWidget(self.cancelButton)

    def assignPressed(self):
        self.assignSignal.emit(str(self.itemComboBox.currentText()), str(self.rigName))
        self.close()


class UpdateButton(QPushButton):
    """
    UI menu item for anim layer tab,
    subclass this and add to the _showMenu function, or just add menu items
    """

    def __init__(self, icon=baseIconFile, toolTip='Close'):
        super(UpdateButton, self).__init__()
        # self.setIcon(QIcon(":/{0}".format('closeTabButton.png')))
        self.setFixedSize(18 * dpiScale(), 18 * dpiScale())

        pixmap = QPixmap(os.path.join(IconPath, icon))
        icon = QIcon(pixmap)

        self.setIcon(icon)

        self.setFlat(True)
        self.setToolTip(toolTip)
        self.setStyleSheet("background-color: transparent;border: 0px")
        self.setStyleSheet(getqss.getStyleSheet())
