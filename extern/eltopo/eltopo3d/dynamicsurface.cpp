// ---------------------------------------------------------
//
//  dynamicsurface.cpp
//  Tyson Brochu 2008
//  
//  A triangle mesh with associated vertex locations and 
//  velocities.  Collision detection and solving.
//
// ---------------------------------------------------------

// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <dynamicsurface.h>

#include <vector>
#include <deque>
#include <queue>

#ifdef __APPLE__
#include <OpenGL/gl.h>
#else
#ifdef WIN32
#include <windows.h>
#endif
#include <GL/gl.h>
#endif

#include <vec.h>
#include <mat.h>
#include <array3.h>
#include <ccd_wrapper.h>
#include <gluvi.h>
#include <ctime>
#include <nondestructivetrimesh.h>
#include <broadphasegrid.h>
#include <wallclocktime.h>
#include <cassert>
#include <sparse_matrix.h>
#include <krylov_solvers.h>
#include <fstream>
#include <lapack_wrapper.h>
#include <array2.h>

#include <ccd_wrapper.h>
#include <collisionqueries.h>

//#define USE_EXACT_ARITHMETIC_RAY_CASTING

#ifdef USE_EXACT_ARITHMETIC_RAY_CASTING
#include <tunicate.h>
#endif

// ---------------------------------------------------------
// Local constants, typedefs, macros
// ---------------------------------------------------------

// ---------------------------------------------------------
//  Extern globals
// ---------------------------------------------------------

const double G_EIGENVALUE_RANK_RATIO = 0.03;

// ---------------------------------------------------------
// Static function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Add a collision to the list as long as it doesn't have the same vertices as any other collisions in the list.
///
// ---------------------------------------------------------

static void add_unique_collision( std::vector<Collision>& collisions, const Collision& new_collision )
{
   for ( std::vector<Collision>::iterator iter = collisions.begin(); iter != collisions.end(); ++iter )
   {
      if ( iter->same_vertices( new_collision ) )
      {
         return;
      }
   }
   
   collisions.push_back( new_collision );
}

// ---------------------------------------------------------
///
/// Helper function: multiply transpose(A) * D * B
///
// ---------------------------------------------------------

static void AtDB(const SparseMatrixDynamicCSR &A, const double* diagD, const SparseMatrixDynamicCSR &B, SparseMatrixDynamicCSR &C)
{
   assert(A.m==B.m);
   C.resize(A.n, B.n);
   C.set_zero();
   for(int k=0; k<A.m; ++k)
   {
      const DynamicSparseVector& r = A.row[k];
      
      for( DynamicSparseVector::const_iterator p=r.begin(); p != r.end(); ++p )
      {
         int i = p->index;
         double multiplier = p->value * diagD[k];
         C.add_sparse_row( i, B.row[k], multiplier );
      }
   }
}

// ---------------------------------------------------------
// Member function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// DynamicSurface constructor.  Copy triangles and vertex locations.
///
// ---------------------------------------------------------

DynamicSurface::DynamicSurface( const std::vector<Vec3d>& vertex_positions, 
                                const std::vector<Vec3ui>& triangles,
                                const std::vector<double>& masses,
                                double in_proximity_epsilon,
                                bool in_collision_safety,
                                bool in_verbose ) :
   m_proximity_epsilon( in_proximity_epsilon ),
   m_verbose( in_verbose ),   
   m_collision_safety( in_collision_safety ),
   m_positions(0), m_newpositions(0), m_velocities(0), m_masses(0),
   m_mesh(),
   m_num_collisions_this_step(0), m_total_num_collisions(0)
{
   
   m_broad_phase = new BroadPhaseGrid();
   
   std::cout << "constructing dynamic surface" << std::endl;
  
   for(unsigned int i = 0; i < vertex_positions.size(); i++)
   {
      m_positions.push_back( vertex_positions[i] );
		m_newpositions.push_back( vertex_positions[i] );
      m_velocities.push_back( Vec3d(0,0,0) );
      m_masses.push_back( masses[i] );
   }
   
   for(unsigned int i = 0; i < triangles.size(); i++)
   {
      m_mesh.m_tris.push_back( triangles[i] );
   }
   
   std::cout << "constructed dynamic surface" << std::endl;
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

DynamicSurface::~DynamicSurface()
{
   delete m_broad_phase;
}


// ---------------------------------------------------------
///
/// Compute rank of the quadric metric tensor at a vertex
///
// ---------------------------------------------------------

unsigned int DynamicSurface::classify_vertex( unsigned int v )
{     
   if ( m_mesh.m_vtxtri[v].empty() )     { return 0; }
   
   const std::vector<unsigned int>& incident_triangles = m_mesh.m_vtxtri[v];
   
   std::vector< Vec3d > N;
   std::vector< double > W;
   
   for ( unsigned int i = 0; i < incident_triangles.size(); ++i )
   {
      unsigned int triangle_index = incident_triangles[i];
      N.push_back( get_triangle_normal(triangle_index) );
      W.push_back( get_triangle_area(triangle_index) );
   }
   
   Mat33d A(0,0,0,0,0,0,0,0,0);
   
   for ( unsigned int i = 0; i < N.size(); ++i )
   {
      A(0,0) += N[i][0] * W[i] * N[i][0];
      A(1,0) += N[i][1] * W[i] * N[i][0];
      A(2,0) += N[i][2] * W[i] * N[i][0];
      
      A(0,1) += N[i][0] * W[i] * N[i][1];
      A(1,1) += N[i][1] * W[i] * N[i][1];
      A(2,1) += N[i][2] * W[i] * N[i][1];
      
      A(0,2) += N[i][0] * W[i] * N[i][2];
      A(1,2) += N[i][1] * W[i] * N[i][2];
      A(2,2) += N[i][2] * W[i] * N[i][2];
   }
   
   // get eigen decomposition
   double eigenvalues[3];
   double work[9];
   int info = ~0, n = 3, lwork = 9;
   LAPACK::get_eigen_decomposition( &n, A.a, &n, eigenvalues, work, &lwork, &info );
   
   if ( info != 0 )
   {
      std::cout << "Eigen decomp failed.  Incident triangles: " << std::endl;
      for ( unsigned int i = 0; i < W.size(); ++i )
      {
         std::cout << "normal: ( " << N[i] << " )    ";  
         std::cout << "area: " << W[i] << std::endl;
      }
      return 4;
   }
   
   // compute rank of primary space
   unsigned int rank = 0;
   for ( unsigned int i = 0; i < 3; ++i )
   {
      if ( eigenvalues[i] > G_EIGENVALUE_RANK_RATIO * eigenvalues[2] )
      {
         ++rank;
      }
   }
   
   return rank;
   
}



// ---------------------------------------------------------
///
/// Add a triangle to the surface.  Update the underlying TriMesh and acceleration grid. 
///
// ---------------------------------------------------------

unsigned int DynamicSurface::add_triangle( const Vec3ui& t )
{
   unsigned int new_triangle_index = m_mesh.m_tris.size();
   m_mesh.nondestructive_add_triangle( t );

   if ( m_collision_safety )
   {
      // Add to the triangle grid
      Vec3d low, high;
      triangle_static_bounds( new_triangle_index, low, high );
      m_broad_phase->add_triangle( new_triangle_index, low, high );
      
      // Add edges to grid as well
      unsigned int new_edge_index = m_mesh.get_edge( t[0], t[1] );
      assert( new_edge_index != m_mesh.m_edges.size() );
      edge_static_bounds( new_edge_index, low, high );
      m_broad_phase->add_edge( new_edge_index, low, high );
      
      new_edge_index = m_mesh.get_edge( t[1], t[2] );
      assert( new_edge_index != m_mesh.m_edges.size() );   
      edge_static_bounds( new_edge_index, low, high );
      m_broad_phase->add_edge( new_edge_index, low, high );
      
      new_edge_index = m_mesh.get_edge( t[2], t[0] );
      assert( new_edge_index != m_mesh.m_edges.size() );   
      edge_static_bounds( new_edge_index, low, high );
      m_broad_phase->add_edge( new_edge_index, low, high );
   }
   
   return new_triangle_index;
}


// ---------------------------------------------------------
///
/// Remove a triangle from the surface.  Update the underlying TriMesh and acceleration grid. 
///
// ---------------------------------------------------------

void DynamicSurface::remove_triangle(unsigned int t)
{
   m_mesh.nondestructive_remove_triangle( t );
   if ( m_collision_safety )
   {
      m_broad_phase->remove_triangle( t );
   }
}


// ---------------------------------------------------------
///
/// Add a vertex to the surface.  Update the acceleration grid. 
///
// ---------------------------------------------------------

unsigned int DynamicSurface::add_vertex( const Vec3d& new_vertex_position, 
                                         const Vec3d& new_vertex_velocity, 
                                         double new_vertex_mass )
{
   m_positions.push_back( new_vertex_position );
   m_newpositions.push_back( new_vertex_position );
   m_velocities.push_back( new_vertex_velocity );
   m_masses.push_back( new_vertex_mass );
      
   unsigned int new_vertex_index = m_mesh.nondestructive_add_vertex( );

   assert( new_vertex_index == m_positions.size() - 1 );
   
   if ( m_collision_safety )
   {
      m_broad_phase->add_vertex( new_vertex_index, m_positions[new_vertex_index], m_positions[new_vertex_index] );       
   }
   
   return new_vertex_index;
}


// ---------------------------------------------------------
///
/// Remove a vertex from the surface.  Update the acceleration grid. 
///
// ---------------------------------------------------------

void DynamicSurface::remove_vertex( unsigned int vertex_index )
{
   m_mesh.nondestructive_remove_vertex( vertex_index );
   
   if ( m_collision_safety )
   {
      m_broad_phase->remove_vertex( vertex_index );
   }
   
   m_positions[ vertex_index ] = Vec3d( 0.0, 0.0, 0.0 );
   m_newpositions[ vertex_index ] = Vec3d( 0.0, 0.0, 0.0 );
}


// --------------------------------------------------------
///
/// Determine surface IDs for all vertices
///
// --------------------------------------------------------

void DynamicSurface::partition_surfaces( std::vector<unsigned int>& surface_ids, std::vector< std::vector< unsigned int> >& surfaces ) const
{
      
   static const unsigned int UNASSIGNED = (unsigned int) ~0;
   
   surfaces.clear();
   
   surface_ids.clear();
   surface_ids.resize( m_positions.size(), UNASSIGNED );
   
   unsigned int curr_surface = 0;
   
   while ( true )
   { 
      unsigned int next_unassigned_vertex;
      for ( next_unassigned_vertex = 0; next_unassigned_vertex < surface_ids.size(); ++next_unassigned_vertex )
      {
         if ( m_mesh.m_vtxedge[next_unassigned_vertex].empty() ) { continue; }
         
         if ( surface_ids[next_unassigned_vertex] == UNASSIGNED )
         {
            break;
         }
      }
      
      if ( next_unassigned_vertex == surface_ids.size() )
      {
         break;
      }
      
      std::queue<unsigned int> open;
      open.push( next_unassigned_vertex );
      
      std::vector<unsigned int> surface_vertices;
      
      while ( false == open.empty() )
      {
         unsigned int vertex_index = open.front();
         open.pop();
         
         if ( m_mesh.m_vtxedge[vertex_index].empty() ) { continue; }
         
         if ( surface_ids[vertex_index] != UNASSIGNED )
         {
            assert( surface_ids[vertex_index] == curr_surface );
            continue;
         }
         
         surface_ids[vertex_index] = curr_surface;
         surface_vertices.push_back( vertex_index );
         
         const std::vector<unsigned int>& incident_edges = m_mesh.m_vtxedge[vertex_index];
         
         for( unsigned int i = 0; i < incident_edges.size(); ++i )
         {
            unsigned int adjacent_vertex = m_mesh.m_edges[ incident_edges[i] ][0];
            if ( adjacent_vertex == vertex_index ) { adjacent_vertex = m_mesh.m_edges[ incident_edges[i] ][1]; }
            
            if ( surface_ids[adjacent_vertex] == UNASSIGNED )
            {
               open.push( adjacent_vertex );
            }
            else
            {
               assert( surface_ids[adjacent_vertex] == curr_surface );
            }
            
         } 
      }
      
      surfaces.push_back( surface_vertices );
      
      ++curr_surface;
      
   }
   
   std::cout << " %%%%%%%%%%%%%%%%%%%%%%% number of surfaces: " << surfaces.size() << std::endl;
   
   //
   // assert all vertices are assigned and share volume IDs with their neighbours
   //
   
   for ( unsigned int i = 0; i < surface_ids.size(); ++i )
   {
      if ( m_mesh.m_vtxedge[i].empty() ) { continue; }
      
      assert( surface_ids[i] != UNASSIGNED );
      
      const std::vector<unsigned int>& incident_edges = m_mesh.m_vtxedge[i];    
      for( unsigned int j = 0; j < incident_edges.size(); ++j )
      {
         unsigned int adjacent_vertex = m_mesh.m_edges[ incident_edges[j] ][0];
         if ( adjacent_vertex == i ) { adjacent_vertex = m_mesh.m_edges[ incident_edges[j] ][1]; }
         assert( surface_ids[adjacent_vertex] == surface_ids[i] );         
      } 
      
   }
   
}


// ---------------------------------------------------------
///
/// Compute the maximum timestep that will not invert any triangle normals, using a quadratic solve as in [Jiao 2007].
///
// ---------------------------------------------------------

double DynamicSurface::compute_max_timestep_quadratic_solve( const std::vector<Vec3ui>& tris, 
                                                       const std::vector<Vec3d>& positions, 
                                                       const std::vector<Vec3d>& displacements, 
                                                       bool verbose ) 
{
   double max_beta = 1.0;
   
   double min_area = 1e30;
   
   for ( unsigned int i = 0; i < tris.size(); ++i )
   {
      if ( tris[i][0] == tris[i][1] ) { continue; }
      
      const Vec3d& x1 = positions[tris[i][0]];
      const Vec3d& x2 = positions[tris[i][1]];
      const Vec3d& x3 = positions[tris[i][2]];
      
      const Vec3d& u1 = displacements[tris[i][0]];
      const Vec3d& u2 = displacements[tris[i][1]];
      const Vec3d& u3 = displacements[tris[i][2]];
      
      Vec3d new_x1 = x1 + u1;
      Vec3d new_x2 = x2 + u2;
      Vec3d new_x3 = x3 + u3;
      
      const Vec3d c0 = cross( (x2-x1), (x3-x1) );
      const Vec3d c1 = cross( (x2-x1), (u3-u1) ) - cross( (x3-x1), (u2-u1) );
      const Vec3d c2 = cross( (u2-u1), (u3-u1) );
      const double a = dot(c0, c2);
      const double b = dot(c0, c1);
      const double c = dot(c0, c0);
      
      double beta = 1.0;
      
      min_area = min( min_area, c );
      
      if ( c < 1e-14 )
      {
         if ( verbose ) 
         {
            printf( "super small triangle %d (%d %d %d)\n", i, tris[i][0], tris[i][1], tris[i][2] );
         }
      }
      
      if ( fabs(a) == 0 )
      {
         if ( verbose ) 
         { 
            //printf( "triangle %d: ", i ); 
            //printf( "a == 0 (%g)\n", a ); 
         }
         
         if ( ( fabs(b) > 1e-14 ) && ( -c / b >= 0.0 ) )
         {
            beta = -c / b;
         }
         else
         {
            if ( verbose )
            {
               if ( fabs(b) < 1e-14 )
               {
                  printf( "triangle %d: ", i ); 
                  printf( "b == 0 too (%g).\n", b );
               }
            }
         }
      }
      else
      {
         double descriminant = b*b - 4.0*a*c;
         
         if ( descriminant < 0.0  )
         {
            // Hmm, what does this mean?
            if ( verbose )
            {
               printf( "triangle %d: descriminant == %g\n", i, descriminant );
            }
            
            beta = 1.0;
         }
         else
         {
            double q;
            if ( b > 0.0 )
            {
               q = -0.5 * ( b + sqrt( descriminant ) );
            }
            else
            {
               q = -0.5 * ( b - sqrt( descriminant ) );
            }
            
            double beta_1 = q / a;
            double beta_2 = c / q;
            
            if ( beta_1 < 0.0 )
            {
               if ( beta_2 < 0.0 )
               {
                  assert( dot( triangle_normal(x1, x2, x3), triangle_normal(new_x1, new_x2, new_x3) ) > 0.0 );
               }
               else
               {
                  beta = beta_2;
               }
            }
            else
            {
               if ( beta_2 < 0.0 )
               {
                  beta = beta_1;
               }
               else if ( beta_1 < beta_2 )
               {
                  beta = beta_1;
               }
               else
               {
                  beta = beta_2;
               }
            }
            
         }
      }
      
      bool changed = false;
      if ( beta < max_beta )
      {
         max_beta = 0.99 * beta;
         changed = true;
         
         if ( verbose )
         {
            printf( "changing beta --- triangle: %d\n", i );
            printf( "new max beta: %g\n", max_beta );
            printf( "a = %g, b = %g, c = %g\n", a, b, c );
         }
         
         if ( max_beta < 1e-4 )
         {
            //assert(0);
         }
         
      }
      
      new_x1 = x1 + max_beta * u1;
      new_x2 = x2 + max_beta * u2;
      new_x3 = x3 + max_beta * u3;
      
      Vec3d old_normal = cross(x2-x1, x3-x1);
      Vec3d new_normal = cross(new_x2-new_x1, new_x3-new_x1);
      
      if ( dot( old_normal, new_normal ) < 0.0 )
      {
         printf( "triangle %d: (%d %d %d)\n", i, tris[i][0], tris[i][1], tris[i][2] );
         printf( "old normal: %g %g %g\n", old_normal[0], old_normal[1], old_normal[2] );
         printf( "new normal: %g %g %g\n", new_normal[0], new_normal[1], new_normal[2] );         
         printf( "dot product: %g\n", dot( triangle_normal(x1, x2, x3), triangle_normal(new_x1, new_x2, new_x3) ) );
         printf( "%s\n", (changed ? "changed" : "not changed") );
         printf( "beta: %g\n", beta );
         printf( "max beta: %g\n", max_beta );
         //assert(0);
      }
   }
   
   return max_beta;
}


// ---------------------------------------------------------
///
/// Compute the unsigned distance to the surface.
///
// ---------------------------------------------------------

double DynamicSurface::distance_to_surface( const Vec3d& p, unsigned int& closest_triangle )
{
   
   double padding = m_proximity_epsilon;
   double min_distance = 1e30;
   
   while ( min_distance == 1e30 )
   {
      
      Vec3d xmin( p - Vec3d( padding ) );
      Vec3d xmax( p + Vec3d( padding ) );
      
      std::vector<unsigned int> nearby_triangles;   
      
      m_broad_phase->get_potential_triangle_collisions( xmin, xmax, nearby_triangles );
            
      for ( unsigned int j = 0; j < nearby_triangles.size(); ++j )
      {
         const Vec3ui& tri = m_mesh.m_tris[ nearby_triangles[j] ];

         if ( tri[0] == tri[1] || tri[1] == tri[2] || tri[0] == tri[2] ) { continue; }

         if ( m_masses[tri[0]] > 1.5 && m_masses[tri[1]] > 1.5 && m_masses[tri[2]] > 1.5 ) { continue; }
         
         double curr_distance;
         check_point_triangle_proximity( p, m_positions[tri[0]], m_positions[tri[1]], m_positions[tri[2]], curr_distance );
         if ( curr_distance < padding )
         {   
            min_distance = min( min_distance, curr_distance );
            closest_triangle = nearby_triangles[j];
         }
      }

      padding *= 2.0;

   }

   return min_distance;

}


// ---------------------------------------------------------
///
/// Run intersection detection against all triangles
///
// ---------------------------------------------------------

void DynamicSurface::get_triangle_intersections( const Vec3d& segment_point_a, 
                                                 const Vec3d& segment_point_b,
                                                 std::vector<double>& hit_ss,
                                                 std::vector<unsigned int>& hit_triangles ) const
{
   Vec3d aabb_low, aabb_high;
   minmax( segment_point_a, segment_point_b, aabb_low, aabb_high );
   
   std::vector<unsigned int> overlapping_triangles;
   m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, overlapping_triangles );
   
   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[ overlapping_triangles[i] ];
      
      Vec3ui t = sort_triangle( tri );
      assert( t[0] < t[1] && t[0] < t[2] && t[1] < t[2] );
      
      const Vec3d& v0 = m_positions[ t[0] ];
      const Vec3d& v1 = m_positions[ t[1] ];
      const Vec3d& v2 = m_positions[ t[2] ];      
      
      unsigned int dummy_index = m_positions.size();
      
      double bary1, bary2, bary3;
      Vec3d normal;
      double s;
      double relative_normal_displacement;
      
      bool hit = point_triangle_collision( segment_point_a, segment_point_b, dummy_index,
                                           v0, v0, t[0],
                                           v1, v1, t[1],
                                           v2, v2, t[2],
                                           bary1, bary2, bary3,
                                           normal,
                                           s, relative_normal_displacement );
                                
      if ( hit )
      {
         hit_ss.push_back( s );
         hit_triangles.push_back( overlapping_triangles[i] );
      }         
      
   }
   
}

