# encoding=utf8
"""
Twist Utils
-----------

Utility functions for building,updating and aligning twists segments.

    - For building guides use  :func:`generateTwistSegmentGuides` for each segment needed.
    - For building the joints use :func:`generateTwistJointsFromGuides` for each segment.
    - For building the animation Rig use :func:`rigTwistJoints` for each segment.
    - To update the distribution settings in the scene use :func:`updateSceneGuideAttributes`

"""
from zoo.libs.hive.base import definition
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import general
from zoo.libs.hive import constants
from zoo.libs.hive.base.util import componentutils

if general.TYPE_CHECKING:
    from zoo.libs.hive import api

DISTRIBUTION_TYPE_LINEAR = 0
DISTRIBUTION_TYPE_OFFSET = 1

GRAPH_DEBUG = False


def updateSceneGuideAttributes(twistPrefix, guideSettingsNode, guideLayerDefinition, startPos,
                               endPos, count, reverseFractions=False):
    """Updates the twist guide settings nodes attributes with new distributed values which is
    used for aligning guides.

    :param twistPrefix: the twist prefix name for all twist guides.
    :type twistPrefix: str
    :param guideSettingsNode: The guide settings node attached to the components guideLayer.
    :type guideSettingsNode: :class:`api.SettingsNode`
    :param guideLayerDefinition: The component guideLayer definition instance \
    This Function will modify the layer in place.

    :type guideLayerDefinition: :class:`api.GuideLayerDefinition`
    :param startPos: the start position vector in world space to start the twist generation.
    :type startPos: :class:`zapi.Vector`
    :param endPos: The end position vector in world space to start the twist generation.
    :type endPos: :class:`zapi.Vector`
    :param count: The number of guides to generate.
    :type count: int
    :param reverseFractions: If  reverseFractions is True then the node network will be changed \
    so that the twist starts at the start joint useful for  UprArm/UprLeg segments.

    :type reverseFractions: bool
    """
    distributionSettings = guideLayerDefinition.guideSettings("distributionType", "linearFirstLastOffset")
    for index, pos in generateTwistPositions(distributionSettings["distributionType"].value,
                                             distributionSettings["linearFirstLastOffset"].value,
                                             count,
                                             startPos,
                                             endPos
                                             ):
        multiplier = pos[1]
        # reverse the twist fraction, used in situations where the twist needs less influence near the driver.
        multiplier = 1.0 - multiplier if reverseFractions else multiplier

        index = str(index).zfill(2)
        guidId = "".join((twistPrefix, index))
        guideSettingsNode.attribute(guidId).set(multiplier)


def generateTwistPositions(distributionType,
                           linearFirstLastOffset,
                           count,
                           startPos, endPos,
                           ):
    linearDistType = distributionType == DISTRIBUTION_TYPE_LINEAR
    if linearDistType:
        distFunc = mayamath.evenLinearPointDistribution(start=startPos, end=endPos, count=count)
    else:
        distFunc = mayamath.firstLastOffsetLinearPointDistribution(start=startPos, end=endPos, count=count,
                                                                   offset=linearFirstLastOffset)

    for index, pos in enumerate(distFunc):
        yield index, pos


