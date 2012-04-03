// ---------------------------------------------------------
//
//  surftrack.h
//  Tyson Brochu 2008
//  
//  The SurfTrack class: a dynamic mesh with topological changes and mesh maintenance operations.
//
// ---------------------------------------------------------

#ifndef EL_TOPO_SURFTRACK_H
#define EL_TOPO_SURFTRACK_H

#include <dynamicsurface.h>
#include <edgecollapser.h>
#include <edgeflipper.h>
#include <edgesplitter.h>
#include <meshmerger.h>
#include <meshpincher.h>
#include <meshsmoother.h>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

class SubdivisionScheme;
typedef std::vector<size_t> TriangleSet;

// ---------------------------------------------------------
//  Class definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Structure for setting up a SurfTrack object with some initial parameters.  This is passed to the SurfTrack constructor.
///
// ---------------------------------------------------------

struct SurfTrackInitializationParameters
{
    
    ///  Constructor. Sets default values for parameters which are not likely to be specified.
    ///
    SurfTrackInitializationParameters();
    
    /// Elements closer than this are considered "near" (or proximate)
    ///
    double m_proximity_epsilon;
    
    /// Coefficient of friction to apply during collisions
    ///
    double m_friction_coefficient;
    
    /// Smallest triangle area to allow
    ///
    double m_min_triangle_area;
    
    /// Collision epsilon to use during mesh improvment operations (i.e. if any mesh elements are closer than this, the operation is 
    /// aborted).  NOTE: This should be greater than collision_epsilon, to prevent improvement operations from moving elements into 
    /// a collision configuration.
    ///
    double m_improve_collision_epsilon;
    
    /// Whether to set the min and max edge lengths as fractions of the initial average edge length
    ///
    bool m_use_fraction;
    
    // If use_fraction is true, the following three values are taken to be fractions of the average edge length of the new surface.
    // If use_fraction is false, these are absolute.
    
    /// Smallest edge length allowed
    ///
    double m_min_edge_length;
    
    /// Longest edge length allowed
    ///
    double m_max_edge_length; 
    
    /// Maximum change in volume allowed for one operation
    ///
    double m_max_volume_change;
    
    /// Smallest interior angle at a triangle vertex allowed
    ///
    double m_min_triangle_angle;
    
    /// Largest interior angle at a triangle vertex allowed
    ///
    double m_max_triangle_angle;   
    
    /// Whether to scale by curvature when computing edge lengths, in order to refine high-curvature regions
    ///
    bool m_use_curvature_when_splitting;

    /// Whether to scale by curvature when computing edge lengths, in order to coarsen low-curvature regions
    ///
    bool m_use_curvature_when_collapsing;
    
    /// The minimum curvature scaling allowed
    ///
    double m_min_curvature_multiplier;
    
    /// The maximum curvature scaling allowed
    ///
    double m_max_curvature_multiplier;
    
    /// Whether to allow vertices to move during improvement
    ///
    bool m_allow_vertex_movement;
    
    /// Minimum edge length improvement in order to flip an edge
    //
    double m_edge_flip_min_length_change;
    
    /// Elements within this distance will trigger a merge attempt   
    ///
    double m_merge_proximity_epsilon;
    
    /// Type of subdivision to use when collapsing or splitting (butterfly, quadric error minimization, etc.)
    ///
    SubdivisionScheme *m_subdivision_scheme;   
    
    /// Whether to enforce collision-free surfaces (including during mesh maintenance operations)
    ///
    bool m_collision_safety;
    
    /// Whether to allow changes in topology
    ///
    bool m_allow_topology_changes;
    
    /// Whether to allow non-manifold (edges incident on more than two triangles)
    ///
    bool m_allow_non_manifold;
    
    /// Whether to allow mesh improvement
    ///
    bool m_perform_improvement;
    
};

// ---------------------------------------------------------
///
/// Used to build a list of edges sorted in order of increasing length.
/// 
// ---------------------------------------------------------

struct SortableEdge
{    
    /// Constructor
    ///
    SortableEdge( size_t ei, double el ) : 
    m_edge_index(ei), 
    m_edge_length(el) 
    {}
    
    /// Comparison operator for sorting
    ///
    bool operator<( const SortableEdge& other ) const
    {
        return (this->m_edge_length < other.m_edge_length);
    }
    
