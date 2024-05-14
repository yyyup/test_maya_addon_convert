from zoo.apps.toolpalette import palette
from zoo.preferences.interfaces import coreinterfaces


class AssetIconShelf(palette.ToolDefinition):
    id = "zoo.shelf.assets"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "packageAssetsMenu_shlf",
              "label": "Asset Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs.get("variant")
        # Imports -----------------------------
        from zoo.libs.maya.cmds.assets import defaultassets
        # Create from the menu item -----------------------------
        if name == "zoo_build_scene_camera":
            cameraTransform, cameraShape = defaultassets.createDefaultCamera(type=defaultassets.CAMTYPE_DEFAULT)
            defaultassets.setCameraResolution(cameraShape=cameraShape, setRes=False, grid=True)
            return
        # Check renderer
        from zoo.libs.maya.cmds.renderer import rendererload
        from zoo.libs.pyqt.widgets import elements
        # Check renderer is loaded -----------------------------
        renderer = coreinterfaces.generalInterface().primaryRenderer()
        if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(renderer):
                return
        if name == "zoo_build_macbeth_balls":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_MACBETH_BALLS,
                                                     lightPresetPath="",
                                                     hdrImage="",
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     setDefaultRenderSet=False,
                                                     message=True)
        elif name == "zoo_build_scene_studio_rim":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.ASSET_LIGHTPRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS_BW,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     message=True)
        elif name == "zoo_build_scene_studio_three_point":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.THREE_POINT_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS_BW,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
        elif name == "zoo_build_scene_studio_three_point_drk":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.THREE_POINT_DRK_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS_BW,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
        elif name == "zoo_build_scene_studio_soft_top":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.SOFT_TOP_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS_BW,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
        elif name == "zoo_build_scene_studio_red_aqua_rim":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.RED_AQUA_RIM_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     message=True)
        elif name == "zoo_build_scene_skydome_factory_grey":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.DEFAULT_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS_BW,
                                                     hdrIntMult=defaultassets.HDR_F_PUMPS_BW_INT_MULT,
                                                     hdrRotOffset=defaultassets.HDR_F_PUMPS_BW_ROT_OFFSET,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
        elif name == "zoo_build_scene_skydome_factory_color":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.DEFAULT_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_F_PUMPS,
                                                     hdrIntMult=defaultassets.HDR_F_PUMPS_INT_MULT,
                                                     hdrRotOffset=defaultassets.HDR_F_PUMPS_ROT_OFFSET,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
        elif name == "zoo_build_scene_skydome_winter":
            defaultassets.buildDefaultAssetsSceneCyc(renderer=renderer,
                                                     assetDirPath=defaultassets.MODEL_ASSETS_PATH,
                                                     assetZooScene=defaultassets.ASSET_CYC_GREY_SCENE,
                                                     lightPresetPath=defaultassets.WINTER_F_LIGHT_PRESET_PATH,
                                                     hdrImage=defaultassets.HDR_WINTER_F,
                                                     hdrIntMult=defaultassets.HDR_WINTER_F_INT_MULT,
                                                     hdrRotOffset=defaultassets.HDR_WINTER_F_ROT_OFFSET,
                                                     buildCamera=False,
                                                     setRes=False,
                                                     replaceByType=True,
                                                     darkShader=False,
                                                     message=True)
