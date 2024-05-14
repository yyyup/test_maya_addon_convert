from zoo.apps.hiveartistui.views import treewidgetframe
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import groupedtreewidget, iconmenu
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore

BETA_LABEL = " Beta"


class ComponentLibrary(treewidgetframe.TreeWidgetFrame):
    """
    The component library which shows the list of components currently available to the
    user. On clicking one of the elements it will create one component and add it to the
    ComponentTreeView.

    ComponentLibrary
        toolbarLayout (With Search and extra buttons)
        ComponentLibraryWidget (Widget with list of possible components to add)
            TreeWidgetItem (Items of the Tree)
                ComponentItemWidget(Each TreeWidgetItem has the an ItemWidget which interacts with the user)

            TreeWidgetItem (Items of the Tree)
                ComponentItemWidget(Each TreeWidgetItem has the an ItemWidget which interacts with the user)

            etc...

    ComponentLibrarySettings (Settings dialogue when you right click and click settings if it is needed)

    """

    def __init__(self, componentReg=None, componentMdlReg=None, parent=None, locked=False):
        """

        :param componentReg:
        :type componentReg: hive.zoo.libs.hivebase.registry.TemplateRegistry
        :param parent:
        :type parent:  zoo.apps.hiveartistui.views.createui.CreateView
        """
        super(ComponentLibrary, self).__init__(parent=parent, title="COMPONENTS")
        self.preference = coreinterfaces.coreInterface()
        self.menuBtn = iconmenu.IconMenuButton(parent=parent)
        compWidget = ComponentLibraryWidget(componentReg, componentMdlReg, parent, locked)
        compWidget.setDragDropEnabled(False)
        self.initUi(compWidget)

        self.connections()
        self.preference.themeUpdated.connect(self.updateTheme)

    def updateTheme(self, event):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        iconColor = event.themeDict.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColor, size=16)

    def setupToolbar(self):
        """ Set up toolbar
        The toolbar for the ComponentTreeView which will have widgets such as the searchbar,
        and other useful buttons.
        :return:
        """

        super(ComponentLibrary, self).setupToolbar()

        self.menuBtn.setFixedHeight(20)
        iconColour = self.preference.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColour, size=16)

        self.toolbarLayout.addWidget(self.menuBtn)
        self.menuBtn.hide()  # todo: reimplement

        self.menuBtn.addAction("Add Group", connect=self.addGroup, icon=iconlib.iconColorized("folder",
                                                                                              size=utils.dpiScale(32)))
        self.menuBtn.addAction("Delete Group", connect=self.deleteGroup, icon=iconlib.iconColorized("trash"))


class ComponentLibraryWidget(groupedtreewidget.GroupedTreeWidget):
    """ The ComponentLibraryWidget.

    The TreeWidget with the list of components that we can add to the rig. We can add components to the rig here,
    drag and drop elements that is only for this widget If you dont want to move things around, set locked to True.

    """

    def __init__(self, componentReg, componentModelReg, parent=None, locked=False):
        """

        :param componentReg:
        :param componentModelReg:
        :param parent:
        :type parent: zoo.apps.hiveartistui.views.createview.CreateView
        :param locked:
        """
        self.componentRegistry = componentReg
        self.componentModelRegistry = componentModelReg
        self.createView = parent
        self.themePref = coreinterfaces.coreInterface()
        self._groupIcon = iconlib.iconColorized("openFolder01", size=utils.dpiScale(64))
        super(ComponentLibraryWidget, self).__init__(parent, locked)

        self.themePref.themeUpdated.connect(self.updateTheme)
        self.setRootIsDecorated(True)

    def initUi(self):
        """
        Gets a list of components through the componentRegistry and puts it into the Tree.
        :return:
        """
        self.setSortingEnabled(False)
        super(ComponentLibraryWidget, self).initUi()

        components = []
        for n, d in self.componentRegistry.components.items():
            components.append((n, d["object"].betaVersion))

        for i, [c, isBeta] in enumerate(components):
            wgt = ComponentItemWidget(c, componentModelRegistry=self.componentModelRegistry,
                                      actionEvent=self.createComponent, parent=self)
            name = c.replace("component", "")
            if isBeta:
                name += BETA_LABEL
            self.addNewItem(name, wgt, icon=wgt.icon, widgetInfo=c)

        self.setCurrentItem(None)
        self.setSortingEnabled(True)
        self.sortItems(0, QtCore.Qt.AscendingOrder)

    def updateTheme(self, event):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        for item in self.iterator():
            widget = self.itemWidget(item)
            icon = widget.generateIcon(event.themeDict)
            item.setIcon(0, icon)

    def createComponent(self):
        """ Send the createComponent upstream to the view so it can create it in the HiveUI.
        May switch this to use signals.
        :return:
        """
        self.createView.createComponent(self.sender().name.replace(BETA_LABEL, ""))

    def addGroup(self, name="", expanded=True, groupSelected=True, groupWgt=None):
        """ Adds a group or folder directory to the tree

        :param name:
        :param expanded:
        :param groupSelected:
        :param groupWgt:
        :return:
        """
        group = super(ComponentLibraryWidget, self).addGroup(name, expanded, groupSelected, groupWgt)
        group.setIcon(groupedtreewidget.WIDGET_COL, self._groupIcon)
        return group

    def updateWidget(self, item):
        """ Update the QTreeWidgetItem to its itemWidget.

        In this case it is the ComponentWidget

        :param item:
        :return:
        """
        # Retrieve the componentModel that is stored in the item
        componentName = self.itemWidgetInfo(item)
        wgt = ComponentItemWidget(componentName, componentModelRegistry=self.componentModelRegistry,
                                  actionEvent=self.createComponent, parent=self)
        self.setItemWidget(item, groupedtreewidget.WIDGET_COL, wgt)

    def updateGroupWidget(self, item):
        groupWidget = super(ComponentLibraryWidget, self).updateGroupWidget(item)
        groupWidget.setFixedHeight(10)
        return groupWidget


class ComponentItemWidget(groupedtreewidget.ItemWidgetLabel):
    def __init__(self, name, componentModelRegistry, actionEvent=None, parent=None):
        """

        :param name:
        :param componentModelRegistry:
        :param actionEvent:
        :param parent:
        """
        self.name = name
        self.componentModelRegistry = componentModelRegistry
        self.icon = None
        self.themePref = coreinterfaces.coreInterface()

        super(ComponentItemWidget, self).__init__("", parent=parent)

        self.connectEvent(actionEvent)

    def initUi(self):
        super(ComponentItemWidget, self).initUi()

        col = self.themePref.HIVE_COMPONENT_COLOR
        self.icon = iconlib.iconColorizedLayered(['roundedsquarefilled', self.componentIcon()], size=utils.dpiScale(16),
                                                 colors=[col], iconScaling=[1, 0.7])

    def generateIcon(self, themeDict):
        """ Generate the icon that will be used in the item

        :type themeDict: preferences.interface.themedict.ThemeDict
        :return:
        :rtype:
        """
        col = themeDict.HIVE_COMPONENT_COLOR
        icon = iconlib.iconColorizedLayered(['roundedsquarefilled', self.componentIcon()], size=utils.dpiScale(16),
                                            colors=[col], iconScaling=[1, 0.7])

        return icon

    def componentIcon(self):
        return self.componentModelRegistry.findComponent(self.name).icon
