from maya import cmds
import maya.mel as mel

from zoo.libs.maya.utils import general


def loadPlugin():
    return general.loadPlugin('brSmoothWeights')


def smoothSkinBrush():
    # todo check for plugin
    mel.eval('brSmoothWeightsToolCtx')


def getTool():
    """Returns the braverabbit smooth weights skin tool

    :return tool: The smooth skins context as a maya tool
    :rtype tool: str
    """
    tool = mel.eval("brSmoothWeightsContext")
    return tool


def setTool(tool):
    cmds.setToolTo(tool)


def brushSize(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, size=True)


def setBrushSize(tool, size=5.0):
    cmds.brSmoothWeightsContext(tool, edit=True, size=size)


def strength(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, strength=True)


def setStrength(tool, strength=0.25):
    cmds.brSmoothWeightsContext(tool, edit=True, strength=strength)


def oversampling(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, oversampling=True)


def setOversampling(tool, oversampling=1):
    cmds.brSmoothWeightsContext(tool, edit=True, oversampling=oversampling)


def flood(tool):
    cmds.brSmoothWeightsContext(tool, edit=True, flood=True)


def openBraverabbitToolWindow():
    mel.eval("toolPropertyWindow;")

