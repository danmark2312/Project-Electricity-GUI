# -*- coding: utf-8 -*-
def aggregate_measurements(tvec, data, period):
    """
    Aggregates data with respect to the time given by the user.

    INPUT:
        tvec: N x 6 matrix where each row is a time vector
        data: N x 4 matrix where each row is a set of measurements
        period: A string being one of the following
            - "month"
            - "day"
            - "hour"
            - "hour of the day"
            - "minute"

        Attention! Both tvec and data have to be non-aggregated or filtered data

    OUTPUT:
        tvec_a: N x 6 dataFrame where each row is a time vector
        data_a: N x 4 dataFrame where each row is a set of measurements

    USAGE:
        tvec_a, data_a = aggregate_measurements(tvec,data,period)


    @Author: Simon Moe Sørensen, moe.simon@gmail.com
    """

    # Ignore cases
    period = period.lower()

    # If period is minute, then delete all aggregations
    if period == "minute":
        data_a = data
        tvec_a = tvec
        return tvec_a, data_a

    # Join tvec and data
    df = tvec.join(data)

    # Define dictionary of periods
    period_dict = {
        "hour": ['year', 'month', 'day', 'hour'],
        "day": ['year', 'month', 'day'],
        "month": ['year', 'month'],
        "hour of the day": ['hour']}

    # Group the data according to defined period
    df_g = df.groupby(period_dict[period])

    if period != "hour of the day":
        # Define tvec by getting the first line of each group
        # i.e when it is grouped by day, it will find the first
        # line of the day, which can be 2008 12 1 0 0 0, 2008 12 2 0 0 0
        # and so on. Also reset indexes
        tvec_a = df_g.head(1).iloc[:, 0:5].reset_index(drop=True)

        # Get the dataFrame of aggregated data
        df_g = df_g['zone1', 'zone2', 'zone3',
                    'zone4'].sum()  # Sum the measurements

        data_a = df_g.reset_index(drop=True)  # Reset indexes

    # Do the same as above, but configured for hour of the day
    else:
        tvec_a = df_g.head(1).iloc[:, 3].reset_index(
            drop=True)  # Get only hours
        df_g = df_g['zone1', 'zone2', 'zone3',
                    'zone4'].mean()  # Define measurements as an average
        data_a = df_g.reset_index(drop=True)  # Reset indexes

    return tvec_a, data_a