// ---------------------------------------------------------
///
/// Run intersection detection against all triangles and return the number of hits.
///
// ---------------------------------------------------------

unsigned int DynamicSurface::get_number_of_triangle_intersections( const Vec3d& segment_point_a, 
                                                                   const Vec3d& segment_point_b ) const
{
   int num_hits = 0;
   int num_misses = 0;
   Vec3d aabb_low, aabb_high;
   minmax( segment_point_a, segment_point_b, aabb_low, aabb_high );
   
   std::vector<unsigned int> overlapping_triangles;
   m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, overlapping_triangles );

   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[ overlapping_triangles[i] ];
      
      Vec3ui t = sort_triangle( tri );
      assert( t[0] < t[1] && t[0] < t[2] && t[1] < t[2] );
      
      const Vec3d& v0 = m_positions[ t[0] ];
      const Vec3d& v1 = m_positions[ t[1] ];
      const Vec3d& v2 = m_positions[ t[2] ];      
      
      unsigned int dummy_index = m_positions.size();
      static const bool degenerate_counts_as_hit = true;

      bool hit = segment_triangle_intersection( segment_point_a, dummy_index,
                                                segment_point_b, dummy_index + 1, 
                                                v0, t[0],
                                                v1, t[1],
                                                v2, t[2],   
                                                degenerate_counts_as_hit );
      
      if ( hit )
      {
         ++num_hits;
      }         
      else
      {
         ++num_misses;
      }
   }
      
   return num_hits;

}


#ifdef USE_EXACT_ARITHMETIC_RAY_CASTING

static Mat44d look_at(const Vec3d& from,
                      const Vec3d& to)
{
   Mat44d T;
   Vec3d c=-normalized(to-from);
   Vec3d a=cross(Vec3d(0,1,0), c);
   Vec3d b=cross(c, a);
   
   T(0,0)=a[0]; T(0,1)=a[1]; T(0,2)=a[2]; T(0,3) = -dot(a,from);
   T(1,0)=b[0]; T(1,1)=b[1]; T(1,2)=b[2]; T(1,3) = -dot(b,from);
   T(2,0)=c[0]; T(2,1)=c[1]; T(2,2)=c[2]; T(2,3) = -dot(c,from);
   T(3,0)=0.0;  T(3,1)=0.0;  T(3,2)=0.0;  T(3,3) = 1.0;
   
   return T;
}

static Vec3d apply_to_point( const Mat44d& M, const Vec3d& x )
{
   double w = M(3,0)*x[0] + M(3,1)*x[1] + M(3,2)*x[2] + M(3,3);
   
   return Vec3d((M(0,0)*x[0] + M(0,1)*x[1] + M(0,2)*x[2] + M(0,3))/w,
                (M(1,0)*x[0] + M(1,1)*x[1] + M(1,2)*x[2] + M(1,3))/w,
                (M(2,0)*x[0] + M(2,1)*x[1] + M(2,2)*x[2] + M(2,3))/w );
}

// ---------------------------------------------------------
///
/// Run intersection detection against all triangles and return the number of hits.  Use exact arithmetic.
///
// ---------------------------------------------------------

unsigned int DynamicSurface::get_number_of_triangle_intersections_exact( const Vec3d& segment_point_a, 
                                                                         const Vec3d& segment_point_b ) const
{
   int num_hits = 0;
   int num_misses = 0;
   Vec3d aabb_low, aabb_high;
   minmax( segment_point_a, segment_point_b, aabb_low, aabb_high );
   
   std::vector<unsigned int> overlapping_triangles;
   m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, overlapping_triangles );
   
   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[ overlapping_triangles[i] ];
      
      Vec3ui t = sort_triangle( tri );
      assert( t[0] < t[1] && t[0] < t[2] && t[1] < t[2] );
      
      const Vec3d v0 = (m_positions[ t[0] ]);
      const Vec3d v1 = (m_positions[ t[1] ]);
      const Vec3d v2 = (m_positions[ t[2] ]);      
            
      Vec3d ortho = cross( v1-v0, v2-v0 );
      
      double ray_length = mag( segment_point_b - segment_point_a );
      Vec3d ray_direction = ( segment_point_b - segment_point_a ) / ray_length;
      Vec3d ray_origin( segment_point_a );
      
      // find plane intersection with ray
      double dn=dot( ray_direction, ortho );

      if ( dn==0 )
      {
         ++num_misses;
         continue;
      }
   
      double s0 = -dot( ray_origin - v0, ortho ) / dn;

      if ( s0 < 0 || s0 > ray_length ) 
      { 
         // no hit
         ++num_misses;
         continue;
      }
      
      Mat44d transform = look_at( ray_direction, Vec3d(0,0,0) );
      
      Vec3d a = apply_to_point( transform, v0 - ray_origin );
      Vec3d b = apply_to_point( transform, v1 - ray_origin );
      Vec3d c = apply_to_point( transform, v2 - ray_origin );
      
      Vec2d a2( a[0], a[1] );
      Vec2d b2( b[0], b[1] );
      Vec2d c2( c[0], c[1] );
      Vec2d r2( 0, 0 );
      
      //std::cout << "2d triangle: " << a2 << ", " << b2 << ", " << c2 << std::endl;
      
      double bary[4];
      int dummy_index = m_positions.size();
      int result = sos_simplex_intersection2d( 3, 
                                               t[0], a2.v, 
                                               t[1], b2.v, 
                                               t[2], c2.v, 
                                               dummy_index, r2.v, 
                                               &(bary[0]), &(bary[1]), &(bary[2]), &(bary[3]) );

      if ( result != 0 )
      {
         ++num_hits;
      }         
      else
      {
         ++num_misses;
      }
   }
   
   return num_hits;
}

#endif


// ---------------------------------------------------------
///
/// Determine whether a point is inside the volume defined by the surface.  Uses raycast-voting.
///
// ---------------------------------------------------------

bool DynamicSurface::point_is_inside( const Vec3d& p )
{

#ifdef USE_EXACT_ARITHMETIC_RAY_CASTING
   
   // Exact arithmetic ray casting:
   Vec3d ray_end( p + Vec3d( 1e+3, 1, 0 ) );
   int hits = get_number_of_triangle_intersections_exact( p, ray_end );
   
   if ( hits % 2 == 1 ) { return true; }   
   return false;
   
#else
   
   //
   // The point is inside if there are an odd number of hits on a ray cast from the point. 
   // We'll cast six rays for numerical robustness.
   //

   
   unsigned int inside_votes = 0;
   
   // shoot a ray in the positive-x direction
   Vec3d ray_end( p + Vec3d( 1e+3, 1, 0 ) );
   int hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }
   
   // negative x
   ray_end = p - Vec3d( 1e+3, 0, 1 );
   hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }

   // positive y
   ray_end = p + Vec3d( 1, 1e+3, 0 );
   hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }

   // negative y
   ray_end = p - Vec3d( 0, 1e+3, 1 );
   hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }

   // positive z
   ray_end = p + Vec3d( 0, 1, 1e+3 );
   hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }
   
   // negative z
   ray_end = p - Vec3d( 1, 0, 1e+3 );
   hits = get_number_of_triangle_intersections( p, ray_end );
   if ( hits % 2 == 1 ) { ++inside_votes; }
   
   return ( inside_votes > 3 );
   
