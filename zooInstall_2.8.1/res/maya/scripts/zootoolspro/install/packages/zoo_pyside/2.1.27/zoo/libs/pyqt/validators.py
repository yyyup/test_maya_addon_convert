from zoovendor.Qt import QtGui


class UpperCaseValidator(QtGui.QValidator):
    """ Validator that keeps the text upper case
    todo: untested

    """
    def validate(self, string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos