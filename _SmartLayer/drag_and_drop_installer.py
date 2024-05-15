import os
import sys
import shutil
import maya.cmds as cmds


package_name = "_SmartLayer"
icon_name = "SmartLayerIcon.png"
shelf_button_name = "SmartLayer"


def onMayaDroppedPythonFile(*args, **kwargs):
    
    installer_file = __file__
    source_path = os.path.dirname(installer_file)
    
    install_package(source_path, package_name, installer_file)
    create_shelf_button(source_path, icon_name, package_name)


def install_package(source_path, package_name, installer_file):
    """ 
    copying files from folder with package to 'C:/Users/<USER>/Documents/maya/scripts/<package_name>, ignoring the installer file'.
    """
    maya_app_dir = cmds.internalVar(userAppDir=1)
    destination_base_path = os.path.normpath(os.path.join(maya_app_dir, "scripts", package_name))
    installer_file_name = os.path.basename(installer_file)

    for root, dirs, files in os.walk(source_path):
        relative_path = os.path.relpath(root, source_path)
        destination_path = os.path.join(destination_base_path, relative_path)
        
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        for file in files:
            if file == installer_file_name:
                continue
            source_file = os.path.join(root, file)
            destination_file = os.path.join(destination_path, file)

            shutil.copy(source_file, destination_file)
            print("File copied: ", source_file, " to ", destination_file)


def create_shelf_button(source_path, icon_name, package_name):
    """ 
    copying the icon to the icons path, adding shelf item'
    """

    icons_path = os.path.join(cmds.internalVar(userPrefDir=True), 'icons')
    try:
        shutil.copy(os.path.join(source_path, icon_name), os.path.join(icons_path, icon_name))
    except:
        pass
    current_shelf_tab = cmds.tabLayout('ShelfLayout', query=True, selectTab=True)
    
    shelf_command = """import sys

python_version = sys.version[0]
packages = ['{}']

if python_version == "3":
    from importlib import reload
    modules_to_reload = []
    for module in sys.modules.keys():
        for pkg_name in packages:
            if module.startswith(pkg_name):
                modules_to_reload.append(module)

    modules_to_reload.reverse()
    for module in modules_to_reload:
        reload(sys.modules[module])

for i in list(sys.modules.keys()):
    for package in packages:
        if i.startswith(package):
            del(sys.modules[i])

import {}.main
{}.main.main()""".format(package_name, package_name, package_name)

    shelf_icon = os.path.join(icons_path, icon_name)

    if not os.path.isfile(shelf_icon):
        print("Warning: Icon file not found at:", shelf_icon)
        shelf_icon = "commandButton.png"

    cmds.shelfButton(
        label = shelf_button_name,
        command = shelf_command,
        image = shelf_icon,
        parent = current_shelf_tab,
        annotation = '{} command'.format(shelf_button_name)
    )
    print("Shelf button '{}' has been created on '{}' shelf.".format(shelf_button_name, current_shelf_tab))

