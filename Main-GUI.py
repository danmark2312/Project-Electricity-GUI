"""
This script runs a GUI where the user can load data by drag and drop or
by direct filename, and analyze the data, including plotting.

It is adviced to read the Readme first or press F1 in the application

@Author: Simon Moe Sørensen (s174420)
"""
# Importing libraries
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
import ctypes
import webbrowser
import os
import sys

# Importing functions and classes
from src.load_measurements import load_measurements, FileExtensionError
from src.aggregate_measurements import aggregate_measurements
from src.print_statistics import print_statistics
from src.myFrame import myFrame
from src.dragAndDrop import DragAndDrop

# Import plot and make them look pretty
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
matplotlib.style.use('ggplot')  # Set plotting layout


class App():
    """
    Class that takes no arguments and initiates the GUI when called.
    During initialization it combines the different buttons and events in the
    UI to a method in the same class
    """

    def __init__(self):
        # Initial variables
        self.unit = "Watt-hour"
        self.aggId = 1  # Identifies current aggregation
        self.period = "minute"
        self.periodCheck = None

        # Configure UI
        self.setupUi(MainWindow)
        # Set second tab as disabled
        self.tabWidget.setTabEnabled(1, False)

        # Add functionality to program by connecting different methods to
        # the interactive parts of the program (buttons, menus and so on)
        # Dataload
        self.loadfile_input.returnPressed.connect(self.dataLoad)
        self.loadfile_btn.clicked.connect(self.dataLoad)
        self.drop_input.fileDrop.connect(self.dataLoad)
        # Aggregate buttons
        self.agg_min_btn.clicked.connect(self.aggData)
        self.agg_hour_btn.clicked.connect(self.aggData)
        self.agg_day_btn.clicked.connect(self.aggData)
        self.agg_month_btn.clicked.connect(self.aggData)
        self.agg_hDay_btn.clicked.connect(self.aggData)
        # Command buttons
        self.stat_btn.clicked.connect(self.statToggle)
        self.plot_btn.clicked.connect(self.plotToggle)
        self.showdata_btn.clicked.connect(self.showData)
        self.plot_focus_btn.clicked.connect(self.plotFocus)
        # Dropdown menus
        self.plotMenu.currentIndexChanged.connect(self.menuChange)
        # Plot on changetype events
        self.aggcurrent_line.textChanged.connect(self.dataPlot)
        self.aggcurrent_line.textChanged.connect(self.printStat)
        self.plotMenu.currentIndexChanged.connect(self.dataPlot)
        self.plotFrame.resized.connect(self.plotResize)

# On change of dropdown menu
    def menuChange(self):
        """
        Print any changes done to how the data is plotted
        """
        self.print_("Changed plot data to {}".format(
            str(self.plotMenu.currentText())))  # Print changes

# Show data
    def showData(self):
        """
        Print the current data into the display window
        """
        pd.set_option('display.max_rows', 500)  # Set amount of rows
        # Print data based on current aggregation
        if self.aggId != 5:
            self.print_(str(self.tvec.join(self.data)) +
                        "\nData printed \nCurrent unit: {}".format(self.unit))
        else:
            self.data.index.name = 'Hour of the day'
            self.print_(str(self.data))

# Show/hide plot
    def plotToggle(self):
        """
        Toggle plot button and window
        """
        # Hide plot
        if self.plot_btn.text() == "Hide plot":
            self.plotFrame.hide()  # Hide widget
            self.plot_btn.setText("Show plot")  # Set btn text
            self.print_("Hiding plot")  # Display msg
        # Show plot
        else:
            self.plotFrame.show()
            self.plot_btn.setText("Hide plot")
            self.print_("Showing plot")
            self.dataPlot()

