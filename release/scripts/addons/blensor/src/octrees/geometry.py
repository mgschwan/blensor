"""
Some supporting 3D geometric code

(C) James Cranch 2013-2014
"""


from math import sqrt


def bounding(x, e):
    if x > e:
        return None
    else:
        return x


def agreement(g):
    "Do all these booleans agree? If so, on what?"
    prejudice = None
    for b in g:
        if b is None:
            return None
        if prejudice is (not b):
            return None
        prejudice = b
    return prejudice


def centroid(b):
    "The centroid of box b"
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b
    return ((minx+maxx)/2, (miny+maxy)/2, (minz+maxz)/2)


def box_volume(b):
    "The volume of box b"
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b
    return (maxx-minx)*(maxy-miny)*(maxz-minz)


def point_in_box(p, b):
    "Is p in b?"
    (x, y, z) = p
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b
    return (minx <= x < maxx) and (miny <= y < maxy) and (minz <= z < maxz)


def box_contains(b1, b2):
    "Is all of b1 in b2?"
    ((minx1, maxx1), (miny1, maxy1), (minz1, maxz1)) = b1
    ((minx2, maxx2), (miny2, maxy2), (minz2, maxz2)) = b2
    return (minx2 <= minx1 and maxx1 <= maxx2
            and miny2 <= miny1 and maxy1 <= maxy2
            and minz2 <= minz1 and maxz1 <= maxz2)


def boxes_disjoint(b1, b2):
    "Are b1 and b2 disjoint?"
    ((minx1, maxx1), (miny1, maxy1), (minz1, maxz1)) = b1
    ((minx2, maxx2), (miny2, maxy2), (minz2, maxz2)) = b2
    return (maxx2 <= minx1 or maxx1 <= minx2
            or maxy2 <= miny1 or maxy1 <= miny2
            or maxz2 <= minz1 or maxz1 <= minz2)


def union_box(b1, b2):
    "The smallest box containing b1 and b2"
    ((minx1, maxx1), (miny1, maxy1), (minz1, maxz1)) = b1
    ((minx2, maxx2), (miny2, maxy2), (minz2, maxz2)) = b2
    return ((min(minx1, minx2), max(maxx1, maxx2)),
            (min(miny1, miny2), max(maxy1, maxy2)),
            (min(minz1, minz2), max(maxz1, maxz2)))


def vertices(bounds):
    "The vertices of a box"
    (xs, ys, zs) = bounds
    for x in xs:
        for y in ys:
            for z in zs:
                yield (x, y, z)


def subboxes(bounds):
    "The eight boxes contained within a box"
    ((minx, maxx), (miny, maxy), (minz, maxz)) = bounds
    midx = (maxx+minx)/2
    midy = (maxy+miny)/2
    midz = (maxz+minz)/2
    for bx in [(minx, midx), (midx, maxx)]:
        for by in [(miny, midy), (midy, maxy)]:
            for bz in [(minz, midz), (midz, maxz)]:
                yield (bx, by, bz)


def narrow(bounds, coords):
    "Narrow down a box to an appropriate subbox"

    ((minx, maxx), (miny, maxy), (minz, maxz)) = bounds

    midx = (maxx+minx)/2
    midy = (maxy+miny)/2
    midz = (maxz+minz)/2

    (x, y, z) = coords

    if x < midx:
        r = 0
        newx = (minx, midx)
    else:
        r = 1
        newx = (midx, maxx)
    if y < midy:
        s = 0
        newy = (miny, midy)
    else:
        s = 1
        newy = (midy, maxy)
    if z < midz:
        t = 0
        newz = (minz, midz)
    else:
        t = 1
        newz = (midz, maxz)

    return ((r, s, t), (newx, newy, newz))


def euclidean_point_point(p, q):
    "The euclidean distance between points p and q"
    (x1, y1, z1) = p
    (x2, y2, z2) = q
    return sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)


def nearest_point_in_box(p, b):
    "Returns the nearest point in a box b to a point p"
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b
    (x, y, z) = p
    if x < minx:
        x0 = minx
    elif x < maxx:
        x0 = x
    else:
        x0 = maxx
    if y < miny:
        y0 = miny
    elif y < maxy:
        y0 = y
    else:
        y0 = maxy
    if z < minz:
        z0 = minz
    elif z < maxz:
        z0 = z
    else:
        z0 = maxz
    return (x0, y0, z0)


def furthest_point_in_box(p, b):
    "Returns the furthest point in a box b to a point p"
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b
    (x, y, z) = p
    if 2*x > minx+maxx:
        x0 = minx
    else:
        x0 = maxx
    if 2*y > miny+maxy:
        y0 = miny
    else:
        y0 = maxy
    if 2*z > minz+maxz:
        z0 = minz
    else:
        z0 = maxz
    return (x0, y0, z0)


def euclidean_point_box(p, b):
    "The euclidean distance between p and a box b"
    return euclidean_point_point(p, nearest_point_in_box(p, b))


def euclidean_point_box_max(p, b):
    "The furthest distance between p and a box b"
    return euclidean_point_point(p, furthest_point_in_box(p, b))


