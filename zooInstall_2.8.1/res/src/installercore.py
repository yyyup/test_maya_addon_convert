import shutil
import os
import json
import sys
import logging
import glob
import traceback

import maya.mel as mel
from maya import cmds
import maya.api.OpenMaya as om2

from res.src import const, utils, ui
from res.src.const import Images
from res.src.ui import ImageDialog

logger = logging.getLogger("zoo_installer.{}".format(__name__))
#
if os.environ.get('ZOO_INSTALLER_DEBUG') == "True":
    logger.setLevel(logging.DEBUG)


# ----------------------------------------
# Main Logic
# ----------------------------------------

class InstallerCore(object):
    # Length of the longest path from ./zoo_preferences in the default install
    # Currently it is "prefs/maya/zoo_hotkey_editor/Maya_Default_ZooMod.json"
    preferencesLongest = 60
    zooLongestPath = 170
    _fileLimit = 255

    def __init__(self, installDialog):
        """ Installer core code

        """
        self.installDialog = installDialog
        installed = self.installedZooPath()
        self.currentDirectory = os.path.dirname(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
        self.prefsDirectory = self.getMayaPrefsPath()
        if installed:
            self.scriptsDirectory = os.path.dirname(installed)
        else:
            self.scriptsDirectory = os.path.join(self.prefsDirectory, const.SCRIPTS_DIR)
        self.moduleDirectory = self.installedModPath() or os.path.join(self.prefsDirectory, const.MODULES_DIR)
        self.zooPrefsDirectory = os.path.expanduser(
            self.userPreferencePath(installed) if installed else utils.patchRootPath(const.PREFS_DIR)).replace("\\",
                                                                                                               "/")
        self.prefsToInstall = os.path.dirname(self.zooPrefsDirectory)
        logger.debug("Init Variables in InstallerCore: ")
        logger.debug("  installed: '{}'".format(installed))
        logger.debug("  prefsToInstall: '{}'".format(self.prefsToInstall))
        logger.debug("  scriptsDirectory: '{}'".format(self.scriptsDirectory))
        logger.debug("  moduleDirectory: '{}'".format(self.moduleDirectory))

    def preinstallCheck(self, scriptsDirectory, moduleDirectory, prefDirectory):
        """ Checks before installing

        :return:
        """
        if self.zooInstalled() and os.path.exists(prefDirectory) and prefDirectory != self.zooPrefsDirectory:
            res = ui.MessageBoxQt.showQuestion(parent=self.installDialog,
                                               title="Preferences",
                                               message="The preference folder already exists in: \n\n'{}' \n\nOverwrite?".format(
                                                   prefDirectory),
                                               buttonA="Yes",
                                               buttonB="No",
                                               buttonC="Cancel"
                                               )

            if res == "B":
                return False
            elif res == "C":
                return None

        return True

    def _unloadZoo(self):
        """ Unload the zoo plugins

        :return:
        """
        cmds.unloadPlugin("zootools.py")

    def checkPathLengths(self, scriptsDirectory, moduleDirectory, prefDirectory):
        """ Return the lengths of the paths so we can make sure it's less than 255 chars for the Windows
        max path len

        :param scriptsDirectory:
        :param moduleDirectory:
        :param prefDirectory:
        :return:
        """
        self.scriptsDirLen = len(scriptsDirectory)
        self.moduleDirLen = len(moduleDirectory)
        self.prefDirLen = len(prefDirectory)

        if not self.checkModuleLength(moduleDirectory):
            return False

        # Check the length of the preferences directory
        if not self.checkPreferenceLength(prefDirectory):
            return False

        # Check the length of the scripts directory
        if not self.checkScriptsLength(scriptsDirectory):
            return False

        return True

    def checkModuleLength(self, moduleDirectory, message=True):
        moduleZooFile = os.path.join(moduleDirectory, const.ZOO_MOD)
        if len(moduleZooFile) > self._fileLimit:
            if message:
                text = "Module zoo file location too long. \n\nPlease pick a shorter path."
                ui.errorPopup(text)
            return False
        return True

    def longestModulePath(self):
        return self._fileLimit - len(const.ZOO_MOD)

    def longestPrefPath(self):
        return self._fileLimit - self.preferencesLongest

    def longestScriptsPath(self):
        return self._fileLimit - self.zooLongestPath

    def checkPreferenceLength(self, prefDirectory, message=True):

        prefLongest = len(prefDirectory) + self.preferencesLongest
        if prefLongest > self._fileLimit:
            if message:
                text = "Preference file location too long. Path length must be less than {}. \n\nPlease pick a shorter path.".format(
                    self.longestPrefPath())
                ui.errorPopup(text)
            return False
        return True

    def checkScriptsLength(self, scriptsDir, message=True):
        if len(scriptsDir) + self.zooLongestPath > self._fileLimit:
            if message:
                text = "Scripts path length too long. Path length must be less than {}. \n\nPlease pick a shorter path.".format(
                    self.longestScriptsPath())
                ui.errorPopup(text)
            return False
        return True

    def install(self, scriptsDirectory, moduleDirectory, prefDirectory):
        """Install or upgrades Zoo Tools Pro 2 from the "maya" directory next to this python file.

        :param scriptsDirectory: Usually the full path to /maya/scripts
        :type scriptsDirectory: str
        :param moduleDirectory: Usually the full path to /maya/modules
        :type moduleDirectory: str
        :param prefDirectory:
        """
        upgrade = "installed"
        installedVersion = self.installedVersionPretty()
        version = self.versionPretty()
        newer = self.isNewerVersion()
        prefDirectory = os.path.join(prefDirectory, "zoo_preferences").replace("\\", "/")

        if not self.checkPathLengths(scriptsDirectory, moduleDirectory, prefDirectory):
            return {}

        if self.preinstallCheck(scriptsDirectory, moduleDirectory, prefDirectory) is None:
            logger.debug("Pre-install check cancelled")
            return {}

        if os.path.isdir(os.path.join(scriptsDirectory, const.ZOO_FOLDER)):
            if self.isNewerVersion() == "YES":
                upgrade = "upgraded"
            elif self.isNewerVersion() == "NO":
                upgrade = "downgraded"
            elif self.isNewerVersion() == "EQUAL":
                upgrade = "replaced"

            # Unload zoo
            self._unloadZoo()

        om2.MGlobal.displayInfo("Copy Location Path: {}".format(scriptsDirectory))

        # Copy files across to maya/scripts/zootoolpro
        self.installedScripts = self.copyZooFolder(scriptsDirectory)  # errors already reported
        if not self.installedScripts:
            return {}
        om2.MGlobal.displayInfo("Scripts copied: {}/zootoolspro".format(scriptsDirectory))

        # Create maya/modules/zootoolspro.mod
        if not self.createModFile(moduleDirectory, scriptsDirectory):  # errors already reported
            return {}
        om2.MGlobal.displayInfo("Module created: {}/zootoolspro.mod".format(moduleDirectory))

        if not self.setPreferenceDirectory(prefDirectory):
            return {}
        om2.MGlobal.displayInfo("Preference Directory set: {}".format(prefDirectory))
        restarting = False
        # Success message
        if installedVersion and newer != "EQUAL":
            logger.debug("Has been installed before, need to restart maya.")
            message = "Zoo Tools Pro 2 has been {} successfully. " \
                      "\n\nFrom Version {} --> {}\n\n" \
                      "Please restart Maya for the changes to take effect.".format(upgrade, installedVersion, version)
            restarting = ui.restartMayaPopup(message, parent=self.installDialog)
        elif newer == "EQUAL":
            logger.debug("Installed version is equal to installer")

            message = "Zoo Tools Pro 2 has been {} successfully.\n\n" \
                      "Please restart Maya for the changes to take effect.".format(upgrade, installedVersion, version)
            restarting = ui.restartMayaPopup(message, parent=self.installDialog)
        else:
            logger.debug("Not installed previously, loading plugin.")
            message = "Zoo Tools Pro 2 has been {} successfully. ".format(upgrade)
            self.loadZooPlugin(os.path.join(scriptsDirectory, "zootoolspro", "install", "core"))

        om2.MGlobal.displayInfo(message.replace("\n\n", " "))
        logger.debug("Install successful.")

        return {"success": True, "restarting": restarting}

    def installedPrefPath(self):
        """ Installed Pref Path

        :return:
        """
        installed = self.installedZooPath()
        if installed:
            return self.userPreferencePath(installed)

    def loadZooPlugin(self, rootDirectory):
        """ Load the zoo plugin

        :param rootDirectory:
        :return:
        """
        if utils.mayaVersion() >= 2022:
            securityDialog = ImageDialog(parent=self.installDialog,
                                         imageFile=Images.ALLOW_PLUGIN,
                                         text="Maya 2022 requires users to allow new plugins. "
                                              "Please allow permissions for Zoo Tools Pro.",
                                         title="Allow Plugin",
                                         header="Please Allow Plugin Execution",
                                         width=585)
            securityDialog.modalShow()

        logger.debug("Loading plugins from '{}'".format(rootDirectory))
        os.environ["ZOOTOOLS_PRO_ROOT"] = rootDirectory
        rootDirectory = rootDirectory.replace("\\", "/")

        # Callback to clean up after installing
        callback = const.CLEANUP_PYC_CALLBACK.format(rootDirectory)
        extensionsFolder = os.path.join(os.environ["ZOOTOOLS_PRO_ROOT"],
                                        "extensions")

        zooTools = os.path.join(extensionsFolder, "maya", "plug-ins", "zootools.py")
        scriptsFolder = os.path.join(extensionsFolder, "maya", "scripts")
        sys.path.append(os.path.join(os.environ["ZOOTOOLS_PRO_ROOT"], "python"))
        sys.path.append(scriptsFolder) # just for the current session
        cmds.loadPlugin(zooTools, addCallback=callback)

        # Autoload
        logger.debug("Setting autoload for 'zootools.py'")
        cmds.pluginInfo("zootools.py", autoload=1, e=1)
        cmds.pluginInfo("zootools.py", savePluginPrefs=1)
        logger.debug("Selecting \'ZooToolsPro' Shelf")

    def setPreferenceDirectory(self, prefDirectory, move=True):
        """ Set preferences directory. Doesn't need zoo to be installed

        :param prefDirectory:
        :return:
        """
        logger.debug("setPreferenceDirectory: {}".format(prefDirectory))
        scriptsDir = self.installedScripts
        if not self.installedScripts:
            return False

        # Move preferences if different
        if self.zooInstalled() and move and prefDirectory != self.zooPrefsDirectory:
            installedPrefPath = self.installedPrefPath()
            logger.debug("Moving Preferences from '{}' to '{}'".format(installedPrefPath, prefDirectory))
            ui.moveRootLocation(installedPrefPath, prefDirectory, parent=self.installDialog)

        prefRootsPath = os.path.join(scriptsDir,
                                     "zootoolspro", "config", "env", "preference_roots.config")

        with open(prefRootsPath, 'r') as f:
            prefRoot = json.load(f)

        # Add ~ in place of the home directory
        prefRoot['user_preferences'] = prefDirectory.replace(os.path.expanduser("~"), "~")
        with open(prefRootsPath, 'w') as f:
            f.write(json.dumps(prefRoot, indent=4))

        logger.debug("Writing to preference_roots: {}".format(prefDirectory))

        return True

    def userPreferencePath(self, zooPath):
        """ User preference path found from the zootools pro path

        :param zooPath:
        :return:
        """
        if zooPath is None:
            return None
        userPrefs = utils.patchRootPath(self.preferenceRoots(zooPath)['user_preferences'])
        return userPrefs

    def preferenceRoots(self, zooPath):
        prefRootsPath = os.path.join(zooPath,
                                     "config", "env",
                                     "preference_roots.config")

        with open(prefRootsPath, 'r') as f:
            prefRoot = json.load(f)

        return prefRoot

    @classmethod
    def getMayaPrefsPath(cls):
        """Returns the users maya prefs folder full path eg:

            C:/Users/userName/Documents/maya

        :return prefsDirectory: The full path to the users maya prefs location
        :rtype prefsDirectory:
        """
        versionPrefsFolder = mel.eval("internalVar -upd")  # Eg. path to maya/2020/prefs folder
        return os.path.abspath(os.path.join(versionPrefsFolder, "../.."))  # up two directories /maya only

    def isNewerVersion(self):
        """

        :return: True if newer, false if not newer. None if zoo isn't installed
        """

        version = self.version()
        installedVersion = self.installedVersion()
        if installedVersion is None:
            return "NOT_INSTALLED"

        if version > installedVersion:
            return "YES"
        elif version == installedVersion:
            return "EQUAL"
        return "NO"

    def version(self):
        """ Build version of this installer

        :return:
        """
        with open(os.path.join(self.currentDirectory, "maya", "scripts", "zootoolspro", "zoo_package.json")) as f:
            zooJson = json.load(f)

        return tuple(zooJson['version'].split("."))

    def versionPretty(self):
        """ This installer's version as a string

        :return:
        """
        return ".".join(self.version())

    def installedVersion(self):
        """ Installed build version

        :return:
        """
        if not self.zooInstalled():
            return

        if self.zooLoaded():
            from zoo.core.api import currentConfig
            try:
                buildVersion = currentConfig().buildVersion()
                return tuple(buildVersion.split("."))
            except AttributeError:  # For the issue where buildVersion has not been set up yet
                return None
        zootoolsproPath = self.installedZooPath()
        with open(os.path.join(zootoolsproPath, "zoo_package.json")) as f:
            zooJson = json.load(f)
        return tuple(zooJson['version'].split("."))

    def installedVersionPretty(self):
        version = self.installedVersion()
        if version:
            return ".".join(self.installedVersion())

    def installedZooPath(self):
        """ Installed zoo path

        :return:
        """
        if not self.zooInstalled():
            return

        if self.zooLoaded():
            from zoo.core.api import currentConfig
            if hasattr(currentConfig(), "rootPath"):
                return currentConfig().rootPath

        return utils.parentDir(cmds.pluginInfo("zootools.py", q=1, path=1), 6)

    def zooLoaded(self):
        try:
            return cmds.pluginInfo("zootools.py", q=1, l=1)
        except:
            return False

    def zooInstalled(self):
        """ Checks if zoo is installed

        :return:
        """

        try:
            cmds.pluginInfo("zootools.py", q=1, p=1)
            return True
        except:
            return False

    def createModFile(self, moduleDirectory, scriptsDirectory):
        """Creates the zootoolspro.mod file creating the path correctly.

        :param moduleDirectory: The modules folder full path
        :type moduleDirectory: str

        :return moduleDirectory: the full path to the /maya/modules/ directory
        :rtype moduleDirectory: str
        """
        moduleText = const.MOD_TEXT.format(scriptsDirectory)
        # Check if "maya/modules" folder already exists
        moduleZooFile = os.path.join(moduleDirectory, const.ZOO_MOD)
        if not os.path.isdir(moduleDirectory):
            if not ui.makeDirectory(moduleDirectory):  # error reported
                return False
        # Check if file "zootoolspro.mod" exists
        if os.path.isfile(moduleZooFile) and const.ZOO_MOD in moduleZooFile:
            om2.MGlobal.displayInfo("Upgrading: Rebuilding file as it exists {}".format(moduleZooFile))
            try:
                os.remove(moduleZooFile)
            except:
                message = "The file could not be deleted {} \n\n{}".format(moduleZooFile, const.DID_NOT_INSTALL)
                om2.MGlobal.displayInfo(message)
                ui.errorPopup(message)
                return False
        # Create "zootoolspro.mod" file in the modules directory
        print("length of ", moduleZooFile, len(moduleZooFile))
        utils.saveFileTxt(moduleText, moduleZooFile)

        return True

    def installedPrefRootPath(self):
        installed = self.installedZooPath()
        if installed:
            return os.path.join(installed,
                                "config", "env",
                                "preference_roots.config")

    def prefRootPath(self, zooPath):
        return os.path.join(zooPath,
                            "config", "env",
                            "preference_roots.config")

    def installedPrefRoots(self):
        installed = self.installedZooPath()
        if installed:
            return self.preferenceRoots(installed)

    def modDirs(self):
        return os.getenv("MAYA_MODULE_PATH", "").split(os.pathsep)

    def installedModPath(self):
        """

        :return:
        """
        for path in self.modDirs():
            if glob.glob(os.path.join(path, "zootoolspro.mod")):
                return path

    def _installedModPathLegacy(self):
        installed = self.installedZooPath()
        if not installed:
            return

        return self.preferenceRoots(installed).get("maya_mod", "")

    def copyZooFolder(self, scriptsDirectory):
        """Copies the maya/scripts/zootoolpro folder from the unzipped source to the destination in the user prefs

        :return scriptsDirectory: The scripts directory maya/scripts if successful
        :rtype scriptsDirectory: str
        """
        zooTargetDir = os.path.join(scriptsDirectory, "zootoolspro")
        if not os.path.isdir(scriptsDirectory):
            if not ui.makeDirectory(scriptsDirectory):  # error reported
                return False
        # Get the zoo folder to copy
        zooSourceDir = os.path.join(self.currentDirectory, "maya/scripts/zootoolspro")
        # Check if exists already
        if not os.path.isdir(zooSourceDir):
            message = "Cannot find the source `maya` folder, be sure that the files have been unzipped " \
                      "with the `maya` folder in the same folder as the " \
                      "drag and drop python file.\n\n{}".format(const.DID_NOT_INSTALL)
            om2.MGlobal.displayError(message)
            ui.errorPopup(message)
            return False
        # Check upgrading
        if os.path.isdir(zooTargetDir) and "zootoolspro" in zooTargetDir:  # it exists already so delete for the upgrade
            om2.MGlobal.displayInfo("Upgrading: Deleting and remaking directory {} ".format(zooTargetDir))
            try:
                shutil.rmtree(zooTargetDir)
            except:
                message = "Could not delete folder {} \n\n{}".format(zooTargetDir, const.DID_NOT_INSTALL)
                traceback.print_exc()
                om2.MGlobal.displayError(message)
                ui.errorPopup(message)
                return False
        # Copy files to new location
        if not ui.copyDirectory(zooSourceDir, zooTargetDir, (
                ".gitignore", "*.git", "__pycache__", "*.pyc", ".vscode", ".idea")):  # message already reported
            return False
        return scriptsDirectory

    def prefDirs(self):
        """ The preference directories

        :return:
        """
        return [os.path.expanduser("~"), self.prefsDirectory]


def deletePycFiles(path):
    files = pycFiles(path)
    for f in files:
        os.remove(f)


def pycFiles(path):
    return [os.path.join(dir, f) for (dir, subdirs, fs) in os.walk(path) for f in fs if f.endswith(".pyc")]
