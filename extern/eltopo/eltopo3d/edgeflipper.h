// ---------------------------------------------------------
//
//  edgeflipper.h
//  Tyson Brochu 2011
//  
//  Functions supporting the "edge flip" operation: replacing non-delaunay edges with their dual edges.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_EDGEFLIPPER_H
#define EL_TOPO_EDGEFLIPPER_H

// ---------------------------------------------------------
//  Nested includes
// ---------------------------------------------------------

#include <cstddef>
#include <vector>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

class SurfTrack;
template<unsigned int N, class T> struct Vec;
typedef Vec<3,double> Vec3d;
typedef Vec<2,size_t> Vec2st;
typedef Vec<3,size_t> Vec3st;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Edge flipper object.  Tries to produce Delaunay mesh by replacing edges with the "opposite" edge in their neighbourhood.
///
// ---------------------------------------------------------

class EdgeFlipper
{
    
public:
    
    /// Constructor
    ///
    EdgeFlipper( SurfTrack& surf, double edge_flip_min_length_change ) :
    m_surf( surf ),
    m_edge_flip_min_length_change( edge_flip_min_length_change )
    {}
    
    /// Flip all non-delaunay edges
    ///
    bool flip_pass();
    
    
private:

    /// The mesh this object operates on
    /// 
    SurfTrack& m_surf;
    
    /// Minimum edge length improvement in order to flip an edge
    ///
    double m_edge_flip_min_length_change;
    
    /// Check whether the new triangles created by flipping an edge introduce any intersection
    ///
    bool flip_introduces_collision(size_t edge_index, 
                                   const Vec2st& new_edge, 
                                   const Vec3st& new_triangle_a, 
                                   const Vec3st& new_triangle_b );
    
    /// Flip an edge: remove the edge and its incident triangles, then add a new edge and two new triangles
    ///
    bool flip_edge( size_t edge, size_t tri0, size_t tri1, size_t third_vertex_0, size_t third_vertex_1 );
    
    
};


#endif
