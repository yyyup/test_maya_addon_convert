from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath


class JawComponent(api.Component):
    creator = "DavidSparrow"
    description = "The Triple Jaw component which contains top lip, bottom lip and jaw"
    definitionName = "jaw"
    icon = "componentJaw"

    def idMapping(self):
        deformIds = {"topLip": "topLip",
                     "jaw": "jaw",
                     "chin": "chin",
                     "botLip": "botLip"}
        outputIds = {"topLip": "topLip",
                     "jaw": "jaw",
                     "chin": "chin",
                     "botLip": "botLip"}
        inputIds = {"jaw": "rootIn"}
        rigLayerIds = {"topLip": "topLip",
                       "jaw": "jaw",
                       "rotAll": "rotAll",
                       "botLip": "botLip"}
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
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "rotAll")),
                                        label="Rotate All"),
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "Jaw")),
                                        label="Jaw"),
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "topLip")),
                                        label="Top Lip"),
                api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", "botLip")),
                                        label="Bottom Lip")
            ],
            "drivers": [api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "root")),
                                                label="Parent Component", internal=True),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "rotAll")),
                                                label="Rotate All"),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "Jaw")),
                                                label="Jaw"),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "topLip")),
                                                label="Top Lip"),
                        api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", "botLip")),
                                                label="Bottom Lip")
                        ]
        }

    def alignGuides(self):
        guideLayer = self.guideLayer()
        guides = {i.id(): i for i in guideLayer.iterGuides(includeRoot=False)}
        aimGuide = guides["chin"]
        aimPosition = aimGuide.translation()
        guidesToModify, matrices = [], []

        for guideId, guide in guides.items():
            if not guide.autoAlign.asBool():
                continue
            if guideId == "chin":
                guide.resetTransform(False, True, True)
                continue
            aimVector = zapi.Vector(guide.autoAlignAimVector.value())
            upVector = zapi.Vector(guide.autoAlignUpVector.value())
            quat = mayamath.lookAt(guide.translation(),
                                   aimPosition, aimVector=aimVector, upVector=upVector, worldUpVector=None,
                                   constrainAxis=zapi.Vector(1, 1, 1))
            currentMatrix = guide.transformationMatrix()
            currentMatrix.setScale((1, 1, 1), zapi.kWorldSpace)
            currentMatrix.setRotation(quat)
            matrices.append(currentMatrix)
            guidesToModify.append(guide)

        # batch update the guides.
        api.setGuidesWorldMatrix(guidesToModify, matrices)

    def setupInputs(self):
        super(JawComponent, self).setupInputs()
        inputLayer = self.inputLayer()
        guideDef = self.definition
        worldIn = inputLayer.inputNode("root")
        trans = guideDef.guideLayer.guide("jaw").transformationMatrix(scale=False)
        worldIn.setWorldMatrix(trans.asMatrix())

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        deformLayer = self.deformLayer()
        inputLayer = self.inputLayer()
        outputLayer = self.outputLayer()
        guideLayerDef = self.definition.guideLayer
        naming = self.namingConfiguration()
        outputs = {i.id(): i for i in outputLayer.outputs()}
        compName, compSide = self.name(), self.side()
        _ctrls = {}
        for guidDef in guideLayerDef.iterGuides(includeRoot=False):

            # create the control
            guideId = guidDef.id
            outputNode = outputs.get(guideId)
            jnt = deformLayer.joint(guideId)

            if guideId != "chin":
                guidDef.name = naming.resolve("controlName", {"componentName": compName,
                                                              "side": compSide,
                                                              "id": guidDef.id,
                                                              "type": "control"})
                ctrl = rigLayer.createControl(name=guidDef.name,
                                              id=guideId,
                                              rotateOrder=guidDef.get("rotateOrder", 0),
                                              translate=guidDef.get("translate", (0, 0, 0)),
                                              rotate=guidDef.get("rotate", (0, 0, 0, 1)),
                                              parent=guidDef.parent,
                                              shape=guidDef.get("shape"),
                                              selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                              srts=[{"name": "_".join([guidDef.name, "srt"])}])
                _ctrls[guideId] = ctrl

                if not jnt:
                    continue

                const, constUtilities = api.buildConstraint(jnt,
                                                            drivers={"targets": ((ctrl.fullPathName(partialName=True,
                                                                                                    includeNamespace=False),
                                                                                  ctrl),)},
                                                            constraintType="point", maintainOffset=True)
                rigLayer.addExtraNodes(constUtilities)
                const, constUtilities = api.buildConstraint(jnt,
                                                            drivers={"targets": ((ctrl.fullPathName(partialName=True,
                                                                                                    includeNamespace=False),
                                                                                  ctrl),)},
                                                            constraintType="orient", maintainOffset=True)
                rigLayer.addExtraNodes(constUtilities)
                const, constUtilities = api.buildConstraint(jnt,
                                                            drivers={"targets": ((ctrl.fullPathName(partialName=True,
                                                                                                    includeNamespace=False),
                                                                                  ctrl),)},
                                                            constraintType="scale", maintainOffset=True)
                rigLayer.addExtraNodes(constUtilities)
            if guideId in ("topLip", "jaw"):
                jnt.attribute("worldMatrix")[0].connect(outputNode.offsetParentMatrix)
            else:
                jnt.attribute("matrix").connect(outputNode.offsetParentMatrix)

        rootCtrl = _ctrls["rotAll"]
        rootCtrl.setParent(rigLayer.rootTransform())
        _ctrls["topLip"].setParent(rootCtrl)
        _ctrls["jaw"].setParent(rootCtrl, useSrt=True)

        # bind the root input node
        rootInput = inputLayer.inputNode("root")
        zapi.buildConstraint(rootCtrl.srt(),
                             drivers={"targets": ((rootInput.name(includeNamespace=False), rootInput),)},
                             maintainOffset=True,
                             constraintType="matrix", trace=False)

    def setupSelectionSet(self, deformLayer, deformJoints):
        """Overridden to ignore the chin and root jnts.

        :param deformLayer: The deformLayer instance
        :type deformLayer: :class:`layers.HiveDeformLayer`
        :param deformJoints: The joint id to joint map.
        :type deformJoints: dict[str, :class:`hnodes.Joint`]
        """
        return [v for k, v in deformJoints.items() if k != "chin"]
