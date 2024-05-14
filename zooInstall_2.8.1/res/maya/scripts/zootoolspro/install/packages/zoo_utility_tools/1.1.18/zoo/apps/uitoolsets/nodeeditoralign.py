from functools import partial

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.qt import nodeeditor

from zoo.libs.maya.mayacommand import mayaexecutor as executor

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class NodeEditorAlign(toolsetwidget.ToolsetWidget):
    id = "nodeEditorAlign"
    info = "Align nodes in the Node Maya's Editor"
    uiData = {"label": "Node Editor Align",
              "icon": "verticalAlignCenter",
              "tooltip": "Align nodes in the Node Maya's Editor",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-node-editor-align/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(NodeEditorAlign, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(NodeEditorAlign, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def alignNodes(self, align):
        """Aligns nodes in the node editor, with multiple nodes selected run

        align variable options:

            0: Horizontal Top
            1: Horizontal Bottom
            2: Vertical Left
            3: Vertical Right
            4: Vertical Center
            5: Horizontal Center

        :param align: The way to align
        :type align: int
        """
        executor.execute("zoo.maya.nodeEditor.alignment", align=align)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.compactWidget.verticalLeftBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_LEFT)
        )
        self.compactWidget.verticalRightBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_RIGHT)
        )
        self.compactWidget.horizontalTopBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_TOP)
        )
        self.compactWidget.horizontalBottomBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_BOTTOM)
        )
        self.compactWidget.verticalCenterBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_CENTER_X)
        )
        self.compactWidget.horizontalCenterBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_CENTER_Y)
        )
        self.compactWidget.diagonalLeftToRightBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_DIAGONALLY_LEFT_RIGHT)
        )
        self.compactWidget.diagonalRightToLeftBtn.clicked.connect(
            partial(self.alignNodes, nodeeditor.ALIGN_DIAGONALLY_RIGHT_LEFT)
        )


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
        # Vertical Align Label ---------------------------------------
        toolTip = ""
        self.horizontalLabel = elements.Label(text="Horizontally Align Node Editor Nodes", toolTip=toolTip)
        # Node Horizontal Align Buttons ---------------------------------------
        tooltip = "Align Node Editor nodes horizontally to the top most node \n" \
                  "Select two or more nodes in the node editor and run"
        self.horizontalTopBtn = elements.styledButton("",
                                                      icon="verticalAlignTop",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_LABEL_SML)
        tooltip = "Align Node Editor nodes horizontally to the center of the nodes \n" \
                  "Select two or more nodes in the node editor and run"
        self.horizontalCenterBtn = elements.styledButton("",
                                                         icon="verticalAlignCenter",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_LABEL_SML)
        tooltip = "Align Node Editor horizontally to the bottom most node \n" \
                  "Select two or more nodes in the node editor and run"
        self.horizontalBottomBtn = elements.styledButton("",
                                                         icon="verticalAlignBottom",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_LABEL_SML)
        # Vertical Align Label ---------------------------------------
        toolTip = ""
        self.verticalLabel = elements.Label(text="Vertically Align Node Editor Nodes", toolTip=toolTip)
        # Node Vertical Align Buttons ---------------------------------------
        tooltip = "Align Node Editor nodes vertically to the left most node \n" \
                  "Select two or more nodes in the node editor and run"
        self.verticalLeftBtn = elements.styledButton("",
                                                     icon="horizontalAlignLeft",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_LABEL_SML)
        tooltip = "Align Node Editor nodes vertically to the center of the nodes \n" \
                  "Select two or more nodes in the node editor and run"
        self.verticalCenterBtn = elements.styledButton("",
                                                       icon="horizontalAlignCenter",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_LABEL_SML)
        tooltip = "Align Node Editor nodes vertically to the right most node \n" \
                  "Select two or more nodes in the node editor and run"
        self.verticalRightBtn = elements.styledButton("",
                                                      icon="horizontalAlignRight",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_LABEL_SML)
        self.diagonalLabel = elements.Label(text="Diagonally Align Node Editor Nodes", toolTip="")
        tooltip = "Align Node Editor nodes diagonally From Left to Right \n" \
                  "Select two or more nodes in the node editor and run"
        self.diagonalLeftToRightBtn = elements.styledButton("",
                                                            icon="horizontalAlignRight",
                                                            toolTip=tooltip,
                                                            style=uic.BTN_LABEL_SML)
        tooltip = "Align Node Editor nodes diagonally From Right to Reft \n" \
                  "Select two or more nodes in the node editor and run"
        self.diagonalRightToLeftBtn = elements.styledButton("",
                                                            icon="horizontalAlignRight",
                                                            toolTip=tooltip,
                                                            style=uic.BTN_LABEL_SML)


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
        # Horizontal Layout ---------------------------------------
        horizontalLayout = elements.hBoxLayout()
        horizontalLayout.addWidget(self.horizontalLabel, 9)
        horizontalLayout.addWidget(self.horizontalTopBtn, 1)
        horizontalLayout.addWidget(self.horizontalCenterBtn, 1)
        horizontalLayout.addWidget(self.horizontalBottomBtn, 1)
        # Vertical Layout ---------------------------------------
        verticalLayout = elements.hBoxLayout()
        verticalLayout.addWidget(self.verticalLabel, 9)
        verticalLayout.addWidget(self.verticalLeftBtn, 1)
        verticalLayout.addWidget(self.verticalCenterBtn, 1)
        verticalLayout.addWidget(self.verticalRightBtn, 1)
        diagonalLayout = elements.hBoxLayout()
        diagonalLayout.addWidget(self.diagonalLabel, 9)
        diagonalLayout.addWidget(self.diagonalLeftToRightBtn, 1)
        diagonalLayout.addWidget(self.diagonalRightToLeftBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addLayout(verticalLayout)
        mainLayout.addLayout(diagonalLayout)
