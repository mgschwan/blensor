
// ---------------------------------------------------------
//
//  surftrack.cpp
//  Tyson Brochu 2008
//  
//  Implementation of the SurfTrack class: a dynamic mesh with 
//  topological changes and mesh maintenance operations.
//
// ---------------------------------------------------------


// ---------------------------------------------------------
// Includes
// ---------------------------------------------------------

#include <surftrack.h>

#include <vector>
#include <queue>

#ifdef __APPLE__
#include <OpenGL/gl.h>
#include <GLUT/glut.h>
#include <vecLib/clapack.h>
#else
#ifdef WIN32
#include <windows.h>
#endif
#include <GL/gl.h>
#include <GL/glut.h>
#endif

#include <ccd_wrapper.h>
#include <cassert>
#include <vec.h>
#include <array3.h>
#include <nondestructivetrimesh.h>
#include <lapack_wrapper.h>

#include <broadphase.h>
#include <subdivisionscheme.h>

#include <gluvi.h>
#include <wallclocktime.h>

#include <cstdio>
#include <cstdlib>

// ---------------------------------------------------------
//  Global externs
// ---------------------------------------------------------

// ---------------------------------------------------------
// Local constants, typedefs, macros
// ---------------------------------------------------------

// ---------------------------------------------------------
// Static function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Convert hue/sat/val to RGB.  Used to visualize data on the vertices.
///
// ---------------------------------------------------------
/*
static Vec3d hueToRGB(double hue, double sat, double val) 
{
   //compute hue (adapted from Wikipedia)
   int Hi = (int)(floor(hue / 60.0f)) % 6;
   double f = hue / 60 - Hi;
   double p = val * (1 - sat);
   double q = val * (1- f * sat);
   double t = val * (1 - (1 - f) * sat);
   Vec3d result; // r,g,b each in (0,1)
   switch(Hi) {
      case 0:
         result = Vec3d(val, t, p);
         break;
      case 1:
         result = Vec3d(q, val, p);
         break;
      case 2:
         result = Vec3d(p, val, t);
         break;
      case 3:
         result = Vec3d(p, q, val);
         break;
      case 4:
         result = Vec3d(t, p, val);
         break;
      case 5:
         result = Vec3d(val, p, q);
         break;
   }
   
   return result;
}
*/

// ---------------------------------------------------------
//  Member function definitions
// ---------------------------------------------------------

// ---------------------------------------------------------
///
/// Default initialization parameters
///
// ---------------------------------------------------------

SurfTrackInitializationParameters::SurfTrackInitializationParameters() :
   m_proximity_epsilon( 1e-4 ),
   m_min_triangle_area( 1e-7 ),
   m_improve_collision_epsilon( 2e-6 ),
   m_use_fraction( false ),
   m_min_edge_length( UNINITIALIZED_DOUBLE ),     // <- Don't allow instantiation without setting these parameters
   m_max_edge_length( UNINITIALIZED_DOUBLE ),     // <-
   m_max_volume_change( UNINITIALIZED_DOUBLE ),   // <-
   m_edge_flip_min_length_change( 1e-8 ),
   m_merge_proximity_epsilon( 1e-5 ),
   m_subdivision_scheme(NULL),
   m_collision_safety(true),
   m_allow_topology_changes(true),
   m_perform_improvement(true)
{}


// ---------------------------------------------------------
///
/// Create a SurfTrack object from a set of vertices and triangles using the specified paramaters
///
// ---------------------------------------------------------

SurfTrack::SurfTrack( const std::vector<Vec3d>& vs, 
                      const std::vector<Vec3ui>& ts, 
                      const std::vector<double>& masses,
                      const SurfTrackInitializationParameters& initial_parameters ) :

   DynamicSurface( vs, 
                   ts,
                   masses,
                   initial_parameters.m_proximity_epsilon, 
                   initial_parameters.m_collision_safety ),

   m_improve_collision_epsilon( initial_parameters.m_improve_collision_epsilon ),
   m_edge_flip_min_length_change( initial_parameters.m_edge_flip_min_length_change ),
   m_max_volume_change( UNINITIALIZED_DOUBLE ),   
   m_min_edge_length( UNINITIALIZED_DOUBLE ),
   m_max_edge_length( UNINITIALIZED_DOUBLE ),
   m_merge_proximity_epsilon( initial_parameters.m_merge_proximity_epsilon ),   
   m_min_triangle_area( initial_parameters.m_min_triangle_area ),
   m_subdivision_scheme( initial_parameters.m_subdivision_scheme ),
   m_dirty_triangles(0),   
   m_allow_topology_changes( initial_parameters.m_allow_topology_changes ),
   m_perform_improvement( initial_parameters.m_perform_improvement )
{
      
   std::cout << "m_allow_topology_changes: " << m_allow_topology_changes << std::endl;
   std::cout << "m_perform_improvement: " << m_perform_improvement << std::endl;
   
   m_mesh.update_connectivity( m_positions.size() );
   m_verbose = true;
   trim_non_manifold( );
   m_verbose = false;
   m_mesh.update_connectivity( m_positions.size() );
   
   assert( initial_parameters.m_min_edge_length != UNINITIALIZED_DOUBLE );
   assert( initial_parameters.m_max_edge_length != UNINITIALIZED_DOUBLE );
   assert( initial_parameters.m_max_volume_change != UNINITIALIZED_DOUBLE );
   
   
   double avg_length = DynamicSurface::get_average_non_solid_edge_length();   
   std::cout << " %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% average edge length: " << avg_length << std::endl;
   
   if ( initial_parameters.m_use_fraction )
   {      
      m_min_edge_length = initial_parameters.m_min_edge_length * avg_length;
      m_max_edge_length = initial_parameters.m_max_edge_length * avg_length;
      m_max_volume_change = initial_parameters.m_max_volume_change * avg_length * avg_length * avg_length;        
   }
   else
   {
      m_min_edge_length = initial_parameters.m_min_edge_length;
      m_max_edge_length = initial_parameters.m_max_edge_length;
      m_max_volume_change = initial_parameters.m_max_volume_change;  
   }
   
   if ( m_subdivision_scheme == NULL )
   {
      m_subdivision_scheme = new MidpointScheme();
      should_delete_subdivision_scheme_object = true;
   }
   else
   {
      should_delete_subdivision_scheme_object = false;
   }
      
   rebuild_static_broad_phase();
   
}


SurfTrack::~SurfTrack()
{
   if ( should_delete_subdivision_scheme_object )
   {
      delete m_subdivision_scheme;
   }
}

// ---------------------------------------------------------
///
/// Display the surface in OpenGL using the specified options
///
// ---------------------------------------------------------

#ifdef USE_GUI

void SurfTrack::render( unsigned int options )
{
   //
   // edges
   //
   
   glDisable(GL_LIGHTING);
   glDepthFunc(GL_LEQUAL);
   
   if ( options & RENDER_EDGES )
   {
      glLineWidth(2);
      glBegin(GL_LINES);
      
      for(unsigned int e = 0; e < m_mesh.m_edges.size(); e++)
      {
         if ( m_mesh.m_edgetri[e].size() < 2 )
         {
            glColor3d(1,0,0);
         }
         else
         {
            glColor3d(0,0,0);
         }
         
         Vec2ui& edge = m_mesh.m_edges[e];
         Vec3d& vtx0 = m_positions[edge[0]];
         Vec3d& vtx1 = m_positions[edge[1]];
         glVertex3d(vtx0[0], vtx0[1], vtx0[2]);
         glVertex3d(vtx1[0], vtx1[1], vtx1[2]);
      }
      
      glEnd(); 
   }
   
   //
   // vertices
   //

   if (options & RENDER_VERTEX_DATA)
   {
      glPointSize(5);
      glBegin(GL_POINTS);
      
      for ( unsigned int v = 0; v < m_positions.size(); ++v )
      {
         if ( m_mesh.m_vtxtri[v].empty() )
         {
            continue;
         }
         
         if ( m_masses[v] > 100.0 )
         {
            glColor3f( 1.0f, 0.0f, 0.0f );
         }
         else
         {
            glColor3f( 0.0f, 1.0f, 0.0f );
         }
                  
         glVertex3dv( m_positions[v].v );      
         
      }
      glEnd();
   }   
   
   //
   // triangles
   //
   
   if ( options & RENDER_TRIANGLES )
   {
      if ( options & TWO_SIDED )
      {
         glLightModeli( GL_LIGHT_MODEL_TWO_SIDE, 1 );
      }
      else
      {
         glEnable(GL_CULL_FACE);
      }
      
      glEnable(GL_LIGHTING);
      glShadeModel(GL_SMOOTH);
      //Gluvi::set_generic_lights();
      //Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_FRONT);   // exterior surface colour
      //Gluvi::set_generic_material(1.0f, 1.0f, 1.0f, GL_BACK);
      
      if ( options & NO_SHADING )
      {
         glDisable(GL_LIGHTING);
         glColor3d(1,1,1);
      }
           
      if ( options & RENDER_EDGES )
      {
         glEnable(GL_POLYGON_OFFSET_FILL);
         glPolygonOffset(1.0f, 1.0f);      //  allow the wireframe to show through
      }
      
      glEnable(GL_DEPTH_TEST);
      glDepthMask(GL_TRUE);
            
      glBegin(GL_TRIANGLES);
      
      for(unsigned int i = 0; i < m_mesh.m_tris.size(); i++)
      {
         const Vec3ui& tri = m_mesh.m_tris[i];
         
         const Vec3d& v0 = m_positions[tri[0]];
         const Vec3d& v1 = m_positions[tri[1]];
         const Vec3d& v2 = m_positions[tri[2]];
         
         glNormal3dv( get_vertex_normal(tri[0]).v );
         glVertex3d(v0[0], v0[1], v0[2]);

         glNormal3dv( get_vertex_normal(tri[1]).v );
         glVertex3d(v1[0], v1[1], v1[2]);
         
         glNormal3dv( get_vertex_normal(tri[2]).v );
         glVertex3d(v2[0], v2[1], v2[2]);
         
      }
      
      glEnd();

      
      if ( options & RENDER_EDGES )
      {
         glDisable(GL_POLYGON_OFFSET_FILL);
      }
      
      glDisable(GL_LIGHTING);
      
   }

}

#endif

// ---------------------------------------------------------
///
/// Ray cast into the scene, return index of the closest primitive of the type specified
///
// ---------------------------------------------------------

unsigned int SurfTrack::ray_cast( const Vec3f& ray_origin, 
                                  const Vec3f& ray_direction, 
                                  unsigned int primitive_type, 
                                  unsigned int& hit_index )
{

   const double RAY_CAST_HIT_DISTANCE = 2e-2;

   Vec3d rorigin( ray_origin[0], ray_origin[1], ray_origin[2] );
   Vec3d rhead = rorigin + 100.0 * Vec3d( ray_direction[0], ray_direction[1], ray_direction[2] );
   
   unsigned int ray_origin_dummy_index = m_positions.size();
   unsigned int ray_head_dummy_index = m_positions.size() + 1;
   
   Vec3d aabb_low, aabb_high;
   minmax( rorigin, rhead, aabb_low, aabb_high );

   if ( primitive_type == 0)
   {
      // -----------------------------------------------------------------
      // Vertices
      // -----------------------------------------------------------------

      std::cout << "looking for vertices..." << std::endl;
      
      double vertex_min_parameter = 1e30;
      unsigned int vertex_min_index = ~0;
      
      std::vector<unsigned int> overlapping_vertices;
      m_broad_phase->get_potential_vertex_collisions( aabb_low, aabb_high, overlapping_vertices );
      
      std::cout << "potential vertices: " << overlapping_vertices.size() << std::endl;
      
      for ( unsigned int i = 0; i < overlapping_vertices.size(); ++i )
      {
         const Vec3d& v = m_positions[ overlapping_vertices[i] ];
         
         // initialized to silence compiler warnings
         double distance = UNINITIALIZED_DOUBLE;       
         double ray_parameter = UNINITIALIZED_DOUBLE;
         Vec3d normal(UNINITIALIZED_DOUBLE, UNINITIALIZED_DOUBLE, UNINITIALIZED_DOUBLE);
         double normal_multiplier = UNINITIALIZED_DOUBLE;
         
         point_segment_distance( false, 
                                 v, overlapping_vertices[i], 
                                 rhead, ray_head_dummy_index, 
                                 rorigin, ray_origin_dummy_index, 
                                 distance, ray_parameter, normal, normal_multiplier ); 
         
         if ( distance < RAY_CAST_HIT_DISTANCE )
         {
            if ( ray_parameter < vertex_min_parameter )
            {
               vertex_min_parameter = ray_parameter - RAY_CAST_HIT_DISTANCE;
               vertex_min_index = overlapping_vertices[i];
            }
         }
      }

      if ( vertex_min_parameter < 1e30 )
      {
         hit_index = vertex_min_index;
         return SurfTrack::RAY_HIT_VERTEX;
      }
      else
      {
         return SurfTrack::RAY_HIT_NOTHING;
      }
         
   }
   else if ( primitive_type == 1)
   {
         
      // -----------------------------------------------------------------
      // Edges
      // -----------------------------------------------------------------
      
      double edge_min_distance = 1e30;
      unsigned int edge_min_index = ~0;
      
      std::vector<unsigned int> overlapping_edges;
      m_broad_phase->get_potential_edge_collisions( aabb_low, aabb_high, overlapping_edges );

      for ( unsigned int i = 0; i < overlapping_edges.size(); ++i )
      {
         const Vec2ui& e = m_mesh.m_edges[ overlapping_edges[i] ];
         const Vec3d& v0 = m_positions[ e[0] ];
         const Vec3d& v1 = m_positions[ e[1] ];
         
         double distance;
         double ray_parameter, edge_parameter;
         Vec3d normal;
         
         segment_segment_distance( rhead, ray_head_dummy_index, 
                                   rorigin, ray_origin_dummy_index,
                                   v0, e[0], 
                                   v1, e[1],
                                   distance, ray_parameter, edge_parameter, normal );
         
         if ( distance < RAY_CAST_HIT_DISTANCE && edge_parameter > 0.0 && edge_parameter < 1.0 )
         {
            if ( distance < edge_min_distance )
            {
               edge_min_distance = distance; // - RAY_CAST_HIT_DISTANCE;
               edge_min_index = overlapping_edges[i];
            }
         }         
         
      }
      
      if ( edge_min_distance < 1e30 )
      {
         hit_index = edge_min_index;
         return SurfTrack::RAY_HIT_EDGE;
      }
      else
      {
         return SurfTrack::RAY_HIT_NOTHING;
      }
      
      
   }
   else
   {
      // -----------------------------------------------------------------
      // Triangles
      // -----------------------------------------------------------------
       
      double triangle_min_parameter = 1e30;
      unsigned int triangle_min_index = ~0;

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
         
         double ray_parameter, s0, s1, s2, rel_disp;
         Vec3d normal;
         unsigned int dummy_index = m_positions.size();
         
         bool ray_hit = point_triangle_collision( rorigin, rhead, dummy_index, 
                                                  v0, v0, t[0],
                                                  v1, v1, t[1],
                                                  v2, v2, t[2],   
                                                  s0, s1, s2,
                                                  normal, ray_parameter, rel_disp );

         if ( ray_hit )
         {
            if ( ray_parameter < triangle_min_parameter )
            {
               triangle_min_parameter = ray_parameter;
               triangle_min_index = overlapping_triangles[i];
            }
         }         
      }
      
      if ( triangle_min_parameter < 1e30 )
      {
         hit_index = triangle_min_index;
         return SurfTrack::RAY_HIT_TRIANGLE;
      }
      else
      {
         return SurfTrack::RAY_HIT_NOTHING;
      }
      
   }
   
}


