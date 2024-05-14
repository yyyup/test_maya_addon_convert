import os
import platform
import sys
import webbrowser
import logging

from PySide2 import QtCore, QtGui, QtWidgets
import maya.api.OpenMaya as om2

from res.src import installercore
from res.src import utils, ui

from res.src.const import Images

# os.environ['ZOO_INSTALLER_DEBUG'] = "True" # Uncomment this line to show debug log

logger = logging.getLogger("zoo_installer.{}".format(__name__))
os.environ['ZOO_INSTALLER_DEBUG'] = os.environ.get('ZOO_INSTALLER_DEBUG', 'False')
if os.environ['ZOO_INSTALLER_DEBUG'] == "True":
    logger.setLevel(logging.DEBUG)
zooPathLimit = 170
if utils.isWindows():
    OS_PATH_LIMIT = 255
else:
    OS_PATH_LIMIT = 4096  # linux


def purgeImports():
    """Purge the installer and drag and drop modules from the sys.modules cache that way
    if the user cancels and retries to reinstall from a new location we pick up the new location
    modules instead of the old
    """
    for name in ("res", "res.src",
                 "res.src.utils",
                 "res.src.ui",
                 "res.src.installercore",
                 "res.src.const",
                 "dragdropinstall"):
        if name in sys.modules:
            del sys.modules[name]


# ----------------------------------------
# Main UI
# ----------------------------------------

class InstallDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setProperty("saveWindowPref", True)
        self.parent = parent
        self.setWindowTitle("Zoo Tools Pro Installer")
        self.setFixedWidth(utils.dpiScale(590))
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.core = installercore.InstallerCore(self)
        self._createWidgets()
        self.refreshInstallUpdateBtns()  # update the install or refresh button
        self.createLayouts()
        self.connections()
        self.raise_()

    def createImage(self, parent):
        """Creates the image from the RELATIVE_IMAGE path"""
        zooImagePath = utils.imagePath(Images.BANNER)
        zooImage = QtWidgets.QLabel(parent)
        zooImage.setGeometry(*utils.marginsDpiScale(0, 0, 580, 453))
        zooImage.setPixmap(QtGui.QPixmap(zooImagePath))
        return zooImage

    def _createWidgets(self):
        """ Create widgets

        :return:
        """
        self.zooImage = self.createImage(None)

        # self.scriptsLabel = QtWidgets.QLabel("Scripts <font color='#000000'>Path</font>")
        self.scriptsLabel = QtWidgets.QLabel("Scripts Path")

        scriptsPath = self.core.scriptsDirectory
        self.scriptsPathEdit = QtWidgets.QLineEdit(scriptsPath, parent=self)
        self.scriptsBrowseBtn = QtWidgets.QPushButton(parent=self, text="...")
        self.scriptsBrowseBtn.setFixedWidth(utils.dpiScale(30))

        self.moduleLabel = QtWidgets.QLabel("Module Path")

        modPath = self.core.moduleDirectory
        self.modulePathCombo = ModCombo(self.core, parent=self,
                                        initText=modPath)

        self.moduleBrowseBtn = QtWidgets.QPushButton(parent=self, text="...")
        self.moduleBrowseBtn.setFixedWidth(utils.dpiScale(30))

        self.prefLabel = QtWidgets.QLabel("Zoo Prefs")
        prefPath = self.core.prefsToInstall

        if utils.isWindows():
            prefPath.replace("/", "\\")

        self.prefPathCombo = PrefCombo(self.core, parent=self, initText=prefPath)
        self.prefBrowseBtn = QtWidgets.QPushButton(parent=self, text="...")
        self.prefBrowseBtn.setFixedWidth(utils.dpiScale(30))

        self.installButton = InstallButton(parent=self, text=" Install Zoo Tools Pro")
        self.installButton.setIcon(QtGui.QIcon(utils.imagePath("zooToolsZ_64.png")))

        self.refreshInstallUpdateBtns()

        self.helpButton = QtWidgets.QPushButton(parent=self, text=" Help")
        self.helpButton.setIcon(QtGui.QIcon(utils.imagePath("help_64.png")))
        self.customizeButton = QtWidgets.QPushButton(parent=self, text=" Customize...")
        self.customizeButton.setIcon(QtGui.QIcon(utils.imagePath("editSpanner_64.png")))
        self.expressButton = QtWidgets.QPushButton(parent=self, text=" Back to Express")
        self.expressButton.setIcon(QtGui.QIcon(utils.imagePath("back_64.png")))
        self.expressButton.hide()

    def createLayouts(self):
        """ Create layouts

        :return:
        """
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(*utils.marginsDpiScale(2, 2, 2, 2))
        mainLayout.setSpacing(utils.dpiScale(5))

        customizeLayout = QtWidgets.QGridLayout()
        customizeLayout.setContentsMargins(*utils.marginsDpiScale(10, 5, 10, 2))
        customizeLayout.setHorizontalSpacing(3)
        customizeLayout.setVerticalSpacing(3)
        r = 0
        customizeLayout.setColumnStretch(1, 10)

        newSpacer = lambda: QtWidgets.QSpacerItem(utils.dpiScale(5), utils.dpiScale(5))

        customizeLayout.addWidget(self.scriptsLabel, r, 0)
        customizeLayout.addWidget(self.scriptsPathEdit, r, 1)
        customizeLayout.addWidget(QtWidgets.QLabel(
            "    <i>All the core Zoo Tools scripts are stored in the scripts path under the folder 'zootoolspro'</i>"),
            r + 1, 1, parent=self)
        customizeLayout.addWidget(self.scriptsBrowseBtn, r, 2)
        customizeLayout.addItem(newSpacer(), r + 2, 1)

        r += 3
        customizeLayout.addWidget(self.moduleLabel, r, 0)
        customizeLayout.addWidget(self.modulePathCombo, r, 1)

        customizeLayout.addWidget(QtWidgets.QLabel(
            "    <i>The modules path with the file 'zootoolspro.mod'. Tells maya where the scripts are stored.</i>"),
            r + 1, 1, parent=self)
        customizeLayout.addWidget(self.moduleBrowseBtn, r, 2)
        customizeLayout.addItem(newSpacer(), r + 2, 1)

        r += 3
        customizeLayout.addWidget(self.prefLabel, r, 0)
        customizeLayout.addWidget(self.prefPathCombo, r, 1)
        customizeLayout.addWidget(QtWidgets.QLabel(
            "    <i>The 'zoo_preferences' folder that stores personal settings, presets and assets.</i>"), r + 1, 1,
            parent=self)
        customizeLayout.addWidget(self.prefBrowseBtn, r, 2)
        customizeLayout.addItem(newSpacer(), r + 2, 1)

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setSpacing(2)
        buttonLayout.setContentsMargins(*utils.marginsDpiScale(4, 0, 4, 4))
        buttonLayout.addWidget(self.installButton, 6)
        buttonLayout.addWidget(self.customizeButton, 2)
        buttonLayout.addWidget(self.expressButton, 2)
        buttonLayout.addWidget(self.helpButton, 1)

        self.customizeWgt = QtWidgets.QWidget(self)
        self.customizeWgt.setLayout(customizeLayout)

        self.customizeWgt.hide()
        imageLayout = QtWidgets.QVBoxLayout()
        imageLayout.setContentsMargins(*utils.marginsDpiScale(3, 3, 3, 0))
        imageLayout.addWidget(self.zooImage)
        mainLayout.addLayout(imageLayout)
        mainLayout.addWidget(self.customizeWgt)
        mainLayout.addLayout(buttonLayout)

    def customizeClicked(self):
        self.customizeWgt.show()
        self.expressButton.show()
        self.customizeButton.hide()
        self.resize(self.sizeHint())
        self.sender().setDown(False)

    def expressClicked(self):
        self.customizeWgt.hide()
        self.expressButton.hide()
        self.customizeButton.show()
        self.resize(self.sizeHint())
        self.sender().setDown(False)

    def isExpress(self):
        """ Is Express

        :return:
        """
        return self.customizeButton.isVisible()

    def browseScriptsPath(self):
        """ Browse scripts path button pressed

        :return:
        """

        directoryPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                   "Set Scripts Directory",
                                                                   self.scriptsPathEdit.text())
        self.sender().setDown(False)  # unstuck the button
        if not directoryPath:
            return

        # self.core.scriptsDirectory = directoryPath

        self.refreshInstallUpdateBtns()  # update the install or refresh button
        # Check the browser prefs path, try again if it's too long
        if not self.core.checkScriptsLength(directoryPath):
            self.browseScriptsPath()
            return

        # Check if there are non-ascii characters in path,
        if not checkPathAsciiOnly(directoryPath):
            self.browseScriptsPath()
            return

        self.scriptsPathEdit.setText(directoryPath)

    def refreshInstallUpdateBtns(self):
        newer = self.core.isNewerVersion()
        installed = self.core.zooInstalled()
        version = self.core.versionPretty()

        if not installed:
            self.installButton.setText("Install Zoo Tools Pro {}".format(version))
            return

        if newer == "YES":
            text = "UPGRADE Zoo Tools Pro to '{}'".format(version)
        elif newer == "NO":
            text = "DOWNGRADE Zoo Tools Pro to '{}'".format(version)
        else:
            text = "REINSTALL Zoo Tools Pro '{}'".format(version)
        self.installButton.setText(text)

    def browseModulesPath(self):
        """ Browse Modules path

        :return:
        """
        directoryPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                   "Set Modules Directory",
                                                                   self.modulePathCombo.currentPath())
        self.sender().setDown(False)  # unstuck the button
        if not directoryPath:
            return

        # Check the browser prefs path, try again if it's too long
        if not self.core.checkModuleLength(directoryPath):
            self.browseModulesPath()
            return

        # Check if there are non-ascii characters in path,
        if not checkPathAsciiOnly(directoryPath):
            self.browseScriptsPath()
            return

        # self.core.moduleDirectory = directoryPath
        self.modulePathCombo.setCustom(directoryPath)

    def browsePrefsPath(self):
        """ Browse Modules path

        :return:
        """
        path = self.prefPathCombo.currentPath()
        directoryPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                   "Set Preferences Directory",
                                                                   path)
        self.sender().setDown(False)  # unstuck the button
        if not directoryPath:
            return
        # self.core.zooPrefsDirectory = directoryPath

        # Check the browser prefs path, try again if it's too long
        if not self.core.checkPreferenceLength(directoryPath):
            self.browsePrefsPath()
            return

        # Check if there are non-ascii characters in path,
        if not checkPathAsciiOnly(directoryPath):
            self.browseScriptsPath()
            return

        self.prefPathCombo.setToText(directoryPath)

    def openHelp(self):
        """ Open help link

        :return:
        """

        webbrowser.open('https://create3dcharacters.com/maya-zoo-tools-pro-installer')

    def installUpgrade(self):
        """ Install and upgrade button pressed

        :return:
        """
        self.sender().setDown(False)  # unstuck the button
        # Non-Maya module path
        if self.modulePathCombo.currentPath() not in self.core.modDirs():
            logger.debug("Non-maya module path message box.")
            message = "You are about to install on a non-Maya module path. ZooToolsPro WILL NOT WORK unless you add this path to MAYA_MODULE_PATH. Are you sure you want to continue?"
            res = ui.MessageBoxQt.showQuestion(self, "Non-Maya Module Path",
                                               message=message, buttonA="Yes", buttonB="Cancel")
            if res == "B":
                om2.MGlobal.displayWarning("Installation Cancelled")
                logger.debug("Cancelling install from non-maya module message box.")
                return

        # Old version
        if self.core.isNewerVersion() == "NO":
            logger.debug("Downgrading zootools pro message box.")
            installed = self.core.installedVersionPretty()
            version = self.core.versionPretty()
            message = "You are about to downgrade ZooTools Pro from:\n\n'{}' to '{}'\n\nAre you sure you want to do this?".format(
                installed, version)
            res = ui.MessageBoxQt.showQuestion(self, "DOWNGRADE '{}'?".format(version),
                                               message=message, buttonA="Yes", buttonB="Cancel")
            if res == "B":
                logger.debug("Cancelling downgrade")
                om2.MGlobal.displayWarning("Installation Cancelled")
                return

        if self.isExpress():
            scripts = self.core.scriptsDirectory
            modPath = self.core.moduleDirectory
            prefPath = self.core.prefsToInstall
        else:
            scripts = self.scriptsPathEdit.text()
            modPath = self.modulePathCombo.currentPath()
            prefPath = self.prefPathCombo.currentPath()

        self.refreshInstallUpdateBtns()  # update the install or refresh button
        logger.debug("Starting zoo install to: ")
        logger.debug("  scripts: '{}'".format(scripts))
        logger.debug("  modPath: '{}'".format(modPath))
        logger.debug("  prefPath '{}'".format(prefPath))
        install = self.core.install(scripts, modPath, prefPath)
        if install.get("success"):
            if not install.get("restarting"):
                global gettingStarted
                gettingStarted.show()

            self.close()

    def connections(self):
        """ Connections

        :return:
        """
        self.scriptsBrowseBtn.pressed.connect(self.browseScriptsPath)
        self.moduleBrowseBtn.pressed.connect(self.browseModulesPath)
        self.prefBrowseBtn.pressed.connect(self.browsePrefsPath)
        self.helpButton.pressed.connect(self.openHelp)
        self.installButton.pressed.connect(self.installUpgrade)
        self.expressButton.pressed.connect(self.expressClicked)
        self.customizeButton.pressed.connect(self.customizeClicked)


