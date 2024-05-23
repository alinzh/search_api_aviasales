from datetime import datetime

import pandas as pd


def convert_period_for_dates(start_date, end_date):
    """
    start_date is date in format: %Y-%m-%d
    Covert period in many dates.
    :return: list with dates.
    """

    arr_period_dates = (
        pd.date_range(min(start_date, end_date), max(start_date, end_date))
        .strftime("%Y-%m-%d")
        .tolist()
    )
    return arr_period_dates


def format_big_to_small(date_x):
    """
    convert format "%Y-%m-%dT%H:%M:%S%z" to "%Y-%m-%d"
    :param date:
    :return: date in format "%Y-%m-%d"
    """
    source_format = "%Y-%m-%dT%H:%M:%S%z"
    dt = datetime.strptime(date_x, source_format)
    result_date = dt.strftime("%Y-%m-%d")
    return result_date


def convert_day_to_month(date_x):
    """
    convert format "%Y-%m-%d" to "%Y-%m"
    :return: date in "%Y-%m"
    """
    source_format = "%Y-%m-%d"
    new_dates = []
    for i in range(len(date_x)):
        dt = datetime.strptime(date_x[i], source_format)
        result_date = dt.strftime("%Y-%m")
        new_dates.append(result_date)
    return new_dates


def period_for_month(start_date, end_date):
    a_lot_dates = convert_period_for_dates(start_date, end_date)
    format_years_month = convert_day_to_month(a_lot_dates)
    months = list(set(format_years_month))
    return months