#endif
   
}


// ---------------------------------------------------------
///
/// Remove all vertices not incident on any triangles.
///
// ---------------------------------------------------------

void DynamicSurface::clear_deleted_vertices( )
{

   unsigned int j = 0;
   
   for ( unsigned int i = 0; i < m_positions.size(); ++i )
   {
      std::vector<unsigned int>& inc_tris = m_mesh.m_vtxtri[i];

      if ( inc_tris.size() != 0 )
      {
         m_positions[j] = m_positions[i];
         m_newpositions[j] = m_newpositions[i];
         m_velocities[j] = m_velocities[i];
         m_masses[j] = m_masses[i];
         
         for ( unsigned int t = 0; t < inc_tris.size(); ++t )
         {
            Vec3ui& triangle = m_mesh.m_tris[ inc_tris[t] ];
            
            if ( triangle[0] == i ) { triangle[0] = j; }
            if ( triangle[1] == i ) { triangle[1] = j; }
            if ( triangle[2] == i ) { triangle[2] = j; }            
         }
         
         ++j;
      }

   }
      
   m_positions.resize(j);
   m_newpositions.resize(j);
   m_velocities.resize(j);
   m_masses.resize(j);

}


// ---------------------------------------------------------
///
/// Apply an impulse between two edges 
///
// ---------------------------------------------------------

void DynamicSurface::apply_edge_edge_impulse( const Vec2ui& edge0, 
                                              const Vec2ui& edge1,
                                              double s0, 
                                              double s2, 
                                              Vec3d& direction, 
                                              double magnitude )
{
   Vec3d& v0 = m_velocities[edge0[0]];
   Vec3d& v1 = m_velocities[edge0[1]];
   Vec3d& v2 = m_velocities[edge1[0]];
   Vec3d& v3 = m_velocities[edge1[1]];
   double inv_m0 = m_masses[edge0[0]] < 100 ? 1 / m_masses[edge0[0]] : 0.0;
   double inv_m1 = m_masses[edge0[1]] < 100 ? 1 / m_masses[edge0[1]] : 0.0;
   double inv_m2 = m_masses[edge1[0]] < 100 ? 1 / m_masses[edge1[0]] : 0.0;
   double inv_m3 = m_masses[edge1[1]] < 100 ? 1 / m_masses[edge1[1]] : 0.0;
    
   double s1 = 1.0 - s0;
   double s3 = 1.0 - s2;
   double i = magnitude/(s0*s0*inv_m0 + s1*s1*inv_m1 + s2*s2*inv_m2 + s3*s3*inv_m3);
   
   v0 += i*s0*inv_m0 * direction;
   v1 += i*s1*inv_m1 * direction;
   v2 -= i*s2*inv_m2 * direction;
   v3 -= i*s3*inv_m3 * direction;
}

// ---------------------------------------------------------
///
/// Apply an impulse between a point and a triangle
///
// ---------------------------------------------------------

void DynamicSurface::apply_triangle_point_impulse( const Vec3ui& tri, 
                                                   unsigned int v,
                                                   double s1, 
                                                   double s2, 
                                                   double s3, 
                                                   Vec3d& direction, 
                                                   double magnitude )
{

   Vec3d& v0 = m_velocities[v];
   Vec3d& v1 = m_velocities[tri[0]];
   Vec3d& v2 = m_velocities[tri[1]];
   Vec3d& v3 = m_velocities[tri[2]];
   double inv_m0 = m_masses[v] < 100 ? 1 / m_masses[v] : 0.0;
   double inv_m1 = m_masses[tri[0]] < 100 ? 1 / m_masses[tri[0]] : 0.0;
   double inv_m2 = m_masses[tri[1]] < 100 ? 1 / m_masses[tri[1]] : 0.0;
   double inv_m3 = m_masses[tri[2]] < 100 ? 1 / m_masses[tri[2]] : 0.0;

   double i = magnitude / (inv_m0 + s1*s1*inv_m1 + s2*s2*inv_m2 + s3*s3*inv_m3);

   v0 += (i*inv_m0) * direction;
   v1 -= (i*s1*inv_m1) * direction;
   v2 -= (i*s2*inv_m2) * direction;
   v3 -= (i*s3*inv_m3) * direction;
}
 


// ---------------------------------------------------------
///
/// Detect all triangle-point proximities and apply repulsion impulses
///
// ---------------------------------------------------------

void DynamicSurface::handle_triangle_point_proximities( double dt )
{

   unsigned int broadphase_hits = 0;
   unsigned int point_triangle_proximities = 0;
   
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[i];
      
      if ( tri[0] == tri[1] )    { continue; }


      Vec3d low, high;
      triangle_static_bounds( i, low, high );
      std::vector<unsigned int> potential_vertex_collisions;
      m_broad_phase->get_potential_vertex_collisions( low, high, potential_vertex_collisions );
      
      for ( unsigned int j = 0; j < potential_vertex_collisions.size(); ++j )
      {
         unsigned int v = potential_vertex_collisions[j];
   
         if(tri[0] != v && tri[1] != v && tri[2] != v)
         {
            ++broadphase_hits;
            double distance, s1, s2, s3;
            Vec3d normal;
            
            point_triangle_distance( m_positions[v], v,
                                     m_positions[tri[0]], tri[0],
                                     m_positions[tri[1]], tri[1],
                                     m_positions[tri[2]], tri[2],
                                     distance, s1, s2, s3, normal );
            
            if(distance < m_proximity_epsilon)
            {
               
               double relvel = dot(normal, m_velocities[v] - (s1*m_velocities[tri[0]] + s2*m_velocities[tri[1]] + s3*m_velocities[tri[2]]));
               double desired_relative_velocity = ( m_proximity_epsilon - distance ) / dt;
               double impulse = (desired_relative_velocity - relvel);
               
               apply_triangle_point_impulse( tri, v, s1, s2, s3, normal, impulse);
               
               ++point_triangle_proximities;
               
            }
         }      
      }
   }

}


// ---------------------------------------------------------
///
/// Detect all edge-edge proximities and apply repulsion impulses
///
// ---------------------------------------------------------

void DynamicSurface::handle_edge_edge_proximities( double dt )
{

   unsigned int edge_edge_proximities = 0;
   
   for ( unsigned int i = 0; i < m_mesh.m_edges.size(); ++i )
   {
      const Vec2ui& e0 = m_mesh.m_edges[ i ];
      
      if ( e0[0] == e0[1] ) { continue; }
      
      Vec3d low, high;
      edge_static_bounds( i, low, high );
      std::vector<unsigned int> potential_collisions;
      m_broad_phase->get_potential_edge_collisions( low, high, potential_collisions );
      
      for ( unsigned int j = 0; j < potential_collisions.size(); ++j )
      {
         if ( potential_collisions[j] <= i )    { continue; }
         
         const Vec2ui& e1 = m_mesh.m_edges[ potential_collisions[j] ];
         
         if ( e1[0] == e1[1] )   { continue; }
         
         if(e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1])
         {
            double distance, s0, s2;
            Vec3d normal;
            
            segment_segment_distance( m_positions[e0[0]], e0[0],
                                      m_positions[e0[1]], e0[1],
                                      m_positions[e1[0]], e1[0],
                                      m_positions[e1[1]], e0[1],
                                      distance, s0, s2, normal);
            
            if( distance < m_proximity_epsilon )
            {
               ++edge_edge_proximities;
               
               double relvel = dot(normal, s0*m_velocities[e0[0]] + (1.0-s0)*m_velocities[e0[1]] - (s2*m_velocities[e1[0]] + (1.0-s2)*m_velocities[e1[1]]));
               double desired_relative_velocity = ( m_proximity_epsilon - distance ) / dt;               
               double impulse = ( desired_relative_velocity - relvel );
               
               apply_edge_edge_impulse( e0, e1, s0, s2, normal, impulse);
            }
         }
      }
   }
   
}


// ---------------------------------------------------------
///
/// Add point-triangle collision candidates for a specified triangle
///
// ---------------------------------------------------------

void DynamicSurface::add_triangle_candidates(unsigned int t, CollisionCandidateSet& collision_candidates)
{
   Vec3d tmin, tmax;
   triangle_continuous_bounds(t, tmin, tmax);
   tmin -= Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   tmax += Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   
   std::vector<unsigned int> candidate_vertices;
   m_broad_phase->get_potential_vertex_collisions( tmin, tmax, candidate_vertices );
   
   for(unsigned int j = 0; j < candidate_vertices.size(); j++)
   {
      add_to_collision_candidates( collision_candidates, Vec3ui(t, candidate_vertices[j], 0) );
   }
   
}

// ---------------------------------------------------------
///
/// Add edge-edge collision candidates for a specified edge
///
// ---------------------------------------------------------

void DynamicSurface::add_edge_candidates(unsigned int e, CollisionCandidateSet& collision_candidates)
{
   Vec3d emin, emax;
   edge_continuous_bounds(e, emin, emax);
   emin -= Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   emax += Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   
   std::vector<unsigned int> candidate_edges;
   m_broad_phase->get_potential_edge_collisions( emin, emax, candidate_edges);
   
   for(unsigned int j = 0; j < candidate_edges.size(); j++)
   {
      add_to_collision_candidates( collision_candidates, Vec3ui(e, candidate_edges[j], 1) );
   }
}

// ---------------------------------------------------------
///
/// Add point-triangle collision candidates for a specified vertex
///
// ---------------------------------------------------------

void DynamicSurface::add_point_candidates(unsigned int v, CollisionCandidateSet& collision_candidates)
{
   Vec3d vmin, vmax;
   vertex_continuous_bounds(v, vmin, vmax);
   vmin -= Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   vmax += Vec3d( m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon );
   
   std::vector<unsigned int> candidate_triangles;
   m_broad_phase->get_potential_triangle_collisions( vmin, vmax, candidate_triangles);
   
   for(unsigned int j = 0; j < candidate_triangles.size(); j++)
   {
      add_to_collision_candidates( collision_candidates, Vec3ui(candidate_triangles[j], v, 0) );
   }
}

// ---------------------------------------------------------
///
/// Add collision candidates for a specified vertex and all elements incident on the vertex
///
// ---------------------------------------------------------

void DynamicSurface::add_point_update_candidates(unsigned int v, CollisionCandidateSet& collision_candidates)
{
   add_point_candidates(v, collision_candidates);
   
   std::vector<unsigned int>& incident_triangles = m_mesh.m_vtxtri[v];
   std::vector<unsigned int>& incident_edges = m_mesh.m_vtxedge[v];
   
   for(unsigned int i = 0; i < incident_triangles.size(); i++)
      add_triangle_candidates(incident_triangles[i], collision_candidates);
   
   for(unsigned int i = 0; i < incident_edges.size(); i++)
      add_edge_candidates(incident_edges[i], collision_candidates);
}


// ---------------------------------------------------------
///
/// Perform one sweep of impulse collision handling, only for "deformable" vertices against "solid" triangles
///
// ---------------------------------------------------------

void DynamicSurface::handle_point_vs_solid_triangle_collisions( double dt )
{
   
   for(unsigned int i = 0; i < m_mesh.m_tris.size(); i++)
   {
      CollisionCandidateSet triangle_collision_candidates;
      add_triangle_candidates(i, triangle_collision_candidates);
      
      while( false == triangle_collision_candidates.empty() )
      {
         CollisionCandidateSet::iterator iter = triangle_collision_candidates.begin();
         Vec3ui candidate = *iter;
         triangle_collision_candidates.erase(iter);
      
         unsigned int t = candidate[0];
         Vec3ui tri = m_mesh.m_tris[t];
         unsigned int v = candidate[1];
         
         if ( m_masses[v] < 100 && m_masses[tri[0]] > 100 && m_masses[tri[1]] > 100 && m_masses[tri[2]] > 100 )
         {
         
            if(tri[0] != v && tri[1] != v && tri[2] != v)
            {
               double time, s1, s2, s3, rel_disp;
               Vec3d normal;
                            
               Vec3ui sorted_tri = sort_triangle( tri );
               
               assert( sorted_tri[0] < sorted_tri[1] && sorted_tri[0] < sorted_tri[2] && sorted_tri[1] < sorted_tri[2] );
               
               if ( point_triangle_collision( m_positions[v], m_newpositions[v], v, 
                                             m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                             m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                             m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                             s1, s2, s3,
                                             normal,
                                             time, rel_disp ) )                                 
                  
               {
                  
                  ++m_num_collisions_this_step;
                  
                  double relvel = rel_disp / dt;
                  
                  apply_triangle_point_impulse(sorted_tri, v, s1, s2, s3, normal, -relvel);
                                  
                  m_newpositions[v] = m_positions[v] + dt*m_velocities[v];
                  m_newpositions[tri[0]] = m_positions[tri[0]] + dt*m_velocities[tri[0]];
                  m_newpositions[tri[1]] = m_positions[tri[1]] + dt*m_velocities[tri[1]];
                  m_newpositions[tri[2]] = m_positions[tri[2]] + dt*m_velocities[tri[2]];
                  
                  update_continuous_broad_phase( v );
                  update_continuous_broad_phase( tri[0] );
                  update_continuous_broad_phase( tri[1] );
                  update_continuous_broad_phase( tri[2] );             
               }
                  
            }
         }
      }      
   }
   
}


// ---------------------------------------------------------
///
/// Detect all continuous collisions and apply impulses to prevent them.
/// Return true if all collisions were resolved.
///
// ---------------------------------------------------------

