"""
todo: map mirrored components with meta data so we can know the axis to work on
"""

from zoo.libs.hive.library.components.organic import armcomponent
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath


class LegComponent(armcomponent.ArmComponent):
    creator = "David Sparrow"
    definitionName = "legcomponent"
    icon = "componentLeg"
    # determines whether the 'end' guide should be world aligned vs align to parent/child
    worldEndRotation = True
    # guide which to world align to ie. the ball
    worldEndAimGuideId = "ball"
    rootIkVisCtrlName = "ikHipsCtrlVis"
    _pivotGuideIdsForAlignToWorld = ("heel_piv",
                                     "outer_piv",
                                     "inner_piv"
                                     )
    _resetEndGuideAlignment = False
    _alignWorldUpRotationOffset = 180
    fkControlIds = ("uprfk", "midfk", "endfk", "ballfk")
    deformJointIds = ("upr", "mid", "end", "ball")
    fixMidJointMMLabel = "Fix Knee"
    _spaceSwitchDrivers = armcomponent.ArmComponent._spaceSwitchDrivers + [api.SpaceSwitchUIDriver(id_="ballFk",
                                                                                                   label="Ball FK")]
    twistFlipFirstSegmentRotations = True

    def idMapping(self):
        mapping = super(LegComponent, self).idMapping()

        d = {"ball": "ballroll_piv",
             "heel_piv": "heel_piv",
             "outer_piv": "outer_piv",
             "inner_piv": "inner_piv",
             "toeTip_piv": "toeTip_piv",
             "toeTap_piv": "toeTap_piv"
             }
        mapping[api.constants.RIG_LAYER_TYPE].update(d)
        mapping[api.constants.OUTPUT_LAYER_TYPE]["ball"] = "ball"
        mapping[api.constants.DEFORM_LAYER_TYPE].update({"ball": "ball",
                                                         "toe": "toe"})
        return mapping

    def alignGuides(self):

        changes = super(LegComponent, self).alignGuides()
        if not changes:
            return changes
        # ok we now need to align the other guides ensuring we skip the above nodes and twists
        layer = self.guideLayer()
        guides = layer.findGuides(*LegComponent._pivotGuideIdsForAlignToWorld)
        endGuide, ballGuide, toeGuide = layer.findGuides("end", "ball", "toe")
        endGuidePos = endGuide.translation()
        ballGuideTarget = ballGuide.translation()
        ballGuideTarget.y = endGuidePos.y

        toeTipPivot = layer.guide("toeTip_piv")
        # we force auto align on the toe tip since it's always got to match the toe regardless
        guidesToModify, matrices = [], []
        # for each pivot(inner outer, heel, toe tip) copy the alignment rotation between the end piv to ball
        # onto the pivots.
        for guide in guides:
            if not guide.autoAlign.asBool():
                continue
            transform = guide.transformationMatrix(space=zapi.kWorldSpace)
            rot = mayamath.lookAt(endGuidePos, ballGuideTarget,
                                  zapi.Vector(guide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value()),
                                  zapi.Vector(guide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value()),
                                  constrainAxis=zapi.Vector(1, 1, 1))
            transform.setRotation(rot)
            matrices.append(transform.asMatrix())
            guidesToModify.append(guide)

        # aim the ball guide to the toe, we have multiple children here so manual is better
        if ballGuide.autoAlign.asBool():
            transform = ballGuide.transformationMatrix(space=zapi.kWorldSpace)
            rot = mayamath.lookAt(ballGuide.translation(), toeGuide.translation(),
                                  zapi.Vector(ballGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value()),
                                  zapi.Vector(ballGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value()),
                                  constrainAxis=zapi.Vector(1, 1, 1))
            transform.setRotation(rot)
            ballGuideMatrix = transform.asMatrix()
            matrices.append(ballGuideMatrix)
            guidesToModify.append(ballGuide)

        else:
            ballGuideMatrix = ballGuide.worldMatrix()

        if toeGuide.autoAlign.asBool():
            # realign the toe guide by aiming at the ball with the primary aim vector inverted(*-1)
            # this is similar to just zero out but allowing manual and auto align vectors to be used.
            toeTransform = toeGuide.transformationMatrix(space=zapi.kWorldSpace)
            toeRotation = mayamath.lookAt(toeGuide.translation(),
                                          ballGuide.translation(),
                                          zapi.Vector(toeGuide.attribute(
                                              api.constants.AUTOALIGNAIMVECTOR_ATTR).value()) * -1,
                                          zapi.Vector(
                                              toeGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value())
                                          )
            toeTransform.setRotation(toeRotation)
            toeMatrix = toeTransform.asMatrix()
            matrices.append(toeMatrix)
            guidesToModify.append(toeGuide)
        else:
            toeMatrix = toeGuide.worldMatrix()
        guidesToModify.append(toeTipPivot)
        matrices.append(toeMatrix)
        toeTipPivot.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).set(
            toeGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value())
        toeTipPivot.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).set(
            toeGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value())
        # set the ball roll and toe tap alignment to the ball roll
        guidesToModify += layer.findGuides("ballroll_piv")

        matrices += [ballGuideMatrix]
        # batch update the guides.
        api.setGuidesWorldMatrix(guidesToModify, matrices)

        return True

    def setupRig(self, parentNode):
        super(LegComponent, self).setupRig(parentNode)

        namer = self.namingConfiguration()
        rigLayer = self.rigLayer()
        controlPanel = self.controlPanel()
        deformLayer = self.deformLayer()
        definition = self.definition
        guideLayerDef = definition.guideLayer
        defGuides = {g.id: g for g in guideLayerDef.iterGuides()}
        heelPiv = defGuides["heel_piv"]
        toeTipPiv = defGuides["toeTip_piv"]
        ballRollPiv = defGuides["ballroll_piv"]
        innerPiv = defGuides["inner_piv"]
        outerPiv = defGuides["outer_piv"]
        ballDefinition = defGuides["ball"]
        toeDefinition = defGuides["toe"]

        blendTransformParent = rigLayer.taggedNode("end")
        endIk = rigLayer.joint("endik")

        ikJntParent = endIk
        blendAttr = controlPanel.attribute("ikfk")

        ballIkJnt, toeIkJoint = None, None
        compName, compSide = self.name(), self.side()
        ballFkCtrl = None
        # generate the ball and toe joints and controls for both ik and fk
        for guide in (ballDefinition, toeDefinition):
            ikName = namer.resolve("jointName", {"componentName": compName, "side": compSide,
                                                 "system": api.constants.IKTYPE,
                                                 "id": guide.id, "type": "joint"})
            fkGuideId = guide.id + "fk"
            ikGuideId = guide.id + "ik"
            # create transform for the output of the ik/fk since our bind skeleton contains a joint Orient
            # and requires export compatibility
            blendTransform = zapi.createDag(namer.resolve("object",
                                                          {"componentName": compName,
                                                           "side": compSide,
                                                           "section": guide.id + "blend",
                                                           "type": "transform"}),
                                            "transform",
                                            parent=blendTransformParent)
            blendTransform.setRotationOrder(guide.rotateOrder)
            rigLayer.addTaggedNode(blendTransform, guide.id)
            blendTransformParent = blendTransform

            ikJoint = rigLayer.createJoint(name=ikName, translate=guide.translate, rotate=guide.rotate,
                                           rotateOrder=guide.rotateOrder,
                                           parent=ikJntParent, id=ikGuideId)

            if guide.id == "ball":
                ballIkJnt = ikJoint
                fkGuideName = namer.resolve("controlName", {"id": guide.id,
                                                            "componentName": compName,
                                                            "system": api.constants.FKTYPE,
                                                            "side": compSide,
                                                            "type": "control"})
                ctrl = rigLayer.createControl(name=fkGuideName,
                                              id=fkGuideId,
                                              rotateOrder=guide.get("rotateOrder", 0),
                                              translate=guide.get("translate", (0, 0, 0)),
                                              rotate=guide.get("rotate", (0, 0, 0, 1)),
                                              parent="endfk",
                                              shape=guide.get("shape"),
                                              selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                              srts=[{"name": "_".join([fkGuideName, "srt"])}])
                blendAttr.connect(ctrl.visibility)
                ctrl.visibility.hide()
                ballFkCtrl = ctrl
            else:
                toeIkJoint = ikJoint
                # hidden fk transform for blending purposes
                ctrl = zapi.createDag(namer.resolve("object",
                                                    {"componentName": compName,
                                                     "side": compSide,
                                                     "section": fkGuideId,
                                                     "type": "transform"}),
                                      "transform",
                                      parent=ballFkCtrl)
                ctrl.setRotationOrder(guide.rotateOrder)
                ctrl.setTranslation(guide.translate, zapi.kWorldSpace)
                ctrl.setRotation(guide.rotate, zapi.kWorldSpace)

            ikJntParent = ikJoint
            self._blendTriNodes(rigLayer, blendTransform,
                                deformLayer.joint(guide.id),
                                ikJoint, ctrl,
                                blendAttr, guide)
        # create the piv points
        # ballPivot buffer
        #   |-heelpivot
        #       |-outer_roll
        #           |-inner_roll
        #               |-toe_tip
        #                   |-toe_tap
        #                       |-ball->toe ikhanle
        #                   |-ball_roll
        #                       |-leg ikhanle
        #                       |-ankle->ball ikhanle
        #                   |-ball_anim
        pivots = {}
        parent = rigLayer.control("endik")
        heelId = heelPiv.id
        heelName = namer.resolve("controlName", {"componentName": compName,
                                                 "side": compSide,
                                                 "system": api.constants.IKTYPE,
                                                 "id": heelId,
                                                 "type": "control"})
        heelCtrl = rigLayer.createControl(name=heelName,
                                          id=heelId,
                                          rotateOrder=heelPiv.get("rotateOrder", 0),
                                          translate=heelPiv.get("translate", (0, 0, 0)),
                                          rotate=heelPiv.get("rotate", (0, 0, 0, 1)),
                                          parent=parent,
                                          shape=heelPiv.get("shape"),
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                          srts=[{"name": "_".join([heelName, "srt"])},
                                                {"name": "_".join([heelName, "attr", "srt"])}])
        parent = heelCtrl
        pivots[heelPiv.id] = heelCtrl

        for piv in (outerPiv, innerPiv, toeTipPiv, ballRollPiv):
            ctrlName = namer.resolve("controlName", {"componentName": compName,
                                                     "side": compSide,
                                                     "system": api.constants.IKTYPE,
                                                     "id": piv.id,
                                                     "type": "control"})
            ctrl = rigLayer.createControl(name=ctrlName,
                                          id=piv.id,
                                          rotateOrder=piv.get("rotateOrder", 0),
                                          translate=piv.get("translate", (0, 0, 0)),
                                          rotate=piv.get("rotate", (0, 0, 0, 1)),
                                          parent=parent,
                                          shape=piv.get("shape"),
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                          srts=[{"name": "_".join([ctrlName, "srt"])},
                                                {"name": "_".join([ctrlName, "attr", "srt"])}])
            parent = ctrl
            pivots[piv.id] = ctrl

        toeTapName = namer.resolve("controlName", {"componentName": compName,
                                                   "side": compSide,
                                                   "system": api.constants.IKTYPE,
                                                   "id": "toeTap_piv",
                                                   "type": "control"})
        toeTap = rigLayer.createControl(name=toeTapName,
                                        id="toeTap_piv",
                                        rotateOrder=ballDefinition.get("rotateOrder", 0),
                                        translate=ballDefinition.get("translate", (0, 0, 0)),
                                        rotate=ballDefinition.get("rotate", (0, 0, 0, 1)),
                                        parent=pivots[toeTipPiv.id],
                                        shape=ballDefinition.get("shape"),
                                        selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                        srts=[{"name": "_".join([toeTapName, "srt"])},
                                              {"name": "_".join([toeTapName, "attr", "srt"])}])
        pivots["toeTap_piv"] = toeTap

        # deal with the ikSolves
        ballRoll = pivots[ballRollPiv.id]

        ikhandleArray = rigLayer.attribute("ikhandles")
        ikhandleArray.element(0).sourceNode().setParent(ballRoll)
        for startjnt, endjnt, par in ((endIk, ballIkJnt, ballRoll),
                                      (ballIkJnt, toeIkJoint, toeTap)):
            ikHandle, ikEffector = api.createIkHandle(name=namer.resolve("ikHandle", {"componentName": compName,
                                                                                      "section": endjnt.id(),
                                                                                      "side": compSide,
                                                                                      "type": "ikHandle"}),
                                                      startJoint=startjnt,
                                                      endJoint=endjnt,
                                                      solverType="ikSCsolver",
                                                      parent=par)
            ikHandle.hide()
            ikEffector.hide()
            handleElement = ikhandleArray.nextAvailableElementPlug()
            ikHandle.message.connect(handleElement)

        footRollNodes = _createFootRoll(self, controlPanel, pivots, heelPiv, ballDefinition, toeTipPiv)
        sideRollNodes = _createSideRoll(controlPanel, pivots, innerPiv, outerPiv)
        heelToeNodes = _createHeelToeRolls(self, controlPanel, pivots, heelPiv, ballDefinition)
        visibilityNodes = _setupVisibility(self, controlPanel, pivots)

        rigLayer.addExtraNodes(footRollNodes)
        rigLayer.addExtraNodes(sideRollNodes)
        rigLayer.addExtraNodes(heelToeNodes)
        rigLayer.addExtraNodes(visibilityNodes)

    def switchToIk(self):
        deformLayer = self.deformLayer()
        rigLayer = self.rigLayer()
        pivCtrls = rigLayer.findControls("heel_piv",
                                         "outer_piv",
                                         "inner_piv",
                                         "toeTip_piv",
                                         "ballroll_piv",
                                         "toeTap_piv",
                                         )
        for pivCtrl in pivCtrls[:-1]:
            pivCtrl.resetTransform()
        ballJntMat = deformLayer.joint("ball").worldMatrix()
        ikfkData = super(LegComponent, self).switchToIk()
        # reset the ik attributes then set the toeTap pivot ctrl to the jnt transforms
        controlPanel = self.controlPanel()
        controlPanel.attribute("lock").set(0)
        controlPanel.ikRoll.set(0)
        controlPanel.ballRoll.set(0)
        controlPanel.sideBank.set(0)
        pivCtrls[-1].setWorldMatrix(ballJntMat)
        ikfkData["controls"].extend(pivCtrls)
        ikfkData["attributes"].extend([controlPanel.attribute(i) for i in ("ikRoll", "ballRoll", "sideBank", "lock")])
        return ikfkData


