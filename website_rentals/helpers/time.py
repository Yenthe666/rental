import dateutil

def parse_datetime(data):
    if type(data) != str:
        return data.replace(tzinfo=None)
    return dateutil.parser.parse(data).replace(tzinfo=None)
