
from zoo.libs.hive import api
from zoo.libs.maya.utils import mayatestutils
from maya.api import OpenMaya as om2


class TestFkComponent(mayatestutils.BaseMayaTest):
    """Test a basic fk component build so we can test all other query methods
    """
    keepPluginsLoaded = True
    newSceneAfterTest=True
    @classmethod
    def setUpClass(cls):
        super(TestFkComponent, cls).setUpClass()

    def setUp(self):
        cfg = api.Configuration()
        cfg.blackBox = True
        self.rig = api.Rig(cfg)
        self.rig.startSession("TestRig")
        self.component = self.rig.createComponent("fkchain", "testfk", "M")

    def test_buildGuide(self):
        self.rig.buildGuides([self.component])
        self.assertTrue(self.component.buildGuide())
        self.assertTrue(self.component.hasGuide())
        self.assertFalse(self.component.hasRig())
        self.assertIsInstance(self.component.guideLayer(), api.HiveGuideLayer)
        self.assertIsInstance(self.component.container(), api.ContainerAsset)
        self.assertEqual(self.component.container().blackBox, self.rig.configuration.blackBox)

    def test_buildRigWithGuide(self):
        self.rig.buildGuides([self.component])
        self.assertFalse(self.component.hasRig())
        self.rig.buildRigs([self.component])
        self.assertIsInstance(self.component.rigLayer(), api.HiveRigLayer)
        self.assertIsInstance(self.component.inputLayer(), api.HiveInputLayer)
        self.assertIsInstance(self.component.outputLayer(), api.HiveOutputLayer)
        self.assertIsInstance(self.component.deformLayer(), api.HiveDeformLayer)
        self.assertTrue(self.component.hasRig())

    def test_parent(self):
        newComponent = self.rig.createComponent("fkchain", "testcomp", "M")
        self.rig.buildGuides([self.component, newComponent])
        self.assertIsNone(self.component.parent())
        self.component.setParent(newComponent)
        self.assertIsNotNone(self.component.parent())
        self.assertIsInstance(self.component.parent(), api.Component)

    def test_deserialize(self):
        self.rig.buildGuides([self.component])
        deff = self.component.serializeFromScene()
        self.rig.deleteComponent(self.component.name(), self.component.side())
        self.rig.createComponent(definition=deff)

    def test_deleteGuide(self):
        self.rig.buildGuides([self.component])
        self.assertTrue(self.component.deleteGuide())
        self.assertIsNone(self.component.guideLayer())

    def test_deleteRig(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.assertTrue(self.rig.deleteRigs())
        for i in (self.component.rigLayer(),):
            self.assertIsNone(i)

    def test_delete(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.deleteComponent(self.component.name(), self.component.side())
        self.component.rootTransform()
        self.assertFalse(self.component.exists())

    def test_polish(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.polish()
        self.assertIsNone(self.component.guideLayer())
        self.assertIsNone(self.component.container())

    def test_polishWithContainers(self):
        self.rig.configuration.useContainers = True
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.polish()
        self.assertIsNone(self.component.guideLayer())
        self.assertIsNotNone(self.component.container())
        self.assertTrue(self.component.container().blackBox, self.rig.configuration.blackBox)


class TestComponentAll(mayatestutils.BaseMayaTest):
    newSceneAfterTest=True
    keepPluginsLoaded = True
    @classmethod
    def setUpClass(cls):
        super(TestComponentAll, cls).setUpClass()
        super(TestComponentAll, cls).setUpClass()

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("hiveTest")

    def test_buildAllComponentGuides(self):
        comps = self.rig.configuration.componentRegistry().components
        for n, data in comps.items():
            self.rig.createComponent(n, n, "M")
        self.rig.buildGuides()
        for comp in self.rig.components():
            self.assertIsInstance(comp.meta, api.HiveComponent)
            self.assertIsInstance(comp.guideLayer(), api.HiveGuideLayer)

    def test_buildAllComponentRigs(self):
        comps = self.rig.configuration.componentRegistry().components
        for n, data in comps.items():
            self.rig.createComponent(n,n, "M")
        self.rig.buildGuides()
        self.rig.buildDeform()
        self.rig.buildRigs()
        for comp in self.rig.components():
            rigLayer = comp.rigLayer()
            self.assertIsInstance(rigLayer, api.HiveRigLayer)
            self.assertIsInstance(comp.deformLayer(), api.HiveDeformLayer)
            self.assertIsInstance(comp.inputLayer(), api.HiveInputLayer)
            self.assertIsInstance(comp.outputLayer(), api.HiveOutputLayer)
            # now test to make sure that if we have a controlPanel
            # that all anim attributes from the panel is published on the container
            # or as a proxy on each control
            animsettings = comp.definition.get("settings", {}).get("anim")
            if not animsettings:
                continue
            controlPanel = rigLayer.settingNode(api.constants.CONTROL_PANEL_TYPE)
            container = comp.container()
            publishNames = [i.partialName(includeNonMandatoryIndices=True, useLongNames=False,
                                          includeInstancedIndices=True) for i in container.publishedAttributes()]

            if controlPanel is not None:
                controls = rigLayer.iterControls()
                for animSetting in animsettings:
                    self.assertIsInstance(controlPanel.attribute(animSetting["name"]),
                                          om2.MPlug)
                    if self.rig.configuration.useProxyAttributes:
                        for ctrl in controls:
                            self.assertIsInstance(ctrl.attribute(animSetting["name"]),
                                                  om2.MPlug)
                    elif not self.rig.configuration.useProxyAttributes and self.rig.configuration.useContainers:
                        self.assertTrue(animSetting["name"] in publishNames)
