// ---------------------------------------------------------
//
//  meshsmoother.h
//  Tyson Brochu 2011
//  
//  Functions related to the tangent-space mesh smoothing operation.
//
// ---------------------------------------------------------


#ifndef EL_TOPO_MESHSMOOTHER_H
#define EL_TOPO_MESHSMOOTHER_H

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
/// Mesh smoother object.  Performs NULL-space constrained Laplacian smoothing of mesh vertices.
///
// ---------------------------------------------------------

class MeshSmoother
{
    
public:
    
    /// Constructor
    ///
    MeshSmoother( SurfTrack& surf ) :
    m_surf( surf )
    {}
    
    /// NULL-space smoothing of all vertices
    ///
    bool null_space_smoothing_pass( double dt );
    
    /// Compute the maximum timestep that will not invert any triangle normals, using a quadratic solve as in [Jiao 2007].
    ///
    static double compute_max_timestep_quadratic_solve( const std::vector<Vec3st>& tris, 
                                                       const std::vector<Vec3d>& positions, 
                                                       const std::vector<Vec3d>& displacements, 
                                                       bool verbose );   
    
    /// Find a new vertex location using NULL-space smoothing
    ///
    void null_space_smooth_vertex( size_t v, 
                                  const std::vector<double>& triangle_areas, 
                                  const std::vector<Vec3d>& triangle_normals, 
                                  const std::vector<Vec3d>& triangle_centroids, 
                                  Vec3d& displacement ) const;      
    
private:
    
    /// The mesh this object operates on
    /// 
    SurfTrack& m_surf;
    
};

#endif

