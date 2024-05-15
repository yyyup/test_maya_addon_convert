import sys
current_version = int("{0}{1}".format(sys.version_info[0], sys.version_info[1]))
if current_version == 27:
    from .__hybrid__.window27 import *
if current_version == 37:
    from .__hybrid__.window37 import *
if current_version == 39:
    from .__hybrid__.window39 import *
if current_version == 310:
    from .__hybrid__.window310 import *
if current_version == 311:
    from .__hybrid__.window311 import *

