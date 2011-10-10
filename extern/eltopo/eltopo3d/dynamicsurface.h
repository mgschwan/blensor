
// ---------------------------------------------------------
//
//  dynamicsurface.h
//  Tyson Brochu 2008
//  
//  A triangle mesh with associated vertex locations and 
//  velocities.  Functions for collision detection and solving.
//
// ---------------------------------------------------------

#ifndef DYNAMICSURFACE_H
#define DYNAMICSURFACE_H

// ---------------------------------------------------------
// Nested includes
// ---------------------------------------------------------

#include <deque>
#include <map>

#include <mat.h>
#include <nondestructivetrimesh.h>
#include <ccd_wrapper.h>

// ---------------------------------------------------------
//  Forwards and typedefs
// ---------------------------------------------------------

// Broad-phase collision detector.  Avoids performing collision detection between far-away primitives
class BroadPhase;

// Computes the quadric metric tensor at a vertex
// TODO: Move this into a utility class or something
void compute_quadric_metric_tensor( const std::vector<Vec3d>& triangle_normals, 
                                    const std::vector<double>& triangle_areas, 
                                    const std::vector<unsigned int>& incident_triangles,
                                    Mat33d& quadric_metric_tensor );


// A potentially colliding pair of primitives.  Each pair is a triple of unsigned ints:
//  elements 0 and 1 are the indices of the primitives involved.
//  element 2 specifies if the potential collision is point-triangle or edge-edge
typedef std::deque<Vec3ui> CollisionCandidateSet;


// ---------------------------------------------------------
//  Interface declarations
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// A collision between a triangle and a vertex or between two edges
///
// --------------------------------------------------------

struct Collision
{
   
   Collision( bool in_is_edge_edge, const Vec4ui& in_vertex_indices, const Vec3d& in_normal, const Vec4d& in_alphas, double in_relative_displacement ) :
      is_edge_edge( in_is_edge_edge ),
      vertex_indices( in_vertex_indices ),
      normal( in_normal ),
      alphas( in_alphas ),
      relative_displacement( in_relative_displacement )
   {
      if ( !is_edge_edge ) { assert( in_alphas[0] == 1.0 ); }
   }

   // One or more vertices is shared between this Collision and other
   inline bool overlap_vertices( const Collision& other ) const;
   
   // ALL vertices are shared between this Collision and other
   inline bool same_vertices( const Collision& other ) const;
   
   // Are the two elements both edges
   bool is_edge_edge;
   
   // Which vertices are involved in the collision
   Vec4ui vertex_indices;
   
   // Collision normal
   Vec3d normal;
   
   // Barycentric coordinates of the point of intersection
   Vec4d alphas;
   
   // Magnitude of relative motion over the timestep
   double relative_displacement;
   
};

// --------------------------------------------------------
///
/// Used in the simultaneous handling of collisions: a set of connected elements which are in collision
///
// --------------------------------------------------------

struct ImpactZone
{
   ImpactZone() :
      collisions(),
      all_solved( false )
   {}
   
   // Get the set of all vertices in this impact zone
   void get_all_vertices( std::vector<unsigned int>& vertices ) const;
      
   // Whether this ImpactZones shares vertices with other
   bool share_vertices( const ImpactZone& other ) const;

   // Set of collisions with connected vertices
   std::vector<Collision> collisions;  
   
   // Whether all collisions in this zone have been solved (i.e. no longer colliding)
   bool all_solved;
   
};




// --------------------------------------------------------
///
/// A surface mesh.  Essentially consists of a NonDestructiveTriMesh object coupled with a set of vertex locations in 3D space.
///
// --------------------------------------------------------

class DynamicSurface
{

public:
 
   DynamicSurface( const std::vector<Vec3d>& vs, 
                   const std::vector<Vec3ui>& ts, 
                   const std::vector<double>& masses,
                   double in_proximity_epsilon = 1e-4,
                   bool in_collision_safety = true,
                   bool in_verbose = false );

   virtual ~DynamicSurface(); 
   
private:
   
   // Disallowed, do not implement
   DynamicSurface( const DynamicSurface& );
   DynamicSurface& operator=( const DynamicSurface& );
   
public:
   
   // ---------------------------------------------------------
   // Simulation step

   /// (Implemented in SurfTrack)
   /// 
   virtual void improve_mesh( ) {}

   /// Advance from current state to collision-free state as close as possible to predicted state.
   /// 
   virtual void integrate(double dt);
   
   // ---------------------------------------------------------
   // Mesh bookkeeping

   unsigned int add_triangle(const Vec3ui& t);
   void remove_triangle(unsigned int t);  

   unsigned int add_vertex( const Vec3d& new_vertex_position, 
                            const Vec3d& new_vertex_velocity, 
                            double new_vertex_mass );
   
   void remove_vertex(unsigned int v);

   void clear_deleted_vertices( );

   // ---------------------------------------------------------
   // Utility

   inline double get_triangle_area(unsigned int tri) const;
   inline double get_triangle_area(const Vec3ui& tri) const;
   inline double get_triangle_area(unsigned int v0, unsigned int v1, unsigned int v2) const;

   inline double get_min_triangle_area( unsigned int& triangle_index ) const;
   inline double get_min_triangle_area( ) const;
   
   inline Vec3d get_triangle_normal(unsigned int tri) const;
   inline Vec3d get_triangle_normal(const Vec3ui& tri) const;
   inline Vec3d get_triangle_normal(unsigned int v0, unsigned int v1, unsigned int v2) const;
   
   // Return the rank of the eigenspace of the quadric metric tensor at vertex v
   unsigned int classify_vertex( unsigned int v );

   inline Vec3d get_vertex_normal( unsigned int vertex ) const;
   inline Vec3d get_vertex_normal_max( unsigned int vertex_index ) const;
   
   inline double get_edge_length( unsigned int edge_index ) const;
   inline double get_average_edge_length() const;
   inline double get_average_non_solid_edge_length() const;

   /// Determine volume IDs for all vertices
   void partition_surfaces( std::vector<unsigned int>& surface_ids, std::vector< std::vector< unsigned int> >& surfaces ) const;
   
   static double compute_max_timestep_quadratic_solve( const std::vector<Vec3ui>& tris, 
                                                       const std::vector<Vec3d>& positions, 
                                                       const std::vector<Vec3d>& displacements, 
                                                       bool verbose );
   
   inline double get_surface_area( ) const;
   inline double get_predicted_surface_area() const;
   
   inline double get_volume() const;
   inline double get_predicted_volume() const;
   
   void get_triangle_intersections( const Vec3d& segment_point_a, 
                                    const Vec3d& segment_point_b,
                                    std::vector<double>& hit_ss,
                                    std::vector<unsigned int>& hit_triangles ) const;
   
   unsigned int get_number_of_triangle_intersections( const Vec3d& segment_point_a, 
                                                      const Vec3d& segment_point_b ) const;
   
   unsigned int get_number_of_triangle_intersections_exact( const Vec3d& segment_point_a, 
                                                            const Vec3d& segment_point_b ) const;

   double distance_to_surface( const Vec3d& p, unsigned int& closest_triangle );
   bool point_is_inside( const Vec3d& p );
   
   
   // ---------------------------------------------------------
   // Proximity / collision detection and resolution

   void apply_edge_edge_impulse( const Vec2ui& e0, const Vec2ui& e1, double s0, double s2, Vec3d& direction, double magnitude);
   void apply_triangle_point_impulse(const Vec3ui& t, unsigned int v, double s1, double s2, double s3, Vec3d& direction, double magnitude);

   void handle_triangle_point_proximities( double dt );
   void handle_edge_edge_proximities( double dt );

   void add_point_candidates(unsigned int v, CollisionCandidateSet& collision_candidates);  
   void add_edge_candidates(unsigned int e, CollisionCandidateSet& collision_candidates);
   void add_triangle_candidates(unsigned int t, CollisionCandidateSet& collision_candidates);
   void add_point_update_candidates(unsigned int v, CollisionCandidateSet& collision_candidates);
   
   // Impulse-based collision resolution on individual collisions [Bridson 2002]
   // return true if we think we've handled all collisions
   bool handle_collisions(double dt);

   // run one sweep of collision handling, considering only collisions between movable vertices and nonmovable triangles
   void handle_point_vs_solid_triangle_collisions( double dt );
      
   // ---------------------------------------------------------
   // Simulataneous collision detection [Harmon et al. 2008]
   
   // detect all collisions
   bool detect_collisions( std::vector<Collision>& collisions );
   
