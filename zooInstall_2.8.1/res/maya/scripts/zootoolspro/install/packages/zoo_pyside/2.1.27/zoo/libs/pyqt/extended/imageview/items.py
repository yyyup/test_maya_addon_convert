import os
import random
import time

from zoo.libs import iconlib
from zoo.libs.pyqt.uiconstants import QT_SUPPORTED_EXTENSIONS
from zoovendor.Qt import QtGui, QtCore, QtWidgets
from zoo.libs.pyqt import thread, utils
from zoo.core.util import zlogging


logger = zlogging.getLogger(__name__)


class ItemSignals(thread.WorkerSignals):
    updated = QtCore.Signal(object)


class ThreadedIcon(QtCore.QRunnable):
    def __init__(self, iconPath, width=512, height=512, *args, **kwargs):
        super(ThreadedIcon, self).__init__(*args, **kwargs)
        self.signals = ItemSignals()

        # # Add the callback to our kwargs
        kwargs['progress_callback'] = self.signals.progress
        self._path = iconPath
        self.width = width
        self.height = height
        self.placeHolderImage = QtGui.QImage(50, 50, QtGui.QImage.Format_ARGB32)
        self.placeHolderImage.fill(QtGui.qRgb(96, 96, 96))
        self._finished = False
        self._running = False

    def finished(self, state):
        self._finished = state
        self.signals.finished.emit()

    def isFinished(self):
        return self._finished

    def isRunning(self):
        return self._running

    @QtCore.Slot()
    def run(self):

        if not self._path or self._finished:
            return
        self._running = True
        self.signals.updated.emit(self.placeHolderImage)
        try:
            image = QtGui.QImage(self._path)
            # scale down when the image is higher than the requested size
            if image.width() > self.width or image.height() > self.height:
                image = image.scaled(QtCore.QSize(self.width, self.height), QtCore.Qt.KeepAspectRatio)
        except Exception as er:
            self.signals.error.emit((er,))
            self.finished(True)
            self._running = False
            return
        if image.isNull():
            message = "Unable to load image, possibly image format doesn't file extension: {}".format(self._path)
            self.signals.error.emit(message)
        else:
            self.signals.updated.emit(image)
        self.finished(True)
        self._running = False


