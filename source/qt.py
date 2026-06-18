"""
QT Abstraction to support multiple versions of Maya
"""

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
    IS_QT6 = True
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance
    IS_QT6 = False
