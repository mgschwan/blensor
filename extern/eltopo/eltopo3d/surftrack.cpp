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

#include <array3.h>
#include <broadphase.h>
#include <cassert>
#include <ccd_wrapper.h>
#include <collisionpipeline.h>
#include <collisionqueries.h>
#include <edgeflipper.h>
#include <impactzonesolver.h>
#include <lapack_wrapper.h>
#include <nondestructivetrimesh.h>
#include <queue>
#include <runstats.h>
#include <subdivisionscheme.h>
#include <stdio.h>
#include <trianglequality.h>
#include <vec.h>
#include <vector>
#include <wallclocktime.h>


// ---------------------------------------------------------
//  Global externs
// ---------------------------------------------------------

const double G_EIGENVALUE_RANK_RATIO = 0.03;

extern RunStats g_stats;

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
m_friction_coefficient( 0.0 ),
m_min_triangle_area( 1e-7 ),
m_improve_collision_epsilon( 2e-6 ),
m_use_fraction( false ),
m_min_edge_length( UNINITIALIZED_DOUBLE ),     // <- Don't allow instantiation without setting these parameters
m_max_edge_length( UNINITIALIZED_DOUBLE ),     // <-
m_max_volume_change( UNINITIALIZED_DOUBLE ),   // <-
m_min_triangle_angle( 0.0 ),
m_max_triangle_angle( 180.0 ),
m_use_curvature_when_splitting( false ),
m_use_curvature_when_collapsing( false ),
m_min_curvature_multiplier( 1.0 ),
m_max_curvature_multiplier( 1.0 ),
m_allow_vertex_movement( true ),
m_edge_flip_min_length_change( 1e-8 ),
m_merge_proximity_epsilon( 1e-5 ),
m_subdivision_scheme(NULL),
m_collision_safety(true),
m_allow_topology_changes(true),
m_allow_non_manifold(true),
m_perform_improvement(true)
{}


// ---------------------------------------------------------
///
/// Create a SurfTrack object from a set of vertices and triangles using the specified paramaters
///
// ---------------------------------------------------------

SurfTrack::SurfTrack( const std::vector<Vec3d>& vs, 
                     const std::vector<Vec3st>& ts, 
                     const std::vector<double>& masses,
                     const SurfTrackInitializationParameters& initial_parameters ) :

DynamicSurface( vs, 
               ts,
               masses,
               initial_parameters.m_proximity_epsilon, 
               initial_parameters.m_friction_coefficient,
               initial_parameters.m_collision_safety ),

