def float_range(start, stop, step=1.0):
    """Floating point implementation of range()"""
    res = []
    while start <= stop:
        res.append(start)
        start += step
    return res
