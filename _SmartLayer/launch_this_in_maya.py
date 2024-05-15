import sys

python_version = sys.version[0]
packages = ['_SmartLayer']

if python_version == "3":
    print("launching {} in python3..".format(packages))
    from importlib import reload
    modules_to_reload = []
    for module in sys.modules.keys():
        for pkg_name in packages:
            if module.startswith(pkg_name):
                modules_to_reload.append(module)

    modules_to_reload.reverse()
    for module in modules_to_reload:
        print("Reloading {}".format(module))
        reload(sys.modules[module])

for i in list(sys.modules.keys()):
    for package in packages:
        if i.startswith(package):
            del(sys.modules[i])

import _SmartLayer.main
_SmartLayer.main.main()