def _setupVisibility(component, controlPanel, scenePivots):
    namer = component.namingConfiguration()
    compName, compSide = component.name(), component.side()
    footControlVis = controlPanel.attribute("ikFootCtrlVis")
    # construct vis ikfk + control vis logic nodes
    footControlVisSwitchLogic = zapi.logicFloat(controlPanel.ikfk,
                                                0.0,
                                                4,
                                                None,
                                                name=namer.resolve("object", {"componentName": compName,
                                                                              "side": compSide,
                                                                              "section": "footControlVis_equalGt",
                                                                              "type": "floatLogic"})
                                                )

    footControlVisSwitchNode = zapi.conditionFloat(footControlVis,
                                                   0.0,
                                                   footControlVisSwitchLogic.outBool,
                                                   None,
                                                   name=namer.resolve("object", {"componentName": compName,
                                                                                 "side": compSide,
                                                                                 "section": "footControlVis_cond",
                                                                                 "type": "floatCondition"}))
    footControlVisSwitchPlug = footControlVisSwitchNode.outFloat

    for i in scenePivots.values():
        [footControlVisSwitchPlug.connect(obj.visibility) for obj in i.shapes()]
        i.showHideAttributes(zapi.localTranslateAttrs + zapi.localScaleAttrs + ["visibility"], state=False)
        i.setLockStateOnAttributes(["translate", "scale", "visibility"])
    return footControlVisSwitchLogic, footControlVisSwitchNode


