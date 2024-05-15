import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 27:
    from .__hybrid__.main_window27 import *
if current_version == 37:
    from .__hybrid__.main_window37 import *
if current_version == 39:
    from .__hybrid__.main_window39 import *
if current_version == 310:
    from .__hybrid__.main_window310 import *
if current_version == 311:
    from .__hybrid__.main_window311 import *