# Focus plot
    def plotFocus(self):
        """
        Closes all other boxes than plot and statistics to make plot more in
        focus
        """
        # If user wants to focus plot
        if self.plot_focus_btn.text() == "Focus plot":
            self.plot_focus_btn.setText("Unfocus plot")
            self.infocurrent_box.hide()
            self.agg_box.hide()
            self.cmd_box.hide()
            self.display_window.hide()
            self.line_2.hide()

        else:
            self.plot_focus_btn.setText("Focus plot")
            self.infocurrent_box.show()
            self.agg_box.show()
            self.cmd_box.show()
            self.display_window.show()
            self.line_2.show()

# Adjust plot to new size
    def plotResize(self):
        """
        Resizes plot to current canvas size
        Known bugs:
            - On a Macbook (12" display) the plt.tight_layout() method makes the
            program crash, worked around by letting the user manually adjust
            the plot size instead.

            - On a Macbook (12" display) the fontsize is way too large. Adjusting
            the code for this very particular case would make it unneccesary
            large. It could be solved by
            defining a 2 plot functions in another .py script for windows and macs
        """
        # Check for mac OS and small resolution and stop resize if true
        if sys.platform == "darwin" and self.screen_bool:
            return

        # Check if canvas is visible and within reasonable size
        width = int(self.canvas.width())
        if self.canvas.isVisible() and (width > 400):
            plt.tight_layout()

# Plot data
    def dataPlot(self):
        """
        Plots data to FigureCanvas widget if calling the function makes
        the plot visible. Such as clicking "show plots" or changing plotting
        type while plots have already been plotted.
        If a large amount of data is present, ask if user wants to procede
        """
        # Check if plotting type (each or all-types) has changed and window is
        # open. Then plot. If the window is closed or data has already been
        # plotted, then don't do plotting
        if MainWindow.sender() == self.plotMenu and self.canvas.isVisible():
            pass
        elif self.period == self.periodCheck or not self.canvas.isVisible():
            return

        # Warn user about large loading time
        if len(self.data) > 300000:
            # Warn user about large plotting data that can make the program lag
            choice = self.showQuestion("Attention! Large amount of data",
                                       "You are about to generate plot from a large amount of data which will make the program slow on most computers\nAre you sure you want to continue?")
            if choice == 0:
                self.plot_btn.click()  # Hide plot by simulating a click
                return

        self.print_("Data changed, generating new plot")  # Msg plot new data
        self.figure.clf()  # Clear current plot

        # Get current plotting option from plotMenu
        pltChoice = self.plotMenu.currentText()

        # Define the plotting data type
        if pltChoice == "All zones":
            pltData = self.data.sum(axis=1).copy()
            legends = ["Sum of all zones"]  # Define legend from string
        elif pltChoice == "Each zone":
            pltData = self.data.copy()
            legends = pltData.columns  # Get legends as columns

        # ===========================
        # Defining data to plot
        # ===========================
        # Define x-axis
        if self.aggId != 5:  # If aggregation is not hour of the day
            xLabel = "Date"
            # Create a datetime series
            xAxis = pd.to_datetime(self.tvec)
        else:
            xLabel = "Hour of the day"
            xAxis = pd.to_datetime(self.tvec, format='%H')

        # Check for dataFrame or Series type and rename index
        if isinstance(pltData, pd.DataFrame):
            pltData = pltData.set_index([xAxis])
        else:
            pltData.set_axis(0, xAxis)

        # ===========================
        # Plotting starts here
        # ===========================
        ax = self.figure.add_subplot(1, 1, 1)  # Create axis to plot on

        # Plot either line or bar plot depending on length of data
        if len(pltData) < 25:
            # Plot a bar graph. xAxis cannot be implemented in the same way
            # as a line graph, so worked around it by plotting through pandas
            # and assigning index in a separate command
            pltData.plot(kind='bar', ax=ax,
                         use_index=False)  # Pandas plot

            # Seperate xTicks for hour of the day and month
            if xLabel == "Date":  # Month
                plt.xticks(range(len(pltData.index)),
                           pltData.index.strftime("%b %Y"))  # Assign index
            else:  # Hour of the day
                plt.xticks(range(len(pltData.index)),
                           pltData.index.strftime("%H:00"))  # Assign index
        else:
            # Plot a line graph
            ax.plot(pltData.index, pltData.values)

            # Define datetime locations and formatting. Using AutoDateXXXXX to
            # make it adaptable to zooming
            locator = mdates.AutoDateLocator()
            formatter = mdates.AutoDateFormatter(locator)

            # Create custom datetime formats from the self.scaled dictionary inside
            # the AutoDateFormatter class
            formatter.scaled[365] = '%b\n%Y'  # Years
            formatter.scaled[30] = '%b\n%Y'  # Months
            formatter.scaled[1.0] = '%d. %b\n%Y'  # Days
            formatter.scaled[1. / 24.] = '%H:00\n%d. %b %y'  # Hours
            formatter.scaled[1. / (60. * 24.)] = '%H:%M\n%d. %b'  # Minutes
            formatter.scaled[1. / (60 * 60 * 24)] = '%H:%M:%S\n%d. %b'  # Sec

            # Assign the locator and formatter to the xAxis
            ax.xaxis.set_minor_locator(locator)
            ax.xaxis.set_major_formatter(formatter)

        self.figure.autofmt_xdate()  # Set proper rotations for xAxis
        # Add additional options to plot (self explanatory)
        ax.legend(legends, loc=0)
        ax.grid(True)
        ax.set_title("Electricity consumption per {}".format(self.period))
        ax.set_xlabel(xLabel)
        ax.set_ylabel(self.unit)

        # Set subplot size if plot is displayable. If it is below
        # 400 px width, then it is impossible to see anything anyways
        if int(self.canvas.width()) > 400:
            plt.tight_layout()

        self.canvas.draw()  # Draw to canvas

        # Define variable to check if data has already been generated
        self.periodCheck = self.period