class BaseItem(object):
    _emptyThumbnail = None  # type: QtGui.Qicon or None

    def __init__(self, name=None, description=None, iconPath=None, filePath="", toolTip="", thumbnail=""):
        """ The base Item for ThumbnailWidget

        Thumbnail can be relative

        :param name:
        :param description:
        :param iconPath:
        :param filePath:
        :param toolTip:
        :param thumbnail:
        """
        if BaseItem._emptyThumbnail is None:
            BaseItem._emptyThumbnail = iconlib.iconPath("emptyThumbnail")["sizes"][200]["path"]
        self.iconPath = iconPath or ""
        self.filePath = filePath
        self.fileName = ""
        self.ext = ""
        self.imageExt = "jpg"
        self._description = description or ""
        self.directory = ""
        self.metadata = {}
        self.user = ""
        self.toolTip = toolTip
        self.iconThread = None  # type: ThreadedIcon
        self._thumbnail = thumbnail
        self.setFilePath(filePath)
        self.name = name or self.fileName

    def fileNameExt(self):
        return self.fileName + "." + self.ext

    def setFilePath(self, path):
        """ Breaks the path into data that the class can use

        :param path:
        :return:
        """

        self.directory = os.path.dirname(path)
        self.filePath = path
        file = os.path.basename(path)
        fileSplit = file.split(".")
        self.fileName = fileSplit[0]
        self.ext = fileSplit[1]
        if self.ext in QT_SUPPORTED_EXTENSIONS:
            self.imageExt = self.ext

    def fullPath(self):
        return os.path.join(self.directory, self.fileNameExt())

    def thumbnailExists(self):
        return os.path.exists(self._thumbnail)

    @property
    def thumbnail(self):
        """ Returns the expected thumbnail. If it doesn't exist just use an empty one

        :return:
        """

        thumbnail = self.thumbnailLookPath()
        if thumbnail and os.path.exists(thumbnail):  # todo: could be slow if thumbnail is checked lots of times
            self._thumbnail = thumbnail
            return thumbnail
        return self._emptyThumbnail

    @thumbnail.setter
    def thumbnail(self, value):
        self._thumbnail = value
        if value is None:
            self.imageExt = self.imageExt
        else:
            self.imageExt = os.path.splitext(value)[-1][1:].lower()

    def thumbnailLookPath(self):
        """ The location to look for the thumbnail.
        Replace this thumbnail in the returned path to change its thumbnail

        :return:
        """
        if not self._thumbnail:
            return os.path.join(self.directory, self.fileName + "." + self.imageExt)

        return self._thumbnail

    def description(self):
        return self.metadata.get("description")

    def iconLoaded(self):
        return self.iconThread is not None and self.iconThread.isFinished()

    def tags(self):
        return self.metadata.get("tags", "")

    def websites(self):
        return self.metadata.get("websites", "")

    def creators(self):
        return self.metadata.get("creators", "")

    def hasTag(self, tag):
        for i in self.tags():
            if tag in i:
                return True
        return False

    def hasAnyTags(self, tags):
        for i in tags:
            if self.hasTag(i):
                return True
        return False

    def serialize(self):
        return {"metadata": {"time": "",
                             "version": "",
                             "user": "",
                             "name": self.name,
                             "application": {"name": "",
                                             "version": ""},
                             "description": "",
                             "tags": []},
                }


