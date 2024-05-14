"""Hive Mirror/symmetry copy/poste and Animation related tool code.

from zoo.libs.hive.anim import mirroranim
mirroranim.mirrorPasteHiveCtrlsSel(0, 24.0, offset=0.0, mirrorControlPanel=True, preCycle="cycle",
                               postCycle="cycle", limitRange=False)

"""

from collections import OrderedDict

from zoo.libs.maya import zapi
from zoo.libs.utils import output

from zoo.libs.hive import api as hiveapi
from zoo.libs.hive.anim.mirrorconstants import FLIP_ATTR_DICT

from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.animation import mirroranimation


# ---------------------------
# FLIP MIRROR ANIM FUNCTIONS
# ---------------------------


def componentsAndIds():
    """Simple helper function that outputs the name of the selected controls, their components and IDs.

        from zoo.libs.hive.anim import mirror
        mirror.componentsAndIds()

    """
    selNodes = list(zapi.selected(filterTypes=zapi.kTransform))
    for node in selNodes:
        components = hiveapi.componentsFromNodes([node])
        component = list(components.keys())[0]
        output.displayInfo("---------------")
        output.displayInfo("Control: {}".format(node.fullPathName()))
        output.displayInfo("Component: {}".format(component.componentType))
        output.displayInfo("ID: {}".format(hiveapi.ControlNode(node.object()).id()))


def selectedControlsIds():
    """Returns selected controls as zapi objects and their control ids

    :return:
    :rtype:
    """
    selIds = list()
    selControls = list()
    selNodes = list(zapi.selected(filterTypes=zapi.kTransform))

    for node in selNodes:
        controlId = hiveapi.ControlNode(node.object()).id()
        if not controlId or not node.hasFn(zapi.kNodeTypes.kTransform):
            continue
        selControls.append(node)
        selIds.append(controlId)

    return selControls, selIds


def controlPair(control, controlId):
    """From the animation control return information about the opposite control:

        targetCtrl: opposite control as zapi
        sourceComponent: The control's component as a python object
        targetComponent: The opposite control's component as a python object

    If none found returns three None types.

    :param control: control object as zapi will filter if not a control.
    :type control: :class:`zapi.DagNode`
    :param controlId: The name of the controls ID
    :type controlId: str
    :return oppositeInfo: Opposite information, see documentation.
    :rtype oppositeInfo: tuple()
    """
    components = hiveapi.componentsFromNodes([control])
    if not components:
        return None, None, None
    sourceComponent = list(components.keys())[0]  # first key will be the component object
    oppositeSideLabel = sourceComponent.namingConfiguration().field("sideSymmetry").valueForKey(sourceComponent.side())
    if not oppositeSideLabel:
        return None, None, None
    targetComponent = sourceComponent.rig.component(sourceComponent.name(), oppositeSideLabel)
    if not targetComponent:
        return None, None, None
    targetCtrl = targetComponent.rigLayer().control(controlId)
    if not targetCtrl:
        return None, None, None
    return targetCtrl, sourceComponent, targetComponent


def controlPairDicts(controls, ids):
    """Returns lists of the anim control curve lists opposites (target controls) if they exist as a pairDictList.

    Returns a list of dicts, each dict has contents:

        "source": source controls as zapi node
        "target": target controls as zapi node
        "id": ids as str "endIk"
        "sourceComponent": source component object
        "targetComponent": source component object
        "componentType": component type as str "leg"

    :param controls: A list of source control as list(zapi)
    :type controls: list(:class:`zapi.DagNode`)
    :param ids: A list of string IDs ["endIk", "fk00"]
    :type ids: list(str)
    :return pairDictList: matching lists containing source/target controls, components, types and IDs.
    :rtype pairDictList: list(dict())
    """
    pairDictList = list()

    # iterate over all controls ---------------------
    for i, ctrl in enumerate(controls):
        targetCtrl, sourceComponent, targetComponent = controlPair(ctrl, ids[i])
        if not targetCtrl:
            output.displayWarning("Skipping `{}`, no opposite found".format(ctrl.fullPathName(partialName=True)))
            continue
        if targetCtrl in controls:  # User has selected both pairs, use only one.
            output.displayWarning("Two mirrored controls selected. Select only one control per type, "
                                  "the control will be mirrored to its opposite.")
            return dict()
        # Opposite control found so add dict to pair list -------------------
        pairDictList.append({"source": ctrl,
                             "target": targetCtrl,
                             "sourceComponent": sourceComponent,
                             "targetComponent": targetComponent,
                             "id": ids[i],
                             "componentType": sourceComponent.componentType})
    return pairDictList


