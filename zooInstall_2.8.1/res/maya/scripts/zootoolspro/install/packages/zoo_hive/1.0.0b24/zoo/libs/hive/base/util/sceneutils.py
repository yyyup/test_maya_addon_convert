from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.qt import mayaui

from maya import cmds


def setMayaUIContainerDisplaySettings(attrsShowAtTop=None,
                                      outlinerDisplayUnderParent=None):
    """Changes the container visibility in the outliner and channelbox.
    This function isn't undoable because maya doesn't treat these commands as undoable.

    :param attrsShowAtTop: If True then the selected transform attributes will be displayed\
    at the top
    :type attrsShowAtTop: bool
    :param outlinerDisplayUnderParent: if True then DGContainers will be hidden in the outliner.
    :type outlinerDisplayUnderParent: bool
    """
    if attrsShowAtTop is not None and mayaenv.isInteractive():
        # mayas UI is confusing True for show at top means the bottom so here we invert the rig config
        mayaui.setChannelBoxAtTop("mainChannelBox", attrsShowAtTop)
    if outlinerDisplayUnderParent is not None and mayaenv.isInteractive():
        for outliner in mayaui.outlinerPaths():
            cmds.outlinerEditor(outliner, e=True, showContainerContents=not outlinerDisplayUnderParent)
            cmds.outlinerEditor(outliner, e=True, showContainedOnly=not outlinerDisplayUnderParent)

