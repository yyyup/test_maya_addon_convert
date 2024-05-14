from functools import partial

from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.views import componentsettings
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants
from zoo.libs.utils import general
from zoo.libs.maya.qt import mayaui
from zoo.libs.maya import zapi
from zoo.core.util import strutils

if general.TYPE_CHECKING:
    from zoo.libs.hive.library.components.organic.spine import spineikcomponent


class SpineIkComponentModel(model.ComponentModel):
    """Base Class for SpineIK class and subclasses to support better UI
    organization.
    """
    componentType = "spineIk"

    def createWidget(self, componentWidget, parentWidget):
        return SpineIkSettingsWidget(componentWidget,
                                     parentWidget,
                                     componentModel=self)


class SpineIkSettingsWidget(componentsettings.ComponentSettingsWidget):
    showSpaceSwitching = True

    def __init__(self, componentWidget, parent, componentModel):
        super(SpineIkSettingsWidget, self).__init__(componentWidget, parent, componentModel)
        self._distanceWidgets = []
        self._generalSettingsLayoutCreated = False

    def initUi(self):
        guideLayerDef = self.componentModel.component.definition.guideLayer
        primarySettings = guideLayerDef.guideSettings("jointCount", "fkCtrlCount",
                                                      "ikJointCount")
        for settingName, setting in primarySettings.items():
            func = self.settingNumericChanged
            if settingName == "jointCount":
                func = self._onBindJointCountChanged
            componentsettings.createIntWidget(self, setting,
                                              strutils.titleCase(settingName),
                                              self.layout(),
                                              func,
                                              )

        self.generalSettings = elements.CollapsableFrameThin("General Settings", parent=self,
                                                             collapsed=True)
        self.generalSettings.closeRequested.connect(
            partial(self.componentWidget.tree.updateTreeWidget, True))
        self.generalSettings.openRequested.connect(self.onGeneralSettingsFrameOpen)

        layout = self.layout()
        layout.addWidget(self.generalSettings)
        self.createSpaceLayout()
        self.createNamingConventionLayout()

    def _onBindJointCountChanged(self, widget, setting, *args, **kwargs):
        self.settingNumericChanged(widget, setting, *args, **kwargs)
        self._createDistanceSettings()
        self.componentWidget.tree.updateTreeWidget(True)

    def _onSquashBtnClicked(self):
        mayaui.openGraphEditor()
        component = self.componentModel.component  # type: spineikcomponent.SpineIkComponent
        zapi.select([component.animCurve()])

    def _createDistanceSettings(self):
        self.clearDistanceSettings()
        component = self.componentModel.component  # type: spineikcomponent.SpineIkComponent
        definition = component.definition
        for index in range(definition.guideLayer.guideSetting("jointCount").value):
            guideId = component.jointIdForNumber(index)
            guideSetting = definition.guideLayer.guideSetting("{}Distance".format(guideId))
            wid = componentsettings.createFloatWidget(self, guideSetting,
                                                      strutils.titleCase(guideSetting.name),
                                                      self.generalSettings.hiderLayout,
                                                      self.settingNumericChanged,
                                                      supportsSlider=True
                                                      )
            self._distanceWidgets.append(wid)

    def clearDistanceSettings(self):
        for wid in self._distanceWidgets:
            wid.deleteLater()
        self._distanceWidgets = []

    def onGeneralSettingsFrameOpen(self):
        if self._generalSettingsLayoutCreated:
            self.componentWidget.tree.updateTreeWidget(True)
            return

        self._generalSettingsLayoutCreated = True
        tooltip = ""
        curveBtn = elements.styledButton("Edit Squash Profile",
                                         icon="graphEditor",
                                         toolTip=tooltip,
                                         style=uiconstants.BTN_DEFAULT)
        self.generalSettings.hiderLayout.addWidget(curveBtn)
        curveBtn.clicked.connect(self._onSquashBtnClicked)
        self._createDistanceSettings()
        self.componentWidget.tree.updateTreeWidget(True)
