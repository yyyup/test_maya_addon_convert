from zoo.apps.hiveartistui import hivetool, utils
from zoo.libs.commands import hive
from zoo.libs.hive import api
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.utils import general
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output


class SaveTemplateTool(hivetool.HiveTool):
    id = "saveTemplate"
    uiData = {
        "icon": "hive_save",
        "label": "Template Menu"
    }

    def execute(self, exportAll=False):
        if not self.rigModel:
            return
        selectedItems = self.uiInterface.templateLibrary().selectedItems()
        rig = self.rigModel.rig
        if not selectedItems:
            templateName = rig.name()
        else:
            templateName = selectedItems[0].template["name"]
        if exportAll:
            components = []
        else:
            components = [c.component for c in self.selectedModels]
            if not components:
                output.displayWarning("Please Select at least one component to save")
                return
        name = elements.MessageBox.inputDialog(parent=self.parentWidget,
                                               title="New Template",
                                               text=templateName or "Template",
                                               message="Name of new template:"
                                               )
        if not name:
            return
        registry = api.Configuration().templateRegistry()
        if registry.hasTemplate(name):
            state = elements.MessageBox.showOK(title="Confirm", parent=self.parentWidget,
                                               message="Template already exists, do wish to override?",
                                               icon="Question",
                                               default=1, buttonA="Yes", buttonB="No")
            if not state:
                return
        hive.saveTemplate(rig, name, components)
        self.requestRefresh()

    def variants(self):
        return [
            {"id": "default",
             "name": "Save Selected Template",
             "icon": "hive_save",
             "args": {}},
            {"id": "all",
             "name": "Save All Templates",
             "icon": "hive_save",
             "args": {"exportAll": True}}
        ]


class DeleteTemplateTool(hivetool.HiveTool):
    id = "deleteTemplate"
    uiData = {
        "icon": "trash",
        "label": "Delete Template"
    }

    def execute(self):
        selectedItems = self.uiInterface.templateLibrary().selectedItems()
        if not selectedItems:
            return
        templateName = selectedItems[0].template["name"]
        if not elements.MessageBox.showOK(title="Confirm", parent=self.parentWidget,
                                          message="Are you sure you wish to delete template: {}".format(templateName),
                                          icon="Question",
                                          default=0, buttonA="Yes", buttonB="No"):
            return
        hive.deleteTemplate(templateName)
        self.requestRefresh()


class RenameTemplateTool(hivetool.HiveTool):
    id = "renameTemplate"
    uiData = {
        "icon": "pencil",
        "label": "Rename Template"
    }

    def execute(self):
        templateLibrary = self.uiInterface.templateLibrary()
        selectedItems = templateLibrary.selectedItems()
        if not selectedItems:
            return
        templateName = selectedItems[0].template["name"]
        newName = elements.MessageBox.inputDialog(parent=self.parentWidget,
                                                  title="Rename Template", text=templateName,
                                                  message="New name of template:")
        if not newName:
            return
        api.Configuration().templateRegistry().renameTemplate(templateName, newName)
        self.requestRefresh()


class LoadFromFromTemplate(hivetool.HiveTool):
    id = "loadFromTemplate"
    uiData = {
        "icon": "pencil",
        "label": "Load From Template"
    }

    def execute(self):
        success = utils.checkSceneUnits(parent=self.uiInterface.artistUi())
        if not success:
            return

        templateLibrary = self.uiInterface.templateLibrary()
        selectedItems = templateLibrary.selectedItems()
        if not selectedItems:
            return
        templateName = selectedItems[0].template["name"]
        rigModel = self.rigModel
        rig = None
        if rigModel is not None:
            rig = rigModel.rig
        if rig:
            typeIndex, _ = elements.MessageBox.showMultiChoice(title="Confirm Choice", parent=self.parentWidget,
                                                               message="Do you wish to add to the current rig or "
                                                                       "replace It?",
                                                               choices=("Add", "Replace"),
                                                               showDiscard=False, default=0, buttonC="Cancel")
            if typeIndex == -1:
                return
            elif typeIndex == 0 or not rig:
                hive.loadTemplate(
                    filePath=self.uiInterface.artistUi().hiveConfig.templateRegistry().templatePath(templateName),
                    rig=rig)
            else:
                with general.undoContext("ReplaceAndLoadHiveTemplate"):
                    hive.deleteRig(rig)
                    hive.loadTemplate(
                        filePath=self.uiInterface.artistUi().hiveConfig.templateRegistry().templatePath(templateName))
        else:
            hive.loadTemplate(
                filePath=self.uiInterface.artistUi().hiveConfig.templateRegistry().templatePath(templateName))

        self.requestRefresh()


class RefreshTemplates(hivetool.HiveTool):
    id = "refreshTemplates"
    uiData = {
        "icon": "reload",
        "label": "Refresh Hive Templates"
    }

    def execute(self):
        self.uiInterface.artistUi().hiveConfig.templateRegistry().refresh()


class UpdateRigUpdateTemplate(hivetool.HiveTool):
    id = "updateRigUpdateTemplate"
    uiData = {
        "icon": "upload",
        "label": "Update Rig from Template"
    }

    def execute(self):
        templateLibrary = self.uiInterface.templateLibrary()
        selectedItems = templateLibrary.selectedItems()
        if not selectedItems:
            return
        templateName = selectedItems[0].template["name"]
        rigModel = self.rigModel
        rig = None
        if rigModel is not None:
            rig = rigModel.rig
        if rig:
            templateData = api.Configuration().templateRegistry().template(templateName)
            valid = api.templateutils.validateUpdateRigFromTemplate(rig, templateData)
            if valid:
                compNames = ", ".join([comp.serializedTokenKey() for comp in valid["missingComponents"]])
                elements.MessageBox.showWarning(parent=self.parentWidget,
                                                title="Invalid rig",
                                                message="Rig contains components which don't exist in the template.\n"
                                                        "At this time we don't support this behavior.\n"
                                                        "Offending Components : {}".format(compNames),
                                                buttonA=None,
                                                buttonB="OK")
                return
            choice = elements.MessageBox.showSave(title="Save Scene", parent=self.parentWidget,
                                                  message="Updating the Rig is Destructive and there"
                                                          " is no going back, recommend saving the scene")
            if choice == "cancel":
                return
            elif choice == "save":
                if not saveexportimport.saveAsDialogMaMb():  # file saved
                    return

            api.commands.updateRigFromTemplateData(rig,
                                                   templateData,
                                                   {})  # todo: remapUI
            self.requestRefresh(True)