class GettingStartedDialog(ui.ImageDialog):
    def __init__(self):
        super(GettingStartedDialog, self).__init__(parent=utils.mayaMainWindow(),
                                                   imageFile=Images.GETTING_STARTED,
                                                   text="Congratulations, Zoo Tools Pro has been installed. "
                                                        "Click on the video below to get started.",
                                                   title="Welcome to Zoo Tools Pro",
                                                   header="Welcome to Zoo Tools Pro!",
                                                   # buttonB="Get Started!",
                                                   buttonIconB=Images.PLAY,
                                                   width=590, clickable=True)
        # self.buttonClicked.connect(lambda b: self.gettingStarted() if b == "B" else None)
        self.imagePressed.connect(self.gettingStarted)
        self.destroyed.connect(purgeImports)

    def showEvent(self, *args, **kwargs):
        super(GettingStartedDialog, self).showEvent(*args, **kwargs)
        self.gettingStarted()
        self.raise_()

    def gettingStarted(self):
        webbrowser.open('https://create3dcharacters.com/zootools-getting-started/')


class InstallButton(QtWidgets.QPushButton):
    def setText(self, text):
        super(InstallButton, self).setText(" " + text)


class SelectCombo(QtWidgets.QComboBox):
    def __init__(self, core, parent=None, initText=None):
        """ Able to browse and select

        :param core:
        :type core: InstallerCore
        :param parent:
        """
        super(SelectCombo, self).__init__(parent)
        self._init()
        self.setStyleSheet("background-color: #2b2b2b")
        self.core = core
        self.updateCombo()

        if initText:
            self.setToText(initText)

    def _init(self):
        pass

    def setCustom(self, custom):
        self.clear()
        if utils.isWindows():
            custom = custom.replace("/", "\\")
        self.addItems(self.items() + ["Other: " + custom])
        self.setCurrentIndex(self.count() - 1)

    def updateCombo(self):
        self.clear()
        self.addItems(self.items())

    def items(self):
        """

        :return:
        :rtype: list
        """
        pass

    def setToText(self, text):
        """Sets the index based on the text

        :param text: Text to search and switch the comboxBox to
        :type text: str
        """
        # if utils.isWindows():
        #     text = text.replace("")
        if utils.isWindows():
            text = text.replace("/", "\\")
        index = self.findText(text, QtCore.Qt.MatchFixedString)

        if index >= 0:
            self.setCurrentIndex(index)
            return True

        if index != 0:
            self.setCustom(text)
        return False

    def currentPath(self):
        text = self.currentText()
        if utils.isWindows():
            text = text.replace("\\", '/')
        if text[:7] != "Other: ":
            return text
        else:
            return text[7:]

    def currentIsOther(self):
        return self.currentText()[:7] == "Other: "