# Show/hide stats
    def statToggle(self):
        """
        Toggle statistics button and window
        """
        # Hide stats
        if self.stat_btn.text() == "Hide statistics":
            self.statistics.hide()  # Hide statistics widget
            self.stat_btn.setText("Show statistics")  # Set btn text
            self.print_("Hiding statistics")  # Display msg
        # Show stats (does opposite of before)
        else:
            self.statistics.show()
            self.stat_btn.setText("Hide statistics")
            self.print_("Showing statistics")
            self.printStat()  # Print update statistics

# Print statistics by creating a table widget
    def printStat(self):
        """
        Prints statistics by assigning the dataFrame values from the
        print_statistics function to the QTableWidget: statistics
        """
        # Dont print statistics if window is not open
        if not self.statistics.isVisible():
            return
        # Get statistics dataframe
        df_stat = print_statistics(self.tvec, self.data)

        # Set statistics widget to same size of df_stat
        self.statistics.setColumnCount(
            len(df_stat.columns))
        self.statistics.setRowCount(
            len(df_stat.index))

        # Assign values to rows and collumns in table
        for i in range(len(df_stat.index)):
            for j in range(len(df_stat.columns)):
                self.statistics.setItem(i, j, QtWidgets.QTableWidgetItem(
                    str(round(df_stat.iloc[i, j], 3))))  # Round to 3 digits

        # Set layout for horizontal and vertical headers
        self.statistics.setHorizontalHeaderLabels(
            ["Min", "25%", "50%", "75%", "Max"])
        self.statistics.setVerticalHeaderLabels(
            ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "All"])
        # Dynamically adjust widget size
        self.statistics.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        # Set column width
        for column in range(len(df_stat.columns)):
            self.statistics.setColumnWidth(column, 75)

# Print function
    def print_(self, text):
        """
        Prints text to display_window

        INPUT:
            text: string with text to be printed

        OUTPUT:
            text printed onto display_window
        """
        self.display_window.insertPlainText(
            "\n--------------\n{}\n--------------".format(text))
        # Stay at bottom of window when printing so it only shows the
        # newest printed data
        self.display_window.ensureCursorVisible()

