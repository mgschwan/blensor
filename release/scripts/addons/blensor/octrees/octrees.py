#    Octrees in Python
#    Copyright (C) 2013--14  James Cranch
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
A simple octree library

(C) James Cranch 2013-2014
"""



import heapq

from blensor.octrees.geometry import *
from blensor.octrees.inner.octree_inner import *


class Octree():
    """
    Octrees: efficient data structure for data associated with points
    in 3D space.

    Usage:
        Octree((minx, maxx), (miny, maxy), (minz, maxz))
    creates an empty octree with bounds as given.
    """

    def __init__(self, bounds, tree=Tree.empty()):
        self.bounds = bounds
        self.tree = tree

    def check_bounds(self, p):
        if not point_in_box(p, self.bounds):
            raise KeyError("Point (%s, %s, %s) out of bounds" % p)

    def __len__(self):
        return len(self.tree)

    def __eq__(self, other):
        return self.bounds == other.bounds and self.tree == other.tree

    def __iter__(self):
        return iter(self.tree)

    def copy(self):
        """
        Return a copy of self.

        Since Octree is just a wrapper for a pure data structure, this
        is performed in constant time.
        """
        return Octree(self.bounds, self.tree)

    def get(self, p, default=None):
        """
        Finds the data associated to the point at p.
        """
        if point_in_box(p, self.bounds):
            return self.tree.get(self.bounds, p, default)
        else:
            return default

    def insert(self, p, d):
        """
        Adds a point at p with value d. Raises KeyError if there is
        already a point there (unlike the "update" method).
        """
        self.check_bounds(p)
        self.tree = self.tree.insert(self.bounds, p, d)

    def update(self, p, d):
        """
        Adds a point at p with value d. Overwrites if there is already
        a point there (unlike the "insert" method).
        """
        self.check_bounds(p)
        self.tree = self.tree.update(self.bounds, p, d)

    def remove(self, p):
        """
        Removes the point at p; raises KeyError if there is not such a
        point.
        """
        self.check_bounds(p)
        self.tree = self.tree.remove(self.bounds, p)

    def extend(self, g):
        "Inserts all the points in g."
        for (p, d) in g:
            self.insert(p, d)

    def simple_union(self, other):
        """
        Return the union of two octrees with the same bounds. When
        there are points in both, one will overwrite the other (which
        of the two remain is undefined).
        """
        if self.bounds != other.bounds:
            raise ValueError("Bounds don't agree")
        return Octree(self.bounds, self.tree.union(other.tree, self.bounds))

    def rebound(self, newbounds):
        """
        New version with changed bounds, and with a tree restructured
        accordingly. Drops all points lying outside the new bounds.
        """
        return Octree(newbounds, self.tree.rebound(self.bounds, newbounds))

    def general_union(self, other):
        """
        Return the union of two octrees of arbitrary bounds. When
        there are points in both, one will overwrite the other (which
        of the two remain is undefined).
        """
        x = self
        y = other
        b = union_box(x.bounds, y.bounds)
        if b != x.bounds:
            x = x.rebound(b)
        if b != y.bounds:
            y = y.rebound(b)
        return x.simple_union(y)

    def subset(self, point_fn, box_fn=None):
        """
        Selects a subset of an octree. The function point_fn takes
        coordinates and returns True or False. The function box_fn
        takes coordinates and returns True (if all points in that box
        are in), False (if all points in that box are out), or None
        (if some may be in and some others may be out).

        If box_fn is not given, it defaults to considering point_fn on
        the eight vertices of the box (returning None if they
        disagree).
        """
        if box_fn is None:
            box_fn = lambda b: agreement(point_fn(v) for v in vertices(b))

        return Octree(self.bounds,
                      self.tree.subset(self.bounds, point_fn, box_fn))

    def by_score(self, pointscore, boxscore):
        """
        Iterates through points in some kind of geometric order: for
        example, proximity to a given point.

        Returns tuples of the form (score, coords, value).

        Arguments:

        - pointscore
            A function which associates to coordinates (x, y, z) a
            value, the "score". Lower scores will be returned
            earlier. A score of None is considered infinite: that
            point will not be returned.

        - boxscore
            A function which assigns to a box the lowest possible
            score of any point in that box. Again, a score of None is
            considered infinite: we cannot be interested in any point
            in that box.

        The algorithm maintains a heap of points and boxes in order of
        how promising they are. In particular, if only the earliest
        results are needed, not much extra processing is done.
        """
        l = []
        self.tree.enqueue(l, self.bounds, pointscore, boxscore)

        while len(l) > 0:
            (score, isnode, location, stuff) = heapq.heappop(l)
            if isnode:
                for (b, t) in stuff.children(location):
                    t.enqueue(l, b, pointscore, boxscore)
            else:
                yield (score, location, stuff)

    def by_distance_from_point(self, p, epsilon=None):
        """
        Return points in order of distance from p, in the form
        (distance, coords, value).

        Takes an optional argument epsilon; if this is given, then it
        stops when the distance exceeds epsilon. This is more
        efficient than merely truncating the results.
        """
        if epsilon is None:
            p_fn = lambda q: euclidean_point_point(p, q)
            b_fn = lambda b: euclidean_point_box(p, b)
        else:
            p_fn = lambda q: bounding(euclidean_point_point(p, q), epsilon)
            b_fn = lambda b: bounding(euclidean_point_box(p, b), epsilon)

        for t in self.by_score(p_fn, b_fn):
            yield t

    def by_distance_from_point_rev(self, p):
        """
        Return points in order of distance from p, in the form
        (distance, coords, value), furthest first.
        """
        fp = lambda q: -euclidean_point_point(p, q)
        fb = lambda b: min(-euclidean_point_point(p, q) for q in vertices(b))
        for (d, c, v) in self.by_score(fp, fb):
            yield (-d, c, v)

    def nearest_to_point(self, p):
        """
        Return the nearest point to p, in the form (distance, coords,
        value).
        """
        for t in self.by_distance_from_point(p):
            return t

    def nearest_to_box(self, b):
        """
        Return the nearest point to a box, in the form (distance, coords,
        value).
        """
        for t in self.by_score(lambda p: euclidean_point_box(p, b),
                               lambda b2: euclidean_box_box(b2, b)):
            return t

    def nearest_to_box_far_corner(self, b):
        """
        Return the point which has the lowest maximum distance to a
        box, in the form (distance, coords, value).
        """
        for t in self.by_score(lambda p: euclidean_point_box_max(p, b),
                               lambda b2: euclidean_box_box_minmax(b2, b)):
            return t

    def by_proximity(self, other, epsilon=None):
        """
        Given two octrees, return points from the first which are
        close to some point from the second, in decreasing order of
        proximity.

        Yields tuples of the form (distance, coords1, coords2, data1,
        data2).

        If epsilon is given, then it does not return points further
        apart than epsilon. This can be slightly more efficient than
        simply stopping once the distances exceed epsilon.
        """

        def pointscore(p):
            t = other.nearest_to_point(p)
            if t is None:
                return None
            elif epsilon is not None and t[0] > epsilon:
                return None
            else:
                return t

        def boxscore(b):
            t = other.nearest_to_box(b)
            if t is None:
                return None
            elif epsilon is not None and t[0] > epsilon:
                return None
            else:
                return t
        for ((d, c2, v2), c1, v1) in self.by_score(pointscore, boxscore):
            yield (d, c1, c2, v1, v2)

    def by_isolation(self, other, epsilon=None):
        """
        Given two octrees, return points from the first which are far
        from every point in the second, in increasing order of
        proximity.

        Yields tuples of the form (distance, coords1, coords2, data1,
        data2).

        If epsilon is given, it does not return points that are closer
        than epsilon to the other octree. This is more efficient than
        simply truncating the output.
        """

        def pointscore(p):
            t = other.nearest_to_point(p)
            if t is None:
                return None
            (s, c, v) = t
            if epsilon is not None and s < epsilon:
                return None
            else:
                return (-s, c, v)

        def boxscore(b):
            t = other.nearest_to_box_far_corner(b)
            if t is None:
                return None
            (s, c, v) = t
            if epsilon is not None and s < epsilon:
                return None
            else:
                return (-s, c, v)
        for ((d, c2, v2), c1, v1) in self.by_score(pointscore, boxscore):
            yield (-d, c1, c2, v1, v2)

    def deform(self, point_function, bounds=None, box_function=None):
        """
        Moves all the points according to point_function, assumed to
        be a continuous function.

        It also uses box_function to compute a box bounding the image
        of a given box. If box_function is not given, it assumes that
        the image of boxes is a convex set.

        One can also give explicit bounds, which by default are
        obtained by calling box_function on the existing bounds.

        For large octrees and well-behaved functions, this should be
        significantly faster than repopulating an octree from scratch.
        """

        if box_function is None:
            box_function = lambda b: convex_box_deform(point_function, b)
        if bounds is None:
            bounds = box_function(self.bounds)
        return Octree(bounds,
                      self.tree.deform(self.bounds, bounds,
                                       point_function, box_function))

    def apply_matrix(self, matrix, bounds=None):
        """
        Moves the points according to the given matrix.

        Bounds can be given.
        """
        return self.deform(lambda p: matrix_action(matrix, p), bounds)

    def pairs_by_score(self, other, p_p_score, p_b_score,
                       b_p_score, b_b_score):
        """
        Iterates through pairs of points, one from each of two
        argument octrees.

        This is more elaborate than "by_score" above, but similar in
        many regards. In order to make it efficient, we need to
        provide four scoring functions. The first one scores two
        points, the others give the minimum possible score for a point
        and a box, a box and a point, and a box and a box
        respectively.

        If any scoring functions return None, that is treated as
        infinite: the pairs are not of interest.

        Returns a 5-tuple consisting of: the score, the two sets of
        coordinates, and the data associated to the two points.
        """
        l = []

        def enqueue2(tree1, tree2, bounds1, bounds2):
            if isinstance(tree1, Empty) or isinstance(tree2, Empty):
                pass
            elif isinstance(tree1, Singleton):
                if isinstance(tree2, Singleton):
                    s = p_p_score(tree1.coords, tree2.coords)
                    if s is not None:
                        heapq.heappush(l, (s, False, False,
                                           tree1.coords, tree2.coords,
                                           tree1.data, tree2.data))
                else:
                    s = p_b_score(tree1.coords, bounds2)
                    if s is not None:
                        heapq.heappush(l, (s, False, True, tree1.coords,
                                           bounds2, tree1.data, tree2))
            else:
                if isinstance(tree2, Singleton):
                    s = b_p_score(bounds1, tree2.coords)
                    if s is not None:
                        heapq.heappush(l, (s, True, False, bounds1,
                                           tree2.coords, tree1, tree2.data))
                else:
                    s = b_b_score(bounds1, bounds2)
                    if s is not None:
                        heapq.heappush(l, (s, True, True, bounds1,
                                           bounds2, tree1, tree2))

        enqueue2(self.tree, other.tree, self.bounds, other.bounds)

        while len(l) > 0:
            (score, isnode1, isnode2,
             loc1, loc2, stuff1, stuff2) = heapq.heappop(l)
            if isnode1:
                if isnode2:
                    for (b1, t1) in stuff1.children(loc1):
                        for (b2, t2) in stuff2.children(loc2):
                            enqueue2(t1, t2, b1, b2)
                else:
                    for (b1, t1) in stuff1.children(loc1):
                        enqueue2(t1, Tree.singleton(loc2, stuff2), b1, None)
            else:
                if isnode2:
                    for (b2, t2) in stuff2.children(loc2):
                        enqueue2(Tree.singleton(loc1, stuff1), t2, None, b2)
                else:
                    yield (score, loc1, loc2, stuff1, stuff2)

    def pairs_by_distance(self, other, epsilon):
        """
        Returns pairs within epsilon of each other, one from each
        octree. Returns them in increasing order of distance.
        """
        pp = lambda p1, p2: bounding(euclidean_point_point(p1, p2), epsilon)
        bp1 = lambda p, b: bounding(euclidean_point_box(p, b), epsilon)
        bp2 = lambda b, p: bounding(euclidean_point_box(p, b), epsilon)
        bb = lambda b1, b2: bounding(euclidean_box_box(b1, b2), epsilon)
        for t in self.pairs_by_score(other, pp, bp1, bp2, bb):
            yield t

    def pairs_generate(self, other, p_p_fn,
                       p_b_fn=None, b_p_fn=None, b_b_fn=None):
        """
        Yields pairs of points satisfying some criterion.

        Requires four functions: p_p_fn which takes values either
        True or False to say whether a pair should be yielded. The
        others act on boxes, and may return True ("everything is of
        interest"), False ("nothing is of interest") or None ("maybe
        some things are and some things aren't").

        If the later functions are not given, they default to
        considering all vertices.
        """
        if p_b_fn is None:
            p_b_fn = lambda p, b: agreement(p_p_fn(p, q)
                                            for q in vertices(b))
        if b_p_fn is None:
            b_p_fn = lambda b, p: agreement(p_p_fn(q, p)
                                            for q in vertices(b))
        if b_b_fn is None:
            b_b_fn = lambda b1, b2: agreement(p_b_fn(p, b2)
                                              for p in vertices(b1))

        def inner(tree1, tree2, bounds1, bounds2):
            x = b_b_fn(bounds1, bounds2)
            if x is True:
                for (c1, v1) in tree1:
                    for (c2, v2) in tree2:
                        yield (c1, c2, v1, v2)
            elif x is False:
                pass
            elif isinstance(tree1, Empty):
                pass
            elif isinstance(tree2, Empty):
                pass
            elif isinstance(tree1, Singleton):
                c1 = tree1.coords
                v1 = tree1.data
                for (c2, v2) in tree2.subset(bounds2,
                                             lambda p: p_p_fn(c1, p),
                                             lambda b: p_b_fn(c1, b)):
                    yield (c1, c2, v1, v2)
            elif isinstance(tree2, Singleton):
                c2 = tree2.coords
                v2 = tree2.data
                for (c1, v1) in tree1.subset(bounds1,
                                             lambda p: p_p_fn(p, c2),
                                             lambda b: b_p_fn(b, c2)):
                    yield (c1, c2, v1, v2)
            else:
                for (b1, t1) in tree1.children(bounds1):
                    for (b2, t2) in tree2.children(bounds2):
                        for t in inner(t1, t2, b1, b2):
                            yield t
        for t in inner(self.tree, other.tree, self.bounds, other.bounds):
            yield t

    def pairs_nearby(self, other, epsilon):
        """
        Generates pairs within epsilon of each other, in any order.
        """
        def p_p_fn(p1, p2):
            return euclidean_point_point(p1, p2) < epsilon

        def p_b_fn(p, b):
            if euclidean_point_box(p, b) < epsilon:
                if euclidean_point_box_max(p, b) < epsilon:
                    return True
                else:
                    return None
            else:
                return False

        def b_p_fn(b, p):
            if euclidean_point_box(p, b) < epsilon:
                if euclidean_point_box_max(p, b) < epsilon:
                    return True
                else:
                    return None
            else:
                return False

        def b_b_fn(b1, b2):
            if euclidean_box_box(b1, b2) < epsilon:
                if euclidean_box_box_max(b1, b2) < epsilon:
                    return True
                else:
                    return None
            else:
                return False

        for t in self.pairs_generate(other, p_p_fn, p_b_fn, b_p_fn, b_b_fn):
            yield t
