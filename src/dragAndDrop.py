from PyQt5 import QtCore, QtWidgets


class DragAndDrop(QtWidgets.QPlainTextEdit):
    """
    Sets a QPlainTextEdit widget to be able to recieve drops
    while at the same time disabling user interactions when needed.
    It extends QtWidgets.QPlainTextEdit and emits a custom signal when
    a file is dropped. Moreover the class also needs a parent when initialized
    """
    fileDrop = QtCore.pyqtSignal()  # Defining custom signal

    # Initiation, make widget acceptable to drops and non-editable
    # note DragAndDrop requires a parent
    def __init__(self, parent):
        super(DragAndDrop, self).__init__(parent)  # Avoid inheritance issues
        self.setAcceptDrops(True)
        self.setReadOnly(True)

    # On file-entering event, check if valid file, if yes, set write to true
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():  # Check for url of file
            e.accept()  # Accept file
            self.setReadOnly(False)
        else:
            e.ignore()  # Don't accept file

    # On drop event, get url, disable write then emit drop signal
    def dropEvent(self, e):
        # Get file location and save as floc
        self.floc = e.mimeData().text()
        self.setReadOnly(True)  # Disable read
        self.fileDrop.emit()  # Emit signal on dropEvent
