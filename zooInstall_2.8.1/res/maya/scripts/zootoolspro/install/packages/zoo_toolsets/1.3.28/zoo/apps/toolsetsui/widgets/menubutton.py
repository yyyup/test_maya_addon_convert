from functools import partial

from zoo.preferences.interfaces import coreinterfaces

from zoovendor.Qt import QtCore

from zoo.apps.toolsetsui.widgets.toolseticonpopup import ToolsetIconPopup
from zoo.libs.pyqt.widgets import elements


class ToolsetMenuButton(elements.IconMenuButton):
    """ Toolset Menu Button (triple dot menu)

    The button that has three menus in one. Left click menu, middle click menu, and right click menu.

    Currently the toolset menu has 3 mouse click button behaviours:

    - Left click Menu: Opens the toolset groups menu (eg. Animation, Rigging, Retopology)
    - Middle Click Menu: Icon Popup Menu - a popup window that displays rows of icons of all the toolsets
    - Right Click Menu: Opens a menu with all the toolsets
    """
    menuIcon = "menudots"

    def __init__(self, parent=None, size=20, toolsetRegistry=None):
        """ Toolset Menu button

        :param parent:
        :type parent: zoo.apps.toolsetsui.widgets.toolsetframe.ToolsetFrame
        :param size:
        :type size: int
        :param toolsetRegistry:
        :type toolsetRegistry: zoo.apps.toolsetsui.registry.ToolsetRegistry
        """
        super(ToolsetMenuButton, self).__init__(parent=parent)
        self.toolsetFrame = parent  # type:

        self.themePref = coreinterfaces.coreInterface()
        self.setIconByName(self.menuIcon, self.themePref.MAIN_FOREGROUND_COLOR)
        self.toolsetRegistry = toolsetRegistry
        self.toolsetPopup = ToolsetIconPopup(toolsetFrame=self.toolsetFrame, toolsetRegistry=self.toolsetRegistry,
                                             iconSize=size)
        self.setIconSize(QtCore.QSize(size, size))
        self.setFixedWidth(25)

        self.initialiseMenus()

    def initUi(self):
        """ Initialize the ui

        :return:
        """
        super(ToolsetMenuButton, self).initUi()

        self.setSearchable(mouseMenu=QtCore.Qt.LeftButton, searchable=True)
        self.setSearchable(mouseMenu=QtCore.Qt.RightButton, searchable=True)
        self.setTearOffEnabled(mouseMenu=QtCore.Qt.LeftButton, tearoff=True)
        self.setTearOffEnabled(mouseMenu=QtCore.Qt.RightButton, tearoff=True)
        self.setWindowTitle("Toolset Groups", mouseMenu=QtCore.Qt.LeftButton)
        self.setWindowTitle("All Toolsets", mouseMenu=QtCore.Qt.RightButton)
        rmenu = self.menu(QtCore.Qt.RightButton)
        rmenu.setStyleSheet("QMenu { menu-scrollable: 1; }")

    def initialiseMenus(self):
        """ Initialise the left click, middle click and right click menu

        :return:
        """
        # LEFT CLICK menu with the groups
        for tg in self.toolsetRegistry.groupsData():
            color = tg['color']
            self.addAction(tg['name'],
                           mouseMenu=QtCore.Qt.LeftButton,
                           connect=partial(self.toolsetFrame.setGroup, tg['type']),
                           icon="roundedsquarefilled",
                           iconSize=20,
                           iconColor=color)

        # MIDDLE CLICK MENU with the toolset icon popup
        self.middleClicked.connect(self.toolsetMiddleClick)

        # RIGHT CLICK MENU that displays all the toolsets
        for td in self.toolsetRegistry.definitions(sort=True):
            if td.uiData.get("hidden", False) or td.id == "toolsetId":
                continue


            color = self.toolsetRegistry.toolsetColor(td.id)

            self.addAction(td.uiData['label'],
                           mouseMenu=QtCore.Qt.RightButton,
                           connect=partial(self.toolsetFrame.toggleToolset, td.id, True),
                           icon=td.uiData['icon'],
                           iconSize=20,
                           iconText=td.uiData['icon'],
                           iconColor=color)

    def toolsetMiddleClick(self):
        """ The middle click toolset icon popup

        :return:
        """
        pos = self.menuPos(QtCore.Qt.AlignRight, self.toolsetPopup)
        self.toolsetPopup.setTearOff(False)
        self.toolsetPopup.show(pos)


