from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging

logger = zlogging.zooLogger


class Reload(palette.ToolDefinition):
    id = "zoo.reload"
    creator = "David Sparrow"
    tags = ["reload"]
    uiData = {"icon": "menu_zoo_reload",
              "tooltip": "Reloads zootools by reloading the zootools.py plugin",
              "label": "Reload",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        from zoo.core import api
        cfg = api.currentConfig()
        rootPath = cfg.rootPath

        cfg.reload()

        from zoo.core import api
        from zoo.core import engine
        from zoounreal import unrealengine
        coreConfig = api.zooFromPath(rootPath)
        engine.startEngine(coreConfig, unrealengine.UnrealEngine, "unreal")


class Shutdown(palette.ToolDefinition):
    id = "zoo.shutdown"
    creator = "David Sparrow"
    tags = ["menu_shutdown"]
    uiData = {"icon": "zoo_shutdown",
              "tooltip": "shutdown zootools by unloading the zootools.py plugin",
              "label": "Shutdown",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self):
        from zoo.core import api
        api.currentConfig().shutdown()