bool DynamicSurface::handle_collisions(double dt)
{
   
   const unsigned int MAX_PASS = 3;
   const unsigned int MAX_CANDIDATES = (unsigned int) 1e+6; 
   
   CollisionCandidateSet update_collision_candidates;
   
   if ( MAX_PASS == 0 )
   {
      return false;
   }
   
   bool collision_found = true;
   bool candidate_overflow = false;

   for ( unsigned int pass = 0; ( collision_found && (pass < MAX_PASS) ); ++pass )
   {
      collision_found = false;
      
      for(unsigned int i = 0; i < m_mesh.m_tris.size(); i++)
      {
         CollisionCandidateSet triangle_collision_candidates;
         add_triangle_candidates(i, triangle_collision_candidates);
         
         while( false == triangle_collision_candidates.empty() )
         {
            CollisionCandidateSet::iterator iter = triangle_collision_candidates.begin();
            Vec3ui candidate = *iter;
            triangle_collision_candidates.erase(iter);
            
            unsigned int t = candidate[0];
            Vec3ui tri = m_mesh.m_tris[t];
            unsigned int v = candidate[1];
            
            if(tri[0] != v && tri[1] != v && tri[2] != v)
            {
               double time, s1, s2, s3, rel_disp;
               Vec3d normal;              

               Vec3ui sorted_tri = sort_triangle( tri );

               if ( point_triangle_collision( m_positions[v], m_newpositions[v], v,
                                             m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                             m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                             m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                             s1, s2, s3,
                                             normal,
                                             time, rel_disp ) )               
                  
               {
                                                             
                  ++m_num_collisions_this_step;
                  
                  double relvel = rel_disp / dt;
                 
                  apply_triangle_point_impulse(sorted_tri, v, s1, s2, s3, normal, -relvel);
                  
                  if ( m_verbose ) std::cout << "(PT) time: " << time << ", relative velocity before: " << relvel;
                  
                  double relvel_after = dot(normal, m_velocities[v] - (s1*m_velocities[sorted_tri[0]] + s2*m_velocities[sorted_tri[1]] + s3*m_velocities[sorted_tri[2]]));
                  
                  if ( m_verbose ) std::cout << " and relative velocity after: " << relvel_after << std::endl;
                  
                  m_newpositions[v] = m_positions[v] + dt*m_velocities[v];
                  m_newpositions[tri[0]] = m_positions[tri[0]] + dt*m_velocities[tri[0]];
                  m_newpositions[tri[1]] = m_positions[tri[1]] + dt*m_velocities[tri[1]];
                  m_newpositions[tri[2]] = m_positions[tri[2]] + dt*m_velocities[tri[2]];
                  
                  update_continuous_broad_phase( v  );
                  update_continuous_broad_phase( tri[0] );
                  update_continuous_broad_phase( tri[1] );
                  update_continuous_broad_phase( tri[2] );
                                    
                  if ( pass == MAX_PASS - 1 )
                  {
                     if ( update_collision_candidates.size() < MAX_CANDIDATES )
                     {
                        add_point_update_candidates(v, update_collision_candidates);
                        add_point_update_candidates(tri[0], update_collision_candidates);
                        add_point_update_candidates(tri[1], update_collision_candidates);
                        add_point_update_candidates(tri[2], update_collision_candidates);
                     }
                     else
                     {
                        candidate_overflow = true;
                     }
                  }
                  
                  collision_found = true;
                  
               }            
            }
         }      
      }
         
      m_verbose = false;
      
      for(unsigned int i = 0; i < m_mesh.m_edges.size(); i++)
      {
         CollisionCandidateSet edge_collision_candidates;
         add_edge_candidates(i, edge_collision_candidates);
                           
         while ( false == edge_collision_candidates.empty() )
         {
            CollisionCandidateSet::iterator iter = edge_collision_candidates.begin();
            Vec3ui candidate = *iter;
            edge_collision_candidates.erase(iter);
                     
            Vec2ui e0 = m_mesh.m_edges[candidate[0]];
            Vec2ui e1 = m_mesh.m_edges[candidate[1]];
                                    
            assert( candidate[0] == i );
            
            if ( candidate[1] <= i ) { continue; }
            
            if ( e0[0] == e0[1] ) { continue; }
            if ( e1[0] == e1[1] ) { continue; }
               
            if(e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1])
            {
               double time, s0, s2, rel_disp;
               Vec3d normal;

               if ( e0[1] < e0[0] ) { swap( e0[0], e0[1] ); }
               if ( e1[1] < e1[0] ) { swap( e1[0], e1[1] ); }
               
               if ( ( e0[1] < e0[0] ) || ( e1[1] < e1[0] ) )
               {
                  std::cout << e0 << std::endl;
                  std::cout << e1 << std::endl;
                  assert(0);
               }
               
               if ( segment_segment_collision( m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                              m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                              m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                              m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                              s0, s2,
                                              normal,
                                              time, rel_disp ) )
                  
               {
                                    
                  ++m_num_collisions_this_step;
                  
                  double relvel = rel_disp / dt;
                  
                  if ( m_verbose ) 
                  {
                     std::cout << "(EE) time: " << time << ", relative velocity before: " << relvel;
                     std::cout << ", normal: " << normal;
                  }
                  
                  apply_edge_edge_impulse(e0, e1, s0, s2, normal, -relvel);
                  
                  double relvel_after = dot(normal, s0*m_velocities[e0[0]] + (1.0-s0)*m_velocities[e0[1]] - (s2*m_velocities[e1[0]] + (1.0-s2)*m_velocities[e1[1]]));
                  
                  if ( m_verbose ) std::cout << " and relative velocity after: " << relvel_after << std::endl;

                  m_newpositions[e0[0]] = m_positions[e0[0]] + dt*m_velocities[e0[0]];
                  m_newpositions[e0[1]] = m_positions[e0[1]] + dt*m_velocities[e0[1]];
                  m_newpositions[e1[0]] = m_positions[e1[0]] + dt*m_velocities[e1[0]];
                  m_newpositions[e1[1]] = m_positions[e1[1]] + dt*m_velocities[e1[1]];
                  
                  update_continuous_broad_phase( e0[0] );
                  update_continuous_broad_phase( e0[1] );
                  update_continuous_broad_phase( e1[0] );
                  update_continuous_broad_phase( e1[1] );
                                    
                  if ( pass == MAX_PASS - 1 )
                  {
                     if ( update_collision_candidates.size() < MAX_CANDIDATES )
                     {
                        add_point_update_candidates(e0[0], update_collision_candidates);
                        add_point_update_candidates(e0[1], update_collision_candidates);
                        add_point_update_candidates(e1[0], update_collision_candidates);
                        add_point_update_candidates(e1[1], update_collision_candidates);
                     }
                     else
                     {
                        candidate_overflow = true;
                     }
                  }
                  
                  collision_found = true;
                  
                  m_verbose = false;
                  
               }               
            }
         }      
      }
         
   }
   
   {
      CollisionCandidateSet::iterator new_end = std::unique( update_collision_candidates.begin(), update_collision_candidates.end() );
      update_collision_candidates.erase( new_end, update_collision_candidates.end() );
   }
   
   unsigned int n = update_collision_candidates.size();
   unsigned int c = 0;
   
   while( !update_collision_candidates.empty() && c++ < (5 * n) )
   {

      CollisionCandidateSet::iterator iter = update_collision_candidates.begin();
      Vec3ui candidate = *iter;
      update_collision_candidates.erase(iter);
            
      if(candidate[2]==0)
      {
         unsigned int t = candidate[0];
         const Vec3ui& tri = m_mesh.m_tris[t];
         unsigned int v = candidate[1];
         
         if(tri[0] != v && tri[1] != v && tri[2] != v)
         {
            double time, s1, s2, s3, rel_disp;
            Vec3d normal;
            
            Vec3ui sorted_tri = sort_triangle( tri );            
            
            if ( point_triangle_collision( m_positions[v], m_newpositions[v], v,
                                          m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                          m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                          m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                          s1, s2, s3,
                                          normal,
                                          time, rel_disp ) )               
               
            {

               ++m_num_collisions_this_step;
               
               double relvel = rel_disp / dt;
               
               if ( m_verbose ) std::cout << "VT ( " << v << " " << tri << " ) relative velocity before: " << relvel; 
               
               apply_triangle_point_impulse( sorted_tri, v, s1, s2, s3, normal, -relvel);
               
               double relvel_after = dot(normal, m_velocities[v] - (s1*m_velocities[tri[0]] + s2*m_velocities[tri[1]] + s3*m_velocities[tri[2]]));
               
               if ( m_verbose ) std::cout << " and relative velocity after: " << relvel_after << std::endl;

               m_newpositions[v] = m_positions[v] + dt*m_velocities[v];
               m_newpositions[tri[0]] = m_positions[tri[0]] + dt*m_velocities[tri[0]];
               m_newpositions[tri[1]] = m_positions[tri[1]] + dt*m_velocities[tri[1]];
               m_newpositions[tri[2]] = m_positions[tri[2]] + dt*m_velocities[tri[2]];
               
               update_continuous_broad_phase( v  );
               update_continuous_broad_phase( tri[0] );
               update_continuous_broad_phase( tri[1] );
               update_continuous_broad_phase( tri[2] );
               
               if ( update_collision_candidates.size() < MAX_CANDIDATES )
               {
                  add_point_update_candidates(v, update_collision_candidates);
                  add_point_update_candidates(tri[0], update_collision_candidates);
                  add_point_update_candidates(tri[1], update_collision_candidates);
                  add_point_update_candidates(tri[2], update_collision_candidates);
               }
               else
               {
                  candidate_overflow = true;
               }
            }
         }
      }
      else
      {
         Vec2ui e0 = m_mesh.m_edges[candidate[0]];
         Vec2ui e1 = m_mesh.m_edges[candidate[1]];
         if(e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1])
         {
            if ( e0[1] < e0[0] ) { swap( e0[0], e0[1] ); }
            if ( e1[1] < e1[0] ) { swap( e1[0], e1[1] ); }
            
            double time, s0, s2, rel_disp;
            Vec3d normal;
            
            if ( segment_segment_collision( m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                           m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                           m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                           m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                           s0, s2,
                                           normal,
                                           time, rel_disp ) )
               
            {

               ++m_num_collisions_this_step;
               
               double relvel = rel_disp / dt;
               
               if ( m_verbose ) std::cout << "EE relative velocity before: " << relvel;
               
               apply_edge_edge_impulse(e0, e1, s0, s2, normal, -relvel);
               
               double relvel_after = dot(normal, s0*m_velocities[e0[0]] + (1.0-s0)*m_velocities[e0[1]] - (s2*m_velocities[e1[0]] + (1.0-s2)*m_velocities[e1[1]]));
               
               if ( m_verbose ) std::cout << " and relative velocity after: " << relvel_after << std::endl;            
                              
               m_newpositions[e0[0]] = m_positions[e0[0]] + dt*m_velocities[e0[0]];
               m_newpositions[e0[1]] = m_positions[e0[1]] + dt*m_velocities[e0[1]];
               m_newpositions[e1[0]] = m_positions[e1[0]] + dt*m_velocities[e1[0]];
               m_newpositions[e1[1]] = m_positions[e1[1]] + dt*m_velocities[e1[1]];
                              
               
               update_continuous_broad_phase( e0[0] );
               update_continuous_broad_phase( e0[1] );
               update_continuous_broad_phase( e1[0] );
               update_continuous_broad_phase( e1[1] );
               
               if ( update_collision_candidates.size() < MAX_CANDIDATES )
               {
                  add_point_update_candidates(e0[0], update_collision_candidates);
                  add_point_update_candidates(e0[1], update_collision_candidates);
                  add_point_update_candidates(e1[0], update_collision_candidates);
                  add_point_update_candidates(e1[1], update_collision_candidates);
               }
               else
               {
                  candidate_overflow = true;
               }
               
            }
         }
      }
      
   }

   
   return ( !candidate_overflow ) && ( update_collision_candidates.empty() );
   
}



// ---------------------------------------------------------
///
/// Detect all continuous collisions
///
// ---------------------------------------------------------

bool DynamicSurface::detect_collisions( std::vector<Collision>& collisions )
{
   
   static const unsigned int MAX_COLLISIONS = 5000;
   
   rebuild_continuous_broad_phase();
  
   //
   // point-triangle
   //
   
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {     
      const Vec3ui& tri = m_mesh.m_tris[i];
      
      if ( tri[0] == tri[1] || tri[1] == tri[2] || tri[2] == tri[0] )    { continue; }

      Vec3d low, high;
      triangle_continuous_bounds( i, low, high );
      
      std::vector<unsigned int> potential_collisions;
      
      m_broad_phase->get_potential_vertex_collisions( low, high, potential_collisions );
      
      for ( unsigned int j = 0; j < potential_collisions.size(); ++j )
      {
         unsigned int vertex_index = potential_collisions[j];
         
         assert ( m_mesh.m_vtxtri[vertex_index].size() != 0 );
      
         if( tri[0] != vertex_index && tri[1] != vertex_index && tri[2] != vertex_index )
         {
            double time, s1, s2, s3, rel_disp;
            Vec3d normal;
            
            Vec3ui sorted_tri = sort_triangle( tri );            
            
            if ( point_triangle_collision( m_positions[vertex_index], m_newpositions[vertex_index], vertex_index,
                                           m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                           m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                           m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                           s1, s2, s3,
                                           normal,
                                           time, rel_disp ) )               
               
            {
               ++m_num_collisions_this_step;
                              
               Collision new_collision( false, Vec4ui( vertex_index, sorted_tri[0], sorted_tri[1], sorted_tri[2] ), normal, Vec4d( 1, -s1, -s2, -s3 ), rel_disp );
                                             
               collisions.push_back( new_collision );
               
               if ( collisions.size() > MAX_COLLISIONS ) 
               {
                  return false; 
               }
            }            
         }
      }
   }
   
   //
   // edge-edge
   //

   for ( unsigned int edge_index_a = 0; edge_index_a < m_mesh.m_edges.size(); ++edge_index_a )
   {
      if ( m_mesh.m_edges[edge_index_a][0] == m_mesh.m_edges[edge_index_a][1] )    { continue; }
      
      Vec3d low, high;
      edge_continuous_bounds(edge_index_a, low, high);
      std::vector<unsigned int> potential_collisions;
      m_broad_phase->get_potential_edge_collisions( low, high, potential_collisions );
      
      for ( unsigned int j = 0; j < potential_collisions.size(); ++j )
      {
   
         unsigned int edge_index_b = potential_collisions[j];
         
         if ( edge_index_b <= edge_index_a )    { continue; }
         
         assert ( m_mesh.m_edges[edge_index_b][0] != m_mesh.m_edges[edge_index_b][1] );
                  
         Vec2ui e0 = m_mesh.m_edges[edge_index_a];
         Vec2ui e1 = m_mesh.m_edges[edge_index_b];
         
         if( e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1] )
         {            
            
            double time, s0, s2, rel_disp;
            Vec3d normal;
            
            if ( e0[1] < e0[0] ) { swap( e0[0], e0[1] ); }
            if ( e1[1] < e1[0] ) { swap( e1[0], e1[1] ); }
            
            if ( segment_segment_collision( m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                            m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                            m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                            m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                            s0, s2,
                                            normal,
                                            time, rel_disp ) )
               
            {
                  
               ++m_num_collisions_this_step;
               
               Collision new_collision( true, Vec4ui( e0[0], e0[1], e1[0], e1[1] ), normal, Vec4d( -s0, -(1-s0), s2, (1-s2) ), rel_disp );
                              
               collisions.push_back( new_collision );
               
               if ( collisions.size() > MAX_COLLISIONS ) 
               {
                  std::cout << "maxed out collisions at edge " << edge_index_a << std::endl;
                  return false; 
               }                 
            }
            else if ( segment_segment_collision( m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                                 m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                                 m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                                 m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                                 s0, s2,
                                                 normal,
                                                 time, rel_disp ) )
               
            {
               
               ++m_num_collisions_this_step;
               
               Collision new_collision( true, Vec4ui( e0[0], e0[1], e1[0], e1[1] ), normal, Vec4d( -s0, -(1-s0), s2, (1-s2) ), rel_disp );
               
               collisions.push_back( new_collision );
               
               if ( collisions.size() > MAX_COLLISIONS ) 
               {
                  std::cout << "maxed out collisions at edge " << edge_index_a << std::endl;
                  return false; 
               }               
               
            }
            
         }
      }
   }
   
   return true;
   
}