// --------------------------------------------------------
///
/// Continuous collision detection between two triangles.  Duplicates collision detection, so 
/// should be used rarely, and only when inconvenient to run edge-edge and point-tri tests individually.
///
// --------------------------------------------------------

bool SurfTrack::check_triangle_vs_triangle_collision( const Vec3ui& triangle_a, const Vec3ui& triangle_b )
{
   // --------------------------------------------------------
   // Point-triangle
   // --------------------------------------------------------
   
   // one point from triangle_a vs triangle_b
   
   for ( unsigned int i = 0; i < 3; ++i )
   {
      unsigned int vertex_0 = triangle_a[i];
      
      Vec3ui tb = sort_triangle(triangle_b);
      assert( tb[0] < tb[1] && tb[0] < tb[2] && tb[1] < tb[2] );

      unsigned int vertex_1 = tb[0];
      unsigned int vertex_2 = tb[1];
      unsigned int vertex_3 = tb[2];
      
      if ( vertex_0 == vertex_1 || vertex_0 == vertex_2 || vertex_0 == vertex_3 )
      {
         continue;
      }
   
      if ( point_triangle_collision(  m_positions[ vertex_0 ], m_newpositions[ vertex_0 ], vertex_0,
                                      m_positions[ vertex_1 ], m_newpositions[ vertex_1 ], vertex_1, 
                                      m_positions[ vertex_2 ], m_newpositions[ vertex_2 ], vertex_2,
                                      m_positions[ vertex_3 ], m_newpositions[ vertex_3 ], vertex_3 ) )
         
      {
         return true;
      }
   }
   
   // one point from triangle_b vs triangle_a
   
   for ( unsigned int i = 0; i < 3; ++i )
   {
      unsigned int vertex_0 = triangle_b[i];
      
      Vec3ui ta = sort_triangle(triangle_a);
      assert( ta[0] < ta[1] && ta[0] < ta[2] && ta[1] < ta[2] );
      
      unsigned int vertex_1 = ta[0];
      unsigned int vertex_2 = ta[1];
      unsigned int vertex_3 = ta[2];
            
      if ( vertex_0 == vertex_1 || vertex_0 == vertex_2 || vertex_0 == vertex_3 )
      {
         continue;
      }
      
      if ( point_triangle_collision(  m_positions[ vertex_0 ], m_newpositions[ vertex_0 ], vertex_0,
                                      m_positions[ vertex_1 ], m_newpositions[ vertex_1 ], vertex_1,
                                      m_positions[ vertex_2 ], m_newpositions[ vertex_2 ], vertex_2,
                                      m_positions[ vertex_3 ], m_newpositions[ vertex_3 ], vertex_3 ) )
      {
         return true;
      }
   }
   
   
   // --------------------------------------------------------
   // edge-edge
   // --------------------------------------------------------
   
   static const unsigned int i_plus_one[3] = { 1, 2, 0 };      // avoid (i+1) % 3
   
   for ( unsigned i = 0; i < 3; ++i )
   {
      // one edge
      unsigned int vertex_0 = triangle_a[i];
      unsigned int vertex_1 = triangle_a[ i_plus_one[i] ];
      
      for ( unsigned j = 0; j < 3; ++j )
      {
         // another edge
         unsigned int vertex_2 = triangle_b[j];
         unsigned int vertex_3 = triangle_b[ i_plus_one[j] ];
         
         if ( vertex_0 == vertex_2 || vertex_0 == vertex_3 || vertex_1 == vertex_2 || vertex_1 == vertex_3 )
         {
            continue;
         }

         if ( vertex_1 < vertex_0 ) { swap( vertex_0, vertex_1 ); }
         if ( vertex_3 < vertex_2 ) { swap( vertex_2, vertex_3 ); }
         
         if ( segment_segment_collision(  m_positions[ vertex_0 ], m_newpositions[ vertex_0 ], vertex_0, 
                                          m_positions[ vertex_1 ], m_newpositions[ vertex_1 ], vertex_1,
                                          m_positions[ vertex_2 ], m_newpositions[ vertex_2 ], vertex_2,
                                          m_positions[ vertex_3 ], m_newpositions[ vertex_3 ], vertex_3 ) )               
         {
            return true;
         }
      }
   }
   
   return false;
}


// ========================================================
// Edge splitting functions
// ========================================================

// --------------------------------------------------------
///
/// Check if the "pseudo motion" of moving new_vertex_position to new_vertex_smooth_position introduces any intersections
///
// --------------------------------------------------------

bool SurfTrack::split_edge_pseudo_motion_introduces_collision( const Vec3d& new_vertex_position, 
                                                               const Vec3d& new_vertex_smooth_position, 
                                                               unsigned int edge,
                                                               unsigned int tri0, 
                                                               unsigned int tri1, 
                                                               unsigned int vertex_a,
                                                               unsigned int vertex_b,
                                                               unsigned int vertex_c,
                                                               unsigned int vertex_d )
{

   if ( !m_collision_safety)
   {
      return false;
   }
   
   // new point vs all triangles
   {
      
      Vec3d aabb_low, aabb_high;
      minmax( new_vertex_position, new_vertex_smooth_position, aabb_low, aabb_high );

      aabb_low -= m_proximity_epsilon * Vec3d(1,1,1);
      aabb_high += m_proximity_epsilon * Vec3d(1,1,1);
         
      std::vector<unsigned int> overlapping_triangles;
      m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, overlapping_triangles );
      
      for ( unsigned int i = 0; i < overlapping_triangles.size(); ++i )
      {
         
         if ( overlapping_triangles[i] == tri0 || overlapping_triangles[i] == tri1 )
         {
            continue;
         }
         
         unsigned int triangle_vertex_0 = m_mesh.m_tris[ overlapping_triangles[i] ][0];
         unsigned int triangle_vertex_1 = m_mesh.m_tris[ overlapping_triangles[i] ][1];
         unsigned int triangle_vertex_2 = m_mesh.m_tris[ overlapping_triangles[i] ][2];
         
         double t_zero_distance;
         unsigned int dummy_index = m_positions.size();
         point_triangle_distance( new_vertex_position, dummy_index, 
                                  m_positions[ triangle_vertex_0 ], triangle_vertex_0,
                                  m_positions[ triangle_vertex_1 ], triangle_vertex_1,
                                  m_positions[ triangle_vertex_2 ], triangle_vertex_2,
                                  t_zero_distance );
         
         if ( t_zero_distance < m_improve_collision_epsilon )
         {
            return true;
         }

         Vec3ui sorted_triangle = sort_triangle( Vec3ui( triangle_vertex_0, triangle_vertex_1, triangle_vertex_2 ) );
         
         
         if ( point_triangle_collision(  new_vertex_position, new_vertex_smooth_position, dummy_index,
                                         m_positions[ sorted_triangle[0] ], m_positions[ sorted_triangle[0] ], sorted_triangle[0],
                                         m_positions[ sorted_triangle[1] ], m_positions[ sorted_triangle[1] ], sorted_triangle[1],
                                         m_positions[ sorted_triangle[2] ], m_positions[ sorted_triangle[2] ], sorted_triangle[2] ) )
               
         {
            return true;
         }
      }
       
   }
   
   // new edges vs all edges
   
   {
      
      Vec3d edge_aabb_low, edge_aabb_high;
      
      // do one big query into the broadphase for all 4 new edges
      minmax( new_vertex_position, new_vertex_smooth_position, 
              m_positions[ vertex_a ], m_positions[ vertex_b ], m_positions[ vertex_c ], m_positions[ vertex_d ],
              edge_aabb_low, edge_aabb_high );
      
      edge_aabb_low -= m_proximity_epsilon * Vec3d(1,1,1);
      edge_aabb_high += m_proximity_epsilon * Vec3d(1,1,1);

      std::vector<unsigned int> overlapping_edges;
      m_broad_phase->get_potential_edge_collisions( edge_aabb_low, edge_aabb_high, overlapping_edges );
      
      for ( unsigned int i = 0; i < overlapping_edges.size(); ++i )
      {
         
         if ( overlapping_edges[i] == edge ) { continue; }
         if ( m_mesh.m_edges[ overlapping_edges[i] ][0] == m_mesh.m_edges[ overlapping_edges[i] ][1] ) { continue; }
         
         unsigned int edge_vertex_0 = m_mesh.m_edges[ overlapping_edges[i] ][0];
         unsigned int edge_vertex_1 = m_mesh.m_edges[ overlapping_edges[i] ][1];
         unsigned int dummy_index = m_positions.size();
         
         if ( vertex_a != edge_vertex_0 && vertex_a != edge_vertex_1 ) 
         {
            double t_zero_distance;   
            segment_segment_distance( new_vertex_position, dummy_index,
                                      m_positions[ vertex_a ], vertex_a, 
                                      m_positions[ edge_vertex_0 ], edge_vertex_0,
                                      m_positions[ edge_vertex_1 ], edge_vertex_1,
                                      t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }

            if ( edge_vertex_1 < edge_vertex_0 ) { swap( edge_vertex_0, edge_vertex_1 ); }

            if ( segment_segment_collision( m_positions[ vertex_a ], m_positions[ vertex_a ], vertex_a,
                                            new_vertex_position, new_vertex_smooth_position, dummy_index,
                                            m_positions[ edge_vertex_0 ], m_positions[ edge_vertex_0 ], edge_vertex_0,
                                            m_positions[ edge_vertex_1 ], m_positions[ edge_vertex_1 ], edge_vertex_1 ) )
                  
            {      
               return true;
            }
         }
         
         if ( vertex_b != edge_vertex_0 && vertex_b != edge_vertex_1 ) 
         {
            double t_zero_distance;
            segment_segment_distance( new_vertex_position, dummy_index,
                                      m_positions[ vertex_b ], vertex_b,
                                      m_positions[ edge_vertex_0 ], edge_vertex_0,
                                      m_positions[ edge_vertex_1 ], edge_vertex_1,
                                      t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }

            if ( edge_vertex_1 < edge_vertex_0 ) { swap( edge_vertex_0, edge_vertex_1 ); }
                        
            if ( segment_segment_collision( m_positions[ vertex_b ], m_positions[ vertex_b ], vertex_b, 
                                            new_vertex_position, new_vertex_smooth_position, dummy_index,
                                            m_positions[ edge_vertex_0 ], m_positions[ edge_vertex_0 ], edge_vertex_0,
                                            m_positions[ edge_vertex_1 ], m_positions[ edge_vertex_1 ], edge_vertex_1 ) )
                  
            {          
               return true;
            }
         }
         
         if ( vertex_c != edge_vertex_0 && vertex_c != edge_vertex_1 ) 
         {
            double t_zero_distance;
            segment_segment_distance( new_vertex_position, dummy_index,
                                      m_positions[ vertex_c ], vertex_c,
                                      m_positions[ edge_vertex_0 ], edge_vertex_0,
                                      m_positions[ edge_vertex_1 ], edge_vertex_1,
                                      t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
            
            if ( edge_vertex_1 < edge_vertex_0 ) { swap( edge_vertex_0, edge_vertex_1 ); }
            
            if ( segment_segment_collision( m_positions[ vertex_c ], m_positions[ vertex_c ], vertex_c,
                                            new_vertex_position, new_vertex_smooth_position, dummy_index, 
                                            m_positions[ edge_vertex_0 ], m_positions[ edge_vertex_0 ], edge_vertex_0,
                                            m_positions[ edge_vertex_1 ], m_positions[ edge_vertex_1 ], edge_vertex_1 ) )
            {         
               return true;
            }
         }
         
         if ( vertex_d != edge_vertex_0 && vertex_d != edge_vertex_1 ) 
         {
            double t_zero_distance;
            segment_segment_distance( new_vertex_position, dummy_index,
                                      m_positions[ vertex_d ], vertex_d,
                                      m_positions[ edge_vertex_0 ], edge_vertex_0,
                                      m_positions[ edge_vertex_1 ], edge_vertex_1,
                                      t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
            
            if ( edge_vertex_1 < edge_vertex_0 ) { swap( edge_vertex_0, edge_vertex_1 ); }
            
            if ( segment_segment_collision( m_positions[ vertex_d ], m_positions[ vertex_d ], vertex_d,
                                            new_vertex_position, new_vertex_smooth_position, dummy_index,
                                            m_positions[ edge_vertex_0 ], m_positions[ edge_vertex_0 ], edge_vertex_0,
                                            m_positions[ edge_vertex_1 ], m_positions[ edge_vertex_1 ], edge_vertex_1 ) )
            {         
               return true;
            }
         }	
      }
      
   }
  
   // new triangle vs all points
   
   {
      Vec3d triangle_aabb_low, triangle_aabb_high;
      
      // do one big query into the broadphase for all 4 new triangles
      minmax( new_vertex_position, new_vertex_smooth_position, 
              m_positions[ vertex_a ], m_positions[ vertex_b ], m_positions[ vertex_c ], m_positions[ vertex_d ],
              triangle_aabb_low, triangle_aabb_high );
      
      triangle_aabb_low -= m_proximity_epsilon * Vec3d(1,1,1);
      triangle_aabb_high += m_proximity_epsilon * Vec3d(1,1,1);
      
      std::vector<unsigned int> overlapping_vertices;
      m_broad_phase->get_potential_vertex_collisions( triangle_aabb_low, triangle_aabb_high, overlapping_vertices );
            
      const Vec3d& position_a = m_positions[vertex_a];
      const Vec3d& position_b = m_positions[vertex_b];
      const Vec3d& position_c = m_positions[vertex_c];
      const Vec3d& position_d = m_positions[vertex_d];
      const Vec3d& position_e = new_vertex_position;
      const Vec3d& newposition_e = new_vertex_smooth_position;
      unsigned int dummy_e = m_positions.size();
      
      for ( unsigned int i = 0; i < overlapping_vertices.size(); ++i )
      {
         
         if ( m_mesh.m_vtxtri[overlapping_vertices[i]].empty() ) { continue; }

         unsigned int overlapping_vert_index = overlapping_vertices[i];
         const Vec3d& vert = m_positions[overlapping_vert_index];
         
         // triangle aec
         if ( overlapping_vertices[i] != vertex_a && overlapping_vertices[i] != vertex_c )
         {
            double t_zero_distance;
            point_triangle_distance( vert, overlapping_vert_index, position_a, vertex_a, position_e, dummy_e, position_c, vertex_c, t_zero_distance );
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
            
            if ( vertex_a < vertex_c )
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                              position_a, position_a, vertex_a,
                                              position_c, position_c, vertex_c,
                                              position_e, newposition_e, dummy_e ) )
               {         
                  return true;
               }
            }
            else
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                              position_c, position_c, vertex_c,
                                              position_a, position_a, vertex_a,
                                              position_e, newposition_e, dummy_e ) )
               {         
                  return true;
               }
            }               
         }

         // triangle ceb
         if ( overlapping_vertices[i] != vertex_c && overlapping_vertices[i] != vertex_b )
         {
            double t_zero_distance;
            point_triangle_distance( vert, overlapping_vert_index, 
                                     position_c, vertex_c,
                                     position_e, dummy_e,
                                     position_b, vertex_b, 
                                     t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
            
            if ( vertex_b < vertex_c )
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                              position_b, position_b, vertex_b,
                                              position_c, position_c, vertex_c,
                                              position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }
            }
            else
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                              position_c, position_c, vertex_c,
                                              position_b, position_b, vertex_b,
                                              position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }               
            }
         }

         // triangle dbe
         if ( overlapping_vertices[i] != vertex_d && overlapping_vertices[i] != vertex_b )
         {
            double t_zero_distance;
            point_triangle_distance( vert, overlapping_vert_index, 
                                     position_d, vertex_d,
                                     position_b, vertex_b, 
                                     position_e, dummy_e,
                                     t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
   
            if ( vertex_b < vertex_d )
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                             position_b, position_b, vertex_b,
                                             position_d, position_d, vertex_d,
                                             position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }
            }
            else
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                             position_d, position_d, vertex_d,
                                             position_b, position_b, vertex_b,
                                             position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }               
            }
         }

         // triangle dea
         if ( overlapping_vertices[i] != vertex_d && overlapping_vertices[i] != vertex_a )
         {
            double t_zero_distance;
            point_triangle_distance( vert, overlapping_vert_index,
                                     position_d, vertex_d,
                                     position_e, dummy_e,
                                     position_a, vertex_a,
                                     t_zero_distance );
            
            if ( t_zero_distance < m_improve_collision_epsilon )
            {
               return true;
            }
            
            if ( vertex_a < vertex_d )
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                             position_a, position_a, vertex_a,
                                             position_d, position_d, vertex_d,
                                             position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }
            }
            else
            {
               if ( point_triangle_collision( vert, vert, overlapping_vert_index,
                                             position_d, position_d, vertex_d,
                                             position_a, position_a, vertex_a,
                                             position_e, newposition_e, dummy_e ) )
               {        
                  return true;
               }               
            }
         }
         
      }
   }
   
   return false;
   
}

                                                
// --------------------------------------------------------
///
/// Split an edge, using subdivision_scheme to determine the new vertex location, if safe to do so.
///
// --------------------------------------------------------

