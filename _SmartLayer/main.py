""" 

Copyright © 2024 Viachaslau Baravik. All rights reserved.

This software and its content (including but not limited to code, documentation, design, and related materials) are the exclusive intellectual property of Viachaslau Baravik.
Unauthorized copying, modification, distribution, dissemination, or use of this software, either in whole or in part, is strictly prohibited without the express written permission of the copyright holder.

By using this software, you acknowledge and agree that it contains confidential and proprietary information that is protected by applicable intellectual property and other laws.
You agree to abide by and maintain the confidentiality of this software and to prevent any unauthorized copying of the material. Violation of these terms may lead to legal action.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHOR OR COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
IN THE SOFTWARE.

"""
import os

import maya.cmds as cmds
maya_version = cmds.about(version=True)
try:
    if int(maya_version) >= 2025:
        from PySide6 import QtCore
    else:
        from PySide2 import QtCore
except ValueError:
    from PySide2 import QtCore

from _SmartLayer.UI.main_window import SmartLayerWindow
from  _SmartLayer.UI.UI_utilities import UI_Utilities

def create_gui():
    if cmds.window("SmartLayerWindowID", exists=1):
        cmds.deleteUI("SmartLayerWindowID")
    if cmds.windowPref("SmartLayerWindowID", exists=1):
        cmds.windowPref("SmartLayerWindowID", remove=1)

    global SmartLayerDialog
    SmartLayerDialog = SmartLayerWindow(scale=UI_Utilities.find_ui_scale(), root_path=os.path.dirname(__file__))
    SmartLayerDialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    SmartLayerDialog.closeEvent = lambda event: SmartLayerDialog.deleteLater()

    # standart window
    SmartLayerDialog.show()
    
    # or dockable widget
    # SmartLayerDialog.show(dockable = True, area='right', allowedArea='right', floating=True)
    # cmds.workspaceControl('MyCustomWidgetUIIdWorkspaceControl',
    #                         label = 'Smart Layer, Beta',
    #                         edit = 1,
    #                         tabToControl = ['AttributeEditor', -1],
    #                         widthProperty = 'fixed',
    #                         initialWidth = 400)

def main():
    create_gui()