m_collapser( *this, initial_parameters.m_use_curvature_when_collapsing, initial_parameters.m_min_curvature_multiplier ),
m_splitter( *this, initial_parameters.m_use_curvature_when_splitting, initial_parameters.m_max_curvature_multiplier ),
m_flipper( *this, initial_parameters.m_edge_flip_min_length_change ),
m_smoother( *this ),
m_merger( *this ),
m_pincher( *this ),
m_improve_collision_epsilon( initial_parameters.m_improve_collision_epsilon ),
m_edge_flip_min_length_change( initial_parameters.m_edge_flip_min_length_change ),
m_max_volume_change( UNINITIALIZED_DOUBLE ),   
m_min_edge_length( UNINITIALIZED_DOUBLE ),
m_max_edge_length( UNINITIALIZED_DOUBLE ),
m_merge_proximity_epsilon( initial_parameters.m_merge_proximity_epsilon ),   
m_min_triangle_area( initial_parameters.m_min_triangle_area ),
m_min_triangle_angle( initial_parameters.m_min_triangle_angle ),
m_max_triangle_angle( initial_parameters.m_max_triangle_angle ),
m_subdivision_scheme( initial_parameters.m_subdivision_scheme ),
should_delete_subdivision_scheme_object( m_subdivision_scheme == NULL ? true : false ),
m_dirty_triangles(0),   
m_allow_topology_changes( initial_parameters.m_allow_topology_changes ),
m_allow_non_manifold( initial_parameters.m_allow_non_manifold ),
m_perform_improvement( initial_parameters.m_perform_improvement ),
m_allow_vertex_movement( initial_parameters.m_allow_vertex_movement ),
m_vertex_change_history(),
m_triangle_change_history(),
m_defragged_triangle_map(),
m_defragged_vertex_map()
{
    
    if ( m_verbose )
    {
        std::cout << " ======== SurfTrack ======== " << std::endl;   
        std::cout << "m_allow_topology_changes: " << m_allow_topology_changes << std::endl;
        std::cout << "m_perform_improvement: " << m_perform_improvement << std::endl;   
        std::cout << "m_min_triangle_area: " << m_min_triangle_area << std::endl;
        std::cout << "initial_parameters.m_use_fraction: " << initial_parameters.m_use_fraction << std::endl;
    }
    
    if ( m_collision_safety )
    {
        rebuild_static_broad_phase();
    }
    
    assert( initial_parameters.m_min_edge_length != UNINITIALIZED_DOUBLE );
    assert( initial_parameters.m_max_edge_length != UNINITIALIZED_DOUBLE );
    assert( initial_parameters.m_max_volume_change != UNINITIALIZED_DOUBLE );
    
    if ( initial_parameters.m_use_fraction )
    {
        double avg_length = DynamicSurface::get_average_non_solid_edge_length();   
        m_collapser.m_min_edge_length = initial_parameters.m_min_edge_length * avg_length;
        m_splitter.m_max_edge_length = initial_parameters.m_max_edge_length * avg_length;
        m_min_edge_length = initial_parameters.m_min_edge_length * avg_length;
        m_max_edge_length = initial_parameters.m_max_edge_length * avg_length;
        m_max_volume_change = initial_parameters.m_max_volume_change * avg_length * avg_length * avg_length;        
    }
    else
    {
        m_collapser.m_min_edge_length = initial_parameters.m_min_edge_length;
        m_splitter.m_max_edge_length = initial_parameters.m_max_edge_length;
        m_min_edge_length = initial_parameters.m_min_edge_length;
        m_max_edge_length = initial_parameters.m_max_edge_length;
        m_max_volume_change = initial_parameters.m_max_volume_change;  
    }
    
    if ( m_verbose )
    {
        std::cout << "m_min_edge_length: " << m_min_edge_length << std::endl;
        std::cout << "m_max_edge_length: " << m_max_edge_length << std::endl;
        std::cout << "m_max_volume_change: " << m_max_volume_change << std::endl;
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
    
    if ( false == m_allow_topology_changes )
    {
        m_allow_non_manifold = false;
    }
    
}

// ---------------------------------------------------------
///
/// Destructor.  Deallocates the subdivision scheme object if we created one.
///
// ---------------------------------------------------------

SurfTrack::~SurfTrack()
{
    if ( should_delete_subdivision_scheme_object )
    {
        delete m_subdivision_scheme;
    }
}


// ---------------------------------------------------------
///
/// Add a triangle to the surface.  Update the underlying TriMesh and acceleration grid. 
///
// ---------------------------------------------------------

size_t SurfTrack::add_triangle( const Vec3st& t )
{
    size_t new_triangle_index = m_mesh.nondestructive_add_triangle( t );
    
    assert( t[0] < get_num_vertices() );
    assert( t[1] < get_num_vertices() );
    assert( t[2] < get_num_vertices() );
    
    if ( m_collision_safety )
    {
        // Add to the triangle grid
        Vec3d low, high;
        triangle_static_bounds( new_triangle_index, low, high );
        m_broad_phase->add_triangle( new_triangle_index, low, high, triangle_is_solid(new_triangle_index) );
        
        // Add edges to grid as well
        size_t new_edge_index = m_mesh.get_edge_index( t[0], t[1] );
        assert( new_edge_index != m_mesh.m_edges.size() );
        edge_static_bounds( new_edge_index, low, high );
        m_broad_phase->add_edge( new_edge_index, low, high, edge_is_solid( new_edge_index ) );
        
        new_edge_index = m_mesh.get_edge_index( t[1], t[2] );
        assert( new_edge_index != m_mesh.m_edges.size() );   
        edge_static_bounds( new_edge_index, low, high );
        m_broad_phase->add_edge( new_edge_index, low, high, edge_is_solid( new_edge_index )  );
        
        new_edge_index = m_mesh.get_edge_index( t[2], t[0] );
        assert( new_edge_index != m_mesh.m_edges.size() );   
        edge_static_bounds( new_edge_index, low, high );
        m_broad_phase->add_edge( new_edge_index, low, high, edge_is_solid( new_edge_index )  );
    }
    
    m_triangle_change_history.push_back( TriangleUpdateEvent( TriangleUpdateEvent::TRIANGLE_ADD, new_triangle_index, t ) );
    
    return new_triangle_index;
}


// ---------------------------------------------------------
///
/// Remove a triangle from the surface.  Update the underlying TriMesh and acceleration grid. 
///
// ---------------------------------------------------------

void SurfTrack::remove_triangle(size_t t)
{
    m_mesh.nondestructive_remove_triangle( t );
    if ( m_collision_safety )
    {
        m_broad_phase->remove_triangle( t );
    }
    
    m_triangle_change_history.push_back( TriangleUpdateEvent( TriangleUpdateEvent::TRIANGLE_REMOVE, t, Vec3st(0) ) );
    
}

// ---------------------------------------------------------
///
/// Add a vertex to the surface.  Update the acceleration grid. 
///
// ---------------------------------------------------------

size_t SurfTrack::add_vertex( const Vec3d& new_vertex_position, double new_vertex_mass )
{
    size_t new_vertex_index = m_mesh.nondestructive_add_vertex( );
    
    if( new_vertex_index > get_num_vertices() - 1 )
    {
        pm_positions.resize( new_vertex_index  + 1 );
        pm_newpositions.resize( new_vertex_index  + 1 );
        m_masses.resize( new_vertex_index  + 1 );
    }
    
    pm_positions[new_vertex_index] = new_vertex_position;
    pm_newpositions[new_vertex_index] = new_vertex_position;
    m_masses[new_vertex_index] = new_vertex_mass;
    
    if ( m_collision_safety )
    {
        m_broad_phase->add_vertex( new_vertex_index, get_position(new_vertex_index), get_position(new_vertex_index), vertex_is_solid(new_vertex_index) );       
    }
    
    return new_vertex_index;
}


// ---------------------------------------------------------
///
/// Remove a vertex from the surface.  Update the acceleration grid. 
///
// ---------------------------------------------------------

void SurfTrack::remove_vertex( size_t vertex_index )
{
    m_mesh.nondestructive_remove_vertex( vertex_index );
    
    if ( m_collision_safety )
    {
        m_broad_phase->remove_vertex( vertex_index );
    }
    
    m_vertex_change_history.push_back( VertexUpdateEvent( VertexUpdateEvent::VERTEX_REMOVE, vertex_index, Vec2st(0,0) ) );
    
}


// ---------------------------------------------------------
///
/// Remove deleted vertices and triangles from the mesh data structures
///
// ---------------------------------------------------------

void SurfTrack::defrag_mesh( )
{
    
    //
    // First clear deleted vertices from the data stuctures
    // 
    
    double start_time = get_time_in_seconds();
    
    
    // do a quick pass through to see if any vertices have been deleted
    bool any_deleted = false;
    for ( size_t i = 0; i < get_num_vertices(); ++i )
    {  
        if ( m_mesh.vertex_is_deleted(i) )
        {
            any_deleted = true;
            break;
        }
    }    
    
    if ( !any_deleted )
    {
        for ( size_t i = 0; i < get_num_vertices(); ++i )
        {
            m_defragged_vertex_map.push_back( Vec2st(i,i) );
        }
        
        double end_time = get_time_in_seconds();      
        g_stats.add_to_double( "total_clear_deleted_vertices_time", end_time - start_time );
        
    }
    else
    {
        
        // Note: We could rebuild the mesh from scratch, rather than adding/removing 
        // triangles, however this function is not a major computational bottleneck.
        
        size_t j = 0;
        
        std::vector<Vec3st> new_tris = m_mesh.get_triangles();
        
        for ( size_t i = 0; i < get_num_vertices(); ++i )
        {      
            if ( !m_mesh.vertex_is_deleted(i) )
            {
                pm_positions[j] = pm_positions[i];
                pm_newpositions[j] = pm_newpositions[i];
                m_masses[j] = m_masses[i];
                
                m_defragged_vertex_map.push_back( Vec2st(i,j) );
                
                // Now rewire the triangles containting vertex i
                
                // copy this, since we'll be changing the original as we go
                std::vector<size_t> inc_tris = m_mesh.m_vertex_to_triangle_map[i];
                
                for ( size_t t = 0; t < inc_tris.size(); ++t )
                {
                    Vec3st triangle = m_mesh.get_triangle( inc_tris[t] );
                    
                    assert( triangle[0] == i || triangle[1] == i || triangle[2] == i );
                    if ( triangle[0] == i ) { triangle[0] = j; }
                    if ( triangle[1] == i ) { triangle[1] = j; }
                    if ( triangle[2] == i ) { triangle[2] = j; }        
                    
                    remove_triangle(inc_tris[t]);       // mark the triangle deleted
                    add_triangle(triangle);             // add the updated triangle
                }
                
                ++j;
            }
        }
        
        pm_positions.resize(j);
        pm_newpositions.resize(j);
        m_masses.resize(j);
    }
    
    double end_time = get_time_in_seconds();
    
    g_stats.add_to_double( "total_clear_deleted_vertices_time", end_time - start_time );
    
    
    //
    // Now clear deleted triangles from the mesh
    // 
    
    m_mesh.set_num_vertices( get_num_vertices() );    
    m_mesh.clear_deleted_triangles( &m_defragged_triangle_map );
    
    if ( m_collision_safety )
    {
        rebuild_continuous_broad_phase();
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
    for ( size_t i = 0; i < m_mesh.num_triangles(); ++i )
    {
        
        const Vec3st& current_triangle = m_mesh.get_triangle(i);
        
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
        const Vec3st& tri_edges = m_mesh.m_triangle_to_edge_map[i];
        
        bool flap_found = false;
        
        for ( unsigned int e = 0; e < 3 && flap_found == false; ++e )
        {
            const std::vector<size_t>& edge_tris = m_mesh.m_edge_to_triangle_map[ tri_edges[e] ];
            
            for ( size_t t = 0; t < edge_tris.size(); ++t )
            {
                if ( edge_tris[t] == i )
                {
                    continue;
                }
                
                size_t other_triangle_index = edge_tris[t];
                const Vec3st& other_triangle = m_mesh.get_triangle( other_triangle_index );
                
                if ( (other_triangle[0] == other_triangle[1]) || 
                    (other_triangle[1] == other_triangle[2]) || 
                    (other_triangle[2] == other_triangle[0]) ) 
                {
                    assert( !"repeated vertices" );
                }
                
                if ( ((current_triangle[0] == other_triangle[0]) || (current_triangle[0] == other_triangle[1]) || (current_triangle[0] == other_triangle[2])) &&
                    ((current_triangle[1] == other_triangle[0]) || (current_triangle[1] == other_triangle[1]) || (current_triangle[1] == other_triangle[2])) &&
                    ((current_triangle[2] == other_triangle[0]) || (current_triangle[2] == other_triangle[1]) || (current_triangle[2] == other_triangle[2])) ) 
                {
                    
                    size_t common_edge = tri_edges[e];
                    if ( m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], current_triangle ) == 
                        m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], other_triangle ) )
                    { 
                        assert( false );
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

void SurfTrack::trim_non_manifold( std::vector<size_t>& triangle_indices )
{   
    
    // If we're not allowing non-manifold, assert we don't have any
    
    if ( false == m_allow_non_manifold )
    {
        // check for edges incident on more than 2 triangles
        
        for ( size_t i = 0; i < m_mesh.m_edge_to_triangle_map.size(); ++i )
        {
            if ( m_mesh.edge_is_deleted(i) ) { continue; }
            assert( m_mesh.m_edge_to_triangle_map[i].size() == 1 ||
                   m_mesh.m_edge_to_triangle_map[i].size() == 2 );
        }
        
        triangle_indices.clear();
        return;
    }
    
    for ( size_t j = 0; j < triangle_indices.size(); ++j )      
    {
        size_t i = triangle_indices[j];
        
        const Vec3st& current_triangle = m_mesh.get_triangle(i);
        
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
            
            if ( m_verbose ) { std::cout << "deleting degenerate triangle " << i << ": " << current_triangle << std::endl; }
            
            // delete it
            remove_triangle( i );
            
            continue;
        }
        
        
        //
        // look for flaps
        //
        const Vec3st& tri_edges = m_mesh.m_triangle_to_edge_map[i];
        
        bool flap_found = false;
        
        for ( unsigned int e = 0; e < 3 && flap_found == false; ++e )
        {
            const std::vector<size_t>& edge_tris = m_mesh.m_edge_to_triangle_map[ tri_edges[e] ];
            
            for ( size_t t = 0; t < edge_tris.size(); ++t )
            {
                if ( edge_tris[t] == i )
                {
                    continue;
                }
                
                size_t other_triangle_index = edge_tris[t];
                const Vec3st& other_triangle = m_mesh.get_triangle( other_triangle_index );
                
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
                        std::cout << "flap found while topology changes disallowed" << std::endl;
                        std::cout << current_triangle << std::endl;
                        std::cout << other_triangle << std::endl;
                        assert(0);
                    }
                    
                    size_t common_edge = tri_edges[e];
                    if ( m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], current_triangle ) == 
                        m_mesh.oriented( m_mesh.m_edges[common_edge][0], m_mesh.m_edges[common_edge][1], other_triangle ) )
                    {
                        continue;
                    }
                    
                    // the dangling vertex will be safely removed by the vertex cleanup function
                    
                    // delete the triangle
                    
                    if ( m_verbose )
                    {
                        std::cout << "flap: triangles << " << i << " [" << current_triangle << 
                        "] and " << edge_tris[t] << " [" << other_triangle << "]" << std::endl;
                    }
                    
                    remove_triangle( i );
                    
                    // delete its opposite
                    
                    remove_triangle( other_triangle_index );
                    
                    flap_found = true;
                    break;
                }
                
            }
            
        }
        
    }
    
    triangle_indices.clear();
    
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
        
        // edge splitting
        while ( m_splitter.split_pass() ) {}
        
        // edge flipping
        m_flipper.flip_pass();		
        
        // edge collapsing
        while ( m_collapser.collapse_pass() ) {}
        
        // null-space smoothing
        if ( m_allow_vertex_movement )
        {
            m_smoother.null_space_smoothing_pass( 1.0 );
        }
        
        if ( m_collision_safety )
        {
            assert_mesh_is_intersection_free( false );
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
    
    if ( false == m_allow_topology_changes )
    {
        return;
    }
    
    bool merge_occurred = true;
    while ( merge_occurred )
    {
        
        merge_occurred = m_merger.merge_pass();
        
        m_pincher.separate_singular_vertices();
        
        if ( m_collision_safety )
        {
            assert_mesh_is_intersection_free( false );
        }
    }      
    
}