def _createHeelToeRolls(component, controlPanel, scenePivots, heelDefinition, ballDefinition):
    naming = component.namingConfiguration()
    toeTapAttrTransform = scenePivots["toeTap_piv"].srt(1)
    heelGuideAimVector = heelDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    heelGuideUpVector = heelDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
    ballGuideAimVector = ballDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    ballGuideUpVector = ballDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
    heelPivot = scenePivots["heel_piv"].srt(1)
    compName, compSide = component.name(), component.side()

    outerDoubleLinear = setupRotationAxisDriver("_".join([heelPivot.name(False), "invert"]),
                                                zapi.Vector(heelGuideAimVector),
                                                zapi.Vector(heelGuideUpVector),
                                                controlPanel.heelSideToSide, heelPivot,
                                                overrideInvert=True,
                                                useVector=1)
    nodes = []
    if outerDoubleLinear:
        nodes.append(outerDoubleLinear)
    upDownDoubleLinear = setupRotationAxisDriver(naming.resolve("object", {"componentName": compName,
                                                                           "side": compSide,
                                                                           "section": "toeUpDown_invert",
                                                                           "type": "multDoubleLinear"}),
                                                 zapi.Vector(ballGuideAimVector),
                                                 zapi.Vector(ballGuideUpVector),
                                                 controlPanel.toeUpDown, toeTapAttrTransform,
                                                 overrideInvert=True)
    sideDoubleLinear = setupRotationAxisDriver(naming.resolve("object", {"componentName": compName,
                                                                         "side": compSide,
                                                                         "section": "toeSide_invert",
                                                                         "type": "multDoubleLinear"}),
                                               zapi.Vector(ballGuideAimVector),
                                               zapi.Vector(ballGuideUpVector),
                                               controlPanel.toeSide, toeTapAttrTransform,
                                               overrideInvert=True,
                                               useVector=1)
    bankDoubleLinear = setupRotationAxisDriver(naming.resolve("object", {"componentName": compName,
                                                                         "side": compSide,
                                                                         "section": "toeBank_invert",
                                                                         "type": "multDoubleLinear"}),
                                               zapi.Vector(ballGuideAimVector),
                                               zapi.Vector(ballGuideUpVector),
                                               controlPanel.toeBank, toeTapAttrTransform,
                                               overrideInvert=False,
                                               useVector=0)
    if upDownDoubleLinear:
        nodes.append(upDownDoubleLinear)
    if sideDoubleLinear:
        nodes.append(sideDoubleLinear)
    if bankDoubleLinear:
        nodes.append(bankDoubleLinear)

    return nodes


