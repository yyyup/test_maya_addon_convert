def update_members(members):
    """An example of adding Qsci to Qt.py.

    Arguments:
        members (dict): The default list of members in Qt.py.
            Update this dict with any modifications needed.
    """

    # Include Qsci module for scintilla lexer support.
    members["QtCore"].append("QIdentityProxyModel")