   // detect collisions among vertices present in impact_zones
   void detect_new_collisions( const std::vector<ImpactZone> impact_zones, std::vector<Collision>& collisions );

   // merge impact zones with common vertices
   void merge_impact_zones( std::vector<ImpactZone>& impact_zones, std::vector<ImpactZone>& new_impact_zones );
   
   // iteratively run collision detection and inelastic projection on an active set of collisions
   bool iterated_inelastic_projection( ImpactZone& iz, double dt );

   // attempt to set normal velocity to zero for all collisions in the impact zone
   bool inelastic_projection( const ImpactZone& iz );
  
   // detect and solve all collisions
   bool handle_collisions_simultaneous(double dt);
   
   // ---------------------------------------------------------
   // Rigid Impact Zones [BFA 2002]

   bool collision_solved( const Collision& collision );
   
   bool new_rigid_impact_zones(double dt);
   
   void calculate_rigid_motion( double dt, std::vector<unsigned int>& vs );
   
   std::vector<unsigned int> merge_impact_zones( std::vector<unsigned int>& zones, 
                                                 unsigned int z0, 
                                                 unsigned int z1, 
                                                 unsigned int z2, 
                                                 unsigned int z3 );
   
   // ---------------------------------------------------------
   // Broadphase

   void rebuild_static_broad_phase( );
   void rebuild_continuous_broad_phase( );

   void update_static_broad_phase( unsigned int vertex_index );
   void update_continuous_broad_phase( unsigned int vertex_index );  
   
   void vertex_static_bounds(unsigned int v, Vec3d &xmin, Vec3d &xmax) const;
   void edge_static_bounds(unsigned int e, Vec3d &xmin, Vec3d &xmax) const;
   void triangle_static_bounds(unsigned int t, Vec3d &xmin, Vec3d &xmax) const; 
   
   void vertex_continuous_bounds(unsigned int v, Vec3d &xmin, Vec3d &xmax) const;
   void edge_continuous_bounds(unsigned int e, Vec3d &xmin, Vec3d &xmax) const;
   void triangle_continuous_bounds(unsigned int t, Vec3d &xmin, Vec3d &xmax) const;

   // ---------------------------------------------------------
   // Intersection detection 
   
   bool check_triangle_vs_all_triangles_for_intersection( unsigned int tri_index );
   bool check_triangle_vs_all_triangles_for_intersection( const Vec3ui& tri );
      
   void assert_mesh_is_intersection_free( bool degeneracy_counts_as_intersection = false );             // uses m_positions
   void assert_predicted_mesh_is_intersection_free();    // uses m_newpositions

   // ---------------------------------------------------------
   // Data members
      
   // Elements closer than this are proximal
   double m_proximity_epsilon;

   // Dump lots of details to stdout
   bool m_verbose;
   
   // Ensure that no mesh elements intersect, during mesh moving and mesh maintenance
   bool m_collision_safety;
   
   // Vertex positions, predicted locations, velocities and masses
   std::vector<Vec3d> m_positions, m_newpositions, m_velocities;
   std::vector<double> m_masses;

   // The mesh "graph"
   NonDestructiveTriMesh m_mesh;

   // collision acceleration structures
   BroadPhase* m_broad_phase;
      
   // TEMP:
   unsigned int m_num_collisions_this_step;
   unsigned int m_total_num_collisions;
};

// ---------------------------------------------------------
//  Inline functions
// ---------------------------------------------------------

// --------------------------------------------------------
///
/// Determine if another collision has any vertices in common with this collision.
///
// --------------------------------------------------------

inline bool Collision::overlap_vertices( const Collision& other ) const
{
   for ( unsigned short i = 0; i < 4; ++i )
   {
      if ( vertex_indices[i] == other.vertex_indices[0] || 
           vertex_indices[i] == other.vertex_indices[1] || 
           vertex_indices[i] == other.vertex_indices[2] || 
           vertex_indices[i] == other.vertex_indices[3] )
      {
         return true;
      }
   }
   
   return false;
}

// --------------------------------------------------------
///
/// Determine if another collision has all the same vertices as this collision.
///
// --------------------------------------------------------

inline bool Collision::same_vertices( const Collision& other ) const
{
   bool found[4];
   for ( unsigned short i = 0; i < 4; ++i )
   {
      if ( vertex_indices[i] == other.vertex_indices[0] || 
          vertex_indices[i] == other.vertex_indices[1] || 
          vertex_indices[i] == other.vertex_indices[2] || 
          vertex_indices[i] == other.vertex_indices[3] )
      {
         found[i] = true;
      }
      else
      {
         found[i] = false;
      }
   }
   
   return ( found[0] && found[1] && found[2] && found[3] );
}

