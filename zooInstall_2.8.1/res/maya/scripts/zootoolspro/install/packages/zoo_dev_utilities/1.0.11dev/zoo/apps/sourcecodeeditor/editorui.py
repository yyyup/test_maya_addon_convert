"""
.. todo::

    file save/open.
    autosave tabs to linked files or local zoo cache folder.
    feed maya stdout to output widget
    tab icons
    code completion
"""
import logging
import sys
import traceback

from zoovendor import six

from zoo.libs.pyqt.extended.sourcecodeeditor import pythoneditor
from zoo.libs.pyqt.widgets import logoutput
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore


class SourceCodeUI(elements.ZooWindow):
    helpUrl = "https://www.create3dcharacters.com/zoo2"
    windowSettingsPath = "zoo/sourcecodeui"
    def __init__(self, parent=None, resizable=True, width=960, height=540, modal=False,
                 alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False, saveWindowPref=False,
                 titleBar=None, overlay=True, minimizeEnabled=True, initPos=None):
        super(SourceCodeUI, self).__init__("SourceCodeEditor", "Source Code Editor", parent, resizable, width, height,
                                           modal,
                                           alwaysShowAllTitle,
                                           minButton, maxButton,
                                           onTop, saveWindowPref, titleBar, overlay, minimizeEnabled, initPos)
        layout = elements.vBoxLayout()
        self.setMainLayout(layout)
        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._outputWidget = logoutput.OutputLogDialog(title="Output", parent=self)

        self._stdoutRedirect = StdoutFeed(parent=self)
        self._stdinRedirect = StdinFeed(self._requestUserInput, parent=self)
        self._stderrRedirect = StderrorFeed(parent=self)

        self._inputWidget = pythoneditor.TabbedEditor(name="scriptEditorInput",
                                                      parent=self)
        self._logout = logoutput.OutputLogDialog("History", parent=parent)
        self._inputWidget.addNewEditor(name="python", language="python")
        self._splitter.addWidget(self._outputWidget)
        self._splitter.addWidget(self._inputWidget)
        self._splitter.addWidget(self._outputWidget)
        self._splitter.addWidget(self._inputWidget)
        layout.addWidget(self._splitter)

        self._stdoutRedirect.output.connect(self.writeStdOutToOutput)
        self._stderrRedirect.error.connect(self.writeStdErrToOutput)
        self._inputWidget.executed.connect(self.execute)
        self._locals = {"scriptEditor": self,
                        "__name__": "__main__",
                        "__doc__": None,
                        "__package__": None}

    @property
    def outputWidget(self):
        return self._outputWidget

    @property
    def inputWidget(self):
        return self._inputWidget

    def _requestUserInput(self):
        print("input")

    def writeStdOutToOutput(self, msg):

        self.outputWidget.factoryLog(msg, logging.INFO)

    def writeStdErrToOutput(self, msg):
        self.outputWidget.factoryLog(msg, logging.ERROR)

    def execute(self, script):

        script = script.replace(u"\u2029", "\n")
        script = six.ensure_str(script).strip()
        if not script:
            return

        with self._stdoutRedirect as stdOutFeed:
            with self._stdinRedirect:

                stdOutFeed.write(script)  # echo the script
                evalCode = True
                try:
                    outputCode = compile(script, "<string>", "eval")
                except SyntaxError:
                    evalCode = False
                    try:
                        outputCode = compile(script, "string", "exec")
                    except SyntaxError:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)
                        return

                # ok we've compiled the code now exec
                if evalCode:
                    try:
                        results = eval(outputCode, self._locals, self._locals)
                        if results is not None:
                            stdOutFeed.write(str(results))
                    except Exception:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)
                else:
                    try:
                        exec(outputCode, self._locals, self._locals)
                    except Exception:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)


class StdoutFeed(QtCore.QObject):
    output = QtCore.Signal(str)

    def __init__(self, writeToStdout=True, parent=None):
        super(StdoutFeed, self).__init__(parent=parent)

        # temporarily assigned during enter
        self.stdHandle = None
        self.writeToStdout = writeToStdout

    def __enter__(self):
        self.stdHandle = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.stdHandle

    def write(self, msg):
        msg = six.ensure_str(msg)
        self.output.emit(msg)
        QtCore.QCoreApplication.processEvents()
        if self.writeToStdout and self.stdHandle:
            self.stdHandle.write(msg)


class StdinFeed(QtCore.QObject):
    inputRequested = QtCore.Signal(str)

    def __init__(self, readLineCallback, parent=None):
        super(StdinFeed, self).__init__(parent=parent)

        self.stdHandle = None
        self.readLineCallback = readLineCallback

    def __enter__(self):
        self.stdHandle = sys.stdin
        sys.stdin = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdin = self.stdHandle

    def readline(self):
        self.readLineCallback()


class StderrorFeed(QtCore.QObject):
    error = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(StderrorFeed, self).__init__(parent=parent)

        # temporarily assigned during enter
        self.stdHandle = None

    def write(self, msg):
        self.error.emit(msg)
        QtCore.QCoreApplication.processEvents()
        sys.stderr.write(msg)