// ---------------------------------------------------------
///
/// Detect continuous collisions among elements in the given ImpactZones, and adjacent to the given ImpactZones.
///
// ---------------------------------------------------------

void DynamicSurface::detect_new_collisions( const std::vector<ImpactZone> impact_zones, std::vector<Collision>& collisions )
{

   rebuild_continuous_broad_phase();
   
   std::vector<unsigned int> zone_vertices;
   std::vector<unsigned int> zone_edges;
   std::vector<unsigned int> zone_triangles;

   // Get all vertices in the impact zone
   
   for ( unsigned int i = 0; i < impact_zones.size(); ++i )
   {
      for ( unsigned int j = 0; j < impact_zones[i].collisions.size(); ++j )
      {
         add_unique( zone_vertices, impact_zones[i].collisions[j].vertex_indices[0] );
         add_unique( zone_vertices, impact_zones[i].collisions[j].vertex_indices[1] );
         add_unique( zone_vertices, impact_zones[i].collisions[j].vertex_indices[2] );
         add_unique( zone_vertices, impact_zones[i].collisions[j].vertex_indices[3] );         
         
         update_continuous_broad_phase( impact_zones[i].collisions[j].vertex_indices[0] );
         update_continuous_broad_phase( impact_zones[i].collisions[j].vertex_indices[1] );
         update_continuous_broad_phase( impact_zones[i].collisions[j].vertex_indices[2] );
         update_continuous_broad_phase( impact_zones[i].collisions[j].vertex_indices[3] );         
         
      }
   }
   
   // Get all triangles in the impact zone
   
   for ( unsigned int i = 0; i < zone_vertices.size(); ++i )
   {
      for ( unsigned int j = 0; j < m_mesh.m_vtxtri[zone_vertices[i]].size(); ++j )
      {
         add_unique( zone_triangles, m_mesh.m_vtxtri[zone_vertices[i]][j] );
      }
   }

   // Get all edges in the impact zone
   
   for ( unsigned int i = 0; i < zone_vertices.size(); ++i )
   {
      for ( unsigned int j = 0; j < m_mesh.m_vtxedge[zone_vertices[i]].size(); ++j )
      {
         add_unique( zone_edges, m_mesh.m_vtxedge[zone_vertices[i]][j] );
      }
   }

   // Check zone vertices vs all triangles
   
   for ( unsigned int i = 0; i < zone_vertices.size(); ++i )
   {
      unsigned int vertex_index = zone_vertices[i];

      Vec3d query_low, query_high;
      vertex_continuous_bounds( zone_vertices[i], query_low, query_high );
      std::vector<unsigned int> overlapping_triangles;
      m_broad_phase->get_potential_triangle_collisions( query_low, query_high, overlapping_triangles );
      
      for ( unsigned int j = 0; j < overlapping_triangles.size(); ++j )
      {
         const Vec3ui& tri = m_mesh.m_tris[overlapping_triangles[j]];
         
         assert( m_mesh.m_vtxtri[vertex_index].size() != 0 );
         
         if( tri[0] != vertex_index && tri[1] != vertex_index && tri[2] != vertex_index )
         {
            double time, s1, s2, s3, rel_disp;
            Vec3d normal;
            
            Vec3ui sorted_tri = sort_triangle( tri );            
            assert( sorted_tri[0] < sorted_tri[1] && sorted_tri[1] < sorted_tri[2] && sorted_tri[0] < sorted_tri[2] );
            
            if ( point_triangle_collision( m_positions[vertex_index], m_newpositions[vertex_index], vertex_index,
                                                    m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                                    m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                                    m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                                    s1, s2, s3,
                                                    normal,
                                                    time, rel_disp ) )               
               
            {
                             
               assert( fabs(mag(normal) - 1.0) < 1e-10 );
               
               Collision new_collision( false, Vec4ui( vertex_index, sorted_tri[0], sorted_tri[1], sorted_tri[2] ), normal, Vec4d( 1, -s1, -s2, -s3 ), rel_disp );
               
               add_unique_collision( collisions, new_collision );
               
               bool exists = false;
               for ( unsigned int z = 0; z < impact_zones.size(); ++z )
               {
                  for ( unsigned int c = 0; c < impact_zones[z].collisions.size(); ++c )
                  {
                     if ( new_collision.same_vertices( impact_zones[z].collisions[c] ) )
                     {
                        std::cout << "duplicate collision: " << new_collision.vertex_indices << std::endl;
                        exists = true;
                     }
                  }
               }
               
               if ( !exists )
               {
                  ++m_num_collisions_this_step;
               }
               
            } 
         }
      }
   }
   
   // Check zone triangles vs all vertices
   
   for ( unsigned int i = 0; i < zone_triangles.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[zone_triangles[i]];
      
      Vec3d query_low, query_high;
      triangle_continuous_bounds( zone_triangles[i], query_low, query_high );
      std::vector<unsigned int> overlapping_vertices;
      m_broad_phase->get_potential_vertex_collisions( query_low, query_high, overlapping_vertices );
      
      for ( unsigned int j = 0; j < overlapping_vertices.size(); ++j )
      {                      
         unsigned int vertex_index = overlapping_vertices[j];
         
         assert( m_mesh.m_vtxtri[vertex_index].size() != 0 );
         
         if( tri[0] != vertex_index && tri[1] != vertex_index && tri[2] != vertex_index )
         {
            double time, s1, s2, s3, rel_disp;
            Vec3d normal;
            
            Vec3ui sorted_tri = sort_triangle( tri ); 
            assert( sorted_tri[0] < sorted_tri[1] && sorted_tri[1] < sorted_tri[2] && sorted_tri[0] < sorted_tri[2] );
                        
            if ( point_triangle_collision( m_positions[vertex_index], m_newpositions[vertex_index], vertex_index,
                                                    m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                                    m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                                    m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                                    s1, s2, s3,
                                                    normal,
                                                    time, rel_disp ) )                
            {
               
               assert( fabs(mag(normal) - 1.0) < 1e-10 );
               
               Collision new_collision( false, Vec4ui( vertex_index, sorted_tri[0], sorted_tri[1], sorted_tri[2] ), normal, Vec4d( 1, -s1, -s2, -s3 ), rel_disp );                              
               
               add_unique_collision( collisions, new_collision );
               
               bool exists = false;
               for ( unsigned int z = 0; z < impact_zones.size(); ++z )
               {
                  for ( unsigned int c = 0; c < impact_zones[z].collisions.size(); ++c )
                  {
                     if ( new_collision.same_vertices( impact_zones[z].collisions[c] ) )
                     {
                        std::cout << "duplicate collision: " << new_collision.vertex_indices << std::endl;
                        exists = true;
                     }
                  }
               }
               
               if ( !exists )
               {
                  ++m_num_collisions_this_step;
               }
               
               
            } 
         }
      }
   }
   
   // Check zone edges vs all edges
   
   for ( unsigned int i = 0; i < zone_edges.size(); ++i )
   {
      unsigned int edge_index_a = zone_edges[i];
      
      if ( m_mesh.m_edges[edge_index_a][0] == m_mesh.m_edges[edge_index_a][1] )    { continue; }
      
      Vec3d low, high;
      edge_continuous_bounds(edge_index_a, low, high);
      std::vector<unsigned int> potential_collisions;
      m_broad_phase->get_potential_edge_collisions( low, high, potential_collisions );
            
      for ( unsigned int j = 0; j < potential_collisions.size(); ++j )
      {   
         unsigned int edge_index_b = potential_collisions[j];
         
         assert ( m_mesh.m_edges[edge_index_b][0] != m_mesh.m_edges[edge_index_b][1] );    
         
         Vec2ui e0 = m_mesh.m_edges[edge_index_a];
         Vec2ui e1 = m_mesh.m_edges[edge_index_b];
         
         if( e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1] )
         {
            if ( e0[1] < e0[0] ) { swap( e0[0], e0[1] ); }
            if ( e1[1] < e1[0] ) { swap( e1[0], e1[1] ); }
            
            assert( e0[0] < e0[1] && e1[0] < e1[1] );
            
            double time, s0, s2, rel_disp;
            Vec3d normal;
            
            if ( segment_segment_collision( m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                            m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                            m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                            m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                            s0, s2,
                                            normal,
                                            time, rel_disp ) )
               
            {
                              
               normalize(normal);
               
               Collision new_collision( true, Vec4ui( e0[0], e0[1], e1[0], e1[1] ), normal, Vec4d( -s0, -(1-s0), s2, (1-s2) ), rel_disp );
               
               add_unique_collision( collisions, new_collision );
               
               
               bool exists = false;
               for ( unsigned int z = 0; z < impact_zones.size(); ++z )
               {
                  for ( unsigned int c = 0; c < impact_zones[z].collisions.size(); ++c )
                  {
                     if ( new_collision.same_vertices( impact_zones[z].collisions[c] ) )
                     {
                        std::cout << "duplicate collision: " << new_collision.vertex_indices << std::endl;
                        exists = true;
                     }
                  }
               }
               
               if ( !exists )
               {
                  ++m_num_collisions_this_step;
               }
               

            }
            else if ( segment_segment_collision( m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                                 m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                                 m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                                 m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                                 s0, s2,
                                                 normal,
                                                 time, rel_disp ) )
            {
               normalize(normal);
               
               Collision new_collision( true, Vec4ui( e1[0], e1[1], e0[0], e0[1] ), normal, Vec4d( -s0, -(1-s0), s2, (1-s2) ), rel_disp );
               
               add_unique_collision( collisions, new_collision );
               
               bool exists = false;
               for ( unsigned int z = 0; z < impact_zones.size(); ++z )
               {
                  for ( unsigned int c = 0; c < impact_zones[z].collisions.size(); ++c )
                  {
                     if ( new_collision.same_vertices( impact_zones[z].collisions[c] ) )
                     {
                        std::cout << "duplicate collision: " << new_collision.vertex_indices << std::endl;
                        exists = true;
                     }
                  }
               }
               
               if ( !exists )
               {
                  ++m_num_collisions_this_step;
               } 
            }
         }
      }
   }
}




// ---------------------------------------------------------
///
/// Combine impact zones which have overlapping vertex stencils
///
// ---------------------------------------------------------

void DynamicSurface::merge_impact_zones( std::vector<ImpactZone>& new_impact_zones, std::vector<ImpactZone>& master_impact_zones )
{
   
   bool merge_ocurred = true;
      
   for ( unsigned int i = 0; i < master_impact_zones.size(); ++i )
   {
      master_impact_zones[i].all_solved = true;
   }

   for ( unsigned int i = 0; i < new_impact_zones.size(); ++i )
   {
      new_impact_zones[i].all_solved = false;
   }

   
   while ( merge_ocurred )
   {
            
      merge_ocurred = false;
           
      for ( unsigned int i = 0; i < new_impact_zones.size(); ++i )
      {
         bool i_is_disjoint = true;
         
         for ( unsigned int j = 0; j < master_impact_zones.size(); ++j )
         {
            // check if impact zone i and j share any vertices
            
            if ( master_impact_zones[j].share_vertices( new_impact_zones[i] ) )
            {
               
               bool found_new_collision = false;
               
               // steal all of j's collisions
               for ( unsigned int c = 0; c < new_impact_zones[i].collisions.size(); ++c )
               {

                  bool same_collision_exists = false;
                  
                  for ( unsigned int m = 0; m < master_impact_zones[j].collisions.size(); ++m )
                  {                 
                     if ( master_impact_zones[j].collisions[m].same_vertices( new_impact_zones[i].collisions[c] ) )
                     {

                        same_collision_exists = true;
                        break;
                     }
                     
                  }
                  
                  if ( !same_collision_exists )
                  {
                     master_impact_zones[j].collisions.push_back( new_impact_zones[i].collisions[c] );
                     found_new_collision = true;
                  }
               }
               
               // did we find any collisions in zone i that zone j didn't already have?
               if ( found_new_collision )
               {
                  master_impact_zones[j].all_solved &= new_impact_zones[i].all_solved;
               }
               
               merge_ocurred = true;
               i_is_disjoint = false;
               break;
            }
            
         }     // end for(j)
         
         if ( i_is_disjoint )
         {
            // copy the impact zone
            
            ImpactZone new_zone;
            for ( unsigned int c = 0; c < new_impact_zones[i].collisions.size(); ++c )
            {
               new_zone.collisions.push_back( new_impact_zones[i].collisions[c] );
            }
            
            new_zone.all_solved = new_impact_zones[i].all_solved;
            
            master_impact_zones.push_back( new_zone );
         }
      }     // end for(i)
      
      new_impact_zones = master_impact_zones;
      master_impact_zones.clear();
      
   }  // while

   master_impact_zones = new_impact_zones;
     
}


