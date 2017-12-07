from PyQt5 import QtCore, QtWidgets


class myWindow(QtWidgets.QMainWindow):
    """
    Overrides the resizeEvent method from QMainWindow and emits a pyqtSignal
    when the MainWindow is resized
    """
    resized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(myWindow, self).__init__(parent=parent)

    def resizeEvent(self, event):
        self.resized.emit()