def _createSideRoll(controlPanel, scenePivots, innerPivDefinition, outputPivDefinition):
    sideRollPlug = controlPanel.attribute("sideBank")
    sideRollCond = zapi.conditionVector(sideRollPlug,
                                        0.0,
                                        (sideRollPlug, 0.0, 0.0),
                                        (0.0, sideRollPlug, 0.0),
                                        operation=4, name="sideBank_greater")

    innerGuideAimVector = innerPivDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    innerGuideUpVector = innerPivDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
    outerGuideAimVector = outputPivDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    outerGuideUpVector = outputPivDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value

    innerPiv = scenePivots["inner_piv"].srt(index=1)
    outerPiv = scenePivots["outer_piv"].srt(index=1)

    innerDoubleLinear = setupRotationAxisDriver("_".join([innerPiv.name(False), "invert"]),
                                                zapi.Vector(innerGuideAimVector),
                                                zapi.Vector(outerGuideUpVector),
                                                sideRollCond.outColorG, innerPiv, overrideInvert=True, useVector=0)
    outerDoubleLinear = setupRotationAxisDriver("_".join([outerPiv.name(False), "invert"]),
                                                zapi.Vector(outerGuideAimVector),
                                                zapi.Vector(innerGuideUpVector),
                                                sideRollCond.outColorR, outerPiv, overrideInvert=True, useVector=0)
    newNodes = [sideRollCond]
    if innerDoubleLinear:
        newNodes.append(innerDoubleLinear)
    if outerDoubleLinear:
        newNodes.append(outerDoubleLinear)

    return newNodes


