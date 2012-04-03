#ifndef MARCHING_TILES_HIRES_H
#define MARCHING_TILES_HIRES_H

#include <array3.h>
#include <hashtable.h>
#include <vec.h>

struct MarchingTilesHiRes
{
    std::vector<Vec3ui> tri;
    std::vector<Vec3d> x;
    std::vector<Vec3d> normal;
    Vec3d origin;
    double dx;
    const Array3d& phi;
    
    MarchingTilesHiRes(const Vec3d &origin_, double dx_, const Array3d& phi_) : 
    tri(0), x(0), normal(0),
    origin(origin_), dx(dx_), phi(phi_),
    edge_cross()
    {}
    
    void contour(void);
    void improve_mesh(void);
    void estimate_normals(void);
    
private:
    HashTable<Vec6i,unsigned int> edge_cross; // stores vertices that have been created already at given edge crossings
    
    double eval(double i, double j, double k); // interpolate if non-integer coordinates given
    void eval_gradient(double i, double j, double k, Vec3d& grad);
    void contour_tile(size_t i, size_t j, size_t k); // add triangles for contour in the given tile (starting at grid point (4*i,4*j,4*k))
    void contour_tet(const Vec3i& x0, const Vec3i& x1, const Vec3i& x2, const Vec3i& x3, double p0, double p1, double p2, double p3);
    int find_edge_cross(const Vec3i& x0, const Vec3i& x1, double p0, double p1);
};

#endif