def generateTwistSegmentGuides(component,
                               guideLayerDefinition,
                               count,
                               startPos, endPos,
                               parentGuide,
                               twistPrefix,
                               reverseFractions=False):
    """ Guide generation function for one segment.

    This will generate twists in a evenly spaced way from the start position to the end position.
    If distributionType from the guide settings is `linearFirstLastOffset` then the first and
    last guides will have their positions offset instead.

    If `reverseFractions` is True then the fractions from start to end will be reversed so that
    the fraction 0.25 becomes 0.75(1.0-fraction). This should be used when the twist driver
    is the parent guide/joint ie. uprArm/leg. False for lwrArm.

    :param component: The Component instance
    :type component: :class:`api.Component`
    :param guideLayerDefinition: The component guideLayer definition instance \
    This Function will modify the layer in place.

    :type guideLayerDefinition: :class:`api.GuideLayerDefinition`
    :param count: The number of guides to generate.
    :type count: int
    :param startPos: the start position vector in world space to start the twist generation.
    :type startPos: :class:`zapi.Vector`
    :param endPos: The end position vector in world space to start the twist generation.
    :type endPos: :class:`zapi.Vector`
    :param parentGuide: The Parent guide which the twists will be parented too.
    :type parentGuide: :class:`api.GuideDefinition`
    :param twistPrefix: the twist prefix name for all twist guides.
    :type twistPrefix: str
    :param reverseFractions: If True the Fractions will be reverse . \
    ie. twist 2 fraction 0.25 will become 0.75.(1.0-fraction).

    :type reverseFractions: bool

    """
    configuration = component.configuration
    distributionSettings = guideLayerDefinition.guideSettings("distributionType", "linearFirstLastOffset")
    selectionHighlighting = configuration.selectionChildHighlighting
    namingConfig = component.namingConfiguration()
    compName, compSide = component.name(), component.side()

    for index, pos in generateTwistPositions(distributionSettings["distributionType"].value,
                                             distributionSettings["linearFirstLastOffset"].value,
                                             count,
                                             startPos,
                                             endPos
                                             ):
        position, multiplier = pos

        # reverse the twist fraction, used in situations where the twist needs less influence near the driver.
        multiplier = 1.0 - multiplier if reverseFractions else multiplier

        index = str(index).zfill(2)
        guidId = "".join((twistPrefix, index))
        name = namingConfig.resolve("guideName", {"componentName": compName, "side": compSide,
                                                  "id": guidId,
                                                  "type": "guide"})
        aimVector = parentGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
        upVector = parentGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
        # create the guide definition and parent it to the parentGuide then generate the twist fraction setting.
        guideLayerDefinition.createGuide(name=name,
                                         id=guidId,
                                         parent=parentGuide.id,
                                         color=(0.0, 0.5, 0.5),
                                         selectionChildHighlighting=selectionHighlighting,
                                         translate=list(position),
                                         rotate=parentGuide.rotate,
                                         shape="circle",
                                         scale=(0.5, 0.5, 0.5),
                                         attributes=[{"name": constants.MIRROR_ATTR, "value": True},
                                                     {"name": constants.AUTOALIGNAIMVECTOR_ATTR,
                                                      "Type": zapi.attrtypes.kMFnNumeric3Double,
                                                      "value": list(aimVector)},
                                                     {"name": constants.AUTOALIGNUPVECTOR_ATTR,
                                                      "Type": zapi.attrtypes.kMFnNumeric3Double,
                                                      "value": list(upVector)}
                                                     ],
                                         shapeTransform={"translate": list(position),
                                                         "rotate": list(parentGuide.rotate)})
        setting = guideLayerDefinition.guideSetting(guidId)
        if setting is None:
            # create the guide twist settings
            settingDef = definition.AttributeDefinition(name=guidId,
                                                        Type=zapi.attrtypes.kMFnNumericFloat,
                                                        value=multiplier,
                                                        # if not linearDistType and index not in (0, count - 1) else 0.0,
                                                        keyable=False,
                                                        channelBox=True)
            guideLayerDefinition.addGuideSetting(settingDef)
        else:
            setting.value = multiplier


def generateTwistJointsFromGuides(component, deformLayerDef, twistGuides, startJointDef):
    """Generates the joint definitions from the provided twist guide definitions.

    :param component: The Component instance
    :type component: :class:`api.Component`
    :param deformLayerDef: The deform layer definition where the joints will be generated
    :type deformLayerDef: :class:`api.DeformLayerDefinition`
    :param twistGuides: The twist guide definitions which the joints will be generated from.
    :type twistGuides: list[:class:`api.GuideDefinition`]
    :param startJointDef: The start guide ie. the parent guide.
    :type startJointDef: :class:`api.GuideDefinition`

    """
    compName, compSide = component.name(), component.side()
    namingConfig = component.namingConfiguration()
    for guide in twistGuides:
        deformLayerDef.createJoint(name=namingConfig.resolve("skinJointName", {"componentName": compName,
                                                                               "side": compSide, "id": guide.id,
                                                                               "type": "joint"}),
                                   id=guide.id,
                                   rotateOrder=guide.get("rotateOrder", 0),
                                   translate=guide.get("translate", (0, 0, 0)),
                                   rotate=startJointDef.rotate,
                                   parent=startJointDef.id)


