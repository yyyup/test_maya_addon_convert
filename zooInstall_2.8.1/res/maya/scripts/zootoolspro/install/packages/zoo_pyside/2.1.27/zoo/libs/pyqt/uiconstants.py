# Colors
DARKBGCOLOR = tuple([93, 93, 93])
MEDBGCOLOR = tuple([73, 73, 73])
MAYABGCOLOR = tuple([68, 68, 68])
DEFAULT_ICON_COLOR = tuple([192, 192, 192])
# DPI
DEFAULT_DPI = 96

# Pixel Size is not handled by dpi, use utils.dpiScale()
MARGINS = (2, 2, 2, 2)  # default margins left, top, right, bottom

SPACING = 2
SSML = 4  # the regular spacing of each widget, spacing is between each sub widget
SREG = 6  # the regular spacing of each widget, spacing is between each sub widget
SLRG = 10  # larger spacing of each widget, spacing is between each sub widget
SVLRG = 15  # very large spacing of each widget, spacing is between each sub widget
SVLRG2 = 20
SXLRG = 30  # extra large spacing of each widget, spacing is between each sub widget

TOPPAD = 10  # padding between the top widget and the top of frame. ie top of a toolset
BOTPAD = 5  # padding between the bottom widget and the bottom of frame. ie bot of a toolset
REGPAD = 10  # padding between widgets
SMLPAD = 5
VSMLPAD = 3
LRGPAD = 15
WINSIDEPAD = 6  # the overall window each side
WINTOPPAD = 6  # the overall window padding at the top of frame
WINBOTPAD = 6  # the overall window padding at the bottom of frame

MAYA_BTN_PADDING = 4, 2, 0, 2
ZOO_BTN_PADDING = 7, 4, 4, 4
NO_ICON_BTN_PADDING = 8, 8, 4, 7
ZOO_BTN_ICON_SIZE = 16
MAYA_BTN_ICON_SIZE = 24

# Button Width Sizes
BTN_W_ICN_SML = 10
BTN_W_ICN_REG = 20
BTN_W_ICN_MED = 30
BTN_W_ICN_LRG = 40
BTN_W_REG_SML = 90
BTN_W_REG_LRG = 180

# Sizes of the resizers Frameless
FRAMELESS_VERTICAL_PAD = 12
FRAMELESS_HORIZONTAL_PAD = 10

# Button Styles
BTN_DEFAULT = 0  # Default zoo extended button with optional text or an icon.
BTN_TRANSPARENT_BG = 1  # Default zoo extended button w transparent bg.
BTN_ICON_SHADOW = 2  # Main zoo IconPushButton button (icon in a colored box) with shadow underline
BTN_DEFAULT_QT = 3   # Default style uses vanilla QPushButton and not zoo's extended button
BTN_ROUNDED = 4  # Rounded button stylesheeted bg color and stylesheeted icon colour
BTN_LABEL_SML = 5  # Qt label with a small icon button

# Colors
COLOR_ERROR = "00ff06"  # fluorescent green
COLOR_ADMIN_GREEN = "17a600"
COLOR_ADMIN_GREEN_RGB = (23, 166, 0)


TITLE_LOGOICON_SIZE = 22
QWIDGETSIZE_MAX = 16777215

QT_SUPPORTED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "bmp", "pbm", "pgm", "ppm", "xbm", "xpm"]

try:
    from zoovendor.Qt import QtWidgets
    DOUBLE_CLICK_INTERVAL = QtWidgets.QApplication.doubleClickInterval()
except AttributeError:
    DOUBLE_CLICK_INTERVAL = 500