class ModCombo(SelectCombo):

    def items(self):
        dirs = self.core.modDirs()
        if utils.isWindows():
            dirs = [x.replace("/", "\\") for x in dirs]
        return dirs


class PrefCombo(SelectCombo):

    def items(self):
        dirs = self.core.prefDirs()

        if utils.isWindows():
            dirs = [x.replace("/", "\\") for x in dirs]
        return dirs


# ----------------------------------------
# RUN DRAG AND DROP
# ----------------------------------------
gettingStarted = GettingStartedDialog()


def checkFileLength(path):
    """ Check the file length of the install location. If it's too long then warn the user to
    move to a separate location

    :return:
    """
    if len(path) + zooPathLimit > OS_PATH_LIMIT:
        text = "The install location is too long as {} is limited to {} characters and zootools has long paths. " \
               "\n\nPlease move this directory to a shorter path length such as:" \
               "\n\nC:\\users\\yourname\\downloads\\zootoolspro_version".format(platform.system(), OS_PATH_LIMIT)
        ui.errorPopup(text)
        return False
    return True


def checkPathAsciiOnly(path, message=True):
    if not utils.isAsciiOnly(path):
        if message:
            text = "Invalid Path:\n\n" \
                   "{}\n\n" \
                   "Install path must be placed on English locations only. \n" \
                   "Non-English characters in paths not currently supported.\n\n" \
                   "Example:\n" \
                   "C:\\users\\yourname\\downloads\\zootoolspro_version".format(path)
            ui.errorPopup(text)
        return False
    return True


def onMayaDroppedPythonFile(*args, **kwargs):
    """Main function that runs while dragging the file into Maya.

    Will install Zoo Tools Pro so long as the install folders are located beside this python file.
    """
    try:
        path = os.path.dirname(os.path.realpath(__file__))

        if not checkFileLength(path):
            purgeImports()
            return

        if not checkPathAsciiOnly(path):
            purgeImports()
            return
        install = InstallDialog(utils.mayaMainWindow())
        install.show()

    except Exception:
        purgeImports()
