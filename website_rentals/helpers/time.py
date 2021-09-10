import dateutil
import datetime


def float_to_time(number):
    """Convert a float to hours and minutes."""
    return {
        "hours": int(number),
        "minutes": int((number - int(number)) * 60),
    }


def parse_datetime(data):
    """Parses either a string, date, or datetime into a datetime that is not timezone aware."""
    if type(data) == str:
        data = dateutil.parser.parse(data)

    if type(data) == datetime.date:
        return datetime.datetime(
            year=data.year, month=data.month, day=data.day, hour=0, minute=0, second=0
        )

    if type(data) == datetime.datetime:
        return data.replace(tzinfo=None)

    raise Exception("parse_datetime only accepts a datetime or date as a parameter.")
