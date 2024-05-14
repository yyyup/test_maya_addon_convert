from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath


class AimComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "aimcomponent"
    icon = "componentAim"

    def idMapping(self):
        deformIds = {"eye": "eye"}
        outputIds = {"eye": "root",
                     "aim": "aim"}
        inputIds = {"eye": "root"}
        rigLayerIds = {"eye": "eye",
                       "aim": "aim"}
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
        return {
            "driven": [
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "eye")),
                                        label="Eye"),
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "aim")),
                                        label="Aim")
            ],
            "drivers": [api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "root")),
                                                label="Parent Component", internal=True),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "eye")),
                                                label="Eye"),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "aim")),
                                                label="Aim")
                        ]
        }

    def alignGuides(self):
        if not self.hasGuide():
            return
        guideLayer = self.guideLayer()
        eye, aim, upVec = guideLayer.findGuides("eye", "aim", "upVec")
        if not eye.autoAlign.asBool():
            return []
        upVector = eye.autoAlignUpVector.value()
        aimVector = eye.autoAlignAimVector.value()
        quat = mayamath.lookAt(sourcePosition=eye.translation(),
                               aimPosition=aim.translation(),
                               aimVector=zapi.Vector(aimVector),
                               upVector=zapi.Vector(upVector),
                               worldUpVector=upVec.translation(space=zapi.kWorldSpace))
        currentMatrix = eye.transformationMatrix()
        currentMatrix.setScale((1, 1, 1), zapi.kWorldSpace)
        currentMatrix.setRotation(quat)
        # batch update the guides.
        api.setGuidesWorldMatrix([eye], [currentMatrix.asMatrix()])

    def setupInputs(self):
        super(AimComponent, self).setupInputs()
        inputLayer = self.inputLayer()
        guideDef = self.definition
        rootIn = inputLayer.inputNode("root")
        rootMat = guideDef.guideLayer.guide("eye").transformationMatrix(scale=False)
        rootIn.setWorldMatrix(rootMat.asMatrix())

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        rigLayerTransform = rigLayer.rootTransform()
        deformLayer = self.deformLayer()
        outputLayer = self.outputLayer()
        inputLayer = self.inputLayer()
        namer = self.namingConfiguration()
        rootIn = inputLayer.inputNode("root")
        deformJoint = deformLayer.joint("eye")
        rootOut = outputLayer.outputNode("root")
        definition = self.definition
        guideLayer = definition.guideLayer
        eyeDef = guideLayer.guide("eye")
        compName, compSide = self.name(), self.side()
        extraNodes = []
        # create parent offset for deformLayer
        controls = {}
        for index, guidDef in enumerate((guideLayer.guide("aim"), eyeDef)):
            # create the control
            guideId = guidDef.id
            name = namer.resolve("controlName", {"componentName": compName,
                                                 "side": compSide,
                                                 "id": guideId,
                                                 "type": "control"})
            ctrl = rigLayer.createControl(name=name,
                                          id=guideId,
                                          rotateOrder=guidDef.get("rotateOrder", 0),
                                          translate=guidDef.get("translate", (0, 0, 0)),
                                          rotate=guidDef.get("rotate", (0, 0, 0, 1)),
                                          parent=None,
                                          shape=guidDef.get("shape"),
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                          srts=[{"id": guideId, "name": "_".join([name, "srt"])}])
            controls[guideId] = ctrl
            # # create the output node
            out = outputLayer.outputNode(guideId)
            if out is None:
                continue
            const, constUtilities = zapi.buildConstraint(out, {
                "targets": ((ctrl.fullPathName(partialName=True, includeNamespace=True), ctrl),)},
                                                         constraintType="matrix", maintainOffset=False)

            extraNodes.extend(constUtilities)

        aimDef = guideLayer.guide("upVec")
        aimUpVec = api.createDag(aimDef.name, "transform")
        aimUpVec.setWorldMatrix(api.Matrix(aimDef.worldMatrix))
        aimUpVec.setParent(rigLayerTransform)
        # constrain the UpVec to the root input that way it follows based on the incoming parent transform
        const, constUtilities = api.buildConstraint(aimUpVec,
                                                    drivers={"targets": (
                                                        (rootIn.fullPathName(partialName=True, includeNamespace=False),
                                                         rootIn),)},
                                                    maintainOffset=True,
                                                    constraintType="matrix"
                                                    )
        extraNodes.extend(constUtilities)
        # srt which will be constrained by the aim
        aimSpaceSrt = rigLayer.createSrtBuffer("eye", "_".join([eyeDef.name, "srt"]))
        aimControl = controls["aim"]
        const, constUtilities = api.buildConstraint(aimSpaceSrt,
                                                    drivers={"targets": ((aimControl.fullPathName(partialName=True,
                                                                                                  includeNamespace=False),
                                                                          aimControl),)},
                                                    constraintType="aim",
                                                    worldUpType=1,
                                                    aimVector=list(
                                                        eyeDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value),
                                                    worldUpObject=aimUpVec.fullPathName(),
                                                    maintainOffset=True
                                                    )
        extraNodes.extend(constUtilities)
        rootEyeSrt = controls["eye"].srt()
        rootAimSrt = controls["aim"].srt()
        # bind deform joints to the ctrl
        extraNodes.extend(zapi.buildConstraint(deformJoint, {"targets": (("eye", controls["eye"]),)},
                                               constraintType="parent", maintainOffset=True,
                                               trace=False)[1])
        extraNodes.extend(zapi.buildConstraint(deformJoint, {"targets": (("eye", controls["eye"]),)},
                                               constraintType="scale", maintainOffset=True,
                                               trace=False)[1])
        extraNodes.extend(zapi.buildConstraint(rootEyeSrt, {"targets": (("parent", rootIn),)},
                                               constraintType="matrix", maintainOffset=True,
                                               trace=False)[1])
        extraNodes.extend(zapi.buildConstraint(rootAimSrt, {"targets": (("parent", rootIn),)},
                                               constraintType="matrix", maintainOffset=True,
                                               trace=False)[1])
        extraNodes.extend(zapi.buildConstraint(rootOut, {"targets": (("parent", deformJoint),)},
                                               constraintType="matrix", maintainOffset=True,
                                               trace=False)[1])
        rigLayer.addExtraNodes(extraNodes)
