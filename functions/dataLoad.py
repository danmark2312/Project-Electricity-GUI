# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


class FileExtensionError(Exception):
    """
    Custom exception that displays an error message 'msg' when called
    """

    def __init__(self, msg):
        self.msg = msg


def load_measurements(filename, fmode):
    """
    Loads data from a .csv file and separates it into two variables
    tvec and data. Any corrupt data will be handled in the mode specified
    by the user (fmode). If a problem with either forward fill or backward fill
    is encountered, then print a warning and change to drop mode.

    INPUT:
        filename: String, the full name of the datafile
        fmode: String, specifying how to handle corrupted measurements.
            Can be:
                "forward fill"
                "backward fill"
                "drop"

    OUTPUT:
        tvec: N x 6 dataFrame where each row is a time vector
        data: N x 4 dataFrame where each row is a set of measurements
        warning: String, warning message

    USAGE:
        tvec,data = load_measurements(filename,fmode)

    @Author: Simon Moe Sørensen, moe.simon@gmail.com
    """

    # Initial variables
    warning = False
    fmodeStr = ["forward fill", "backward fill", "drop"]
    fmode = fmode.lower()

    # Check if csv file
    if ".csv" not in filename:
        raise FileExtensionError("Wrong file extension, please try again")

    # Load the datafile into DataFrame (variable name: df)
    df = pd.read_csv(filename, header=None,
                     names=["year", "month", "day", "hour", "minute", "second", "zone1", "zone2", "zone3", "zone4"])

    # Replace -1 with NaN values
    df = df.replace(-1, np.NaN)

    # Check if first or last row is corrupted and compare to errorhandling mode
    # if special case is found, change to drop mode and print warning
    if df.iloc[0, :].isnull().any() and fmode in fmodeStr[0]:
        # Change to drop mode
        fmodeold = fmode
        fmode = "drop"
        # Print warning
        warning = True

    elif df.iloc[len(df) - 1, :].isnull().any() and fmode in fmodeStr[1]:
        # Change to drop mode
        fmodeold = fmode
        fmode = "drop"
        # Print warning
        warning = True

    # Do errorhandling
    if fmode == "forward fill":
        # Use pandas forward fill
        df = df.ffill()

    elif fmode == "backward fill":
        # Use pandas backfill
        df = df.bfill()

    elif fmode == "drop":
        # Use pandas drop missing values
        df = df.dropna()

    # Print warning
    if warning:
        warning = ("""
!WARNING!
{} error
dropping all corrupted rows""".format(fmodeold))

    # Define data and tvec as a pandas dataFrame
    data = df.iloc[:, 6:10]
    tvec = df.iloc[:, 0:6]

    return tvec, data, warning
