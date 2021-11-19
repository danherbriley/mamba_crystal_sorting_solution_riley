from enum import IntEnum
import matplotlib.pyplot as plt

from random import random, seed
from math import sin, cos, radians, sqrt, pi
from typing import Optional
from shapely.geometry import Polygon


def polygon_area(corners):
    """Implementation of Shoelace formula."""
    n = len(corners)  # of corners
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return round(area, 12)  # round to 12 decimal places because of floating point arithmetics problems)


# define Python user-defined exceptions
class NotAllowedError(Exception):
    """Raised when performing not allowed operation."""
    pass


class Symmetry(IntEnum):
    none = 360
    twofold = 180
    threefold = 120
    fourfold = 90
    sixfold = 60


class ShapeGenerator(object):

    def __init__(self, radius: float, rotations: Symmetry):
        self._radius = radius
        self._rotations = rotations
        self._shape = None
        self._ready = True
        self._shapes = []

    @property
    def current_shape(self):
        return self._shape

    def new_shape(self):
        """Generate new shape and return it."""
        if self._ready:
            self._ready = False
            self._shape = self._get_shape()
            return self._shape
        else:
            raise NotAllowedError("Shape generator is not ready, submit previous shape position")

    def place_shape(self, x: float, y: float, rotation: int):
        """Place shape to have its position at given coordinates.

        x, y: coordinates of the first point of the shape (shape[0])
        rotation: rotation of the shape in degrees (must be allowed by symmetry)
        """
        if self._shape is None:
            raise NotAllowedError("There is no shape to place, get a new shape first")

        s = self._rotate_shape(self._shape, rotation)
        s = self._translate_shape(s, x, y)

        # check for corners outside the radius
        for corner in s:
            distance = round(sqrt(corner[0] * corner[0] + corner[1] * corner[1]), 12)  # round to 12 decimal places because of floating point arithmetics problems)
            if distance > self._radius:
                raise NotAllowedError(f"You can't place a shape outside of the circle of radius {self._radius}!")

        # check collisions using shapely library
        current_shape = Polygon(s)
        other_shapes = [Polygon(x) for x in self._shapes]
        for x in other_shapes:
            if current_shape.intersection(x).area > 0.0000001:
                print(current_shape.intersection(x).area, len(self._shapes))
                raise NotAllowedError(f"You can't place a shape so it overlaps with other shape!")

        self._shapes.append(s)
        self._shape = None
        self._ready = True

    def show_results(self):
        f = plt.figure()
        # add circle
        ax = f.gca()
        ax.set_aspect(1)
        circle = plt.Circle((0, 0), self._radius, color='#aaa')
        ax.add_patch(circle)
        # add shapes
        for s in self._shapes:
            s = s + [s[0]]    # in order to close the loop
            xs, ys = zip(*s)  # zip to x and y
            plt.plot(xs, ys)
        plt.show()

    def print_results(self):
        print(f"Number of shapes: {len(self._shapes)}")
        print(f"Filled area: {self.filled_area}")

    @property
    def filled_area(self):
        area = sum([polygon_area(x) for x in self._shapes])  # total area of shapes
        ratio = area / (pi * self._radius * self._radius)
        # return value between 0 - 1
        return ratio
    
    @property
    def placed_shapes(self):
        return len(self._shapes)

    def _get_shape(self):
        raise NotImplementedError("You need to override this method")

    def _translate_shape(self, shape, x, y):
        """"""
        translated = []
        dx = x - shape[0][0]
        dy = y - shape[0][1]
        for corner in shape:
            translated.append([corner[0] + dx, corner[1] + dy])
        return translated

    def _rotate(self, point, angle, center_point=(0, 0)):
        """Rotates a point around center_point(origin by default).
        Angle is in degrees.
        Rotation is counter-clockwise.
        """
        angle_rad = radians(angle % 360)
        # Shift the point so that center_point becomes the origin
        new_point = (point[0] - center_point[0], point[1] - center_point[1])
        new_point = (new_point[0] * cos(angle_rad) - new_point[1] * sin(angle_rad),
                     new_point[0] * sin(angle_rad) + new_point[1] * cos(angle_rad))
        # Reverse the shifting we have done
        new_point = (new_point[0] + center_point[0], new_point[1] + center_point[1])
        return new_point

    def _rotate_shape(self, shape, angle):
        """Rotates the current shape around first point.
        Rotation is counter-clockwise.
        Angle is in degrees.
        """
        if angle % int(self._rotations) > 0:
            raise NotAllowedError(f"Rotation of {angle}° is not allowed in {self._rotations} symmetry.")
        rotated = []
        center = shape[0]
        for corner in shape:
            rotated.append(self._rotate(corner, angle, center))
        return rotated


class RandomShapeGenerator(ShapeGenerator):
    def _get_shape(self):
        a = []
        a.append([ random(), random()])
        a.append([-random(), random()])
        a.append([-random(),-random()])
        a.append([ random(),-random()])
        return a

    def __init__(self, radius: float, rotations: Symmetry, fixed_seed: int = None):
        if fixed_seed is not None:
            seed(fixed_seed)
        self._radius = radius
        self._rotations = rotations
        self._shape = None
        self._ready = True
        self._shapes = []


class SquareShapeGenerator(ShapeGenerator):
    def _get_shape(self):
        a = [[1, 1], [1, 0], [0, 0], [0, 1]]
        return a


# SFG competition placer interface:

class Placer(object):
    def __init__(self, sg: ShapeGenerator):
        self._sg = sg
    
    def run(self):
        # do some magic
        return self._sg