def _createFootRoll(component, controlPanel, scenePivots, heelDefinition, ballRollDefinition, toeDefinition):
    """Sets up the reverse foot roll attributes in a way where we adapt to the auto alignment
    values making it possible to support multiple orientations.

    :param controlPanel:
    :type controlPanel: :class:`api.SettingsNode`
    :param scenePivots:
    :type scenePivots: dict[str, :class:`zapi.DagNode`]
    :param toeDefinition:
    :type toeDefinition: :class:`api.GuideDefinition`
    :type ballRollDefinition: :class:`api.GuideDefinition`
    :return:
    :rtype:
    """
    namer = component.namingConfiguration()
    compName, compSide = component.name(), component.side()

    createdNodes = []
    ballRollPiv = scenePivots["ballroll_piv"].srt(index=1)
    ballRollTipGuideAimVector = ballRollDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    ballRollGuideUpVector = ballRollDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
    heelGuideAimVector = heelDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
    heelGuideUpVector = heelDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
    setRange = zapi.createSetRange(name=namer.resolve("object", {"componentName": compName,
                                                                 "side": compSide,
                                                                 "section": "ballPivBallRollBreak",
                                                                 "type": "setRange"}),
                                   value=(controlPanel.ballRoll, controlPanel.ballRoll, controlPanel.ballRoll),
                                   min_=(0.0, 0.0, -180), max_=(180, controlPanel.footBreak, 0.0),
                                   oldMin=(controlPanel.footBreak, 0.0, -180),
                                   oldMax=(180, controlPanel.footBreak, 0.0))
    # condition for toe tip
    ballRollBreak = zapi.conditionVector(controlPanel.ballRoll,
                                         controlPanel.footBreak,
                                         (setRange.outValueX, 0.0, 0.0),
                                         (0.0, 0.0, 0.0),
                                         operation=2,
                                         name=namer.resolve("object", {"componentName": compName,
                                                                       "side": compSide,
                                                                       "section": "ballRollBreakGreatThan",
                                                                       "type": "condition"}))
    # condition for the heel, below zero rotation
    n = setupRotationAxisDriver(namer.resolve("object", {"componentName": compName,
                                                         "side": compSide,
                                                         "section": "heelRollInvert",
                                                         "type": "multDoubleLinear"}),
                                zapi.Vector(heelGuideAimVector)* -1,
                                zapi.Vector(heelGuideUpVector),
                                setRange.outValueZ, scenePivots["heel_piv"].srt(1), overrideInvert=True)
    if n is not None:
        createdNodes.append(n)

    # ball roll
    n = setupRotationAxisDriver(namer.resolve("object", {"componentName": compName,
                                                         "side": compSide,
                                                         "section": "ballRollInvert",
                                                         "type": "multDoubleLinear"}),
                                zapi.Vector(ballRollTipGuideAimVector)*-1,
                                zapi.Vector(ballRollGuideUpVector),
                                setRange.outValueY,
                                ballRollPiv)
    if n is not None:
        createdNodes.append(n)

    createdNodes += [setRange, ballRollBreak]

    # post foot break rotation == toe rotation
    n = setupRotationAxisDriver(namer.resolve("object", {"componentName": compName,
                                                         "side": compSide,
                                                         "section": "ballRollToeInvert",
                                                         "type": "multDoubleLinear"}),
                                toeDefinition.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value*-1.0,
                                toeDefinition.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value,
                                ballRollBreak.outColorR,
                                scenePivots["toeTip_piv"].srt(index=1),

                                # useVector=0
                                )
    if n is not None:
        createdNodes.append(n)
    return createdNodes


