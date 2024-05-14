"""Mirror/symmetry copy/poste animation related code.


    from zoo.libs.maya.cmds.animation import mirroranimation
    source = "pCube_L"
    target = "pCube_R"
    flipCurveAttrs = ["translateX", "rotateY", "rotateZ"]
    mirroranimation.mirrorPasteAnimObj(source, target, 1.0, 25.0, cyclePre="cycle", cyclePost="cycle", mode="replace",
                                      flipCurveAttrs=flipCurveAttrs, offset=0.0, matchRange=False, proxyAttrs=True)

"""

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import attributes, selection
from zoo.libs.maya.cmds.animation import keyframes, bakeanim

FLIP_STANDARD_WORLD = ["translateX", "rotateY", "rotateZ"]
FLIP_STANDARD_FK = ["translateX", "translateY", "translateZ"]


def mirrorPasteAnimAttrs(source, target, attrList, startFrame, endFrame, mode="replace", offset=0.0,
                         flipCurveAttrs=None, cyclePre="cycle", cyclePost="cycle", limitRange=False,
                         includeStaticValues=True):
    """Copy/pastes animation from a source to target and can potentially flip attributes and offset for cycles.

    :param source: The source object to copy animation from
    :type source: str
    :param target: The target object to copy animation to
    :type target: str
    :param attrList: A list of attribute names to copy
    :type attrList: list(str)
    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool

    :return success:  Did the copy/paste succeed?
    :rtype success: bool
    """
    animCurves = list()
    if not flipCurveAttrs:
        flipCurveAttrs = list()
    success = False

    for attr in attrList:
        targetCurve = ".".join([target, attr])
        if mode == "replace":
            # Remove existing keys on target
            cmds.cutKey(target, time=(-10000, 100000), attribute=attr)  # Delete if all keys before paste

        # Copy/paste the keys, static values and flip ----------------
        if keyframes.copyPasteKeys(source, target, attr, start=startFrame, end=endFrame, mode=mode,
                                   includeStaticValues=includeStaticValues):  # If copied keys
            if attr in flipCurveAttrs:  # Flip curves
                cmds.scaleKey(targetCurve, time=(), valueScale=-1.0, valuePivot=0.0)
            if offset:  # Offset frames
                cmds.keyframe(targetCurve, time=(), edit=True, relative=True, timeChange=offset)
            success = True
        else:  # Flip static value if float
            if attr in flipCurveAttrs:  # Flip curves
                value = cmds.getAttr(".".join([source, attr]))
                if isinstance(value, float):
                    try:
                        cmds.setAttr(".".join([target, attr]), value * -1.0)
                    except:
                        pass

    # Set to cycle pre post
    cmds.setInfinity(target, attribute=attrList, preInfinite=cyclePre, postInfinite=cyclePost)

    if limitRange:  # limit the range of keys on the target (cleanup extra frame to be the same as start and end)
        for attr in attrList:
            animCurve = ".".join([target, attr])
            if cmds.keyframe(animCurve, query=True, keyframeCount=True):  # Has keys
                animCurves.append(".".join([target, attr]))
        if animCurves:
            bakeanim.bakeLimitKeysToTimerange(startFrame, endFrame, animCurves)

    return success


def mirrorPasteAnimObj(source, target, startFrame, endFrame, cyclePre="cycle", cyclePost="cycle", mode="replace",
                       flipCurveAttrs=None, offset=0.0, limitRange=False, proxyAttrs=True):
    """Copy/pastes animation from a source to target and can potentially flip attributes and offset for cycles.

    This function uses channel box attributes for the mirror/copy/paste.

    :param source: The source object to copy animation from
    :type source: str
    :param target: The target object to copy animation to
    :type target: str
    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param proxyAttrs: If True the includes proxy attributes in the copy/paste
    :type proxyAttrs: bool

    :return success:  Did the copy/paste succeed?
    :rtype success: bool
    """
    # Get all channel box attributes
    attrList = attributes.channelBoxAttrs(source, settableOnly=True, includeProxyAttrs=proxyAttrs)
    # Mirror cycle obj
    return mirrorPasteAnimAttrs(source, target, attrList, startFrame, endFrame, mode=mode, offset=offset,
                                flipCurveAttrs=flipCurveAttrs, cyclePre=cyclePre, cyclePost=cyclePost,
                                limitRange=limitRange)


def mirrorPasteAnimSel(startFrame, endFrame, cyclePre="cycle", cyclePost="cycle", mode="replace",
                       flipCurveAttrs=None, offset=0.0, limitRange=False, proxyAttrs=True, includeStaticValues=True,
                       message=True):
    """

    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param proxyAttrs: If True the includes proxy attributes in the copy/paste
    :type proxyAttrs: bool
    :param includeStaticValues: If True copies/flips even if there are no keyframes.
    :type includeStaticValues: bool
    :param message: Report messages to the user?
    :type message: bool
    """
    success = False
    selObjs = cmds.ls(selection=True, type="transform")
    if not selObjs:
        if message:
            output.displayWarning("No objects have been selected")
        return
    if len(selObjs) == 1:
        if message:
            output.displayWarning("Please select more than one object, "
                                  "the first half of the selection will be copied to the second half.")
        return
    # Get optional channel box selection --------
    selAttrs = cmds.channelBox('mainChannelBox', q=True, sma=True) or cmds.channelBox('mainChannelBox', q=True,
                                                                                      sha=True)
    # Arrange the selected objects in pairs ----------------------
    sourceObs, targetObjs = selection.selectionPairs(oddEven=False, forceEvenSelection=True, type="transform")
    if not sourceObs:
        return  # warning already given
    # Do the mirror ----------------------
    for i, source in enumerate(sourceObs):
        if not selAttrs:
            result = mirrorPasteAnimObj(source, targetObjs[i], startFrame, endFrame, cyclePre=cyclePre,
                                        cyclePost=cyclePost, mode=mode, flipCurveAttrs=flipCurveAttrs, offset=offset,
                                        limitRange=limitRange, proxyAttrs=proxyAttrs)
        else:
            result = mirrorPasteAnimAttrs(source, targetObjs[i], selAttrs, startFrame, endFrame, mode=mode,
                                          offset=offset, flipCurveAttrs=flipCurveAttrs, cyclePre=cyclePre,
                                          cyclePost=cyclePost, limitRange=limitRange,
                                          includeStaticValues=includeStaticValues)
        if result:
            success = True
    if message:
        if success:
            output.displayInfo("Success: Animation copied.")
