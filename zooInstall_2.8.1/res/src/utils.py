import os
import sys
import subprocess
import logging
import platform
from PySide2 import QtWidgets
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as omui
import maya.mel as mel
from maya import cmds
from maya import OpenMaya as om1

from res.src import const

logger = logging.getLogger("zoo_installer.{}".format(__name__))
if os.environ.get('ZOO_INSTALLER_DEBUG') == "True":
    logger.setLevel(logging.DEBUG)

if sys.version_info > (3,):
    long = int


def mayaVersion():
    """Returns maya's currently active maya version ie. 2016

    :return: maya version as an int with no updates (decimals) ie. 2016
    :rtype: int
    """
    return int(om1.MGlobal.mayaVersion())


def mayaMainWindow():
    from shiboken2 import wrapInstance as wrapinstance
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapinstance(long(main_window_ptr), QtWidgets.QWidget)


def imagePath(imageFile):
    return os.path.join(currentDirectory(), const.IMAGES, imageFile)


def currentDirectory():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def dpiMult():
    desktop = QtWidgets.QApplication.desktop()
    logicalY = 96
    if desktop is not None:
        logicalY = desktop.logicalDpiY()
    return max(1, float(logicalY) / float(96))


def dpiScale(value):
    """Resize by value based on current DPI

    :param value: the default 2k size in pixels
    :type value: int
    :return value: the size in pixels now dpi monitor ready (4k 2k etc)
    :rtype value: int
    """
    mult = dpiMult()
    return value * mult


def marginsDpiScale(left, top, right, bottom):
    """ Convenience function to return contents margins

    :param left:
    :param top:
    :param right:
    :param bottom:
    :return:
    """

    if type(left) == tuple:
        margins = left
        return dpiScale(margins[0]), dpiScale(margins[1]), dpiScale(margins[2]), dpiScale(margins[3])
    return (dpiScale(left), dpiScale(top), dpiScale(right), dpiScale(bottom))


def restartMaya(force=False, delay=3):
    """ Restarts maya with the same environment.

    Add delay in case maya takes a while to close and save.

    :return:
    """

    my_env = os.environ.copy()
    maya = sys.executable

    if isWindows():
        command = "ping -n {} 127.0.0.1 >nul && {}".format(delay, maya)
    else:
        command = "sleep {} && {}".format(delay, maya)

    subprocess.Popen(command, env=my_env, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
    cmds.quit(force=force)


def fileModified():
    """Checks if the current scene has been modified, returns True if it needs saving.

    :return fileModified: True is there have been modifications to the current scene
    :rtype fileModified: bool
    """
    return cmds.file(query=True, modified=True)


def createNewScene(force=True):
    """Creates a new maya scene

    :param force: Will force a new scene even if the current scene has not been saved, False will error if not saved
    :type force: bool
    """
    cmds.file(newFile=True, force=force)


def getCurrentMayaWorkspace():
    """Returns the current project directory

    :return projectDirectoryPath: the path of the current Maya project directory
    :rtype projectDirectoryPath: str
    """
    return cmds.workspace(q=True, rootDirectory=True)


def getProjSubDirectory(sudDirectory="scenes", message=True):
    """Returns the path of the current Maya project sub directory Eg:

        /scenes/
        or
        /sourceImages/
        etc

    Note: If not found will default to the home directory of your OS.

    :param sudDirectory: The subDirectory of the project directory, can be multiple directories deep
    :type sudDirectory: str
    :param message: Warn the user if the path wasn't found?
    :type message: bool
    :return directoryPath: The path of the directory
    :rtype directoryPath: str
    """
    projectDir = getCurrentMayaWorkspace()
    directory = os.path.join(projectDir, sudDirectory)
    if not os.path.isdir(directory):  # Doesn't exist so set to Home directory
        homeDirectory = os.path.expanduser("~")  # home directory
        om2.MGlobal.displayWarning("Directory `{}` doesn't exist, setting to `{}`".format(directory, homeDirectory))
        directory = homeDirectory
    return directory


def saveAsDialogMaMb(windowCaption="Save File", directory="", okCaption="OK"):
    """Pops up a save file dialog but does not save the file, returns the name of the file to save.

    :return filePath: The path of the file saved, if cancelled will be ""
    :rtype filePath: str
    """
    if not directory:
        # get the current file location
        currentFilePath = cmds.file(query=True, sceneName=True, shortName=False)  # the current filename
        if not currentFilePath:  # is an unsaved file
            directory = getProjSubDirectory(sudDirectory="scenes")
        else:
            directory = os.path.split(currentFilePath)[0]  # the directory path
    multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
    filePath = cmds.fileDialog2(fileFilter=multipleFilters,
                                dialogStyle=2,
                                caption=windowCaption,
                                startingDirectory=directory,
                                okCaption=okCaption)
    if not filePath:
        return filePath
    if filePath:  # Is a list so make a string path
        filePath = filePath[0]
    # Save file
    if filePath.split(".")[-1] == "ma":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaAscii', save=True)
    if filePath.split(".")[-1] == "mb":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaBinary', save=True)
    om2.MGlobal.displayInfo("Success: File saved `{}`".format(filePath))
    return filePath


def selectShelfTab(name):
    gShelfTopLevel = mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")
    cmds.shelfTabLayout(gShelfTopLevel, selectTab=name, e=1)


def shelfExists(name):
    gShelfTopLevel = mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")
    return name in cmds.shelfTabLayout(gShelfTopLevel, childArray=1, q=1)


def parentDir(path, num=1):
    """ Get the parent directory

    :param path: str
    :param num: Number of times it should iterate through the parents
    :return:
    """
    for p in range(num):
        path = os.path.dirname(path)
    return path


def saveFileTxt(formattedText, newfile):
    """Saves a string to a file

    :param formattedText: the text
    :type formattedText: str
    :param newfile: the file to be saved full path
    :type newfile: str
    """
    with open(newfile, "w") as fileInstance:
        fileInstance.write(formattedText)


def isAsciiOnly(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def isWindows():
    """
    :rtype: bool
    """
    return platform.system().lower().startswith('win')


def patchRootPath(rootPath):
    """Patch for zootools preferences path with the use of "~" where python now prioritizes USERPROFILE
    over HOME which happens to affect maya 2022 and below which sets the USERPROFILE to ~/Documents but
    maya 2023 is set to ~/ so this patches it globally across zoo only if "~" is the first character and
    it's windows ensuring that the existing prefs and updating/new installations are maintained.
    """
    if isWindows() and rootPath.startswith("~"):
        globalUserFolder = os.path.expanduser("~")
        parts = rootPath.split(os.path.sep)
        if len(parts) > 1 and parts[1].lower() == "documents":
            rootPath = os.path.join(parts[0], os.path.join(*parts[2:]))
        if not globalUserFolder.lower().endswith("/documents"):
            rootPath = rootPath.replace("~", os.path.join(globalUserFolder, "Documents"))
    return rootPath
