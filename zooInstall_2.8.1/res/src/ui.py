from distutils.dir_util import copy_tree
import os
import shutil
import errno
import logging
from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds
import maya.api.OpenMaya as om2

from res.src import const, utils

logger = logging.getLogger("zoo_installer.{}".format(__name__))

if os.environ.get('ZOO_INSTALLER_DEBUG') == "True":
    logger.setLevel(logging.DEBUG)


class ImageDialog(QtWidgets.QDialog):
    buttonClicked = QtCore.Signal(str)

    def __init__(self, parent=None, imageFile="", text="", title="", header="",
                 buttonA="OK", buttonB="",
                 buttonIconA=const.Images.CHECKMARK, buttonIconB=None,
                 width=None, modal=False, clickable=False):
        """ ImageDialog

        :param parent:
        :param imageFile:
        :param text:
        :param title:
        :param header:
        :param buttonA:
        :param buttonB:
        :param buttonIconA:
        :param buttonIconB:
        :param width:
        :param modal:
        :param clickable:
        """
        super(ImageDialog, self).__init__(parent=parent)
        self.imageFile = imageFile
        self.text = text
        self.title = title
        self.header = header
        self.buttonsInfo = ((buttonA, buttonIconA), (buttonB, buttonIconB))
        self._buttons = []
        self.width = width
        self.modal = modal
        self.clickable = clickable
        self.closed = False
        self._initUi()

    def _initUi(self):
        """ Initialize the ui

        :return:
        """
        self.setModal(self.modal)
        text = self.text
        # Dialog
        self.setWindowTitle(self.title)
        if self.width:
            self.setFixedWidth(self.width)
        self.setContentsMargins(*utils.marginsDpiScale(0, 10, 0, 10))

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(*utils.marginsDpiScale(5, 5, 0, 0))
        mainLayout.setSpacing(utils.dpiScale(2))
        headerLabel = self._headerLabel()

        image = self.imageLayout(self)

        textLabel = QtWidgets.QLabel(text=text, parent=self)
        buttonLayout = self._buttonLayout()
        buttonLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        textLayout = QtWidgets.QVBoxLayout()
        textLayout.setSpacing(utils.dpiScale(10))
        textLayout.setContentsMargins(*utils.marginsDpiScale(10, 0, 10, 2))
        textLayout.addWidget(headerLabel)
        textLayout.addWidget(textLabel)

        mainLayout.addLayout(textLayout)
        mainLayout.addLayout(image)
        mainLayout.addLayout(buttonLayout)

    def _buttonLayout(self):
        """ Button Layout

        :return:
        """
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttons = []
        width = -1

        for i, (btnText, btnIcon) in enumerate(self.buttonsInfo):
            if not btnText:
                continue
            button = QtWidgets.QPushButton(" " + btnText, parent=self)

            if btnIcon:
                button.setIcon(QtGui.QIcon(utils.imagePath(btnIcon)))

            buttons.append(button)
            button.setProperty("btn", btnText)
            if button.width() > width:
                width = button.width()

            buttonLayout.addSpacing(utils.dpiScale(5)) if i > 0 else None
            buttonLayout.addWidget(button)
            button.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
            button.setFixedWidth(width)  # Same size for both
            button.clicked.connect(self.buttonClickedEvent)
        self._buttons = buttons
        buttonLayout.addStretch(1)

        return buttonLayout

    def buttonClickedEvent(self):
        """ Button Clicked event

        :return:
        """
        self.close()
        btn = self.sender()
        if btn:
            self.buttonClicked.emit(btn.property('btn'))

    def closeEvent(self, event):
        self.closed = True
        super(ImageDialog, self).closeEvent(event)

    def close(self):
        self.closed = True
        super(ImageDialog, self).close()

    def _headerLabel(self):
        headerText = self.header  # type: str
        headerLabel = QtWidgets.QLabel(text=headerText.upper(), parent=self)
        headerLabel.setStyleSheet("font-weight: bold; font-size: 14px; color: white")
        return headerLabel

    def imageLayout(self, parent):
        """ Creates the image layout

        :param parent:
        :return:
        """

        imageLayout = QtWidgets.QHBoxLayout()
        imageLayout.setContentsMargins(*utils.marginsDpiScale(0, 10, 0, 10))
        zooImagePath = utils.imagePath(self.imageFile)
        self.zooImage = ClickableImage(clickable=self.clickable, parent=parent)
        imageLayout.addWidget(self.zooImage)
        width = self.width
        pixmap = QtGui.QPixmap(zooImagePath)
        if width:
            pixmap = pixmap.scaledToWidth(width - utils.dpiScale(10), QtCore.Qt.SmoothTransformation)
        self.zooImage.setPixmap(pixmap)

        return imageLayout

    @property
    def imagePressed(self):
        return self.zooImage.clicked

    def modalShow(self):
        self.show()
        self.raise_()
        while self.closed is False or self.isVisible():
            QtWidgets.QApplication.processEvents()


