import math

from parapy.core  import Input, Attribute, Part
from parapy.geom  import (
    GeomBase,
    Point, Polygon, RevolvedSolid,
    XOY, rotate,
)

from Flow_station import FlowStation
from Duct         import Duct

class Casing(Duct):
