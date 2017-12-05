# -*- coding: utf-8 -*-
def print_statistics(tvec, data):
    """
    ATTENTION: this function inputs 'tvec', because it is a criteria. Even though
        it is not actually being used...

    Displays some descriptive statistics and outputs them as a
    table for the user to see

    INPUT:
        tvec: N x 6 matrix where each row is a time vector
        data: N x 4 matrix where each row is a set of measurements

    OUTPUT:
        stat: dataFrame containing descriptive statistics of data matrix

    USAGE:
        stat = print_statistics(tvec,data)

    @Author: Simon Moe Sørensen, moe.simon@gmail.com
    """
    # Define the relevant statistics
    dStats = ['min', '25%', '50%', '75%', 'max']

    # Get descriptive statistics of data, zone-wise
    statzone = data.describe().T[dStats].rename(
        index={'zone1': 1, 'zone2': 2, 'zone3': 3, 'zone4': 4})
    # The line above computes the statistics, transposes it, while only selecting
    # the relevant statistics. Then it renames the integers to zones

    # Get descriptive statistics of all zones
    statall = statzone.sum().describe().T[dStats].rename('All')
    # The line above does practically the same, however it is a Series and
    # has different renaming syntax than a dataFrame

    # Add together in a table
    stat = statzone.append(statall)

    # Assign index-column name
    stat.index.name = "Zone"

    return stat
