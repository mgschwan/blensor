
// ---------------------------------------------------------
//
//  surftrack.h
//  Tyson Brochu 2008
//  
//  The SurfTrack class: a dynamic mesh with topological changes and mesh maintenance operations.
//
// ---------------------------------------------------------

#ifndef SURFTRACK_H
#define SURFTRACK_H

#include <dynamicsurface.h>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

typedef std::vector<unsigned int> TriangleSet;
class SubdivisionScheme;

// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Structure for setting up a SurfTrack object with some initial parameters.  This is passed to the SurfTrack constructor.
///
// ---------------------------------------------------------

struct SurfTrackInitializationParameters
{

   /// Set default values for parameters which are not likely to be specified
   SurfTrackInitializationParameters();

   /// Elements closer than this are considered "near" (or proximate)
   double m_proximity_epsilon;
   
   double m_min_triangle_area;
         
   /// Collision epsilon to use during mesh improvment operations (i.e. if any mesh elements are closer than this, the operation is 
   /// aborted).  NOTE: This should be greater than collision_epsilon, to prevent improvement operations from moving elements into 
   /// a collision configuration.
   double m_improve_collision_epsilon;
   
   /// Whether to set the min and max edge lengths as fractions of the initial average edge length
   bool m_use_fraction;
   
   /// If use_fraction is true, these are taken to be fractions of the average edge length of the new surface.
   /// If use_fraction is false, these are absolute.
   double m_min_edge_length;
   double m_max_edge_length; 
   double m_max_volume_change;
   
   /// Minimum edge length improvement in order to flip an edge
   double m_edge_flip_min_length_change;
   
   /// Elements within this distance will trigger a merge attempt   
   double m_merge_proximity_epsilon;
   
   /// Type of subdivision to use when collapsing or splitting (butterfly, quadric error minimization, etc.)
   SubdivisionScheme *m_subdivision_scheme;   
   
   /// Whether to enforce collision-free surfaces (including during mesh maintenance operations)
   bool m_collision_safety;
   
   /// Whether to allow changes in topology
   bool m_allow_topology_changes;

   /// Whether to allow mesh improvement
   bool m_perform_improvement;

};

// ---------------------------------------------------------
///
/// Used to build a list of edges sorted in order of increasing length.
/// 
// ---------------------------------------------------------
struct SortableEdge
{
   unsigned int edge_index;
   double edge_length;
   
   SortableEdge( unsigned int ei, double el ) : edge_index(ei), edge_length(el) {}
   
   bool operator<( const SortableEdge& other ) const
   {
      return (this->edge_length < other.edge_length);
   }
};

// ---------------------------------------------------------
///
/// Pair of proximal edges, sortable by distance.  Used to build a list of edge pairs in ascending order of proximity, so we can 
/// handle them from nearest to farthest.
///
// ---------------------------------------------------------
struct SortableEdgeEdgeProximity
{
   SortableEdgeEdgeProximity( unsigned int a, unsigned int b, double d ) :
   edge_a( a ),
   edge_b( b ),
   distance( d )
   {}
   
   unsigned int edge_a;
   unsigned int edge_b;
   double distance;
   
   bool operator<( const SortableEdgeEdgeProximity& other ) const
   {
      return distance < other.distance;
   }
};


// ---------------------------------------------------------
///
/// A DynamicSurface with topological and mesh maintenance operations.
///
// ---------------------------------------------------------

class SurfTrack : public DynamicSurface
{
   
public:
       
   /// Rendering options
   ///
   static const unsigned int RENDER_EDGES = 1;
   static const unsigned int RENDER_TRIANGLES = 2;
   static const unsigned int RENDER_VERTEX_DATA = 4;
   static const unsigned int RENDER_COLLIDING_TRIANGLES = 8;
   static const unsigned int NO_SHADING = 16;
   static const unsigned int TWO_SIDED = 32;


   /// Create a SurfTrack object from a set of vertices and triangles using the specified paramaters
   ///
   SurfTrack( const std::vector<Vec3d>& vs, 
              const std::vector<Vec3ui>& ts, 
              const std::vector<double>& masses,
              const SurfTrackInitializationParameters& initial_parameters );

   
   ~SurfTrack();
   
private:
   
