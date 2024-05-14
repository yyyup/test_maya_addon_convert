from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.modeling import subdivisions

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SubDSmoothControl(toolsetwidget.ToolsetWidget):
    id = "subDSmoothControl"
    info = "A GUI for controlling the subD smooth settings on mesh shapes."
    uiData = {"label": "SubD Smooth Control",
              "icon": "subDSmooth",
              "tooltip": "A GUI for controlling the subD smooth settings on mesh shapes.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-subd-smooth-control/"}

    # ------------------
    # STARTUP
    # ------------------

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.updateWidgets()
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback
        self.refreshUpdateUIFromSelection(update=False)  # update GUI from current in scene selection

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(SubDSmoothControl, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SubDSmoothControl, self).widgets()

    def saveProperties(self):
        """Saves properties, keeps self.properties up to date with every widget change
        Overridden function which automates properties updates. Exposed here in case of extra functionality.

        properties are auto-linked if the name matches the widget name
        """
        super(SubDSmoothControl, self).saveProperties()
        self.updateWidgets()  # disable or enable widgets

    # ------------------
    # Callbacks
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        self.refreshUpdateUIFromSelection()  # will update the GUI

    def refreshUpdateUIFromSelection(self, update=True):
        """Updates the GUI on selection change

        :param update: updateProperties?
        :type update: bool
        """
        subDValue, vpDiv, renderDiv, useForRender, showSubDs = subdivisions.subDSettingsSelected()
        if not vpDiv:  # bail as nothing found
            return
        self.properties.viewportDivisionsFSlider.value = vpDiv
        self.properties.renderDivisionsFSlider.value = renderDiv
        self.properties.useForRenderingCheckbox.value = useForRender
        self.properties.showSubDsCheckbox.value = showSubDs
        if update:
            self.updateFromProperties()

    # ------------------
    # UI Disable
    # ------------------

    def updateWidgets(self):
        useVPBool = self.properties.useForRenderingCheckbox.value
        self.compactWidget.renderDivisionsFSlider.setEnabled(not useVPBool)
        if useVPBool:
            self.properties.renderDivisionsFSlider.value = self.properties.viewportDivisionsFSlider.value
        self.compactWidget.renderDivisionsFSlider.blockSignals(True)
        self.updateFromProperties()
        self.compactWidget.renderDivisionsFSlider.blockSignals(False)

    # ------------------
    # LOGIC
    # ------------------

    def applySubDSettings(self):
        """Sets the subD settings on selected objects
        """
        subdivisions.setSubDSettingsList(previewDivisions=self.properties.viewportDivisionsFSlider.value,
                                         rendererDivisions=self.properties.renderDivisionsFSlider.value,
                                         usePreview=self.properties.useForRenderingCheckbox.value,
                                         displaySubs=self.properties.showSubDsCheckbox.value,
                                         message=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def applySubDSettingsUndo(self, checked=True):
        """Use this function on the checkboxes for single click undo, not for the sliders"""
        self.applySubDSettings()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.applyBtn.clicked.connect(self.applySubDSettings)
            widget.showSubDsCheckbox.stateChanged.connect(self.applySubDSettingsUndo)
            widget.useForRenderingCheckbox.stateChanged.connect(self.applySubDSettingsUndo)
            widget.viewportDivisionsFSlider.numSliderChanged.connect(self.applySubDSettings)
            widget.renderDivisionsFSlider.numSliderChanged.connect(self.applySubDSettings)
            # Undo queues
            widget.viewportDivisionsFSlider.sliderPressed.connect(self.openUndoChunk)
            widget.viewportDivisionsFSlider.sliderReleased.connect(self.closeUndoChunk)
            widget.renderDivisionsFSlider.sliderPressed.connect(self.openUndoChunk)
            widget.renderDivisionsFSlider.sliderReleased.connect(self.closeUndoChunk)
        # Callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Display Subds Check Box ---------------------------------------
        tooltip = "Display the subdivision wireframe in the viewport on the selected objects."
        self.showSubDsCheckbox = elements.CheckBox(label="Display Divisions Wireframe",
                                                   checked=False,
                                                   toolTip=tooltip)
        # Viewport Divisions Slider ---------------------------------------
        tooltip = "Set the subdivision levels of the preview (viewport) on selected objects."
        self.viewportDivisionsFSlider = elements.IntSlider(label="Viewport Divisions",
                                                           defaultValue=2.0,
                                                           sliderMin=0.0,
                                                           sliderMax=4.0,
                                                           sliderAccuracy=4,
                                                           decimalPlaces=0,
                                                           dynamicMax=True,
                                                           toolTip=tooltip)
        # Use Preview for Rendering Check Box ---------------------------------------
        tooltip = "Use the same subdivision levels in the viewport and renderer?"
        self.useForRenderingCheckbox = elements.CheckBox(label="Use Viewport For Rendering",
                                                         checked=True,
                                                         toolTip=tooltip)
        # Renderer Divisions Slider ---------------------------------------
        tooltip = "Set the subdivision render levels as seen in the renderer."
        self.renderDivisionsFSlider = elements.IntSlider(label="Renderer Divisions",
                                                         defaultValue=2.0,
                                                         sliderMin=0.0,
                                                         sliderMax=4.0,
                                                         sliderAccuracy=4,
                                                         decimalPlaces=0,
                                                         dynamicMax=True,
                                                         toolTip=tooltip)
        # Apply Button ---------------------------------------
        tooltip = "Apply the subD smooth settings to the selected polygon objects."
        self.applyBtn = elements.styledButton("Apply Settings",
                                              icon="subDSmooth",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Display Checkbox Layout ---------------------------------------
        displayCheckboxLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))
        displayCheckboxLayout.addWidget(self.useForRenderingCheckbox, 1)
        displayCheckboxLayout.addWidget(self.showSubDsCheckbox, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(displayCheckboxLayout)
        mainLayout.addWidget(self.viewportDivisionsFSlider)
        mainLayout.addWidget(self.renderDivisionsFSlider)
        mainLayout.addWidget(self.applyBtn)