// ---------------------------------------------------------
///
/// Iteratively project out relative normal velocities for a set of collisions in an impact zone until all collisions are solved.
///
// ---------------------------------------------------------

bool DynamicSurface::iterated_inelastic_projection( ImpactZone& iz, double dt )
{
   assert( m_masses.size() == m_positions.size() );
   
   static const unsigned int MAX_PROJECTION_ITERATIONS = 20;
   
   for ( unsigned int i = 0; i < MAX_PROJECTION_ITERATIONS; ++i )
   {
      m_verbose = true;
      bool success = inelastic_projection( iz );
      m_verbose = false;
            
      if ( !success )
      {
         std::cout << "failure in inelastic projection" << std::endl;
         return false;
      }
      
      bool collision_still_exists = false;
      
      for ( unsigned int c = 0; c < iz.collisions.size(); ++c )
      {
         // run collision detection on this pair again
         
         Collision& collision = iz.collisions[c];
         const Vec4ui& vs = collision.vertex_indices;
            
         m_newpositions[vs[0]] = m_positions[vs[0]] + dt * m_velocities[vs[0]];
         m_newpositions[vs[1]] = m_positions[vs[1]] + dt * m_velocities[vs[1]];
         m_newpositions[vs[2]] = m_positions[vs[2]] + dt * m_velocities[vs[2]];
         m_newpositions[vs[3]] = m_positions[vs[3]] + dt * m_velocities[vs[3]];
            
         if ( m_verbose ) { std::cout << "checking collision " << vs << std::endl; }
         
         if ( collision.is_edge_edge )
         {
            
            double time, s0, s2, rel_disp;
            Vec3d normal;
            
            assert( vs[0] < vs[1] && vs[2] < vs[3] );       // should have been sorted by original collision detection
            
            
            if ( segment_segment_collision( m_positions[vs[0]], m_newpositions[vs[0]], vs[0],
                                                     m_positions[vs[1]], m_newpositions[vs[1]], vs[1],
                                                     m_positions[vs[2]], m_newpositions[vs[2]], vs[2],
                                                     m_positions[vs[3]], m_newpositions[vs[3]], vs[3],
                                                     s0, s2,
                                                     normal,
                                                     time, rel_disp, false ) )               
            {
               
               std::cout << "collision remains.  delta alphas: " << Vec4d( -s0, -(1-s0), s2, (1-s2) ) - collision.alphas << std::endl;
               std::cout << "alphas: " << Vec4d( -s0, -(1-s0), s2, (1-s2) ) << std::endl;
               std::cout << "normal: " << normal << std::endl;
               std::cout << "rel_disp: " << rel_disp << std::endl;
               std::cout << "time: " << time << std::endl;               
               collision.normal = normal;
               collision.alphas = Vec4d( -s0, -(1-s0), s2, (1-s2) );
               collision.relative_displacement = rel_disp;
               collision_still_exists = true;
            }
            
         }
         else
         {
               
            double time, s1, s2, s3, rel_disp;
            Vec3d normal;
            
            assert( vs[1] < vs[2] && vs[2] < vs[3] && vs[1] < vs[3] );    // should have been sorted by original collision detection
            
            if ( point_triangle_collision( m_positions[vs[0]], m_newpositions[vs[0]], vs[0],
                                                    m_positions[vs[1]], m_newpositions[vs[1]], vs[1],
                                                    m_positions[vs[2]], m_newpositions[vs[2]], vs[2],
                                                    m_positions[vs[3]], m_newpositions[vs[3]], vs[3],
                                                    s1, s2, s3,
                                                    normal,
                                                    time, rel_disp, false ) )                                 
            {
               std::cout << "collision remains.  delta alphas: " << Vec4d( 1, -s1, -s2, -s3 ) - collision.alphas << std::endl;
               std::cout << "alphas: " << Vec4d( 1, -s1, -s2, -s3 ) << std::endl;            
               std::cout << "normal: " << normal << std::endl;
               std::cout << "rel_disp: " << rel_disp << std::endl;
               std::cout << "time: " << time << std::endl;               
               collision.normal = normal;
               collision.alphas = Vec4d( 1, -s1, -s2, -s3 );
               collision.relative_displacement = rel_disp;
               collision_still_exists = true;
            }
            
         }
         
      } // for collisions
      
      if ( false == collision_still_exists )  
      {
         return true; 
      }
      
   } // for iterations
 
   std::cout << "reached max iterations for this zone" << std::endl;

   return false;
   
}


// ---------------------------------------------------------
///
/// Project out relative normal velocities for a set of collisions in an impact zone.
///
// ---------------------------------------------------------

bool DynamicSurface::inelastic_projection( const ImpactZone& iz )
{
   
   if ( m_verbose )
   {
      std::cout << " ----- using sparse solver " << std::endl;
   }
   
   static double IMPULSE_MULTIPLIER = 0.8;
   
   const unsigned int k = iz.collisions.size();    // notation from [Harmon et al 2008]: k == number of collisions
   
   std::vector<unsigned int> zone_vertices;
   iz.get_all_vertices( zone_vertices );
   
   const unsigned int n = zone_vertices.size();       // n == number of distinct colliding vertices
   
   if ( m_verbose )
   {
      std::cout << "GCT: " << 3*n << "x" << k << std::endl;
   }
   
   SparseMatrixDynamicCSR GCT( 3*n, k );
   GCT.set_zero();
   
   // construct matrix grad C transpose
   for ( unsigned int i = 0; i < k; ++i )
   {
      // set col i
      const Collision& coll = iz.collisions[i];
      
      for ( unsigned int v = 0; v < 4; ++v )
      {
         // block row j ( == block column j of grad C )
         unsigned int j = coll.vertex_indices[v];
         
         std::vector<unsigned int>::iterator zone_vertex_iter = find( zone_vertices.begin(), zone_vertices.end(), j );
         
         assert( zone_vertex_iter != zone_vertices.end() );
         
         unsigned int mat_j = (unsigned int) ( zone_vertex_iter - zone_vertices.begin() );
         
         GCT(mat_j*3, i) = coll.alphas[v] * coll.normal[0];
         GCT(mat_j*3+1, i) = coll.alphas[v] * coll.normal[1];
         GCT(mat_j*3+2, i) = coll.alphas[v] * coll.normal[2];
         
      }
   }

   Array1d inv_masses;
   inv_masses.reserve(3*n);
   Array1d column_velocities;
   column_velocities.reserve(3*n);
   
   for ( unsigned int i = 0; i < n; ++i )
   {
      if ( m_masses[zone_vertices[i]] < 100.0 )
      {
         inv_masses.push_back( 1.0 / m_masses[zone_vertices[i]] );
         inv_masses.push_back( 1.0 / m_masses[zone_vertices[i]] );
         inv_masses.push_back( 1.0 / m_masses[zone_vertices[i]] );
      }
      else
      {
         // infinite mass (scripted objects)
         
         inv_masses.push_back( 0.0 );
         inv_masses.push_back( 0.0 );
         inv_masses.push_back( 0.0 );         
      }

      column_velocities.push_back( m_velocities[zone_vertices[i]][0] );
      column_velocities.push_back( m_velocities[zone_vertices[i]][1] );
      column_velocities.push_back( m_velocities[zone_vertices[i]][2] );
   }

   //
   // minimize | M^(-1/2) * GC^T x - M^(1/2) * v |^2
   //
   
   // solution vector
   Array1d x(k);
         
   static const bool use_cgnr = false;
   KrylovSolverStatus solver_result;
   
   if ( use_cgnr )
   {
      std::cout << "CGNR currently disabled: matrices are not scaled by masses." << std::endl;
      assert( false );
      
      CGNR_Solver cg_solver;
      SparseMatrixStaticCSR solver_matrix( GCT );
      cg_solver.max_iterations = INT_MAX;
      solver_result = cg_solver.solve( solver_matrix, column_velocities.data, x.data );      
   }
   else
   {
      // normal equations: GC * M^(-1) GCT * x = GC * v
      //                   A * x = b

      SparseMatrixDynamicCSR A( k, k );
      A.set_zero();
      AtDB( GCT, inv_masses.data, GCT, A ); 
      
      Array1d b(k);
      GCT.apply_transpose( column_velocities.data, b.data );   

      if ( m_verbose )  { std::cout << "system built" << std::endl; }

      MINRES_CR_Solver solver;   
      SparseMatrixStaticCSR solver_matrix( A );    // convert dynamic to static
      solver.max_iterations = 1000;
      solver_result = solver.solve( solver_matrix, b.data, x.data ); 
   }

   if ( solver_result != KRYLOV_CONVERGED )
   {
      std::cout << "CR solver failed: ";
      
      if ( solver_result == KRYLOV_BREAKDOWN )
      {
         std::cout << "KRYLOV_BREAKDOWN" << std::endl;
      }
      else
      {
         std::cout << "KRYLOV_EXCEEDED_MAX_ITERATIONS" << std::endl;
      }
      
      return false;          
   } 
   
   // apply impulses 
   Array1d applied_impulses(3*n);
   GCT.apply( x.data, applied_impulses.data );
     
   for ( unsigned int i = 0; i < applied_impulses.size(); ++i )
   {
      column_velocities[i] -= IMPULSE_MULTIPLIER * inv_masses[i] * applied_impulses[i];      
   }
   
   for ( unsigned int i = 0; i < n; ++i )
   {
      Vec3d new_velocity( column_velocities[3*i], column_velocities[3*i + 1], column_velocities[3*i + 2] );
      
      m_velocities[zone_vertices[i]][0] = column_velocities[3*i];
      m_velocities[zone_vertices[i]][1] = column_velocities[3*i + 1];
      m_velocities[zone_vertices[i]][2] = column_velocities[3*i + 2];      
   }
    
   
   return true;
   
}


// ---------------------------------------------------------
///
/// Handle all collisions simultaneously by iteratively solving individual impact zones until no new collisions are detected.
///
// ---------------------------------------------------------

