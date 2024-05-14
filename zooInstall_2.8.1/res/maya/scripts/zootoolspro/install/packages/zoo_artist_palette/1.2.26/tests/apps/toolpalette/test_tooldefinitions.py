from zoo.libs.utils import unittestBase
from zoo.apps.toolpalette import run
from zoo.apps.toolpalette import default_definitions
from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging

try:
    from unittest import mock
except ImportError:
    from zoovendor import mock


class TestDefaultDefinitions(unittestBase.BaseUnitest):

    def setUp(self):
        self.instance = run.currentInstance()
        if self.instance is None:
            self.instance = run.load()

    def test_loadsDefaultDefinitions(self):
        definitions = self.instance.typeRegistry.getPlugin("definition")  # type: palette.DefinitionType
        plugins = list(definitions.plugins())
        self.assertTrue(default_definitions.ToggleZooLogging.id in plugins)
        self.assertTrue(default_definitions.HelpIconShelf.id in plugins)
        self.assertTrue(default_definitions.ResetAllWindowPosition.id in plugins)

    def test_helpCallsWebBrowser(self):

        for variant in default_definitions.HelpIconShelf._ADDRESSES:
            with mock.patch("webbrowser.open") as mockwbopen:
                self.instance.executePluginById(default_definitions.HelpIconShelf.id, variant=variant)
                self.assertTrue(mockwbopen.called)

    def test_loggingTogglesDebugMode(self):
        """Tests the toggling of debug logging through the definition works.
        """
        zlogging.setGlobalDebug(False)  # actual core test is in zooTools main repo
        self.instance.executePluginById(default_definitions.ToggleZooLogging.id)
        self.assertTrue(zlogging.isGlobalDebug())
        self.instance.executePluginById(default_definitions.ToggleZooLogging.id)
        self.assertFalse(zlogging.isGlobalDebug())