   // Disallow copying and assignment by declaring private
   //
   SurfTrack( const SurfTrack& );
   SurfTrack& operator=( const SurfTrack& );
   
   
public:
   
   /// Display the surface in OpenGL using the specified options
   ///
   void render( unsigned int options = RENDER_EDGES | RENDER_TRIANGLES );

   /// Ray cast into the scene, return index of the closest primitive of the type specified
   ///
   enum { RAY_HIT_VERTEX, RAY_HIT_EDGE, RAY_HIT_TRIANGLE, RAY_HIT_NOTHING };
   unsigned int ray_cast( const Vec3f& ray_origin, const Vec3f& ray_direction, unsigned int primitive_type, unsigned int& hit_index );      

   /// advance one time step (just calls the version in DynamicSurface)
   ///
   inline void integrate(double dt);
   
   /// run mesh maintenance operations
   ///
   void improve_mesh( );

   /// run edge-edge merging
   ///
   void topology_changes( );
   
   // ---------------------------------------------------------
   // mesh maintenance operations
   // ---------------------------------------------------------
      
   /// Split an edge, using subdivision_scheme to determine the new vertex location, if safe to do so.
   ///
   bool split_edge( unsigned int edge );
   
   /// Split all long edges
   ///
   bool split_pass();
   
   /// Delete an edge by moving its source vertex to its destination vertex
   ///
   bool collapse_edge(unsigned int edge );
   
   /// Collapse all short edges
   ///
   bool collapse_pass();
   
   /// Flip an edge: remove the edge and its incident triangles, then add a new edge and two new triangles
   ///
   bool flip_edge(unsigned int edge, unsigned int tri0, unsigned int tri1, unsigned int third_vertex_0, unsigned int third_vertex_1 );
   
   /// Flip all non-delaunay edges
   ///
   bool flip_pass();
   
   /// Find a new vertex location using NULL-space smoothing
   ///
   void null_space_smooth_vertex( unsigned int v, 
                                  const std::vector<double>& triangle_areas, 
                                  const std::vector<Vec3d>& triangle_normals, 
                                  const std::vector<Vec3d>& triangle_centroids, 
                                  Vec3d& displacement ) const;      
         
   /// NULL-space smoothing of all vertices
   ///
   bool null_space_smoothing_pass( double dt );


   // ---------------------------------------------------------
   // topological merging
   // ---------------------------------------------------------
   
   /// Attempt to merge between two edges
   ///
   bool zipper_edges(unsigned int edge0, unsigned int edge1);   
      
   /// Zipper nearby edges together
   ///
   bool merge_pass();
         
   // ---------------------------------------------------------
   // mesh cleanup
   // ---------------------------------------------------------
   
   /// Check for and delete flaps and zero-area triangles among the given triangle indices, then separate singular vertices.
   ///
   void trim_non_manifold( const std::vector<unsigned int>& triangle_indices );
   
   /// Check for and delete flaps and zero-area triangles among *all* triangles, then separate singular vertices.
   ///
   inline void trim_non_manifold();
   
   /// Find vertices with disconnected neighbourhoods, and pull them apart
   ///
   void separate_singular_vertices();

   // ---------------------------------------------------------
   // collision queries
   // ---------------------------------------------------------
      
   void assert_no_degenerate_triangles();
   
   // ---------------------------------------------------------
   // mesh maintenance helpers
   // ---------------------------------------------------------
      
   // split
   bool split_edge_pseudo_motion_introduces_collision( const Vec3d& new_vertex_position, 
                                                       const Vec3d& new_vertex_smooth_position, 
                                                       unsigned int edge,
                                                       unsigned int tri0, 
                                                       unsigned int tri1,
                                                       unsigned int vertex_a,
                                                       unsigned int vertex_b,
                                                       unsigned int vertex_c,
                                                       unsigned int vertex_d );
   	
   // collapse
   bool check_triangle_vs_triangle_collision( const Vec3ui& triangle_a, const Vec3ui& triangle_b );
   bool collapse_edge_pseudo_motion_introduces_collision( unsigned int source_vertex, 
                                                          unsigned int destination_vertex, 
                                                          unsigned int edge_index, const 
                                                          Vec3d& vertex_new_position );
   