def euclidean_box_box(b1, b2):
    "The euclidean distance between two boxes"
    ((minx1, maxx1), (miny1, maxy1), (minz1, maxz1)) = b1
    ((minx2, maxx2), (miny2, maxy2), (minz2, maxz2)) = b2
    if maxx1 < minx2:
        x = minx2 - maxx1
    elif maxx2 < minx1:
        x = minx1 - maxx2
    else:
        x = 0
    if maxy1 < miny2:
        y = miny2 - maxy1
    elif maxy2 < miny1:
        y = miny1 - maxy2
    else:
        y = 0
    if maxz1 < minz2:
        z = minz2 - maxz1
    elif maxz2 < minz1:
        z = minz1 - maxz2
    else:
        z = 0
    return sqrt(x*x+y*y+z*z)


def euclidean_box_box_max(b1, b2):
    "The maximum distance between two boxes"
    ((minx1, maxx1), (miny1, maxy1), (minz1, maxz1)) = b1
    ((minx2, maxx2), (miny2, maxy2), (minz2, maxz2)) = b2
    x = max(maxx2-minx1, maxx1-minx2)
    y = max(maxy2-miny1, maxy1-miny2)
    z = max(maxz2-minz1, maxz1-minz2)
    return sqrt(x*x+y*y+z*z)


def euclidean_box_box_minmax(b1, b2):
    """
    The minimum over all points in b1 of the maximum over all points
    in b2 of the distance.
    """
    p = nearest_point_in_box(centroid(b2), b1)
    return euclidean_point_box_max(p, b2)


def convex_box_deform(f, b):
    """
    Given a function f taking points to points, and a box b, returns
    the box containing f applied to the vertices of b.
    """
    l = [f(p) for p in vertices(b)]
    minx = min(q[0] for q in l)
    maxx = max(q[0] for q in l)
    miny = min(q[1] for q in l)
    maxy = max(q[1] for q in l)
    minz = min(q[2] for q in l)
    maxz = max(q[2] for q in l)
    return ((minx, maxx), (miny, maxy), (minz, maxz))


def matrix_action(m, p):
    return tuple(sum(m[i][j]*p[j] for j in range(3)) for i in range(3))


def line_segment_intersects_box(p, q, b):
    """
    Does the line segment between p and q intersect the box b?
    """
    (px, py, pz) = p
    (qx, qy, qz) = q
    ((minx, maxx), (miny, maxy), (minz, maxz)) = b

    # Do the x coordinates overlap the box? If not, can stop, if so,
    # can trim the line to the box by x coordinate.
    if qx < px:
        (px, py, pz, qx, qy, qz) = (qx, qy, qz, px, py, pz)
    if qx < minx or maxx < px:
        return False
    if px < minx:
        l = (minx-px)/(qx-px)
        px = (1-l)*px + l*qx
        py = (1-l)*py + l*qy
        pz = (1-l)*pz + l*qz
    if maxx < qx:
        l = (maxx-px)/(qx-px)
        qx = (1-l)*px + l*qx
        qy = (1-l)*py + l*qy
        qz = (1-l)*pz + l*qz

    # Do the y coordinates overlap the box? If not, can stop, if so,
    # can trim the line to the box by y coordinate.
    if qy < py:
        (px, py, pz, qx, qy, qz) = (qx, qy, qz, px, py, pz)
        print("swapping; p = %s, q = %s" % ((px, py, pz), (qx, qy, qz)))
    if qy < miny or maxy < py:
        return False
    if py < miny:
        l = (miny-py)/(qy-py)
        px = (1-l)*px + l*qx
        py = (1-l)*py + l*qy
        pz = (1-l)*pz + l*qz
    if maxy < qy:
        l = (maxy-py)/(qy-py)
        qx = (1-l)*px + l*qx
        qy = (1-l)*py + l*qy
        qz = (1-l)*pz + l*qz

    # Now just look at the z coordinates.
    if qz < pz:
        (px, py, pz, qx, qy, qz) = (qx, qy, qz, px, py, pz)
    if qz < minz or maxz < pz:
        return False
    else:
        return True


def line_intersects_box(a, v, b):
    """
    Does the line a+rv meet the box b?
    """
    mins = []
    maxs = []
    for (ac, vc, ec) in zip(a, v, b):
        ec1, ec2 = ec
        if vc == 0:
            if not(min(ec1, ec2) <= ac <= max(ec1, ec2)):
                return False
        else:
            r, s = (ec1-ac)/vc, (ec2-ac)/vc
            mins.append(min(r, s))
            maxs.append(max(r, s))
    return max(mins) <= min(maxs)


def halfline_intersects_box(a, v, b):
    """
    Does the halfline a+rv with r positive meet the box b?
    """
    mins = []
    maxs = []
    for (ac, vc, ec) in zip(a, v, b):
        ec1, ec2 = ec
        if vc == 0:
            if not(min(ec1, ec2) <= ac <= max(ec1, ec2)):
                return False
        else:
            r, s = (ec1-ac)/vc, (ec2-ac)/vc
            mins.append(min(r, s))
            maxs.append(max(r, s))
    return max(mins) <= min(maxs) and 0 <= min(maxs)


def box_intersects_plane(b, f):
    """
    Does the box b intersect the plane defined by f(x)=0?
    """
    return (any(f(p) >= 0 for p in vertices(b))
            and any(f(q) <= 0 for q in vertices(b)))
