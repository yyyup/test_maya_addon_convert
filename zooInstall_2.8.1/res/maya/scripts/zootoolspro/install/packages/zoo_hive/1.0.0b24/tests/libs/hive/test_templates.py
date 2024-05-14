from zoo.libs.hive import api
from zoo.libs.maya.utils import mayatestutils


class TestRoboBall(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("robo_ball")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestNatalie(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("natalie")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestRobot(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("robot")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestBiped(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("biped_lightweight")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestMannequin(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("zoo_mannequin")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestArm(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestArmThreeFinger(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_three_finger")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestArmThreeFingerNmc(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_three_finger_nmc")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())


class TestArmNmc(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_nmc")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        self.assertTrue(r.buildGuides())
        self.assertTrue(r.buildDeform())
        self.assertTrue(r.buildRigs())
        self.assertTrue(r.polish())