def setupRotationAxisDriver(name,
                            aimVector,
                            upVector,
                            inputPlug,
                            outputTransformNode,
                            overrideInvert=False,
                            useVector=-1):
    """

    :param name:
    :type name:
    :param aimVector:
    :type aimVector:
    :param upVector:
    :type upVector:
    :param inputPlug:
    :type inputPlug:
    :param outputTransformNode:
    :type outputTransformNode:
    :param overrideInvert:
    :type overrideInvert:
    :param useVector:
    :type useVector:
    :return:
    :rtype:
    """
    axisIndex, isNegative = mayamath.perpendicularAxisFromAlignVectors(zapi.Vector(aimVector),
                                                                       zapi.Vector(upVector))
    if useVector >= 0:
        attributeName = "rotate" + mayamath.primaryAxisNameFromVector(aimVector if useVector == 0 else upVector)
    else:
        attributeName = zapi.localRotateAttrs[axisIndex]
    outputAttr = inputPlug
    doubleLinear = None
    if isNegative and not overrideInvert:
        doubleLinear = zapi.createDG(name, "multDoubleLinear")
        outputAttr.connect(doubleLinear.input1)
        doubleLinear.input2.set(-1)
        outputAttr = doubleLinear.output
    outputAttr.connect(outputTransformNode.attribute(attributeName))
    return doubleLinear