bool SurfTrack::split_edge( unsigned int edge )
{
   Vec2ui original_edge = m_mesh.m_edges[edge];
      
   // --------------
   
   // Only split edges inicident on 2 triangles
   if ( m_mesh.m_edgetri[edge].size() != 2 )
   {
      return false;
   }

   // --------------
   
   unsigned int tri0 = m_mesh.m_edgetri[edge][0];
   unsigned int tri1 = m_mesh.m_edgetri[edge][1];
   double area0 = get_triangle_area( tri0 );
   double area1 = get_triangle_area( tri1 );
   
   // Splitting degenerate triangles causes problems
   if ( area0 < m_min_triangle_area || area1 < m_min_triangle_area )
   {
      return false;
   }

   // --------------

   // convert triangles abc and dba into triangles aec, ceb, dbe and dea
   
   unsigned int vertex_a = m_mesh.m_edges[edge][0];
   unsigned int vertex_b = m_mesh.m_edges[edge][1];
   unsigned int vertex_c, vertex_d;
   
   if ( m_mesh.oriented( vertex_a, vertex_b, m_mesh.m_tris[tri0] ) )
   {
      // tri0 = abc
		assert( m_mesh.oriented( vertex_b, vertex_a, m_mesh.m_tris[tri1] ) );
      vertex_c = m_mesh.get_third_vertex( vertex_a, vertex_b, m_mesh.m_tris[tri0] );      
      vertex_d = m_mesh.get_third_vertex( vertex_b, vertex_a, m_mesh.m_tris[tri1] );
   }
   else
   {
      // tri1 = abc
      assert( m_mesh.oriented( vertex_a, vertex_b, m_mesh.m_tris[tri1] ) );
      assert( m_mesh.oriented( vertex_b, vertex_a, m_mesh.m_tris[tri0] ) );
      vertex_c = m_mesh.get_third_vertex( vertex_a, vertex_b, m_mesh.m_tris[tri1] );
      vertex_d = m_mesh.get_third_vertex( vertex_b, vertex_a, m_mesh.m_tris[tri0] );
   }
   
   Vec3d new_vertex_position = 0.5 * ( m_positions[ vertex_a ] + m_positions[ vertex_b ] );
   Vec3d new_vertex_smooth_position;
   
   // generate the new midpoint according to the subdivision scheme
   m_subdivision_scheme->generate_new_midpoint( edge, *this, new_vertex_smooth_position );

   // --------------

   // check if the generated point introduces an intersection
   
   bool use_smooth_point = ! ( split_edge_pseudo_motion_introduces_collision( new_vertex_position, 
                                                                              new_vertex_smooth_position, 
                                                                              edge, 
                                                                              tri0, 
                                                                              tri1, 
                                                                              vertex_a, 
                                                                              vertex_b, 
                                                                              vertex_c, 
                                                                              vertex_d ) );
      
   // --------------
   
   // check normal inversion
   if ( use_smooth_point )
   {
      Vec3d tri0_normal = get_triangle_normal( tri0 );
      Vec3d tri1_normal = get_triangle_normal( tri1 );
      if ( dot( tri0_normal, tri1_normal ) >= 0.0 )
      {
         Vec3d new_normal = triangle_normal( m_positions[vertex_a], new_vertex_smooth_position, m_positions[vertex_c] );
         if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
         {
            use_smooth_point = false;
         }
         new_normal = triangle_normal( m_positions[vertex_c], new_vertex_smooth_position, m_positions[vertex_b] );
         if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
         {
            use_smooth_point = false;
         }         
         new_normal = triangle_normal( m_positions[vertex_d], m_positions[vertex_b], new_vertex_smooth_position );
         if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
         {
            use_smooth_point = false;
         }         
         new_normal = triangle_normal( m_positions[vertex_d], new_vertex_smooth_position, m_positions[vertex_a] );
         if ( dot( new_normal, tri0_normal ) < 0.0 || dot( new_normal, tri1_normal ) < 0.0 )
         {
            use_smooth_point = false;
         }         
      }
   }
   
   // --------------
   
   // if the new point introduces an intersection, try using the edge midpoint
   
   if ( use_smooth_point == false )
   {
      if ( m_verbose ) { printf( "not using smooth subdivision\n" ); }
      new_vertex_smooth_position = new_vertex_position;
      
      if ( split_edge_pseudo_motion_introduces_collision( new_vertex_position, 
                                                          new_vertex_smooth_position, 
                                                          edge, 
                                                          tri0, 
                                                          tri1, 
                                                          vertex_a, 
                                                          vertex_b, 
                                                          vertex_c, 
                                                          vertex_d ) )
      {
         if ( m_verbose )  { std::cout << "Even mid-point subdivision introduces collision.  Backing out." << std::endl; }
         return false;
      }
   }
 	else
   {
      if ( m_verbose ) { printf( "using smooth subdivision\n" ); }
   }
   
   // --------------
   
   // Do the actual splitting
   
   Vec3d new_vertex_velocity = 0.5 * ( m_velocities[ vertex_a ] + m_velocities[ vertex_b ] );
         
   double new_vertex_mass = min( m_masses[ vertex_a ], m_masses[ vertex_b ] );
   unsigned int vertex_e = add_vertex( new_vertex_smooth_position, new_vertex_velocity, new_vertex_mass );
   
   if ( m_verbose ) std::cout << "new vertex: " << vertex_e << std::endl;
   
   remove_triangle( tri0 );
   remove_triangle( tri1 );

   unsigned int new_triangle_index = add_triangle( Vec3ui( vertex_a, vertex_e, vertex_c ) );
   new_triangle_index = add_triangle( Vec3ui( vertex_c, vertex_e, vertex_b ) );
   new_triangle_index = add_triangle( Vec3ui( vertex_d, vertex_b, vertex_e ) );
   new_triangle_index = add_triangle( Vec3ui( vertex_d, vertex_e, vertex_a ) );      
   
   return true;
   
}


// ========================================================
// Edge collapse functions
// ========================================================

// --------------------------------------------------------
///
/// Check the "pseudo motion" introduced by a collapsing edge for collision
///
// --------------------------------------------------------

bool SurfTrack::collapse_edge_pseudo_motion_introduces_collision( unsigned int source_vertex, 
                                                                  unsigned int destination_vertex, 
                                                                  unsigned int edge_index, 
                                                                  const Vec3d& vertex_new_position )
{
   if ( !m_collision_safety )
   {
      return false;
   }
   
   assert( m_newpositions.size() > 0 );
     
   // Change source vertex predicted position to superimpose onto dest vertex
   m_newpositions[source_vertex] = vertex_new_position;
   m_newpositions[destination_vertex] = vertex_new_position;
   
   update_continuous_broad_phase( source_vertex );
   update_continuous_broad_phase( destination_vertex );
   
   // Get the set of triangles which are going to be deleted
   std::vector< unsigned int >& triangles_incident_to_edge = m_mesh.m_edgetri[edge_index];   

   // Get the set of triangles which move because of this motion
   std::vector<unsigned int> moving_triangles;
   for ( unsigned int i = 0; i < m_mesh.m_vtxtri[source_vertex].size(); ++i )
   {
      moving_triangles.push_back( m_mesh.m_vtxtri[source_vertex][i] );
   }
   for ( unsigned int i = 0; i < m_mesh.m_vtxtri[destination_vertex].size(); ++i )
   {
      moving_triangles.push_back( m_mesh.m_vtxtri[destination_vertex][i] );
   }
   
   // Check this set of triangles for collisions, holding everything else static
		
   for ( unsigned int i = 0; i < moving_triangles.size(); ++i )
   { 
      
      // Disregard triangles which will end up being deleted - those triangles incident to the collapsing edge.
      bool triangle_will_be_deleted = false;
      for ( unsigned int j = 0; j < triangles_incident_to_edge.size(); ++j )
      {
         if ( moving_triangles[i] == triangles_incident_to_edge[j] )
         {
            triangle_will_be_deleted = true;
            break;
         }
      }
      
      if ( triangle_will_be_deleted ) { continue; }
      
      const Vec3ui& current_triangle = m_mesh.m_tris[ moving_triangles[i] ];
      
      if ( m_collision_safety )
      {
         // Test the triangle vs all other triangles
         Vec3d aabb_low, aabb_high;
         minmax( m_positions[ current_triangle[0] ], m_positions[ current_triangle[1] ], m_positions[ current_triangle[2] ], 
                 m_newpositions[ current_triangle[0] ], m_newpositions[ current_triangle[1] ], m_newpositions[ current_triangle[2] ], 
                 aabb_low, aabb_high );

         std::vector<unsigned int> overlapping_triangles;
         m_broad_phase->get_potential_triangle_collisions( aabb_low, aabb_high, overlapping_triangles );
         
         for ( unsigned j=0; j < overlapping_triangles.size(); ++j )
         {
            // Don't check against triangles which are incident to the dest vertex
            bool triangle_incident_to_dest = false;
            for ( unsigned int k = 0; k < moving_triangles.size(); ++k )
            {
               if ( moving_triangles[k] == overlapping_triangles[j] )
               {
                  triangle_incident_to_dest = true;
                  break;
               }
            }
            if ( triangle_incident_to_dest )    { continue; }
            
            if ( check_triangle_vs_triangle_collision( current_triangle, m_mesh.m_tris[ overlapping_triangles[j] ] ) )
            {
               if ( m_verbose ) { printf( "collapse edge not collision-safe\n" ); }
               return true;
            }
         }
      }
      
   }

   return false;
   
}


// --------------------------------------------------------
///
/// 
///
// --------------------------------------------------------