bool DynamicSurface::handle_collisions_simultaneous(double dt)
{

   // copy
   std::vector<Vec3d> old_velocities = m_velocities;

   std::vector<ImpactZone> impact_zones;

   bool finished_detecting_collisions = false;
   
   std::vector<Collision> total_collisions;
   finished_detecting_collisions = detect_collisions(total_collisions);
      
   while ( false == total_collisions.empty() )
   {      
      // insert each new collision constraint into its own impact zone
      std::vector<ImpactZone> new_impact_zones;
      for ( unsigned int i = 0; i < total_collisions.size(); ++i )
      {
         ImpactZone new_zone;
         new_zone.collisions.push_back( total_collisions[i] );
         new_impact_zones.push_back( new_zone );
      }
      
      assert( new_impact_zones.size() == total_collisions.size() );

      // merge all impact zones that share vertices
      merge_impact_zones( new_impact_zones, impact_zones );

      for ( int i = 0; i < (int) impact_zones.size(); ++i )
      {
         if ( impact_zones[i].all_solved ) 
         {
            impact_zones.erase( impact_zones.begin() + i );
            --i;
         }
      }

      for ( int i = 0; i < (int) impact_zones.size(); ++i )
      {
         assert( false == impact_zones[i].all_solved );
      }            
            
      bool solver_ok = true;
      
      // for each impact zone
      for ( unsigned int i = 0; i < impact_zones.size(); ++i )
      {
         
         std::vector<unsigned int> zone_vertices;
         
         // reset impact zone to pre-response m_velocities
         for ( unsigned int j = 0; j < impact_zones[i].collisions.size(); ++j )
         {
            Vec4ui& vs = impact_zones[i].collisions[j].vertex_indices;
            
            m_velocities[vs[0]] = old_velocities[vs[0]];
            m_velocities[vs[1]] = old_velocities[vs[1]];
            m_velocities[vs[2]] = old_velocities[vs[2]];
            m_velocities[vs[3]] = old_velocities[vs[3]]; 
            
            zone_vertices.push_back( vs[0] );
            zone_vertices.push_back( vs[1] );
            zone_vertices.push_back( vs[2] );
            zone_vertices.push_back( vs[3] );            
         }
         
         // apply inelastic projection
         
         solver_ok &= iterated_inelastic_projection( impact_zones[i], dt );
                  
         // reset predicted m_positions
         for ( unsigned int j = 0; j < impact_zones[i].collisions.size(); ++j )
         {
            const Vec4ui& vs = impact_zones[i].collisions[j].vertex_indices;            

            m_newpositions[vs[0]] = m_positions[vs[0]] + dt * m_velocities[vs[0]];
            m_newpositions[vs[1]] = m_positions[vs[1]] + dt * m_velocities[vs[1]];
            m_newpositions[vs[2]] = m_positions[vs[2]] + dt * m_velocities[vs[2]];
            m_newpositions[vs[3]] = m_positions[vs[3]] + dt * m_velocities[vs[3]];
         } 
      
      }  // for IZs
      
      if ( false == solver_ok )
      {
         std::cout << "solver problem" << std::endl;
         return false;
      }
      
      total_collisions.clear();
      
      if ( !finished_detecting_collisions )
      {
         std::cout << "attempting to finish global collision detection" << std::endl;
         finished_detecting_collisions = detect_collisions( total_collisions );
         impact_zones.clear();
      }
      else
      {
         detect_new_collisions( impact_zones, total_collisions );
      }
      
   }
   
   return true;
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

bool DynamicSurface::collision_solved( const Collision& collision )
{
   if ( collision.is_edge_edge )
   {
      Vec2ui e0( collision.vertex_indices[0], collision.vertex_indices[1] );
      Vec2ui e1( collision.vertex_indices[2], collision.vertex_indices[3] );
      
      double time, s0, s2, rel_disp;
      Vec3d normal;
      
      if ( e0[1] < e0[0] ) { swap( e0[0], e0[1] ); }
      if ( e1[1] < e1[0] ) { swap( e1[0], e1[1] ); }
      
      if ( segment_segment_collision( m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                     m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                     m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                     m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                     s0, s2,
                                     normal,
                                     time, rel_disp ) )
         
      {
         return false;
      }
      else if ( segment_segment_collision( m_positions[e1[0]], m_newpositions[e1[0]], e1[0],
                                          m_positions[e1[1]], m_newpositions[e1[1]], e1[1],
                                          m_positions[e0[0]], m_newpositions[e0[0]], e0[0],
                                          m_positions[e0[1]], m_newpositions[e0[1]], e0[1],
                                          s0, s2,
                                          normal,
                                          time, rel_disp ) )
         
      {
         return false;
      }
      
   }
   else
   {
      unsigned int vertex_index = collision.vertex_indices[0];
      Vec3ui tri( collision.vertex_indices[1], collision.vertex_indices[2], collision.vertex_indices[3] );
      
      Vec3ui sorted_tri = sort_triangle( tri );            
      
      double time, s1, s2, s3, rel_disp;
      Vec3d normal;

      if ( point_triangle_collision( m_positions[vertex_index], m_newpositions[vertex_index], vertex_index,
                                     m_positions[sorted_tri[0]], m_newpositions[sorted_tri[0]], sorted_tri[0],
                                     m_positions[sorted_tri[1]], m_newpositions[sorted_tri[1]], sorted_tri[1],
                                     m_positions[sorted_tri[2]], m_newpositions[sorted_tri[2]], sorted_tri[2],
                                     s1, s2, s3,
                                     normal,
                                     time, rel_disp ) )               
         
      {
         return false; 
      }                  
   }
   
   return true;
   
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------


bool DynamicSurface::new_rigid_impact_zones(double dt)
{
   
   // copy
   std::vector<Vec3d> old_velocities = m_velocities;
   
   std::vector<ImpactZone> impact_zones;
   
   bool finished_detecting_collisions = false;
   
   std::vector<Collision> total_collisions;
   finished_detecting_collisions = detect_collisions(total_collisions);
      
   while ( false == total_collisions.empty() )
   {      
      // insert each new collision constraint into its own impact zone
      std::vector<ImpactZone> new_impact_zones;
      for ( unsigned int i = 0; i < total_collisions.size(); ++i )
      {
         ImpactZone new_zone;
         new_zone.collisions.push_back( total_collisions[i] );
         new_impact_zones.push_back( new_zone );
      }
      
      assert( new_impact_zones.size() == total_collisions.size() );
      
      // merge all impact zones that share vertices
      merge_impact_zones( new_impact_zones, impact_zones );
      
      for ( int i = 0; i < (int) impact_zones.size(); ++i )
      {
         if ( impact_zones[i].all_solved ) 
         {
            impact_zones[i].all_solved = false;
            impact_zones.erase( impact_zones.begin() + i );
            --i;
         }
      }
      
      for ( int i = 0; i < (int) impact_zones.size(); ++i )
      {
         assert( false == impact_zones[i].all_solved );
      }            
      
      // for each impact zone
      for ( unsigned int i = 0; i < impact_zones.size(); ++i )
      {
         
         std::vector<unsigned int> zone_vertices;
         impact_zones[i].get_all_vertices( zone_vertices );
         calculate_rigid_motion(dt, zone_vertices);
         
         bool all_solved = true;
         for ( unsigned int c = 0; c < impact_zones[i].collisions.size(); ++c )
         {
            all_solved &= collision_solved( impact_zones[i].collisions[c] );
         }
         
         if ( !all_solved )
         {
            std::cout << "RIZ failed.  Getting desperate!" << std::endl;
            
            Vec3d average_velocity(0,0,0);
            for ( unsigned int v = 0; v < zone_vertices.size(); ++v )
            {
               average_velocity += m_velocities[ zone_vertices[v] ];
            }
            average_velocity /= (double) zone_vertices.size();
            
            for ( unsigned int v = 0; v < zone_vertices.size(); ++v )
            {
               m_velocities[ zone_vertices[v] ] = average_velocity;
               m_newpositions[ zone_vertices[v] ] = m_positions[ zone_vertices[v] ] + dt * m_velocities[ zone_vertices[v] ];
            }
         }
         
      }  
      
      total_collisions.clear();
      
      if ( !finished_detecting_collisions )
      {
         finished_detecting_collisions = detect_collisions( total_collisions );
         impact_zones.clear();
      }
      else
      {
         detect_new_collisions( impact_zones, total_collisions );
      }
      
   }
   
   return true;
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

void DynamicSurface::calculate_rigid_motion(double dt, std::vector<unsigned int>& vs)
{
   Vec3d xcm(0,0,0);
   Vec3d vcm(0,0,0);
   double mass = 0;
   
   for(unsigned int i = 0; i < vs.size(); i++)
   {
      unsigned int idx = vs[i];
      double m = m_masses[idx];
      
      mass += m;
      
      m_velocities[idx] = ( m_newpositions[idx] - m_positions[idx] ) / dt;
      
      xcm += m * m_positions[idx];
      vcm += m * m_velocities[idx];
   }
   
   xcm /= mass;
   vcm /= mass;
   
   Vec3d L(0,0,0);
   
   for(unsigned int i = 0; i < vs.size(); i++)
   {
      unsigned int idx = vs[i];
      double m = m_masses[idx];
      
      Vec3d xdiff = m_positions[idx] - xcm;
      Vec3d vdiff = m_velocities[idx] - vcm;
      
      L += m * cross(xdiff, vdiff);
   }
   
   Mat33d I(0,0,0,0,0,0,0,0,0);
   
   for(unsigned int i = 0; i < vs.size(); i++)
   {
      unsigned int idx = vs[i];
      double m = m_masses[idx];
      
      Vec3d xdiff = m_positions[idx] - xcm;
      Mat33d tens = outer(-xdiff, xdiff);
      
      double d = mag2(xdiff);
      tens(0,0) += d;
      tens(1,1) += d;
      tens(2,2) += d;
      
      I += m * tens;
   }
   
//   std::cout << "determinant " << determinant(I);
//   std::cout << "I " << std::endl << I << std::endl;
//   std::cout << "I^-1 " << std::endl << inverse(I) << std::endl;
   
   Vec3d w = inverse(I) * L;
   double wmag = mag(w);
   Vec3d wnorm = w/wmag;
   
   double cosdtw = cos(dt * wmag);
   Vec3d sindtww = sin(dt * wmag) * wnorm;
   
   Vec3d xrigid = xcm + dt * vcm;
   
   for(unsigned int i = 0; i < vs.size(); i++)
   {
      unsigned int idx = vs[i];
      
      Vec3d xdiff = m_positions[idx] - xcm;
      Vec3d xf = dot(xdiff, wnorm) * wnorm;
      Vec3d xr = xdiff - xf;
      
      m_newpositions[idx] = xrigid + xf + cosdtw * xr + cross(sindtww, xr);
      
      m_velocities[idx] = ( m_newpositions[idx] - m_positions[idx] ) / dt;
   }
   
//   std::cout << "\n\ninter-vertex distances after rigid motion: " << std::endl;
//   for(unsigned int i = 0; i < vs.size(); i++)
//   {
//      for(unsigned int j = 0; j < vs.size(); j++)
//      {
//         std::cout << dist( m_newpositions[vs[i]], m_newpositions[vs[j]] ) << std::endl;
//      }
//   }
   
   // std::cout << "calculated rigid motion" << std::endl;
   // for(unsigned int i = 0; i < vs.size(); i++)
   // for(unsigned int j = 0; j < vs.size(); j++)
   // std::cout << (dist(positions[vs[i]], positions[vs[j]]) - dist(newpositions[vs[i]], newpositions[vs[j]])) << std::endl;
   
}


// ---------------------------------------------------------
///
/// 
///
// ---------------------------------------------------------

std::vector<unsigned int> DynamicSurface::merge_impact_zones( std::vector<unsigned int>& zones, 
                                                              unsigned int z0, 
                                                              unsigned int z1, 
                                                              unsigned int z2, 
                                                              unsigned int z3 )
{
   
   std::vector<unsigned int> vs;
   for(unsigned int i = 0; i < m_positions.size(); i++)
   {
      unsigned int& z = zones[i];
      if(z == z0)
      {
         vs.push_back(i);
      }
      else if(z == z1)
      {
         vs.push_back(i);
         z = z0;
      }
      else if(z == z2)
      {
         vs.push_back(i);
         z = z0;
      }
      else if(z == z3)
      {
         vs.push_back(i);
         z = z0;
      }
   }
      
   return vs;
}


// ---------------------------------------------------------
///
/// Advance mesh by one time step 
///
// ---------------------------------------------------------

void DynamicSurface::integrate( double dt )
{     
      
   std::cout << "---------------------- El Topo: integration and collision handling --------------------" << std::endl;
   
   assert( m_positions.size() == m_velocities.size() );
  
   double curr_dt = dt;
   double t = 0;
      
   while ( t < dt )
   {
      
      // Handle proximities

//      for(unsigned int i = 0; i < m_positions.size(); i++)
//      {
//         m_velocities[i] = ( m_newpositions[i] - m_positions[i] ) / curr_dt;
//      }
      
      m_num_collisions_this_step = 0;
      
      if ( m_collision_safety )
      {
         rebuild_static_broad_phase();
         handle_edge_edge_proximities( curr_dt );
         handle_triangle_point_proximities( curr_dt );
      }

      
      for(unsigned int i = 0; i < m_positions.size(); i++)
      {
         m_newpositions[i] = m_positions[i] + curr_dt * m_velocities[i];  
      }
      
      
      if ( m_collision_safety )
      {        
         // Handle continuous collisions
         rebuild_continuous_broad_phase();

         bool all_collisions_handled = false;

         handle_point_vs_solid_triangle_collisions( curr_dt );
         all_collisions_handled = handle_collisions( curr_dt );
         
         // failsafe impact zones 
         
         bool solver_ok = true;
         
         if ( !all_collisions_handled )
         {
            //solver_ok = handle_collisions_simultaneous( curr_dt );            
         }

         if ( !solver_ok )
         {
            // punt to rigid impact zones
           // new_rigid_impact_zones( curr_dt );
         }  
         
         //assert_predicted_mesh_is_intersection_free();
         
      }

      m_total_num_collisions += m_num_collisions_this_step;
      
      // Set m_positions
      for(unsigned int i = 0; i < m_positions.size(); i++)
      {
         m_positions[i] = m_newpositions[i];
      } 
      
      t += curr_dt;
   }
   

}

// ---------------------------------------------------------
///
/// Construct static acceleration structure
///
// ---------------------------------------------------------

void DynamicSurface::rebuild_static_broad_phase()
{
   m_broad_phase->update_broad_phase_static( *this );
}

// ---------------------------------------------------------
///
/// Construct continuous acceleration structure
///
// ---------------------------------------------------------

void DynamicSurface::rebuild_continuous_broad_phase()
{
   m_broad_phase->update_broad_phase_continuous( *this );
}


// ---------------------------------------------------------
///
/// Update the broadphase elements incident to the given vertex
///
// ---------------------------------------------------------

void DynamicSurface::update_static_broad_phase( unsigned int vertex_index )
{
   const std::vector<unsigned int>& incident_tris = m_mesh.m_vtxtri[ vertex_index ];
   const std::vector<unsigned int>& incident_edges = m_mesh.m_vtxedge[ vertex_index ];
   
   Vec3d low, high;
   vertex_static_bounds( vertex_index, low, high );
   m_broad_phase->update_vertex( vertex_index, low, high );
   
   for ( unsigned int t = 0; t < incident_tris.size(); ++t )
   {
      triangle_static_bounds( incident_tris[t], low, high );
      m_broad_phase->update_triangle( incident_tris[t], low, high );
   }
   
   for ( unsigned int e = 0; e < incident_edges.size(); ++e )
   {
      edge_static_bounds( incident_edges[e], low, high );
      m_broad_phase->update_edge( incident_edges[e], low, high );
   }

}


// ---------------------------------------------------------
///
/// Update the broadphase elements incident to the given vertex, using current and predicted vertex positions
///
// ---------------------------------------------------------

void DynamicSurface::update_continuous_broad_phase( unsigned int vertex_index )
{
   const std::vector<unsigned int>& incident_tris = m_mesh.m_vtxtri[ vertex_index ];
   const std::vector<unsigned int>& incident_edges = m_mesh.m_vtxedge[ vertex_index ];

   Vec3d low, high;
   vertex_continuous_bounds( vertex_index, low, high );
   m_broad_phase->update_vertex( vertex_index, low, high );
   
   for ( unsigned int t = 0; t < incident_tris.size(); ++t )
   {
      triangle_continuous_bounds( incident_tris[t], low, high );
      m_broad_phase->update_triangle( incident_tris[t], low, high );
   }
   
   for ( unsigned int e = 0; e < incident_edges.size(); ++e )
   {
      edge_continuous_bounds( incident_edges[e], low, high );
      m_broad_phase->update_edge( incident_edges[e], low, high );
   }
}


// ---------------------------------------------------------
///
/// Compute the (padded) AABB of a vertex
///
// ---------------------------------------------------------

void DynamicSurface::vertex_static_bounds(unsigned int v, Vec3d &xmin, Vec3d &xmax) const
{
   if ( m_mesh.m_vtxtri[v].empty() )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {
      xmin = m_positions[v] - Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = m_positions[v] + Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
}

// ---------------------------------------------------------
///
/// Compute the AABB of an edge
///
// ---------------------------------------------------------

void DynamicSurface::edge_static_bounds(unsigned int e, Vec3d &xmin, Vec3d &xmax) const
{
   const Vec2ui& edge = m_mesh.m_edges[e];
   if ( edge[0] == edge[1] )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {            
      minmax(m_positions[edge[0]], m_positions[edge[1]], xmin, xmax);
      xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
}

// ---------------------------------------------------------
///
/// Compute the AABB of a triangle
///
// ---------------------------------------------------------

void DynamicSurface::triangle_static_bounds(unsigned int t, Vec3d &xmin, Vec3d &xmax) const
{
   const Vec3ui& tri = m_mesh.m_tris[t];  
   if ( tri[0] == tri[1] )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {      
      minmax(m_positions[tri[0]], m_positions[tri[1]], m_positions[tri[2]], xmin, xmax);
      xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
}

// ---------------------------------------------------------
///
/// Compute the AABB of a continuous vertex
///
// ---------------------------------------------------------

void DynamicSurface::vertex_continuous_bounds(unsigned int v, Vec3d &xmin, Vec3d &xmax) const
{
   if ( m_mesh.m_vtxtri[v].empty() )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {
      minmax(m_positions[v], m_newpositions[v], xmin, xmax);
      xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
}

// ---------------------------------------------------------
///
/// Compute the AABB of a continuous edge
///
// ---------------------------------------------------------

void DynamicSurface::edge_continuous_bounds(unsigned int e, Vec3d &xmin, Vec3d &xmax) const
{
   const Vec2ui& edge = m_mesh.m_edges[e];   
   if ( edge[0] == edge[1] )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {      
      minmax(m_positions[edge[0]], m_newpositions[edge[0]], m_positions[edge[1]], m_newpositions[edge[1]], xmin, xmax);
      xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);   
   }
}

// ---------------------------------------------------------
///
/// Compute the AABB of a continuous triangle
///
// ---------------------------------------------------------

void DynamicSurface::triangle_continuous_bounds(unsigned int t, Vec3d &xmin, Vec3d &xmax) const
{
   const Vec3ui& tri = m_mesh.m_tris[t];
   if ( tri[0] == tri[1] )
   {
      xmin = Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax = -Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   }
   else
   {
      minmax(m_positions[tri[0]], m_newpositions[tri[0]], m_positions[tri[1]], m_newpositions[tri[1]], m_positions[tri[2]], m_newpositions[tri[2]], xmin, xmax);
      xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
      xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);   
   }
}


// --------------------------------------------------------
///
/// Check a triangle (by index) vs all other triangles for any kind of intersection
///
// --------------------------------------------------------

bool DynamicSurface::check_triangle_vs_all_triangles_for_intersection( unsigned int tri_index  )
{
   return check_triangle_vs_all_triangles_for_intersection( m_mesh.m_tris[tri_index] );
}

// --------------------------------------------------------
///
/// Check a triangle vs all other triangles for any kind of intersection
///
// --------------------------------------------------------

bool DynamicSurface::check_triangle_vs_all_triangles_for_intersection( const Vec3ui& tri )
{
   bool any_intersection = false;
   
   std::vector<unsigned int> overlapping_triangles;
   Vec3d low, high;
   
   minmax( m_positions[tri[0]], m_positions[tri[1]], low, high );
   low -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   high += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   
   m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
   
   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      
      bool result = check_edge_triangle_intersection_by_index( tri[0], tri[1],
                                                              m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][2],
                                                              m_positions,
                                                              false );
      
      if ( result )
      {
         check_edge_triangle_intersection_by_index( tri[0], tri[1],
                                                   m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][2],
                                                   m_positions,
                                                   true );
         
         any_intersection = true;
      }
   }
   
   minmax( m_positions[tri[1]], m_positions[tri[2]], low, high );
   low -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   high += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   
   overlapping_triangles.clear();
   m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
   
   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      
      bool result = check_edge_triangle_intersection_by_index( tri[1], tri[2],
                                                              m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][2],
                                                              m_positions,
                                                              false );
      
      if ( result )
      {
         check_edge_triangle_intersection_by_index( tri[1], tri[2],
                                                   m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][2],
                                                   m_positions,
                                                   true );
         
         any_intersection = true;
      }
   }
   
   minmax( m_positions[tri[2]], m_positions[tri[0]], low, high );
   low -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   high += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   
   overlapping_triangles.clear();
   m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
   
   for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
   {
      
      bool result = check_edge_triangle_intersection_by_index( tri[2], tri[0],
                                                              m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                              m_mesh.m_tris[overlapping_triangles[i]][2],
                                                              m_positions,
                                                              false );
      
      if ( result )
      {
         check_edge_triangle_intersection_by_index( tri[2], tri[0],
                                                   m_mesh.m_tris[overlapping_triangles[i]][0], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][1], 
                                                   m_mesh.m_tris[overlapping_triangles[i]][2],
                                                   m_positions,
                                                   true );
         
         any_intersection = true;         
      }
   }
   
   //
   // edges
   //
   
   minmax( m_positions[tri[0]], m_positions[tri[1]], m_positions[tri[2]], low, high );
   low -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   high += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
   
   std::vector<unsigned int> overlapping_edges;
   m_broad_phase->get_potential_edge_collisions( low, high, overlapping_edges );
   
   for ( unsigned int i = 0; i < overlapping_edges.size(); ++i )
   {
      
      bool result = check_edge_triangle_intersection_by_index( m_mesh.m_edges[overlapping_edges[i]][0], m_mesh.m_edges[overlapping_edges[i]][1], 
                                                              tri[0], tri[1], tri[2],
                                                              m_positions,
                                                              false );
      
      if ( result )
      {
         check_edge_triangle_intersection_by_index( m_mesh.m_edges[overlapping_edges[i]][0], m_mesh.m_edges[overlapping_edges[i]][1], 
                                                   tri[0], tri[1], tri[2],
                                                   m_positions,
                                                   true );
         
         any_intersection = true;         
      }
   }
   
   return any_intersection;
}


