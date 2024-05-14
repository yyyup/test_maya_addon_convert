import itertools

from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.views import componentsettings
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import strutils
from functools import partial
from zoo.libs.commands import hive


class ArmComponentModel(model.ComponentModel):
    """Base Class for Vchain class and subclasses to support better UI
    organization.
    """
    componentType = "armcomponent"

    def createWidget(self, componentWidget, parentWidget):
        return VChainSettingsWidget(componentWidget,
                                    parentWidget,
                                    componentModel=self)


class LegComponentModel(ArmComponentModel):
    componentType = "legcomponent"


class VChainSettingsWidget(componentsettings.ComponentSettingsWidget):
    def __init__(self, componentWidget, parent, componentModel):
        self.twistSegmentWidgets = []
        self.bendySettingWidgets = []
        super(VChainSettingsWidget, self).__init__(componentWidget, parent, componentModel)

    def initUi(self):
        self.generalSettingsLayout = elements.CollapsableFrameThin("Advanced Settings", parent=self,
                                                                   collapsed=True)
        self.twistSettingsLayout = elements.CollapsableFrameThin("Twist Settings", parent=self.generalSettingsLayout,
                                                                 collapsed=True)
        self.bendySettingsLayout = elements.CollapsableFrameThin("Bendy Settings", parent=self.generalSettingsLayout,
                                                                 collapsed=True)
        self.generalSettingsLayout.addWidget(self.twistSettingsLayout)
        self.generalSettingsLayout.addWidget(self.bendySettingsLayout)
        layout = self.layout()

        guideLayerDef = self.componentModel.component.definition.guideLayer
        primarySettings = guideLayerDef.guideSettings("hasStretch", "ikfk_default",
                                                      "hasTwists", "hasBendy", "uprSegmentCount",
                                                      "lwrSegmentCount", "distributionType")
        self._createIKFKWidget(primarySettings, layout)
        hasTwists = primarySettings["hasTwists"]
        hasBendy = primarySettings["hasBendy"]
        hasStretch = primarySettings["hasStretch"]

        hasStretchWidget = componentsettings.createBooleanWidget(self, hasStretch, "Has Stretch", layout,
                                                                 self.onHasStretch)
        twistsBendyWidget = componentsettings.createRadioWidget(self, [None, hasTwists, hasBendy],
                                                                ["No Twists", "Twists", "Twists & Bendy(Beta)"], layout,
                                                                self.onTwistsBendyChanged)
        self.settingsWidgets.append((hasStretch, hasStretchWidget))
        self.settingsWidgets.append((hasTwists, twistsBendyWidget))

        layout.addWidget(self.generalSettingsLayout)
        self.createSpaceLayout()

        self.generalSettingsLayout.toggled.connect(partial(self.componentWidget.tree.updateTreeWidget, delay=True))
        self.twistSettingsLayout.toggled.connect(partial(self.componentWidget.tree.updateTreeWidget, delay=True))
        self.bendySettingsLayout.toggled.connect(self._onToggleBendyWidget)
        self.generalSettingsLayout.setEnabled(hasTwists.value or hasBendy.value)
        self.twistSettingsLayout.setEnabled(hasTwists.value)
        self.bendySettingsLayout.setEnabled(hasBendy.value)

        if hasTwists.value:
            self._createTwistWidgets(guideLayerDef, primarySettings, self.twistSettingsLayout)

        self.createNamingConventionLayout()

    def onHasStretch(self, checkbox, guideSetting, state):
        self.settingCheckboxChanged(checkbox, guideSetting, state)

    def onTwistsBendyChanged(self, event):
        """

        :param event:
        :type event: :class:`zoo.libs.pyqt.widgets.joinedRadio.JoinedRadioButtonEvent`
        """
        hasTwists = False
        hasBendy = False
        if event.index == 0:  # None
            self.generalSettingsLayout.setEnabled(False)
            if not self.generalSettingsLayout.collapsed:
                # Hack to hide the flickering on collapse. Updates are re-enabled on tree.updateTreeWidget
                self.componentWidget.tree.setUpdatesEnabled(False)
                self.generalSettingsLayout.onCollapsed()
        elif event.index == 1:  # hasTwists
            hasTwists = True
            self.generalSettingsLayout.setEnabled(True)
            self.twistSettingsLayout.setEnabled(True)
            self.bendySettingsLayout.setEnabled(False)
        else:  # bendy + twists
            hasBendy = True
            hasTwists = True
            self.twistSettingsLayout.setEnabled(True)
            self.bendySettingsLayout.setEnabled(True)
            self.generalSettingsLayout.setEnabled(True)

        self.componentWidget.tree.updateTreeWidget(delay=True)
        hive.updateGuideSettings(self.componentModel.component, {"hasTwists": hasTwists,
                                                                 "hasBendy": hasBendy})

    def _createIKFKWidget(self, primarySettings, layout):
        """ creates the enum attribute to choose the default state for the ik fk switch.

        :param primarySettings: The list of guide settings for twists.
        :type primarySettings: dict[str, :class:`zoo.libs.hive.api.AttributeDefinition`]
        :param layout: The parent widget for the widget.
        :type layout: :class:`QtWidgets.QVBoxLayout`
        """
        ikfkDefault = primarySettings["ikfk_default"]
        combo = componentsettings.createEnumWidget(self, ikfkDefault, strutils.titleCase("Ikfk Default"),
                                                   layout, ["IK", "FK"], self.enumChanged)
        self.settingsWidgets.append((primarySettings["ikfk_default"], combo))
        layout.addWidget(combo)

    def _createTwistWidgets(self, guideLayerDefinition, primarySettings, layout):
        """
        :param guideLayerDefinition: The current components guide layer definition instance
        :type guideLayerDefinition: :class:`zoo.libs.hive.api.GuideLayerDefinition`
        :param primarySettings: The list of guide settings for twists.
        :type primarySettings: dict[str, :class:`zoo.libs.hive.api.AttributeDefinition`]
        :param layout: The collapsableFrame Layout which is a widget but has layout methods.
        :type layout: :class:`elements.CollapsableFrame`
        """
        self._clearTwistSettings()
        uprSegment = primarySettings["uprSegmentCount"]
        lwrSegment = primarySettings["lwrSegmentCount"]
        distributionType = primarySettings["distributionType"]
        componentsettings.createEnumWidget(self, distributionType, "Distribution Type",
                                           layout, None, self._onDistributionChanged)
        self.uprTwistSegmentWidget = componentsettings.createIntWidget(self, uprSegment, "Upr Segment Count",
                                                                       layout, self._onSegmentValueChanged)

        self.lwrTwistSegmentWidget = componentsettings.createIntWidget(self, lwrSegment, "Lwr Segment Count",
                                                                       layout, self._onSegmentValueChanged)
        if distributionType.value == 0:
            self.uprTwistSegmentWidget.setMinValue(1)
            self.lwrTwistSegmentWidget.setMinValue(1)
        else:
            self.uprTwistSegmentWidget.setMinValue(3)
            self.lwrTwistSegmentWidget.setMinValue(3)

        self.settingsWidgets.append((uprSegment, self.uprTwistSegmentWidget))
        self.settingsWidgets.append((lwrSegment, self.lwrTwistSegmentWidget))
        # segment count change
        self._createSegmentWidgets(itertools.chain(*self.componentModel.component.twistIds()),
                                   guideLayerDefinition, layout)

    def _onToggleBendyWidget(self):
        if self.bendySettingsLayout.collapsed:
            self._createBendyWidgets(self.componentModel.component.definition.guideLayer, self.bendySettingsLayout)
        self.componentWidget.tree.updateTreeWidget(delay=True)

    def _createBendyWidgets(self, guideLayerDef, layout):
        self._clearBendySettings()

        for bendyCtrlId in self.componentModel.component.bendyIds():
            settingDef = guideLayerDef.guideSetting("{}Position".format(bendyCtrlId))
            if settingDef is None:
                continue

            bendyWidget = componentsettings.createFloatWidget(self, settingDef,
                                                              strutils.titleCase(settingDef.name),
                                                              layout, self.settingNumericChanged)
            bendyWidget.setMinValue(0.0)
            bendyWidget.setMaxValue(1.0)
            self.bendySettingWidgets.append(bendyWidget)

    def _onDistributionChanged(self, event, widget, setting):
        """Called when the twist distribution type has changed.

        :type event:  :class:`zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent`
        :param widget: The combo box for the enum attribute.
        :type widget: :class:`elements.ComboBoxRegular`
        :param setting: The guide setting
        :type setting: :class:`zao.libs.hive.api.AttributeDefinition`
        """
        self.enumChanged(event, widget, setting)
        if event.index == 0:
            self.uprTwistSegmentWidget.setMinValue(0)
            self.lwrTwistSegmentWidget.setMinValue(0)
        else:
            self.uprTwistSegmentWidget.setMinValue(3)
            self.lwrTwistSegmentWidget.setMinValue(3)

    def _createSegmentWidgets(self, guideIds, guideLayerDefinition, layout):
        """Generates All widgets for a single twist Segment.

        Note you need to handle refresh the treewidget for size hinting . We don't
        handle this here for optimisation.

        :param guideIds: The list of guide ids for twists to display in the UI.
        :type guideIds: list[str]
        :param guideLayerDefinition: The current components guide layer definition instance
        :type guideLayerDefinition: :class:`zoo.libs.hive.api.GuideLayerDefinition`
        :param layout: The collapsableFrame Layout which is a widget but has layout methods.
        :type layout: :class:`elements.CollapsableFrame`
        """
        for twistSetting in sorted(guideLayerDefinition.guideSettings(*guideIds).values(),
                                   key=lambda x: x.name):
            edit = componentsettings.createFloatWidget(self, twistSetting,
                                                       strutils.titleCase(twistSetting.name),
                                                       layout, self.settingNumericChanged)
            self.settingsWidgets.append((twistSetting, edit))
            self.twistSegmentWidgets.append(edit)

    def _onSegmentValueChanged(self, widget, setting):
        """Called when the twist segment count has changed.

        Updates hive component which will handle scene state.
        Purges current twist widgets and rebuilds from new count and then lets the treewidget
        know to handle the size hint.

        :param widget: The zoo tools integer edit widget
        :type widget: :class:`elements.IntEdit`
        :param setting: The guide setting
        :type setting: :class:`zao.libs.hive.api.AttributeDefinition`
        """

        changed = self.settingNumericChanged(widget, setting)
        if not changed:
            return
        guideLayerDef = self.componentModel.component.definition.guideLayer
        for twistWidget in self.twistSegmentWidgets:
            twistWidget.deleteLater()
        self.twistSegmentWidgets = []
        self._createSegmentWidgets(itertools.chain(*self.componentModel.component.twistIds()),
                                   guideLayerDef, self.twistSettingsLayout)
        self.componentWidget.tree.updateTreeWidget()

    def _clearTwistSettings(self):
        for edit in self.twistSegmentWidgets:
            edit.deleteLater()
        self.twistSegmentWidgets = []
        self.settingsWidgets = []

    def _clearBendySettings(self):
        for edit in self.bendySettingWidgets:
            edit.deleteLater()
        self.bendySettingWidgets = []
