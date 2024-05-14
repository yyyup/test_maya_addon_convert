from zoo.apps.toolpalette import palette


class HotkeyEditorUi(palette.ToolDefinition):
    id = "zoo.hotkeyeditorui"
    creator = "Keen Foong"
    tags = ["hotkey", "hotkeys", "editor"]
    uiData = {"icon": "menu_keyboard",
              "label": "Zoo Hotkey Editor",
              "tooltip": "Zoo Hotkey Editor: \nLoad, edit and create Zoo Tools hotkey sets.",
              "label": "Hotkey Editor",
              "color": "",
              "backgroundColor": "",
              # "multipleTools": False,
              # "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.hotkeyeditor import hotkeyeditorui
        from zoo.core.engine import currentEngine

        engine = currentEngine()
        return engine.showDialog(windowCls=hotkeyeditorui.HotkeyEditorUI,
                                 name="HotkeyEditor",
                                 allowsMultiple=False)
