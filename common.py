import math

class Common(object):

    @classmethod
    def dm2deg(cls, dm=None):  # GPGGA -> GoogleMaps
        decimal, integer = math.modf(dm / 100.0)
        value = integer + ((decimal / 60.0) * 100.0)
        return value

    @classmethod
    def checkSum(cls, body=b''):
        cs = 0
        for v in body:
            cs ^= v
        return cs
