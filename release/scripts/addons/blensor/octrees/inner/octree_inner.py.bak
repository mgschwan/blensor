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
The core functionality: a purely functional implementation. We have
this two-layer setup so that octree nodes do not have to store their
own bounds.

Also, people used to python expect mutable data structures; mutability
is most easily provided using a wrapper.

The user should probably not ever want to import or use this code
directly.

(C) James Cranch 2013-2014
"""

from __future__ import division

import heapq

from octrees.geometry import *


class Tree():

    def smartnode(self, data):
        if len(data) != 8:
            (((a, b), (c, d)), ((e, f), (g, h))) = data
            data = [a, b, c, d, e, f, g, h]
        singleton = None
        for x in data:
            if isinstance(x, Node):
                return self.node(data)
            elif isinstance(x, Singleton):
                if singleton is not None:
                    return self.node(data)
                else:
                    singleton = x
        if singleton is not None:
            return singleton
        else:
            return self.empty()


class Empty(Tree):

    def __init__(self):
        pass

    def __iter__(self):
        return
        yield

    def __len__(self):
        return 0

    def __eq__(self, other):
        return isinstance(other, Empty)

    def __hash__(self):
        return hash((self.empty,))

    def get(self, bounds, coords, default):
        return default

    def insert(self, bounds, coords, data):
        return self.singleton(coords, data)

    def update(self, bounds, coords, data):
        return self.singleton(coords, data)

    def remove(self, bounds, coords):
        raise KeyError("Removing non-existent point")

    def subset(self, bounds, point_fn, box_fn):
        return self

    def enqueue(self, heap, bounds, pointscore, boxscore):
        pass

    def union(self, other, bounds, swapped=False):
        return other

    def rebound(self, oldbounds, newbounds):
        return self

    def deform(self, oldbounds, newbounds, point_fn, box_fn):
        return self

Tree.empty = Empty


class Singleton(Tree):

    def __init__(self, coords, data):
        self.coords = coords
        self.data = data

    def __len__(self):
        return 1

    def __iter__(self):
        yield (self.coords, self.data)

    def __eq__(self, other):
        return (isinstance(other, Singleton)
                and self.coords == other.coords
                and self.data == other.data)

    def __hash__(self):
        return hash((self.singleton, coords, data))

    def get(self, bounds, coords, default):
        if self.coords == coords:
            return self.data
        else:
            return default

    def insert(self, bounds, coords, data):
        if self.coords == coords:
            raise KeyError("Key (%s,%s,%s) already present" % (self.coords))
        else:
            return self.node().insert(bounds, self.coords,
                                      self.data).insert(bounds, coords, data)

    def update(self, bounds, coords, data):
        if self.coords == coords:
            return self.singleton(coords, data)
        else:
            return self.node().insert(bounds, self.coords,
                                      self.data).insert(bounds, coords, data)

    def remove(self, bounds, coords):
        if self.coords == coords:
            return self.empty()
        else:
            raise KeyError("Removing non-existent point")

    def subset(self, bounds, point_fn, box_fn):
        if point_fn(self.coords):
            return self
        else:
            return self.empty()

    def enqueue(self, heap, bounds, pointscore, boxscore):
        s = pointscore(self.coords)
        if s is not None:
            heapq.heappush(heap, (s, False, self.coords, self.data))

    def union(self, other, bounds, swapped=False):
        return other.update(bounds, self.coords, self.data)

    def rebound(self, oldbounds, newbounds):
        if point_in_box(self.coords, newbounds):
            return self
        else:
            return self.empty()

    def deform(self, oldbounds, newbounds, point_fn, box_fn):
        coords = point_fn(self.coords)
        if point_in_box(coords, newbounds):
            return self.singleton(coords, self.data)
        else:
            return self.empty()

Tree.singleton = Singleton


class Node(Tree):

    def __init__(self, content=None):
        """
        Takes either a list of eight octrees, or generators of two
        nested three deep.
        """
        if content is None:
            content = [self.empty()]*8
        if len(content) == 8:
            (a, b, c, d, e, f, g, h) = content
            self.content = (((a, b), (c, d)), ((e, f), (g, h)))
        else:
            self.content = tuple(tuple(tuple(b) for b in a) for a in content)

    def __len__(self):
        return sum(sum(sum(len(x) for x in b) for b in a)
                   for a in self.content)

    def __iter__(self):
        for x in self.content:
            for y in x:
                for z in y:
                    for t in iter(z):
                        yield t

    def __eq__(self, other):
        return (isinstance(other, Node)
                and self.content_array() == other.content_array())

    def __hash__(self):
        return hash((self.node, content))

    def content_array(self):
        return [[list(b) for b in a] for a in self.content]

    def get(self, bounds, coords, default):
        ((r, s, t), newbounds) = narrow(bounds, coords)
        return self.content_array()[r][s][t].get(newbounds, coords, default)

    def insert(self, bounds, coords, data):
        a = self.content_array()
        ((r, s, t), newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].insert(newbounds, coords, data)
        return self.node(a)

    def update(self, bounds, coords, data):
        a = self.content_array()
        ((r, s, t), newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].update(newbounds, coords, data)
        return self.node(a)

    def remove(self, bounds, coords):
        a = self.content_array()
        ((r, s, t), newbounds) = narrow(bounds, coords)
        a[r][s][t] = a[r][s][t].remove(newbounds, coords)
        return self.smartnode(a)

    def children_no_bounds(self):
        for u in self.content:
            for v in u:
                for w in v:
                    yield w

    def children(self, bounds):
        for (b, x) in zip(subboxes(bounds), self.children_no_bounds()):
            yield (b, x)

    def subset(self, bounds, point_fn, box_fn):
        x = box_fn(bounds)
        if x is None:
            return self.smartnode(list(t.subset(b, point_fn, box_fn)
                                       for (b, t) in self.children(bounds)))
        elif x:
            return self
        else:
            return self.empty()

    def enqueue(self, heap, bounds, pointscore, boxscore):
        s = boxscore(bounds)
        if s is not None:
            heapq.heappush(heap, (s, True, bounds, self))

    def union(self, other, bounds, swapped=False):
        if swapped:
            return self.node([x.union(y, b)
                              for (x, y, b) in zip(self.children_no_bounds(),
                                                   other.children_no_bounds(),
                                                   subboxes(bounds))])
        else:
            return other.union(self, bounds, swapped=True)

    def rebound(self, oldbounds, newbounds):
        if box_contains(oldbounds, newbounds):
            return self.node([self.rebound(oldbounds, b)
                              for b in subboxes(newbounds)])
        elif boxes_disjoint(oldbounds, newbounds):
            return self.empty()
        else:
            return reduce(lambda x, y: x.union(y, newbounds),
                          (x.rebound(b, newbounds)
                           for (b, x) in self.children(oldbounds)))

    def deform(self, oldbounds, newbounds, point_fn, box_fn):
        if box_contains(oldbounds, newbounds):
            return self.node([self.deform(oldbounds, b, point_fn, box_fn)
                              for b in subboxes(newbounds)])
        elif boxes_disjoint(box_fn(oldbounds), newbounds):
            return self.empty()
        else:
            return reduce(lambda x, y: x.union(y, newbounds),
                          (x.deform(b, newbounds, point_fn, box_fn)
                           for (b, x) in self.children(oldbounds)))

Tree.node = Node
