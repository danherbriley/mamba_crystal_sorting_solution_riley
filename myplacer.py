from mocker import ShapeGenerator
from typing import List, Tuple
from matplotlib.patches import Polygon
from mocker import Placer, NotAllowedError
import matplotlib.pyplot as plt

from random import uniform
from shapely.geometry import *
from shapely.ops import unary_union
import math


class MyPlacer(Placer):
    

    def __init__(self, sg : ShapeGenerator):
        """Constructor

        Args:
            sg (ShapeGenerator): ShapeGenerator object, refer to mocker documentation
        """
        super().__init__(sg)
        # count of placed shapes
        self._count = 0


    def run(self):
        """Main placing method. Runs until a shape cannot be placed into circle.
        Until then it continuously places shapes as low as possible. If a rotation
        is specified, it picks the lowest placement over all possible orientations.

        Returns:
            ShapeGenerator: Shape generator object that is filled with placed shapes
        """

        # no rotations
        if self._sg._rotations == 360:
            # loop runs until a shape cannot be placed
            while(True):
                # get new shape and its placements
                poly = self._sg.new_shape()
                lines = self._feasible_placements(Polygon(poly))

                # no placement available
                if not lines:
                    break

                # lowest placement point
                point = self._placer(lines)

                # highest point of polygon
                highp = self._highest_point(poly)

                # vector from highest vertex of polygon to its first
                dist_hp_firstp = (poly[0][0] - highp[0], poly[0][1] - highp[1])\
                
                # place the shape 
                self._sg.place_shape(point[0] + dist_hp_firstp[0], point[1] + dist_hp_firstp[1], 0)
                self._count+=1


        else:
            # loop runs until a shape cannot be placed in any possible orientation
            while(True):
                # get new shape
                poly = self._sg.new_shape()

                can_be_placed = False   # true if shape can be placed in any rotation
                rotation = 0    # current orientation of shape
                point = (0, 100)    # ridiculously high point, will be overriden

                # try all roatations
                for i in range(360//self._sg._rotations):
                    # turn the shape by specified angle, get placements for current orientation
                    poly = self._sg._rotate_shape(poly, self._sg._rotations)
                    lines = self._feasible_placements(Polygon(poly))

                    
                    if not lines:
                        # no placement available, try another rotation
                        continue
                    can_be_placed = True

                    # get lowest placement for curr. orientation
                    pnt = self._placer(lines)

                    if pnt[1] < point[1]:
                        # if lowest placement for curr. orientation is lower than the one for previous orientations
                        point = pnt
                        rotation = i+1  # save the number of rotations of the shape
                    elif pnt[1] == point[1] and pnt[0] < point[0]:
                        # same height but the newer placement is more to the left
                        point = pnt
                        rotation = i+1

                
                if not can_be_placed:
                    # no placement found over all orientations
                    break
                
                # rotate shape into its correct orientation to find vector from first point to highest point
                poly = self._sg._rotate_shape(poly, self._sg._rotations*rotation)
                highp = self._highest_point(poly)
                dist_hp_firstp = (poly[0][0] - highp[0], poly[0][1] - highp[1])

                # place shape 
                self._sg.place_shape(point[0] + dist_hp_firstp[0], point[1] + dist_hp_firstp[1], rotation*self._sg._rotations)
                self._count += 1

        return self._sg


    def _placer(self, lines : List):
        """Finds lowes point out of all possible placements

        Args:
            lines (List(List(Tuple(int, int)))): List of lines along which a shape can be placed

        Returns:
            Tuple(int, int): lowest point out of all lines
        """

        points = []
        for line in lines:
            points.append(self._lowest_point(line))

        return self._lowest_point(points)


    def _feasible_placements(self, polygon : Polygon):
        """Finds lines along which the shape can be placed. A line is where a shape can be placed by
        its highest point so that it touches another shape/the edge of the circle

        An inner-fit polygon(IFP) for the shape and the circle 
        and a no-fit polygon(NFP) for the shape and all currently placed shapes
        are found, then an intersection of the two is constructed.
        Finally, the intersection is stripped of parts that are inside the NFP and
        would result in overlapping

        Args:
            polygon (Polygon): shape to find placement lines

        Returns:
            List(List(Tuple(int, int))): List of lines. A line consists of points representing vertices
        """

        ifp = self._polygon_to_coords(self._inner_fit_circle(polygon).convex_hull)

        # if no shape has been placed yet
        if not self._sg._shapes:
            return [ifp]

        # get NFP
        nfp = self._no_fit_polygons(polygon)

        # intersection of IFP and NFP
        final = nfp.intersection(Polygon(ifp))

        lines = []

        # if the intersection is a has a single exterior
        if isinstance(final, Polygon):
            # removal of IFP part
            line = self._remove_back_parts(final, nfp)
            if line:
                # append non empty lines
                lines.append(line)  
            # add interiors as well
            for interior in final.interiors:
                lines.append(list(interior.coords))
        # if the intersection has multiple exteriors
        elif isinstance(final, MultiPolygon):
            for plgn, plgf in zip(nfp, final):
                # removal of the IFP part
                line = self._remove_back_parts(plgf, plgn)
                if line:
                    # append non empty lines
                    lines.append(line)
                # add interiors as well
                for interior in plgf.interiors:
                    lines.append(list(interior.coords))

        return lines

    def _no_fit_polygons(self, polygon : Polygon):
        """Compute no fit polygon of a new shape and all placed shapes
        by computing no fit polygons for all placed shapes and a new shape
        and then taking their union

        Args:
            polygon (Polygon): new shape

        Returns:
            Polygon: no fit polygon
        """

        nfps = []
        for shape in self._sg._shapes:
            nfps.append(self._fit_nfp(Polygon(shape), self._minkowski_difference(Polygon(shape), polygon)))
        nfp = unary_union(nfps)
        return nfp
        

    def _remove_back_parts(self, isc : Polygon, nfp : Polygon):
        """Removes parts which remain in the intersection of NFP and IFP which belong to inner fit polygon

        Args:
            isc (Polygon): intersection of IFP and NFP
            nfp (Polygon): no fit polygon

        Returns:
            List(Tuple(int, int)): true intersection(points from NFP that are inside of IFP)
        """
        
        # Conversion from Polygon to list of coords
        isc = self._polygon_to_coords(isc)
        nfp = self._polygon_to_coords(nfp)

        true_isc = []

        # Check coords if theyre in true intersection
        for coord in isc:
            # if the coord is a vertex of the NFP
            if coord in nfp:
                true_isc.append(coord)

        return true_isc


    def _inner_fit_circle(self, polygon : Polygon):
        """ Inner fit polygon for circle and a shape to be placed.
            Created by sliding the shape around the circle in a counter-clockwise direction
            The shape is placed by its highest point

        Args:
            polygon (Polygon): input shape to make IFP

        Returns:
            Polygon: IFP
        """

        #orient shape ccw
        polygon,_ = self._orient_shapes(polygon)
        polygon = self._polygon_to_coords(polygon)

        # when polygon collides, change its direction by this angle(degs)
        angle_size = 4  

        # center the polygon, place it by its highest point to (0,0)
        highestp = self._highest_point(polygon)
        dist_hp_firstp = (polygon[0][0] - highestp[0], polygon[0][1] - highestp[1])
        highestp = (0,0)
        polygon = self._sg._translate_shape(polygon, 0 + dist_hp_firstp[0], 0 + dist_hp_firstp[1])

        #place polygon to the edge
        move_vect, intersection = self._slide(polygon, (1,0))
        polygon = self._sg._translate_shape(polygon, 
                    polygon[0][0] + move_vect[0], polygon[0][1] + move_vect[1])
        
        #set up first point of inner fit polygon
        highestp = (highestp[0] + move_vect[0], highestp[1] + move_vect[1])
        inner_fit = [highestp]

        #get starting angle
        move_vect = self._perpendicular_left_vector(intersection)

        for i in range(0, int(math.ceil(360/angle_size))-1):
            move_vect = self._ccw_rotation(move_vect,angle_size)    #get angle of slide
            move_vect,_ = self._slide(polygon, move_vect)   #calculate slide length of polygon
            
            #if the shape can move
            if move_vect[0] != 0 or move_vect[1] != 0:
                #move the polygon
                polygon = self._sg._translate_shape(polygon, polygon[0][0] + move_vect[0], polygon[0][1] + move_vect[1])
                #add inner fit polygon vertex
                highestp = (highestp[0] + move_vect[0], highestp[1] + move_vect[1])     
                inner_fit.append(highestp)
        
        return Polygon(inner_fit)


    def _slide(self, polygon : Polygon, direction : Tuple):
        """returns multiple of direction vector in which the shape can maximally move
        and the point where it "crashes" into wall(IFP)

        Args:
            polygon (Polygon): shape to be slid
            direction (Tuple(int, int)): direction(vector) of shape

        Returns:
            Tuple(int, int): direction vector(its length is the length of the movement)
            Tuple(int, int): final point of the shape's slide(intersection with IFP)
        """

        polygon = self._polygon_to_coords(polygon)
        direction = self._normalize_vector(direction)
        smallest_mult = self._sg._radius*100
        point_of_intersection = (0,0)

        #for each point compute its intersection with circle under given direction
        #solve equation (direction)^2 * k^2 + 2(direction . point)*t + (point)^2 - radius^2
        #take the lowest moving distance so that the polygon stays in the circle
        for point in polygon[:-1]:
            a = self._dot_product(direction, direction)
            b = 2*self._dot_product(direction, point)
            c = self._dot_product(point, point) - self._sg._radius**2
            discriminant = b**2 -4*a*c
            if discriminant >= 0:
                mult = (-b + math.sqrt(discriminant))/(2*a)
                if mult - 0.01 < smallest_mult:
                    smallest_mult = mult-0.01
                    point_of_intersection = (point[0] + direction[0]*mult, point[1] + direction[1]*mult)
        
        return (direction[0]*smallest_mult, direction[1]*smallest_mult), point_of_intersection


    def _ccw_rotation(self, vector : Tuple, degs : int):
        """Rotate a vector counterclockwise

        Args:
            vector (Tuple(int, int)): Vector to be rotated
            degs (int): rotation angle in degs

        Returns:
            Tuple(int, int): Rotated vector
        """

        degs = math.radians(degs)
        return (vector[0]*math.cos(degs) - vector[1]*math.sin(degs), vector[0]*math.sin(degs) + vector[1]*math.cos(degs))


    def _dot_product(self, v1 : Tuple, v2 : Tuple):
        """Dot product of two vectors

        Args:
            v1 (Tuple(int, int)): First vector
            v2 (Tuple(int, int)): Second vector

        Returns:
            int: Dot product of v1 and v2
        """

        return v1[0]*v2[0] + v1[1]*v2[1]


    def _perpendicular_left_vector(self, vector : Tuple):
        """Finds left perpendicular vector

        Args:
            vector (Tuple(int,int)): Input vector

        Returns:
            Tuple(int, int): Left perpendicular vector
        """

        return self._normalize_vector((-vector[1], vector[0]))
            

    def _normalize_vector(self, vector : Tuple):
        """Normalizes a vector

        Args:
            vector (Tuple(int, int)): Vector to be normalized

        Returns:
            Tuple(int, int): Normalized vector
        """

        euc = self._euclidean_dist(vector)
        return (vector[0]/euc, vector[1]/euc)
    

    def _euclidean_dist(self, point : Tuple):
        """Euclidean distance from (0,0)

        Args:
            point (Tuple(int, int)): Point

        Returns:
            int: Euclidean distace of point from (0,0)
        """

        return math.sqrt(point[0]**2 + point[1]**2)


    def _highest_point(self, poly : Polygon):
        """ Finds highest, eventually the highest point which is also the rightest

        Args:
            poly Polygon: Shape

        Returns:
            (int, int): Highest point of shape
        """

        coords = self._polygon_to_coords(poly)

        point = coords[0]

        for p in coords:
            if p[1] > point[1]:
                point = p
            elif p[1] == point[1]:
                if p[0] > point[0]:
                    point = p
        
        return point


    def _fit_nfp(self, poly : Polygon, nfp : List):
        """Fits NFP to an already placed polygon by matching them by their lowest points

        Args:
            poly (Polygon): A shape that is already placed
            nfp (List(Tuple(int, int))): no fit polygon of shape above

        Returns:
            Polygon: placed NFP
        """

        x, y = self._lowest_point(poly)
        return Polygon(self._sg._translate_shape(nfp, x, y))


    def _lowest_point(self, poly : Polygon):
        """ Finds lowest, eventually the lowest point which is also the leftest

        Args:
            poly Polygon: Shape

        Returns:
            (int, int): Lowest point of shape
        """

        coords = self._polygon_to_coords(poly)

        point = coords[0]

        for p in coords:
            if p[1] < point[1]:
                point = p
            elif p[1] == point[1]:
                if p[0] < point[0]:
                    point = p
        
        return point


    def _polygon_to_coords(self, poly : object):
        """Test if shape is an object of type Polygon, if it is, convert it

        Args:
            poly (object): shape object

        Returns:
            list of coords: list of vertices of shape
        """

        if isinstance(poly, Polygon):
            return list(poly.exterior.coords)
        
        return poly
        


    def _minkowski_difference(self, polygonA : Polygon, polygonB : Polygon):
        """NFP of two shapes, shape A is already placed,
        shape B to be placed
        Take edges of both polygons as vectors, order them in asc. order by angle to x-axis
        Construct NFP by placing the vectors in order behind each other

        Args:
            polygonA (Polygon): already placed shape
            polygonB (Polygon): shape to be placed

        Returns:
            list((int, int)): no fit polygon of pA, pB]
        """

        polygonA, polygonB = polygonA.convex_hull, polygonB.convex_hull
        polygonA, polygonB = self._orient_shapes(polygonA, polygonB)

        vectorsA, vectorsB = self._points_to_edges(polygonA), self._points_to_edges(polygonB)

        angles = self._get_angles(vectorsA + vectorsB)

        nfp = [(0,0)]

        for x in range(0,len(angles)-1):
            nfp.append((nfp[x][0] + angles[x][0][0], nfp[x][1] + angles[x][0][1]))

        nfp.append((0,0))

        return nfp


    def _orient_shapes(self, polygonA : Polygon, polygonB=None ):
        """Orient both polygons correctly, A counter-clockwise, B clockwise

        Args:
            polygonA (Polygon): shape to have its coords ordered counter-clockwise
            polygonB (Polygon, optional): shape to have its coords ordered clockwise. Defaults to None.

        Returns:
            Polygon, Polygon: the first has vertices ordered ccw, latter cw
        """

        if not LinearRing(list(polygonA.exterior.coords)).is_ccw:
            polygonA = Polygon((list(polygonA.exterior.coords)[::-1])[:-1])
        if polygonB is not None and LinearRing(list(polygonB.exterior.coords)).is_ccw:
            polygonB = Polygon((list(polygonB.exterior.coords)[::-1])[:-1])
        
        return polygonA, polygonB


    def _points_to_edges(self, polygon : Polygon):
        """Point representation to vector representation of shape

        Args:
            polygon (Polygon): shape

        Returns:
            list((int, int)): List of edges of shape as vectors
        """

        polygon = self._polygon_to_coords(polygon)
        vectors = []
        for i in range(0, len(polygon)-1):
            vectors.append((polygon[i+1][0] - polygon[i][0], polygon[i+1][1] - polygon[i][1]))
        
        return vectors


    def _get_angles(self, polygon_vectors : List):
        """Get angles relative to positive x-axis, sort ascending by angle

        Args:
            polygon_vectors (List(Tuple(int, int))): List of vectors representing edges of shapes

        Returns:
            list((int, int)): Ordered list of vectors by their angles to the x-axis, in asc. order
        """

        angles = []
        for vector in polygon_vectors:
            angles.append([vector, self._angle_x(vector)])
        return sorted(angles, key=lambda x: x[1])


    def _angle_x(self, vector : Tuple):
        """Get angle rel. to x-axis

        Args:
            vector ((int, int)): vector

        Returns:
            int: Angle of vector to positive x-axis
        """

        angle = 0
        if vector[0] == 0:
            if vector[1] > 0:
                return math.pi/2
            return 3/2*math.pi
        else:
            angle = math.atan(vector[1]/vector[0])

        if vector[0] < 0:
            angle += math.pi

        if angle < 0:
            angle += 2*math.pi
        return angle
