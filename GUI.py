"""
This script runs a GUI where the user can load data by drag and drop or
by direct filename, and analyze the data, including plotting.

@Author: Simon Moe Sørensen (s174420)

TODO:
implement embeded plots
"""


# Importing libraries
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

# Importing functions and exceptions
from functions.dataLoad import load_measurements, FileExtensionError
from functions.dataAggregation import aggregate_measurements
from functions.statistics import print_statistics

# Import plots and make them look pretty
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
matplotlib.style.use('ggplot')

"""
class plotCanvas(QtWidgets.QDialog):

    A class that creates a canvas on which to plot graphs
    It extends QtWidgets.QDialog


    def __init__(self, parent):
        super(plotCanvas, self).__init__(parent)
        self.figure = plt.figure()  # A figure to plot on
        # Create canvas on based on the current figure
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        self.toolbar = NavigationToolbar(self.canvas, self)

    def dataPlot(self, plotCanvas):
        # Clear canvas figure
        self.figure.clear()
        # See if user wants to plot for minutely aggregation
        if len(App.data) > 300000:
            choice = App.showQuestion("Attention! Large amount of data",
                                      "You are about to generate plots from a large amount of data, which may take above 30 seconds\nAre you sure you want to continue?")
            if choice == 0:
                return None
        # Get current plotting option from plotsMenu
        pltChoice = App.plotsMenu.currentText()
        # Define the plotting data
        if pltChoice == "All zones":
            pltData = App.data.sum(axis=1)
        elif pltChoice == "Each zone":
            pltData = App.data

        # Define x-axis and delete 0's
        if App.senderId != 5:
            # Get tvec as string without 0's
            tvec_0 = App.tvec.iloc[:, 0:(
                len(App.tvec.columns) - App.senderId)].astype(str)
            # set xAxis variable as years
            xAxis = tvec_0.iloc[:, 0]
            # Add all the columns of tvec_0 into a series
            for i in range(len(tvec_0.columns) - 1):
                xAxis = xAxis + " " + tvec_0.iloc[:, i + 1]
            xLabel = "Date"  # Set label
        else:
            xAxis = App.tvec
            xLabel = "Hour of the day"

        # Check type and rename index depending on this
        if isinstance(pltData, pd.DataFrame):
            pltData = pltData.set_index([xAxis])
        else:
            pltData = pltData.rename(xAxis)

        # Plot bars if length is less than 25
        if len(pltData) < 25:
            pltData.plot(kind='bar')
        else:
            pltData.plot()

        # Add options to plot
        plt.xlabel(xLabel)  # Add x-label
        plt.xticks(rotation=45)
        plt.ylabel(App.unit)  # Add y-label
        plt.title("Consumption per {}".format(App.period))
        # Define plot parameters
        plt.subplots_adjust(top=0.93, bottom=0.245, left=0.165, right=0.855,
                            hspace=0.2, wspace=0.2)  # adjust size
        plotCanvas.canvas.draw()
        # Add pie-chart
        plt.figure(figsize=(8, 8))
        App.data.sum().rename("").plot(kind='pie', title="Distribution of electricity consumption",
                                       autopct='%.2f%%', fontsize=16)  # Define pie chart
        plt.show()  # Display
        App.print_("Printed plots")  # Print
"""


class DragAndDrop(QtWidgets.QPlainTextEdit):
    """
    A class that sets a QPlainTextEdit widget to be able to recieve drops
    while at the same time disabling user interactions when needed.
    It extends QtWidgets.QPlainTextEdit and emits a custom signal when
    a file is dropped. Moreover the class also needs a parent when initialized
    """
    fileDrop = QtCore.pyqtSignal()  # Defining custom signal

    # Initiation, make widget acceptable to drops and non-editable
    # note DragAndDrop requires a parent
    def __init__(self, parent):
        super(DragAndDrop, self).__init__(
            parent)  # Avoid inheritance issues
        self.setAcceptDrops(True)
        self.setReadOnly(True)

    # On file-entering event, check if valid file, if yes, set write to true
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():  # Check for url of file
            e.accept()  # Accept file
            self.setReadOnly(False)  # Enable read
        else:
            e.ignore()  # Don't accept file

    # On drop event, get url and then disable write
    def dropEvent(self, e):
        # Get file location and save as floc
        self.floc = e.mimeData().text()
        self.setReadOnly(True)  # Disable read
        self.fileDrop.emit()  # Emit signal on dropEvent


