#ifndef MAKELEVELSET2_H
#define MAKELEVELSET2_H

#include "array2.h"
#include "vec.h"

// edge is a list of edges in the mesh, and x is the positions of the vertices
void make_level_set2(const std::vector<Vec2ui> &edge, const std::vector<Vec2d> &x,
                     const Vec2d &origin, double dx, int nx, int ny,
                     Array2d &phi);

#endif
