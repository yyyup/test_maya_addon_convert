DID_NOT_INSTALL = "Zoo Tools Pro 2 has not been installed."
CLEANUP_PYC_CALLBACK = """
# %s
from maya import cmds
import os, time, threading
def cleanpycs():
    time.sleep(0.5)
    try:
        [os.remove(os.path.join(dir,f)) for (dir, subdirs, fs) in os.walk('{}') for f in fs if f.endswith(".pyc")]
    except:
        pass

t = threading.Thread(target=cleanpycs)
t.start()"""

MOD_TEXT = "+ zootoolspro 2.0 {}/zootoolspro/install/core/extensions/maya\n" \
           "ZOOTOOLS_PRO_ROOT := ../../\n" \
           "scripts: ./Scripts"
ZOO_MOD = "zootoolspro.mod"

MODULES_DIR = "modules"
SCRIPTS_DIR = "scripts"
PREFS_DIR = "~/zoo_preferences"
ZOO_FOLDER = "zootoolspro"

IMAGES = "res/images"


class Images(object):
    BANNER = "zoo_rhino.jpg"
    ALLOW_PLUGIN = "allowPlugin.png"
    GETTING_STARTED = "gettingStarted.jpg"
    GETTING_STARTED2 = "play_zoo.png"
    CHECKMARK = "checkMark_64"
    CLOSE = "close_64"
    LOGO_CIRCLE = "logoOnCircle.png"
    PLAY = "play_64.png"