class TreeItem(QtGui.QStandardItem):
    backgroundColor = QtGui.QColor(70, 70, 80)
    backgroundColorSelected = QtGui.QColor(50, 180, 240)
    backgroundColorHover = QtGui.QColor(50, 180, 150)
    textColorSelected = QtGui.QColor(255, 255, 255)
    textColor = QtGui.QColor(255, 255, 255)
    textBGColor = QtGui.QColor(0, 0, 0)
    backgroundBrush = QtGui.QBrush(backgroundColor)
    backgroundColorSelectedBrush = QtGui.QBrush(backgroundColorSelected)
    backgroundColorHoverBrush = QtGui.QBrush(backgroundColorHover)
    borderColorSelected = QtGui.QColor(0, 0, 0)
    borderColorHover = QtGui.QColor(0, 0, 0)
    borderColor = QtGui.QColor(0, 0, 0)
    backgroundColorIcon = QtGui.QColor(50, 50, 50)
    _hash = 0

    def __init__(self, item, parent=None, themePref=None, squareIcon=False):
        """

        :param item:
        :type item:
        :param parent:
        :type parent:
        :param themePref:
        :type themePref: preferences.interface.preference_interface.ZooToolsPreference
        :param squareIcon:
        :type squareIcon:
        """
        super(TreeItem, self).__init__(parent)
        self._generateHash()

        self.currentTheme = ""
        self.padding = 0
        self.textHeight = 11
        self.borderWidth = 1
        self.textPaddingH = 7
        self.textPaddingV = 2

        self.showText = True
        self._item = item  # type: BaseItem
        self._pixmap = None
        self.iconSize = QtCore.QSize(256, 256)
        self._font = QtGui.QFont("Tahoma")
        self.aspectRatio = QtCore.Qt.KeepAspectRatioByExpanding

        self.themePref = themePref
        self.squareIcon = squareIcon

        self.setEditable(False)
        self.setBorderWidth(1)

        if themePref is not None:
            self.initColors()

    def _generateHash(self):
        """ Generates a hash number

        :return:
        """
        self._hash = int(time.time() * random.random())  # using id(self) crashes

    def initColors(self):
        self.updateTheme()

    def updateTheme(self, event=None):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """

        if event:
            self.backgroundColorSelected = QtGui.QColor(*event.themeDict.BROWSER_SELECTED_COLOR)
            self.backgroundColor = QtGui.QColor(*event.themeDict.BROWSER_BG_COLOR)
            self.backgroundColorIcon = QtGui.QColor(*event.themeDict.BROWSER_ICON_BG_COLOR)
            self.textColorSelected = QtGui.QColor(*event.themeDict.TBL_TREE_ACT_TEXT_COLOR)
            self.borderColorSelected = QtGui.QColor(*event.themeDict.BROWSER_SELECTED_COLOR)
            self.borderColorHover = QtGui.QColor(*event.themeDict.BROWSER_BORDER_HOVER_COLOR)
            self.textColor = QtGui.QColor(*event.themeDict.BROWSER_TEXT_COLOR)
            self.textBGColor = QtGui.QColor(*event.themeDict.BROWSER_TEXT_BG_COLOR)

        else:
            self.backgroundColorSelected = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_SELECTED_COLOR", self.currentTheme))
            self.backgroundColor = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_BG_COLOR", self.currentTheme))
            self.backgroundColorIcon = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_ICON_BG_COLOR", self.currentTheme))
            self.textColorSelected = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$TBL_TREE_ACT_TEXT_COLOR", self.currentTheme))
            self.borderColorSelected = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_SELECTED_COLOR", self.currentTheme))
            self.borderColorHover = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_BORDER_HOVER_COLOR", self.currentTheme))
            self.textColor = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_TEXT_COLOR", self.currentTheme))
            self.textBGColor = QtGui.QColor(
                *self.themePref.stylesheetSettingColour("$BROWSER_TEXT_BG_COLOR", self.currentTheme))

        self.currentTheme = self.themePref.currentTheme()

        self.textHeight = self.themePref.DEFAULT_FONTSIZE
        self.borderWidth = self.themePref.ONE_PIXEL
        self.textPaddingH = utils.dpiScale(7)
        self.textPaddingV = utils.dpiScale(1)

        self.backgroundBrush = QtGui.QBrush(self.backgroundColor)
        self.backgroundColorHover = self.backgroundColor
        self.backgroundColorHoverBrush = QtGui.QBrush(self.backgroundColorHover)
        self.backgroundColorSelectedBrush = QtGui.QBrush(self.backgroundColorSelected)
        self.borderColor = QtGui.QColor(self.backgroundColor)

    def item(self):
        return self._item

    def itemText(self):
        return self._item.name

    def applyFromImage(self, image):
        """

        :param image:
        :type image: :class:`QtGui.QImage`
        """
        pixmap = QtGui.QPixmap.fromImage(image)
        self._pixmap = pixmap

    def setIconPath(self, iconPath):
        self._item.iconPath = iconPath
        self._pixmap = QtGui.QPixmap(iconPath)

    def pixmap(self):
        """

        :return:
        :rtype: QtGui.QPixmap
        """
        if self._pixmap is None:
            return QtGui.QPixmap()
        if not self._pixmap.isNull():
            return self._pixmap
        elif not os.path.exists(self._item.iconPath):
            return QtGui.QPixmap()
        return self._pixmap

    def toolTip(self):
        return self._item.toolTip

    def isEditable(self, *args, **kwargs):
        return False

    def sizeHint(self):
        """ Size Hint

        :return:
        :rtype:
        """
        sizeHint = self.model().view.iconSize()
        pxSize = QtCore.QSize(1, 1)
        if self._pixmap:
            pxSize = self._pixmap.rect().size()

        size = min(sizeHint.height(), sizeHint.width())
        pxSize = QtCore.QSize(128, 128) if pxSize == QtCore.QSize(0, 0) else pxSize
        aspectRatio = 1
        if not self.squareIcon:
            aspectRatio = float(pxSize.width()) / float(pxSize.height())
        sizeHint.setWidth(size * aspectRatio)

        sizeHint.setHeight(size + 1)

        if self.showText:
            sizeHint.setHeight(sizeHint.height() + self.textHeight + self.textPaddingV * 2)

        return sizeHint

    def font(self, index):
        return self._font

    def textAlignment(self, index):
        return QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom

    def iconAlignment(self, index):
        return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

    def isSelected(self, option):
        return option.state & QtWidgets.QStyle.State_Selected == QtWidgets.QStyle.State_Selected

    def isMouseOver(self, option):
        """ Is mouse over

        :param option:
        :type option:
        :return:
        :rtype:
        """
        return option.state & QtWidgets.QStyle.State_MouseOver == QtWidgets.QStyle.State_MouseOver

    def setBorderWidth(self, width):
        self.borderWidth = utils.dpiScale(width)

    def paint(self, painter, option, index):
        """ Paint the item

        :param painter:
        :type painter:
        :param option:
        :type option:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        painter.save()
        self._paintBackground(painter, option, index)
        if self.showText:
            self._paintText(painter, option, index)
        if self._pixmap is not None:
            self._paintIcon(painter, option, index)
        painter.restore()

    def _paintIcon(self, painter, option, index):
        """ Paint the icon

        :param painter:
        :type painter:  QtGui.QPainter
        :param option:
        :type option:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        rect = self.iconRect(option)
        pixmap = self.pixmap()  # type: QtGui.QPixmap
        if pixmap.isNull():
            return
        pixmap = pixmap.scaled(
            rect.width() - self.borderWidth * 2,
            rect.height() - self.borderWidth * 2,
            self.aspectRatio,
            QtCore.Qt.SmoothTransformation,
        )

        pixmapRect = QtCore.QRect(rect)
        pixmapRect.setWidth(pixmap.width())
        pixmapRect.setHeight(pixmap.height())

        aspectRatio = float(max(1, pixmap.width())) / float(max(1, pixmap.height()))

        iconAlign = self.iconAlignment(None)

        if iconAlign & QtCore.Qt.AlignHCenter == QtCore.Qt.AlignHCenter:
            x = float(rect.width() - pixmap.width()) * 0.5
        elif iconAlign & QtCore.Qt.AlignLeft == QtCore.Qt.AlignLeft:
            x = 0
        else:  # todo: set the rest of the flags
            x = float(rect.width() - pixmap.width()) * 0.5
            logger.warning("Flags not set for TreeItem._paintIcon()! x-Value")

        if iconAlign & QtCore.Qt.AlignVCenter == QtCore.Qt.AlignVCenter:
            y = float(rect.height() - pixmap.height()) * 0.5
        else:  # todo: set the rest of the flags
            y = float(rect.height() - pixmap.height()) * 0.5
            logger.warning("Flags not set for TreeItem._paintIcon() y-Value!  ")

        x += self.borderWidth
        pixmapRect.translate(x, y)

        # Hacky fixes to visuals =[
        if self.squareIcon:
            clippedRect = QtCore.QRect(pixmapRect)
            clippedRect.setWidth(clippedRect.width() - 1)
            if clippedRect.height() <= clippedRect.width():  # Wide icons
                translate = (clippedRect.width() - clippedRect.height()) / 2
                clippedRect.setWidth(clippedRect.height() - 1)
                pixmapRect.translate(-translate, 0)
            else:  # Tall Icons
                translate = (clippedRect.height() - clippedRect.width()) / 2
                clippedRect.setHeight(clippedRect.width() + 2)
                clippedRect.setWidth(clippedRect.width())
                clippedRect.translate(0, translate)
            painter.setClipRect(clippedRect)
        else:
            if aspectRatio > 1:
                pixmapRect.setWidth(pixmapRect.width())
            elif aspectRatio >= 1:
                pixmapRect.setWidth(pixmapRect.width() - 1)
        painter.drawPixmap(pixmapRect, pixmap)

    def _paintText(self, painter, option, index):
        isSelected = self.isSelected(option)
        text = self._item.name
        color = self.textColorSelected if isSelected else self.textColor
        rect = QtCore.QRect(option.rect)
        width = rect.width() - self.textPaddingH * 2
        height = rect.height()
        padding = self.padding
        x, y = padding, padding
        rect.translate(x + self.textPaddingH, y + self.textPaddingV)
        rect.setWidth(width - padding)
        rect.setHeight(height - padding - self.textPaddingV)
        font = self.font(index)
        font.setPixelSize(self.textHeight)

        align = self.textAlignment(index)
        metrics = QtGui.QFontMetricsF(font)
        textWidth = metrics.width(text)
        # does the text fit? if not cut off the text
        if textWidth > rect.width() - padding:
            text = metrics.elidedText(text, QtCore.Qt.ElideRight, rect.width())

        if isSelected:
            textBgColor = self.borderColorSelected
        else:
            textBgColor = self.textBGColor

        textBg = QtCore.QRect(option.rect)

        textBg.setTop(textBg.top() + textBg.height() - (self.textHeight + self.textPaddingV * 2))
        textBg.translate(max(1, self.borderWidth * 0.5), max(1, self.borderWidth * 0.5) - 2)
        textBg.setWidth(textBg.width() - self.borderWidth * 2 - 1)
        textBg.setHeight(self.textHeight + self.textPaddingV)
        painter.setBrush(textBgColor)
        painter.setPen(textBgColor)
        painter.drawRect(textBg)

        pen = QtGui.QPen(color)
        painter.setPen(pen)
        painter.setFont(font)
        painter.drawText(rect, align, text)

    def _paintBackground(self, painter, option, index):

        isSelected = self.isSelected(option)
        isMouseOver = self.isMouseOver(option)
        brush = self.backgroundBrush
        borderColor = self.borderColor
        if isSelected:
            brush = self.backgroundColorSelectedBrush
            if isMouseOver:
                borderColor = self.borderColorHover
            else:
                borderColor = self.borderColorSelected
        elif isMouseOver:
            brush = self.backgroundColorHoverBrush
            borderColor = self.borderColorHover


        pen = QtGui.QPen(borderColor)
        pen.setJoinStyle(QtCore.Qt.MiterJoin)
        pen.setWidth(self.borderWidth)
        painter.setPen(pen)

        rect = QtCore.QRect(option.rect)
        rect.setWidth(rect.width() - self.borderWidth)
        rect.setHeight(rect.height() - self.borderWidth)
        rect.translate(self.borderWidth * 0.5, self.borderWidth * 0.5)

        painter.setBrush(brush)
        painter.drawRect(rect)

        # Icon background
        iconPen = QtGui.QPen(self.backgroundColorIcon)
        iconPen.setWidth(0)
        iconRect = QtCore.QRect(rect)
        painter.setBrush(QtGui.QBrush(self.backgroundColorIcon))
        iconRect.setHeight(iconRect.height() - (self.textHeight + self.textPaddingV * 2))
        iconRect.translate(max(1, self.borderWidth * 0.5), max(1, self.borderWidth * 0.5))
        iconRect.setWidth(iconRect.width() - self.borderWidth * 2)
        painter.setPen(iconPen)
        painter.drawRect(iconRect)

    def iconRect(self, option):
        """ Icon rect

        :param option:
        :type option:
        :return:
        :rtype:
        """
        padding = self.padding
        rect = option.rect
        width = rect.width() - padding
        height = rect.height() - padding
        # deal with the text #
        if self.showText:
            height -= self.textHeight + self.textPaddingV * 2
        rect.setWidth(width)
        rect.setHeight(height)

        x = padding + (float(width - rect.width()) * 0.5)
        y = padding + (float(height - rect.height()) * 0.5)
        rect.translate(x, y)
        return rect
