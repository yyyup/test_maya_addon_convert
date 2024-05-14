from zoo.apps.toolpalette import palette


class ModelingIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.modeling"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "modelingMenu_shlf",
              "label": "Modeling Tools: \nTools related to polygon modelling.",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "createZbrushGrid":
            from zoo.libs.maya.cmds.modeling import create
            create.createZBrushGridPlaneSize()