    /// The index of the edge
    ///
    size_t m_edge_index;
    
    /// The stored edge length
    ///
    double m_edge_length;

};


// ---------------------------------------------------------
///
/// Keeps track of a vertex removal or addition.  If it's an addition, it also points to the edge that was split to create it.
///
// ---------------------------------------------------------

struct VertexUpdateEvent
{
    /// Constructor
    ///
    VertexUpdateEvent(bool is_remove = false, 
                      size_t vertex_index = (size_t)~0, 
                      const Vec2st& split_edge = Vec2st((size_t)~0) ) :
    m_is_remove( is_remove ),
    m_vertex_index( vertex_index ),
    m_split_edge( split_edge )
    {}
    
    /// Tag for identifying a vertex removal
    ///
    static const bool VERTEX_REMOVE = true;
    
    /// Tag for identifying a vertex addition
    ///
    static const bool VERTEX_ADD = false;
    
    /// Wether this event is a vertex removal
    ///
    bool m_is_remove;
    
    /// The index of the vertex being added or removed
    ///
    size_t m_vertex_index;   
    
    /// If this is a vertex addition due to edge splitting, the edge that was split
    ///
    Vec2st m_split_edge;
    
};


// ---------------------------------------------------------
///
/// Keeps track of a triangle removal or addition. If addition, contains the three vertices that form the new triangle.
///
// ---------------------------------------------------------

struct TriangleUpdateEvent
{
    /// Constructor
    ///
    TriangleUpdateEvent(bool is_remove = false, 
                        size_t triangle_index = (size_t)~0, 
                        const Vec3st& triangle = Vec3st((size_t)~0) ) :
    m_is_remove( is_remove ),
    m_triangle_index( triangle_index ),
    m_tri( triangle )
    {}
    
    /// Tag for identifying a triangle removal
    ///
    static const bool TRIANGLE_REMOVE = true;
    
    /// Tag for identifying a triangle addition
    ///
    static const bool TRIANGLE_ADD = false;
    
    /// Wether this event is a triangle removal
    ///
    bool m_is_remove;
    
    /// The index of the triangle being added or removed
    ///
    size_t m_triangle_index;  
    
    /// If this is a triangle addition, the triangle added
    ///
    Vec3st m_tri;
    
};


// ---------------------------------------------------------
///
/// A DynamicSurface with topological and mesh maintenance operations.
///
// ---------------------------------------------------------

class SurfTrack : public DynamicSurface
{
    
public:
    
    /// Create a SurfTrack object from a set of vertices and triangles using the specified paramaters
    ///
    SurfTrack(const std::vector<Vec3d>& vs, 
              const std::vector<Vec3st>& ts, 
              const std::vector<double>& masses,
              const SurfTrackInitializationParameters& initial_parameters );
    
    /// Destructor
    ///
    ~SurfTrack();
    
private:
    
    /// Disallow copying and assignment by declaring private
    ///
    SurfTrack( const SurfTrack& );
    
    /// Disallow copying and assignment by declaring private
    ///
    SurfTrack& operator=( const SurfTrack& );
    
    
public:
    
    //
    // Mesh bookkeeping
    //
    
    /// Add a triangle to the surface.  Update the underlying TriMesh and acceleration grid. 
    ///
    size_t add_triangle(const Vec3st& t);
    
    /// Remove a triangle from the surface.  Update the underlying TriMesh and acceleration grid. 
    ///
    void remove_triangle(size_t t);  
    
    /// Add a vertex to the surface.  Update the acceleration grid. 
    ///
    size_t add_vertex( const Vec3d& new_vertex_position, double new_vertex_mass );
    
    /// Remove a vertex from the surface.  Update the acceleration grid. 
    ///
    void remove_vertex(size_t v);
    
    /// Remove deleted vertices and triangles from the mesh data structures
    ///
    void defrag_mesh();

    //
    // Main operations
    //
    
    /// Run mesh maintenance operations
    ///
    void improve_mesh( );
    
    /// Run edge-edge merging
    ///
    void topology_changes( );
    
    //
    // Mesh cleanup
    //
    
    /// Check for and delete flaps and zero-area triangles among the given triangle indices, then separate singular vertices.
    ///
    void trim_non_manifold( std::vector<size_t>& triangle_indices );
    
