#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 20:56:13 2017

@author: anne
"""
import numpy as np

machineEpsilon = np.finfo(float).eps

def ray_triangle_intersection(ray_near, ray_dir, v1, v2, v3):
    """
    Möller–Trumbore intersection algorithm in pure python
    Based on http://en.wikipedia.org/wiki/M%C3%B6ller%E2%80%93Trumbore_intersection_algorithm
    
    Implementation taken from https://github.com/kliment/Printrun/blob/master/printrun/stltool.py
    
    """
    rows = 1
    if len(v1.shape) == 2:
        rows = v1.shape[1]
    
    invalids = np.ones ((rows), dtype=np.bool)
    eps = machineEpsilon
    edge1 = v2 - v1
    edge2 = v3 - v1
    pvec = np.cross(ray_dir, edge2)
    det = edge1.dot(pvec)
    if abs(det) < eps:
        return False, None
    inv_det = 1. / det
    tvec = ray_near - v1
    u = tvec.dot(pvec) * inv_det
    if u < 0. or u > 1.:
        return False, None
    qvec = numpy.cross(tvec, edge1)
    v = ray_dir.dot(qvec) * inv_det
    if v < 0. or u + v > 1.:
        return False, None

    t = edge2.dot(qvec) * inv_det
    if t < eps:
        return False, None

    return True, t

#def closest_triangle_intersection(origin, ray_dir, triangles):
    