bool SurfTrack::collapse_edge_introduces_normal_inversion( unsigned int source_vertex, 
                                                           unsigned int destination_vertex, 
                                                           unsigned int edge_index, 
                                                           const Vec3d& vertex_new_position )
{
   
   assert( m_newpositions.size() > 0 );
   
   // Change source vertex predicted position to superimpose onto dest vertex
   m_newpositions[source_vertex] = vertex_new_position;
   m_newpositions[destination_vertex] = vertex_new_position;
   
   // Get the set of triangles which are going to be deleted
   std::vector< unsigned int >& triangles_incident_to_edge = m_mesh.m_edgetri[edge_index];   
   
   // Get the set of triangles which move because of this motion
   std::vector<unsigned int> moving_triangles;
   for ( unsigned int i = 0; i < m_mesh.m_vtxtri[source_vertex].size(); ++i )
   {
      moving_triangles.push_back( m_mesh.m_vtxtri[source_vertex][i] );
   }
   for ( unsigned int i = 0; i < m_mesh.m_vtxtri[destination_vertex].size(); ++i )
   {
      moving_triangles.push_back( m_mesh.m_vtxtri[destination_vertex][i] );
   }

   //
   // check for normal inversion
   //
   
   for ( unsigned int i = 0; i < moving_triangles.size(); ++i )
   { 
      
      // Disregard triangles which will end up being deleted - those triangles incident to the collapsing edge.
      bool triangle_will_be_deleted = false;
      for ( unsigned int j = 0; j < triangles_incident_to_edge.size(); ++j )
      {
         if ( moving_triangles[i] == triangles_incident_to_edge[j] )
         {
            triangle_will_be_deleted = true;
            break;
         }
      }
      
      if ( triangle_will_be_deleted ) { continue; }
      
      const Vec3ui& current_triangle = m_mesh.m_tris[ moving_triangles[i] ];
      Vec3d old_normal = get_triangle_normal( current_triangle );
   
      Vec3d new_normal;
      
      double new_area;
      if ( current_triangle[0] == source_vertex || current_triangle[0] == destination_vertex )
      { 
         new_normal = triangle_normal( vertex_new_position, m_positions[current_triangle[1]], m_positions[current_triangle[2]] ); 
         new_area = triangle_area( vertex_new_position, m_positions[current_triangle[1]], m_positions[current_triangle[2]] ); 
      }
      else if ( current_triangle[1] == source_vertex || current_triangle[1] == destination_vertex ) 
      { 
         new_normal = triangle_normal( m_positions[current_triangle[0]], vertex_new_position, m_positions[current_triangle[2]] ); 
         new_area = triangle_area( m_positions[current_triangle[0]], vertex_new_position, m_positions[current_triangle[2]] ); 
      }
      else 
      { 
         assert( current_triangle[2] == source_vertex || current_triangle[2] == destination_vertex ); 
         new_normal = triangle_normal( m_positions[current_triangle[0]], m_positions[current_triangle[1]], vertex_new_position );
         new_area = triangle_area( m_positions[current_triangle[0]], m_positions[current_triangle[1]], vertex_new_position );
      }      
     
      if ( dot( new_normal, old_normal ) < 0.0 )
      {
         if ( m_verbose ) { printf( "collapse edge introduces normal inversion\n" ); }
         return true;
      } 
      
      if ( new_area < m_min_triangle_area * m_min_triangle_area )
      {
         if ( m_verbose ) { printf( "collapse edge introduces tiny triangle area\n" ); }
         return true;
      }         
   }

   return false;
   
}


// --------------------------------------------------------
///
/// Determine wether collapsing an edge will introduce an unacceptable change in volume.
///
// --------------------------------------------------------

bool SurfTrack::collapse_edge_introduces_volume_change( unsigned int source_vertex, 
                                                        unsigned int edge_index, 
                                                        const Vec3d& vertex_new_position )
{
   //
   // If any incident triangle has a tiny area, collapse the edge without regard to volume change
   //

   const std::vector<unsigned int>& inc_tris = m_mesh.m_edgetri[edge_index];
   
   for ( unsigned int i = 0; i < inc_tris.size(); ++i )
   {
      if ( get_triangle_area( inc_tris[i] ) < m_min_triangle_area )
      {
         return false;
      }
   }

   //
   // Check volume change
   //

   const std::vector< unsigned int >& triangles_incident_to_vertex = m_mesh.m_vtxtri[source_vertex];
   double volume_change = 0;

   for ( unsigned int i = 0; i < triangles_incident_to_vertex.size(); ++i )
   {
      Vec3ui& inc_tri = m_mesh.m_tris[ triangles_incident_to_vertex[i] ];
      volume_change += tetrahedron_signed_volume( vertex_new_position, m_positions[inc_tri[0]], m_positions[inc_tri[1]], m_positions[inc_tri[2]] );
   }

   if ( fabs(volume_change) > m_max_volume_change )
   {
      if ( m_verbose ) { printf( "collapse edge introduces volume change\n" ); }
      return true;
   }
   
   return false;

}


// --------------------------------------------------------
///
/// Delete an edge by moving its source vertex to its destination vertex
///
// --------------------------------------------------------

bool SurfTrack::collapse_edge( unsigned int edge )
{

   unsigned int vertex_to_keep = m_mesh.m_edges[edge][0];
   unsigned int vertex_to_delete = m_mesh.m_edges[edge][1];
     
   Vec3d vertex_new_position;
   
   
   // --------------
   
   // rank 1, 2, 3 = smooth, ridge, peak
   // if the vertex ranks don't match, keep the higher rank vertex
   
   if ( classify_vertex( vertex_to_keep ) > classify_vertex( vertex_to_delete ) )
   {
      vertex_new_position = m_positions[vertex_to_keep];
   }
   else if ( classify_vertex( vertex_to_delete ) > classify_vertex( vertex_to_keep ) )
   {
      unsigned int tmp = vertex_to_delete;
      vertex_to_delete = vertex_to_keep;
      vertex_to_keep = tmp;
      
      vertex_new_position = m_positions[vertex_to_keep];
   }
   else
   {
      // ranks are equal
      m_subdivision_scheme->generate_new_midpoint( edge, *this, vertex_new_position );
   }

   if ( m_verbose ) { printf( "Collapsing edge.  Doomed vertex: %d --- Vertex to keep: %d \n", vertex_to_delete, vertex_to_keep ); }
   
   // --------------
   
   // If we're disallowing topology changes, don't let an edge collapse form a degenerate tet
   if ( false == m_allow_topology_changes )
   {

      // for each triangle that *would* be created, make sure that there isn't already a triangle with those 3 vertices
      
      for ( unsigned int i = 0; i < m_mesh.m_vtxtri[vertex_to_delete].size(); ++i )
      {
         Vec3ui new_triangle = m_mesh.m_tris[ m_mesh.m_vtxtri[vertex_to_delete][i] ];
         if ( new_triangle[0] == vertex_to_delete )   { new_triangle[0] = vertex_to_keep; }
         if ( new_triangle[1] == vertex_to_delete )   { new_triangle[1] = vertex_to_keep; }
         if ( new_triangle[2] == vertex_to_delete )   { new_triangle[2] = vertex_to_keep; }

         for ( unsigned int j = 0; j < m_mesh.m_vtxtri[vertex_to_keep].size(); ++j )
         {
            if ( NonDestructiveTriMesh::triangle_has_these_verts( m_mesh.m_tris[ m_mesh.m_vtxtri[vertex_to_keep][j] ], new_triangle ) )
            {
               return false;
            }            
         }
      }
   }
   
	// Copy this vector, don't take a reference, as deleting will change the original
   std::vector< unsigned int > triangles_incident_to_edge = m_mesh.m_edgetri[edge];
    
   // --------------
   
   // Do not collapse edge on a degenerate tet or degenerate triangle
   for ( unsigned int i=0; i < triangles_incident_to_edge.size(); ++i )
   {
      const Vec3ui& triangle_i = m_mesh.m_tris[ triangles_incident_to_edge[i] ];
         
      if ( triangle_i[0] == triangle_i[1] || triangle_i[1] == triangle_i[2] || triangle_i[2] == triangle_i[0] )
      {
         return false;
      }
      
      for ( unsigned int j=i+1; j < triangles_incident_to_edge.size(); ++j )
      {
         const Vec3ui& triangle_j = m_mesh.m_tris[ triangles_incident_to_edge[j] ];
         
         if ( ( triangle_i[0] == triangle_j[0] || triangle_i[0] == triangle_j[1] || triangle_i[0] == triangle_j[2] ) &&
              ( triangle_i[1] == triangle_j[0] || triangle_i[1] == triangle_j[1] || triangle_i[1] == triangle_j[2] ) &&
              ( triangle_i[2] == triangle_j[0] || triangle_i[2] == triangle_j[1] || triangle_i[2] == triangle_j[2] ) )
         {
            return false;
         }
      }
   }
         
   // --------------
   
   // Check vertex pseudo motion for collisions and volume change
   
   if ( mag ( m_positions[m_mesh.m_edges[edge][1]] - m_positions[m_mesh.m_edges[edge][0]] ) > 0 )
   {
      bool volume_change = collapse_edge_introduces_volume_change( vertex_to_delete, edge, vertex_new_position );

      if ( volume_change )
      {
         // Restore saved positions which were changed by the function we just called.
         m_newpositions[vertex_to_keep] = m_positions[vertex_to_keep];
         m_newpositions[vertex_to_delete] = m_positions[vertex_to_delete];         
         return false;
      }
      
      bool collision = collapse_edge_pseudo_motion_introduces_collision( vertex_to_delete, vertex_to_keep, edge, vertex_new_position );
      
      collision |= collapse_edge_introduces_normal_inversion(  vertex_to_delete, vertex_to_keep, edge, vertex_new_position );
      
      // Restore saved positions which were changed by the function we just called.
      m_newpositions[vertex_to_keep] = m_positions[vertex_to_keep];
      m_newpositions[vertex_to_delete] = m_positions[vertex_to_delete];
      
      if ( collision )
      {
         //std::cout << "edge collapse would introduce collision or change volume too much or invert triangle normals" << std::endl;
         return false;
      }
   }

   // --------------
   
   // move the vertex we decided to keep
   
   m_newpositions[vertex_to_keep] = m_positions[vertex_to_keep] = vertex_new_position;

   if ( m_collision_safety )
   {
      update_static_broad_phase( vertex_to_keep );
   }
   
   // Delete triangles incident on the edge
   
   for ( unsigned int i=0; i < triangles_incident_to_edge.size(); ++i )
   {
      if ( m_verbose )
      {
         printf( "removing edge-incident triangle: %d %d %d\n", 
                 m_mesh.m_tris[ triangles_incident_to_edge[i] ][0],
                 m_mesh.m_tris[ triangles_incident_to_edge[i] ][1],
                 m_mesh.m_tris[ triangles_incident_to_edge[i] ][2] );
      }
      
      remove_triangle( triangles_incident_to_edge[i] );
   }
   
   // Find anything pointing to the doomed vertex and change it
   
   // copy the list of triangles, don't take a refence to it
   std::vector< unsigned int > triangles_incident_to_vertex = m_mesh.m_vtxtri[vertex_to_delete];    
   
   for ( unsigned int i=0; i < triangles_incident_to_vertex.size(); ++i )
   {
      assert( triangles_incident_to_vertex[i] != triangles_incident_to_edge[0] );
      assert( triangles_incident_to_vertex[i] != triangles_incident_to_edge[1] );
      
      Vec3ui new_triangle = m_mesh.m_tris[ triangles_incident_to_vertex[i] ];
      
      if ( new_triangle[0] == vertex_to_delete )   { new_triangle[0] = vertex_to_keep; }
      if ( new_triangle[1] == vertex_to_delete )   { new_triangle[1] = vertex_to_keep; }
      if ( new_triangle[2] == vertex_to_delete )   { new_triangle[2] = vertex_to_keep; }
   
      if ( m_verbose ) { printf( "adding updated triangle: %d %d %d\n", new_triangle[0], new_triangle[1], new_triangle[2] ); }
      
      unsigned int new_triangle_index = add_triangle( new_triangle );
      
      m_dirty_triangles.push_back( new_triangle_index );
   }
   
   for ( unsigned int i=0; i < triangles_incident_to_vertex.size(); ++i )
   {  
      if ( m_verbose )
      {
         printf( "removing vertex-incident triangle: %d %d %d\n", 
                         m_mesh.m_tris[ triangles_incident_to_vertex[i] ][0],
                         m_mesh.m_tris[ triangles_incident_to_vertex[i] ][1],
                         m_mesh.m_tris[ triangles_incident_to_vertex[i] ][2] );
      }
      
      remove_triangle( triangles_incident_to_vertex[i] );
   }
   
   // Delete vertex
   assert( m_mesh.m_vtxtri[vertex_to_delete].empty() );
   remove_vertex( vertex_to_delete );
   
   return true;
}


// ========================================================
// Edge flip functions
// ========================================================

// --------------------------------------------------------
///
/// Check whether the new triangles created by flipping an edge introduce any intersection
///
// --------------------------------------------------------

