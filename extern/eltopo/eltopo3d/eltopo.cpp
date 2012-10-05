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

#include "../common/runstats.h"
RunStats g_stats;

// ---------------------------------------------------------
///
/// Static operations: edge collapse, edge split, edge flip, null-space smoothing, and topological changes
///
// ---------------------------------------------------------

void el_topo_static_operations( const ElTopoMesh* inputs,
                               const struct ElTopoGeneralOptions* general_options,
                               const struct ElTopoStaticOperationsOptions* options, 
                               struct ElTopoDefragInformation* defrag_info,  
                               struct ElTopoMesh* outputs )
{
    //
    // data wrangling
    //
    
    std::vector<Vec3d> vs;
    std::vector<double> masses;
    
    for ( int i = 0; i < inputs->num_vertices; ++i )
    {
        vs.push_back( Vec3d( inputs->vertex_locations[3*i], inputs->vertex_locations[3*i + 1], inputs->vertex_locations[3*i + 2] ) );
        masses.push_back( inputs->vertex_masses[i] );      
    }
    
    std::vector<Vec3st> ts;
    for ( int i = 0; i < inputs->num_triangles; ++i )
    {
        ts.push_back( Vec3st( inputs->triangles[3*i], inputs->triangles[3*i + 1], inputs->triangles[3*i + 2] ) );
    }
    
    
    // =================================================================================
    
    //
    // do the actual operations
    //
    
    // build a SurfTrack
    SurfTrackInitializationParameters construction_parameters;
    
    construction_parameters.m_proximity_epsilon = general_options->m_proximity_epsilon;
    
    construction_parameters.m_use_fraction = false;
    construction_parameters.m_min_edge_length = options->m_min_edge_length;
    construction_parameters.m_max_edge_length = options->m_max_edge_length;
    construction_parameters.m_max_volume_change = options->m_max_volume_change;   
    construction_parameters.m_min_triangle_angle = options->m_min_triangle_angle;
    construction_parameters.m_max_triangle_angle = options->m_max_triangle_angle;
    construction_parameters.m_use_curvature_when_splitting = options->m_use_curvature_when_splitting;
    construction_parameters.m_use_curvature_when_collapsing = options->m_use_curvature_when_collapsing;
    construction_parameters.m_min_curvature_multiplier = options->m_min_curvature_multiplier;
    construction_parameters.m_max_curvature_multiplier = options->m_max_curvature_multiplier;
    construction_parameters.m_allow_vertex_movement = options->m_allow_vertex_movement;
    construction_parameters.m_edge_flip_min_length_change = options->m_edge_flip_min_length_change;   
    construction_parameters.m_merge_proximity_epsilon = options->m_merge_proximity_epsilon;
    construction_parameters.m_collision_safety = general_options->m_collision_safety;
    construction_parameters.m_allow_topology_changes = options->m_allow_topology_changes;
    construction_parameters.m_perform_improvement = options->m_perform_improvement;
    construction_parameters.m_subdivision_scheme = (SubdivisionScheme*) options->m_subdivision_scheme;
    
    
    SurfTrack surface_tracker( vs, ts, masses, construction_parameters ); 
    
    surface_tracker.improve_mesh();
    
    // do merging
    surface_tracker.topology_changes();
    
    surface_tracker.defrag_mesh();
    
    
    // =================================================================================
    
    defrag_info->num_vertex_changes = to_int(surface_tracker.m_vertex_change_history.size());
    defrag_info->vertex_is_remove = (int*) malloc( defrag_info->num_vertex_changes * sizeof(int) );
    defrag_info->vertex_index = (int*) malloc( defrag_info->num_vertex_changes * sizeof(int) );
    defrag_info->split_edge = (int*) malloc( 2 * defrag_info->num_vertex_changes * sizeof(int) );
    
    for ( int i = 0; i < defrag_info->num_vertex_changes; ++i )
    {
        defrag_info->vertex_is_remove[i] = surface_tracker.m_vertex_change_history[i].m_is_remove ? 1 : 0;
        defrag_info->vertex_index[i] = to_int(surface_tracker.m_vertex_change_history[i].m_vertex_index);
        defrag_info->split_edge[2*i+0] = to_int(surface_tracker.m_vertex_change_history[i].m_split_edge[0]);
        defrag_info->split_edge[2*i+1] = to_int(surface_tracker.m_vertex_change_history[i].m_split_edge[1]);
    }
    
    defrag_info->num_triangle_changes = to_int(surface_tracker.m_triangle_change_history.size());
    defrag_info->triangle_is_remove = (int*) malloc( defrag_info->num_triangle_changes * sizeof(int) );
    defrag_info->triangle_index = (int*) malloc( defrag_info->num_triangle_changes * sizeof(int) );
    defrag_info->new_tri = (int*) malloc( 3 * defrag_info->num_triangle_changes * sizeof(int) );
    
    for ( int i = 0; i < defrag_info->num_triangle_changes; ++i )
    {
        defrag_info->triangle_is_remove[i] = surface_tracker.m_triangle_change_history[i].m_is_remove ? 1 : 0;
        defrag_info->triangle_index[i] = to_int(surface_tracker.m_triangle_change_history[i].m_triangle_index);
        defrag_info->new_tri[3*i+0] = to_int(surface_tracker.m_triangle_change_history[i].m_tri[0]);
        defrag_info->new_tri[3*i+1] = to_int(surface_tracker.m_triangle_change_history[i].m_tri[1]);
        defrag_info->new_tri[3*i+2] = to_int(surface_tracker.m_triangle_change_history[i].m_tri[2]);
    }
    
    
    defrag_info->defragged_triangle_map_size = to_int(surface_tracker.m_defragged_triangle_map.size());
    defrag_info->defragged_triangle_map = (int*) malloc( 2 * defrag_info->defragged_triangle_map_size * sizeof(int)  );
    