    /// Check for and delete flaps and zero-area triangles among *all* triangles, then separate singular vertices.
    ///
    inline void trim_non_manifold();
    
    /// Fire an assert if any degenerate triangles or tets (flaps) are found.
    /// 
    void assert_no_degenerate_triangles();
    
    //
    // Member variables
    //
    
    /// Edge collapse operation object
    ///
    EdgeCollapser m_collapser;
    
    /// Edge split operation object
    ///
    EdgeSplitter m_splitter;
    
    /// Edge flip operation object
    ///
    EdgeFlipper m_flipper;
    
    /// NULL-space surface smoothing
    /// 
    MeshSmoother m_smoother;
    
    /// Surface merging object
    ///
    MeshMerger m_merger;
    
    /// Surface splitting operation object
    ///
    MeshPincher m_pincher;
    
    /// Collision epsilon to use during mesh improvment operations
    ///
    double m_improve_collision_epsilon;
    
    /// Minimum edge length improvement in order to flip an edge
    ///
    double m_edge_flip_min_length_change;
    
    /// Maximum volume change allowed when flipping or collapsing an edge
    ///
    double m_max_volume_change;
    
    /// Mimimum edge length.  Edges shorter than this will be collapsed.
    ///
    double m_min_edge_length;   
    
    /// Maximum edge length.  Edges longer than this will be subdivided.
    ///
    double m_max_edge_length;   
    
    /// Elements within this distance will trigger a merge attempt
    ///
    double m_merge_proximity_epsilon;
    
    /// Try to prevent triangles with area less than this
    ///
    double m_min_triangle_area;
    
    /// Don't create triangles with angles less than this.  If angles less than this do exist, try to remove them.
    ///
    double m_min_triangle_angle;
    
    /// Don't create triangles with angles greater than this.  If angles greater than this do exist, try to remove them.
    ///
    double m_max_triangle_angle;
    
    /// Interpolation scheme, determines edge midpoint location
    ///
    SubdivisionScheme *m_subdivision_scheme;
    
    /// If we allocate our own SubdivisionScheme object, we must delete it in this object's deconstructor.
    ///
    bool should_delete_subdivision_scheme_object;
    
    /// Triangles which are involved in connectivity changes which may introduce degeneracies
    ///
    std::vector<size_t> m_dirty_triangles;
    
    /// Whether to allow merging and separation
    ///
    bool m_allow_topology_changes;
    
    /// Whether to allow non-manifold (edges incident on more than two triangles)
    ///
    bool m_allow_non_manifold;
    
    /// Whether to perform adaptivity operations
    ///
    bool m_perform_improvement;
    
    /// When doing mesh optimization, whether to allow the vertices to move.  If set to false, we allow edge flipping, edge 
    /// splitting, and edge collapsing (where the edge is collapsed down to one of its endpoints).  If true, we do mesh smoothing,
    /// as well as allowing a collapsed edge to collapse down to some point other than an endpoint.
    ///
    bool m_allow_vertex_movement;
        
    /// History of vertex removal or addition events
    ///
    std::vector<VertexUpdateEvent> m_vertex_change_history;
    
    /// History of triangle removal or addition events
    ///    
    std::vector<TriangleUpdateEvent> m_triangle_change_history;
    
    /// Map of triangle indices, mapping pre-defrag triangle indices to post-defrag indices
    ///
    std::vector<Vec2st> m_defragged_triangle_map;
    
    /// Map of vertex indices, mapping pre-defrag vertex indices to post-defrag indices
    ///
    std::vector<Vec2st> m_defragged_vertex_map;
    
};

// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Search the entire mesh for non-manifold elements and remove them
/// NOTE: SHOULD USE THE VERSION THAT ACCEPTS A SET OF TRIANGLE INDICES INSTEAD.
///
// ---------------------------------------------------------

inline void SurfTrack::trim_non_manifold()
{
    
    std::vector<size_t> triangle_indices;
    triangle_indices.resize( m_mesh.num_triangles() );
    for ( size_t i = 0; i < triangle_indices.size(); ++i )
    {
        triangle_indices[i] = i;
    }
    
    trim_non_manifold( triangle_indices );
}

#endif