bool SurfTrack::flip_introduces_collision( unsigned int edge_index, 
                                           const Vec2ui& new_edge, 
                                           const Vec3ui& new_triangle_a, 
                                           const Vec3ui& new_triangle_b )
{  
   if ( !m_collision_safety )
   {
      return false;
   }
   
   const Vec2ui& old_edge = m_mesh.m_edges[edge_index];
   
   unsigned int tet_vertex_indices[4] = { old_edge[0], old_edge[1], new_edge[0], new_edge[1] };
   
   const Vec3d tet_vertex_positions[4] = { m_positions[ tet_vertex_indices[0] ], 
                                           m_positions[ tet_vertex_indices[1] ], 
                                           m_positions[ tet_vertex_indices[2] ], 
                                           m_positions[ tet_vertex_indices[3] ] };
   
   Vec3d low, high;
   minmax( tet_vertex_positions[0], tet_vertex_positions[1], tet_vertex_positions[2], tet_vertex_positions[3], low, high );
   
   std::vector<unsigned int> overlapping_vertices;
   m_broad_phase->get_potential_vertex_collisions( low, high, overlapping_vertices );
   
   // do point-in-tet tests
   for ( unsigned int i = 0; i < overlapping_vertices.size(); ++i ) 
   { 
      if ( (overlapping_vertices[i] == old_edge[0]) || (overlapping_vertices[i] == old_edge[1]) || 
           (overlapping_vertices[i] == new_edge[0]) || (overlapping_vertices[i] == new_edge[1]) ) 
      {
         continue;
      }
      
      if ( point_tetrahedron_intersection( m_positions[overlapping_vertices[i]], overlapping_vertices[i],
                                           tet_vertex_positions[0], tet_vertex_indices[0],
                                           tet_vertex_positions[1], tet_vertex_indices[1],
                                           tet_vertex_positions[2], tet_vertex_indices[2],
                                           tet_vertex_positions[3], tet_vertex_indices[3] ) ) 
      {
         return true;
      }
   }
   
   //
   // Check new triangle A vs existing edges
   //

   minmax( m_positions[new_triangle_a[0]], m_positions[new_triangle_a[1]], m_positions[new_triangle_a[2]], low, high );
   std::vector<unsigned int> overlapping_edges;
   m_broad_phase->get_potential_edge_collisions( low, high, overlapping_edges );
   
   for ( unsigned int i = 0; i < overlapping_edges.size(); ++i )
   {
      unsigned int overlapping_edge_index = overlapping_edges[i];
      const Vec2ui& edge = m_mesh.m_edges[overlapping_edge_index];
      
      if ( check_edge_triangle_intersection_by_index( edge[0], edge[1], 
                                                      new_triangle_a[0], new_triangle_a[1], new_triangle_a[2], 
                                                      m_positions, m_verbose ) )
      {
         return true;
      }      
   }

   //
   // Check new triangle B vs existing edges
   //
   
   minmax( m_positions[new_triangle_b[0]], m_positions[new_triangle_b[1]], m_positions[new_triangle_b[2]], low, high );
   
   overlapping_edges.clear();
   m_broad_phase->get_potential_edge_collisions( low, high, overlapping_edges );
   
   for ( unsigned int i = 0; i < overlapping_edges.size(); ++i )
   {
      unsigned int overlapping_edge_index = overlapping_edges[i];
      const Vec2ui& edge = m_mesh.m_edges[overlapping_edge_index];
      
      if ( check_edge_triangle_intersection_by_index( edge[0], edge[1], 
                                                      new_triangle_b[0], new_triangle_b[1], new_triangle_b[2], 
                                                      m_positions, m_verbose ) )
      {
         return true;
      }      
   }
   
   //
   // Check new edge vs existing triangles
   //   
   
   minmax( m_positions[new_edge[0]], m_positions[new_edge[1]], low, high );
   std::vector<unsigned int> overlapping_triangles;
   m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
   
   for ( unsigned int i = 0; i <  overlapping_triangles.size(); ++i )
   {
      const Vec3ui& tri = m_mesh.m_tris[overlapping_triangles[i]];
            
      if ( check_edge_triangle_intersection_by_index( new_edge[0], new_edge[1],
                                                      tri[0], tri[1], tri[2],
                                                      m_positions, m_verbose ) )
      {         
         return true;
      }                                              
   }
   
   return false;
   
}

// --------------------------------------------------------
///
/// Flip an edge: remove the edge and its incident triangles, then add a new edge and two new triangles
///
// --------------------------------------------------------

bool SurfTrack::flip_edge( unsigned int edge, 
                           unsigned int tri0, 
                           unsigned int tri1, 
                           unsigned int third_vertex_0, 
                           unsigned int third_vertex_1 )
{  
   
   Vec2ui& edge_vertices = m_mesh.m_edges[edge];
   
   // Find the vertices which will form the new edge
   Vec2ui new_edge( third_vertex_0, third_vertex_1);
   
   // --------------
   
   // Control volume change
   double vol = fabs( tetrahedron_signed_volume( m_positions[edge_vertices[0]], 
                                                 m_positions[edge_vertices[1]], 
                                                 m_positions[new_edge[0]], 
                                                 m_positions[new_edge[1]] ) ); 
   
   if ( vol > m_max_volume_change )
   {
      return false;
   }
   
   // --------------
   
   // Prevent non-manifold surfaces if we're not allowing topology changes
   if ( false == m_allow_topology_changes )
   {
      for ( unsigned int i = 0; i < m_mesh.m_vtxedge[ third_vertex_0 ].size(); ++i )
      {
         if ( ( m_mesh.m_edges[ m_mesh.m_vtxedge[third_vertex_0][i] ][0] == third_vertex_1 ) ||
              ( m_mesh.m_edges[ m_mesh.m_vtxedge[third_vertex_0][i] ][1] == third_vertex_1 ) )
         {
            // edge already exists
            return false;
         }
      }
   }
   
   // --------------
   
   // Don't flip edge on a degenerate tet
   if ( third_vertex_0 == third_vertex_1 )
   {
      return false;
   }
   
   // --------------
   
   // Create the new triangles
   // new edge winding order == winding order of old triangle0 == winding order of new triangle0
   
   unsigned int new_triangle_third_vertex_0, new_triangle_third_vertex_1;
   if ( m_mesh.oriented( m_mesh.m_edges[edge][0], m_mesh.m_edges[edge][1], m_mesh.m_tris[tri0] ) ) 
   {
		assert( m_mesh.oriented( m_mesh.m_edges[edge][1], m_mesh.m_edges[edge][0], m_mesh.m_tris[tri1] ) );
      new_triangle_third_vertex_0 = m_mesh.m_edges[edge][1];
      new_triangle_third_vertex_1 = m_mesh.m_edges[edge][0];
   }
   else
   {
		assert( m_mesh.oriented( m_mesh.m_edges[edge][0], m_mesh.m_edges[edge][1], m_mesh.m_tris[tri1] ) );
		assert( m_mesh.oriented( m_mesh.m_edges[edge][1], m_mesh.m_edges[edge][0], m_mesh.m_tris[tri0] ) );
      new_triangle_third_vertex_0 = m_mesh.m_edges[edge][0];
      new_triangle_third_vertex_1 = m_mesh.m_edges[edge][1];
   }
   
   Vec3ui new_triangle0( new_edge[0], new_edge[1], new_triangle_third_vertex_0 );
   Vec3ui new_triangle1( new_edge[1], new_edge[0], new_triangle_third_vertex_1 );
   
   if ( m_verbose )
   {
      std::cout << "flip --- new triangle 0: " << new_triangle0 << std::endl;
      std::cout << "flip --- new triangle 1: " << new_triangle1 << std::endl;
   }
   
   // --------------
   
   // if both triangle normals agree before flipping, make sure they agree after flipping
   if ( dot( get_triangle_normal(tri0), get_triangle_normal(tri1) ) > 0.0 ) 
   {
      if ( dot( get_triangle_normal(new_triangle0), get_triangle_normal(new_triangle1) ) < 0.0 )
      {
         return false;
      }
      
      if ( dot( get_triangle_normal(new_triangle0), get_triangle_normal(tri0) ) < 0.0 )
      {
         return false;
      }

      if ( dot( get_triangle_normal(new_triangle1), get_triangle_normal(tri1) ) < 0.0 )
      {
         return false;
      }

      if ( dot( get_triangle_normal(new_triangle0), get_triangle_normal(tri1) ) < 0.0 )
      {
         return false;
      }
      
      if ( dot( get_triangle_normal(new_triangle1), get_triangle_normal(tri0) ) < 0.0 )
      {
         return false;
      }
   }
   
   // --------------
   
   // Prevent intersection
   if ( m_collision_safety && flip_introduces_collision( edge, new_edge, new_triangle0, new_triangle1 ) )
   {
      return false;
   }
   
   // --------------
   
   // Prevent degenerate triangles
   if ( triangle_area( m_positions[new_triangle0[0]], m_positions[new_triangle0[1]], m_positions[new_triangle0[2]] ) < m_min_triangle_area )
   {
      return false;
   }
   
   if ( triangle_area( m_positions[new_triangle1[0]], m_positions[new_triangle1[1]], m_positions[new_triangle1[2]] ) < m_min_triangle_area )
   {
      return false;
   }
    

   // --------------
   
   // Control change in area
   
   float old_area = get_triangle_area( tri0 ) + get_triangle_area( tri1 );
   float new_area = triangle_area( m_positions[new_triangle0[0]], m_positions[new_triangle0[1]], m_positions[new_triangle0[2]] ) 
                  + triangle_area( m_positions[new_triangle1[0]], m_positions[new_triangle1[1]], m_positions[new_triangle1[2]] );
   
   if ( fabs( old_area - new_area ) > 0.1 * old_area )
   {
      return false;
   }
         
   // --------------
   
   // Don't flip unless both vertices are on a smooth patch
   if ( ( classify_vertex( edge_vertices[0] ) > 1 ) || ( classify_vertex( edge_vertices[1] ) > 1 ) )
   {
      return false;
   }        
   
   // --------------
   
   // Okay, now do the actual operation
   
   Vec3ui old_tri0 = m_mesh.m_tris[tri0];
   Vec3ui old_tri1 = m_mesh.m_tris[tri1];
   
   remove_triangle( tri0 );
   remove_triangle( tri1 );
   
   unsigned int new_triangle_index_0 = add_triangle( new_triangle0 );
   unsigned int new_triangle_index_1 = add_triangle( new_triangle1 );
   
   if ( m_collision_safety )
   {
      if ( check_triangle_vs_all_triangles_for_intersection( new_triangle_index_0 ) )
      {
         std::cout << "missed an intersection.  New triangles: " << new_triangle0 << ", " << new_triangle1 << std::endl;
         std::cout << "old triangles: " << old_tri0 << ", " << old_tri1 << std::endl;
      }
      
      if ( check_triangle_vs_all_triangles_for_intersection( new_triangle_index_1 ) )
      {
         std::cout << "missed an intersection.  New triangles: " << new_triangle0 << ", " << new_triangle1 << std::endl;
         std::cout << "old triangles: " << old_tri0 << ", " << old_tri1 << std::endl;      
      }
   }
   
   m_dirty_triangles.push_back( new_triangle_index_0 );
   m_dirty_triangles.push_back( new_triangle_index_1 );   
   
   if ( m_verbose ) { printf( "edge flip: ok\n" ); }
   
   return true;
   
}

// ========================================================
// Non-manifold cleanup functions
// ========================================================

// --------------------------------------------------------
///
/// Return the edge incident on two triangles.  Returns ~0 if triangles are not adjacent.
///
// --------------------------------------------------------

unsigned int SurfTrack::get_common_edge( unsigned int triangle_a, unsigned int triangle_b )
{
   const Vec3ui& triangle_a_edges = m_mesh.m_triedge[triangle_a];
   const Vec3ui& triangle_b_edges = m_mesh.m_triedge[triangle_b];
   
   for ( unsigned int i = 0; i < 3; ++i )
   {
      for ( unsigned int j = 0; j < 3; ++j )
      {
         if ( triangle_a_edges[i] == triangle_b_edges[j] )
         {
            return triangle_a_edges[i];
         }
      }      
   }
   
   return ~0;
}


// --------------------------------------------------------
///
/// Partition the triangles incident to a vertex into connected components
///
// --------------------------------------------------------

void SurfTrack::partition_vertex_neighbourhood( unsigned int vertex_index, std::vector< TriangleSet >& connected_components )
{
   // triangles incident to vertex
	TriangleSet triangles_incident_to_vertex = m_mesh.m_vtxtri[vertex_index];
	
   // unvisited triangles which are adjacent to some visited ones and incident to vt
   TriangleSet unvisited_triangles, visited_triangles;
   
   while ( triangles_incident_to_vertex.size() > 0 )
   {
      unvisited_triangles.clear();
      visited_triangles.clear();
      unvisited_triangles.push_back( triangles_incident_to_vertex.back() );
      
      while ( unvisited_triangles.size() > 0 )
      {
         // get an unvisited triangle
         unsigned int curr_tri = unvisited_triangles.back();
         unvisited_triangles.pop_back();
         
         // delete it from triangles_incident_to_vertex
         triangles_incident_to_vertex.erase( find(triangles_incident_to_vertex.begin(), triangles_incident_to_vertex.end(), curr_tri) );
         
         // put it on closed
         visited_triangles.push_back(curr_tri);
         
         // get find a triangle which is incident to vertex and adjacent to curr_tri
         for ( unsigned int i = 0; i < triangles_incident_to_vertex.size(); ++i )
         {
            unsigned int incident_triangle_index =  triangles_incident_to_vertex[i];
            
            if ( curr_tri == incident_triangle_index )
            {
               continue;
            }
            
            if ( triangles_are_adjacent( curr_tri, incident_triangle_index ) )
            {
               // if not in visited_triangles or unvisited_triangles, put them on unvisited_triangles
               if ( ( find(unvisited_triangles.begin(), unvisited_triangles.end(), incident_triangle_index) == unvisited_triangles.end() ) &&
                    ( find(visited_triangles.begin(), visited_triangles.end(), incident_triangle_index) == visited_triangles.end() ) ) 
               {
                  unvisited_triangles.push_back( incident_triangle_index );
               }
            }
         }
      }
      
      // one connected component = visited triangles
      connected_components.push_back(visited_triangles);
   }   
}

// --------------------------------------------------------
///
/// Duplicate a vertex and move the two copies away from each other slightly
///
// --------------------------------------------------------

bool SurfTrack::pull_apart_vertex( unsigned int vertex_index, const std::vector< TriangleSet >& connected_components )
{
   double dx = 10.0 * m_proximity_epsilon;
   
   TriangleSet triangles_to_delete;
   std::vector< Vec3ui > triangles_to_add;
   std::vector< unsigned int > vertices_added;
   
   // for each connected component except the last one, create a duplicate vertex
   for (unsigned short i = 0; i < connected_components.size() - 1; ++i)
   {
      // duplicate the vertex 
      unsigned int duplicate_vertex_index = add_vertex( m_positions[vertex_index], 
                                                        m_velocities[vertex_index],
                                                        m_masses[vertex_index] );
      
      vertices_added.push_back( duplicate_vertex_index );
      
      Vec3d centroid( 0.0, 0.0, 0.0 );
      
      // map component triangles to the duplicate vertex
      for ( unsigned int t = 0; t < connected_components[i].size(); ++t ) 
      {
         // create a new triangle with 2 vertices the same, and one vertex set to the new duplicate vertex
         Vec3ui new_triangle = m_mesh.m_tris[ connected_components[i][t] ]; 
         
         for ( unsigned short v = 0; v < 3; ++v ) 
         {
            if ( new_triangle[v] == vertex_index )
            {
               new_triangle[v] = duplicate_vertex_index;
            }
            else
            {         
               centroid += m_positions[ new_triangle[v] ];
            }
         }
         
         triangles_to_add.push_back( new_triangle );
         triangles_to_delete.push_back( connected_components[i][t] ); 
      }
      
      // compute the centroid    
      centroid /= ( connected_components[i].size() * 2 );
      
      // move the duplicate vertex towards the centroid
      m_positions[duplicate_vertex_index] = (1.0 - dx) * m_positions[duplicate_vertex_index] + dx * centroid;
      
   }
   
   if ( m_collision_safety )
   {
      // check new triangles for collision safety
      for ( unsigned int i = 0; i < triangles_to_add.size(); ++i ) 
      {
         const Vec3ui& current_triangle = triangles_to_add[i];
         Vec3d low, high;
         
         minmax(m_positions[current_triangle[0]], m_positions[current_triangle[1]], m_positions[current_triangle[2]], low, high );
         
         std::vector<unsigned int> overlapping_triangles;
         m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
         
         for ( unsigned int j=0; j < overlapping_triangles.size(); ++j )
         {        
            const Vec3ui& tri_j = m_mesh.m_tris[overlapping_triangles[j]];
            
            assert( tri_j[0] != tri_j[1] );
            
            if ( check_triangle_triangle_intersection( current_triangle, tri_j, m_positions ) )
            {
               // collision occurs - abort separation
               return false;
            }
         }
      }
      
      // check new triangles vs each other as well
      for ( unsigned int i = 0; i < triangles_to_add.size(); ++i ) 
      {
         for ( unsigned int j = i+1; j < triangles_to_add.size(); ++j ) 
         {
            if ( check_triangle_triangle_intersection( triangles_to_add[i], triangles_to_add[j], m_positions ) )
            {
               // collision occurs - abort separation
               return false;
            }         
         }
      }
   }
   
   for ( unsigned int i = 0; i < triangles_to_add.size(); ++i )
   {
      add_triangle( triangles_to_add[i] );
   }
   
   for ( unsigned int i = 0; i < triangles_to_delete.size(); ++i )
   {
      remove_triangle( triangles_to_delete[i] );
   }
   
   if ( m_verbose ) { printf( "pulled apart a vertex\n" ); }
   
   return true;
}