// --------------------------------------------------------
///
/// Extract the set of all vertices in all collisions in an ImpactZone
///
// --------------------------------------------------------

inline void ImpactZone::get_all_vertices( std::vector<unsigned int>& vertices ) const
{
   vertices.clear();
   for ( unsigned int i = 0; i < collisions.size(); ++i )
   {
      add_unique( vertices, collisions[i].vertex_indices[0] );
      add_unique( vertices, collisions[i].vertex_indices[1] );
      add_unique( vertices, collisions[i].vertex_indices[2] );
      add_unique( vertices, collisions[i].vertex_indices[3] );
   }
}


// --------------------------------------------------------
///
/// Determine whether another ImpactZone shares any vertices with this ImpactZone
///
// --------------------------------------------------------

inline bool ImpactZone::share_vertices( const ImpactZone& other ) const
{
   for ( unsigned int i = 0; i < collisions.size(); ++i )
   {
      for ( unsigned int j = 0; j < other.collisions.size(); ++j )
      {
         if ( collisions[i].overlap_vertices( other.collisions[j] ) )
         {
            return true;
         }
      }
   }
   
   return false;
}


// --------------------------------------------------------
///
/// Add a collision to the list
///
// --------------------------------------------------------

inline void add_to_collision_candidates( CollisionCandidateSet& collision_candidates, const Vec3ui& new_collision )
{  
   collision_candidates.push_back( new_collision );
   return;   
}


// --------------------------------------------------------
///
/// Compute area of a triangle specified by three vertices
///
// --------------------------------------------------------