// ---------------------------------------------------------
///
/// Fire an assert if any edge is intersecting any triangles
///
// ---------------------------------------------------------

void DynamicSurface::assert_mesh_is_intersection_free( bool degeneracy_counts_as_intersection )
{
       
   //g_intersecting_triangles.clear();
   
   m_broad_phase->update_broad_phase_static( *this );
      
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {
      std::vector<unsigned int> edge_candidates;
      
      Vec3d low, high;
      triangle_static_bounds( i, low, high );       
      m_broad_phase->get_potential_edge_collisions( low, high, edge_candidates );
         
      const Vec3ui& triangle_a = m_mesh.m_tris[i];
      
      if ( triangle_a[0] == triangle_a[1] || triangle_a[1] == triangle_a[2] || triangle_a[2] == triangle_a[0] )    { continue; }
      
      assert( m_mesh.get_edge( triangle_a[0], triangle_a[1] ) != m_mesh.m_edges.size() );
      assert( m_mesh.get_edge( triangle_a[1], triangle_a[2] ) != m_mesh.m_edges.size() );
      assert( m_mesh.get_edge( triangle_a[2], triangle_a[0] ) != m_mesh.m_edges.size() );
      
      for ( unsigned int j = 0; j < edge_candidates.size(); ++j )
      {
         
         const Vec2ui& edge_b = m_mesh.m_edges[ edge_candidates[j] ];
         
         if ( edge_b[0] == edge_b[1] )    { continue; }
         
         if (    edge_b[0] == triangle_a[0] || edge_b[0] == triangle_a[1] || edge_b[0] == triangle_a[2] 
              || edge_b[1] == triangle_a[0] || edge_b[1] == triangle_a[1] || edge_b[1] == triangle_a[2] )
         {
            continue;
         }
         
         if ( segment_triangle_intersection( m_positions[edge_b[0]], edge_b[0], m_positions[edge_b[1]], edge_b[1],
                                             m_positions[triangle_a[0]], triangle_a[0], 
                                             m_positions[triangle_a[1]], triangle_a[1],
                                             m_positions[triangle_a[2]], triangle_a[2],
                                             degeneracy_counts_as_intersection, m_verbose ) )
         {   
            
            if ( m_collision_safety )
            {
               std::cout << "Intersection!  Triangle " << triangle_a << " vs edge " << edge_b << std::endl;
               
               segment_triangle_intersection( m_positions[edge_b[0]], edge_b[0], m_positions[edge_b[1]], edge_b[1],
                                              m_positions[triangle_a[0]], triangle_a[0],
                                              m_positions[triangle_a[1]], triangle_a[1], 
                                              m_positions[triangle_a[2]], triangle_a[2],
                                              true, true );
               
               assert(0);
            }
            
         }
      }
   }

}


// ---------------------------------------------------------
///
/// Using m_newpositions as the geometry, fire an assert if any edge is intersecting any triangles
///
// ---------------------------------------------------------

void DynamicSurface::assert_predicted_mesh_is_intersection_free( )
{
       
   rebuild_continuous_broad_phase();
   
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {
      std::vector<unsigned int> edge_candidates;
      
      Vec3d low, high;
      triangle_continuous_bounds( i, low, high );       
      m_broad_phase->get_potential_edge_collisions( low, high, edge_candidates );
      
      const Vec3ui& triangle_a = m_mesh.m_tris[i];
      
      if ( triangle_a[0] == triangle_a[1] || triangle_a[1] == triangle_a[2] || triangle_a[2] == triangle_a[0] )    { continue; }
      
      for ( unsigned int j = 0; j < edge_candidates.size(); ++j )
      {
         
         const Vec2ui& edge_b = m_mesh.m_edges[ edge_candidates[j] ];
         
         if ( edge_b[0] == edge_b[1] )    { continue; }
         
         if ( check_edge_triangle_intersection_by_index( edge_b[0], edge_b[1], 
                                                         triangle_a[0], triangle_a[1], triangle_a[2], 
                                                         m_newpositions, m_verbose )  )
         {
            if ( m_collision_safety )
            {
               std::cout << "Intersection!  Triangle " << triangle_a << " vs edge " << edge_b << std::endl;
            }
                        
            m_verbose = true;
                        
            std::vector<Collision> check_collisions;
            detect_collisions( check_collisions );
            std::cout << "number of collisions detected: " << check_collisions.size() << std::endl;
            
            std::cout << "-----\n edge-triangle check using m_positions:" << std::endl;
            
            bool result = check_edge_triangle_intersection_by_index( edge_b[0], edge_b[1], 
                                                       triangle_a[0], triangle_a[1], triangle_a[2], 
                                                       m_positions, m_verbose );
            
            std::cout << "result: " << result << std::endl;
            
            std::cout << "-----\n edge-triangle check using new m_positions" << std::endl;
            
            result = check_edge_triangle_intersection_by_index( edge_b[0], edge_b[1], 
                                                       triangle_a[0], triangle_a[1], triangle_a[2], 
                                                       m_newpositions, m_verbose );
            
            std::cout << "result: " << result << std::endl;
            
            Vec3ui sorted_triangle = sort_triangle( triangle_a );
            
            std::cout << "sorted_triangle: " << sorted_triangle << std::endl;
            
            const Vec3d& ea = m_positions[edge_b[0]];
            const Vec3d& eb = m_positions[edge_b[1]];
            const Vec3d& ta = m_positions[sorted_triangle[0]];
            const Vec3d& tb = m_positions[sorted_triangle[1]];
            const Vec3d& tc = m_positions[sorted_triangle[2]];
            
            const Vec3d& ea_new = m_newpositions[edge_b[0]];
            const Vec3d& eb_new = m_newpositions[edge_b[1]];
            const Vec3d& ta_new = m_newpositions[sorted_triangle[0]];
            const Vec3d& tb_new = m_newpositions[sorted_triangle[1]];
            const Vec3d& tc_new = m_newpositions[sorted_triangle[2]];
            
            std::cout.precision(20);
            
            std::cout << "old: (edge0 edge1 tri0 tri1 tri2 )" << std::endl;
            
            std::cout << ea << std::endl;
            std::cout << eb << std::endl;
            std::cout << ta << std::endl;
            std::cout << tb << std::endl;
            std::cout << tc << std::endl;
            
            std::cout << "new: " << std::endl;
            
            std::cout << ea_new << std::endl;
            std::cout << eb_new << std::endl;
            std::cout << ta_new << std::endl;
            std::cout << tb_new << std::endl;
            std::cout << tc_new << std::endl;
            
            std::vector<double> possible_times;

            Vec3d normal;
            
            std::cout << "-----" << std::endl;
            
            if( segment_segment_collision( ea, ea_new, edge_b[0], eb, eb_new, edge_b[1], ta, ta_new, sorted_triangle[0], tb, tb_new, sorted_triangle[1] ) )
            {
               
               bool check_flipped = segment_segment_collision( ta, ta_new, sorted_triangle[0], tb, tb_new, sorted_triangle[1], ea, ea_new, edge_b[0], eb, eb_new, edge_b[1] );
               
               assert( check_flipped );
               
               
               double time, s0, s2, rel_disp;
               Vec3d normal;
               
               assert ( segment_segment_collision( ea, ea_new, edge_b[0], 
                                                   eb, eb_new, edge_b[1], 
                                                   ta, ta_new, sorted_triangle[0], 
                                                   tb, tb_new, sorted_triangle[1],
                                                   s0, s2,
                                                   normal,
                                                   time, rel_disp ) );
                  
               
               Vec3d xmin, xmax;
               minmax( ea, ea_new, eb, eb_new, xmin, xmax);
               xmin -= Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);
               xmax += Vec3d(m_proximity_epsilon, m_proximity_epsilon, m_proximity_epsilon);   
               std::vector<unsigned int> potential_collisions;
               m_broad_phase->get_potential_edge_collisions( xmin, xmax, potential_collisions );
             
               for ( unsigned int c = 0; c < potential_collisions.size(); ++c )
               {
                  const Vec2ui& other_edge = m_mesh.m_edges[ potential_collisions[c] ];
                  
                  if ( ( other_edge[0] == sorted_triangle[0] && other_edge[1] == sorted_triangle[1] ) ||
                       ( other_edge[1] == sorted_triangle[0] && other_edge[0] == sorted_triangle[1] ) )
                  {
                     std::cout << "Broadphase hit" << std::endl;
                  }
               }
               
               assert(0);
               
            }
            
            std::cout << "-----" << std::endl;
            
            assert( !segment_segment_collision( ea, ea_new, edge_b[0], eb, eb_new, edge_b[1], tb, tb_new, sorted_triangle[1], tc, tc_new, sorted_triangle[2] ) );
                        
            std::cout << "-----" << std::endl;

            assert( !segment_segment_collision( ea, ea_new, edge_b[0], eb, eb_new, edge_b[1], tc, tc_new, sorted_triangle[2], ta, ta_new, sorted_triangle[0] ) );
            
            std::cout << "-----" << std::endl;
            
            assert( !point_triangle_collision( ea, ea_new, edge_b[0], ta, ta_new, sorted_triangle[0], tb, tb_new, sorted_triangle[1], tc, tc_new, sorted_triangle[2] ) );
            
            std::cout << "-----" << std::endl;

            assert( !point_triangle_collision( eb, eb_new, edge_b[1], ta, ta_new, sorted_triangle[0], tb, tb_new, sorted_triangle[1], tc, tc_new, sorted_triangle[2] ) );
                                   
            m_verbose = false;
            
            if ( m_collision_safety )
            {
               std::cout << "no collisions detected" << std::endl;
               //assert(0);
            }
         }
      }
   }
   
}