// --------------------------------------------------------
///
/// Find vertices with disconnected neighbourhoods, and pull them apart
///
// --------------------------------------------------------

void SurfTrack::separate_singular_vertices()
{
   for ( unsigned int i = 0; i < m_positions.size(); ++i )
   {
      // Partition the set of triangles adjacent to this vertex into connected components
      std::vector< TriangleSet > connected_components;
      partition_vertex_neighbourhood( i, connected_components );
      
      if ( connected_components.size() > 1 ) 
      {
         pull_apart_vertex( i, connected_components );
      }
   }
}


// --------------------------------------------------------
///
/// Fire an assert if any triangle has repeated vertices or if any zero-volume tets are found.
///
// --------------------------------------------------------

void SurfTrack::assert_no_degenerate_triangles( )
{

   // for each triangle on the surface
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {

      const Vec3ui& current_triangle = m_mesh.m_tris[i];
      
      if ( (current_triangle[0] == 0) && (current_triangle[1] == 0) && (current_triangle[2] == 0) ) 
      {
         // deleted triangle
         continue;
      }
      
      //
      // check if triangle has repeated vertices
      //
      
      assert ( !( (current_triangle[0] == current_triangle[1]) || 
                       (current_triangle[1] == current_triangle[2]) || 
                       (current_triangle[2] == current_triangle[0]) ) );
    
      //
      // look for flaps
      //
      const Vec3ui& tri_edges = m_mesh.m_triedge[i];
      
      bool flap_found = false;
      
      for ( unsigned int e = 0; e < 3 && flap_found == false; ++e )
      {
         const std::vector<unsigned int>& edge_tris = m_mesh.m_edgetri[ tri_edges[e] ];
         
         for ( unsigned int t = 0; t < edge_tris.size(); ++t )
         {
            if ( edge_tris[t] == i )
            {
               continue;
            }
            
            unsigned int other_triangle_index = edge_tris[t];
            const Vec3ui other_triangle = m_mesh.m_tris[ other_triangle_index ];
            
            if ( (other_triangle[0] == other_triangle[1]) || 
                 (other_triangle[1] == other_triangle[2]) || 
                 (other_triangle[2] == other_triangle[0]) ) 
            {
               continue;
            }
            
            if ( ((current_triangle[0] == other_triangle[0]) || (current_triangle[0] == other_triangle[1]) || (current_triangle[0] == other_triangle[2])) &&
                 ((current_triangle[1] == other_triangle[0]) || (current_triangle[1] == other_triangle[1]) || (current_triangle[1] == other_triangle[2])) &&
                 ((current_triangle[2] == other_triangle[0]) || (current_triangle[2] == other_triangle[1]) || (current_triangle[2] == other_triangle[2])) ) 
            {
               
               unsigned int common_edge = tri_edges[e];
               if ( m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], current_triangle ) == 
                    m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], other_triangle ) )
               { 
                  continue;
               }
               
               assert( false );
            }
         }         
      }
      
   }
      
}


// --------------------------------------------------------
///
/// Delete flaps and zero-area triangles.  Then separate singular vertices.
///
// --------------------------------------------------------

void SurfTrack::trim_non_manifold( const std::vector<unsigned int>& triangle_indices )
{   
   
   bool changed = false;
        
   for ( unsigned int j = 0; j < triangle_indices.size(); ++j )      
   {
      unsigned int i = triangle_indices[j];
      
      const Vec3ui& current_triangle = m_mesh.m_tris[i];
      
      if ( (current_triangle[0] == 0) && (current_triangle[1] == 0) && (current_triangle[2] == 0) ) 
      {
         continue;
      }
      
      //
      // look for triangles with repeated vertices
      //
      if (    (current_triangle[0] == current_triangle[1])
           || (current_triangle[1] == current_triangle[2]) 
           || (current_triangle[2] == current_triangle[0]) )
      {     
         if ( m_verbose ) { printf( "deleting degenerate triangle %d: %d %d %d\n", i, current_triangle[0], current_triangle[1], current_triangle[2] ); }
         
         // delete it
         remove_triangle( i );
         
         changed = true;         
         continue;
      }
            
      
      //
      // look for flaps
      //
      const Vec3ui& tri_edges = m_mesh.m_triedge[i];
      
      bool flap_found = false;
      
      for ( unsigned int e = 0; e < 3 && flap_found == false; ++e )
      {
         const std::vector<unsigned int>& edge_tris = m_mesh.m_edgetri[ tri_edges[e] ];
         
         for ( unsigned int t = 0; t < edge_tris.size(); ++t )
         {
            if ( edge_tris[t] == i )
            {
               continue;
            }
            
            unsigned int other_triangle_index = edge_tris[t];
            const Vec3ui other_triangle = m_mesh.m_tris[ other_triangle_index ];
             
            if (    (other_triangle[0] == other_triangle[1]) 
                 || (other_triangle[1] == other_triangle[2]) 
                 || (other_triangle[2] == other_triangle[0]) ) 
            {
               continue;
            }
            
            if ( ((current_triangle[0] == other_triangle[0]) || (current_triangle[0] == other_triangle[1]) || (current_triangle[0] == other_triangle[2])) &&
                 ((current_triangle[1] == other_triangle[0]) || (current_triangle[1] == other_triangle[1]) || (current_triangle[1] == other_triangle[2])) &&
                 ((current_triangle[2] == other_triangle[0]) || (current_triangle[2] == other_triangle[1]) || (current_triangle[2] == other_triangle[2])) ) 
            {
               
               if ( false == m_allow_topology_changes )
               {
                  std::cout << current_triangle << std::endl;
                  std::cout << other_triangle << std::endl;
                  assert(0);
               }
               
               unsigned int common_edge = tri_edges[e];
               if ( m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], current_triangle ) == 
                    m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], other_triangle ) )
               {
                  continue;
               }
               
               // the dangling vertex will be safely removed by the vertex cleanup function
               
               // delete the triangle
               
               if ( m_verbose )
               {
                  printf( "flap: triangles %d [%d %d %d] and %d [%d %d %d]\n",
                          i, current_triangle[0], current_triangle[1], current_triangle[2],
                          edge_tris[t], other_triangle[0], other_triangle[1], other_triangle[2] );
               }
               
               remove_triangle( i );
               
               // delete its opposite
               
               remove_triangle( other_triangle_index );
                              
               changed = true;
               flap_found = true;
               break;
            }
            
         }
         
      }
         
   }
      
   if ( m_allow_topology_changes )
   {
      separate_singular_vertices();
   }
   
}


// ========================================================
//  NULL-space smoothing functions
// ========================================================

// --------------------------------------------------------
///
/// Find a new vertex location using NULL-space smoothing
///
// --------------------------------------------------------

void SurfTrack::null_space_smooth_vertex( unsigned int v, 
                                  const std::vector<double>& triangle_areas, 
                                  const std::vector<Vec3d>& triangle_normals, 
                                  const std::vector<Vec3d>& triangle_centroids, 
                                  Vec3d& displacement ) const
{
   
   if ( m_mesh.m_vtxtri[v].empty() )     
   { 
      displacement = Vec3d(0,0,0);
      return; 
   }
   
   const std::vector<unsigned int>& edges = m_mesh.m_vtxedge[v];
   for ( unsigned int j = 0; j < edges.size(); ++j )
   {
      if ( m_mesh.m_edgetri[ edges[j] ].size() == 1 )
      {
         displacement = Vec3d(0,0,0);
         return;
      }
   }
   
   const std::vector<unsigned int>& incident_triangles = m_mesh.m_vtxtri[v];
   
   std::vector< Vec3d > N;
   std::vector< double > W;
   
   for ( unsigned int i = 0; i < incident_triangles.size(); ++i )
   {
      unsigned int triangle_index = incident_triangles[i];
      N.push_back( triangle_normals[triangle_index] );
      W.push_back( triangle_areas[triangle_index] );
   }
   
   Mat33d A(0,0,0,0,0,0,0,0,0);
   
   // Ax = b from N^TWni = N^TWd
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
      printf( "incident_triangles: %d\n", (int)incident_triangles.size() );
      for ( unsigned int i = 0; i < incident_triangles.size(); ++i )
      {
         unsigned int triangle_index = incident_triangles[i];
         std::cout << "triangle: " << m_mesh.m_tris[triangle_index] << std::endl;
         std::cout << "normal: " << triangle_normals[triangle_index] << std::endl;
         std::cout << "area: " << triangle_areas[triangle_index] << std::endl;
      }
      
      assert(0);
   }
   
   // compute basis for null space
   std::vector<Vec3d> T;
   for ( unsigned int i = 0; i < 3; ++i )
   {
      if ( eigenvalues[i] < G_EIGENVALUE_RANK_RATIO * eigenvalues[2] )
      {
         T.push_back( Vec3d( A(0,i), A(1,i), A(2,i) ) );
      }
   }
   
   Mat33d null_space_projection(0,0,0,0,0,0,0,0,0);
   for ( unsigned int row = 0; row < 3; ++row )
   {
      for ( unsigned int col = 0; col < 3; ++col )
      {
         for ( unsigned int i = 0; i < T.size(); ++i )
         {
            null_space_projection(row, col) += T[i][row] * T[i][col];
         }
      }  
   }
   
   Vec3d t(0,0,0);      // displacement
   double sum_areas = 0;
   
   for ( unsigned int i = 0; i < incident_triangles.size(); ++i )
   {
      double area = triangle_areas[incident_triangles[i]];
      sum_areas += area;
      Vec3d c = triangle_centroids[incident_triangles[i]] - m_positions[v];
      t += area * c;
   }
   
   t = null_space_projection * t;
   t /= sum_areas;
   
   displacement = t;
}


// ========================================================
//  Zippering functions
// ========================================================

// --------------------------------------------------------
///
/// Move vertices around so v[0] and v[4] are closest together
///
// --------------------------------------------------------

void SurfTrack::twist_vertices( unsigned int *zipper_vertices )
{
   double min_dist = 1e+30, dist;
   Vec2ui min_pair(~0, ~0);
   
   // find the closest pair among the 8 vertices
   for (int i=0; i<4; ++i) 
   {
      for (int j=4; j<8; ++j) 
      {
         dist = mag( m_positions[zipper_vertices[i]] - m_positions[zipper_vertices[j]] );
         if (dist < min_dist) 
         {
            min_dist = dist;
            min_pair[0] = i;
            min_pair[1] = j;
         }
      }
   }
   
   unsigned int new_vertices[8];
   for (int i=0; i<4; ++i) 
   {
      new_vertices[i]   = zipper_vertices[(min_pair[0] + i) % 4];
      new_vertices[i+4] = zipper_vertices[(min_pair[1] + i - 4) % 4 + 4];
   }
   
   memcpy( zipper_vertices, new_vertices, 8 * sizeof(unsigned int) );
   
}

// --------------------------------------------------------
///
/// Create a set of triangles to add to perform the zippering operation
///
// --------------------------------------------------------

