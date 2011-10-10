
// ---------------------------------------------------------
//
//  eltopo.cpp
//  Tyson Brochu 2009
//
//  C-callable API for El Topo
//
// ---------------------------------------------------------

#include <eltopo.h>
#include <surftrack.h>


// ---------------------------------------------------------
///
/// Static operations: edge collapse, edge split, edge flip, null-space smoothing, and topological changes
///
// ---------------------------------------------------------

void el_topo_static_operations( const int in_num_vertices,                      // input
                        const double* in_vertex_locations,           
                        const int in_num_triangles,                   
                        const int* in_triangles,
                        const double* in_masses,
                        const struct ElTopoGeneralOptions* general_options,     // options
                        const struct ElTopoStaticOperationsOptions* options, 
                        int* out_num_vertices,                                  // output
                        double** out_vertex_locations,  
                        int* out_num_triangles,
                        int** out_triangles,
                        double** out_masses ) 
{
   //
   // data wrangling
   //
   
   std::vector<Vec3d> vs;
   std::vector<double> ms;
   for ( int i = 0; i < in_num_vertices; ++i )
   {
      vs.push_back( Vec3d( in_vertex_locations[3*i], in_vertex_locations[3*i + 1], in_vertex_locations[3*i + 2] ) );
      ms.push_back( in_masses[i] );
   }

   std::vector<Vec3ui> ts;
   for ( int i = 0; i < in_num_triangles; ++i )
   {
      ts.push_back( Vec3ui( in_triangles[3*i], in_triangles[3*i + 1], in_triangles[3*i + 2] ) );
   }
   

   // =================================================================================
   
   //
   // do the actual operations
   //
   
   // build a SurfTrack
   SurfTrackInitializationParameters construction_parameters;
            
   construction_parameters.m_min_edge_length = options->m_min_edge_length;
   construction_parameters.m_max_edge_length = options->m_max_edge_length;
   construction_parameters.m_max_volume_change = options->m_max_volume_change;
   construction_parameters.m_merge_proximity_epsilon = options->m_merge_proximity_epsilon;
   construction_parameters.m_collision_safety = general_options->m_collision_safety;
   construction_parameters.m_allow_topology_changes = options->m_allow_topology_changes;
   construction_parameters.m_perform_improvement = options->m_perform_improvement;
   construction_parameters.m_subdivision_scheme = (SubdivisionScheme*) options->m_subdivision_scheme;

   SurfTrack surface_tracker( vs, ts, ms, construction_parameters );
   
   surface_tracker.clear_deleted_vertices();
   
   // perform mesh improvement
   surface_tracker.improve_mesh();
   
   // do merging
   surface_tracker.topology_changes();
      
   // TEMP
   for ( unsigned int i = 0; i < surface_tracker.m_positions.size(); ++i )
   {
      assert( surface_tracker.m_mesh.m_vtxtri[i].size() > 0 );
   }
   
   // =================================================================================

   //
   // data wrangling
   //
   
   *out_num_vertices = surface_tracker.m_positions.size();
   *out_vertex_locations = (double*) malloc( 3 * (*out_num_vertices) * sizeof(double) );
   *out_masses = (double*) malloc( (*out_num_vertices) * sizeof(double) );
   for ( int i = 0; i < (*out_num_vertices); ++i )
   {
      (*out_vertex_locations)[3*i] = surface_tracker.m_positions[i][0];
      (*out_vertex_locations)[3*i + 1] = surface_tracker.m_positions[i][1];      
      (*out_vertex_locations)[3*i + 2] = surface_tracker.m_positions[i][2];            
      (*out_masses)[i] = surface_tracker.m_masses[i];
   }
   
   *out_num_triangles = surface_tracker.m_mesh.m_tris.size();
   *out_triangles = (int*) malloc( 3 * (*out_num_triangles) * sizeof(int) );
   for ( int i = 0; i < (*out_num_triangles); ++i )
   {
      (*out_triangles)[3*i] = surface_tracker.m_mesh.m_tris[i][0];
      (*out_triangles)[3*i + 1] = surface_tracker.m_mesh.m_tris[i][1]; 
      (*out_triangles)[3*i + 2] = surface_tracker.m_mesh.m_tris[i][2];       
   }
   
}


// ---------------------------------------------------------
///
/// Free memory allocated by static operations.
///
// ---------------------------------------------------------

void el_topo_free_static_operations_results( double* out_vertex_locations, int* out_triangles, double* out_masses )
{
   free( out_vertex_locations );
   free( out_triangles );
   free( out_masses );
}
  

// ---------------------------------------------------------
///
/// Surface vertex position integration.
///
// ---------------------------------------------------------

extern "C" void el_topo_integrate( const int num_vertices, 
                        const double *in_vertex_locations, 
                        const double *in_vertex_new_locations, 
                        const int num_triangles, 
                        const int *triangles,
                        const double *in_masses,
                        const struct ElTopoGeneralOptions* general_options,
                        const struct ElTopoIntegrationOptions* options,
                        double **out_vertex_locations )
{
   //
   // data wrangling
   //
   
   std::vector<Vec3d> vs;
   std::vector<double> masses;
   for ( int i = 0; i < num_vertices; ++i )
   {
      vs.push_back( Vec3d( in_vertex_locations[3*i], in_vertex_locations[3*i + 1], in_vertex_locations[3*i + 2] ) );
      masses.push_back(in_masses[i]);
   }
   
   std::vector<Vec3ui> ts;
   for ( int i = 0; i < num_triangles; ++i )
   {
      ts.push_back( Vec3ui( triangles[3*i], triangles[3*i + 1], triangles[3*i + 2] ) );
   }
   
   
   // =================================================================================
   
   //
   // do the integration
   //
   
   // build a DynamicSurface
   DynamicSurface dynamic_surface( vs, ts, masses, options->m_proximity_epsilon, general_options->m_collision_safety );

   dynamic_surface.m_mesh.update_connectivity( num_vertices );
   
   // set velocities
   dynamic_surface.m_velocities.resize( num_vertices );
   for ( int i = 0; i < num_vertices; ++i )
   {
      dynamic_surface.m_newpositions[i] = Vec3d( in_vertex_new_locations[3*i], in_vertex_new_locations[3*i + 1], in_vertex_new_locations[3*i + 2] );
      dynamic_surface.m_velocities[i] = ( dynamic_surface.m_newpositions[i] - dynamic_surface.m_positions[i] ) / options->m_dt;
   }
   
   // advance by dt
   dynamic_surface.integrate( options->m_dt );
   
   
   // =================================================================================   
   
   //
   // data wrangling
   //
   
   *out_vertex_locations = (double*) malloc( 3 * num_vertices * sizeof(double) );
   for ( int i = 0; i < num_vertices; ++i )
   {
      (*out_vertex_locations)[3*i]     = dynamic_surface.m_positions[i][0];
      (*out_vertex_locations)[3*i + 1] = dynamic_surface.m_positions[i][1];
      (*out_vertex_locations)[3*i + 2] = dynamic_surface.m_positions[i][2];
   }
      
}


// ---------------------------------------------------------
///
/// Free memory allocated by integration.
///
// ---------------------------------------------------------

void el_topo_free_integrate_results( double* out_vertex_locations )
{
   free( out_vertex_locations );
}

   