class ClickableImage(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, clickable=False, *args, **kwargs):
        self.clickable = clickable
        super(ClickableImage, self).__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super(ClickableImage, self).mouseReleaseEvent(event)


class MessageBoxQt(object):
    @classmethod
    def showQuestion(cls, parent=None, title="", message="", buttonA="Continue", buttonB="Cancel", buttonC=None,
                     icon="Question"):
        """Simple function for a dialog window with two or three buttons with changeable button names.

        buttonC=None will not show the third button.

        Icons are "NoIcon", "Warning", "Question", "Information" or "Critical"

        Returns strings "A", "B" or "C" depending on the button pressed.

        :param parent: The parent widget, can leave as None and will parent to Maya
        :type parent: object
        :param title: The name title of the window
        :type title: str
        :param message: The message/question as presented to the user inside the window
        :type message: str
        :param buttonA: The string name of the first button
        :type buttonA: str
        :param buttonB: The string name of the second button
        :type buttonB: str
        :param buttonC: The string name of the third (optional) button, if None is ignored
        :type buttonC: str

        :return buttonPressed: The button pressed, either "A", "B" or "C"
        :rtype buttonPressed: str
        """
        box = QtWidgets.QMessageBox(parent=parent or utils.mayaMainWindow())
        if icon == "Warning":
            box.setIcon(QtWidgets.QMessageBox.Warning)
        elif icon == "Question":
            box.setIcon(QtWidgets.QMessageBox.Question)
        elif icon == "Information":
            box.setIcon(QtWidgets.QMessageBox.Information)
        elif icon == "Critical":
            box.setIcon(QtWidgets.QMessageBox.Critical)
        elif icon == "NoIcon":
            box.setIcon(QtWidgets.QMessageBox.NoIcon)

        logger.debug("Showing message box: ")
        logger.debug("  title: '{}'".format(title))
        logger.debug("  message: '{}'".format(message))

        box.setWindowTitle(title)
        box.setText(message)
        buttonA_pressed = box.addButton(buttonA, QtWidgets.QMessageBox.YesRole)
        buttonB_pressed = box.addButton(buttonB, QtWidgets.QMessageBox.NoRole)
        if buttonC:
            buttonC_pressed = box.addButton(buttonC, QtWidgets.QMessageBox.NoRole)
        else:
            buttonC_pressed = None
        box.exec_()
        if box.clickedButton() == buttonA_pressed:
            logger.debug("buttonA '{}' pressed.".format(buttonA))
            return "A"
        elif box.clickedButton() == buttonB_pressed:
            logger.debug("buttonB '{}' pressed.".format(buttonB))
            return "B"
        elif box.clickedButton() == buttonC_pressed:
            logger.debug("buttonC '{}' pressed.".format(buttonC))
            return "C"
        else:
            return None


def errorPopup(errorMessage, parent=None):
    """Handle when an error occurs

    Show the error in an error message window.
    """
    flags = QtWidgets.QMessageBox.StandardButton.Ok
    QtWidgets.QMessageBox.warning(parent or utils.mayaMainWindow(), "Error!", errorMessage, flags)