bool SurfTrack::get_zipper_triangles( unsigned int edge_index_a, unsigned int edge_index_b, std::vector<Vec3ui>& output_triangles )
{
   assert( output_triangles.size() == 8 );
   
   const Vec2ui& edge_a = m_mesh.m_edges[edge_index_a];
   const Vec2ui& edge_b = m_mesh.m_edges[edge_index_b];
   
   unsigned int zipper_vertices[8];
   
   zipper_vertices[0] = edge_a[0];
   zipper_vertices[2] = edge_a[1];
   zipper_vertices[4] = edge_b[0];
   zipper_vertices[6] = edge_b[1];
   
   const std::vector<unsigned int>& incident_triangles_a = m_mesh.m_edgetri[edge_index_a];
   
   assert( incident_triangles_a.size() == 2 );       // should be checked before calling this function
   
   unsigned int third_vertices[2];
   third_vertices[0] = m_mesh.get_third_vertex( zipper_vertices[0], zipper_vertices[2], m_mesh.m_tris[incident_triangles_a[0]] );
   third_vertices[1] = m_mesh.get_third_vertex( zipper_vertices[0], zipper_vertices[2], m_mesh.m_tris[incident_triangles_a[1]] );
   
   if ( m_mesh.oriented(zipper_vertices[0], zipper_vertices[2], m_mesh.m_tris[incident_triangles_a[0]] ) ) 
   {
      zipper_vertices[1] = third_vertices[0];
      zipper_vertices[3] = third_vertices[1];
   } 
   else if ( m_mesh.oriented(zipper_vertices[0], zipper_vertices[2], m_mesh.m_tris[incident_triangles_a[1]]) ) 
   {
      zipper_vertices[3] = third_vertices[0];
      zipper_vertices[1] = third_vertices[1];
   } 
   else 
   {
      // Should not happen
      std::cout << "Orientation check failed" << std::endl;
      assert( false );
   }
   
   const std::vector<unsigned int>& incident_triangles_b = m_mesh.m_edgetri[edge_index_b];
   
   assert( incident_triangles_b.size() == 2 );       // should be checked before calling this function
   
   assert( edge_index_b < m_mesh.m_edges.size() );
          
   const Vec2ui& ce = m_mesh.m_edges[edge_index_b];
   const std::vector<unsigned int>& et = m_mesh.m_edgetri[edge_index_b];
   third_vertices[0] = m_mesh.get_third_vertex( ce[0], ce[1], m_mesh.m_tris[et[0]] );
   
   third_vertices[0] = m_mesh.get_third_vertex( zipper_vertices[4], zipper_vertices[6], m_mesh.m_tris[incident_triangles_b[0]] );
   third_vertices[1] = m_mesh.get_third_vertex( zipper_vertices[4], zipper_vertices[6], m_mesh.m_tris[incident_triangles_b[1]] );   
   
   if ( m_mesh.oriented(zipper_vertices[4], zipper_vertices[6], m_mesh.m_tris[incident_triangles_b[0]]) ) 
   {
      zipper_vertices[5] = third_vertices[0];
      zipper_vertices[7] = third_vertices[1];
   } 
   else if ( m_mesh.oriented(zipper_vertices[4], zipper_vertices[6], m_mesh.m_tris[incident_triangles_b[1]]) ) 
   {
      zipper_vertices[7] = third_vertices[0];
      zipper_vertices[5] = third_vertices[1];
   } 
   else 
   {
      // Should not happen
      std::cout << "Orientation check failed" << std::endl;
      assert( false );
   }
   
   // Check for degenerate case
   for ( unsigned int i = 0; i < 8; ++i) 
   {
      for ( unsigned int j = i+1; j < 8; ++j) 
      {
         
         if ( zipper_vertices[i] == zipper_vertices[j] )         // vertices not distinct
         {
            return false;
         }
         
         // Check if an edge already exists between two vertices in opposite edge neighbourhoods
         // (i.e. look for an edge which would be created by zippering)
         
         if ( (i < 4) && (j > 3) )
         {
            
            for ( unsigned int ii = 0; ii < m_mesh.m_vtxedge[ zipper_vertices[i] ].size(); ++ii )
            {
               for ( unsigned int jj = 0; jj < m_mesh.m_vtxedge[ zipper_vertices[j] ].size(); ++jj )
               {
                  if ( m_mesh.m_vtxedge[ zipper_vertices[i] ][ii] == m_mesh.m_vtxedge[ zipper_vertices[j] ][jj] )
                  {
                     return false;
                  }
               }
            }
         }
         
      }
   }
   
   // Twist so that vertices 0 and 4 are the pair closest together
   twist_vertices( zipper_vertices );
   
   // now we can use a closed formula to construct zippering triangles

   output_triangles[0] = Vec3ui( zipper_vertices[0], zipper_vertices[4], zipper_vertices[1] );  // a e b
   output_triangles[1] = Vec3ui( zipper_vertices[1], zipper_vertices[4], zipper_vertices[7] );  // b e h
   output_triangles[2] = Vec3ui( zipper_vertices[1], zipper_vertices[7], zipper_vertices[2] );  // b h c
   output_triangles[3] = Vec3ui( zipper_vertices[2], zipper_vertices[7], zipper_vertices[6] );  // c h g
   output_triangles[4] = Vec3ui( zipper_vertices[2], zipper_vertices[6], zipper_vertices[3] );  // c g d
   output_triangles[5] = Vec3ui( zipper_vertices[3], zipper_vertices[6], zipper_vertices[5] );  // d g f
   output_triangles[6] = Vec3ui( zipper_vertices[3], zipper_vertices[5], zipper_vertices[0] );  // d f a
   output_triangles[7] = Vec3ui( zipper_vertices[0], zipper_vertices[5], zipper_vertices[4] );  // a f e
   
   return true;
}


// --------------------------------------------------------
///
/// Check whether the introduction of the new zippering triangles causes a collision 
///
// --------------------------------------------------------

bool SurfTrack::zippering_introduces_collision( const std::vector<Vec3ui>& new_triangles, 
                                                const std::vector<unsigned int>& deleted_triangles )
{
   for ( unsigned int i = 0; i < new_triangles.size(); ++i )
   {
      // Check all existing edges vs new triangles
      Vec3d low, high;
      minmax(m_positions[new_triangles[i][0]], m_positions[new_triangles[i][1]], m_positions[new_triangles[i][2]], low, high);
      
      std::vector<unsigned int> overlapping_triangles;
      m_broad_phase->get_potential_triangle_collisions( low, high, overlapping_triangles );
      
      const Vec3ui& current_triangle = new_triangles[i];
      
      // Check to make sure there doesn't already exist triangles with the same vertices
      for ( unsigned int t = 0; t < overlapping_triangles.size(); ++t )      
      {
         const Vec3ui& other_triangle = m_mesh.m_tris[overlapping_triangles[t]];
         
         if (    ((current_triangle[0] == other_triangle[0]) || (current_triangle[0] == other_triangle[1]) || (current_triangle[0] == other_triangle[2]))
				  && ((current_triangle[1] == other_triangle[0]) || (current_triangle[1] == other_triangle[1]) || (current_triangle[1] == other_triangle[2]))
				  && ((current_triangle[2] == other_triangle[0]) || (current_triangle[2] == other_triangle[1]) || (current_triangle[2] == other_triangle[2])) ) 
         {
            return true;
         }
      }
      
      // Check all existing triangles vs new triangles
      for ( unsigned int t = 0; t < overlapping_triangles.size(); ++t )      
      {
         bool go_to_next_triangle = false;
         for ( unsigned int d = 0; d < deleted_triangles.size(); ++d )
         {
            if ( overlapping_triangles[t] == deleted_triangles[d] )
            {
               go_to_next_triangle = true;
               break;
            }
         }
         if ( go_to_next_triangle )   
         { 
            continue; 
         }
              
         if ( check_triangle_triangle_intersection( new_triangles[i], 
                                                    m_mesh.m_tris[overlapping_triangles[t]], 
                                                    m_positions ) )
         {
            return true;
         }     
      }
      
      // Check new triangles vs each other
      for ( unsigned int j = 0; j < new_triangles.size(); ++j )
      {
         if ( i == j )  { continue; }
         
         if ( check_triangle_triangle_intersection( new_triangles[i], 
                                                    new_triangles[j], 
                                                    m_positions ) )
         {
            return true;
         }
      }      
   }
   
   // For real collision safety, we need to check for vertices inside the new, joined volume.  
   // Checking edges vs triangles is technically not enough.
   
   return false;
}



unsigned int g_zipper_non_manifold_edges;
unsigned int g_zipper_mass_match;
unsigned int g_zipper_no_set_triangles;
unsigned int g_zipper_collision;

// --------------------------------------------------------
///
/// Attempt to merge between two edges
///
// --------------------------------------------------------

bool SurfTrack::zipper_edges( unsigned int edge_index_a, unsigned int edge_index_b )
{
   // For now we'll only zipper edges which are incident on 2 triangles
   if ( m_mesh.m_edgetri[edge_index_a].size() != 2 || m_mesh.m_edgetri[edge_index_b].size() != 2 )
   {
      if ( m_verbose ) { std::cout << "ZIPPER: edge non-manifold" << std::endl; }
      ++g_zipper_non_manifold_edges;
      return false;
   }
   
   if (    ( m_masses[m_mesh.m_edges[edge_index_a][0]] != m_masses[m_mesh.m_edges[edge_index_a][1]] )
        || ( m_masses[m_mesh.m_edges[edge_index_b][0]] != m_masses[m_mesh.m_edges[edge_index_b][1]] ) )
   {
      ++g_zipper_mass_match;
      return false;
   }
   
   if ( m_masses[ m_mesh.m_edges[edge_index_a][0] ] != m_masses[ m_mesh.m_edges[edge_index_b][0] ] )
   { 
      if ( m_verbose ) { std::cout << "ZIPPER: edge m_masses don't match" << std::endl;  }
      ++g_zipper_mass_match;
      return false;
   }
   
   //
   // Get the set of 8 new triangles which will join the two holes in the mesh
   //
   
   std::vector<Vec3ui> new_triangles;
   new_triangles.resize(8);
   if ( false == get_zipper_triangles( edge_index_a, edge_index_b, new_triangles ) )
   {
      if ( m_verbose ) { std::cout << "ZIPPER: couldn't get a set of triangles" << std::endl;   }
      ++g_zipper_no_set_triangles;
      return false;
   }
   
   // Keep a list of triangles to delete
   std::vector<unsigned int> deleted_triangles;
   deleted_triangles.push_back( m_mesh.m_edgetri[edge_index_a][0] );
   deleted_triangles.push_back( m_mesh.m_edgetri[edge_index_a][1] );
   deleted_triangles.push_back( m_mesh.m_edgetri[edge_index_b][0] );
   deleted_triangles.push_back( m_mesh.m_edgetri[edge_index_b][1] );   
   
   //
   // Check the new triangles for collision safety, ignoring the triangles which will be deleted
   //
   
   bool saved_verbose = m_verbose;
   m_verbose = false;

   if ( m_collision_safety && zippering_introduces_collision( new_triangles, deleted_triangles ) )
   {
      m_verbose = saved_verbose;
      if ( m_verbose ) { std::cout << "ZIPPER: collision check failed" << std::endl; }
      ++g_zipper_collision;
      return false;
   }
  
   m_verbose = saved_verbose;
   
   //
   // Add the new triangles
   //
   
   unsigned int new_index = add_triangle( new_triangles[0] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[1] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[2] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[3] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[4] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[5] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[6] );
   m_dirty_triangles.push_back( new_index );
   new_index = add_triangle( new_triangles[7] );
   m_dirty_triangles.push_back( new_index );
   
   //
   // Remove the old triangles
   //
   
   remove_triangle( m_mesh.m_edgetri[edge_index_a][0] );
   remove_triangle( m_mesh.m_edgetri[edge_index_a][0] );
   remove_triangle( m_mesh.m_edgetri[edge_index_b][0] );
   remove_triangle( m_mesh.m_edgetri[edge_index_b][0] );
   
   return true;
   
}



// ========================================================
//  Improvement passes
// ========================================================

// --------------------------------------------------------
///
/// Split all long edges
///
// --------------------------------------------------------

bool SurfTrack::split_pass( )
{
	std::cout << "---------------------- El Topo: splitting ----------------------" << std::endl;
      
   // whether a split operation was successful in this pass
   bool split_occurred = false;
   
   std::vector<SortableEdge> sortable_edges_to_try;
   
   for( unsigned int i = 0; i < m_mesh.m_edges.size(); i++ )
   {    
      if ( m_mesh.m_edges[i][0] == m_mesh.m_edges[i][1] )   { continue; }     // skip deleted edges
      if ( m_mesh.m_edgetri[i].size() < 2 ) { continue; }                     // skip boundary edges
      if ( m_masses[ m_mesh.m_edges[i][0] ] > 100.0 && m_masses[ m_mesh.m_edges[i][1] ] > 100.0 )     { continue; }    // skip solids
      
      unsigned int vertex_a = m_mesh.m_edges[i][0];
      unsigned int vertex_b = m_mesh.m_edges[i][1];
      
      assert( vertex_a < m_positions.size() );
      assert( vertex_b < m_positions.size() );
      
      double current_length = dist(  m_positions[ vertex_a ], m_positions[ vertex_b ] );
      
      if ( current_length > m_max_edge_length )
      {
         sortable_edges_to_try.push_back( SortableEdge( i, current_length ) );
      }
   }
   
   
   //
   // sort in ascending order, then iterate backwards
   //
   
   std::sort( sortable_edges_to_try.begin(), sortable_edges_to_try.end() );

   std::vector<SortableEdge>::reverse_iterator iter = sortable_edges_to_try.rbegin();
   for ( ; iter != sortable_edges_to_try.rend(); ++iter )
   {
      
      unsigned int longest_edge = iter->edge_index;
      
      // recompute edge length -- a prior split may have fixed this edge already
      double longest_edge_length = get_edge_length( longest_edge );  
      
      if ( longest_edge_length > m_max_edge_length )
      {
         
         if ( m_verbose ) 
         {
            printf( "splitting edge %d / %d, length = %f\n", longest_edge, (int)m_mesh.m_edges.size(), longest_edge_length );
            printf( "edge %d %d... ", m_mesh.m_edges[longest_edge][0], m_mesh.m_edges[longest_edge][1] );
         }
         
         // skip non-manifold and deleted edges
         if ( ( m_mesh.m_edgetri[longest_edge].size() != 2 ) || ( m_mesh.m_edges[longest_edge][0] == m_mesh.m_edges[longest_edge][1] ) )
         { 
            continue;      
         }    
         
         bool result = split_edge( longest_edge );
         
         if ( m_verbose ) { printf( " result: %s\n", (result ? "ok" : "failed")); }
         
         split_occurred |= result;
         
      }
   }

   return split_occurred;
     
}

// --------------------------------------------------------
///
/// Collapse all short edges
///
// --------------------------------------------------------

