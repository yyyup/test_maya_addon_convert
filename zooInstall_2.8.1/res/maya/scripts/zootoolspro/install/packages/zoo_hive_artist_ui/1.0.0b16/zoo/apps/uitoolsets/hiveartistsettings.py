from functools import partial

from zoo.apps.hiveartistui import uiinterface
from zoo.apps.hiveartistui.hivenaming import presetwidget
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.hive import api as hiveapi
from zoo.libs.hive.library.tools.toolui import buildscriptwidget
from zoo.libs.maya.qt import mayaui
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.preferences.interfaces import hiveinterfaces
from zoovendor.Qt import QtWidgets, QtCore

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class HiveArtistSettings(toolsetwidget.ToolsetWidget):
    id = "hiveArtistSettings"
    info = "Hive artist ui settings"
    uiData = {"label": "Global Rig Settings",
              "icon": "zoo_preferences",
              "tooltip": "Hive Artist ui settings",
              "defaultActionDoubleClick": False,
              "hidden": True}

    rigRenamed = QtCore.Signal()

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self._currentRig = None
        self._hivePreferences = hiveinterfaces.hiveInterface()
        self._hiveSettings = self._hivePreferences.settings()

    def resetUi(self):
        for widget in self.widgets():
            widget.buildScriptsWidget.clear()
        super(HiveArtistSettings, self).resetUi()

    @property
    def currentRig(self):
        """

        :return:
        :rtype: :class:`hiveapi.Rig`
        """
        return self._currentRig

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [GuiCompact(parent=self, properties=self.properties)]

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[:class:`GuiCompact`]
        """
        return super(HiveArtistSettings, self).widgets()

    def setRig(self, rig):
        """

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        :return:
        :rtype:
        """

        self._currentRig = rig
        self.properties.rigNameEdit.value = rig.name()
        self.properties.containerRadioGroup.value = rig.configuration.useContainers
        self.properties.blackBoxCheckBox.value = rig.configuration.blackBox
        self.properties.childHighlighting.value = rig.configuration.selectionChildHighlighting
        self.properties.autoAlignGuidesCheckBox.value = rig.configuration.autoAlignGuides

        self.properties.containerAttrsShowAtTopCheckBox.value = self._hiveSettings["settings"][
            "containerAttrsShowAtTop"]
        self.properties.containerOutlinerDisplayUnderParentCheckBox.value = self._hiveSettings["settings"][
            "containerOutlinerDisplayUnderParent"]
        self.properties.controlShapesHiddenCheckbox.value = rig.configuration.hideControlShapesInOutliner
        self.properties.useProxyAttributesCheckBox.value = rig.configuration.useProxyAttributes
        self.updateFromProperties()
        buildScriptRegistry = self._currentRig.configuration.buildScriptRegistry()
        buildScriptCurrentProperties = self._currentRig.configuration.buildScriptConfig(rig)
        for widget in self.widgets():
            widget.buildScriptsWidget.setItemList(
                [{"id": i,
                  "label": i,
                  "properties": plugin.properties(),
                  "defaultPropertyValue": buildScriptCurrentProperties.get(i, {})
                  }
                 for i, plugin in buildScriptRegistry.plugins.items()]
            )
            widget.buildScriptsWidget.setCurrentItems([i.id for i in self._currentRig.configuration.buildScripts])
        self._setContainerUiState(not rig.configuration.useContainers)
        self._onBeforeBrowseNamingPreset()

    def updateUi(self):
        if self._currentRig:
            self.setRig(self._currentRig)

    # ------------------
    # LOGIC
    # ------------------

    def rigNameChanged(self, text):
        if self._currentRig:
            self._currentRig.rename(text)
            self.rigRenamed.emit()

    def useProxyChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig, settings={"useProxyAttributes": bool(state)})

    def _setContainerUiState(self, index):
        if index == 1:
            for widget in self.widgets():
                widget.blackBoxCheckBox.setEnabled(True)
                widget.containerOutlinerDisplayUnderParentCheckBox.setEnabled(True)
                widget.containerAttrsShowAtTopCheckBox.setEnabled(True)
        else:
            for widget in self.widgets():
                widget.blackBoxCheckBox.setEnabled(False)
                widget.containerOutlinerDisplayUnderParentCheckBox.setEnabled(False)
                widget.containerAttrsShowAtTopCheckBox.setEnabled(False)
        # required for the outliner to reflect the state change as it's not automatic
        mayaui.refreshOutliners()

    def useContainersChanged(self, index):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"useContainers": bool(index)})
            self._setContainerUiState(index)

    def blackBoxChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"blackBox": bool(state)})
            # required for the outliner to reflect the state change as it's not automatic
            mayaui.refreshOutliners()

    def childHighlightingChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"selectionChildHighlighting": bool(state)})

    def autoAlignChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"autoAlignGuides": bool(state)})

    def singleChainHierChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"singleChainHierarchy": bool(state)})

    def containerAttrsShowAtTopChanged(self, state):
        if self._currentRig:
            hiveapi.sceneutils.setMayaUIContainerDisplaySettings(attrsShowAtTop=bool(state))
            self._hiveSettings["settings"]["containerAttrsShowAtTop"] = bool(state)
            self._hiveSettings.save()

    def containerOutlinerDisplayUnderParentChanged(self, state):
        if self._currentRig:
            hiveapi.sceneutils.setMayaUIContainerDisplaySettings(outlinerDisplayUnderParent=bool(state))
            self._hiveSettings["settings"]["containerOutlinerDisplayUnderParent"] = bool(state)
            self._hiveSettings.save()

    def useProxyAttributesChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"useProxyAttributes": bool(state)})

    def onBuildScriptAdded(self, item):
        success = self._currentRig.configuration.addBuildScript(item["id"])
        if success:
            self._currentRig.saveConfiguration()

    def onBuildScriptRemoved(self, item):
        success = self._currentRig.configuration.removeBuildScript(item["id"])

        if success:
            self.currentRig.saveConfiguration()

    def onBuildScriptPropertyChanged(self, scriptName, propertyName, propertyValue):
        cfg = self.currentRig.configuration.buildScriptConfig(self.currentRig)
        currentData = cfg.get(scriptName, {})
        currentData.update({propertyName: propertyValue})

        self.currentRig.configuration.updateBuildScriptConfig(self.currentRig,
                                                              {scriptName: currentData}
                                                              )

    def controlShapesHiddenChanged(self, state):
        if self._currentRig:
            hiveapi.commands.updateRigConfiguration(self._currentRig,
                                                    settings={"hideControlShapesInOutliner": bool(state)})
            # required for the outliner to reflect the state change as it's not automatic
            mayaui.refreshOutliners()

    def _onBeforeBrowseNamingPreset(self):
        widget = self.currentWidget()
        currentRigPreset = self.currentRig.configuration.currentNamingPreset
        rootPreset = self.currentRig.configuration.namePresetRegistry().rootPreset
        if currentRigPreset is None:
            widget.namingPresetWidget.setText("No Preset Override")
        else:
            widget.namingPresetWidget.setText(currentRigPreset.name)
        widget.namingPresetWidget.setPreset(rootPreset)

    def _onBrowserNamingSelectionChanged(self, presetName):
        self.currentRig.configuration.setNamingPresetByName(presetName)
        self.currentRig.saveConfiguration()
        # update the Hive artist UI tree if available
        uiInstance = uiinterface.instance()
        tree = uiInstance.tree()
        if tree is not None:
            tree.sync()

    # ------------------
    # CONNECTIONS
    # ------------------

    def setEnabled(self, enabled):
        """ Set enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        for widget in self.widgets():
            widget.setEnabled(enabled)

    def uiConnections(self):
        """ ui Connections

        :return:
        :rtype:
        """
        for widget in self.widgets():
            widget.rigNameEdit.textModified.connect(self.rigNameChanged)
            widget.containerRadioGroup.toggled.connect(self.useContainersChanged)
            widget.blackBoxCheckBox.stateChanged.connect(self.blackBoxChanged)
            widget.childHighlighting.stateChanged.connect(self.childHighlightingChanged)
            widget.autoAlignGuidesCheckBox.stateChanged.connect(self.autoAlignChanged)
            widget.containerAttrsShowAtTopCheckBox.stateChanged.connect(self.containerAttrsShowAtTopChanged)
            widget.useProxyAttributesCheckBox.stateChanged.connect(self.useProxyAttributesChanged)
            widget.containerOutlinerDisplayUnderParentCheckBox.stateChanged.connect(
                self.containerOutlinerDisplayUnderParentChanged)
            widget.buildScriptsWidget.changed.connect(partial(self.updateTree, delayed=True))
            widget.buildScriptsWidget.addedScript.connect(self.onBuildScriptAdded)
            widget.buildScriptsWidget.removeScript.connect(self.onBuildScriptRemoved)
            widget.buildScriptsWidget.propertyChanged.connect(self.onBuildScriptPropertyChanged)
            widget.namingPresetWidget.beforeBrowseSig.connect(self._onBeforeBrowseNamingPreset)
            widget.namingPresetWidget.presetSelectedSig.connect(self._onBrowserNamingSelectionChanged)
            widget.controlShapesHiddenCheckbox.stateChanged.connect(self.controlShapesHiddenChanged)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties

        self.rigNameEdit = elements.StringEdit(label="Name", labelRatio=5, editRatio=16, parent=self)

        self.containerRadioGroup = elements.RadioButtonGroup(("No Containers", "Use Containers"),
                                                             default=0, parent=self,
                                                             alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.containerRadioGroup.radioButtons[0].setMinimumWidth(utils.dpiScale(140))
        self.containerRadioGroup.radioButtons[1].setMinimumWidth(utils.dpiScale(120))

        self.blackBoxCheckBox = elements.CheckBox(label="Black Box",
                                                  right=True,
                                                  labelRatio=6,
                                                  boxRatio=1, parent=self)
        self.childHighlighting = elements.CheckBox(label="Select Child Highlight",
                                                   right=True,
                                                   labelRatio=6,
                                                   boxRatio=1, parent=self)
        self.autoAlignGuidesCheckBox = elements.CheckBox(label="Auto Align Guides",
                                                         right=True,
                                                         labelRatio=6,
                                                         boxRatio=1, parent=self)
        self.containerAttrsShowAtTopCheckBox = elements.CheckBox(label="Container attrs show at top",
                                                                 right=True,
                                                                 labelRatio=6,
                                                                 boxRatio=1, parent=self)
        self.useProxyAttributesCheckBox = elements.CheckBox(label="Use Proxy Attributes",
                                                            right=True,
                                                            labelRatio=6,
                                                            boxRatio=1, parent=self)
        self.containerOutlinerDisplayUnderParentCheckBox = elements.CheckBox(
            label="Container Display under parent",
            right=True,
            labelRatio=6,
            boxRatio=1, parent=self)
        self.controlShapesHiddenCheckbox = elements.CheckBox(label="Shapes Hidden in Outliner",
                                                             right=True,
                                                             labelRatio=6,
                                                             boxRatio=1, parent=self)
        self.buildScriptsWidget = buildscriptwidget.BuildScriptWidget(label="Build Scripts", parent=self)
        self.namingPresetWidget = presetwidget.PresetChooser(parent=self)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`toolsetwidget.PropertiesDict`
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties)

        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------

        checkBoxLayout = elements.GridLayout(hSpacing=uic.SLRG)

        checkBoxLayout.addWidget(self.blackBoxCheckBox, 0, 0)

        checkBoxLayout.addWidget(self.containerAttrsShowAtTopCheckBox, 0, 1)
        checkBoxLayout.addWidget(self.containerOutlinerDisplayUnderParentCheckBox, 1, 0)
        checkBoxLayout.addWidget(self.useProxyAttributesCheckBox, 1, 1)
        # Main Layout -----------------------------------------------
        mainLayout.addWidget(self.rigNameEdit)
        miscLayout = elements.GridLayout(hSpacing=uic.SLRG)

        mainLayout.addWidget(elements.LabelDivider("Containers"))
        mainLayout.addWidget(self.containerRadioGroup)
        mainLayout.addLayout(checkBoxLayout)
        mainLayout.addWidget(elements.LabelDivider("Miscellaneous"))
        mainLayout.addLayout(miscLayout)
        mainLayout.addWidget(elements.LabelDivider("Naming"))
        mainLayout.addWidget(self.namingPresetWidget)
        mainLayout.addWidget(elements.LabelDivider("Scripts"))
        mainLayout.addWidget(self.buildScriptsWidget)
        miscLayout.addWidget(self.childHighlighting, 0, 0)
        miscLayout.addWidget(self.autoAlignGuidesCheckBox, 0, 1)
        miscLayout.addWidget(self.controlShapesHiddenCheckbox, 1, 0)

        mainLayout.setAlignment(self.containerRadioGroup, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
