from zoo.libs import iconlib
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.models import treemodel
from zoo.libs.pyqt.models import delegates
from zoo.libs.pyqt import utils
from zoo.libs.utils import output
from zoo.libs.utils import filesystem
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore


class TemplateLibrary(treeviewplus.TreeViewPlus):
    def __init__(self, templateReg, title="templates", parent=None, expand=True, sorting=True):
        super(TemplateLibrary, self).__init__(title, parent, expand, sorting)
        self.preference = coreinterfaces.coreInterface()
        self.preference.themeUpdated.connect(self.updateTheme)
        self._core = parent.core
        self._createView = parent
        self.templateRegistry = templateReg
        self._rootSource = TemplateDataSource({}, iconColor=[])

        self.treeView.setHeaderHidden(True)
        self.treeView.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)  # Remove dotted line on selection
        self.treeView.setIndentation(utils.dpiScale(10))
        self.setAlternatingColorEnabled(False)
        delegate = delegates.HtmlDelegate(parent=self.treeView)
        self.treeView.setItemDelegateForColumn(0, delegate)

        self.menuBtn = elements.IconMenuButton(parent=parent)
        self.templateModel = TemplateModel(self.templateRegistry, self._rootSource, parent=self)
        self.setModel(self.templateModel)
        self._setupLayout()
        self.refresh()
        self.contextMenuRequested.connect(self.onContextMenu)

    def updateTheme(self, event):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        iconColor = event.themeDict.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColor, size=16)

    def _setupLayout(self):
        self.menuBtn.setFixedHeight(utils.dpiScale(20))
        self.menuBtn.setFixedWidth(utils.dpiScale(22))
        iconColour = self.preference.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColour, size=16)
        self.toolbarLayout.setContentsMargins(*utils.marginsDpiScale(*(10, 6, 2, 0)))
        self.toolbarLayout.addWidget(self.menuBtn)

        self.menuBtn.addAction("Save Rig As Template", connect=self.onSaveAll, icon=iconlib.iconColorized("hive_save"))
        self.menuBtn.addAction("Save Selected Components", connect=self.onSaveSelected,
                               icon=iconlib.iconColorized("hive_save"))
        self.menuBtn.addAction("Rename Template", connect=self.onRenameTemplate, icon=iconlib.iconColorized("pencil"))
        self.menuBtn.addAction("Delete Template", connect=self.onDeleteTemplate, icon=iconlib.iconColorized("trash"))
        self.menuBtn.addAction("Update Rig from Template", connect=self.onUpdateFromTemplate,
                               icon=iconlib.iconColorized("upload"))
        self.menuBtn.addAction("Open Template Location", connect=self.onBrowserToTemplates,
                               icon=iconlib.iconColorized("globe"))

        self.menuBtn.addAction("Refresh", connect=self.onRefreshTemplates,
                               icon=iconlib.iconColorized("reload"))
        self.treeView.itemDoubleClicked.connect(self.onDoubleClicked)

    def refresh(self):
        self._rootSource.setUserObjects([])
        self.setSortingEnabled(False)
        self.templateModel.reloadTemplates()
        self.templateModel.reload()
        self.expandAll()
        self.setSortingEnabled(True)

    def onShowInExplorer(self, dataSource):
        filesystem.openLocation(dataSource.template["path"])
        output.displayInfo("OS window opened to the Path: `{}` folder location".format(dataSource.template["path"]))

    def onContextMenu(self, selection, menu):
        menu.setSearchVisible(False)
        menu.addActionExtended("Rename", connect=self.onRenameTemplate, icon=iconlib.iconColorized("pencil"))
        menu.addActionExtended("Delete", connect=self.onDeleteTemplate, icon=iconlib.iconColorized("trash"))
        menu.addActionExtended("Update Rig from Template", connect=self.onUpdateFromTemplate,
                               icon=iconlib.iconColorized("upload"))
        menu.addSeparator()
        menu.addActionExtended("Open Folder Location", connect=self.onBrowserToTemplates,
                               icon=iconlib.iconColorized("globe"))

    def onBrowserToTemplates(self):
        selection = self.selectedItems()
        if not selection:
            output.displayWarning("Please Select at least one template.")
            return
        for selectedItem in selection:
            filesystem.openLocation(selectedItem.template["path"])
            output.displayInfo(
                "OS window opened to the Path: `{}` folder location".format(selectedItem.template["path"]))

    def onDoubleClicked(self, index):
        item = self.templateModel.itemFromIndex(index)
        if item:
            self._createView.addTemplate(item.template["name"])

    def onSaveAll(self):
        self._core.executeTool("saveTemplate", {"exportAll": True})
        self.refresh()

    def onSaveSelected(self):
        self._core.executeTool("saveTemplate")
        self.refresh()

    def onDeleteTemplate(self):
        self._core.executeTool("deleteTemplate")
        self.refresh()

    def onRenameTemplate(self):
        self._core.executeTool("renameTemplate")
        self.refresh()

    def onRefreshTemplates(self):
        self._core.executeTool("refreshTemplates")
        self.refresh()

    def onUpdateFromTemplate(self):
        self._core.executeTool("updateRigUpdateTemplate")


class TemplateModel(treemodel.TreeModel):

    def __init__(self, templateRegistry, root, parent=None):
        super(TemplateModel, self).__init__(root, parent)
        self.themePref = coreinterfaces.coreInterface()
        self.templateRegistry = templateRegistry

    def reloadTemplates(self):
        col = self.themePref.HIVE_TEMPLATE_COLOR
        for n, path in sorted(self.templateRegistry.templates.items()):
            template = self.templateRegistry.template(n)
            templateInfo = {"name": n,
                            "path": path,
                            "icon": template.get("icon", "")}
            source = TemplateDataSource(templateInfo, model=self, parent=self.root, iconColor=col)
            self.root.addChild(source)


class TemplateDataSource(datasources.BaseDataSource):

    def __init__(self, template, iconColor, headerText=None, model=None, parent=None):
        super(TemplateDataSource, self).__init__(headerText, model, parent)
        self.template = template
        _icon = template.get('icon') or "template"
        iconName = _icon or "template"

        self._icon = iconlib.iconColorizedLayered(['roundedsquarefilled', iconName], size=utils.dpiScale(16),
                                                  colors=[iconColor], iconScaling=[1, 0.8])

    def data(self, index):
        return self.template["name"].replace("component", "")

    def icon(self, index):
        return self._icon

    def isEditable(self, index):
        return False

    def foregroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return self.enabledColor