class App():
    def __init__(self):
        # Initial variables
        self.unit = "Watt-hour"
        self.senderId = 1
        self.period = "minute"

        # Configure UI
        self.setupUi(MainWindow)
        # Set second tab as disabled
        self.tabWidget.setTabEnabled(1, False)

        # Add functionality to program by connecting different methods to
        # the interactive parts of the program (buttons, menus and so on)
        # Dataload
        self.loadfile_input.returnPressed.connect(
            self.dataLoad)
        self.loadfile_btn.clicked.connect(self.dataLoad)
        self.drop_input.fileDrop.connect(self.dataLoad)
        # Aggregate buttons
        self.agg_min_btn.clicked.connect(self.aggData)
        self.agg_hour_btn.clicked.connect(self.aggData)
        self.agg_day_btn.clicked.connect(self.aggData)
        self.agg_month_btn.clicked.connect(self.aggData)
        self.agg_hDay_btn.clicked.connect(self.aggData)
        # Command buttons
        self.stat_btn.clicked.connect(self.printStat)
        self.plot_btn.clicked.connect(self.dataPlot)
        self.showdata_btn.clicked.connect(self.showData)
        # Dropdown menus
        self.plotsMenu.currentIndexChanged.connect(
            self.menuChange)


# On change of dropdown menu
    def menuChange(self):
        self.print_("Changed plot data to {}".format(
            str(self.plotsMenu.currentText())))

# Show data
    def showData(self):
        pd.set_option('display.max_rows', 500)  # Set amount of rows
        # Print data
        if self.senderId != 5:
            self.print_(str(self.tvec.join(self.data)) +
                        "\nData printed \nCurrent unit: {}".format(self.unit))
        else:
            self.data.index.name = 'Hour of the day'
            self.print_(str(self.data))

# Question box
    def showQuestion(self, windowName, message):
        msg = QtWidgets.QMessageBox()
        choice = QtWidgets.QMessageBox.question(msg,
                                                windowName, message,
                                                msg.Yes | msg.No)  # Display question box
        # Set choice as binary 1 or 0
        if choice == msg.Yes:
            choice = 1
        else:
            choice = 0
        return choice

# Plot data
    def dataPlot(self):
        # See if user wants to plot for minutely aggregation
        if len(self.data) > 300000:
            choice = self.showQuestion("Attention! Large amount of data",
                                       "You are about to generate plots from a large amount of data, which may take above 30 seconds\nAre you sure you want to continue?")
            if choice == 0:
                return None
        # Get current plotting option from plotsMenu
        pltChoice = self.plotsMenu.currentText()
        # Define the plotting data
        if pltChoice == "All zones":
            pltData = self.data.sum(axis=1)
        elif pltChoice == "Each zone":
            pltData = self.data

        # Define x-axis and delete 0's
        if self.senderId != 5:
            # Get tvec as string without 0's
            tvec_0 = self.tvec.iloc[:, 0:(
                len(self.tvec.columns) - self.senderId)].astype(str)
            # set xAxis variable as years
            xAxis = tvec_0.iloc[:, 0]
            # Add all the columns of tvec_0 into a series
            for i in range(len(tvec_0.columns) - 1):
                xAxis = xAxis + " " + tvec_0.iloc[:, i + 1]
            xLabel = "Date"  # Set label
        else:
            xAxis = self.tvec
            xLabel = "Hour of the day"

        # Check type and rename index
        if isinstance(pltData, pd.DataFrame):
            pltData = pltData.set_index([xAxis])
        else:
            pltData = pltData.rename(xAxis)

        # Plot bars if length is less than 25
        if len(pltData) < 25:
            pltData.plot(kind='bar')
        else:
            pltData.plot()

        # Add options to plot
        plt.xlabel(xLabel)  # Add x-label
        plt.xticks(rotation=45)
        plt.ylabel(self.unit)  # Add y-label
        plt.title("Consumption per {}".format(self.period))
        # Define plot parameters
        plt.subplots_adjust(top=0.93, bottom=0.245, left=0.165, right=0.855,
                            hspace=0.2, wspace=0.2)  # adjust size
        # Add pie-chart
        plt.figure(figsize=(8, 8))
        self.data.sum().rename("").plot(kind='pie', title="Distribution of electricity consumption",
                                        autopct='%.2f%%', fontsize=16)  # Define pie chart
        plt.show()  # Display
        self.print_("Printed plots")  # Print