# Aggregate data
    def aggData(self):
        """
        Aggregate data based on the button clicked, change units
        if neccesary and display new aggregation

        Uses aggregate_measurements function to aggregate the data
        """
        periodStr = ["minute", "hour", "day", "month",
                     "hour of the day"]  # String of periods

        # Get the sender (which button is pressed) and it's id
        sender = MainWindow.sender()
        self.aggId = sender.property("AggId")

        # Define period
        self.period = periodStr[(self.aggId) - 1]

        # Aggregate data, but always from raw data to go from higher
        # aggregates to lower aggregates. I.e Month -> Hour
        self.tvec, self.data = aggregate_measurements(
            self.tvecOld, self.dataOld, self.period)

        # Change unit if any value of data is above 5000
        if (self.data > 5000).any().any():
            self.data = self.data / 1000
            self.unit = "Kilowatt-hour"
        else:
            self.unit = "Watt-hour"

        # Display the changes made
        self.aggcurrent_line.setText("{} aggregation | Unit: {}".format(
            sender.text(), self.unit))
        self.print_("Aggregated for the {}".format(
            periodStr[self.aggId - 1]))

# Load data
    def dataLoad(self):
        """
        Load data from the filename specified in the loadfile_input QLineEdit
        or from the location of the dropped file into the drop_input box
        If user's screen is small, then open in fullscreen and warn user

        Also resets the second tab and all relating data, in case the user
        loads data a second time

        Uses load_measurements function to aggregate the data
        """
        sender = MainWindow.sender()  # Get sender (by drag n drop or filename)
        try:
            # Define filename dependent on sender
            if sender == (self.drop_input):
                filename = self.drop_input.floc  # Get file from drop
            else:
                filename = self.loadfile_input.text()  # Get file from text

            # Define fmode from current dropdown menu
            fmode = str(self.error_dropmenu.currentText())

            fmode = fmode[0:fmode.find("(") - 1]  # Only get relevant text

            # Call load data function
            self.tvec, self.data, warning = load_measurements(
                filename, fmode)

            # Check if warning needs to be printed
            if type(warning) == str:
                self.showWarning(warning)  # display warning
                self.error_dropmenu.setCurrentIndex(2)  # set to drop mode

            # Save data for later use
            self.tvecOld, self.dataOld = self.tvec, self.data

            # Send information to user
            self.showInfo(
                "File succesfully loaded, with the following errorhandling: \n{}".format(fmode))

            # Ask if user wants to open maximized
            choice = self.showQuestion("Recommended view",
                                       "It is recommended to run this program in maximized mode\n"
                                       "Do you want to maximize the window?")
            # If yes, open as maximized
            if choice == 1:
                MainWindow.showMaximized()

            # Set second tab as enabled
            self.tabWidget.setTabEnabled(1, True)

            # Reset analysis tab in case the user loaded new data
            self.aggcurrent_line.setText(
                "Minutely aggregation | Unit: Watt-hour")  # Set aggregation text
            self.display_window.setPlainText("")  # Clear display window
            self.tabWidget.setCurrentIndex(1)  # Change to second tab
            self.periodCheck = None  # reset previous plot

            # Check if any windows are open in display_box and close them
            if self.statistics.isVisible():
                self.stat_btn.click()

            if self.canvas.isVisible():
                self.plot_btn.click()
                self.figure.clf()

            if self.plot_focus_btn.text() == "Unfocus plot":
                self.plot_focus_btn.click()

            # Check for a small screen
            screen_res = QtWidgets.QDesktopWidget().availableGeometry()
            self.screen_bool = int(screen_res.width()) < 1300 or int(
                screen_res.height()) < 700

            if self.screen_bool:
                self.showWarning(
                    "You have a very small screen!\nProgram might crash when plotting. \nUsing fullscreen mode to minimize chances of a crash")
                # If the user has a small resolution and is on a mac then
                # inform the user about how to adjust plots
                if sys.platform == "darwin":
                    self.showInfo(
                        "You must manually adjust the plot size.\nClick on the 5'th icon from the left and choose 'tight layout' when plotting")
                MainWindow.showFullScreen()

        # Print message if any of given errors are raised
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
        """
        Shows a critical type popup window

        INPUT:
            text: string with the text to print

        OUTPUT:
            Popup window
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(text)
        msg.setWindowTitle("Error!")
        msg.setWindowIcon(QtGui.QIcon('resources/Icon.ico'))
        msg.exec_()

    def showWarning(self, text):
        """
        Shows a warning type popup window

        INPUT:
            text: string with the text to print

        OUTPUT:
            Popup window
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(text)
        msg.setWindowTitle("Warning!")
        msg.setWindowIcon(QtGui.QIcon('resources/Icon.ico'))
        msg.exec_()

    def showInfo(self, text):
        """
        Shows an info type popup window

        INPUT:
            text: string with the text to print

        OUTPUT:
            Popup window
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Information")
        msg.setWindowIcon(QtGui.QIcon('resources/Icon.ico'))
        msg.exec_()

# Question box
    def showQuestion(self, windowName, message):
        """
        Ask the user a question as a popup box
        """
        qBox = QtWidgets.QMessageBox()  # Create message box widget

        # Center widget
        geometry = qBox.frameGeometry()  # Geometry of qBox
        cp = QtWidgets.QDesktopWidget().screenGeometry().center()  # Centerpoint
        geometry.moveCenter(cp)  # Set qBox's frame to center point
        qBox.move(geometry.topLeft())  # Move qBox to center point
        # Add Icon
        qBox.setWindowIcon(QtGui.QIcon('resources/Icon.ico'))

        # Display question
        choice = QtWidgets.QMessageBox.question(qBox,
                                                windowName, message,
                                                qBox.Yes | qBox.No)  # Display question box
        # Set choice as binary 1 or 0
        if choice == qBox.Yes:
            choice = 1
        else:
            choice = 0
        return choice

# Close application
    def close_app(self):
        """
        Closes application, but asks user first
        """
        if self.showQuestion("Quitting", "Are you sure you want to quit?") == 1:
            sys.exit()

# Open readme file
    def help_app(self):
        """
        Displays a help pdf file
        """
        path = os.path.dirname(os.path.abspath(
            __file__)) + "/resources/userguide.pdf"  # Define path to pdf
        webbrowser.open_new(
            r'file:///' + path)  # Open path

    def fs_app(self):
        """
        Toggles fullscreen
        """
        if MainWindow.windowState() & QtCore.Qt.WindowFullScreen:
            MainWindow.showNormal()
        else:
            MainWindow.showFullScreen()

    # The UI has been mainly generated by QtDesigner. However widgets such as:
    # plot, menubars and the dropdown menu for plotting data have been added
    # manually
    def setupUi(self, MainWindow):
        """
        Initiates the GUI
        """
        # Make sure to get icon in taskbar as well (on windows only)
        if sys.platform == "win32":
            myappid = u'dankmemes'  # arbitrary string, using 'u' for unicode
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)
        # Initial window
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowIcon(QtGui.QIcon('resources/Icon.ico'))
        MainWindow.setMinimumSize(650, 500)
        MainWindow.resize(734, 525)
        # Center MainWindow
        geometry = MainWindow.frameGeometry()  # Geometry of qBox
        cp = QtWidgets.QDesktopWidget().screenGeometry().center()  # Centerpoint
        geometry.moveCenter(cp)  # Set qBox's frame to center point
        MainWindow.move(geometry.topLeft())  # Move qBox to center point
        # Initiate GUI with widget and vertical layout
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(
            self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
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
        self.infocurrent_box = QtWidgets.QGroupBox(
            self.tab_2)
        self.infocurrent_box.setObjectName("aggcurrent_box")
        self.infocurrent_box.setMaximumSize(314159, 80)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(
            self.infocurrent_box)
        self.verticalLayout_4.setObjectName(
            "verticalLayout_4")
        # Show current aggregate - LineEdit widget
        self.aggcurrent_line = QtWidgets.QLineEdit(
            self.infocurrent_box)
        self.aggcurrent_line.setAlignment(
            QtCore.Qt.AlignCenter)
        self.aggcurrent_line.setDragEnabled(False)
        self.aggcurrent_line.setReadOnly(True)
        self.aggcurrent_line.setClearButtonEnabled(False)
        self.aggcurrent_line.setMinimumSize(0, 25)
        self.aggcurrent_line.setObjectName(
            "aggcurrent_line")
        self.verticalLayout_4.addWidget(
            self.aggcurrent_line)
        self.verticalLayout_3.addWidget(self.infocurrent_box)
        # Actual aggregate data box and it's correlated buttons
        self.agg_box = QtWidgets.QGroupBox(self.tab_2)
        self.agg_box.setObjectName("agg_box")
        self.agg_box.setMaximumSize(314159, 70)
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
        self.cmd_box.setMaximumSize(314159, 155)
        self.gridLayout = QtWidgets.QGridLayout(
            self.cmd_box)
        self.gridLayout.setObjectName("gridLayout")
        # Drop down menu for plot
        self.plotMenu = QtWidgets.QComboBox(self.cmd_box)
        self.plotMenu.setObjectName("plotMenu")
        self.plotMenu.addItem("")
        self.plotMenu.addItem("")
        self.gridLayout.addWidget(
            self.plotMenu, 0, 0, 1, 1)
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
        self.display_box.setMinimumSize(400, 0)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(
            self.display_box)
        self.horizontalLayout_5.setObjectName(
            "horizontalLayout_5")

        # Plot window
        self.plotFrame = myFrame(self.display_box)  # Create frame
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(
            self.plotFrame)  # Create vLayout for plot

        # Add focus button
        self.plot_focus_btn = QtWidgets.QPushButton(self.plotFrame)
        self.plot_focus_btn.setObjectName("plot_focus_btn")
        self.verticalLayout_5.addWidget(self.plot_focus_btn)

        # Add plotting canvas
        self.figure = plt.figure()  # a figure to plot on
        self.canvas = FigureCanvas(self.figure)  # canvas to display plot on
        self.toolbar = NavigationToolbar(self.canvas, None)  # toolbar
        self.canvas.setMinimumSize(300, 200)
        self.horizontalLayout_5.addWidget(self.plotFrame)  # Add to layout
        self.verticalLayout_5.addWidget(self.toolbar)  # Add toolbar to layout
        self.verticalLayout_5.addWidget(self.canvas)  # Add canvas to layout
        # Hide plot to begin with
        self.plotFrame.hide()

        # Statistics
        self.statistics = QtWidgets.QTableWidget(self.display_box)
        # self.statistics.setMinimumSize(425, 166677)
        self.statistics.setMaximumSize(450, 166677)
        self.statistics.hide()
        self.horizontalLayout_5.addWidget(self.statistics)
        # Display window
        self.display_window = QtWidgets.QPlainTextEdit(
            self.display_box)
        self.display_window.setReadOnly(True)
        self.display_window.setTextInteractionFlags(
            QtCore.Qt.NoTextInteraction)
        self.display_window.setObjectName("display_window")
        self.display_window.setMaximumSize(450, 166677)
        self.horizontalLayout_5.addWidget(
            self.display_window)
        # self.horizontalLayout_5.addStretch()
        self.verticalLayout_3.addWidget(self.display_box)
        # Finish tabs
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        # Menubar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        options = self.menubar.addMenu("Options")

        # Set parameters for helpAction
        helpAction = QtWidgets.QAction('Show help', MainWindow)
        helpAction.setStatusTip("Help for App")
        helpAction.triggered.connect(self.help_app)
        helpAction.setShortcut("F1")
        options.addAction(helpAction)  # Add to menu

        # Set parameter for fsAction (full screen action)
        fsAction = QtWidgets.QAction('Toggle fullscreen', MainWindow)
        fsAction.setStatusTip("Toggle fullscreen")
        fsAction.triggered.connect(self.fs_app)
        fsAction.setShortcut("F11")
        options.addAction(fsAction)  # Add to menu

        # Mac OS has built-in quit menu (Cmd+Q)
        # Set parameters for exitAction
        exitAction = QtWidgets.QAction('Exit', MainWindow)
        exitAction.setStatusTip("Quit app")
        exitAction.triggered.connect(self.close_app)
        exitAction.setShortcut("Ctrl+Q")
        options.addAction(exitAction)  # Add to menu

        # Set parameter for fsAction (full screen action)
        dankAction = QtWidgets.QAction('Play dank music', MainWindow)
        dankAction.setStatusTip("Toggle some dank music")
        dankAction.triggered.connect(self.dank_app)
        dankAction.setShortcut("F2")
        options.addAction(dankAction)  # Add to menu

        self.menubar.setGeometry(
            QtCore.QRect(0, 0, 734, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        # Statusbar
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # Retranslate the UI
        self.naming(MainWindow)
        # Set tab order
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.tabWidget, self.error_dropmenu)
        MainWindow.setTabOrder(self.error_dropmenu, self.loadfile_input)
        MainWindow.setTabOrder(self.loadfile_input, self.loadfile_btn)
        MainWindow.setTabOrder(self.loadfile_btn, self.drop_input)
        MainWindow.setTabOrder(self.drop_input, self.aggcurrent_line)
        MainWindow.setTabOrder(self.aggcurrent_line, self.agg_min_btn)
        MainWindow.setTabOrder(self.agg_min_btn, self.agg_hour_btn)
        MainWindow.setTabOrder(self.agg_hour_btn, self.agg_day_btn)
        MainWindow.setTabOrder(self.agg_day_btn, self.agg_month_btn)
        MainWindow.setTabOrder(self.agg_month_btn, self.agg_hDay_btn)
        MainWindow.setTabOrder(self.agg_hDay_btn, self.plotMenu)
        MainWindow.setTabOrder(self.plotMenu, self.plot_btn)
        MainWindow.setTabOrder(self.plot_btn, self.stat_btn)
        MainWindow.setTabOrder(self.stat_btn, self.showdata_btn)
        MainWindow.setTabOrder(self.showdata_btn, self.display_window)

    # So hidden, much wow
    def dank_app(self):
        """
        Toggle some dank music
        """
        from pygame import mixer
        import random
        mixer.init()  # Initialize
        music = ["Allstar", "Big Shaq", "Darude", "HEYAYA", "PPAP",
                 "Seinfeld Theme", "We Are Number One", "To Be Continued",
                 "Shooting star"]
        if mixer.music.get_busy():  # If playing, then stop
            mixer.music.stop()
            self.statusbar.showMessage("Stopped music")
        else:  # Else load some dank music, randomly o.O
            song = random.choice(music)
            mixer.music.load(
                'resources/dank/{}.mp3'.format(song))
            mixer.music.play()
            self.statusbar.showMessage("Now playing: {}".format(song))

    def naming(self, MainWindow):
        MainWindow.setWindowTitle(
            "Analysis of Household Electricity Consumption")
        self.error_box.setTitle("Errorhandling")
        self.error_dropmenu.setToolTip("Click to select errorhandling mode")
        self.error_dropmenu.setStatusTip("Click to select errorhandling mode")
        self.error_dropmenu.setItemText(
            0, "Forward fill (replace corrupt measurement with latest valid measurement)")
        self.error_dropmenu.setItemText(
            1, "Backward fill (replace corrupt measurement with next valid measurement)")
        self.error_dropmenu.setItemText(
            2, "Drop (delete corrupted measurements)")
        self.loadfile_box.setTitle("Filename")
        self.loadfile_input.setToolTip("Please enter a filename")
        self.loadfile_input.setStatusTip(
            "Please enter a filename in this box")
        self.loadfile_input.setPlaceholderText(
            "Please enter the name of the datafile. Ex: 2008.csv")
        self.loadfile_btn.setToolTip("Click to load data")
        self.loadfile_btn.setStatusTip("Click to load data from filename")
        self.loadfile_btn.setText("Load data")
        self.drop_box.setTitle("Drag and Drop")
        self.drop_input.setToolTip("Drag a file into this box to load it")
        self.drop_input.setStatusTip("Drag a file into this box to load it")
        self.drop_input.setPlaceholderText(
            "Please drag a datafile into this box")
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_1), "Load data")
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(
            self.tab_1), "Select this tab to load data")
        self.infocurrent_box.setTitle("Current information")
        self.aggcurrent_line.setToolTip(
            "This is the current information about the data")
        self.aggcurrent_line.setStatusTip(
            "This box shows how the data is currently aggregated and in what unit it is")
        self.aggcurrent_line.setText("Minutely aggregation")
        self.agg_box.setStatusTip("Click to aggregate for daily consumption")
        self.agg_box.setTitle("Aggregate data")
        self.agg_min_btn.setToolTip("Click to aggregate")
        self.agg_min_btn.setStatusTip(
            "Click to aggregate for minutely consumption")
        self.agg_min_btn.setText("Minutely")
        self.agg_hour_btn.setToolTip("Click to aggregate")
        self.agg_hour_btn.setStatusTip(
            "Click to aggregate for hourly consumption")
        self.agg_hour_btn.setText("Hourly")
        self.agg_day_btn.setToolTip("Click to aggregate")
        self.agg_day_btn.setText("Daily")
        self.agg_month_btn.setToolTip("Click to aggregate")
        self.agg_month_btn.setStatusTip(
            "Click to aggregate for monthly consumption")
        self.agg_month_btn.setText("Monthly")
        self.agg_hDay_btn.setToolTip("Click to aggregate")
        self.agg_hDay_btn.setStatusTip(
            "Click to aggregate for the hourly average")
        self.agg_hDay_btn.setText("Hour-of-day")
        self.cmd_box.setTitle("Commands")
        self.stat_btn.setToolTip("Click to hide/show statistics")
        self.stat_btn.setStatusTip(
            "Click to hide/show statistics based on currently aggregated data")
        self.stat_btn.setText("Show statistics")
        self.plot_btn.setToolTip("Click to show/hide data")
        self.plot_btn.setStatusTip("Click to show/hide data in plot")
        self.plot_btn.setText("Show plot")
        self.showdata_btn.setToolTip("Click to show data")
        self.showdata_btn.setStatusTip("Click to show data")
        self.showdata_btn.setText("Print data")
        self.plotMenu.setItemText(0, "Each zone")
        self.plotMenu.setItemText(1, "All zones")
        self.display_box.setTitle("Display window")
        self.display_window.setToolTip(
            "This window will display any messages given")
        self.display_window.setStatusTip(
            "This window will display any messages given")
        self.display_window.setPlaceholderText("No messages to display")
        self.plotMenu.setToolTip(
            "This dropdown menu defines the data which is to be plotted")
        self.plotMenu.setStatusTip(
            "This dropdown menu defines the data which is to be plotted")
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), "Analysis")
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(
            self.tab_2), "Select this tab to analyze data")
        self.plot_focus_btn.setText("Focus plot")
        self.plot_focus_btn.setToolTip("Focus plot")
        self.plot_focus_btn.setStatusTip("Click to focus plot")


# If script is run as main, then initialize the app
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = App()
    MainWindow.show()
    sys.exit(app.exec_())