    for ( int i = 0; i < defrag_info->defragged_triangle_map_size; ++i )
    {
        defrag_info->defragged_triangle_map[2*i+0] = to_int(surface_tracker.m_defragged_triangle_map[i][0]);
        defrag_info->defragged_triangle_map[2*i+1] = to_int(surface_tracker.m_defragged_triangle_map[i][1]);
    }
    
    defrag_info->defragged_vertex_map_size = to_int(surface_tracker.m_defragged_vertex_map.size());
    defrag_info->defragged_vertex_map = (int*) malloc( 2 * defrag_info->defragged_vertex_map_size * sizeof(int) );
    
    for ( int i = 0; i < defrag_info->defragged_vertex_map_size; ++i )
    {
        defrag_info->defragged_vertex_map[2*i+0] = to_int(surface_tracker.m_defragged_vertex_map[i][0]);
        defrag_info->defragged_vertex_map[2*i+1] = to_int(surface_tracker.m_defragged_vertex_map[i][1]);
    }
    
    // =================================================================================
    
    //
    // data wrangling
    //
    
    outputs->num_vertices = to_int(surface_tracker.get_num_vertices());
    outputs->vertex_locations = (double*) malloc( 3 * (outputs->num_vertices) * sizeof(double) );
    outputs->vertex_masses = (double*) malloc( (outputs->num_vertices) * sizeof(double) );
    
    for ( int i = 0; i < outputs->num_vertices; ++i )
    {
        const Vec3d& pos = surface_tracker.get_position(i);
        outputs->vertex_locations[3*i + 0] = pos[0];
        outputs->vertex_locations[3*i + 1] = pos[1];  
        outputs->vertex_locations[3*i + 2] = pos[2];
        outputs->vertex_masses[i] = surface_tracker.m_masses[i];
    }
    
    outputs->num_triangles = to_int(surface_tracker.m_mesh.num_triangles());
    outputs->triangles = (int*) malloc( 3 * (outputs->num_triangles) * sizeof(int) );
    
    for ( int i = 0; i < outputs->num_triangles; ++i )
    {
        const Vec3st& curr_tri = surface_tracker.m_mesh.get_triangle(i); 
        outputs->triangles[3*i + 0] = to_int(curr_tri[0]);
        outputs->triangles[3*i + 1] = to_int(curr_tri[1]);
        outputs->triangles[3*i + 2] = to_int(curr_tri[2]);
    }
    
}


// ---------------------------------------------------------
///
/// Free memory allocated by static operations and defrag.
///
// ---------------------------------------------------------

void el_topo_free_static_operations_results( ElTopoMesh* outputs, struct ElTopoDefragInformation* defrag_info )
{
    free( outputs->vertex_locations );
    free( outputs->vertex_masses );
    free( outputs->triangles );
    
    free( defrag_info->vertex_is_remove );
    free( defrag_info->vertex_index );
    free( defrag_info->split_edge );
    free( defrag_info->triangle_is_remove );
    free( defrag_info->triangle_index );
    free( defrag_info->new_tri );
    free( defrag_info->defragged_triangle_map );
    free( defrag_info->defragged_vertex_map );
}


// ---------------------------------------------------------
///
/// Surface vertex position integration.
///
// ---------------------------------------------------------

void el_topo_integrate( const ElTopoMesh* inputs,
                       const double* in_vertex_new_locations,
                       const struct ElTopoGeneralOptions* general_options,
                       const struct ElTopoIntegrationOptions* options,
                       double **out_vertex_locations,
                       double *out_dt )
{
    //
    // data wrangling
    //
    
    std::vector<Vec3d> vs;
    std::vector<double> masses;
    
    for ( int i = 0; i < inputs->num_vertices; ++i )
    {
        vs.push_back( Vec3d( inputs->vertex_locations[3*i], inputs->vertex_locations[3*i + 1], inputs->vertex_locations[3*i + 2] ) );
        masses.push_back( inputs->vertex_masses[i] );
    }
    
    std::vector<Vec3st> ts;
    for ( int i = 0; i < inputs->num_triangles; ++i )
    {
        ts.push_back( Vec3st( inputs->triangles[3*i], inputs->triangles[3*i + 1], inputs->triangles[3*i + 2] ) );
    }
    
    // =================================================================================
    
    //
    // do the integration
    //
    
    // build a DynamicSurface
	DynamicSurface dynamic_surface( vs, ts, masses, general_options->m_proximity_epsilon, options->m_friction_coefficient, general_options->m_collision_safety, general_options->m_verbose );
    
    dynamic_surface.set_all_newpositions( inputs->num_vertices, in_vertex_new_locations );
    
    // advance by dt
    double actual_dt;
    dynamic_surface.integrate( options->m_dt, actual_dt );
    
    // the dt used may be different than specified (if we cut the time step)
    *out_dt = actual_dt;
    
    
    // =================================================================================   
    
    //
    // data wrangling
    //
    
    *out_vertex_locations = (double*) malloc( 3 * inputs->num_vertices * sizeof(double) );
    for ( int i = 0; i < inputs->num_vertices; ++i )
    {
        const Vec3d& pos = dynamic_surface.get_position(i);
        (*out_vertex_locations)[3*i]     = pos[0];
        (*out_vertex_locations)[3*i + 1] = pos[1];
        (*out_vertex_locations)[3*i + 2] = pos[2];
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