# Print statistics by creating a table widget
    def printStat(self):
        # Get statistics dataframe
        df_stat = print_statistics(self.tvec, self.data)
        self.statistics.setColumnCount(
            len(df_stat.columns))  # Set columns
        self.statistics.setRowCount(
            len(df_stat.index))  # Set rows
        # Assign values to rows and collumns in table
        for i in range(len(df_stat.index)):
            for j in range(len(df_stat.columns)):
                self.statistics.setItem(i, j, QtWidgets.QTableWidgetItem(
                    str(round(df_stat.iloc[i, j], 3))))

        # Set layout
        self.statistics.setHorizontalHeaderLabels(
            ["Min", "25%", "50%", "75%", "Max"])
        self.statistics.setVerticalHeaderLabels(
            ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "All"])
        self.statistics.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)  # Design
        self.print_(
            "Statistics printed \nCurrent unit: {}".format(self.unit))

# Print function
    def print_(self, text):
        self.display_window.insertPlainText(
            "\n===============\n{}\n===============".format(text))
        # Stay at bottom of window
        self.display_window.ensureCursorVisible()

# Aggregate data
    def aggData(self):
        periodStr = ["minute", "hour", "day", "month",
                     "hour of the day"]  # String of periods
        sender = MainWindow.sender()  # get sender
        self.senderId = sender.property(
            "AggId")  # get sender's Id
        # Define period
        self.period = periodStr[(self.senderId) - 1]
        # Aggregate data, but always agg from raw data
        self.tvec, self.data = aggregate_measurements(
            self.tvecOld, self.dataOld, self.period)

        # Check if it is preferable to convert units or keep them
        if (self.data > 5000).any().any():
            self.data = self.data / 1000
            self.unit = "Kilowatt-hour"
        else:
            self.unit = "Watt-hour"

        self.aggcurrent_line.setText("{} aggregation".format(
            sender.text()))  # Change current aggregation
        self.print_("Aggregated for the {}".format(
            periodStr[self.senderId - 1]))  # Print msg

    # data loading by drop
    def dataLoad(self):
        sender = MainWindow.sender()
        try:
            # Define filename dependent on sender
            if sender == (self.drop_input):
                filename = self.drop_input.floc  # Get file location
            else:
                filename = self.loadfile_input.text()  # Get text from filename

            # Get fmode
            fmode = str(self.error_dropmenu.currentText())
            # Only get first part of text
            fmode = fmode[0:fmode.find("(") - 1]
            self.tvec, self.data, warning = load_measurements(
                filename, fmode)  # Load data
            if type(warning) == str:
                self.showWarning(warning)
                self.error_dropmenu.setCurrentIndex(2)
            # Save data for later use
            self.tvecOld, self.dataOld = self.tvec, self.data
            self.showInfo(
                "File succesfully loaded, with the following errorhandling: \n{}".format(fmode))
            # Set second tab as enabled
            self.tabWidget.setTabEnabled(1, True)
            MainWindow.resize(750, 555)  # Set new window size
            # Reset analysis tab in case the user loaded new data
            self.aggcurrent_line.setText(
                "Minutely aggregation")  # Set aggregation text
            self.display_window.setPlainText("")  # Clear display window
            self.statistics.clear()  # Clear statistics
            self.tabWidget.setCurrentIndex(
                1)  # Change to second tab
        except FileNotFoundError:
            self.showCritical(
                "Error! No such file exists, please try again \nIs the file in the same directory as the .exe file? (Does not matter for drag and drop)")
        except FileExtensionError:
            self.showCritical(
                "Error! Wrong file extension, please try again")
        except OSError:
            self.showCritical(
                "Error! Can only load one file at a time, please try again")

    def showCritical(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(text)
        msg.setWindowTitle("Error!")
        msg.exec_()

    def showWarning(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(text)
        msg.setWindowTitle("Warning!")
        msg.exec_()

    def showInfo(self, text):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Information")
        msg.exec_()

    def displayPrint(self, text):
        self.drop_input.insertPlainText(text)

    # The UI has been created by the use of Qt Designer, therefore any code
    # written below this is comment is generated, only slightly modified
    def setupUi(self, MainWindow):
        # Initial GUI and layout
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowIcon(
            QtGui.QIcon('resources/icon.ico'))
        MainWindow.resize(734, 525)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(
            self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.header = QtWidgets.QLabel(self.centralwidget)
        self.header.setObjectName("header")
        self.verticalLayout.addWidget(
            self.header, 0, QtCore.Qt.AlignHCenter)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        # Tab widget
        self.tabWidget = QtWidgets.QTabWidget(
            self.centralwidget)
        self.tabWidget.setTabPosition(
            QtWidgets.QTabWidget.North)
        self.tabWidget.setTabShape(
            QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabBarAutoHide(True)
        self.tabWidget.setObjectName("tabWidget")
        # First tab
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(
            self.tab_1)
        self.verticalLayout_2.setObjectName(
            "verticalLayout_2")
        # Errorhandling, fmode dropdown menu
        self.error_box = QtWidgets.QGroupBox(self.tab_1)
        self.error_box.setStatusTip("")
        self.error_box.setObjectName("error_box")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(
            self.error_box)
        self.horizontalLayout_3.setObjectName(
            "horizontalLayout_3")
        self.error_dropmenu = QtWidgets.QComboBox(
            self.error_box)
        self.error_dropmenu.setLayoutDirection(
            QtCore.Qt.LeftToRight)
        self.error_dropmenu.setObjectName("error_dropmenu")
        self.error_dropmenu.addItem("")
        self.error_dropmenu.addItem("")
        self.error_dropmenu.addItem("")
        self.horizontalLayout_3.addWidget(
            self.error_dropmenu)
        self.verticalLayout_2.addWidget(self.error_box)
        # Load file by filename
        self.loadfile_box = QtWidgets.QGroupBox(self.tab_1)
        self.loadfile_box.setObjectName("loadfile_box")
        self.horizontalLayout = QtWidgets.QHBoxLayout(
            self.loadfile_box)
        self.horizontalLayout.setObjectName(
            "horizontalLayout")
        self.loadfile_input = QtWidgets.QLineEdit(
            self.loadfile_box)
        self.loadfile_input.setObjectName("loadfile_input")
        self.horizontalLayout.addWidget(self.loadfile_input)
        self.loadfile_btn = QtWidgets.QPushButton(
            self.loadfile_box)
        self.loadfile_btn.setObjectName("loadfile_btn")
        self.horizontalLayout.addWidget(self.loadfile_btn)
        self.verticalLayout_2.addWidget(self.loadfile_box)
        # Load file by drag and drop
        self.drop_box = QtWidgets.QGroupBox(self.tab_1)
        self.drop_box.setObjectName("drop_box")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(
            self.drop_box)
        self.horizontalLayout_2.setObjectName(
            "horizontalLayout_2")
        self.drop_input = DragAndDrop(
            self.drop_box)  # Using custom class
        self.drop_input.setObjectName("drop_input")
        self.horizontalLayout_2.addWidget(self.drop_input)
        self.verticalLayout_2.addWidget(self.drop_box)
        # New tab, analysis
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(
            self.tab_2)
        self.verticalLayout_3.setObjectName(
            "verticalLayout_3")
        # Show current aggregate - box
        self.aggcurrent_box = QtWidgets.QGroupBox(
            self.tab_2)
        self.aggcurrent_box.setObjectName("aggcurrent_box")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(
            self.aggcurrent_box)
        self.verticalLayout_4.setObjectName(
            "verticalLayout_4")
        # Show current aggregate - LineEdit widget
        self.aggcurrent_line = QtWidgets.QLineEdit(
            self.aggcurrent_box)
        self.aggcurrent_line.setAlignment(
            QtCore.Qt.AlignCenter)
        self.aggcurrent_line.setDragEnabled(False)
        self.aggcurrent_line.setReadOnly(True)
        self.aggcurrent_line.setClearButtonEnabled(False)
        self.aggcurrent_line.setObjectName(
            "aggcurrent_line")
        self.verticalLayout_4.addWidget(
            self.aggcurrent_line)
        self.verticalLayout_3.addWidget(self.aggcurrent_box)
        # Actual aggregate data box and it's correlated buttons
        self.agg_box = QtWidgets.QGroupBox(self.tab_2)
        self.agg_box.setObjectName("agg_box")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(
            self.agg_box)
        self.horizontalLayout_4.setObjectName(
            "horizontalLayout_4")
        self.agg_min_btn = QtWidgets.QPushButton(
            self.agg_box)
        self.agg_min_btn.setObjectName("agg_min_btn")
        self.agg_min_btn.setProperty("AggId", 1)
        self.horizontalLayout_4.addWidget(self.agg_min_btn)
        self.agg_hour_btn = QtWidgets.QPushButton(
            self.agg_box)
        self.agg_hour_btn.setObjectName("agg_hour_btn")
        self.agg_hour_btn.setProperty("AggId", 2)
        self.horizontalLayout_4.addWidget(self.agg_hour_btn)
        self.agg_day_btn = QtWidgets.QPushButton(
            self.agg_box)
        self.agg_day_btn.setObjectName("agg_day_btn")
        self.agg_day_btn.setProperty("AggId", 3)
        self.horizontalLayout_4.addWidget(self.agg_day_btn)
        self.agg_month_btn = QtWidgets.QPushButton(
            self.agg_box)
        self.agg_month_btn.setObjectName("agg_month_btn")
        self.agg_month_btn.setProperty("AggId", 4)
        self.horizontalLayout_4.addWidget(
            self.agg_month_btn)
        self.agg_hDay_btn = QtWidgets.QPushButton(
            self.agg_box)
        self.agg_hDay_btn.setObjectName("agg_hDay_btn")
        self.agg_hDay_btn.setProperty("AggId", 5)
        self.horizontalLayout_4.addWidget(self.agg_hDay_btn)
        self.verticalLayout_3.addWidget(self.agg_box)
        self.line_2 = QtWidgets.QFrame(self.tab_2)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_3.addWidget(self.line_2)
        # Command box
        self.cmd_box = QtWidgets.QGroupBox(self.tab_2)
        self.cmd_box.setObjectName("cmd_box")
        self.gridLayout = QtWidgets.QGridLayout(
            self.cmd_box)
        self.gridLayout.setObjectName("gridLayout")
        # Drop down menu for plots
        self.plotsMenu = QtWidgets.QComboBox(self.cmd_box)
        self.plotsMenu.setObjectName("plotsMenu")
        self.plotsMenu.addItem("")
        self.plotsMenu.addItem("")
        self.gridLayout.addWidget(
            self.plotsMenu, 0, 0, 1, 1)
        # Statistics button
        self.stat_btn = QtWidgets.QPushButton(self.cmd_box)
        self.stat_btn.setObjectName("stat_btn")
        self.gridLayout.addWidget(self.stat_btn, 2, 0, 1, 1)
        # Line
        self.line_3 = QtWidgets.QFrame(self.cmd_box)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 1, 0, 1, 2)
        # Plot button
        self.plot_btn = QtWidgets.QPushButton(self.cmd_box)
        self.plot_btn.setObjectName("plot_btn")
        self.gridLayout.addWidget(self.plot_btn, 0, 1, 1, 1)
        # Show data button
        self.showdata_btn = QtWidgets.QPushButton(
            self.cmd_box)
        self.showdata_btn.setObjectName("showdata_btn")
        self.gridLayout.addWidget(
            self.showdata_btn, 2, 1, 1, 1)
        self.verticalLayout_3.addWidget(self.cmd_box)
        # Display box
        self.display_box = QtWidgets.QGroupBox(self.tab_2)
        self.display_box.setObjectName("display_box")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(
            self.display_box)
        self.horizontalLayout_5.setObjectName(
            "horizontalLayout_5")
        # Statistics
        self.statistics = QtWidgets.QTableWidget(
            self.display_box)
        self.horizontalLayout_5.addWidget(self.statistics)
        # Display window
        self.display_window = QtWidgets.QPlainTextEdit(
            self.display_box)
        self.display_window.setReadOnly(True)
        self.display_window.setTextInteractionFlags(
            QtCore.Qt.NoTextInteraction)
        self.display_window.setObjectName("display_window")
        self.horizontalLayout_5.addWidget(
            self.display_window)
        """
# Plots window
        self.plot_window = plotCanvas(self.display_window)  # use custom class
        self.horizontalLayout_5.addWidget(self.plot_window)
        """
        self.verticalLayout_3.addWidget(self.display_box)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        # menu and statusbar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(
            QtCore.QRect(0, 0, 734, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # Retranslate the UI
        self.retranslateUi(MainWindow)
        # Set tab order
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(
            self.tabWidget, self.error_dropmenu)
        MainWindow.setTabOrder(
            self.error_dropmenu, self.loadfile_input)
        MainWindow.setTabOrder(
            self.loadfile_input, self.loadfile_btn)
        MainWindow.setTabOrder(
            self.loadfile_btn, self.drop_input)
        MainWindow.setTabOrder(
            self.drop_input, self.aggcurrent_line)
        MainWindow.setTabOrder(
            self.aggcurrent_line, self.agg_min_btn)
        MainWindow.setTabOrder(
            self.agg_min_btn, self.agg_hour_btn)
        MainWindow.setTabOrder(
            self.agg_hour_btn, self.agg_day_btn)
        MainWindow.setTabOrder(
            self.agg_day_btn, self.agg_month_btn)
        MainWindow.setTabOrder(
            self.agg_month_btn, self.agg_hDay_btn)
        MainWindow.setTabOrder(
            self.agg_hDay_btn, self.stat_btn)
        MainWindow.setTabOrder(self.stat_btn, self.plot_btn)
        MainWindow.setTabOrder(
            self.plot_btn, self.display_window)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate(
            "MainWindow", "Analysis of household electricity consumption"))
        self.header.setText(_translate(
            "MainWindow", "Welcome to the Analysis of household electricity consumption program "))
        self.error_box.setTitle(_translate(
            "MainWindow", "Errorhandling"))
        self.error_dropmenu.setToolTip(_translate(
            "MainWindow", "Click to select errorhandling mode"))
        self.error_dropmenu.setStatusTip(_translate(
            "MainWindow", "Click to select errorhandling mode"))
        self.error_dropmenu.setItemText(0, _translate(
            "MainWindow", "Forward fill (replace corrupt measurement with latest valid measurement)"))
        self.error_dropmenu.setItemText(1, _translate(
            "MainWindow", "Backward fill (replace corrupt measurement with next valid measurement)"))
        self.error_dropmenu.setItemText(2, _translate(
            "MainWindow", "Drop (delete corrupted measurements)"))
        self.loadfile_box.setTitle(
            _translate("MainWindow", "Filename"))
        self.loadfile_input.setToolTip(_translate(
            "MainWindow", "Please enter a filename"))
        self.loadfile_input.setStatusTip(_translate(
            "MainWindow", "Please enter a filename in this box"))
        self.loadfile_input.setPlaceholderText(_translate(
            "MainWindow", "Please enter the name of the datafile. Ex: 2008.csv"))
        self.loadfile_btn.setToolTip(_translate(
            "MainWindow", "Click to load data"))
        self.loadfile_btn.setStatusTip(_translate(
            "MainWindow", "Click to load data from filename"))
        self.loadfile_btn.setText(
            _translate("MainWindow", "Load data"))
        self.drop_box.setTitle(_translate(
            "MainWindow", "Drag and Drop"))
        self.drop_input.setToolTip(_translate(
            "MainWindow", "Drag a file into this box to load it"))
        self.drop_input.setStatusTip(_translate(
            "MainWindow", "Drag a file into this box to load it"))
        self.drop_input.setPlaceholderText(_translate(
            "MainWindow", "Please drag a datafile into this box"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1),
                                  _translate("MainWindow", "Load data"))
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(
            self.tab_1), _translate("MainWindow", "Select this tab to load data"))
        self.aggcurrent_box.setTitle(_translate(
            "MainWindow", "Current Aggregation"))
        self.aggcurrent_line.setToolTip(_translate(
            "MainWindow", "This is the current aggregation"))
        self.aggcurrent_line.setStatusTip(_translate(
            "MainWindow", "This box shows how the data is currently aggregated"))
        self.aggcurrent_line.setText(_translate(
            "MainWindow", "Minutely aggregation"))
        self.agg_box.setStatusTip(_translate(
            "MainWindow", "Click to aggregate for daily consumption"))
        self.agg_box.setTitle(_translate(
            "MainWindow", "Aggregate data"))
        self.agg_min_btn.setToolTip(_translate(
            "MainWindow", "Click to aggregate"))
        self.agg_min_btn.setStatusTip(_translate(
            "MainWindow", "Click to aggregate for minutely consumption"))
        self.agg_min_btn.setText(
            _translate("MainWindow", "Minutely"))
        self.agg_hour_btn.setToolTip(_translate(
            "MainWindow", "Click to aggregate"))
        self.agg_hour_btn.setStatusTip(_translate(
            "MainWindow", "Click to aggregate for hourly consumption"))
        self.agg_hour_btn.setText(
            _translate("MainWindow", "Hourly"))
        self.agg_day_btn.setToolTip(_translate(
            "MainWindow", "Click to aggregate"))
        self.agg_day_btn.setText(
            _translate("MainWindow", "Daily"))
        self.agg_month_btn.setToolTip(
            _translate("MainWindow", "Click to aggregate"))
        self.agg_month_btn.setStatusTip(_translate(
            "MainWindow", "Click to aggregate for monthly consumption"))
        self.agg_month_btn.setText(
            _translate("MainWindow", "Monthly"))
        self.agg_hDay_btn.setToolTip(_translate(
            "MainWindow", "Click to aggregate"))
        self.agg_hDay_btn.setStatusTip(_translate(
            "MainWindow", "Click to aggregate for the hourly average"))
        self.agg_hDay_btn.setText(
            _translate("MainWindow", "Hour-of-day"))
        self.cmd_box.setTitle(
            _translate("MainWindow", "Commands"))
        self.stat_btn.setToolTip(_translate(
            "MainWindow", "Click to display statistics"))
        self.stat_btn.setStatusTip(_translate(
            "MainWindow", "Click to display statistics based on currently aggregated data"))
        self.stat_btn.setText(_translate(
            "MainWindow", "Display statistics"))
        self.plot_btn.setToolTip(_translate(
            "MainWindow", "Click to visualize data"))
        self.plot_btn.setStatusTip(_translate(
            "MainWindow", "Click to visualize data in plots"))
        self.plot_btn.setText(_translate(
            "MainWindow", "Visualize data"))
        self.showdata_btn.setToolTip(_translate(
            "MainWindow", "Click to show data"))
        self.showdata_btn.setStatusTip(
            _translate("MainWindow", "Click to show data"))
        self.showdata_btn.setText(
            _translate("MainWindow", "Show data"))
        self.plotsMenu.setItemText(
            0, _translate("MainWindow", "Each zone"))
        self.plotsMenu.setItemText(
            1, _translate("MainWindow", "All zones"))
        self.display_box.setTitle(
            _translate("MainWindow", "Display window"))
        self.display_window.setToolTip(_translate(
            "MainWindow", "This window will display any messages given"))
        self.display_window.setStatusTip(_translate(
            "MainWindow", "This window will display any messages given"))
        self.display_window.setPlaceholderText(
            _translate("MainWindow", "No messages to display"))
        self.plotsMenu.setToolTip(_translate(
            "MainWindow", "This dropdown menu defines the data which is to be plotted"))
        self.plotsMenu.setStatusTip(_translate(
            "MainWindow", "This dropdown menu defines the data which is to be plotted"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2),
                                  _translate("MainWindow", "Analysis"))
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tab_2), _translate(
            "MainWindow", "Select this tab to analyze data"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = App()
    MainWindow.show()
    sys.exit(app.exec_())
