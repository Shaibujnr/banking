from datetime import datetime, date

__todays_date: date = datetime(2020, 4, 1).date()  # April 1, 2020


def get_todays_date():
    """Holds the current date for the application"""
    return __todays_date


def set_todays_date(new_date: date):
    """Sets the current date for the application
    to allow simulation and observation of different
    actions performed on different dates

    Arguments:
        new_date {date} -- Date to change to
    """
    global __todays_date
    __todays_date = new_date
