import os, sys
import shutil

from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging
from zoo.core import api
from zoo.core import packageresolver
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.pyqt import utils
from zoo.core import engine
from zoo.apps.chatgptui import constants, installdialog


logger = zlogging.getLogger(__name__)


class ChatGPT(palette.ToolDefinition):
    id = "zoo.chatgpt.ui"
    creator = "David Sparrow"
    tags = ["OpenAI", "AI", "Chat"]
    uiData = {"icon": "chatGPT_shlf",
              "tooltip": "Zoo Chat GPT: \nOpens the Zoo Chat GPT Window",
              "label": "Zoo Chat GPT",
              }

    def execute(self, *args, **kwargs):

        if sys.version_info[0] < 3:
            output.displayError("Chat GPT only supports Python3 (maya2022+)")
            return
        currentEngine = engine.currentEngine()
        try:
            import openai
        except ImportError:
            installed = self._installDependenciesDialog(currentEngine)
            if not installed:
                output.displayInfo("Operation Cancelled: OpenAI Python Library was not installed.")
            return

        from zoo.apps.chatgptui import chatgptwin, utils as chatGptutils
        # validate the api key and show the dialog if it's not valid, dialog handles validation from the user input
        chatGptutils.setApiKeyIfFound()
        if not chatGptutils.hasApiKey() or not chatGptutils.validateKey(openai.api_key):
            win = currentEngine.showDialog(chatgptwin.ApiKeyDialog, "zoo.chatgpt.apikey", show=True, modal=True)

            while win.msgClosed is False:
                utils.processUIEvents()
            if not win.result:
                return
            chatGptutils.setAPIkey(win.result)
        win = currentEngine.showDialog(chatgptwin.ChatGPTWindow, "zoo.chatgpt.ui", show=True)

        return win

    def restartMayaDialog(self, parent):
        message = constants.RESTART_HOST_MESSAGE.format(api.currentConfig().cacheFolderPath(),
                                                        "Maya")

        elements.MessageBox.showQuestion(title="Zoo Chat GPT Installed", message=message,
                                         buttonA="Close Window", buttonB=None, icon="Info", parent=parent)

    def _installDependenciesDialog(self, currentEngine):
        m = currentEngine.showDialog(installdialog.InstallDialog, "zoo.chatgpt.install", show=True, modal=True)
        while m.msgClosed is False:
            utils.processUIEvents()
        if not m.result:
            return False
        # Install -----
        output.displayInfo("Installing OpenAI Python Library, please wait...")
        cfg = api.currentConfig()
        pkg = cfg.resolver.packageByName("zoo_chatgpt")
        pkg.runInstall()
        if pkg.pipRequirements:
            self._installDependencies(cfg, pkg.pipRequirements)
        requirements = packageresolver.parseRequirementsFile(pkg.pipRequirementsPath)
        pkg.pipRequirements = requirements
        installed = self._installDependencies(cfg, requirements)
        if installed:
            self.restartMayaDialog(parent=currentEngine.host.qtMainWindow)
            output.displayInfo("OpenAI Python Library has been installed, Please restart Maya.")
            return True
        return False

    def _installDependencies(self, cfg, requirements):
        exe = engine.currentEngine().host.pythonExecutable
        if not os.path.exists(exe):
            output.displayError("Mayapy executable not found: {}".format(exe))
            return False
        packageresolver.pipInstallRequirements(cfg.sitePackagesPath(), exe,
                                               requirements, upgrade=False)
        return True


class UninstallChatGPT(palette.ToolDefinition):
    id = "zoo.uninstallChatGpt"
    creator = "David Sparrow"
    tags = ["OpenAI", "AI", "Chat"]
    uiData = {"icon": "chatGPTSimple",
              "tooltip": "Uninstalls Chat GPT and its dependencies",
              "label": "Uninstall Chat GPT",
              "multipleTools": False,
              }

    def execute(self, *args, **kwargs):
        cfg = api.currentConfig()
        cacheFolder = cfg.cacheFolderPath()
        if not os.path.exists(cacheFolder):
            output.displayInfo("Chat GPT is not installed, skipping uninstall.")
            return
        result = elements.MessageBox.showQuestion(parent=engine.currentEngine().host.qtMainWindow,
                                                  title="Uninstall Chat GPT", message="Are you sure you want to "
                                                                                      "uninstall Chat GPT and its "
                                                                                      "dependencies?",
                                                  buttonA="uninstall")
        if result != "A":
            return
        cfg = api.currentConfig()
        pkg = cfg.resolver.packageByName("zoo_chatgpt")
        pkg.runUninstall()
        logger.info("Deleting cache folder: {}".format(cacheFolder))
        try:
            shutil.rmtree(cacheFolder)
        except (PermissionError, OSError):
            output.displayWarning("Unable to delete cache folder due to permissions, "
                                  "please manually delete folder: {}. Close Maya before deleting.".format(cacheFolder))
            return
        output.displayInfo("Chat GPT has been uninstalled, Please restart.")
