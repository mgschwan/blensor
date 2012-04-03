// ---------------------------------------------------------
//
//  meshmerger.h
//  Tyson Brochu 2011
//  
//  Search for mesh edges which are near to each other, zipper their neighbouring triangles together.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_MESHMERGER_H
#define EL_TOPO_MESHMERGER_H

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
typedef Vec<3,size_t> Vec3st;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Pair of proximal edges, sortable by distance.  Used to build a list of edge pairs in ascending order of proximity, so we can 
/// handle them from nearest to farthest.
///
// ---------------------------------------------------------

struct SortableEdgeEdgeProximity
{
    /// Constructor
    /// 
    SortableEdgeEdgeProximity( size_t a, size_t b, double d ) :
    edge_a( a ),
    edge_b( b ),
    distance( d )
    {}
    
    /// Edges indices
    ///
    size_t edge_a, edge_b;
    
    /// Distance between the two edges
    /// 
    double distance;
    
    /// Comparison operator for this class, compares edge-edge distance for each pair
    /// 
    bool operator<( const SortableEdgeEdgeProximity& other ) const
    {
        return distance < other.distance;
    }
    
};

// ---------------------------------------------------------
///
/// Mesh merger object.  Sweeps over all pairs of edges, attempting to merge the surface when nearby edges are found.
///
// ---------------------------------------------------------

class MeshMerger
{
    
public:
    
    /// Constructor
    /// 
    MeshMerger( SurfTrack& surf ) :
    m_surf( surf )
    {}
    
    /// Look for pairs of edges close to each other, attempting to merge when close edges are found.
    ///
    bool merge_pass();
    
    
private:

    /// The mesh this object operates on
    /// 
    SurfTrack& m_surf;
    
    /// Move vertices around so v[0] and v[4] are closest together
    ///
    void twist_vertices( size_t *zipper_vertices );
    
    /// Create a set of triangles to add to perform the zippering operation
    ///
    bool get_zipper_triangles( size_t edge_index_0, size_t edge_index_1, std::vector<Vec3st>& output_triangles );
    
    /// Check whether the introduction of the new zippering triangles causes a collision 
    ///
    bool zippering_introduces_collision( const std::vector<Vec3st>& new_triangles, const std::vector<size_t>& deleted_triangles );
    
    /// Attempt to merge between two edges
    ///    
    bool zipper_edges( size_t edge_index_a, size_t edge_index_b );
    
};


#endif
