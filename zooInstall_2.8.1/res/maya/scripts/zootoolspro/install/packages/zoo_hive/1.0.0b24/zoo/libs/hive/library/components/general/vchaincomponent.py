from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.rig import align, skeletonutils
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import general

STRETCH_ATTRS = ("stretch", "maxStretch",
                 "minStretch", "upperStretch",
                 "lowerStretch")


class VChainComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "vchaincomponent"
    icon = "componentVChain"
    worldEndRotation = False
    worldEndAimGuideId = ""
    # used by the marking menu to determine whether to build the ikfk matching actions.
    hasIkFk = True
    rootIkVisCtrlName = "ikUprCtrlVis"

    # used internally to determine if the end guide should have default alignment behaviour
    # i.e. align to child vs matching parent rotations
    _resetEndGuideAlignment = True
    # note: due to a legacy bug where the plane normal was inverted we flip the upVector if specified by this
    # component setting. so far this is only required on the leg. this needs to be resolved in the future.
    _flipAutoAlignUpVector = 1
    ikControlIds = ("endik", "upVec")
    fkControlIds = ("uprfk", "midfk", "endfk")
    deformJointIds = ("upr", "mid", "end")
    fixMidJointMMLabel = "Fix Mid"
    _spaceSwitchDriven = [api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "endik")),
                                                  label="End IK"),
                          api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "baseik")),
                                                  label="Base IK"),
                          api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "upVec")),
                                                  label="Pole Vector"),
                          api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "uprfk")),
                                                  label="FK")]

    _spaceSwitchDrivers = [api.SpaceSwitchUIDriver(**i.serialize()) for i in _spaceSwitchDriven] + [
        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "midfk")),
                                label="Mid FK"),
        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "endfk")), label="End FK")
    ]

    def idMapping(self):
        deformIds = {"upr": "upr",
                     "mid": "mid",
                     "end": "end"}
        outputIds = {"upr": "upr",
                     "mid": "mid",
                     "end": "end"}
        inputIds = {"upr": "upr",
                    "end": "end",
                    "upVec": "upVec"}
        rigLayerIds = {"upVec": "upVec"}
        return {api.constants.DEFORM_LAYER_TYPE: deformIds,
                api.constants.INPUT_LAYER_TYPE: inputIds,
                api.constants.OUTPUT_LAYER_TYPE: outputIds,
                api.constants.RIG_LAYER_TYPE: rigLayerIds}

    def setDeformNaming(self, namingConfig, modifier):
        compName, compSide = self.name(), self.side()
        for jnt in self.deformLayer().iterJoints():
            jntName = namingConfig.resolve("skinJointName", {"componentName": compName,
                                                             "side": compSide,
                                                             "id": jnt.id(),
                                                             "type": "joint"})
            jnt.rename(jntName, maintainNamespace=False, mod=modifier, apply=False)
        for inputNode in self.inputLayer().inputs():
            name = namingConfig.resolve("inputName", {"componentName": compName,
                                                      "side": compSide,
                                                      "type": "input",
                                                      "id": inputNode.id()})
            inputNode.rename(name, maintainNamespace=False, mod=modifier, apply=False)

        for outputNode in self.outputLayer().outputs():
            name = namingConfig.resolve("outputName", {"componentName": compName,
                                                       "side": compSide,
                                                       "type": "output",
                                                       "id": outputNode.id()})
            outputNode.rename(name, maintainNamespace=False, mod=modifier, apply=False)

    def spaceSwitchUIData(self):

        driven = self._spaceSwitchDriven
        # internal drivers ie. parent and World Space
        drivers = [api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "upr")),
                                           label="Parent Component", internal=True),
                   api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "world")),
                                           label="World Space",
                                           internal=True)]

        drivers += list(self._spaceSwitchDrivers)

        return {
            "driven": driven,
            "drivers": drivers
        }

    def _createAutoPoleGuideGraph(self, guideLayer):
        guideLayer.deleteNamedGraph("autoPoleVector", self.configuration.graphRegistry())
        # align the vchain guides with coplanar, align all others as normal
        uprGuide, midGuide, endGuide, upVecGuide = guideLayer.findGuides("upr", "mid",
                                                                         'end', "upVec")

        with zapi.lockStateAttrContext(upVecGuide, zapi.localTransformAttrs + [zapi.localRotateAttr,
                                                                               zapi.localTranslateAttr,
                                                                               zapi.localScaleAttr],
                                       False):
            upVecGuide.resetTransform(True, True, scale=False)

            graphRegistry = self.configuration.graphRegistry()
            graphData = graphRegistry.graph("autoPoleVector")
            sceneGraph = api.componentutils.createGraphForComponent(self, guideLayer,
                                                                    graphData, track=True,
                                                                    createIONodes=False)
            sceneGraph.connectToInput("autoAlign", upVecGuide.autoAlign)
            sceneGraph.connectToInput("startWorldMatrix", uprGuide.worldMatrixPlug())
            sceneGraph.connectToInput("midWorldMatrix", midGuide.worldMatrixPlug())
            sceneGraph.connectToInput("endWorldMatrix", endGuide.worldMatrixPlug())
            sceneGraph.connectToInput("parentInverseMatrix", midGuide.worldInverseMatrixPlug())
            sceneGraph.connectToInput("distance", upVecGuide.autoPoleVectorDistance)
            sceneGraph.connectToInput("autoPoleVectorDefaultPosition", upVecGuide.autoPoleVectorDefaultPosition)
            sceneGraph.connectToInput("zeroAngleVector", upVecGuide.autoPoleVectorZeroDirection)
            sceneGraph.node("aimMatrix").secondaryMode.set(2)
            sceneGraph.setInputAttr("aimSecondaryInputAxis", zapi.Vector(0, 1, 0))
            sceneGraph.connectFromOutput("worldMatrix", [upVecGuide.offsetParentMatrix])

    def setupGuide(self):
        super(VChainComponent, self).setupGuide()
        guideLayer = self.guideLayer()
        self._createAutoPoleGuideGraph(guideLayer)

    def alignGuides(self):
        if not self.hasGuide():
            return False
        guideLayer = self.guideLayer()
        guideLayer.deleteNamedGraph("autoPoleVector", self.configuration.graphRegistry())

        # align the vchain guides with coplanar, align all others as normal
        uprGuide, midGuide, endGuide, upVecGuide = guideLayer.findGuides("upr", "mid", "end", "upVec")
        vChainGuides = [uprGuide, midGuide, endGuide]
        positions = [o.translation() for o in vChainGuides]
        aimVector = uprGuide.autoAlignAimVector.value()
        upVector = uprGuide.autoAlignUpVector.value()
        rotateAxis, _ = mayamath.perpendicularAxisFromAlignVectors(aimVector, upVector)
        rotateAxis = zapi.Vector(mayamath.AXIS_VECTOR_BY_IDX[rotateAxis])
        if mayamath.isVectorNegative(aimVector):
            rotateAxis *= -1

        constructedPlane = align.constructPlaneFromPositions(positions, vChainGuides, rotateAxis=rotateAxis)
        guides, matrices = [], []

        for currentGuide, targetGuide in align.alignNodesIterator(vChainGuides,
                                                                  constructedPlane,
                                                                  skipEnd=True):
            if not currentGuide.autoAlign.asBool():
                continue

            upVector = currentGuide.autoAlignUpVector.value() * self._flipAutoAlignUpVector
            aimVector = currentGuide.autoAlignAimVector.value()
            rot = mayamath.lookAt(currentGuide.translation(zapi.kWorldSpace),
                                  targetGuide.translation(zapi.kWorldSpace),
                                  aimVector=zapi.Vector(aimVector),
                                  upVector=zapi.Vector(upVector),
                                  worldUpVector=constructedPlane.normal())
            transform = currentGuide.transformationMatrix()
            transform.setRotation(rot)
            matrices.append(transform.asMatrix())
            guides.append(currentGuide)

        if endGuide.autoAlign.asBool():
            if self._resetEndGuideAlignment:
                transform = endGuide.transformationMatrix()
                midRotation = zapi.TransformationMatrix(matrices[-1]).rotation(zapi.kWorldSpace)
                transform.setRotation(midRotation)
                matrices.append(transform.asMatrix())
                guides.append(endGuide)
            else:
                upVector = endGuide.autoAlignUpVector.value()
                aimVector = endGuide.autoAlignAimVector.value()
                endGuide.aimToChild(aimVector=zapi.Vector(aimVector),
                                    upVector=zapi.Vector(upVector))
        api.setGuidesWorldMatrix(guides, matrices)
        self._createAutoPoleGuideGraph(guideLayer)

        return True

    def setupInputs(self):
        super(VChainComponent, self).setupInputs()
        # bind the inputs and outputs to the deform joints
        inputLayer = self.inputLayer()
        rootIn, upVecIn, ikEndIn = inputLayer.findInputNodes("upr", "upVec", "endik")
        guideLayerDef = self.definition.guideLayer
        rootInMatrix = guideLayerDef.guide("upr").transformationMatrix(scale=False)
        # We don't propagate scale from the guide
        rootIn.setWorldMatrix(rootInMatrix.asMatrix())

        # We don't propagate scale from the guide
        if not self.worldEndRotation:
            ikEndInMatrix = guideLayerDef.guide("end").transformationMatrix(scale=False)
        else:

            aimGuide, endGuide = guideLayerDef.findGuides(self.worldEndAimGuideId, "end")
            rot = mayamath.lookAt(zapi.Vector(endGuide.translate), zapi.Vector(aimGuide.translate),
                                  mayamath.ZAXIS_VECTOR, mayamath.YAXIS_VECTOR,
                                  constrainAxis=zapi.Vector(0, 1, 1))
            ikEndInMatrix = endGuide.transformationMatrix(rotate=False, scale=False)
            ikEndInMatrix.setRotation(rot)

        ikEndIn.setWorldMatrix(ikEndInMatrix.asMatrix())
        upVecInMatrix = guideLayerDef.guide("upVec").transformationMatrix(rotate=False, scale=False)
        upVecIn.setWorldMatrix(upVecInMatrix.asMatrix())

    def postSetupDeform(self, parentJoint):
        outputLayer = self.outputLayer()
        deformLayer = self.deformLayer()
        ids = list(self.deformJointIds)

        joints = deformLayer.findJoints(*ids)

        for index, (driver, drivenId) in enumerate(zip(joints, ids)):
            if driver is None:
                continue
            driven = outputLayer.outputNode(drivenId)
            # world Space matrix since we're the root joint for the component
            if index == 0:
                const, constUtilities = api.buildConstraint(driven,
                                                            drivers={"targets": ((driver.fullPathName(partialName=True,
                                                                                                      includeNamespace=False),
                                                                                  driver),)},
                                                            constraintType="matrix",
                                                            maintainOffset=False)
                outputLayer.addExtraNodes(constUtilities)
            else:
                # local space matrix
                driver.attribute("matrix").connect(driven.offsetParentMatrix)
                driven.resetTransform()
            driver.rotateOrder.connect(driven.rotateOrder)
        super(VChainComponent, self).postSetupDeform(parentJoint)

    def preSetupRig(self, parentNode):
        """Overridden to handle stretch state, where we remove or add the anim stretch attributes.

        :param parentNode:
        :type parentNode: :class:`zapi.DagNode`
        """
        # stretch, lock, slide
        definition = self.definition
        hasStretch = definition.guideLayer.guideSetting("hasStretch").value
        rigLayer = definition.rigLayer  # type: api.RigLayerDefinition
        if not hasStretch:
            rigLayer.deleteSettings("controlPanel", STRETCH_ATTRS)
        else:
            orig = self.definition.originalDefinition.rigLayer  # type: api.RigLayerDefinition
            lastInsertName = "ikfk"
            for sett in STRETCH_ATTRS:
                origSetting = orig.setting("controlPanel", sett)
                if origSetting:
                    rigLayer.insertSettingByName("controlPanel", lastInsertName, origSetting, before=False)
                    lastInsertName = origSetting.name
        super(VChainComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        deformLayer = self.deformLayer()
        rigLayer = self.rigLayer()
        controlPanel = self.controlPanel()
        inputLayer = self.inputLayer()
        definition = self.definition
        guideLayerDef = definition.guideLayer
        ikGuides = guideLayerDef.findGuides("upr", "mid", "end")
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.name(), self.side()
        # presize our data
        rootIn, ikEndIn, upVecIn = inputLayer.findInputNodes("upr", "endik", "upVec")

        # todo: move to the definition
        fkCtrls = [None] * 3  # type: list[None or api.ControlNode]
        ikJoints = [None] * 3  # type: list[None or api.Joint]
        self._ikCtrlsTuple = {}  # "baseik", "endik", "upvec"
        self._fkCtrlsTuple = {}

        namer = self.namingConfiguration()
        blendAttr = controlPanel.ikfk
        blendAttr.setFloat(guideLayerDef.guideSetting("ikfk_default").value)
        upvecGuide = guideLayerDef.guide("upVec")
        upVecName = namer.resolve("controlName", {"componentName": compName, "side": compSide,
                                                  "system": "poleVector",
                                                  "id": upvecGuide.id,
                                                  "type": "control"})

        upVecCtrl = rigLayer.createControl(name=upVecName,
                                           id=upvecGuide.id,
                                           translate=upvecGuide.translate,
                                           rotate=(0.0, 0.0, 0.0, 1.0),
                                           parent=rigLayerRoot,
                                           shape=upvecGuide.shape,
                                           rotateOrder=upvecGuide.rotateOrder,
                                           selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                           srts=[{"name": "_".join([upVecName, "srt"]), "id": upvecGuide.id}])

        self._ikCtrlsTuple["upvec"] = upVecCtrl
        parentSpaceRig = api.createDag(namer.resolve("object", {"componentName": compName,
                                                                "side": compSide,
                                                                "section": "parent_space",
                                                                "type": "transform"}), "transform",
                                       parent=rigLayerRoot)
        parentSpaceRig.setWorldMatrix(parentNode.worldMatrix())
        const, constUtilities = api.buildConstraint(parentSpaceRig,
                                                    drivers={"targets": (
                                                        (rootIn.fullPathName(partialName=True, includeNamespace=False),
                                                         rootIn),)},
                                                    constraintType="matrix",
                                                    maintainOffset=True
                                                    )

        rigLayer.addExtraNodes(constUtilities)
        rigLayer.addExtraNode(parentSpaceRig)
        # define or parents
        blendTransformParent = parentSpaceRig
        ikParent = parentSpaceRig
        fkCtrlPt = parentSpaceRig

        for i, guide in enumerate(ikGuides):
            guideId = guide.id
            fkGuideId = guideId + api.constants.FKTYPE
            ikGuideId = guideId + api.constants.IKTYPE

            ikName = namer.resolve("jointName", {"componentName": compName, "side": compSide,
                                                 "id": ikGuideId,
                                                 "system": api.constants.IKTYPE,
                                                 "type": "joint"})

            fkControlName = namer.resolve("controlName", {"componentName": compName, "side": compSide,
                                                          "system": api.constants.FKTYPE,
                                                          "id": fkGuideId,
                                                          "type": "control"})
            fkCtrl = rigLayer.createControl(
                name=fkControlName,
                id=fkGuideId,
                translate=guide.translate,
                rotate=guide.rotate,
                parent=fkCtrlPt,
                rotateOrder=guide.rotateOrder,
                shape=guide.shape,
                shapeTransform=guide.shapeTransform,
                selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                srts=[{"name": "_".join([fkControlName, "srt"])}]
            )

            fkCtrls[i] = fkCtrl
            fkCtrlPt = fkCtrl
            self._fkCtrlsTuple[fkGuideId] = fkCtrl
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
            rigLayer.addTaggedNode(blendTransform, guideId)
            blendTransformParent = blendTransform
            # ik
            ikJnt = rigLayer.createJoint(name=ikName,
                                         translate=guide.translate,
                                         rotate=guide.rotate,
                                         parent=ikParent,
                                         rotateOrder=guide.rotateOrder,
                                         id=ikGuideId)
            ikJoints[i] = ikJnt
            ikParent = ikJnt

            # we are currently on the end guide
            guideName = guide.id
            if guideName == "end":
                ikName = namer.resolve("controlName", {"componentName": compName,
                                                       "side": compSide, "id": ikGuideId,
                                                       "system": api.constants.IKTYPE,
                                                       "type": "control"})
                ctrl = rigLayer.createControl(name=ikName,
                                              id=ikGuideId,
                                              translate=guide.translate,
                                              rotate=guide.rotate if not self.worldEndRotation else ikEndIn.rotation(
                                                  space=zapi.kWorldSpace),
                                              parent=rigLayerRoot,
                                              rotateOrder=guide.rotateOrder,
                                              shape=guide.shape,
                                              shapeTransform=guide.shapeTransform,
                                              selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                              srts=[{"name": "_".join([ikName, "srt"])}])
                self._ikCtrlsTuple[ikGuideId] = ctrl

                const, constUtilities = api.buildConstraint(ikJnt,
                                                            drivers={"targets": (
                                                                (ctrl.fullPathName(partialName=True,
                                                                                   includeNamespace=False),
                                                                 ctrl),)},
                                                            constraintType="orient",
                                                            maintainOffset=True
                                                            )
                rigLayer.addExtraNodes(constUtilities)
                ctrl.connect("scale", ikJnt.attribute("scale"))

            self._blendTriNodes(rigLayer, blendTransform, deformLayer.joint(guide.id), ikJnt, fkCtrl, blendAttr, guide)

        # ikRoot control
        guide = ikGuides[0]
        baseikName = namer.resolve("controlName", {"componentName": compName, "side": compSide,
                                                   "system": api.constants.IKTYPE,
                                                   "id": "baseik", "type": "control"})
        ikRootCtrl = rigLayer.createControl(name=baseikName,
                                            id="baseik",
                                            translate=guide.translate,
                                            rotate=guide.rotate,
                                            parent=rigLayerRoot,
                                            rotateOrder=guide.rotateOrder,
                                            shape=guide.shape,
                                            shapeTransform=guide.shapeTransform,
                                            selectionChildHighlighting=self.configuration.selectionChildHighlighting)
        ikRootSrt = rigLayer.createSrtBuffer("baseik", "_".join([baseikName, "srt"]))
        controlPanel.attribute(self.rootIkVisCtrlName).connect(ikRootCtrl.visibility)
        ikRootCtrl.setLockStateOnAttributes(("rotate", "scale", "visibility"))
        ikRootCtrl.showHideAttributes(zapi.localRotateAttrs + zapi.localScaleAttrs, False)
        self._ikCtrlsTuple["baseik"] = ikRootCtrl
        const, constUtilities = api.buildConstraint(ikJoints[0],
                                                    drivers={"targets": (
                                                        ("baseik", ikRootCtrl),)},
                                                    constraintType="point",
                                                    maintainOffset=True
                                                    )
        rigLayer.addExtraNodes(constUtilities)
        const, constUtilities = api.buildConstraint(ikJoints[0],
                                                    drivers={"targets": (
                                                        ("baseik", ikRootCtrl),)},
                                                    constraintType="orient",
                                                    maintainOffset=True
                                                    )
        rigLayer.addExtraNodes(constUtilities)
        const, constUtilities = api.buildConstraint(ikRootCtrl.srt(),
                                                    drivers={"targets": (
                                                        (rootIn.fullPathName(partialName=True, includeNamespace=False),
                                                         rootIn),)},
                                                    constraintType="matrix",
                                                    maintainOffset=True
                                                    )
        rigLayer.addExtraNodes(constUtilities)

        # take the scale from the Upr Input node and multiply that by the input for each IK srt other than baseIK
        # this will give us the scale support without reaching externally of the component IO
        endIkCtrl = self._ikCtrlsTuple["endik"]
        pvCtrl = self._ikCtrlsTuple["upvec"]

        rootScaleMatrix = zapi.createDG(namer.resolve("object", {"componentName": compName,
                                                                 "side": compSide,
                                                                 "section": endIkCtrl.id(),
                                                                 "type": "pickScale"}), "pickMatrix")
        rootScaleMatrix.useRotate = False
        rootScaleMatrix.useTranslate = False
        rootIn.attribute("worldMatrix")[0].connect(rootScaleMatrix.inputMatrix)
        # compute the offset
        endIkCtrl.srt().resetTransform()
        pvCtrl.srt().resetTransform()
        endIkScaleMulti = zapi.createMultMatrix(namer.resolve("object", {"componentName": compName,
                                                                         "side": compSide,
                                                                         "section": endIkCtrl.id(),
                                                                         "type": "rootScaleMult"}),
                                                (rootScaleMatrix.outputMatrix, ikEndIn.attribute("worldMatrix")[0]),
                                                output=endIkCtrl.srt().offsetParentMatrix)
        upvecScaleMulti = zapi.createMultMatrix(namer.resolve("object", {"componentName": compName,
                                                                         "side": compSide,
                                                                         "section": pvCtrl.id(),
                                                                         "type": "rootScaleMult"}),
                                                (rootScaleMatrix.outputMatrix, upVecIn.attribute("worldMatrix")[0]),
                                                output=pvCtrl.srt().offsetParentMatrix)
        rigLayer.addExtraNodes((endIkScaleMulti, upvecScaleMulti, rootScaleMatrix))

        ikJoints[1].preferredAngle = ikJoints[1].rotation()
        self._doIkSolve(ikJoints)
        # annotation between UpVector and mid control
        annName = namer.resolve("object", {"componentName": compName,
                                           "side": compSide,
                                           "section": "upvec",
                                           "type": "annotation"})
        annotation = rigLayer.createAnnotation(annName,
                                               ikJoints[1],
                                               self._ikCtrlsTuple["upvec"],
                                               parent=rigLayerRoot)
        self._setupVisibility(fkCtrls, annotation, ikRootSrt, blendAttr, rigLayer)

        # for ikfk matching we need the initial matrix offset
        originalOffset = endIkCtrl.offsetMatrix(rigLayer.control("endfk"), zapi.kWorldSpace)
        rigLayer.settingNode("constants").attribute("constant_ikfkEndOffset").set(originalOffset)

    def _setupVisibility(self, fkCtrls, annotation, ikRootCtrl, blendAttr, rigLayer):
        # visibility setup
        naming = self.namingConfiguration()
        revNode = zapi.createReverse(naming.resolve("object", {"componentName": self.name(),
                                                               "side": self.side(),
                                                               "section": "ikfkVisSwitch",
                                                               "type": "reverse"}),
                                     inputs=[blendAttr],
                                     outputs=[])

        revOutputX = revNode.outputX
        reverseVisSwitch = rigLayer.addAttribute("reverseVisSwitch", Type=api.attrtypes.kMFnMessageAttribute)
        revOutputX.connect(annotation.visibility)
        revOutputX.connect(ikRootCtrl.visibility)
        revNode.message.connect(reverseVisSwitch)

        for i in self._ikCtrlsTuple.values():
            [revOutputX.connect(obj.visibility) for obj in i.shapes()]
        for i in fkCtrls:
            [blendAttr.connect(obj.visibility) for obj in i.shapes()]
        rigLayer.addExtraNodes([revNode])

    def _blendTriNodes(self, rigLayer, blendOutput, driven, ik, fk, blendAttr, guide):
        naming = self.namingConfiguration()
        # create the blendMatrix and connect to the offset parent Matrix
        # ensure transforms are reset in the process
        blendMat = zapi.createDG(naming.resolve("object", {"componentName": self.name(),
                                                           "side": self.side(),
                                                           "section": "{}IkFk".format(guide.id),
                                                           "type": "blendMatrix"}),
                                 "blendMatrix")
        localMtx = zapi.createDG(naming.resolve("object", {"componentName": self.name(),
                                                           "side": self.side(),
                                                           "section": "{}IkFkLocal".format(guide.id),
                                                           "type": "multMatrix"}),
                                 "multMatrix")
        blendMat.outputMatrix.connect(localMtx.matrixIn[0])
        blendOutput.parent().attribute("worldInverseMatrix")[0].connect(localMtx.matrixIn[1])
        localMtx.matrixSum.connect(blendOutput.offsetParentMatrix)

        targetElement = blendMat.target[0]
        ik.attribute("worldMatrix")[0].connect(blendMat.inputMatrix)
        fk.attribute("worldMatrix")[0].connect(targetElement.child(0))
        blendAttr.connect(targetElement.child(2))  # weight attr
        # todo: replace with matrix based constraint, note have to handle jointOrient as offset
        _, constUtilities = api.buildConstraint(driven,
                                                drivers={"targets": (("", blendOutput),)},
                                                constraintType="point",
                                                maintainOffset=True
                                                )
        rigLayer.addExtraNodes(constUtilities)
        _, constUtilities = api.buildConstraint(driven,
                                                drivers={"targets": (("", blendOutput),)},
                                                constraintType="orient",
                                                maintainOffset=True
                                                )
        rigLayer.addExtraNodes(constUtilities)
        _, constUtilities = api.buildConstraint(driven,
                                                drivers={"targets": (("", blendOutput),)},
                                                constraintType="scale",
                                                maintainOffset=True
                                                )
        rigLayer.addExtraNodes(constUtilities)

        rigLayer.addExtraNode(blendMat)
        return blendMat

    def _doIkSolve(self, ikJoints):
        definition = self.definition
        ikCtrls = self._ikCtrlsTuple
        handleParent = self._ikCtrlsTuple["endik"]
        namer = self.namingConfiguration()
        rigLayer = self.rigLayer()

        compName, compSide = self.name(), self.side()
        # # ikSolver happens last
        # maya iksolvers are, one solver for the whole rig so make sure we create it at the root namespace
        ikName = namer.resolve("ikHandle", {"componentName": compName,
                                            "section": ikCtrls["endik"].name(),
                                            "side": compSide,
                                            "type": "ikHandle"})
        ikHandle, ikEffector = api.createIkHandle(name=ikName,
                                                  startJoint=ikJoints[0],
                                                  endJoint=ikJoints[2],
                                                  parent=handleParent
                                                  )
        upVecConstraint = api.nodeByName(cmds.poleVectorConstraint(ikCtrls["upvec"].fullPathName(),
                                                                   ikHandle.fullPathName())[0])
        ikHandle.hide()
        ikEffector.hide()

        # create a message attribute to make the ikhandle easily
        metaHandlePlug = rigLayer.addAttribute("ikhandles",
                                               value=None,
                                               Type=api.attrtypes.kMFnMessageAttribute,
                                               isArray=True)
        ikHandle.message.connect(metaHandlePlug.element(0))
        controlPanel = self.controlPanel()
        controlPanel.connect("ikRoll", ikHandle.twist)
        # stretch, lock, slide
        hasStretch = definition.guideLayer.guideSetting("hasStretch").value
        if not hasStretch:
            return ikHandle
        self._setupStretch(rigLayer, ikJoints,
                           definition.guideLayer.findGuides("mid", "end"),
                           self._ikCtrlsTuple,
                           self.inputLayer().inputNode("upr"))

        rigLayer.addExtraNodes((upVecConstraint, ikHandle, ikEffector))
        return ikHandle

    def _setupStretch(self, rigLayer, ikJoints, guides, ctrls, rootInputNode):
        constantsNode = rigLayer.settingNode("constants")
        controlPanel = self.controlPanel()
        # bake in the initial lengths of the segments
        midToUprLen = ikJoints[1].translation(api.kTransformSpace).x
        midToLwrLen = ikJoints[2].translation(api.kTransformSpace).x
        constantsUprInit = constantsNode.constant_uprInitialLength
        constantsLwrInit = constantsNode.constant_lwrInitialLength
        constantsTotalInit = constantsNode.constant_totalInitLength
        constantsUprInit.set(midToUprLen)
        constantsLwrInit.set(midToLwrLen)
        constantsTotalInit.set(midToUprLen + midToLwrLen)
        # cache the controlPanel attrs
        stretchAttr = controlPanel.stretch
        upperStretch, lwrStretch = controlPanel.upperStretch, controlPanel.lowerStretch
        lockAttr = controlPanel.attribute("lock")
        minStretch, maxStretch = controlPanel.minStretch, controlPanel.maxStretch
        negate = mayamath.isVectorNegative(guides[0].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value)
        # First create the primary stretch between the start and end
        graphRegistry = self.configuration.graphRegistry()
        globalStretchGraphData = graphRegistry.graph("ikGlobalStretchNeg" if negate else "ikGlobalStretch")
        globalSegmentGraphData = graphRegistry.graph("ikSegmentScaleStretch")

        globalStretchGraph = api.componentutils.createGraphForComponent(self, rigLayer,
                                                                        globalStretchGraphData, createIONodes=False)
        globalStretchGraph.connectToInput("startWorldMtx", ctrls["baseik"].attribute("worldMatrix")[0])
        globalStretchGraph.connectToInput("endWorldMtx", ctrls["endik"].attribute("worldMatrix")[0])
        globalStretchGraph.connectToInput("initialTotalLength", constantsTotalInit)
        globalStretchGraph.connectToInput("globalScale", rootInputNode.attribute("scale")[1])
        globalStretchGraph.connectToInput("minStretch", minStretch)
        globalStretchGraph.connectToInput("maxStretch", maxStretch)
        outLengthPlug = globalStretchGraph.outputAttr("outLength")

        segmentLengthPlugs = [constantsUprInit, constantsLwrInit]
        stretchAttrs = [upperStretch, lwrStretch]
        segmentCtrls = [ctrls["baseik"], ctrls["endik"]]
        upVector = ctrls["upvec"]

        # now loop over the segments and create the stretch graph for each
        for index, [startEnd, segmentTag] in enumerate(zip(general.chunks(ikJoints, 2, overlap=1), ["upr", "lwr"])):
            _, outputNode = startEnd
            globalSegmentGraphData.name = globalSegmentGraphData.name + segmentTag
            sceneGraph = api.componentutils.createGraphForComponent(self, rigLayer, globalSegmentGraphData,
                                                                    segmentTag, createIONodes=False)
            sceneGraph.connectToInput("globalStretchAmount", outLengthPlug)
            sceneGraph.connectToInput("initialLength", segmentLengthPlugs[index])
            sceneGraph.connectToInput("hasStretchAmount", stretchAttr)
            sceneGraph.connectToInput("lockAmount", lockAttr)
            sceneGraph.connectToInput("stretchAmount", stretchAttrs[index])
            sceneGraph.connectToInput("poleVectorWorldMtx", upVector.attribute("worldMatrix")[0])
            sceneGraph.connectToInput("endWorldMtx", segmentCtrls[index].attribute("worldMatrix")[0])
            aimVector = guides[index].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            axisName = mayamath.primaryAxisNameFromVector(aimVector)
            sceneGraph.connectFromOutput("outStretch", [outputNode.attribute("translate{}".format(axisName))])

    def switchToIk(self):
        deformLayer = self.deformLayer()
        rigLayer = self.rigLayer()
        endik, upVec = rigLayer.findControls(*self.ikControlIds)
        deformJoints = deformLayer.findJoints(*self.deformJointIds)
        midGuide, upVecGuide = self.definition.guideLayer.findGuides("mid", "upVec")
        distance = (midGuide.translate - upVecGuide.translate).length()
        try:
            pvPosition = skeletonutils.poleVectorPosition(deformJoints[0].translation(),
                                                          deformJoints[1].translation(),
                                                          deformJoints[2].translation(),
                                                          distance=distance)
        except ValueError:
            pvPosition = deformJoints[1].translation()
        originalOffset = rigLayer.settingNode("constants").attribute("constant_ikfkEndOffset").value()
        endMatrix = originalOffset.inverse() * deformJoints[2].worldMatrix() * endik.parentInverseMatrix()

        endik.setMatrix(endMatrix)
        upVec.setTranslation(pvPosition, space=zapi.kWorldSpace)
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(0)
        return {
            "controls": [endik, upVec],
            "attributes": [ikfkAttr],
            "selectables": [endik]
        }

    def switchToFk(self):
        # to switch to fk just grab the bind skeleton transforms
        # and apply the transform to the fk controls
        deformLayer = self.deformLayer()
        rigLayer = self.rigLayer()
        deformJnts = deformLayer.findJoints(*self.deformJointIds)
        controls = rigLayer.findControls(*self.fkControlIds)
        mats = []
        for jnt, ctrl in zip(deformJnts, controls):
            mat = jnt.worldMatrix()
            mat = zapi.TransformationMatrix(mat)
            mat.setScale((1, 1, 1), zapi.kWorldSpace)
            mats.append(mat.asMatrix())

        for ctrl, mat in zip(controls, mats):
            ctrl.setWorldMatrix(mat)
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(1)
        return {
            "controls": controls,
            "selectables": [controls[2]],
            "attributes": [ikfkAttr]
        }
