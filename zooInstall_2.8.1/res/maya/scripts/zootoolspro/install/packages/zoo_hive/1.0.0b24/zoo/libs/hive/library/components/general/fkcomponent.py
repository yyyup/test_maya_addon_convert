import math

from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoovendor.six.moves import range


class FkComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "fkchain"
    icon = "componentFK"
    documentation = "Forward Kinematics component"
    _bindJntIdPrefix = "fk"
    # primary translation axis which each new fk will generate along relative to the parent.
    _translationAxis = zapi.Vector(1, 0, 0)
    # default fk pivot rotation
    _rotationAxis = (0, 0, 0)
    # default rotation to apply to all created control shapes
    _shapeRotationAxis = (0, 0, (math.pi * 0.5))
    _firstIndexRotationOrder = zapi.kRotateOrder_XYZ

    @classmethod
    def fkGuideIdForNumber(cls, number):
        return cls._bindJntIdPrefix + str(number).zfill(2)

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

    def idMapping(self):
        guideLayerDef = self.definition.guideLayer
        count = guideLayerDef.guideSetting("jointCount").value
        deformIds = {}
        outputIds = {}
        rigLayerIds = {}
        inputIds = {}
        for i in range(count):
            index = str(i).zfill(2)
            guideId = "fk{}".format(index)
            bindId = self._bindJntIdPrefix + index
            deformIds[guideId] = bindId
            outputIds[guideId] = bindId
            rigLayerIds[guideId] = guideId
            inputIds[guideId] = ""

        return {api.constants.DEFORM_LAYER_TYPE: deformIds,
                api.constants.INPUT_LAYER_TYPE: inputIds,
                api.constants.OUTPUT_LAYER_TYPE: outputIds,
                api.constants.RIG_LAYER_TYPE: rigLayerIds}

    def spaceSwitchUIData(self):
        driven = []
        drivers = [api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "parent")),
                                           label="Parent Component",
                                           internal=True),
                   api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "inputLayer", "world")),
                                           label="World Space", internal=True)]

        guideLayerDef = self.definition.guideLayer

        for guide in guideLayerDef.iterGuides(includeRoot=False):
            driven.append(api.SpaceSwitchUIDriven(id_=api.pathAsDefExpression(("self", "rigLayer", guide.id)),
                                                  label=guide.name))
            drivers.append(api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", guide.id)),
                                                   label=guide.name))

        return {
            "driven": driven,
            "drivers": drivers
        }

    def updateGuideSettings(self, settings):
        originalGuideSettings = super(FkComponent, self).updateGuideSettings(settings)
        if "jointCount" in settings and self.hasGuide():
            # ensure the definition contains the latest scene state.
            # todo: starting to think we need to proxy the component class
            self.serializeFromScene(
                layerIds=api.constants.GUIDE_LAYER_TYPE)
            self.deleteGuide()
            self.rig.buildGuides([self])
        return originalGuideSettings

    def preSetupGuide(self):
        definition = self.definition
        guideLayerDef = definition.guideLayer
        count = guideLayerDef.guideSetting("jointCount").value
        guides = list(guideLayerDef.iterGuides())
        currentGuideCount = len(guides) - 1
        naming = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        # if the definition is the same as the required then just call the base
        # this will happen on a rebuild with a single guide count difference
        if currentGuideCount == count:
            return super(FkComponent, self).preSetupGuide()
        # case where the new count is less than the current, in this case we just
        # delete the definition for the guide from the end.
        elif count < currentGuideCount:
            idsToDelete = ["fk{}".format(str(i).zfill(2)) for i in range(count, len(guides) - 1)]
            guideLayerDef.deleteGuides(*idsToDelete)
            # delete any builtin space switches tied to the deleted guides
            spacesToDelete = []
            for space in definition.spaceSwitching:
                if any(i in space.driven for i in idsToDelete):
                    spacesToDelete.append(space.label)
            definition.removeSpacesByLabel(spacesToDelete)
            return super(FkComponent, self).preSetupGuide()

        root = guideLayerDef.guide("root")
        parent, parentDef = "root", root
        if currentGuideCount:
            parentDef = guides[-1]
            parent = parentDef.id
        if currentGuideCount == 1:
            guidId = "fk01"
            name = naming.resolve("guideName", {"componentName": compName,
                                                "side": compSide,
                                                "id": guidId,
                                                "type": "guide"})
            parentWorld = zapi.Matrix(parentDef.worldMatrix)
            translate = self._translationAxis * parentWorld + zapi.Vector(parentDef.translate)
            worldMtx = zapi.TransformationMatrix(parentWorld)
            worldMtx.setTranslation(translate, zapi.kWorldSpace)
            localMat = zapi.TransformationMatrix()
            localMat.setTranslation(self._translationAxis, zapi.kWorldSpace)
            newGuide = self._createFKGuide(guideLayerDef, name, guidId, parent, worldMtx.asMatrix(),
                                           localMat.asMatrix(), self._firstIndexRotationOrder)
            currentGuideCount += 1
            parent = newGuide.id
            parentDef = newGuide

        for x in range(currentGuideCount, count):
            rotationOrder = self._firstIndexRotationOrder if x == 0 else zapi.kRotateOrder_XYZ
            index = str(x).zfill(2)
            guidId = "".join(("fk", index))
            name = naming.resolve("guideName", {"componentName": compName,
                                                "side": compSide,
                                                "id": guidId,
                                                "type": "guide"})
            matrix = zapi.TransformationMatrix()
            worldMtx = zapi.TransformationMatrix()

            try:
                # create an offset from the parent node to the current. with guides we can just multiple the
                # local matrix by the worldMatrix
                parentWorld = zapi.Matrix(parentDef.worldMatrix)
                parentLocal = zapi.Matrix(parentDef.matrix)
                transform = zapi.TransformationMatrix(parentLocal * parentWorld)
                worldMtx.setTranslation(transform.translation(zapi.kWorldSpace), zapi.kWorldSpace)
                worldMtx.setRotation(zapi.TransformationMatrix(parentWorld).rotation(zapi.kWorldSpace))
                worldMtx.setScale(parentDef.scale, zapi.kWorldSpace)
                matrix.setTranslation(zapi.TransformationMatrix(parentLocal).translation(zapi.kObjectSpace),
                                      zapi.kObjectSpace)
            except (AttributeError, KeyError) as er:
                worldMtx.setTranslation(self._translationAxis * x,
                                        zapi.kWorldSpace)
                worldMtx.setRotation(zapi.EulerRotation(*self._rotationAxis))
                matrix.setTranslation(self._translationAxis, zapi.kObjectSpace)

            newGuide = self._createFKGuide(guideLayerDef, name, guidId, parent, worldMtx.asMatrix(),
                                           matrix.asMatrix(), rotationOrder)
            parent = newGuide.id
            parentDef = newGuide

        return super(FkComponent, self).preSetupGuide()

    def _createFKGuide(self, guideLayer, name, guideId, parent, worldMatrix, localMatrix, rotationOrder):
        shapeMatrix = zapi.TransformationMatrix(worldMatrix)
        shapeMatrix.rotateBy(zapi.EulerRotation(*self._shapeRotationAxis), zapi.kTransformSpace)

        newGuide = guideLayer.createGuide(name=name,
                                          shape="circle",
                                          id=guideId,
                                          parent=parent,
                                          color=(0.0, 0.5, 0.5),
                                          rotationOrder=rotationOrder,
                                          matrix=list(localMatrix),
                                          pivotShape="sphere_arrow",
                                          # cast to list because we don't auto do this in the definition just yet
                                          worldMatrix=list(worldMatrix),
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                          shapeTransform=dict(worldMatrix=list(shapeMatrix.asMatrix())),
                                          srts=[{"name": "_".join((guideId, "piv", "srt"))}]
                                          )

        return newGuide

    def postSetupGuide(self):
        super(FkComponent, self).postSetupGuide()
        guideLayer = self.guideLayer()
        definition = self.definition

        for guide in guideLayer.iterGuides(includeRoot=False):
            hasSpace = guide.attribute("hasSpaceSwitch")
            guideId = guide.id()
            spaceName = "_".join((guideId, "space"))
            if hasSpace is None:
                guide.addAttribute(name="hasSpaceSwitch",
                                   Type=zapi.attrtypes.kMFnNumericBoolean,
                                   default=True,
                                   value=True,
                                   channelBox=True,
                                   keyable=False)
            else:
                hasSpace = hasSpace.value()
                if not hasSpace:
                    continue

            definition.createSpaceSwitch(label=spaceName,
                                         drivenId=api.pathAsDefExpression(("self", "rigLayer", guideId)),
                                         constraintType="orient",
                                         controlPanelFilter={"default": "parent",
                                                             "group": {
                                                                 "name": "_",
                                                                 "label": "Space"
                                                             },
                                                             },
                                         permissions={"allowRename": False, "value": True},
                                         drivers=[{"label": "parent",
                                                   "driver": api.constants.ATTR_EXPR_INHERIT_TOKEN,
                                                   "permissions": {"allowDriverChange": False,
                                                                   "allowRename": False}},
                                                  {"label": "world",
                                                   "driver": api.pathAsDefExpression(
                                                       ("self", "inputLayer", "world")),
                                                   "permissions": {"allowDriverChange": False,
                                                                   "allowRename": False}}])

    def setupInputs(self):
        definition = self.definition
        guideLayerDef = definition.guideLayer
        if not guideLayerDef.hasGuides():
            super(FkComponent, self).setupInputs()
            return

        fkDef = guideLayerDef.guide("fk00")
        super(FkComponent, self).setupInputs()
        layer = self.inputLayer()
        if layer:
            inputNode = layer.inputNode("parent")
            tMatrix = fkDef.transformationMatrix(scale=False)
            # We don't propagate scale from the guide
            inputNode.setWorldMatrix(tMatrix.asMatrix())

    def setupDeformLayer(self, parentJoint=None):
        # build skin joints if any
        definition = self.definition
        deformLayerDef = definition.deformLayer
        deformLayerDef.dag = []
        jointMapping = self.idMapping()[api.constants.DEFORM_LAYER_TYPE]
        for guide in definition.guideLayer.iterGuides(includeRoot=False):
            jntId = jointMapping[guide.id]
            parentId = jointMapping.get(guide.parent, None)
            deformLayerDef.createJoint(name=guide.name,
                                       id=jntId,
                                       rotateOrder=guide.get("rotateOrder", 0),
                                       translate=guide.get("translate", (0, 0, 0)),
                                       rotate=guide.get("rotate", (0, 0, 0, 1)),
                                       parent=parentId)
        super(FkComponent, self).setupDeformLayer(parentJoint)

    def setupOutputs(self, parentNode):
        definition = self.definition
        outputLayerDef = definition.outputLayer
        # delete any outputs which no longer have matching guides
        joints = {i["id"]: i for i in definition.deformLayer.iterDeformJoints()}
        currentOutputs = {i["id"]: i for i in outputLayerDef.iterOutputs()}
        for outId, out in currentOutputs.items():  # type: str, api.OutputDefinition
            if outId in joints:
                continue
            outParent = out.parent
            if outParent:
                currentOutputs[out.parent].deleteChild(outId)
        naming = self.namingConfiguration()
        # for each guide we create an output
        for index, jntDef in enumerate(definition.deformLayer.iterDeformJoints()):
            outputLayerDef.createOutput(name=naming.resolve("outputName", {"componentName": self.name(),
                                                                           "side": self.side(),
                                                                           "id": jntDef.id,
                                                                           "type": "output"}),
                                        id=jntDef.id,
                                        parent=jntDef.parent,
                                        rotateOrder=jntDef.rotateOrder)
        super(FkComponent, self).setupOutputs(parentNode)
        self._connectOutputs()

    def _connectOutputs(self):
        # connect the outputs to the deform layer
        layer = self.outputLayer()
        joints = {jnt.id(): jnt for jnt in self.deformLayer().joints()}
        for index, output in enumerate(layer.outputs()):
            driverJoint = joints.get(output.id())

            if index == 0:
                const, constUtilities = api.buildConstraint(output,
                                                            drivers={
                                                                "targets": ((driverJoint.fullPathName(partialName=True,
                                                                                                      includeNamespace=False),
                                                                             driverJoint),)},
                                                            constraintType="matrix",
                                                            maintainOffset=False)
                layer.addExtraNodes(constUtilities)
            else:
                driverJoint.attribute("matrix").connect(output.offsetParentMatrix)
                output.resetTransform()

    def preSetupRig(self, parentNode):
        spaceSwitches = {i.label: i for i in self.definition.spaceSwitching}
        for guide in self.definition.guideLayer.iterGuides(includeRoot=False):
            hasSpace = guide.attribute("hasSpaceSwitch")
            if not hasSpace:
                continue
            spaceSwitch = spaceSwitches.get("_".join((guide.id, "space")))
            if not spaceSwitch:
                continue
            spaceSwitch.active = hasSpace.value
        super(FkComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        definition = self.definition
        naming = self.namingConfiguration()
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.name(), self.side()
        controls = {}  # guideId: [node, parentId]
        # note controls default parent is the root transform, the appropriate parent will be set after
        # this is because iterGuides is in creation order which may not be the real order meaning the parent
        # may not be created yet.
        for index, guidDef in enumerate(definition.guideLayer.iterGuides(includeRoot=False)):
            ctrlName = naming.resolve("controlName", {"componentName": compName,
                                                      "side": compSide,
                                                      "id": guidDef.id,
                                                      "type": "control"})
            ctrl = rigLayer.createControl(
                name=ctrlName,
                id=guidDef.id,
                translate=guidDef.translate,
                rotate=guidDef.rotate,
                shape=guidDef.shape,
                rotateOrder=guidDef.rotateOrder,
                selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                srts=[{"id": guidDef.id, "name": "_".join([ctrlName, "srt"])}]
            )

            controls[guidDef.id] = (ctrl, guidDef.parent)
        # Handle reparenting all controls into correct hierarchy
        for ctrlId, (childCtrl, parentId) in controls.items():
            parent = controls.get(parentId)
            if not parent:
                parent = rigLayerRoot
            else:
                parent = parent[0]
            childCtrl.setParent(parent, maintainOffset=True)

    def postSetupRig(self, parentNode):
        deformLayer = self.deformLayer()
        inputLayer = self.inputLayer()
        rigLayer = self.rigLayer()
        extras = []
        joints = {i.id(): i for i in deformLayer.iterJoints()}
        rootInputNode = inputLayer.inputNode("parent")
        jointMapping = self.idMapping()[api.constants.DEFORM_LAYER_TYPE]
        for ctrl in rigLayer.iterControls():
            ctrlId = ctrl.id()

            jnt = joints.get(jointMapping[ctrlId])
            # drive the joint by the control
            pointConstraint, pointUtilities = api.buildConstraint(jnt,
                                                                  drivers={"targets": ((ctrlId, ctrl),)},
                                                                  constraintType="point", maintainOffset=True
                                                                  )
            parentConstraint, parentUtilities = api.buildConstraint(jnt,
                                                                    drivers={"targets": ((ctrlId, ctrl),)},
                                                                    constraintType="orient", maintainOffset=True
                                                                    )
            scaleConstraint, scaleUtilities = api.buildConstraint(jnt,
                                                                  drivers={"targets": ((ctrlId, ctrl),)},
                                                                  constraintType="scale", maintainOffset=True
                                                                  )
            if jnt.parent() == parentNode:
                const, constUtilities = zapi.buildConstraint(ctrl.srt(),
                                                             drivers={"targets": ((ctrlId, rootInputNode),)},
                                                             constraintType="matrix",
                                                             maintainOffset=True)
                extras += constUtilities
            extras += parentUtilities
            extras += scaleUtilities
            extras += pointUtilities
        rigLayer.addExtraNodes(extras)
        super(FkComponent, self).postSetupRig(parentNode)
