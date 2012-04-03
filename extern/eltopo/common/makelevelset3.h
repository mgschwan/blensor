#ifndef MAKELEVELSET3_H
#define MAKELEVELSET3_H

#include <array3.h>
#include <vec.h>

// TODO: make 32/64 bit agnostic

// tri is a list of triangles in the mesh, and x is the positions of the vertices
// absolute distances will be nearly correct for triangle soup, but a closed mesh is
// needed for accurate signs. Distances for all grid cells within exact_band cells of
// a triangle should be exact; further away a distance is calculated but it might not
// be to the closest triangle - just one nearby.

void make_level_set3(const std::vector<Vec3st> &tri, const std::vector<Vec3d> &x,
                     const Vec3d &origin, double dx, int ni, int nj, int nk,
                     Array3d &phi, Array3i& closest_tri, const int exact_band );


inline void make_level_set3(const std::vector<Vec3st> &tri, const std::vector<Vec3d> &x,
                            const Vec3d &origin, double dx, int ni, int nj, int nk,
                            Array3d &phi, const int exact_band )
{
    Array3i ignore;
    make_level_set3( tri, x, origin, dx, ni, nj, nk, phi, ignore, exact_band );
}

#endif