def restartMayaPopup(message, parent=None):
    """ Restart Maya popup

    :param message:
    :return: True if restarting, false otherwise
    """

    logger.debug("Quitting maya (cmds.quit())")
    sceneModified = utils.fileModified()
    if not sceneModified:  # Has been saved already so continue
        res = MessageBoxQt.showQuestion(parent=parent, title="Restart Maya?", message=message,
                                        buttonA="Restart Maya",
                                        buttonB="Restart Later")
        if res == "A":
            cmds.quit()  # restartMaya()
            return True
        else:
            return False

    saveRes = saveCurrentScene(message, title="Save and Restart?",
                               buttonA="Save and Restart Maya",
                               buttonB="Discard and Restart",
                               buttonC="Restart Later", parent=parent)
    if saveRes != "cancel":
        cmds.quit(force=True)  # restartMaya(force=True)
        return True
    return False


def copyDirectory(src, dst, ignorePattern=None, parent=None):
    """Copies the directory tree using shutil.copytree

    :param src: the Source directory to copy.
    :type src: str
    :param dst: the destination directory.
    :type dst: str

    :return directoryExists: True if the directory was copied. False if wasn't created
    :rtype directoryExists: bool
    """
    try:
        if ignorePattern:
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignorePattern))
            return True
        shutil.copytree(src, dst)

    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            message = "Failed to copy directory {} to destination: {}\n\n{}".format(src, dst, const.DID_NOT_INSTALL)
            om2.MGlobal.displayError(message)
            errorPopup(message, parent=parent)
            return False
    return True


def saveCurrentScene(message, buttonA="Save", buttonB="Discard", buttonC="Cancel", title="Save File", parent=None):
    """ Save current scene

    Checks if the file has already been saved. Returns "save", "discard" or "cancel".

    If not saved opens "save", "discard" or "cancel" window.  Returns the button pressed if "discard" or "cancel"

    If "save" is clicked it will try to save the current file, if cancelled will return "cancel"

    :return buttonClicked: The button clicked returned as a lower case string "save", "discard" or "cancel"
    :rtype buttonClicked: str
    """
    buttonPressed = MessageBoxQt.showQuestion(title=title,
                                              parent=parent,
                                              message=message,
                                              buttonA=buttonA,
                                              buttonB=buttonB,
                                              buttonC=buttonC)
    if buttonPressed == "A":
        if utils.saveAsDialogMaMb():  # file saved
            return "save"
        else:
            return "cancel"
    elif buttonPressed == "B":
        return "discard"
    else:
        return "cancel"


def makeDirectory(directory, parent=None):
    """Creates a new directory with error checking

    :param directory: a full path to a directory to create
    :type directory:

    :return directoryExists: True if the directory was created or it exists. False if wasn't created
    :rtype directoryExists: bool
    """
    try:
        if os.path.isdir(directory):
            return True  # already exists
        os.mkdir(directory)
        return True
    except OSError:
        message = "The directory could not be created: {} \n\n{}".format(directory, const.DID_NOT_INSTALL)
        om2.MGlobal.displayError(message)
        errorPopup(message, parent=parent)
        return False


def moveRootLocation(rootPath, destinationPath, parent=None):
    """ Physically moves the give root location to the destination directory.

    If the destination doesn't exist it will be created.

    :note: Using this function to move preferences requires a restart

    :param rootPath: The root name location which should be part of the this instance
    :type rootPath: str
    :param destinationPath: The absolute fullpath to the destination folder
    :type destinationPath: str
    :return: first element is whether the root was copied, second element \
    is the original root location
    :rtype: (bool, str)
    :raise: RootDoesntExistsError
    :raise: OSError
    :raise: RootDestinationAlreadyExistsError
    """
    # this will raise a RootDoesntExistsError if the root is missing

    destRoot = destinationPath
    makeDirectory(destinationPath, parent=parent)
    copy_tree(rootPath, destRoot)

    try:
        logger.debug("Removing Root preferences path: {}".format(rootPath))
        shutil.rmtree(rootPath)
        logger.debug("Removed Source preferences path: {}".format(rootPath))
    except OSError:
        logger.error("Failed to remove the preference root: {}".format(rootPath),
                     exc_info=True)
        raise
    return True