def mirrorPasteHiveCtrls(source, target, componentType, idVal, startFrame, endFrame, offset=0.0, preCycle="cycle",
                         postCycle="cycle", limitRange=False):
    """

    :param source: The source control as zapi
    :type source: :class:`zapi.DagNode`
    :param target: The target control as zapi
    :type target: :class:`zapi.DagNode`
    :param componentType: The name of the Hive rig component type eg "armcomponent"
    :type componentType: str
    :param idVal: The Hive string id of the control "endIk"
    :type idVal: str
    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    flipAttrList = list()

    # Build the flip attribute list from mirrorconstants.FLIP_ATTR_DICT ----------------
    if componentType in FLIP_ATTR_DICT:
        compDict = FLIP_ATTR_DICT[componentType]
        if idVal in compDict:
            flipAttrList = compDict[idVal]
        else:  # Remove trail number from ID and try again ie "FK00" > "FK" or "lwrTwistOffset04" > "lwrTwistOffset"
            idTrailNumber = idVal.rstrip('0123456789')
            if idTrailNumber in compDict:
                flipAttrList = compDict[idTrailNumber]

    # Get the attribute list form the channel box ignore proxies ---------------------
    attrList = attributes.channelBoxAttrs(source.fullPathName(), settableOnly=True, includeProxyAttrs=False)

    # Do the mirror ----------------------------
    mirroranimation.mirrorPasteAnimAttrs(source.fullPathName(),
                                         target.fullPathName(),
                                         attrList,
                                         startFrame,
                                         endFrame,
                                         mode="replace",
                                         offset=offset,
                                         flipCurveAttrs=flipAttrList,
                                         cyclePre=preCycle,
                                         cyclePost=postCycle,
                                         limitRange=limitRange)


def mirrorPasteHiveCtrlsDict(pairDictList, startFrame, endFrame, offset=1.0, mirrorControlPanel=True, preCycle="cycle",
                             postCycle="cycle", limitRange=False):
    """

    pairDictList is a list of dicts, each dict has contents:

        "source": source controls as zapi node
        "target": target controls as zapi node
        "id": ids as str "endIk"
        "sourceComponent": source component object
        "targetComponent": source component object
        "componentType": component type as str "leg"

    :param pairDictList: pairDictList a list of dicts with information about the pairs to mirror (see description)
    :type pairDictList: list(dict)
    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param mirrorControlPanel:
    :type mirrorControlPanel: bool
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    sourceComponents = list()
    targetComponents = list()

    # Mirror the controls and ignore proxy attributes (as they are Control Panel attrs) -----------------
    for pairDict in pairDictList:
        mirrorPasteHiveCtrls(pairDict["source"],
                             pairDict["target"],
                             pairDict["componentType"],
                             pairDict["id"],
                             startFrame,
                             endFrame,
                             offset=offset,
                             preCycle=preCycle,
                             postCycle=postCycle,
                             limitRange=limitRange)

    # Mirror the ControlPanel attrs ---------------------------------------------------------
    if not mirrorControlPanel:
        return

    # For controlPanels remove component duplicates and keep order --------------
    for pairDict in pairDictList:
        sourceComponents.append(pairDict["sourceComponent"])
        targetComponents.append(pairDict["targetComponent"])

    # remove duplicates --------
    sourceComponents = list(OrderedDict.fromkeys(sourceComponents))
    targetComponents = list(OrderedDict.fromkeys(targetComponents))

    # Iterate over components for the control panel settings -------------
    for i, sourceComp in enumerate(sourceComponents):
        sourceControlPanel = sourceComp.controlPanel()
        targetControlPanel = targetComponents[i].controlPanel()
        if targetControlPanel and sourceControlPanel:
            # Mirror the Hive control panel nodes
            mirrorPasteHiveCtrls(sourceControlPanel,
                                 targetControlPanel,
                                 sourceComp.componentType,
                                  "controlPanel",
                                 startFrame,
                                 endFrame,
                                 offset=offset,
                                 preCycle=preCycle,
                                 postCycle=postCycle,
                                 limitRange=limitRange)


def mirrorPasteHiveCtrlsSel(startFrame, endFrame, offset=0.0, mirrorControlPanel=True, preCycle="cycle",
                            postCycle="cycle", limitRange=False):
    """Main function that mirrors a Hive selected control to its opposite side.

    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param mirrorControlPanel: Include the proxy attribtues in the mirror (Hive's control panel)
    :type mirrorControlPanel: bool
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    controls, ids = selectedControlsIds()
    if not controls:
        output.displayWarning("No Hive controls selected")
        return
    pairDictList = controlPairDicts(controls, ids)
    if not pairDictList:
        return  # message reported
    mirrorPasteHiveCtrlsDict(pairDictList, startFrame, endFrame, offset=offset, mirrorControlPanel=mirrorControlPanel,
                             preCycle=preCycle, postCycle=postCycle, limitRange=limitRange)

    # Report success message -----------------
    controlList = list()
    for pairDict in pairDictList:
        controlList.append(pairDict["target"].fullPathName(partialName=True))
    output.displayInfo("Mirrored Animation: {}".format(controlList))
    output.displayInfo("Success: Items with pasted mirrored animation (see Script Editor for details)")