inline double triangle_area( const Vec3d& v0, const Vec3d &v1, const Vec3d &v2 )
{
   return 0.5 * mag( cross( v1 - v0, v2 - v0 ) );
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a triangle index
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(unsigned int tri) const
{
   const Vec3ui &t = m_mesh.m_tris[tri]; 
   return get_triangle_area(t[0], t[1], t[2]);
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a triple of vertex indices
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(const Vec3ui& tri) const
{
   return get_triangle_area(tri[0], tri[1], tri[2]);
}

// --------------------------------------------------------
///
/// Compute area of a triangle specified by a three vertex indices
///
// --------------------------------------------------------

inline double DynamicSurface::get_triangle_area(unsigned int v0, unsigned int v1, unsigned int v2) const
{
   const Vec3d &p0 = m_positions[v0];
   const Vec3d &p1 = m_positions[v1];
   const Vec3d &p2 = m_positions[v2];
   
   return 0.5 * mag(cross(p1-p0, p2-p0));
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by three vertices
///
// --------------------------------------------------------

inline Vec3d triangle_normal( const Vec3d& v0, const Vec3d &v1, const Vec3d &v2 )
{
   Vec3d u = v1 - v0;
   Vec3d v = v2 - v0;
   return normalized(cross(u, v));
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by a triangle index
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(unsigned int tri) const
{
   const Vec3ui &t = m_mesh.m_tris[tri]; 
   return get_triangle_normal(t[0], t[1], t[2]);
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by a triple of vertex indices
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(const Vec3ui& tri) const
{
   return get_triangle_normal(tri[0], tri[1], tri[2]);
}

// --------------------------------------------------------
///
/// Compute the normal of a triangle specified by three vertex indices
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_triangle_normal(unsigned int v0, unsigned int v1, unsigned int v2) const
{
   Vec3d u = m_positions[v1] - m_positions[v0];
   Vec3d v = m_positions[v2] - m_positions[v0];
   return normalized(cross(u, v));
}

// --------------------------------------------------------
///
/// Return the triangle with the the smallest area, and that area
///
// --------------------------------------------------------

inline double DynamicSurface::get_min_triangle_area( unsigned int& triangle_index ) const
{
   double min_area = 1e30;
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {
      if ( m_mesh.m_tris[i][0] == m_mesh.m_tris[i][1] )
      {
         continue;
      }
      
      double area = get_triangle_area(i);
      if ( area < min_area )
      {
         min_area = area;
         triangle_index = i;
      }
   }
   
   return min_area;
}

// --------------------------------------------------------
///
/// Return the smallest triangle area
///
// --------------------------------------------------------

inline double DynamicSurface::get_min_triangle_area( ) const
{
   unsigned int dummy;
   return get_min_triangle_area( dummy );
}

// --------------------------------------------------------
///
/// Compute surface normal at the specified vertex (unweighted average of incident triangle normals).
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_vertex_normal( unsigned int vertex ) const
{
   Vec3d normal(0,0,0);
   for ( unsigned int i = 0; i < m_mesh.m_vtxtri[vertex].size(); ++i )
   {
      normal += get_triangle_normal( m_mesh.m_vtxtri[vertex][i] );
   }
   normal /= double(m_mesh.m_vtxtri[vertex].size());
   normal /= mag(normal);
   
   return normal;
}

// --------------------------------------------------------
///
/// Compute surface normal at the specified vertex (weighted according to [Max 1999]).
///
// --------------------------------------------------------

inline Vec3d DynamicSurface::get_vertex_normal_max( unsigned int vertex_index ) const
{
   const std::vector<unsigned int>& inc_tris = m_mesh.m_vtxtri[vertex_index];
   
   Vec3d sum_cross_products(0,0,0);
   
   for ( unsigned int i = 0; i < inc_tris.size(); ++i )
   {
      const Vec3ui& curr_tri = m_mesh.m_tris[inc_tris[i]];
      
      if ( curr_tri[0] == curr_tri[1] ) { continue; }
      
      Vec2ui other_two;
      
      NonDestructiveTriMesh::index_in_triangle( curr_tri, vertex_index, other_two );
      
      unsigned int verti = curr_tri[other_two[0]];
      unsigned int vertnext = curr_tri[other_two[1]];
      
      Vec3d vi = m_positions[verti] - m_positions[vertex_index];
      Vec3d vnext = m_positions[vertnext] - m_positions[vertex_index];
      
      sum_cross_products += cross( vi, vnext ) / ( mag2(vi)*mag2(vnext) );
   }
   
   sum_cross_products /= mag( sum_cross_products );
   
   return sum_cross_products;
}


// --------------------------------------------------------
///
/// Compute length of the specified edge
///
// --------------------------------------------------------

inline double DynamicSurface::get_edge_length( unsigned int edge_index ) const
{
   return mag( m_positions[ m_mesh.m_edges[edge_index][1] ] - m_positions[ m_mesh.m_edges[edge_index][0] ] );
}

// --------------------------------------------------------
///
/// Compute average length over all mesh edges
///
// --------------------------------------------------------

inline double DynamicSurface::get_average_edge_length() const
{
   double sum_lengths = 0;
   for ( unsigned int i = 0; i < m_mesh.m_edges.size(); ++i )
   {
      const Vec2ui& e = m_mesh.m_edges[i]; 
      if ( e[0] == e[1] )  { continue; }
      sum_lengths += mag( m_positions[e[1]] - m_positions[e[0]] ); 
   }
   return sum_lengths / (double) m_mesh.m_edges.size();   
}

// --------------------------------------------------------
///
/// Compute average length over edges on non-solid meshes
///
// --------------------------------------------------------

inline double DynamicSurface::get_average_non_solid_edge_length() const
{
   double sum_lengths = 0;
   unsigned int counted_edges = 0;
   for ( unsigned int i = 0; i < m_mesh.m_edges.size(); ++i )
   {
      const Vec2ui& e = m_mesh.m_edges[i]; 
      if ( e[0] == e[1] )  { continue; }
      if ( m_masses[e[0]] > 100.0 || m_masses[e[1]] > 100.0 ) { continue; }
      sum_lengths += mag( m_positions[e[1]] - m_positions[e[0]] ); 
      ++counted_edges;
   }
   return sum_lengths / (double) counted_edges;   
}

// --------------------------------------------------------
///
/// Compute the surface area
///
// --------------------------------------------------------

inline double DynamicSurface::get_surface_area( ) const
{
   double area=0;
   for(unsigned int t=0; t < m_mesh.m_tris.size(); ++t )
   {
      if ( m_mesh.m_tris[t][0] ==  m_mesh.m_tris[t][1] ) { continue; }
      area += get_triangle_area(t);
   }
   return area;
}
// --------------------------------------------------------
///
/// Compute the surface area using predicted vertex locations
///
// --------------------------------------------------------

inline double DynamicSurface::get_predicted_surface_area( ) const
{
   double area=0;
   for(unsigned int t=0; t < m_mesh.m_tris.size(); ++t )
   {
      if ( m_mesh.m_tris[t][0] ==  m_mesh.m_tris[t][1] ) { continue; }
      const Vec3d &p0 = m_newpositions[m_mesh.m_tris[t][0]];
      const Vec3d &p1 = m_newpositions[m_mesh.m_tris[t][1]];
      const Vec3d &p2 = m_newpositions[m_mesh.m_tris[t][2]];      
      area += 0.5 * mag(cross(p1-p0, p2-p0));
   }
   return area;
}

// --------------------------------------------------------
///
/// Compute the volume enclosed by this surface
///
// --------------------------------------------------------

inline double DynamicSurface::get_volume( ) const
{
   static const double inv_six = 1.0/6.0;
   double volume=0;
   for(unsigned int t=0; t < m_mesh.m_tris.size(); ++t )
   {
      if ( m_mesh.m_tris[t][0] ==  m_mesh.m_tris[t][1] ) { continue; }
      const Vec3ui& tri = m_mesh.m_tris[t];
      volume += inv_six * triple(m_positions[tri[0]], m_positions[tri[1]], m_positions[tri[2]]);
   }
   return volume;
}

// --------------------------------------------------------
///
/// Compute the volume using predicted vertex locations
///
// --------------------------------------------------------

inline double DynamicSurface::get_predicted_volume( ) const
{
   static const double inv_six = 1.0/6.0;
   double volume=0;
   for(unsigned int t=0; t < m_mesh.m_tris.size(); ++t )
   {
      if ( m_mesh.m_tris[t][0] ==  m_mesh.m_tris[t][1] ) { continue; }
      const Vec3ui& tri = m_mesh.m_tris[t];
      volume += inv_six * triple(m_newpositions[tri[0]], m_newpositions[tri[1]], m_newpositions[tri[2]]);
   }
   return volume;
}


// --------------------------------------------------------
///
/// Returns true if the specified edge is intersecting the specified triangle
///
// --------------------------------------------------------

inline bool check_edge_triangle_intersection_by_index( unsigned int edge_a, 
                                                       unsigned int edge_b, 
                                                       unsigned int triangle_a, 
                                                       unsigned int triangle_b, 
                                                       unsigned int triangle_c, 
                                                       std::vector<Vec3d>& m_positions, 
                                                       bool verbose )
{
   if (    edge_a == triangle_a || edge_a == triangle_b || edge_a == triangle_c 
        || edge_b == triangle_a || edge_b == triangle_b || edge_b == triangle_c )
   {
      return false;
   }
   
   return segment_triangle_intersection( m_positions[edge_a], edge_a, m_positions[edge_b], edge_b,
                                         m_positions[triangle_a], triangle_a, m_positions[triangle_b], triangle_b, m_positions[triangle_c], triangle_c,
                                         true, verbose );
   
}


// --------------------------------------------------------
///
/// Returns true if the an edge from one of the triangles intersects the other triangle.
/// NOTE: Using this routine will produce duplicate checks.  Better to use check_edge_triangle_intersection where possible.
///
// --------------------------------------------------------

inline bool check_triangle_triangle_intersection( Vec3ui triangle_a, 
                                                  Vec3ui triangle_b, 
                                                  std::vector<Vec3d>& m_positions )
{
   if ( triangle_a[0] == triangle_a[1] || triangle_b[0] == triangle_b[1] )    
   { 
      return false; 
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_a[0], triangle_a[1], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   m_positions, false ) )
   {
      return true;
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_a[1], triangle_a[2], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   m_positions, false ) )
   {
      return true;
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_a[2], triangle_a[0], 
                                                   triangle_b[0], triangle_b[1], triangle_b[2], 
                                                   m_positions, false ) )
   {
      return true;
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_b[0], triangle_b[1], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   m_positions, false ) )
   {
      return true;
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_b[1], triangle_b[2], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   m_positions, false ) )
   {
      return true;
   }
   
   if ( check_edge_triangle_intersection_by_index( triangle_b[2], triangle_b[0], 
                                                   triangle_a[0], triangle_a[1], triangle_a[2], 
                                                   m_positions, false ) )
   {
		return true;
   }
   
   return false;
}

#endif
