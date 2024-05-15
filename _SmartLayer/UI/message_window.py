import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 27:
    from .__hybrid__.message_window27 import *
if current_version == 37:
    from .__hybrid__.message_window37 import *
if current_version == 39:
    from .__hybrid__.message_window39 import *
if current_version == 310:
    from .__hybrid__.message_window310 import *
if current_version == 311:
    from .__hybrid__.message_window311 import *