bool SurfTrack::collapse_pass()
{
   std::cout << "---------------------- El Topo: collapsing ----------------------" << std::endl;
   
   bool collapse_occurred = false;
      
   // set of triangles to test for degeneracy
   m_dirty_triangles.clear();       
   
   std::vector<SortableEdge> sortable_edges_to_try;
   
   //
   // get set of edges to collapse
   //
   
   for( unsigned int i = 0; i < m_mesh.m_edges.size(); i++ )
   {    
      if ( m_mesh.m_edges[i][0] == m_mesh.m_edges[i][1] )   { continue; }    // skip deleted edges
      if ( m_masses[ m_mesh.m_edges[i][0] ] > 100.0 || m_masses[ m_mesh.m_edges[i][1] ] > 100.0 )     { continue; }    // skip solids
            
      double current_length = get_edge_length( i );
      
      if ( current_length < m_min_edge_length )
      {
         sortable_edges_to_try.push_back( SortableEdge( i, current_length ) );
      }
   }
   
   //
   // sort in ascending order by length (collapse shortest edges first)
   //
   
   std::sort( sortable_edges_to_try.begin(), sortable_edges_to_try.end() );
   
   if ( m_verbose )
   {
      std::cout << sortable_edges_to_try.size() << " candidate edges sorted" << std::endl;
      std::cout << "total edges: " << m_mesh.m_edges.size() << std::endl;
   }

   //
   // attempt to collapse each edge in the sorted list
   //
   
   for ( unsigned int i = 0; i < sortable_edges_to_try.size(); ++i )
   {
      unsigned int e = sortable_edges_to_try[i].edge_index;
      double edge_length = get_edge_length( e );
      
      if ( edge_length < m_min_edge_length )
      {        
         if ( m_verbose )
         {
            printf( "collapsing edge %d / %d, length = %f\n", e, (int)m_mesh.m_edges.size(), edge_length );
            //printf( "edge %d %d... ", m_mesh.m_edges[e][0], m_mesh.m_edges[e][1] );
         }
         
         if ( m_mesh.m_edges[e][0] == m_mesh.m_edges[e][1] )   { continue; }     // skip deleted edges         
         if ( m_mesh.m_edgetri[e].size() < 2 )  { continue; }  // skip boundary edges
         
         bool result = collapse_edge( e );
                  
         if ( m_verbose )
         {
            printf( " result: %s\n", (result ? "ok" : "failed"));
         }
         
         collapse_occurred |= result;
         
      }
   }

   trim_non_manifold( m_dirty_triangles );

   m_dirty_triangles.clear();
   
   return collapse_occurred;
   
}


// --------------------------------------------------------
///
/// Flip all non-delaunay edges
///
// --------------------------------------------------------

bool SurfTrack::flip_pass( )
{
   std::cout << "---------------------- El Topo: flipping ----------------------" << std::endl;
	
   m_dirty_triangles.clear();

   bool flip_occurred_ever = false;          // A flip occurred in this function call
   bool flip_occurred = true;                // A flip occurred in the current loop iteration
   
   static unsigned int MAX_NUM_FLIP_PASSES = 5;
   unsigned int num_flip_passes = 0;
   
   //
   // Each "pass" is once over the entire set of edges (ignoring edges created during the current pass)
   //
   
   while ( flip_occurred && num_flip_passes++ < MAX_NUM_FLIP_PASSES )
   {
      std::cout << "---------------------- El Topo: flipping ";
      std::cout << "pass " << num_flip_passes << "/" << MAX_NUM_FLIP_PASSES;
      std::cout << "----------------------" << std::endl;
      
      flip_occurred = false;
      
      unsigned int number_of_edges = m_mesh.m_edges.size();      // don't work on newly created edges
       
      for( unsigned int i = 0; i < number_of_edges; i++ )
      {
         if ( m_mesh.m_edges[i][0] == m_mesh.m_edges[i][1] )   { continue; }
         if ( m_mesh.m_edgetri[i].size() > 4 || m_mesh.m_edgetri[i].size() < 2 )   { continue; }
         
         unsigned int triangle_a = ~0, triangle_b = ~0;
                  
         if ( m_mesh.m_edgetri[i].size() == 2 )
         {    
            triangle_a = m_mesh.m_edgetri[i][0];
            triangle_b = m_mesh.m_edgetri[i][1];         
            assert (    m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_a] ) 
                     != m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_b] ) );
         }
         else if ( m_mesh.m_edgetri[i].size() == 4 )
         {           
            triangle_a = m_mesh.m_edgetri[i][0];
            
            // Find first triangle with orientation opposite triangle_a's orientation
            unsigned int j = 1;
            for ( ; j < 4; ++j )
            {
               triangle_b = m_mesh.m_edgetri[i][j];
               if (    m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_a] ) 
                    != m_mesh.oriented( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_b] ) )
               {
                  break;
               }
            }
            assert ( j < 4 );
         }
         else
         {
            printf( "%d triangles incident to an edge\n", (int)m_mesh.m_edgetri[i].size() );
            assert(0);
         }
         
         // Don't flip edge on a degenerate triangle
         if (   m_mesh.m_tris[triangle_a][0] == m_mesh.m_tris[triangle_a][1] 
             || m_mesh.m_tris[triangle_a][1] == m_mesh.m_tris[triangle_a][2] 
             || m_mesh.m_tris[triangle_a][2] == m_mesh.m_tris[triangle_a][0] 
             || m_mesh.m_tris[triangle_b][0] == m_mesh.m_tris[triangle_b][1] 
             || m_mesh.m_tris[triangle_b][1] == m_mesh.m_tris[triangle_b][2] 
             || m_mesh.m_tris[triangle_b][2] == m_mesh.m_tris[triangle_b][0] )
         {
            continue;
         }
         
         unsigned int third_vertex_0 = m_mesh.get_third_vertex( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_a] );
         unsigned int third_vertex_1 = m_mesh.get_third_vertex( m_mesh.m_edges[i][0], m_mesh.m_edges[i][1], m_mesh.m_tris[triangle_b] );
         
         if ( third_vertex_0 == third_vertex_1 )
         {
            continue;
         }
         
         bool flipped = false;
         
         double current_length = mag( m_positions[m_mesh.m_edges[i][1]] - m_positions[m_mesh.m_edges[i][0]] );        
         double potential_length = mag( m_positions[third_vertex_1] - m_positions[third_vertex_0] );     
         if ( potential_length < current_length - m_edge_flip_min_length_change )
         {
            flipped = flip_edge( i, triangle_a, triangle_b, third_vertex_0, third_vertex_1 );            
         }
            
         flip_occurred |= flipped;
      }
      
      flip_occurred_ever |= flip_occurred;
   }
   
   
   if ( flip_occurred_ever )
   {
      trim_non_manifold( m_dirty_triangles );
      m_dirty_triangles.clear();
   }
   
   return flip_occurred_ever;
   
}


// --------------------------------------------------------
///
/// NULL-space smoothing
///
// --------------------------------------------------------

bool SurfTrack::null_space_smoothing_pass( double dt )
{
   std::cout << "---------------------- El Topo: vertex redistribution ----------------------" << std::endl;
      
   std::vector<Vec3d> saved_velocities;
   for ( unsigned int i = 0; i < m_velocities.size(); ++i )
   {
      saved_velocities.push_back( m_velocities[i] );
   }
   
   std::vector<double> triangle_areas;
   triangle_areas.reserve(m_mesh.m_tris.size());
   std::vector<Vec3d> triangle_normals;
   triangle_normals.reserve(m_mesh.m_tris.size());
   std::vector<Vec3d> triangle_centroids;
   triangle_centroids.reserve(m_mesh.m_tris.size());
   
   for ( unsigned int i = 0; i < m_mesh.m_tris.size(); ++i )
   {
      if ( m_mesh.m_tris[i][0] == m_mesh.m_tris[i][1] )
      {
         triangle_areas.push_back( 0 );
         triangle_normals.push_back( Vec3d(0,0,0) );
         triangle_centroids.push_back( Vec3d(0,0,0) );
      }
      else
      {
         triangle_areas.push_back( get_triangle_area( i ) );
         triangle_normals.push_back( get_triangle_normal( i ) );
         triangle_centroids.push_back( (m_positions[m_mesh.m_tris[i][0]] + m_positions[m_mesh.m_tris[i][1]] + m_positions[m_mesh.m_tris[i][2]]) / 3 );
      }
   }
   
   std::vector<Vec3d> displacements;
   displacements.resize( m_positions.size(), Vec3d(0) );
   
   for ( unsigned int i = 0; i < m_positions.size(); ++i )
   {
      if ( m_masses[i] < 200 )
      {
         null_space_smooth_vertex( i, triangle_areas, triangle_normals, triangle_centroids, displacements[i] );
      }
   }
   
   // compute maximum dt
   double max_beta = 1.0; //compute_max_timestep_quadratic_solve( m_mesh.m_tris, m_positions, displacements, this->m_verbose );
   
   if ( m_verbose ) { printf( "max beta: %g\n", max_beta ); }
   
   for ( unsigned int i = 0; i < m_positions.size(); ++i )
   {
      m_newpositions[i] = m_positions[i] + (max_beta) * displacements[i];
      m_velocities[i] = (m_newpositions[i] - m_positions[i]) / dt;
   }
      
   // repositioned locations stored in m_newpositions, but needs to be collision safe
   if ( m_collision_safety )
   {
      rebuild_continuous_broad_phase();
      bool all_collisions_handled = handle_collisions(dt);
      if ( !all_collisions_handled )
      {
         bool result = handle_collisions_simultaneous(dt);
         if ( !result )
         {
            new_rigid_impact_zones(dt);
         }
      }
      
   }
   
   // used to test convergence
   double max_position_change = 0.0;
   
   // Set positions
   for(unsigned int i = 0; i < m_positions.size(); i++)
   {
      max_position_change = max( max_position_change, mag( m_newpositions[i] - m_positions[i] ) );
      m_positions[i] = m_newpositions[i];
   } 

   if ( m_verbose ) { std::cout << "max_position_change: " << max_position_change << std::endl; }
   
   // We will test convergence by checking whether the largest change in
   // position has magnitude less than: CONVERGENCE_TOL_SCALAR * average_edge_length  
   const static double CONVERGENCE_TOL_SCALAR = 1.0;   
   bool converged = false;
   if ( max_position_change < CONVERGENCE_TOL_SCALAR * get_average_edge_length() )
   {
      converged = true;
   }
   
   for ( unsigned int i = 0; i < m_velocities.size(); ++i )
   {
      m_velocities[i] = saved_velocities[i];
   }
   
   rebuild_static_broad_phase();
   
   return !converged;
}


// --------------------------------------------------------
///
/// Zipper nearby edges together
///
// --------------------------------------------------------

bool SurfTrack::merge_pass()
{
   std::cout << "---------------------- El Topo: merging / topology change --------------------" << std::endl;
   
   m_broad_phase->update_broad_phase_static( *this );
   
   std::queue<Vec2ui> edge_edge_candidates;

   //
   // Check edge-edge proximities for zippering candidates
   //
   
   bool merge_occured = false;
   
   // sorted by proximity so we merge closest pairs first
   std::vector<SortableEdgeEdgeProximity> proximities;
   
   for(unsigned int i = 0; i < m_mesh.m_edges.size(); i++)
   {
      Vec2ui e0 = m_mesh.m_edges[i];
      
      if ( e0[0] == e0[1] ) { continue; }
      if ( m_masses[e0[0]] > 100 ) { continue; }
         
      Vec3d emin, emax;
      edge_static_bounds(i, emin, emax);
      emin -= m_merge_proximity_epsilon * Vec3d(1,1,1);
      emax += m_merge_proximity_epsilon * Vec3d(1,1,1);
      
      std::vector<unsigned int> edge_candidates;
      m_broad_phase->get_potential_edge_collisions( emin, emax, edge_candidates );
      
      for(unsigned int j = 0; j < edge_candidates.size(); j++)
      {
         unsigned int proximal_edge_index = edge_candidates[j];
         Vec2ui e1 = m_mesh.m_edges[proximal_edge_index];
         
         if ( proximal_edge_index <= i )
         {
            continue;
         }
         
         if ( m_masses[e0[0]] != m_masses[e1[0]] )
         {
            continue;
         }
         
         if(e0[0] != e1[0] && e0[0] != e1[1] && e0[1] != e1[0] && e0[1] != e1[1])
         {
            double distance, s0, s2;
            Vec3d normal;
            
            segment_segment_distance( m_positions[e0[0]], e0[0],
                                      m_positions[e0[1]], e0[1],
                                      m_positions[e1[0]], e1[0],
                                      m_positions[e1[1]], e1[1],
                                      distance, s0, s2, normal );
            
            if (distance < m_merge_proximity_epsilon)
            {
               proximities.push_back( SortableEdgeEdgeProximity(i, proximal_edge_index, distance) );
            }
         }
      }
   }
    
   sort( proximities.begin(), proximities.end() );
                
   if ( m_verbose ) { std::cout << "num merge proximities: " << proximities.size() << std::endl; }
   
   g_zipper_non_manifold_edges = 0;
   g_zipper_mass_match = 0;
   g_zipper_no_set_triangles = 0;
   g_zipper_collision = 0;
   
   for ( unsigned int i = 0; i < proximities.size(); ++i )
   {
      unsigned int edge_index_a = proximities[i].edge_a;
      unsigned int edge_index_b = proximities[i].edge_b;
      
      if ( ( m_mesh.m_edges[edge_index_a][0] == m_mesh.m_edges[edge_index_a][1] ) || ( m_mesh.m_edges[edge_index_b][0] == m_mesh.m_edges[edge_index_b][1] ) )
      {
         continue;
      }
      
      if ( m_verbose ) { std::cout << "proximity: " << proximities[i].distance << std::endl; }
      
      if ( zipper_edges( proximities[i].edge_a, proximities[i].edge_b ) )
      {
         
         trim_non_manifold( m_dirty_triangles );
         m_dirty_triangles.clear();
         
         if ( m_verbose ) { std::cout << "zippered" << std::endl; }
         merge_occured = true;
      }
   }
   
   if ( merge_occured )
   {
      assert_no_degenerate_triangles();
   }
   
   return merge_occured;

}


// --------------------------------------------------------
///
/// One pass: split long edges, flip non-delaunay edges, collapse short edges, null-space smoothing
///
// --------------------------------------------------------

void SurfTrack::improve_mesh( )
{     

   if ( m_perform_improvement )
   {
      rebuild_static_broad_phase();
            
      while ( split_pass() ) {}

      flip_pass();		

      while ( collapse_pass() ) {}
   
      null_space_smoothing_pass( 1.0 );
      
      clear_deleted_vertices();
      m_mesh.update_connectivity( m_positions.size() );

      if ( m_collision_safety )
      {
         assert_mesh_is_intersection_free();
      }
      
   }
         
}

// --------------------------------------------------------
///
/// Perform a pass of merge attempts
///
// --------------------------------------------------------

void SurfTrack::topology_changes( )
{
   
   if ( m_allow_topology_changes )
   {
      bool merge_occurred = true;
      while ( merge_occurred )
      {
         rebuild_static_broad_phase();
         
         //m_verbose = true;
         merge_occurred = merge_pass();
         //m_verbose = false;
         
         if ( !merge_occurred )
         {
            break;
         }
         
         clear_deleted_vertices();
         m_mesh.update_connectivity( m_positions.size() );
         
         if ( m_collision_safety )
         {
            assert_mesh_is_intersection_free();
         }
      }
   }
   
}