   bool collapse_edge_introduces_normal_inversion( unsigned int source_vertex, 
                                                   unsigned int destination_vertex, 
                                                   unsigned int edge_index, 
                                                   const Vec3d& vertex_new_position );
   
   bool collapse_edge_introduces_volume_change( unsigned int source_vertex, 
                                                unsigned int edge_index, 
                                                const Vec3d& vertex_new_position );   
   
   // flip
   bool flip_introduces_collision( unsigned int edge_index, 
                                   const Vec2ui& new_edge, 
                                   const Vec3ui& new_triangle_a, 
                                   const Vec3ui& new_triangle_b );
      
   // zipper
   void twist_vertices( unsigned int *zipper_vertices );
   bool get_zipper_triangles( unsigned int edge_index_0, unsigned int edge_index_1, std::vector<Vec3ui>& output_triangles );
   bool zippering_introduces_collision( const std::vector<Vec3ui>& new_triangles, const std::vector<unsigned int>& deleted_triangles );
   bool get_vertex_triangle_zipper_triangles( unsigned int v, unsigned int t, std::vector<Vec3ui>& new_triangles );   
   bool stitch_triangle_triangle( unsigned int ta, unsigned int tb, std::vector<Vec3ui>& new_tris );

   
   /// Delete flaps and zero-area triangles
   unsigned int get_common_edge( unsigned int triangle_a, unsigned int triangle_b );
   bool triangles_are_adjacent( unsigned int triangle_a, unsigned int triangle_b );
   void partition_vertex_neighbourhood( unsigned int vertex_index, std::vector< TriangleSet >& connected_components );
   bool pull_apart_vertex( unsigned int vertex_index, const std::vector< TriangleSet >& connected_components );

   
   // ---------------------------------------------------------
   // Member variables
   // ---------------------------------------------------------
   
   /// Collision epsilon to use during mesh improvment operations
   double m_improve_collision_epsilon;
   
   /// Minimum edge length improvement in order to flip an edge
   double m_edge_flip_min_length_change;
   
   /// Maximum volume change allowed when flipping or collapsing an edge
   double m_max_volume_change;
   
   /// Mimimum edge length.  Edges shorter than this will be collapsed.
   double m_min_edge_length;   

   /// Maximum edge length.  Edges longer than this will be subdivided.
   double m_max_edge_length;   
  
   /// Elements within this distance will trigger a merge attempt
   double m_merge_proximity_epsilon;
   
   // Try to prevent triangles with area less than this
   double m_min_triangle_area;

   /// Interpolation scheme, determines edge midpoint location
   SubdivisionScheme *m_subdivision_scheme;
   bool should_delete_subdivision_scheme_object;
   
   /// Triangles which are involved in connectivity changes which may introduce degeneracies
   std::vector<unsigned int> m_dirty_triangles;
   
   /// Whether to allow merging and separation
   bool m_allow_topology_changes;
   
   /// Whether to perform adaptivity operations
   bool m_perform_improvement;
      
};

// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Advance mesh by one time step (just calls through to DynamicSurface).
///
// ---------------------------------------------------------

inline void SurfTrack::integrate(double dt)
{       
   DynamicSurface::integrate(dt);
}

// --------------------------------------------------------
///
/// Determine if two triangles are adjacent (if they share an edge)
///
// --------------------------------------------------------

inline bool SurfTrack::triangles_are_adjacent( unsigned int triangle_a, unsigned int triangle_b )
{
   return ( get_common_edge( triangle_a, triangle_b ) != (unsigned int) ~0 );
}


// ---------------------------------------------------------
///
/// Search the entire mesh for non-manifold elements and remove them
/// NOTE: SHOULD USE THE VERSION THAT ACCEPTS A SET OF TRIANGLE INDICES INSTEAD.
///
// ---------------------------------------------------------

inline void SurfTrack::trim_non_manifold()
{
  
   std::vector<unsigned int> triangle_indices;
   triangle_indices.resize( m_mesh.m_tris.size() );
   for ( unsigned int i = 0; i < triangle_indices.size(); ++i )
   {
      triangle_indices[i] = i;
   }
   
   trim_non_manifold( triangle_indices );
}

#endif
