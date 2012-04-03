// ---------------------------------------------------------
//
//  edgecollapser.h
//  Tyson Brochu 2011
//  
//  Functions supporting the "edge collapse" operation: removing short edges from the mesh.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_EDGECOLLAPSER_H
#define EL_TOPO_EDGECOLLAPSER_H

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
typedef Vec<3,size_t> Vec3st;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Edge collapser object.  Removes edges smaller than the specified threshold, optionally scaling measures by mean curvature.
///
// ---------------------------------------------------------

class EdgeCollapser
{
    
public:
    
    /// Edge collapser constructor.  Takes a SurfTrack object and curvature-adaptive parameters.
    ///
    EdgeCollapser( SurfTrack& surf, bool use_curvature, double min_curvature_multiplier );

    /// Collapse all short edges
    ///
    bool collapse_pass();
    
    
    /// Mimimum edge length.  Edges shorter than this will be collapsed.
    ///
    double m_min_edge_length;   
    
    /// Whether to scale by curvature when computing edge lengths, in order to coarsen low-curvature regions
    ///
    bool m_use_curvature;
    
    /// The minimum curvature scaling allowed
    ///
    double m_min_curvature_multiplier;
    
private:
    
    friend class SurfTrack;
    
    /// The mesh this object operates on
    /// 
    SurfTrack& m_surf;

    /// Get all triangles which are incident on either edge end vertex.
    ///
    void get_moving_triangles(size_t source_vertex, 
                              size_t destination_vertex, 
                              std::vector<size_t>& moving_triangles );
    
    
    /// Get all edges which are incident on either edge end vertex.
    ///
    void get_moving_edges(size_t source_vertex, 
                          size_t destination_vertex, 
                          size_t edge_index,
                          std::vector<size_t>& moving_edges );
    
    /// Check the "pseudo motion" introduced by a collapsing edge for collision
    ///
    bool collapse_edge_pseudo_motion_introduces_collision( size_t source_vertex, 
                                                          size_t destination_vertex, 
                                                          size_t edge_index, 
                                                          const Vec3d& vertex_new_position );
    
    /// Determine if the edge collapse operation would invert the normal of any incident triangles.
    ///
    bool collapse_edge_introduces_normal_inversion( size_t source_vertex, 
                                                   size_t destination_vertex, 
                                                   size_t edge_index, 
                                                   const Vec3d& vertex_new_position );
    
    /// Determine whether collapsing an edge will introduce an unacceptable change in volume.
    ///
    bool collapse_edge_introduces_volume_change( size_t source_vertex, 
                                                size_t edge_index, 
                                                const Vec3d& vertex_new_position );   
    
    /// Returns true if the edge collapse would introduce a triangle with a min or max angle outside of the speficied min or max.
    ///
    bool collapse_edge_introduces_bad_angle( size_t source_vertex, 
                                            size_t destination_vertex, 
                                            const Vec3d& vertex_new_position );
    
    /// Delete an edge by moving its source vertex to its destination vertex
    ///
    bool collapse_edge( size_t edge );
    
    /// Determine if the edge should be allowed to collapse
    ///
    bool edge_is_collapsible( size_t edge_index );
    
    
};

#endif


