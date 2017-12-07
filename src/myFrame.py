from PyQt5 import QtCore, QtWidgets


class myFrame(QtWidgets.QFrame):
    """
    Overrides the resizeEvent method from QMainWindow and emits a pyqtSignal
    when the MainWindow is resized
    """
    resized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(myFrame, self).__init__(parent=parent)

    def resizeEvent(self, event):
        self.resized.emit()