def rigTwistJoints(component, rigLayer, guideLayer,
                   twistOffsetGuide, startGuide, startEndSrt, twistJoints,
                   settingsNode, offsetMatrixPlug, ctrlVisPlug,
                   reverseFractions=False, buildTranslation=True, flipRotations=False):
    """The function is responsible for generating the live twist calculation for the anim rig.

    todo.. This whole function needs rewriting as it's a mess.

    :type component: :class:`api.Component`
    :param rigLayer: The components RigLayer node
    :type rigLayer: :class:`api.HiveRigLayer`
    :param guideLayer: The Components guideLayer node
    :type guideLayer: :class:`api.GuideLayerDefinition`
    :param twistOffsetGuide: The primary twist offset guide node.
    :type  twistOffsetGuide: :class:`zapi.DagNode`
    :param startGuide: The start joint for twists.
    :type startGuide: :class:`api.GuideDefinition`
    :param twistJoints: Ordered sequence of joints from first to last.
    :type twistJoints: list[class:`api.Joint`]
    :param settingsNode: The settings node which contains will twist fractions
    :type settingsNode: :class:`api.SettingsNode`
    :param offsetMatrixPlug: The joint segment matrix plug which will store the calculated offset matrix.
    :type offsetMatrixPlug: :class:`api.Plug`
    :param reverseFractions: If  reverseFractions is True then the node network will be changed \
    so that the twist starts at the start joint useful for  UprArm/UprLeg segments.

    :type reverseFractions: bool
    :return: All created DG maths Nodes.
    :rtype: list[:class:`zapi.DGNode`]

    Node network::

             twistOffsetAnim ────────────────────┐
                                                 │
             twistServer ──────────┐             │
                                   ▼             ▼
             Percentage ─────────► Multi ──────► AddRotation──────┐
                                                                  │
                                                                  │
             Start  ─────────┐                                    │
                             ▼                                    ▼
                             blend ─────────►   Aim   ──────────► Control
                             ▲
              End  ──────────┘

    """

    naming = component.namingConfiguration()
    inputGuideOffsetNode = component.inputLayer().settingNode(constants.INPUT_GUIDE_OFFSET_NODE_NAME)
    graphReg = component.configuration.graphRegistry()
    compName, compSide = component.name(), component.side()
    offsetId = twistOffsetGuide.id
    startOutSrt, endOutSrt = startEndSrt
    extras = []

    offset = rigLayer.createControl(id=offsetId,
                                    name=naming.resolve("twistControlName",
                                                        {"componentName": compName, "side": compSide,
                                                         "id": twistOffsetGuide.id, "type": "control"}),
                                    translate=twistOffsetGuide.translate,
                                    rotate=twistOffsetGuide.rotate,
                                    rotateOrder=twistOffsetGuide.rotateOrder)
    ctrlVisPlug.connect(offset.visibility)
    offset.visibility.hide()

    # setup consolidated matrix network for computing the twist rotation
    startJointWorldMatrixPlug = startEndSrt[0].attribute("worldMatrix")[0]
    endJointWorldMatrixPlug = startEndSrt[1].attribute("worldMatrix")[0]

    aimVector = startGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)

    if aimVector is None:
        aimVector = zapi.Vector(constants.DEFAULT_AIM_VECTOR)
    else:
        aimVector = zapi.Vector(aimVector["value"])
    primaryAimVectorAxisName = mayamath.primaryAxisNameFromVector(aimVector)
    primaryAimVectorAxisIdx = mayamath.AXIS_IDX_BY_NAME[primaryAimVectorAxisName]

    flipRotationVector = zapi.Vector(-1, -1, -1)
    if reverseFractions:
        # upr arm/leg requires different math due to upr joint being the driver and the child joint being the ref
        # todo: replace with a quatToEuler once we get a stable solution for the upr arm/leg
        parentNode, root = startOutSrt.parent(), rigLayer.rootTransform()
        startJointName = startOutSrt.name()
        twistServer = zapi.createDag(naming.resolve("object", {"componentName": compName,
                                                               "side": compSide,
                                                               "section": startJointName + "TwistServer",
                                                               "type": "joint"}),
                                     "joint", parent=root)
        ikPickTrans = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                              "side": compSide,
                                                              "section": startJointName + "onlyTranslate",
                                                              "type": "pickMatrix"}),
                                    "pickMatrix")
        restIkPickTrans = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                                  "side": compSide,
                                                                  "section": startJointName + "noScale",
                                                                  "type": "pickMatrix"}),
                                        "pickMatrix")
        ikMult = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                         "side": compSide,
                                                         "section": startJointName + "ikHandle",
                                                         "type": "multMatrix"}),
                               "multMatrix")
        startOutSrt.attribute("matrix").connect(ikPickTrans.inputMatrix)

        restIkPickTrans.useScale.set(0)
        restIkPickTrans.useShear.set(0)
        ikPickTrans.useRotate.set(0)
        ikPickTrans.useScale.set(0)
        ikPickTrans.useShear.set(0)
        ikPickTrans.outputMatrix.connect(ikMult.matrixIn[1])
        _findGuideInputOffsetTransformElement(inputGuideOffsetNode, startGuide.id).child(1).connect(
            restIkPickTrans.inputMatrix)
        restIkPickTrans.outputMatrix.connect(ikMult.matrixIn[0])
        startJointWorldMatrixPlug.connect(twistServer.offsetParentMatrix)
        # position the server joint at the end joint but maintain the start rotations.
        endTransform = endOutSrt.transformationMatrix()
        endTransform.setRotation(zapi.Quaternion())
        endTransform.setScale(zapi.Vector(1, 1, 1), zapi.kWorldSpace)
        twistServer.setMatrix(endTransform.asMatrix() * startOutSrt.attribute("worldInverseMatrix")[0].value())
        twistServer.jointOrient.set(twistServer.rotation())
        twistServer.resetTransform(False, True)
        const, constUtilities = zapi.buildConstraint(driven=offset,
                                                     drivers={"targets": ((None, startOutSrt),)},
                                                     constraintType="matrix",
                                                     maintainOffset=True, trace=False)
        extras.extend(constUtilities)
        twistServer.hide()

        tempJnt = zapi.createDag("tempTwistJnt", "joint", parent=twistServer)
        tempJnt.setWorldMatrix(startOutSrt.worldMatrix())

        ikHandle, effector = zapi.createIkHandle(naming.resolve("ikHandle", {"section": startJointName + "server",
                                                                             "componentName": compName,
                                                                             "side": compSide,
                                                                             "type": "ikHandle"}),
                                                 twistServer, tempJnt, solverType="ikSCsolver",
                                                 parent=parentNode)
        # tempJnt.delete()
        ikHandle.hide()
        effector.hide()
        ikMult.matrixSum.connect(ikHandle.offsetParentMatrix)
        ikHandle.resetTransform()
        outputPlug = twistServer.attribute("rotate{}".format(primaryAimVectorAxisName))
        extras += [ikHandle, effector, twistServer, ikPickTrans, restIkPickTrans, ikMult]
    else:
        offset.resetTransform()
        offsetMatrix = (endOutSrt.worldMatrix() * startOutSrt.worldMatrix().inverse()).inverse()
        offsetMatrixPlug.set(offsetMatrix)
        graphName = "distributedTwist"
        distTwistDrivenMtxPlug = endJointWorldMatrixPlug
        distTwistInvMatrixPlug = startEndSrt[0].attribute("worldInverseMatrix")[0]
        twistOffsetGraphData = graphReg.graph("twistOffsetCtrl")
        twistOffsetGraphData.name += offsetId
        # set up the offset ctrl matrix by taking the rotation/scale from the mid-joint
        # for the translation we multiply the world matrices of the end and mid-joint
        # and connect to result to the offsetParentMatrix to the offset control
        twistOffsetGraph = componentutils.createGraphForComponent(component, rigLayer, twistOffsetGraphData, track=True,
                                                                  createIONodes=GRAPH_DEBUG)
        twistOffsetGraph.connectToInput("driverSrtWorldMtx", startEndSrt[0].attribute("worldMatrix")[0])
        twistOffsetGraph.connectToInput("drivenSrtWorldMtx", endJointWorldMatrixPlug)
        twistOffsetGraph.connectFromOutput("outputMatrix", [offset.offsetParentMatrix])

        twistGraphData = graphReg.graph(graphName)
        twistGraphData.name += offsetId
        twistGraph = componentutils.createGraphForComponent(component, rigLayer, twistGraphData, track=True,
                                                            createIONodes=GRAPH_DEBUG)
        twistGraph.connectToInput("drivenSrtWorldMtx", distTwistDrivenMtxPlug)
        twistGraph.connectToInput("driverSrtWorldInvMtx", distTwistInvMatrixPlug)
        twistGraph.connectToInput("twistOffsetRestPose", offsetMatrixPlug)
        if primaryAimVectorAxisIdx != mayamath.XAXIS:
            # default axis is X, but they need to change based on the primaryAxis
            twistGraph.node("twistOffsetEuler").inputQuatX.disconnectAll()
            twistGraph.node("twistOffsetEuler").attribute(
                "inputQuat{}".format(primaryAimVectorAxisName)).disconnectAll()
        twistGraph.setInputAttr("negateTwistVector", flipRotationVector)
        outputPlug = twistGraph.outputAttr("outputRotation").child(primaryAimVectorAxisIdx)
        extras += list(twistGraph.nodes().values())

    # we delay shape creation until after all math ops that way we can apply the shape in worldSpace without
    # having to worry about the change in the transformation
    shapeData = twistOffsetGuide.shape
    if shapeData:
        if isinstance(shapeData, dict):
            offset.addShapeFromData(shapeData, space=zapi.kWorldSpace, replace=True)
        else:
            offset.addShapeFromLib(shapeData, replace=True)
    rotationOutputGraphs = []
    for jnt in twistJoints:
        jntId = jnt.id()
        guideDef = guideLayer.guide(jntId)
        constantPlug = settingsNode.attribute(jntId)
        aimVector = guideDef.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)

        if aimVector is None:
            aimVector = constants.DEFAULT_AIM_VECTOR
        else:
            aimVector = aimVector["value"]

        aimVectorAttrName = "rotate" + mayamath.primaryAxisNameFromVector(aimVector)
        guideId = guideDef.id
        ctrlName = naming.resolve("twistControlName", {"componentName": compName, "side": compSide,
                                                       "id": guideId, "type": "control"})
        twistControl = rigLayer.createControl(id=guideId,
                                              name=ctrlName,
                                              shape=guideDef.shape,
                                              translate=guideDef.translate,
                                              rotate=guideDef.rotate,
                                              rotateOrder=guideDef.rotateOrder,
                                              parent=startEndSrt[0])
        offsetSrt = rigLayer.createSrtBuffer(guideId, name="_".join([twistControl.name(), "srt"]))
        offsetSrt.resetTransform()
        ctrlVisPlug.connect(twistControl.visibility)

        if buildTranslation:
            offsetBlend = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                                  "side": compSide,
                                                                  "section": guideId,
                                                                  "type": "blendMatrix"}),
                                        "blendMatrix")
            aimMatrix = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                                "side": compSide,
                                                                "section": guideId,
                                                                "type": "aimMatrix"}), "aimMatrix")
            localOffsetMult = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                                      "side": compSide,
                                                                      "section": guideId + "localOffset",
                                                                      "type": "multMatrix"}), "multMatrix")
            localOffsetPick = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                                      "side": compSide,
                                                                      "section": guideId + "localOffset",
                                                                      "type": "pickMatrix"}), "pickMatrix")
            startJointWorldMatrixPlug.connect(offsetBlend.inputMatrix)
            offsetBlend.outputMatrix.connect(aimMatrix.inputMatrix)
            aimMatrix.outputMatrix.connect(localOffsetMult.matrixIn[1])
            _findGuideInputOffsetTransformElement(inputGuideOffsetNode, jntId).child(1).connect(
                localOffsetPick.inputMatrix)
            localOffsetPick.outputMatrix.connect(localOffsetMult.matrixIn[0])
            startEndSrt[0].attribute("worldInverseMatrix")[0].connect(localOffsetMult.matrixIn[2])
            prim = aimMatrix.primary
            secondary = aimMatrix.secondary
            endJointWorldMatrixPlug.connect(prim.child(3))
            offset.attribute("worldMatrix")[0].connect(secondary.child(3))
            prim.child(1).set(1)  # mode
            prim.child(0).set(aimVector)  # inputAxis
            secondary.child(1).set(1)  # mode
            secondary.child(0).set((0, 0, 0))  # inputAxis
            localOffsetPick.useTranslate.set(0)
            localOffsetPick.useScale.set(0)
            localOffsetPick.useShear.set(0)

            targetElement = offsetBlend.target[0]
            endJointWorldMatrixPlug.connect(targetElement.child(0))  # targetMatrix
            targetElement.child(2).set(1.0 - constantPlug.value() if reverseFractions else constantPlug.value())
            targetElement.child(3).set(False)  # scale
            targetElement.child(5).set(False)  # shear
            targetElement.child(6).set(False)  # rotate
            localOffsetMult.matrixSum.connect(offsetSrt.offsetParentMatrix)
            extras.extend((offsetBlend, aimMatrix, localOffsetMult, localOffsetPick))

        twistCtrlRot = graphReg.graph("twistOffsetCtrlRotation")
        twistCtrlRot.name += jntId
        graph = componentutils.createGraphForComponent(component, rigLayer, twistCtrlRot, track=True,
                                                       createIONodes=GRAPH_DEBUG)
        graph.connectToInput("driverRot", outputPlug)
        graph.connectToInput("twistCtrlRot", offset.attribute(aimVectorAttrName))
        graph.connectToInput("restPoseDistance", constantPlug)
        graph.connectFromOutput("outputRotate", [offsetSrt.attribute(aimVectorAttrName)])
        rotationOutputGraphs.append(graph)
        extras += graph.nodes().values()

        const, constUtilities = zapi.buildConstraint(jnt,
                                                     drivers={"targets": ((twistControl.fullPathName(partialName=True,
                                                                                                     includeNamespace=False),
                                                                           twistControl),)},
                                                     constraintType="parent",
                                                     maintainOffset=False)
        extras.extend(constUtilities)
        const, constUtilities = zapi.buildConstraint(jnt,
                                                     drivers={"targets": ((twistControl.fullPathName(partialName=True,
                                                                                                     includeNamespace=False),
                                                                           twistControl),)},
                                                     constraintType="scale",
                                                     maintainOffset=False)
        extras.extend(constUtilities)
        twistControl.showHideAttributes(["visibility"], False)

    # offset.setLockStateOnAttributes(["translate", "scale", "rotateY", "rotateZ"])
    # offset.showHideAttributes(["translate", "scale", "rotateY", "rotateZ"], False)
    return extras


def _findGuideInputOffsetTransformElement(offsetNode, guideId):
    for transformElement in offsetNode.attribute("transforms"):
        if transformElement.child(0).value() == guideId:
            return transformElement
